import { rewrite } from '@vercel/functions';

// Run only on the widget route. The cron endpoint (/api/internal/prewarm) and
// /docs are never touched, so their behavior is unchanged.
export const config = { matcher: '/' };

// Normalize the widget URL before the CDN cache so junk query params can't be
// used as cache-busters: everything collapses onto two cache keys
// (?theme=dark / ?theme=light). Runs at the edge before any function invocation.
export default function middleware(request: Request) {
  const theme = new URL(request.url).searchParams.get('theme');

  // Strict allowlist. A missing theme defaults to dark (the app's default).
  if (theme === null || theme === 'dark') {
    return rewrite(new URL('/?theme=dark', request.url));
  }
  if (theme === 'light') {
    return rewrite(new URL('/?theme=light', request.url));
  }

  // Invalid theme: reject at the edge (422) so junk theme values never reach the
  // function and can't pollute the cache.
  return new Response('theme must be "dark" or "light"', {
    status: 422,
    headers: {
      'content-type': 'text/plain; charset=utf-8',
      'cache-control': 'no-store',
    },
  });
}
