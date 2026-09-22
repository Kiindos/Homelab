variable "cloudflare_api_token" {
  description = "Jeton API Cloudflare (droits : Zone DNS Edit, Cloudflare Tunnel Edit)."
  type        = string
  sensitive   = true
}

variable "account_id" {
  description = "Identifiant du compte Cloudflare."
  type        = string
}

variable "vitrine_zone_id" {
  description = "Zone ID de maximebertrand.eu."
  type        = string
}

variable "vitrine_domain" {
  description = "Domaine du site vitrine."
  type        = string
  default     = "maximebertrand.eu"
}

variable "site_origin" {
  description = "Service interne vers lequel cloudflared renvoie le trafic du site."
  type        = string
  default     = "http://site-vitrine.vlan40.internal:8080"
}

variable "status_origin" {
  description = "Service interne de la page de statut (Uptime Kuma)."
  type        = string
  default     = "http://uptime-kuma.vlan40.internal:3001"
}
