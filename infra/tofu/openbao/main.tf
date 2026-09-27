# Configuration du coffre OpenBao : moteur de secrets, politiques et méthodes de connexion.

resource "vault_mount" "homelab" {
  path        = "homelab"
  type        = "kv"
  options     = { version = "2" }
  description = "Secrets du homelab (clé/valeur versionné)"
}

resource "vault_kv_secret_backend_v2" "homelab" {
  mount        = vault_mount.homelab.path
  max_versions = 20
}

resource "vault_policy" "admin" {
  name   = "admin"
  policy = file("${path.module}/politiques/admin.hcl")
}

resource "vault_policy" "lecture_plateforme" {
  name   = "lecture-plateforme"
  policy = file("${path.module}/politiques/lecture-plateforme.hcl")
}

# --- Connexion des personnes : SSO Authelia (OpenID Connect) ----------------------------------------

resource "vault_jwt_auth_backend" "oidc" {
  path               = "oidc"
  type               = "oidc"
  description        = "Connexion par le SSO du homelab (Authelia, double authentification)"
  oidc_discovery_url = var.oidc_emetteur
  oidc_client_id     = "openbao"
  oidc_client_secret = var.oidc_secret
  default_role       = "admin"

  tune {
    listing_visibility = "unauth" # bouton de connexion affiché dans l'interface web
    default_lease_ttl  = "1h"
    max_lease_ttl      = "8h"
    token_type         = "default-service"
  }
}

resource "vault_jwt_auth_backend_role" "admin" {
  backend      = vault_jwt_auth_backend.oidc.path
  role_name    = "admin"
  role_type    = "oidc"
  user_claim   = "preferred_username"
  groups_claim = "groups"
  bound_claims = { groups = var.groupe_admins }
  oidc_scopes  = ["openid", "profile", "email", "groups"]
  allowed_redirect_uris = [
    "https://${var.nom_coffre}:8200/ui/vault/auth/oidc/oidc/callback",
    "http://localhost:8250/oidc/callback", # CLI : bao login -method=oidc
  ]
  token_policies = [vault_policy.admin.name]
  token_ttl      = 3600
  token_max_ttl  = 28800
}

# --- Connexion des machines : AppRole (Semaphore) -----------------------------------------------------

resource "vault_auth_backend" "approle" {
  type        = "approle"
  description = "Connexion des outils d'automatisation"
}

resource "vault_approle_auth_backend_role" "semaphore" {
  backend               = vault_auth_backend.approle.path
  role_name             = "semaphore"
  token_policies        = [vault_policy.lecture_plateforme.name]
  token_ttl             = 1800
  token_max_ttl         = 3600
  secret_id_bound_cidrs = var.semaphore_sources
  token_bound_cidrs     = var.semaphore_sources
}
