# Adresse, autorité interne et jeton : variables d'environnement VAULT_ADDR, VAULT_CACERT et VAULT_TOKEN
# (jeton obtenu par « bao login -method=oidc », ou jeton racine lors de la toute première configuration).
provider "vault" {
  # Le jeton fourni est utilisé tel quel (pas de jeton enfant) ; OpenBao dérive de Vault 1.14.
  skip_child_token       = true
  skip_get_vault_version = true
  vault_version_override = "1.14.9"
}
