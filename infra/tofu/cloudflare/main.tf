# Site public par tunnel (ADR 0002) et services personnels publiés en direct derrière le WAF (ADR 0008).
# Syntaxe du provider cloudflare v5 : vérifier la doc du registre en cas de montée de version.

# --- Tunnel du site public ------------------------------------------------------------------------

resource "random_bytes" "tunnel_secret" {
  length = 32
}

resource "cloudflare_zero_trust_tunnel_cloudflared" "vitrine" {
  account_id    = var.account_id
  name          = "homelab-vitrine"
  config_src    = "cloudflare"
  tunnel_secret = random_bytes.tunnel_secret.base64
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "vitrine" {
  account_id = var.account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.vitrine.id

  config = {
    ingress = concat(
      [{ hostname = var.site_public, service = var.site_origin }],
      var.publier_status ? [{ hostname = "status.${var.vitrine_domain}", service = var.status_origin }] : [],
      [{ service = "http_status:404" }],
    )
  }
}

data "cloudflare_zero_trust_tunnel_cloudflared_token" "vitrine" {
  account_id = var.account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.vitrine.id
}

locals {
  tunnel_cname = "${cloudflare_zero_trust_tunnel_cloudflared.vitrine.id}.cfargotunnel.com"
}

resource "cloudflare_dns_record" "site_public" {
  zone_id = var.vitrine_zone_id
  name    = var.site_public
  type    = "CNAME"
  content = local.tunnel_cname
  proxied = true
  ttl     = 1
  comment = "Site public via Cloudflare Tunnel - géré par OpenTofu"
}

resource "cloudflare_dns_record" "status" {
  count = var.publier_status ? 1 : 0

  zone_id = var.vitrine_zone_id
  name    = "status.${var.vitrine_domain}"
  type    = "CNAME"
  content = local.tunnel_cname
  proxied = true
  ttl     = 1
  comment = "Page de statut via Cloudflare Tunnel - géré par OpenTofu"
}

# --- Services personnels publiés en direct (sans proxy Cloudflare) --------------------------------

resource "cloudflare_dns_record" "service" {
  for_each = toset(var.services_publics)

  zone_id = var.vitrine_zone_id
  name    = "${each.key}.${var.vitrine_domain}"
  type    = "A"
  content = var.ip_publique
  # « DNS only » : le trafic ne passe pas par Cloudflare (chiffrement de bout en bout, pas de limite de taille).
  proxied = false
  ttl     = 300
  comment = "Service publié derrière OPNsense + BunkerWeb (ADR 0008) - géré par OpenTofu"

  lifecycle {
    precondition {
      condition     = can(cidrhost("${var.ip_publique}/32", 0))
      error_message = "ip_publique doit être une adresse IPv4 valide."
    }
  }
}

output "tunnel_id" {
  value = cloudflare_zero_trust_tunnel_cloudflared.vitrine.id
}

output "tunnel_token" {
  description = "Jeton de cloudflared (à déposer sur la VM web, jamais dans un fichier versionné)."
  value       = data.cloudflare_zero_trust_tunnel_cloudflared_token.vitrine.token
  sensitive   = true
}
