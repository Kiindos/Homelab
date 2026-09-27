variable "etat_passphrase" {
  description = "Phrase de passe de chiffrement de l'état. Fournie par variable d'environnement."
  type        = string
  sensitive   = true
}

variable "nom_coffre" {
  description = "Nom DNS du coffre (URL de rappel de l'interface web)."
  type        = string
}

variable "oidc_emetteur" {
  description = "Émetteur OpenID Connect (portail Authelia)."
  type        = string
}

variable "oidc_secret" {
  description = "Secret du client OpenID Connect « openbao » dans Authelia. Fourni par variable d'environnement."
  type        = string
  sensitive   = true
}

variable "groupe_admins" {
  description = "Groupe de l'annuaire dont les membres administrent le coffre."
  type        = string
  default     = "admins"
}

variable "semaphore_sources" {
  description = "Adresses (CIDR) d'où Semaphore peut s'authentifier et utiliser ses jetons."
  type        = list(string)
  default     = []
}
