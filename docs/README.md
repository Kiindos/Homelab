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

## Traduction anglaise

`en/` contient les mêmes pages en anglais, avec **la même arborescence et les mêmes noms de fichiers** : c'est ce
qui relie une page à sa traduction (sélecteur FR / EN du site, liens `hreflang`). Le site anglais est servi sous
`/en/`. Règles :

- une page ajoutée ou modifiée en français l'est aussi dans `en/` (une page sans traduction n'existe pas sur le
  site anglais) ;
- `status` garde les valeurs françaises du contrat ci-dessus : le site affiche le libellé traduit ;
- les liens entre pages restent relatifs (`../adr/0008-exposition-directe-waf.md`) : ils mènent à la page de la
  même langue ;
- les textes de l'interface du site sont dans `site/i18n/`, la page d'accueil dans `site/data/homelab/<langue>.yaml`,
  les pages propres au site dans `site/content/` et `site/content-en/`.
