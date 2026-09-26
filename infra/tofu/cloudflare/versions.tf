terraform {
  required_version = ">= 1.10.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.26"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # État hors du dépôt public, chemin fourni à l'init (-backend-config=path=…).
  backend "local" {}

  # L'état contient le secret du tunnel : il est chiffré au repos.
  encryption {
    key_provider "pbkdf2" "phrase" {
      passphrase = var.etat_passphrase
    }
    method "aes_gcm" "etat" {
      keys = key_provider.pbkdf2.phrase
    }
    state {
      method   = method.aes_gcm.etat
      enforced = true
    }
    plan {
      method   = method.aes_gcm.etat
      enforced = true
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
