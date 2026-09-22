# Tunnel du site vitrine — voir docs/adr/0002-cloudflare-tunnel.md
# Syntaxe du provider cloudflare v5 : vérifier la doc du registre en cas de montée de version.

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
    ingress = [
      {
        hostname = var.vitrine_domain
        service  = var.site_origin
      },
      {
        hostname = "status.${var.vitrine_domain}"
        service  = var.status_origin
      },
      {
        service = "http_status:404"
      },
    ]
  }
}

locals {
  tunnel_cname = "${cloudflare_zero_trust_tunnel_cloudflared.vitrine.id}.cfargotunnel.com"
}

resource "cloudflare_dns_record" "apex" {
  zone_id = var.vitrine_zone_id
  name    = var.vitrine_domain
  type    = "CNAME"
  content = local.tunnel_cname
  proxied = true
  ttl     = 1
}

resource "cloudflare_dns_record" "status" {
  zone_id = var.vitrine_zone_id
  name    = "status.${var.vitrine_domain}"
  type    = "CNAME"
  content = local.tunnel_cname
  proxied = true
  ttl     = 1
}

output "tunnel_id" {
  value = cloudflare_zero_trust_tunnel_cloudflared.vitrine.id
}
