# Terraform para TAIA en OCI

Esta configuración prepara la adopción del **VPS existente** como
`oci_core_instance.taia`. Es opcional e independiente del despliegue de TAIA.
No instala Docker ni Dokploy ni despliega la aplicación: GitHub Actions ejecuta
CI y solicita el despliegue por la API de Dokploy, que construye y ejecuta
`docker-compose.yml`. Consultar la [guía de Dokploy](../docs/despliegue-dokploy.md).
Terraform se comunica con la API de OCI para administrar infraestructura;
no abre conexiones SSH al servidor.

La primera etapa administra la instancia y consulta sus IP actuales. La VCN,
subnet, VNIC, IP pública, Internet Gateway, rutas y reglas de seguridad existentes
**no quedan administrados como recursos independientes** al importar el VPS.
Para incorporarlos después, hay que inventariar sus valores reales, declarar
cada recurso e importarlo antes de aplicar cambios. No se crean redes ni reglas
de firewall de ejemplo sobre la infraestructura en producción.

## Archivos

| Archivo | Propósito |
| --- | --- |
| `provider.tf` | Terraform >= 1.5 y < 2.0, provider oficial `oracle/oci` 7.x y autenticación externa. |
| `.terraform.lock.hcl` | Versión seleccionada del provider (7.32.0) y sus checksums; se conserva en Git. |
| `main.tf` | Recurso del VPS y bloque de importación por su OCID. |
| `variables.tf` | Variables y comentarios que indican dónde obtener los datos de OCI. |
| `terraform.tfvars.example` | Plantilla para completar en una copia local. |
| `outputs.tf` | OCID, nombre, compartment e IP pública/privada del VPS. |

## 1. Configurar autenticación local

Usar una API key de OCI y un usuario con permisos sobre la instancia y su red.
Guardar la clave privada **fuera del repositorio**. En `~/.oci/config`, configurar
el perfil que utilizará Terraform:

```ini
[DEFAULT]
# OCI > Tenancy details > OCID
tenancy=REEMPLAZAR_OCID_DE_TENANCY
# OCI > usuario propietario de la API key > OCID
user=REEMPLAZAR_OCID_DEL_USUARIO
# OCI > usuario > API keys > Fingerprint
fingerprint=REEMPLAZAR_HUELLA_DE_API_KEY
# Ruta absoluta de la clave privada de API, no la clave SSH del VPS
key_file=/RUTA/ABSOLUTA/FUERA/DEL/REPOSITORIO/oci_api_key.pem
# Identificador de la región del VPS; también se configura en terraform.tfvars
region=REEMPLAZAR_REGION
```

En Windows nativo, el archivo está en `%USERPROFILE%\.oci\config`; para rutas de
clave se pueden usar barras `/`. Si ejecutas Terraform en WSL, usa el archivo
`~/.oci/config` del usuario **de WSL** y una ruta de clave accesible desde Linux.
La región de `terraform.tfvars` prevalece sobre la del perfil. Si la clave está
cifrada, proporciona su contraseña mediante `TF_VAR_private_key_password`,
reconocida por el provider OCI, sin guardarla en el repositorio.

## 2. Completar los datos del VPS

Desde la raíz del repositorio, en PowerShell:

```powershell
Set-Location terraform
Copy-Item terraform.tfvars.example terraform.tfvars
```

En Bash/WSL:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

No sobrescribir una copia local que ya hayas completado. Editar `terraform.tfvars`
y reemplazar todos los marcadores según sus comentarios. Obtener de OCI:

- Región y OCID del VPS existente.
- OCID del compartment actual (o tenancy si está en el raíz).
- Availability domain completo, nombre visible y shape actuales.
- Para un shape Flex, OCPU y RAM actuales en `instance_shape_config`.

Las credenciales van en el perfil externo; los valores del entorno van en
`terraform.tfvars`, que Git ignora. No cambiar los `.tf` para pegar secretos.

## 3. Inicializar y validar

Ejecutar desde `terraform/`:

```bash
terraform init
terraform fmt -check
terraform validate
```

`init` instala la versión del lockfile. No usar `init -upgrade` para esta adopción;
las actualizaciones del provider deben revisarse aparte. `validate` comprueba la
configuración, pero no verifica las credenciales ni que los datos coincidan con OCI.

## 4. Importar el VPS existente

Sustituir el marcador por **el mismo OCID** de `instance_ocid` en `terraform.tfvars`:

```bash
terraform import oci_core_instance.taia "REEMPLAZAR_OCID_DEL_VPS"
terraform state list
terraform state show oci_core_instance.taia
terraform plan
```

`terraform import` registra el VPS en el estado local; no crea otra instancia ni
reconfigura el servidor. El recurso debe aparecer en `terraform state list`.
`state show` puede mostrar metadata sensible: no publicar su salida.

El bloque `import` de `main.tf` también permite la importación declarativa. Si
ejecutas `plan` antes del comando anterior, debe proponer importar la instancia
indicada, con **0 creaciones y 0 destrucciones**. Se conserva tras la importación;
cuando el recurso ya está en el estado, no se vuelve a importar. No modificar su
OCID para cambiar de servidor: usar un estado separado para otro entorno.

## 5. Revisar el primer plan

El objetivo es que no haya cambios en recursos existentes. Pueden aparecer
nuevas salidas de Terraform aunque no cambie la infraestructura. Comparar la
configuración con `terraform state show oci_core_instance.taia` y ajustar los
valores locales hasta que el plan no proponga modificaciones inesperadas.

`prevent_destroy` bloquea eliminaciones y reemplazos mientras se conserve el
recurso en la configuración, pero **no bloquea actualizaciones** ni protege un
recurso cuyo bloque se eliminó. Si aparece un reemplazo, un cambio de shape,
compartment, red, metadata o cualquier otro cambio inesperado, corregir la
configuración antes de aplicar. No usar `ignore_changes = all` para ocultar esas
diferencias. La ausencia de cambios solo puede comprobarse con el VPS real.

## 6. Cambios posteriores

Después de importar y reconciliar la configuración:

```bash
terraform fmt
terraform validate
terraform plan -out=review.tfplan
# Revisar el plan completo antes del siguiente comando.
terraform apply review.tfplan
```

El plan guardado contiene exactamente los cambios revisados. No ejecutar
`apply` como parte del despliegue de la aplicación. Para incorporar recursos de
red, declarar sus propiedades actuales e importarlos por sus OCID; considerar
que pueden estar compartidos con otros servicios.

## Estado y secretos

Se utiliza el backend local de Terraform. `terraform.tfstate`, sus copias,
`*.tfvars`, `*.tfvars.json`, `*.tfplan`, logs de fallos y `.terraform/` están
ignorados por Git. Los `.tf`, esta guía, la plantilla y el lockfile sí se versionan.
Conservar copias protegidas del estado y no compartir planes ni estados en
issues o logs públicos. Evitar operaciones concurrentes desde distintas copias
locales; antes de trabajar en equipo, configurar un backend compartido con
control de acceso y bloqueo.

## Referencias

- [Autenticación del provider OCI](https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm).
- [Instancia OCI e importación (provider 7.32.0)](https://registry.terraform.io/providers/oracle/oci/7.32.0/docs/resources/core_instance).
- [Protección del ciclo de vida en Terraform](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle).
