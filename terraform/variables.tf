# Everything that can differ between machines is a variable, not a hard-coded
# value. Defaults are for local development only.

variable "name_prefix" {
  type        = string
  description = "Prefix for the container, network and volume names."
  default     = "expense-tracker-tf"
}

variable "host_port" {
  type        = number
  description = "Port on the host that is mapped to the app port 8000."
  # 8080 instead of 8000, so it does not collide with docker compose.
  default = 8080

  validation {
    condition     = var.host_port > 1024 && var.host_port <= 65535
    error_message = "host_port must be an unprivileged port between 1025 and 65535."
  }
}

variable "image_tag" {
  type        = string
  description = "Tag of the local image expense-tracker:<tag> that is started."
  # "local" is the tag that "make docker-build" creates.
  default = "local"
}

variable "app_version" {
  type        = string
  description = "Version the app reports on /health."
  default     = "1.0.0-terraform"
}

variable "log_level" {
  type        = string
  description = "Log level of the app."
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.log_level)
    error_message = "log_level must be one of DEBUG, INFO, WARNING, ERROR."
  }
}

variable "db_password" {
  type        = string
  description = "Password of the Postgres user. Set it in terraform.tfvars."
  # Same local-only default as in docker-compose.yml.
  default = "changeme"
  # sensitive: Terraform hides the value in plan and apply output.
  # It is still stored in plain text in the state file.
  sensitive = true
}
