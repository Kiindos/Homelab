variable "proxmox_endpoint" {
  description = "URL de l'API Proxmox (joignable via le VLAN admin ou le VPN)."
  type        = string
  default     = "https://prd-pve-01.example.internal:8006/"
}

variable "proxmox_api_token" {
  description = "Jeton API Proxmox. À fournir via TF_VAR_proxmox_api_token ou un fichier SOPS, jamais en clair."
  type        = string
  sensitive   = true
}

variable "proxmox_insecure" {
  description = "Accepter le certificat auto-signé tant que cert-manager n'est pas en place."
  type        = bool
  default     = true
}
