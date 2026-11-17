from abc import ABC, abstractmethod
import json
import time
import feedparser
from supabase import create_client, Client
from groq import Groq
import os
from dotenv import load_dotenv

class BaseNewsFetcher(ABC):
    """Abstract interface for news source ingestion."""
    def __init__(self, category: str, feed_url: str):
        self._category = category
        self._feed_url = feed_url

    @abstractmethod
    def fetch_raw_articles(self, limit: int = 3) -> list:
        pass


class RSSNewsFetcher(BaseNewsFetcher):
    """Fetches and normalizes entries from an RSS feed."""
    def fetch_raw_articles(self, limit: int = 10) -> list:
        parsed_feed = feedparser.parse(self._feed_url)
        articles = []
        for entry in parsed_feed.entries[:limit]:
            image_url = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800"
            if "media_thumbnail" in entry:
                image_url = entry["media_thumbnail"][0]["url"]
            elif "media_content" in entry:
                image_url = entry["media_content"][0]["url"]

            # Truncate raw summary to 2500 chars to stay well within free-tier token limits
            raw_text = entry.get("summary", entry.get("description", ""))[:2500]

            articles.append({
                "title": entry.get("title", ""),
                "summary": raw_text,
                "source_url": entry.get("link", ""),
                "image_url": image_url,
                "category": self._category
            })
        return articles


class AISummarizer:
    """Encapsulates Groq LLM interaction for structured article summarization."""
    def __init__(self, api_key: str):
        self.__client = Groq(api_key=api_key)
        self.__model_name = self.__resolve_available_model()

    def __resolve_available_model(self) -> str:
        """Fetches active models from Groq and selects a fast model with higher TPM limits."""
        try:
            models = self.__client.models.list().data
            available_ids = [m.id for m in models]
            
            # Prioritize high-throughput models first
            preferred = [
                "llama-3.1-8b-instant",
                "openai/gpt-oss-20b",
                "openai/gpt-oss-120b",
                "llama-3.3-70b-versatile"
            ]
            for candidate in preferred:
                if candidate in available_ids:
                    print(f"[INFO] Selected active Groq model: {candidate}")
                    return candidate
            
            excluded_keywords = ("whisper", "guard", "safeguard", "orpheus", "tts")
            for model_id in available_ids:
                if not any(kw in model_id.lower() for kw in excluded_keywords):
                    print(f"[INFO] Selected fallback Groq model: {model_id}")
                    return model_id
                    
        except Exception as e:
            print(f"[WARN] Could not fetch model list: {e}")
            
        return "openai/gpt-oss-20b"

    def generate_short(self, title: str, text: str) -> dict | None:
        prompt = f"""
        You are an unbiased news editor for 'Straight Facts'. 
        Summarize the following article into a ~60 word short.
        Extract the core "Why It Matters" takeaway and two opposing perspective points if applicable.

        Article Title: {title}
        Article Content/Summary: {text[:2500]}

        Output valid JSON strictly in this format:
        {{
            "title": "Short punchy headline (max 10 words)",
            "summary": "Clear 50-60 word objective news summary.",
            "why_it_matters": "1 concise sentence explaining the direct impact on the reader.",
            "perspective_a": "Brief Side A argument or benefit (1 sentence)",
            "perspective_b": "Brief Side B argument or counter-point (1 sentence)"
        }}
        """
        
        for attempt in range(2):
            try:
                response = self.__client.chat.completions.create(
                    model=self.__model_name,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"[WARN] Summarization attempt {attempt + 1} failed: {e}. Retrying in 5s...")
                time.sleep(5)
                
        return None


class ArticleRepository:
    """Manages database persistence operations for articles."""
    def __init__(self, url: str, key: str):
        self.__supabase: Client = create_client(url, key)

    def get_existing_urls(self) -> set[str]:
        """Loads all stored source URLs into a Hash Set for O(1) lookup."""
        try:
            response = self.__supabase.table("articles").select("source_url").execute()
            return {row["source_url"] for row in response.data if row.get("source_url")}
        except Exception as e:
            print(f"[WARN] Could not fetch existing URLs: {e}")
            return set()

    def save_article(self, article_data: dict) -> bool:
        try:
            self.__supabase.table("articles").insert(article_data).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Database insert failed: {e}")
            return False


class NewsPipelineOrchestrator:
    """Coordinates fetching, summarization, and database storage."""
    def __init__(self, summarizer: AISummarizer, repository: ArticleRepository):
        self.summarizer = summarizer
        self.repository = repository
        self.fetchers: list[BaseNewsFetcher] = []

    def register_fetcher(self, fetcher: BaseNewsFetcher):
        self.fetchers.append(fetcher)

    def run(self):
        print("[INFO] Starting news ingestion pipeline...")
        seen_urls: set[str] = self.repository.get_existing_urls()
        print(f"[INFO] Loaded {len(seen_urls)} existing URLs into deduplication set.")
        saved_count = 0

        for fetcher in self.fetchers:
            raw_articles = fetcher.fetch_raw_articles()
            for raw in raw_articles:
                source_url = raw["source_url"]
                title_preview = raw["title"][:50]

                # O(1) Hash Set lookup to prevent duplicate AI calls & DB inserts
                if source_url in seen_urls:
                    print(f"[INFO] Skipping duplicate article: {title_preview}...")
                    continue

                print(f"[INFO] Processing article: {title_preview}...")
                ai_data = self.summarizer.generate_short(raw["title"], raw["summary"])
                if not ai_data:
                    print(f"[ERROR] Skipping article due to summarization failure: {title_preview}")
                    continue

                payload = {
                    "title": ai_data.get("title", raw["title"]),
                    "summary": ai_data.get("summary"),
                    "why_it_matters": ai_data.get("why_it_matters"),
                    "perspective_a": ai_data.get("perspective_a"),
                    "perspective_b": ai_data.get("perspective_b"),
                    "image_url": raw["image_url"],
                    "source_url": source_url,
                    "category": raw["category"]
                }

                if self.repository.save_article(payload):
                    seen_urls.add(source_url)
                    saved_count += 1
                    print(f"[SUCCESS] Stored article: {payload['title']}")

                time.sleep(2)

        print(f"[INFO] Pipeline finished. Total articles stored: {saved_count}")

if __name__ == "__main__":
    load_dotenv(".env.local")

    SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    GROQ_KEY = os.getenv("GROQ_API_KEY")

    if not all([SUPABASE_URL, SUPABASE_KEY, GROQ_KEY]):
        raise ValueError("Missing environment variables in .env.local or GitHub Secrets.")
    
    summarizer_engine = AISummarizer(api_key=GROQ_KEY)
    db_repo = ArticleRepository(url=SUPABASE_URL, key=SUPABASE_KEY)
    
    pipeline = NewsPipelineOrchestrator(summarizer=summarizer_engine, repository=db_repo)
    pipeline.register_fetcher(RSSNewsFetcher("Tech", "https://feeds.feedburner.com/TechCrunch/"))
    pipeline.register_fetcher(RSSNewsFetcher("Business", "http://feeds.bbci.co.uk/news/business/rss.xml"))
    pipeline.register_fetcher(RSSNewsFetcher("World", "http://feeds.bbci.co.uk/news/world/rss.xml"))
    pipeline.register_fetcher(RSSNewsFetcher("Science", "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml"))
    
    pipeline.run()