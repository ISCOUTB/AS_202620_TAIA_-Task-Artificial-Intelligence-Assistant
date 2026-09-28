# Adopcion del VPS existente. Primero ejecutar terraform import como indica
# README.md. Este bloque tambien permite que un plan sin estado proponga
# importar el OCID indicado en vez de crear una instancia nueva.
# Conservarlo despues de importar: no vuelve a importar un recurso en el estado.
import {
  to = oci_core_instance.taia
  id = var.instance_ocid
}

resource "oci_core_instance" "taia" {
  # Copiar los valores ACTUALES de OCI en terraform.tfvars; no elegir una
  # configuracion nueva durante la adopcion (podria causar cambios/reemplazos).
  availability_domain = var.instance_availability_domain
  compartment_id      = var.compartment_ocid
  display_name        = var.instance_display_name
  shape               = var.instance_shape

  # Para shapes Flex, declarar las OCPU y RAM actuales en instance_shape_config.
  # Para shapes fijos, dejar null y conservar la configuracion leida de OCI.
  dynamic "shape_config" {
    for_each = var.instance_shape_config == null ? [] : [var.instance_shape_config]
    content {
      ocpus         = shape_config.value.ocpus
      memory_in_gbs = shape_config.value.memory_in_gbs
    }
  }

  # Esta primera adopcion administra la instancia. La VCN, subnet, VNIC, IP,
  # gateway y reglas existentes no se crean ni se importan automaticamente.
  # source_details, create_vnic_details y metadata se leen del VPS al importar;
  # no se declaran valores de arranque nuevos ni se ejecutan provisioners.
  # Antes de administrar la red, declarar e importar sus recursos por separado.

  lifecycle {
    # Bloquea destrucciones y reemplazos mientras este recurso siga declarado.
    # No bloquea actualizaciones: revisar siempre terraform plan.
    prevent_destroy = true
  }
}
