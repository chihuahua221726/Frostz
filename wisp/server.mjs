import http from "node:http";
import { server as wisp, logging } from "@mercuryworkshop/wisp-js/server";

const PORT = Number(process.env.PORT) || 8080;
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || "").split(",").filter(Boolean);

logging.set_level(logging.WARN);

wisp.options.allow_private_ips = false;
wisp.options.allow_loopback_ips = false;
wisp.options.allow_udp_streams = false;
wisp.options.port_whitelist = [80, 443];
wisp.options.stream_limit_per_conn = 50;  
wisp.options.stream_limit_total = 2000;    
wisp.options.parse_real_ip = true;       

const server = http.createServer((req, res) => {
	res.writeHead(200, { "Content-Type": "text/plain" });
	res.end("wisp server is up\n");
});

server.on("upgrade", (req, socket, head) => {
	const origin = req.headers.origin;
	const originOk = !ALLOWED_ORIGINS.length || ALLOWED_ORIGINS.includes(origin);

	if (req.url === "/wisp/" && originOk) wisp.routeRequest(req, socket, head);
	else socket.destroy();
});

server.listen(PORT, "127.0.0.1", () => console.log("wisp listening on :" + PORT));
