---
title: Documentation du homelab
description: Point d'entrée de la documentation publiée sur maximebertrand.eu
---

# Documentation

Ce dossier est la **source unique** de la documentation affichée sur [maximebertrand.eu](https://maximebertrand.eu).
À chaque push sur `main` qui modifie `docs/`, le workflow `notify-site.yml` demande au dépôt du site de se reconstruire.

## Contrat avec le site vitrine

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
