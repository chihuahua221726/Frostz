import { handleWispRequest } from "./wisp.js";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/wisp" || url.pathname.startsWith("/wisp/")) {
      return handleWispRequest(request, env);
    }

    if (url.pathname.startsWith("/api/")) {
      return new Response("Not found", { status: 404 });
    }

    return env.ASSETS.fetch(request);
  },
};
