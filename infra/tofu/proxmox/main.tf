# Point de départ : lecture des nœuds pour valider la connexion à l'API.
# Les VM (OPNsense, cloudflared, k3s…) seront ajoutées ici sous forme de modules.
data "proxmox_virtual_environment_nodes" "all" {}

output "nodes" {
  description = "Nœuds Proxmox détectés."
  value       = data.proxmox_virtual_environment_nodes.all.names
}
