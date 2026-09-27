// Propose l'identifiant à partir du prénom (sans accents, en minuscules) tant qu'il n'a pas été saisi à la main,
// et évite le double envoi des formulaires.
(() => {
  const prenom = document.getElementById("prenom");
  const identifiant = document.getElementById("identifiant");
  if (prenom && identifiant) {
    let saisiALaMain = identifiant.value !== "";
    identifiant.addEventListener("input", () => { saisiALaMain = identifiant.value !== ""; });
    prenom.addEventListener("input", () => {
      if (saisiALaMain) return;
      identifiant.value = prenom.value.normalize("NFD").replace(/[̀-ͯ]/g, "")
        .toLowerCase().replace(/[^a-z0-9._-]+/g, "").slice(0, 32);
    });
  }
  for (const formulaire of document.querySelectorAll("form")) {
    formulaire.addEventListener("submit", () => {
      const bouton = formulaire.querySelector("button[type=submit]");
      if (bouton) { bouton.disabled = true; bouton.dataset.envoi = ""; }
    });
  }
})();
