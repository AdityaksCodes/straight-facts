'use client';

import { useState, useMemo } from 'react';

export interface Article {
  id: string;
  title: string;
  summary: string;
  why_it_matters?: string;
  perspective_a?: string;
  perspective_b?: string;
  image_url?: string;
  source_url: string;
  category: string;
  created_at: string;
}

export default function NewsFeedClient({ articles }: { articles: Article[] }) {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  // Group articles into a Hash Map (Map<category, Article[]>) for O(1) category lookup
  const { categoryMap, categories } = useMemo(() => {
    const map = new Map<string, Article[]>();
    map.set('All', articles);

    for (const article of articles) {
      const cat = article.category || 'General';
      if (!map.has(cat)) {
        map.set(cat, []);
      }
      map.get(cat)!.push(article);
    }

    return {
      categoryMap: map,
      categories: Array.from(map.keys()),
    };
  }, [articles]);

  // O(1) lookup for the active category's feed
  const filteredArticles = categoryMap.get(selectedCategory) ?? [];

  return (
    <div className="relative h-screen w-full bg-black text-white">
      {/* Floating Category Filter Bar */}
      <nav className="fixed top-0 left-0 right-0 z-20 flex justify-center gap-2 bg-gradient-to-b from-black/95 via-black/80 to-transparent p-4">
        <div className="flex max-w-md w-full gap-2 overflow-x-auto no-scrollbar">
          {categories.map((category) => {
            const isActive = selectedCategory === category;
            return (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-colors whitespace-nowrap ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-900 text-gray-400 border border-gray-800 hover:text-white'
                }`}
              >
                {category}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Full-Screen Vertical Snap Feed */}
      <div
        key={selectedCategory}
        className="h-screen w-full overflow-y-scroll snap-y snap-mandatory"
      >
        {filteredArticles.length === 0 ? (
          <div className="flex h-screen items-center justify-center text-gray-400 text-sm">
            No articles found in {selectedCategory}.
          </div>
        ) : (
          filteredArticles.map((article) => (
            <section
              key={article.id}
              className="h-screen w-full snap-start flex flex-col justify-between pt-16 pb-6 px-6 max-w-md mx-auto border-b border-gray-800"
            >
              {/* Category Badge */}
              <div>
                <span className="text-xs font-semibold bg-blue-600/20 text-blue-400 border border-blue-500/30 px-3 py-1 rounded-full uppercase tracking-wider">
                  {article.category}
                </span>
              </div>

              {/* Core Content */}
              <div className="space-y-4 my-auto">
                {article.image_url && (
                  <img
                    src={article.image_url}
                    alt={article.title}
                    className="w-full h-44 object-cover rounded-xl border border-gray-800"
                  />
                )}
                <h2 className="text-xl font-bold leading-snug">{article.title}</h2>
                <p className="text-sm text-gray-300 leading-relaxed">{article.summary}</p>

                {/* Why It Matters */}
                {article.why_it_matters && (
                  <div className="bg-gray-900 border border-gray-800 p-3 rounded-xl text-xs space-y-1">
                    <span className="font-bold text-yellow-400">WHY IT MATTERS:</span>
                    <p className="text-gray-300">{article.why_it_matters}</p>
                  </div>
                )}

                {/* Dual Perspectives */}
                {(article.perspective_a || article.perspective_b) && (
                  <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                    {article.perspective_a && (
                      <div className="bg-gray-900 p-2 rounded-lg border border-gray-800">
                        <span className="font-semibold text-blue-400 block mb-1">Side A</span>
                        <p className="text-gray-400">{article.perspective_a}</p>
                      </div>
                    )}
                    {article.perspective_b && (
                      <div className="bg-gray-900 p-2 rounded-lg border border-gray-800">
                        <span className="font-semibold text-purple-400 block mb-1">Side B</span>
                        <p className="text-gray-400">{article.perspective_b}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Footer Link */}
              <div className="text-center">
                <a
                  href={article.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-gray-500 hover:text-gray-300 underline"
                >
                  Read full article on source →
                </a>
              </div>
            </section>
          ))
        )}
      </div>
    </div>
  );
}