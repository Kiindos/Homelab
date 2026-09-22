# Kubernetes (phase 2)

Manifests suivis par Argo CD selon le modèle *app of apps* :

```
kubernetes/
  bootstrap/   Application racine Argo CD
  apps/        Une Application par service (Traefik, cert-manager, site vitrine…)
```

Rien n'est déployé tant que le socle Proxmox (phase 1) n'est pas en place.
