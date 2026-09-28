# Root independiente: nunca usar aqui el estado de terraform/ (OCI).
resource "render_web_service" "taia" {
  name              = var.service_name
  plan              = var.plan
  region            = var.region
  health_check_path = "/health"
  num_instances     = 1

  runtime_source = {
    docker = {
      repo_url        = var.repository_url
      branch          = var.branch
      dockerfile_path = "backend/Dockerfile"
      context         = "."
      # GitHub Actions CD es el unico disparador para nuevos commits.
      auto_deploy_trigger = "off"
    }
  }

  env_vars = {
    for name, value in merge(var.additional_environment_variables, {
      DATABASE_URL    = var.database_url
      TAIA_JWT_SECRET = var.jwt_secret
    }) : name => { value = value }
  }

  lifecycle {
    prevent_destroy = true
  }
}
