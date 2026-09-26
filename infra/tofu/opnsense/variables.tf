variable "etat_passphrase" {
  description = "Phrase de passe de chiffrement de l'état. Fournie par variable d'environnement."
  type        = string
  sensitive   = true
}

variable "opnsense_uri" {
  description = "URL de l'interface d'OPNsense (joignable via le VPN d'administration)."
  type        = string
  default     = "https://fw01.home.maximebertrand.net"
}

variable "opnsense_api_key" {
  description = "Clé API OPNsense. Fournie par variable d'environnement."
  type        = string
  sensitive   = true
}

variable "opnsense_api_secret" {
  description = "Secret API OPNsense. Fourni par variable d'environnement."
  type        = string
  sensitive   = true
}

variable "interface_parente" {
  description = "Carte réseau d'OPNsense qui porte les VLAN."
  type        = string
}

variable "zones" {
  description = "Zones réseau : VLAN, nom du périphérique VLAN (ex. vlan01) et interface affectée dans OPNsense (ex. opt2)."
  type = map(object({
    vlan         = number
    peripherique = string
    interface    = string
  }))
}

variable "domaine_interne" {
  description = "Zone DNS interne."
  type        = string
  default     = "home.maximebertrand.net"
}

variable "hotes" {
  description = "Machines : enregistrement DNS interne et alias de pare-feu (h_<nom>)."
  type = map(object({
    ip          = string
    description = string
  }))
}

variable "services_internes" {
  description = "Noms de services internes (zone interne) servis par un hôte, ex. le proxy interne."
  type        = map(string) # nom => clé de var.hotes
  default     = {}
}

variable "domaine_public" {
  description = "Domaine des services publiés."
  type        = string
  default     = "maximebertrand.net"
}

variable "noms_publics" {
  description = "Noms publics résolus en interne directement vers un hôte (évite le détour par la box)."
  type        = map(string) # nom => clé de var.hotes
  default     = {}
}

variable "alias_ports" {
  description = "Groupes de ports nommés (alias p_<nom>)."
  type = map(object({
    ports       = list(string)
    description = string
  }))
  default = {}
}

variable "alias_hotes_externes" {
  description = "Hôtes Internet nommés (alias x_<nom>), par nom DNS ou adresse."
  type = map(object({
    contenu     = list(string)
    description = string
  }))
  default = {}
}

variable "regles" {
  description = <<-EOT
    Règles de filtrage, indexées par un identifiant stable. Les champs interface, source et destination
    acceptent un nom de zone (remplacé par le réseau de son interface), un alias ou une valeur OPNsense brute.
  EOT
  type = map(object({
    sequence            = number
    interface           = string
    action              = optional(string, "pass")
    protocole           = optional(string, "TCP")
    source              = optional(string, "any")
    destination         = optional(string, "any")
    destination_inverse = optional(bool, false)
    ports               = optional(string, "")
    journal             = optional(bool, false)
    description         = string
  }))
  default = {}
}

variable "redirections" {
  description = "Redirections de ports entrantes sur le WAN (NAT)."
  type = map(object({
    sequence    = number
    protocole   = optional(string, "TCP")
    port        = string
    cible       = string # clé de var.hotes
    port_cible  = string
    description = string
  }))
  default = {}
}
