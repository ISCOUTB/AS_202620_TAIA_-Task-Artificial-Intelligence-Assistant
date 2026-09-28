output "service_id" {
  description = "ID del Web Service para consultar despliegues en Render."
  value       = render_web_service.taia.id
}

output "service_url" {
  description = "URL HTTPS que deben usar los clientes de TAIA."
  value       = render_web_service.taia.url
}

output "health_url" {
  description = "Endpoint de health; no comprueba operaciones de base de datos."
  value       = "${render_web_service.taia.url}/health"
}

output "docs_url" {
  description = "Documentacion Swagger del backend."
  value       = "${render_web_service.taia.url}/docs"
}
