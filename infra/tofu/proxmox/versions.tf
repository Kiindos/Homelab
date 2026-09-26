terraform {
  required_version = ">= 1.10.0"

  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.114"
    }
  }

  # L'état est conservé hors de ce dépôt public ; le chemin est fourni à l'init
  # (-backend-config=path=…), voir docs/runbooks côté interne.
  backend "local" {}

  # L'état contient des secrets (jetons, données cloud-init) : il est chiffré au repos.
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
