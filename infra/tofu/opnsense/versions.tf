terraform {
  required_version = ">= 1.10.0"

  required_providers {
    opnsense = {
      source  = "browningluke/opnsense"
      version = "~> 0.26"
    }
  }

  # État hors du dépôt public, chemin fourni à l'init (-backend-config=path=…).
  backend "local" {}

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
