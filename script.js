(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const sections = document.querySelectorAll(".section");

  if (sections.length && !reduceMotion) {
    sections.forEach((el) => el.classList.add("reveal"));

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.14, rootMargin: "0px 0px -6% 0px" }
    );

    sections.forEach((el) => io.observe(el));
  }
})();

// MyMiniFactory store gallery — data comes from the site's own /api/store proxy.
(() => {
  const root = document.querySelector("[data-store]");
  if (!root) return;

  const statusEl = root.querySelector("[data-store-status]");
  const gridEl = root.querySelector("[data-store-grid]");

  const setStatus = (text) => {
    if (!statusEl) return;
    statusEl.textContent = text;
    statusEl.hidden = !text;
  };

  const escapeHtml = (value) =>
    String(value).replace(/[&<>"']/g, (ch) => {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[ch];
    });

  const render = (products) => {
    gridEl.innerHTML = products
      .map((p) => {
        const name = escapeHtml(p.name);
        const url = escapeHtml(p.url);
        const media = p.image
          ? `<img class="product__img" src="${escapeHtml(p.image)}" alt="${name}" loading="lazy" />`
          : `<span class="product__img product__img--empty" aria-hidden="true"></span>`;
        return `
          <a class="product" href="${url}" target="_blank" rel="noopener">
            ${media}
            <span class="product__name">${name}</span>
          </a>`;
      })
      .join("");
    gridEl.hidden = false;
  };

  fetch("/api/store", { headers: { Accept: "application/json" } })
    .then((res) => res.json())
    .then((data) => {
      if (!data || data.configured === false) {
        setStatus("Store products will appear here once connected.");
        return;
      }
      if (data.error) {
        setStatus("Couldn’t load products right now — visit the full store below.");
        return;
      }
      if (!data.products || data.products.length === 0) {
        setStatus("No products published yet — check the full store below.");
        return;
      }
      setStatus("");
      render(data.products);
    })
    .catch(() => {
      setStatus("Couldn’t load products right now — visit the full store below.");
    });
})();
