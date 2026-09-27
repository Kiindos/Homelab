# Lecture seule des secrets de la plateforme (Semaphore, et poste d'admin pour les déploiements).
path "homelab/data/plateforme/*" {
  capabilities = ["read"]
}
path "homelab/metadata/plateforme" {
  capabilities = ["list"]
}
path "homelab/metadata/plateforme/*" {
  capabilities = ["list", "read"]
}
