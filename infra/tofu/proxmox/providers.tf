provider "proxmox" {
  endpoint  = var.proxmox_endpoint
  api_token = var.proxmox_api_token # format : "user@pam!tokenid=secret"
  insecure  = var.proxmox_insecure

  ssh {
    agent    = true
    username = "root"
  }
}
