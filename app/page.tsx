import { Suspense } from 'react';
import { supabase } from '@/app/lib/supabase';

// Separate component to handle the data fetching
async function ArticlesList() {
  const { data: articles, error } = await supabase
    .from('articles')
    .select('*');

  if (error) {
    return <div className="p-8 text-red-500">Error loading articles: {error.message}</div>;
  }

  return (
    <div className="space-y-6">
      {articles?.map((article) => (
        <div key={article.id} className="p-4 border rounded-xl shadow-sm space-y-2">
          <span className="text-xs bg-blue-100 text-blue-800 font-semibold px-2 py-1 rounded">
            {article.category}
          </span>
          <h2 className="text-lg font-bold">{article.title}</h2>
          <p className="text-sm text-gray-700">{article.summary}</p>
          {article.why_it_matters && (
            <p className="text-sm text-gray-900 font-semibold bg-gray-50 p-2 rounded">
              💡 <span className="underline">Why it matters:</span> {article.why_it_matters}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

// Main page component wrapped in Suspense
export default function Home() {
  return (
    <main className="min-h-screen p-8 max-w-xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold border-b pb-2">Straight Facts - Test Feed</h1>
      <Suspense fallback={<div className="p-8 text-gray-500">Loading straight facts...</div>}>
        <ArticlesList />
      </Suspense>
    </main>
  );
}