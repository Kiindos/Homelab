# Administrateurs (groupe de l'annuaire, connexion SSO avec double authentification) : tout le coffre.
path "*" {
  capabilities = ["create", "read", "update", "patch", "delete", "list", "sudo"]
}
