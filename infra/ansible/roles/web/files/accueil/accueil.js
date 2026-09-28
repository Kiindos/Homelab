// Accueil du homelab : affiche les services auxquels la personne a accès (groupes transmis par le SSO du WAF),
// avec leur mode d'emploi. Données : moi.json (identité) et services.json (catalogue, décrit dans l'inventaire).
(async () => {
  const $ = (id) => document.getElementById(id);
  const lire = async (url) => {
    const reponse = await fetch(url, { cache: "no-store", credentials: "same-origin" });
    if (!reponse.ok) throw new Error(`${url} : ${reponse.status}`);
    return reponse.json();
  };
  try {
    const [moi, catalogue] = await Promise.all([lire("moi.json"), lire("services.json")]);
    const groupes = new Set((moi.groupes || "").split(",").map((g) => g.trim()).filter(Boolean));
    $("utilisateur").textContent = moi.utilisateur || "";
    $("bonjour").textContent = moi.utilisateur ? `Bonjour ${moi.utilisateur}` : "Bonjour";
    $("deconnexion").href = `${catalogue.portail}/logout`;

    const accessibles = catalogue.services.filter((s) => (s.groupes || []).some((g) => groupes.has(g)));
    const modele = $("modele-service");
    for (const service of accessibles) {
      const carte = modele.content.cloneNode(true);
      carte.querySelector(".service__nom").textContent = service.nom;
      carte.querySelector(".service__appli").textContent = service.appli || "";
      carte.querySelector(".service__description").textContent = service.description || "";
      const ouvrir = carte.querySelector(".service__ouvrir");
      ouvrir.href = service.url;
      ouvrir.textContent = service.bouton || "Ouvrir";
      carte.querySelector(".service__connexion").textContent = service.connexion || "";
      const etapes = carte.querySelector(".service__etapes");
      for (const etape of service.etapes || []) {
        const li = document.createElement("li");
        li.textContent = etape;
        etapes.appendChild(li);
      }
      const applis = carte.querySelector(".service__applis");
      for (const appli of service.applis || []) {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = appli.lien;
        a.rel = "noopener";
        a.target = "_blank";
        a.textContent = appli.nom;
        li.appendChild(a);
        applis.appendChild(li);
      }
      if (!(service.etapes || []).length && !(service.applis || []).length && !service.connexion) {
        carte.querySelector(".service__guide").remove();
      }
      $("services").appendChild(carte);
    }
    if (!accessibles.length) {
      const message = $("message");
      message.hidden = false;
      message.textContent = "Aucun service n'est encore ouvert pour votre compte : demandez à l'administrateur.";
    }
  } catch (erreur) {
    const message = $("message");
    message.hidden = false;
    message.classList.add("message--erreur");
    message.textContent = "Impossible de charger vos services pour le moment. Réessayez dans un instant.";
    console.error(erreur);
  }
})();
