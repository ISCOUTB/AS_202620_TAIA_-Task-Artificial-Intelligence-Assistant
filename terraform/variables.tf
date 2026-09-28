# Completar terraform.tfvars a partir de terraform.tfvars.example.
# Los valores reales van en ese archivo local ignorado por Git.

variable "oci_config_profile" {
  description = "Nombre del perfil de autenticacion en ~/.oci/config."
  type        = string
  default     = "DEFAULT"
  nullable    = false

  # CAMBIAR si guardaste las credenciales OCI en un perfil distinto de DEFAULT.
}

variable "oci_region" {
  description = "Identificador de la region OCI donde existe el VPS."
  type        = string
  nullable    = false

  # OCI: selector de region de la consola; usar el identificador (ej. us-ashburn-1).
  # Debe corresponder a la region de la instancia, no necesariamente la home region.
}

variable "instance_ocid" {
  description = "OCID del VPS existente que se incorporara al estado."
  type        = string
  nullable    = false

  # OCI: Compute > Instances > tu VPS > OCID > Copy.
  validation {
    condition     = can(regex("^ocid1\\.instance\\.", var.instance_ocid))
    error_message = "instance_ocid debe ser el OCID de una instancia OCI existente."
  }
}

variable "compartment_ocid" {
  description = "OCID del compartment al que pertenece actualmente el VPS."
  type        = string
  nullable    = false

  # OCI: ver el compartment en la instancia y copiar su OCID en Identity > Compartments.
  # Si el VPS esta en el compartment raiz, usar el OCID de la tenancy.
  validation {
    condition     = can(regex("^ocid1\\.(compartment|tenancy)\\.", var.compartment_ocid))
    error_message = "Usa el OCID del compartment o de la tenancy si es el compartment raiz."
  }
}

variable "instance_availability_domain" {
  description = "Availability domain actual de la instancia, incluido el prefijo de la tenancy."
  type        = string
  nullable    = false

  # OCI: Compute > Instances > tu VPS > Instance information > Availability domain.
  # Copiar el valor completo, por ejemplo AbCd:US-ASHBURN-AD-1; no solo AD-1.
}

variable "instance_display_name" {
  description = "Nombre visible actual del VPS en OCI."
  type        = string
  nullable    = false

  # OCI: Compute > Instances > copiar exactamente el nombre actual de tu VPS.
}

variable "instance_shape" {
  description = "Shape actual del VPS; no cambiarlo durante la importacion."
  type        = string
  nullable    = false

  # OCI: Compute > Instances > tu VPS > Shape (ej. VM.Standard.A1.Flex).
}

variable "instance_shape_config" {
  description = "OCPU y RAM actuales para shapes Flex; null para shapes fijos."
  type = object({
    ocpus         = number
    memory_in_gbs = number
  })
  default = null

  # OCI: detalles del shape de la instancia. Copiar OCPU (no vCPU) y RAM en GB.
  validation {
    condition = var.instance_shape_config == null ? true : (
      var.instance_shape_config.ocpus > 0 && var.instance_shape_config.memory_in_gbs > 0
    )
    error_message = "Las OCPU y la memoria deben ser mayores que cero."
  }
}
