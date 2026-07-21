const http = require("http");
const handler = require("serve-handler");

const port = Number(process.env.PORT) || 4173;
const root = __dirname;

const server = http.createServer((request, response) =>
  handler(request, response, {
    public: root,
    cleanUrls: true,
    headers: [
      {
        source: "**/*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=0, must-revalidate",
          },
        ],
      },
    ],
  })
);

server.listen(port, "0.0.0.0", () => {
  console.log(`[benchtop-front] listening on ${port}`);
});
