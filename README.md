# 📰 Straight Facts

**Straight Facts** is an AI-powered vertical news shorts web application built with Next.js, TypeScript, Supabase, and Python. Designed to combat information overload and media bias, it condenses live RSS news feeds into ~60-word objective summaries enriched with actionable **"Why It Matters"** takeaways and balanced **"Dual Perspectives" (Side A vs. Side B)**.

---

## ✨ Key Features

- **Vertical Snap-Scroll Feed:** Mobile-first, full-screen TikTok/Inshorts-style vertical card navigation powered by CSS scroll-snap (`snap-y snap-mandatory`)[cite: 1, 2, 4].
- **"Why It Matters" Context:** Every news card highlights the direct real-world impact of the story in one concise sentence[cite: 2, 3].
- **Dual Perspectives (Side A vs. Side B):** AI-extracted balanced viewpoints to eliminate echo chambers and present both sides of a story[cite: 1, 3].
- **Instant $O(1)$ Category Filtering:** Dynamic floating filter pills (**All**, **Tech**, **Business**, etc.) backed by a client-side Hash Map (`Map<string, Article[]>`) for instantaneous switching without extra database queries[cite: 1, 2, 4].
- **Automated Daily Ingestion:** A GitHub Actions cron workflow runs daily at **8:00 AM UTC** to fetch fresh news, deduplicate entries in $O(1)$ time using a Hash Set, summarize via Groq LLM, and update Supabase automatically.

---

## 🛠️ Tech Stack

- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS[cite: 2, 6]
- **Backend & Automation:** Python 3, `feedparser`, Groq API (LLM JSON Schema Enforcement), GitHub Actions[cite: 1, 5]
- **Database:** Supabase (PostgreSQL)
- **Deployment:** Vercel[cite: 1]

---

## 🏗️ System Architecture & Core Concepts

### 1. Object-Oriented Backend Pipeline (`ingest_news.py`)
The Python ingestion engine follows clean OOP principles and the Single Responsibility Principle (SRP)[cite: 1, 5]:
- **`BaseNewsFetcher(ABC)` & `RSSNewsFetcher`:** Uses *Abstraction* and *Polymorphism* to normalize articles from multiple RSS feeds (TechCrunch, BBC Business)[cite: 1, 5].
- **`AISummarizer`:** Uses *Encapsulation* to manage Groq API credentials and enforce deterministic JSON outputs (`title`, `summary`, `why_it_matters`, `perspective_a`, `perspective_b`)[cite: 1, 5].
- **`ArticleRepository`:** Isolates all Supabase PostgreSQL read/write operations[cite: 1, 5].
- **`NewsPipelineOrchestrator`:** Uses *Composition* to coordinate fetching, deduplication, AI summarization, and database persistence[cite: 1, 5].

### 2. Data Structures Optimization
- **Backend Deduplication ($O(1)$ Hash Set):** `NewsPipelineOrchestrator` loads existing `source_url` entries into a Python `set[str]` to skip duplicate articles in $O(1)$ average time before invoking the LLM[cite: 1].
- **Frontend Filtering ($O(1)$ Hash Map):** `NewsFeedClient.tsx` indexes fetched articles into a `Map<string, Article[]>` via `useMemo`, allowing instant category filtering with zero network latency[cite: 1, 4].

---

## 📂 Project Structure

```text
straight-facts/
├── .github/
│   └── workflows/
│       └── ingest.yml              # Daily automated GitHub Actions cron job[cite: 1, 4]
├── app/
│   ├── components/
│   │   └── NewsFeedClient.tsx      # Snap-scroll UI, cards, & O(1) category filter[cite: 1, 4]
│   ├── lib/
│   │   └── supabase.ts             # Supabase client initialization[cite: 4]
│   └── page.tsx                    # Next.js Server Component fetching live articles[cite: 1, 4]
├── ingest_news.py                  # OOP Python RSS-to-AI-to-Supabase pipeline[cite: 1, 5]
├── .env.local                      # Local environment variables (gitignored)[cite: 1, 3]
└── package.json
