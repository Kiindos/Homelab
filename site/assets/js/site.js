// Homelab — comportements du site : thème, filtres des ADR, sommaire actif,
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

    // Filtres des décisions par statut
    const filtres = document.querySelectorAll(".filtre");
    filtres.forEach((b) => b.addEventListener("click", () => {
      filtres.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      document.querySelectorAll(".liste-adr--complete li").forEach((c) => {
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
        try { await navigator.clipboard.writeText(pre.innerText.replace(/copier$/, "").trim()); b.textContent = "copié"; }
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
          ? { primaryColor: "#f1eee7", primaryBorderColor: "#847e73", primaryTextColor: "#1f1d1a", lineColor: "#847e73", background: "#fbfaf7", secondaryColor: "#f6f3ec", tertiaryColor: "#fbfaf7" }
          : { primaryColor: "#1f1d1a", primaryBorderColor: "#8a8478", primaryTextColor: "#e8e4db", lineColor: "#8a8478", background: "#161513", secondaryColor: "#23211e", tertiaryColor: "#161513" },
      });
      window.mermaid.run({ querySelector: ".mermaid" });
    }
  });
})();
