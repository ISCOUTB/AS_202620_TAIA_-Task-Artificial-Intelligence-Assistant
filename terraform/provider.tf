terraform {
  # Los bloques import requieren Terraform 1.5 o superior.
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 7.0"
    }
  }
}

provider "oci" {
  auth                = "APIKey"
  config_file_profile = var.oci_config_profile
  region              = var.oci_region

  # COMPLETAR FUERA DEL REPOSITORIO: ~/.oci/config (en el sistema que ejecuta
  # Terraform). El perfil necesita estos valores obtenidos de OCI:
  # tenancy     = OCID de la tenancy (Administration > Tenancy details).
  # user        = OCID del usuario que tiene la API key.
  # fingerprint = huella de la API key (User settings > API keys).
  # key_file    = ruta absoluta de la clave privada de esa API key.
  # region      = identificador de la region donde esta el VPS.
  # No pegar la clave privada ni credenciales en estos archivos .tf.
}
