provider "opnsense" {
  uri        = var.opnsense_uri
  api_key    = var.opnsense_api_key
  api_secret = var.opnsense_api_secret

  # Certificat auto-signé d'OPNsense (nom « OPNsense.internal ») : la vérification est désactivée,
  # mais la connexion passe dans le tunnel WireGuard, qui se termine sur le pare-feu lui-même.
  # À retirer quand l'interface web aura un certificat Let's Encrypt.
  allow_insecure = true
}
