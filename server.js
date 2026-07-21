const http = require("http");
const https = require("https");
const handler = require("serve-handler");

const port = Number(process.env.PORT) || 4173;
const root = __dirname;

// MyMiniFactory store integration.
// Set these as Railway variables (never commit the key):
//   MMF_API_KEY  — API key from MMF account settings
//   MMF_USERNAME — merchant username (defaults to miguelmercado1)
const MMF_API_KEY = process.env.MMF_API_KEY || "";
const MMF_USERNAME = process.env.MMF_USERNAME || "miguelmercado1";

// Small in-memory cache so we don't hit MMF on every page load.
const CACHE_TTL_MS = 5 * 60 * 1000;
let storeCache = { at: 0, payload: null };

function fetchStoreProducts() {
  return new Promise((resolve, reject) => {
    const params = new URLSearchParams({
      store: "1",
      per_page: "24",
      key: MMF_API_KEY,
    });
    const url = `https://www.myminifactory.com/api/v2/users/${encodeURIComponent(
      MMF_USERNAME
    )}/objects?${params.toString()}`;

    https
      .get(url, { headers: { Accept: "application/json" } }, (res) => {
        let body = "";
        res.on("data", (chunk) => (body += chunk));
        res.on("end", () => {
          if (res.statusCode < 200 || res.statusCode >= 300) {
            reject(new Error(`MMF responded ${res.statusCode}`));
            return;
          }
          try {
            resolve(JSON.parse(body));
          } catch (err) {
            reject(new Error("Invalid JSON from MMF"));
          }
        });
      })
      .on("error", reject);
  });
}

function normalize(raw) {
  const items = Array.isArray(raw && raw.items) ? raw.items : [];
  return {
    total: typeof raw.total_count === "number" ? raw.total_count : items.length,
    products: items.map((obj) => {
      const images = Array.isArray(obj.images) ? obj.images : [];
      const primary = images.find((img) => img.is_primary) || images[0] || null;
      const image =
        primary &&
        ((primary.thumbnail && primary.thumbnail.url) ||
          (primary.original && primary.original.url));
      return {
        id: obj.id,
        name: obj.name || "Untitled",
        url: obj.url || "",
        image: image || "",
      };
    }),
  };
}

async function handleStoreApi(request, response) {
  response.setHeader("Content-Type", "application/json; charset=utf-8");

  if (!MMF_API_KEY) {
    response.statusCode = 200;
    response.end(
      JSON.stringify({ configured: false, total: 0, products: [] })
    );
    return;
  }

  const now = Date.now();
  if (storeCache.payload && now - storeCache.at < CACHE_TTL_MS) {
    response.statusCode = 200;
    response.end(JSON.stringify(storeCache.payload));
    return;
  }

  try {
    const raw = await fetchStoreProducts();
    const payload = { configured: true, ...normalize(raw) };
    storeCache = { at: now, payload };
    response.statusCode = 200;
    response.end(JSON.stringify(payload));
  } catch (err) {
    response.statusCode = 502;
    response.end(
      JSON.stringify({ configured: true, error: String(err.message || err), products: [] })
    );
  }
}

const server = http.createServer((request, response) => {
  const url = (request.url || "").split("?")[0];

  if (url === "/api/store") {
    handleStoreApi(request, response);
    return;
  }

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
  });
});

server.listen(port, "0.0.0.0", () => {
  console.log(`[benchtop-front] listening on ${port}`);
});
