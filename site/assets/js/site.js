// Homelab — comportements du site : thème, animations d'apparition, filtres des ADR, sommaire actif,
// copie des blocs de code, schémas Mermaid. Aucun traceur, aucune dépendance (hors Mermaid, chargé à la demande).
(() => {
  const racine = document.documentElement;
  const cle = "homelab-theme";

  // Thème : préférence mémorisée si possible (le stockage peut être indisponible), sinon réglage du système.
  const lire = () => { try { return localStorage.getItem(cle); } catch { return null; } };
  const ecrire = (v) => { try { localStorage.setItem(cle, v); } catch { /* navigation privée */ } };
  const memorise = lire();
  if (memorise === "clair" || memorise === "sombre") racine.dataset.theme = memorise;

  const themeEffectif = () => {
    if (racine.dataset.theme === "clair" || racine.dataset.theme === "sombre") return racine.dataset.theme;
    return matchMedia("(prefers-color-scheme: light)").matches ? "clair" : "sombre";
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelector(".bascule-theme")?.addEventListener("click", () => {
      const suivant = themeEffectif() === "clair" ? "sombre" : "clair";
      racine.dataset.theme = suivant;
      ecrire(suivant);
      if (window.mermaid) location.reload(); // les schémas sont dessinés pour un thème donné
    });

    // Apparition au défilement
    const elements = document.querySelectorAll(".revele");
    if ("IntersectionObserver" in window) {
      const obs = new IntersectionObserver((entrees) => {
        entrees.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("visible"); obs.unobserve(e.target); } });
      }, { rootMargin: "0px 0px -8% 0px" });
      elements.forEach((el) => obs.observe(el));
    } else {
      elements.forEach((el) => el.classList.add("visible"));
    }

    // Filtres des décisions par statut
    const filtres = document.querySelectorAll(".filtre");
    filtres.forEach((b) => b.addEventListener("click", () => {
      filtres.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      document.querySelectorAll(".carte--adr").forEach((c) => {
        c.hidden = b.dataset.filtre !== "tout" && c.dataset.statut !== b.dataset.filtre;
      });
    }));

    // Sommaire : met en évidence la section lue
    const liens = [...document.querySelectorAll(".sommaire a")];
    if (liens.length && "IntersectionObserver" in window) {
      const cibles = liens.map((a) => document.getElementById(decodeURIComponent(a.hash.slice(1)))).filter(Boolean);
      const obs = new IntersectionObserver((entrees) => {
        entrees.forEach((e) => {
          if (e.isIntersecting) liens.forEach((a) => a.classList.toggle("actif", a.hash.slice(1) === e.target.id));
        });
      }, { rootMargin: "0px 0px -70% 0px" });
      cibles.forEach((c) => obs.observe(c));
    }

    // Bouton « copier » sur les blocs de code
    document.querySelectorAll(".prose pre:not(.mermaid)").forEach((pre) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "copier"; b.textContent = "copier";
      b.addEventListener("click", async () => {
        try { await navigator.clipboard.writeText(pre.innerText.replace(/copier$/, "").trim()); b.textContent = "copié ✓"; }
        catch { b.textContent = "échec"; }
        setTimeout(() => { b.textContent = "copier"; }, 1600);
      });
      pre.appendChild(b);
    });

    // Schémas Mermaid (script chargé uniquement sur les pages qui en contiennent)
    if (window.mermaid && document.querySelector(".mermaid")) {
      const clair = themeEffectif() === "clair";
      window.mermaid.initialize({
        startOnLoad: false, securityLevel: "strict", theme: "base",
        fontFamily: getComputedStyle(document.body).fontFamily,
        themeVariables: clair
          ? { primaryColor: "#e6fffb", primaryBorderColor: "#0d9488", primaryTextColor: "#0f172a", lineColor: "#64748b", background: "#ffffff" }
          : { primaryColor: "#111a2c", primaryBorderColor: "#2dd4bf", primaryTextColor: "#e6edf7", lineColor: "#6b7a92", background: "#0b1220", secondaryColor: "#1e1b4b", tertiaryColor: "#0f172a" },
      });
      window.mermaid.run({ querySelector: ".mermaid" });
    }
  });
})();
