terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    render = {
      source  = "render-oss/render"
      version = "= 1.9.1"
    }
  }
}

# Autenticacion externa: RENDER_API_KEY y RENDER_OWNER_ID.
provider "render" {
  # El workflow CD despliega los cambios tras CI; evitar despliegues duplicados.
  skip_deploy_after_service_update = true
}
