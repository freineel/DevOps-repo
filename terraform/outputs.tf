output "app_url" {
  description = "URL of the app on this machine."
  value       = "http://localhost:${var.host_port}"
}

output "health_url" {
  description = "Liveness endpoint, quick check if the app is up."
  value       = "http://localhost:${var.host_port}/health"
}

output "web_container_name" {
  description = "Name of the app container, for docker logs."
  value       = docker_container.web.name
}
