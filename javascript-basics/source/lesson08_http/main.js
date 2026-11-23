{
  const http = require("http");

  function request(port, pathname) {
    return new Promise((resolve, reject) => {
      http
        .get({ host: "127.0.0.1", port, path: pathname }, (res) => {
          let body = "";
          res.on("data", (chunk) => {
            body += chunk;
          });
          res.on("end", () => resolve({ status: res.statusCode, body }));
        })
        .on("error", reject);
    });
  }

  async function main() {
    const server = http.createServer((req, res) => {
      res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("你好，Node HTTP");
    });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    try {
      const result = await request(server.address().port, "/");
      console.log("状态码：", result.status);
      console.log("响应：", result.body);
    } finally {
      await new Promise((resolve) => server.close(resolve));
    }
  }

  main();
}


{
  const http = require("http");

  function request(port, pathname) {
    return new Promise((resolve, reject) => {
      http
        .get({ host: "127.0.0.1", port, path: pathname }, (res) => {
          let body = "";
          res.on("data", (chunk) => {
            body += chunk;
          });
          res.on("end", () => resolve({ status: res.statusCode, body }));
        })
        .on("error", reject);
    });
  }

  async function main() {
    const server = http.createServer((req, res) => {
      const pathname = new URL(req.url, `http://${req.headers.host}`).pathname;
      res.setHeader("Content-Type", "application/json; charset=utf-8");
      if (pathname === "/api/courses") {
        res.writeHead(200);
        res.end(JSON.stringify({ courses: ["JavaScript", "Node"] }));
      } else {
        res.writeHead(404);
        res.end(JSON.stringify({ error: "not found" }));
      }
    });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    try {
      const port = server.address().port;
      const found = await request(port, "/api/courses");
      const missing = await request(port, "/missing");
      console.log("200：", found.body);
      console.log("404：", missing.status, missing.body);
    } finally {
      await new Promise((resolve) => server.close(resolve));
    }
  }

  main();
}


{
  const http = require("http");

  const server = http.createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("pong");
  });

  server.listen(0, "127.0.0.1", () => {
    const port = server.address().port;
    http.get({ host: "127.0.0.1", port, path: "/ping" }, (res) => {
      let body = "";
      res.on("data", (chunk) => {
        body += chunk;
      });
      res.on("end", () => {
        console.log(res.statusCode, body);
        server.close(() => console.log("服务已关闭"));
      });
    });
  });
}
