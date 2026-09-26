---
title: Documentation du homelab
description: Point d'entrée de la documentation publiée sur maximebertrand.net
---

# Documentation

Ce dossier est la **source unique** de la documentation affichée sur [maximebertrand.net](https://maximebertrand.net).
Le site est généré par Hugo depuis le dossier `site/` (thème sur mesure), qui monte ce dossier comme contenu
(voir l'[ADR 0013](adr/0013-site-public-hugo.md)). La CI vérifie que le site se construit sans avertissement.

## Contrat avec le site

Chaque fichier Markdown commence par un frontmatter YAML que le site exploite :

| Champ | Obligatoire | Usage |
|---|---|---|
| `title` | oui | Titre de la page |
| `description` | oui | Résumé (cartes, balise meta) |
| `date` | pour journal, ADR, post-mortem | Tri chronologique (`AAAA-MM-JJ`) |
| `status` | pour les ADR | `proposé`, `accepté`, `remplacé`, `abandonné` |
| `tags` | non | Filtrage sur le site |
| `draft` | non | `true` = non publié |

Les dossiers deviennent des sections du site : `architecture/`, `adr/`, `runbooks/`, `postmortems/`, `journal/`.
Les fichiers commençant par `_` (modèles) ne sont pas publiés.
