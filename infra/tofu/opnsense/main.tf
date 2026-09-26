# Réseau, DNS interne et filtrage d'OPNsense.
# Le détail (adresses, VLAN, règles) est tenu dans le dépôt privé : ce code ne fait que l'appliquer.
# Limite de l'API : l'affectation d'un VLAN à une interface (optN) se fait dans l'interface web.

locals {
  # Un nom de zone est remplacé par l'identifiant de son interface : « opt2 » désigne le réseau de l'interface.
  interface_de = { for nom, zone in var.zones : nom => zone.interface }
}

# --- VLAN ---------------------------------------------------------------------------------------

resource "opnsense_interfaces_vlan" "zone" {
  for_each = var.zones

  parent      = var.interface_parente
  tag         = each.value.vlan
  device      = each.value.peripherique
  description = each.key
}

# --- DNS interne --------------------------------------------------------------------------------

resource "opnsense_unbound_host_override" "hote" {
  for_each = var.hotes

  hostname    = each.key
  domain      = var.domaine_interne
  type        = "A"
  server      = each.value.ip
  description = each.value.description
}

resource "opnsense_unbound_host_override" "service" {
  for_each = var.services_internes

  hostname    = each.key
  domain      = var.domaine_interne
  type        = "A"
  server      = var.hotes[each.value].ip
  description = "Service ${each.key}, servi par ${each.value}"
}

resource "opnsense_unbound_host_override" "public" {
  for_each = var.noms_publics

  hostname    = each.key
  domain      = var.domaine_public
  type        = "A"
  server      = var.hotes[each.value].ip
  description = "Nom public ${each.key}.${var.domaine_public}, résolu en interne vers ${each.value}"
}

# --- Alias ----------------------------------------------------------------------------------------

resource "opnsense_firewall_alias" "hote" {
  for_each = var.hotes

  name        = "h_${replace(each.key, "-", "_")}"
  type        = "host"
  content     = [each.value.ip]
  description = each.value.description
}

resource "opnsense_firewall_alias" "ports" {
  for_each = var.alias_ports

  name        = "p_${each.key}"
  type        = "port"
  content     = each.value.ports
  description = each.value.description
}

resource "opnsense_firewall_alias" "externe" {
  for_each = var.alias_hotes_externes

  name        = "x_${each.key}"
  type        = "host"
  content     = each.value.contenu
  description = each.value.description
}

resource "opnsense_firewall_alias" "prives" {
  name        = "n_prives"
  type        = "network"
  content     = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
  description = "Réseaux privés (RFC 1918) : « Internet » = tout sauf ces réseaux"
}

# --- Filtrage -----------------------------------------------------------------------------------

resource "opnsense_firewall_filter" "regle" {
  for_each = var.regles

  sequence    = each.value.sequence
  description = "${each.value.description} [${each.key}]"

  interface = {
    interface = [lookup(local.interface_de, each.value.interface, each.value.interface)]
  }

  filter = {
    action      = each.value.action
    direction   = "in"
    ip_protocol = "inet"
    protocol    = each.value.protocole
    quick       = true
    log         = each.value.journal

    source = {
      net = lookup(local.interface_de, each.value.source, each.value.source)
    }

    destination = {
      net    = lookup(local.interface_de, each.value.destination, each.value.destination)
      invert = each.value.destination_inverse
      port   = each.value.ports
    }
  }

  depends_on = [
    opnsense_firewall_alias.hote,
    opnsense_firewall_alias.ports,
    opnsense_firewall_alias.externe,
    opnsense_firewall_alias.prives,
  ]
}

# --- Redirections entrantes ---------------------------------------------------------------------

resource "opnsense_firewall_nat_port_forward" "redirection" {
  for_each = var.redirections

  sequence = each.value.sequence
  # L'API n'accepte ici que lettres, chiffres, espaces et points.
  description = "${each.value.description} ${each.key}"
  interface   = ["wan"]
  protocol    = lower(each.value.protocole) # OPNsense l'enregistre en minuscules
  ip_protocol = "inet"

  destination = {
    net  = "wanip"
    port = each.value.port
  }

  target = {
    ip   = opnsense_firewall_alias.hote[each.value.cible].name
    port = each.value.port_cible
  }
}
