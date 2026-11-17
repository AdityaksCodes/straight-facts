import { Suspense } from 'react';
import { supabase } from '@/app/lib/supabase';
import NewsFeedClient, { Article } from '@/app/components/NewsFeedClient';

async function NewsFeed() {
  const { data, error } = await supabase
    .from('articles')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center p-8 text-red-500">
        Error loading news: {error.message}
      </div>
    );
  }

  const articles: Article[] = data ?? [];
  return <NewsFeedClient articles={articles} />;
}

export default function Home() {
  return (
    <main className="bg-black min-h-screen">
      <Suspense
        fallback={
          <div className="flex h-screen items-center justify-center text-gray-400">
            Loading Straight Facts...
          </div>
        }
      >
        <NewsFeed />
      </Suspense>
    </main>
  );
}