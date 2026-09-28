# Comparación de alternativas de despliegue para la API TAIA

**Asignatura:** Arquitectura de Software - Metacurso 202620  
**Proyecto:** TAIA — Task Artificial Intelligence Assistant  
**Pieza evaluada:** API TAIA  
**Alternativas:** Render Web Service y Oracle Cloud Compute VM + Docker  
**Fecha:** Septiembre de 2026

---

# 1. Introducción

Este documento compara dos alternativas de despliegue para una pieza concreta del sistema TAIA: su **API backend desarrollada con FastAPI**.

La comparación se realiza entre:

1. **Render Web Service**, utilizando su instancia Free.
2. **Oracle Cloud Infrastructure (OCI) Compute**, utilizando una máquina virtual AMD `VM.Standard.E5.Flex` y Docker.

La base de datos PostgreSQL utilizada por TAIA se mantiene como una dependencia externa común a ambas alternativas. En ambos escenarios se utiliza **Supabase PostgreSQL**, por lo que la comparación no evalúa el despliegue de la base de datos.

La pieza evaluada es exclusivamente la API, responsable de recibir peticiones HTTP, ejecutar los casos de uso de TAIA y comunicarse con los servicios externos necesarios.

---

# 2. Pieza evaluada

## 2.1 API TAIA

La pieza evaluada corresponde al backend de TAIA, implementado con **FastAPI y Python**.

La API expone endpoints HTTP utilizados por los clientes de TAIA y contiene los módulos funcionales del sistema.

Su arquitectura general para esta evaluación es:

```text
Cliente
   |
   v
API TAIA - FastAPI
   |
   +--------------------+
   |                    |
   v                    v
Módulos TAIA       Supabase PostgreSQL
```

La misma API es desplegada en las dos alternativas para evitar que diferencias en el código afecten la comparación.

---

# 3. Supuestos

Para realizar una comparación reproducible se establecen los siguientes supuestos:

- La pieza evaluada es únicamente la **API TAIA**.
- La API utiliza FastAPI/Python.
- La base de datos PostgreSQL se encuentra en Supabase.
- Supabase es una dependencia externa común a las dos alternativas.
- Las variables sensibles, como `DATABASE_URL`, se proporcionan mediante variables de entorno.
- El código fuente utilizado debe corresponder a la misma versión de TAIA en ambas alternativas.
- Las pruebas deben utilizar los mismos endpoints y cargas.
- La comparación de costos considera principalmente el alojamiento de la API.
- Los costos de Supabase no se atribuyen a ninguna de las dos alternativas porque es una dependencia compartida.
- La alternativa de Oracle utiliza una VM AMD `VM.Standard.E5.Flex` (1 OCPU, 12 GB) con Docker. Esta VM no forma parte de los recursos Always Free (ver 9.2).
- La alternativa de Render utiliza un Web Service Free.

---

# 4. Alternativa A: Render Web Service

## 4.1 Descripción

Render permite desplegar aplicaciones backend como Web Services. FastAPI se encuentra entre los frameworks soportados para este tipo de servicio.

La arquitectura utilizada es:

```text
Internet
   |
   v
Render Web Service
   |
   v
TAIA FastAPI
   |
   v
Supabase PostgreSQL
```

La configuración utilizada para el prototipo fue:

| Elemento | Configuración |
|---|---|
| Servicio | Web Service |
| Aplicación | TAIA API |
| Framework | FastAPI |
| Lenguaje | Python |
| Plan | Free |
| Base de datos | Supabase PostgreSQL |
| Variables de entorno | Configuradas en Render |
| URL | https://taia-backend-latest.onrender.com |

Render permite desplegar Web Services gratuitamente en el plan Free.

## 4.2 Restricciones relevantes

El servicio Free de Render tiene características que afectan directamente el comportamiento de una API:

- 750 horas de instancia gratuitas por workspace cada mes.
- El servicio se suspende después de 15 minutos sin tráfico entrante.
- Cuando llega una nueva petición después de la suspensión, el servicio vuelve a iniciarse.
- Render indica que este arranque puede tardar aproximadamente un minuto.
- El sistema de archivos del servicio es efímero.
- Los Web Services Free no permiten escalar a múltiples instancias.
- Render proporciona TLS administrado y rollbacks para los dos deploys anteriores.

Por lo tanto, el comportamiento después de un período prolongado de inactividad constituye una condición relevante para las pruebas de esta alternativa.

---

# 5. Alternativa B: Oracle Cloud + Docker

## 5.1 Descripción

La segunda alternativa utiliza una máquina virtual de Oracle Cloud Infrastructure sobre la cual se instaló Docker.

La configuración utilizada fue:

| Elemento | Configuración |
|---|---|
| Plataforma | Oracle Cloud Infrastructure |
| Servicio | Compute VM |
| Arquitectura | x86_64 / AMD |
| Shape | VM.Standard.E5.Flex |
| Recursos | 1 OCPU, 12 GB de memoria |
| Sistema operativo | Oracle Linux Server 10.2 |
| Contenedor | Docker |
| Imagen | `ghcr.io/dei0811/taia_backend:v2` |
| Puerto | `8000` |
| Base de datos | Supabase PostgreSQL |

Los únicos shapes de cómputo Always Free de OCI son `VM.Standard.E2.1.Micro` (AMD, 1/8 de OCPU y 1 GB, hasta dos instancias) y `VM.Standard.A1.Flex` (ARM, 2 OCPU y 12 GB en total). Al crear la VM, A1.Flex no tenía capacidad disponible y la consola no ofreció E2.1.Micro, por lo que se utilizó `VM.Standard.E5.Flex`, que **no es Always Free** y se factura por hora.

La arquitectura desplegada es:

```text
Internet
   |
   v
Oracle Cloud VM
   |
   v
Docker
   |
   v
TAIA FastAPI
   |
   v
Supabase PostgreSQL
```

## 5.2 Procedimiento de despliegue

Se creó la máquina virtual y se configuró acceso SSH.

Posteriormente se instaló Docker utilizando los paquetes correspondientes a Oracle Linux.

La imagen de la API se construyó y publicó en GitHub Container Registry:

```text
ghcr.io/dei0811/taia_backend:v2
```

Desde la VM se descargó la imagen:

```bash
sudo docker pull ghcr.io/dei0811/taia_backend:v2
```

El contenedor se ejecutó mediante:

```bash
sudo docker run -d \
  --name taia_backend \
  --env-file ~/taia.env \
  -p 8000:8000 \
  --restart unless-stopped \
  ghcr.io/dei0811/taia_backend:v2
```

La variable de conexión a PostgreSQL se mantuvo fuera de la imagen mediante:

```text
~/taia.env
```

De esta manera, las credenciales no forman parte del repositorio ni de la imagen Docker.

La API fue posteriormente accesible mediante:

```text
http://157.137.215.57:8000/docs
```

---

# 6. Prototipo reproducible

## 6.1 Versión de la API

Para que la comparación sea válida, ambas plataformas utilizaron la misma imagen Docker de la API:

```text
ghcr.io/dei0811/taia_backend:v2
```

Desde que existe el workflow de CD, cada imagen se etiqueta además con los 12 primeros caracteres del SHA del commit, por lo que la versión desplegada se puede rastrear hasta su commit.


# 7. Escenario de prueba

Se define como escenario principal la ejecución de un endpoint HTTP de la API TAIA.

### Escenario S1 — Petición a la API

Para cada plataforma se ejecutan las mismas solicitudes.

Se registran:

- Código HTTP.
- Tiempo de respuesta.
- Disponibilidad.
- Comportamiento después de inactividad.

Ejemplo de medición:

```bash
curl -o /dev/null -s -w \
"HTTP: %{http_code}\nTiempo total: %{time_total}s\n" \
http://HOST:PUERTO/ENDPOINT
```

Las pruebas se deben repetir varias veces para reducir el efecto de una medición aislada.

---

# 8. Prueba de inactividad

Esta prueba es especialmente relevante para Render debido al comportamiento de su plan Free.

## Procedimiento

1. Realizar una petición a la API.
2. Registrar el tiempo de respuesta.
3. No realizar solicitudes durante al menos 15 minutos.
4. Realizar nuevamente la misma petición.
5. Registrar el tiempo de respuesta.
6. Comparar con Oracle Cloud.

Render indica que los Web Services Free se suspenden después de 15 minutos sin tráfico entrante y vuelven a iniciarse cuando reciben una nueva petición. El proceso de reactivación toma aproximadamente un minuto según su documentación.

Oracle, en cambio, mantiene la VM y el contenedor ejecutándose mientras los recursos permanezcan activos.

### Resultados

| Plataforma | Petición normal | Primera petición después de inactividad |
|---|---:|---:|
| Render | 0,14 s | 0,96 s |
| Oracle Cloud | 0,13 s | 0,22 s |

Medición adicional del 27/09/2026 sobre `GET /health`, con el servicio de Render suspendido por inactividad:

| Plataforma | Tiempo de respuesta |
|---|---:|
| Render (`https://taia-backend-latest.onrender.com/health`) | 53,4 s |
| Oracle Cloud (`http://157.137.215.57:8000/health`) | 0,07 s |

Esta segunda medición sí muestra el arranque en frío de Render, cercano al minuto que indica su documentación.


# 9. Costos

## 9.1 Render

El plan Free proporciona 750 horas de instancia por workspace cada mes. Las instancias Free que se encuentran suspendidas no consumen estas horas. Si se consumen las 750 horas, los Web Services Free se suspenden hasta el inicio del siguiente mes.

Por tanto:

| Recurso | Límite Free |
|---|---:|
| Web Service | $0 |
| Horas de instancia | 750 h/mes |
| Memoria | 512 MB |
| CPU | 0.1 CPU |
| Inactividad antes de suspensión | 15 min |
| Almacenamiento local | Efímero |

Render también aplica límites de bandwidth y build pipeline a nivel del workspace. Si no existe un método de pago y se alcanza un límite que generaría cargos, Render puede suspender los servicios correspondientes en lugar de generar el cargo.

### Punto de ruptura

Para una única instancia ejecutándose continuamente:

```text
24 h × 30 días = 720 h/mes
```

Por lo tanto, una única instancia funcionando continuamente durante un mes de 30 días se mantiene dentro de las 750 horas incluidas.

El límite se alcanza al superar las **750 horas mensuales de instancia** del workspace.

---

## 9.2 Oracle Cloud

La VM utilizada, `VM.Standard.E5.Flex` con 1 OCPU y 12 GB, **no forma parte de los recursos Always Free**. Se factura por hora encendida, con precio de lista de 0,03 USD por OCPU-hora y 0,002 USD por GB-hora:

```text
730 h × (1 OCPU × 0,03 + 12 GB × 0,002) USD = 39,42 USD/mes
```

Costo por recurso:

| Recurso | Límite Always Free | Uso de TAIA | Costo |
|---|---:|---:|---:|
| VM `VM.Standard.E5.Flex` | No aplica | 730 h/mes | 39,42 USD/mes |
| Block Volume | 200 GB total | Volumen de arranque de la VM | 0 USD |
| Transferencia saliente | 10 TB/mes | Menos de 1 GB/mes | 0 USD |

La cuenta de OCI exige registrar una tarjeta, y el costo de la VM se carga a ella.

### Punto de ruptura

La VM de cómputo está fuera de la capa gratuita desde la primera hora. Los demás recursos se rompen al superar los 200 GB de Block Volume o los 10 TB/mes de salida.

Para volver a costo cero habría que usar `VM.Standard.A1.Flex` (Always Free) cuando la región tenga capacidad, construyendo la imagen también para ARM64, o `VM.Standard.E2.1.Micro` con solo 1 GB de memoria. El cálculo con el volumen supuesto de TAIA está en [costo_mensual.md](../costo_mensual.md).

---

# 11. Comparación técnica

| Criterio | Render Free | Oracle Cloud + Docker |
|---|---|---|
| Pieza | API TAIA | API TAIA |
| Modelo | Web Service administrado | VM/IaaS |
| Docker | Compatible | Control directo |
| SO administrado por usuario | No | Sí |
| RAM | 512 MB | 12 GB |
| URL pública | Sí | Sí |
| TLS administrado | Sí | Debe configurarse |
| Inactividad | Suspensión después de 15 min | Permanece ejecutándose |
| Control del servidor | Bajo | Alto |
| SSH | No disponible en Free Web Service | Sí |
| Despliegue | Simplificado | Manual |
| Rollback | Dos deploys anteriores | Versiones Docker |
| Operación | Menor carga | Mayor responsabilidad |
| Costo | $0 dentro de límites | 39,42 USD/mes (E5.Flex no es Always Free) |

---

# 12. Procedimiento de reversión

## 12.1 Render

Render proporciona rollback a los dos deploys anteriores más recientes para Free Web Services.

Procedimiento:

```text
Render Dashboard
      ↓
TAIA Web Service
      ↓
Deploys
      ↓
Seleccionar versión anterior
      ↓
Rollback
```

La versión anterior puede restaurarse sin reconstruir manualmente toda la infraestructura.

---

## 12.2 Oracle Cloud

Para Oracle Cloud se recomienda utilizar tags de imagen:

```text
ghcr.io/dei0811/taia_backend:v1
ghcr.io/dei0811/taia_backend:v2
```

Si `v2` presenta un error, se puede volver a `v1`:

```bash
sudo docker pull ghcr.io/dei0811/taia_backend:v1

sudo docker stop taia_backend
sudo docker rm taia_backend

sudo docker run -d \
  --name taia_backend \
  --env-file ~/taia.env \
  -p 8000:8000 \
  --restart unless-stopped \
  ghcr.io/dei0811/taia_backend:v1
```

De esta forma el rollback no depende del código fuente presente en la VM.


# 13. Limitaciones de la evaluación

La comparación presenta algunas limitaciones:

1. Las pruebas de latencia dependen también de la ubicación del cliente y de la conexión de red.
2. Supabase es un servicio externo compartido por las dos alternativas.
3. Las pruebas realizadas corresponden a una API pequeña y no representan necesariamente el comportamiento bajo carga elevada.
4. El plan Free de Render presenta comportamiento de suspensión por inactividad, por lo que sus tiempos de respuesta no son directamente equivalentes a los de una instancia permanentemente activa.
5. La VM de Oracle requiere mayor configuración y mantenimiento que un Web Service administrado.
6. Las mediciones de rendimiento deben interpretarse como resultados del prototipo y no como benchmarks generales de las plataformas.

---

# 14. ADR-001 — Despliegue de la API TAIA

## Estado

**Aceptado**

## Contexto

TAIA requiere desplegar su API FastAPI de forma pública para permitir el consumo de sus endpoints.

Se evaluaron dos alternativas que pueden utilizarse para esta pieza:

- Render Web Service Free.
- Oracle Cloud Compute `VM.Standard.E5.Flex` + Docker.

La base de datos PostgreSQL se mantiene en Supabase en ambos escenarios.

## Alternativas consideradas

### Alternativa 1 — Render

Render proporciona un Web Service administrado, con despliegue simplificado, URL pública, TLS administrado y mecanismos de rollback. Su plan Free presenta suspensión después de 15 minutos sin tráfico y un límite de 750 horas mensuales por workspace.

### Alternativa 2 — Oracle Cloud

Oracle Cloud proporciona una VM AMD sobre la cual se ejecuta Docker. Esto permite controlar directamente el sistema operativo, el runtime y el ciclo de vida del contenedor. La VM `VM.Standard.E5.Flex` no forma parte de los recursos Always Free de OCI: A1.Flex no tenía capacidad y E2.1.Micro no estaba disponible, y su costo es de 39,42 USD/mes.

## Decisión

Para el prototipo de TAIA se utiliza **Oracle Cloud Compute + Docker** como alternativa principal de despliegue de la API.

La decisión se fundamenta en los requisitos definidos para el prototipo:

- disponibilidad continua de la instancia sin depender del spin-down de un Web Service Free;
- control directo sobre Docker;
- acceso SSH al servidor;
- posibilidad de administrar el sistema operativo;
- posibilidad de mantener las imágenes versionadas en GHCR.

Render se mantiene como alternativa viable cuando se prioriza la reducción de tareas operativas y la simplicidad del proceso de despliegue.

## Consecuencias positivas

- La API puede ejecutarse continuamente en la VM.
- Se dispone de acceso directo al sistema operativo.
- Docker permite controlar explícitamente la versión desplegada.
- GHCR permite distribuir las imágenes de la API.

## Consecuencias negativas

- El equipo debe administrar el sistema operativo.
- La configuración de red y firewall es responsabilidad del despliegue.
- HTTPS y DNS requieren configuración adicional.
- Los rollbacks deben gestionarse mediante versiones de imágenes Docker.
- Se requiere supervisar el uso de recursos.
- La VM `VM.Standard.E5.Flex` no es Always Free: cuesta 39,42 USD/mes a precio de lista.

---

# 15. Conclusión

La comparación se realizó sobre una pieza concreta: **la API FastAPI de TAIA**.

Render proporciona una experiencia de despliegue más administrada, mientras que Oracle Cloud proporciona mayor control sobre la máquina virtual y el entorno Docker.

En el escenario evaluado, Render presenta como característica relevante la suspensión del Web Service Free después de 15 minutos de inactividad y la posterior reactivación ante una nueva solicitud.

Oracle Cloud permite ejecutar directamente el contenedor Docker en una VM siempre encendida. La VM utilizada, `VM.Standard.E5.Flex`, no es Always Free y cuesta 39,42 USD/mes; el cómputo Always Free (A1.Flex) no tenía capacidad disponible al crearla.

Los resultados de rendimiento obtenidos durante las pruebas deben interpretarse junto con estas diferencias operativas y económicas. La elección documentada para este prototipo es Oracle Cloud Compute + Docker, debido a los requisitos definidos de control del entorno y ejecución continua de la API.

---

# 16. Checklist de entrega

Antes de entregar:

- [X] Pieza concreta: **API TAIA**
- [X] Render probado
- [X] Oracle Cloud probado
- [X] Supabase identificado como dependencia común
- [X] Supuestos documentados
- [X] Prototipo reproducible
- [X] Evidencia propia de Render
- [X] Evidencia propia de Oracle
- [X] Mediciones de latencia
- [X] Prueba después de 15 min de inactividad en Render
- [X] Costos de ambas alternativas
- [X] Punto de ruptura de capa gratuita
- [X] Procedimiento de rollback de Render
- [X] Procedimiento de rollback de Oracle
- [X] ADR
- [X] No incluir contraseñas, tokens ni `DATABASE_URL` completa