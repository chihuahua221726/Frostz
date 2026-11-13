import http from "node:http";
import { createRequire } from "node:module";
import path from "node:path";
import express from "express";
import { scramjetPath } from "@mercuryworkshop/scramjet/path";
import { server as wisp } from "@mercuryworkshop/wisp-js/server";

const require = createRequire(import.meta.url);
const dirOf = (specifier) => path.dirname(require.resolve(specifier));
const app = express();

app.use((_req, res, next) => {
  res.setHeader("Cross-Origin-Opener-Policy", "same-origin");
  res.setHeader("Cross-Origin-Embedder-Policy", "require-corp");
  next();
});

app.use("/scram/", express.static(scramjetPath));
app.use("/utils/", express.static(dirOf("@mercuryworkshop/scramjet-utils")));
app.use("/controller/", express.static(dirOf("@mercuryworkshop/scramjet-controller")));
app.use("/libcurl/", express.static(dirOf("@mercuryworkshop/libcurl-transport")));
app.use("/epoxy/", express.static(dirOf("@mercuryworkshop/epoxy-transport")));
app.use(express.static("."));

const server = http.createServer(app);
server.on("upgrade", (req, socket, head) => {
  const wispPath = new URL(req.url ?? "/", "http://localhost").pathname;
  if (wispPath === "/wisp/") {
    req.url = wispPath;
    wisp.routeRequest(req, socket, head);
    return;
  }
  socket.end();
});

server.listen(8080, () => {
  console.log("FrostZ running on http://localhost:8080");
});