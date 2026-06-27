import { rewrite } from "@vercel/functions";

export const config = { matcher: "/" };

export default function middleware(request: Request) {
  const theme = new URL(request.url).searchParams.get("theme");

  if (theme === null || theme === "dark") {
    return rewrite(new URL("/?theme=dark", request.url));
  }
  if (theme === "light") {
    return rewrite(new URL("/?theme=light", request.url));
  }

  return new Response('theme must be "dark" or "light"', {
    status: 422,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}
