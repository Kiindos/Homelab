output "vms" {
  description = "VM créées : identifiant, VLAN et adresse."
  value = {
    for nom, vm in proxmox_virtual_environment_vm.vm : nom => {
      vmid = vm.vm_id
      vlan = var.vms[nom].vlan
      ipv4 = split("/", var.vms[nom].ipv4)[0]
    }
  }
}
