output "instance_ocid" {
  description = "OCID del VPS administrado tras la importacion."
  value       = oci_core_instance.taia.id
}

output "instance_display_name" {
  description = "Nombre visible del VPS en OCI."
  value       = oci_core_instance.taia.display_name
}

output "public_ip" {
  description = "IP publica actual de la VNIC primaria, si tiene una asignada."
  value       = oci_core_instance.taia.public_ip
}

output "private_ip" {
  description = "IP privada actual de la VNIC primaria."
  value       = oci_core_instance.taia.private_ip
}

output "compartment_ocid" {
  description = "Compartment que contiene el VPS."
  value       = oci_core_instance.taia.compartment_id
}
