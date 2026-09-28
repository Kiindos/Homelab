// Accueil du homelab : affiche les services auxquels la personne a accès (groupes transmis par le SSO du WAF),
// avec leur mode d'emploi. Données : moi.json (identité), services.json (catalogue, décrit dans l'inventaire) et
// annonces.json (maintenances et incidents en cours, publiés depuis la page des comptes ; facultatif).
(async () => {
  const $ = (id) => document.getElementById(id);
  const lire = async (url) => {
    const reponse = await fetch(url, { cache: "no-store", credentials: "same-origin" });
    if (!reponse.ok) throw new Error(`${url} : ${reponse.status}`);
    return reponse.json();
  };
  const paragraphe = (classe, texte) => {
    const p = document.createElement("p");
    p.className = classe;
    p.textContent = texte;
    return p;
  };
  // Bandeaux : ceux destinés à tout le monde, ou à l'un des groupes de la personne.
  const afficherAnnonces = (liste, groupes) => {
    const zone = $("annonces");
    const visibles = liste.filter((a) => !(a.groupes || []).length || a.groupes.some((g) => groupes.has(g)));
    for (const annonce of visibles) {
      const bloc = document.createElement("article");
      bloc.className = `annonce annonce--${annonce.type}`;
      bloc.setAttribute("role", annonce.type === "incident" ? "alert" : "status");
      const tete = document.createElement("p");
      tete.className = "annonce__tete";
      const etiquette = document.createElement("span");
      etiquette.className = "annonce__type";
      etiquette.textContent = annonce.libelle;
      const titre = document.createElement("strong");
      titre.textContent = annonce.titre;
      tete.append(etiquette, titre);
      bloc.appendChild(tete);
      const infos = [annonce.periode, (annonce.services || []).length ? `Services : ${annonce.services.join(", ")}` : ""];
      if (infos.some(Boolean)) bloc.appendChild(paragraphe("annonce__infos", infos.filter(Boolean).join(" · ")));
      if (annonce.message) bloc.appendChild(paragraphe("annonce__message", annonce.message));
      zone.appendChild(bloc);
    }
    zone.hidden = !visibles.length;
  };
  try {
    const [moi, catalogue, annonces] = await Promise.all([
      lire("moi.json"), lire("services.json"), lire("annonces.json").catch(() => ({ annonces: [] }))]);
    const groupes = new Set((moi.groupes || "").split(",").map((g) => g.trim()).filter(Boolean));
    afficherAnnonces(annonces.annonces || [], groupes);
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
      if (service.capture) {
        const image = document.createElement("img");
        image.src = `guides/${encodeURIComponent(service.capture)}`;
        image.alt = `Écran de connexion : ${service.nom}`;
        image.loading = "lazy";
        image.className = "service__capture";
        carte.querySelector(".service__connexion").after(image);
      }
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
      if (!(service.etapes || []).length && !(service.applis || []).length && !service.connexion && !service.capture) {
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
