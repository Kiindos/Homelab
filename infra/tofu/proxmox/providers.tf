provider "proxmox" {
  endpoint  = var.proxmox_endpoint
  api_token = var.proxmox_api_token # format : "utilisateur@royaume!jeton=secret"

  # Le certificat de Proxmox est vérifié : l'autorité de Proxmox est ajoutée au magasin de
  # certificats du poste (variable d'environnement SSL_CERT_FILE) plutôt que d'ignorer les erreurs TLS.
  insecure = false
}
