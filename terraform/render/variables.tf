variable "service_name" {
  description = "Nombre del Web Service de TAIA en Render."
  type        = string
  default     = "taia-backend"
  nullable    = false
}

variable "repository_url" {
  description = "Repositorio al que la integracion GitHub de Render debe tener acceso."
  type        = string
  default     = "https://github.com/ISCOUTB/AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant"
  nullable    = false
}

variable "branch" {
  description = "Rama desplegada tras CI; usar migrate_to_render para la validacion inicial."
  type        = string
  default     = "main"
  nullable    = false
}

variable "region" {
  description = "Region de Render; elegir segun la ubicacion de PostgreSQL."
  type        = string
  default     = "oregon"
  nullable    = false

  validation {
    condition     = contains(["frankfurt", "ohio", "oregon", "singapore", "virginia"], var.region)
    error_message = "Selecciona una region admitida por Render."
  }
}

variable "plan" {
  description = "Plan de computo del Web Service. starter es de pago; revisar antes de aplicar."
  type        = string
  default     = "starter"
  nullable    = false
}

variable "database_url" {
  description = "URL del PostgreSQL existente o migrado; proporcionar mediante TF_VAR_database_url."
  type        = string
  sensitive   = true
  nullable    = false

  validation {
    condition     = can(regex("^postgresql(\\+psycopg)?://", var.database_url))
    error_message = "Usa postgresql:// o postgresql+psycopg:// para SQLAlchemy y psycopg."
  }
}

variable "jwt_secret" {
  description = "Secreto JWT de produccion; conservar el de OCI para mantener las sesiones."
  type        = string
  sensitive   = true
  nullable    = false

  validation {
    condition     = length(trimspace(var.jwt_secret)) >= 32 && var.jwt_secret != "dev-only-change-me-please-set-a-real-secret"
    error_message = "Configura un secreto JWT de produccion de al menos 32 caracteres."
  }
}

variable "additional_environment_variables" {
  description = "Variables opcionales: GEMINI_API_KEY, GEMINI_MODEL, TAIA_TELEGRAM_BOT_TOKEN y TAIA_TELEGRAM_BOT_USERNAME."
  type        = map(string)
  default     = {}
  sensitive   = true
  nullable    = false
}
