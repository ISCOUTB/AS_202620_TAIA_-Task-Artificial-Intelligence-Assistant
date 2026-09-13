# 4. Estrategia de solución

TAIA adopta un **monolito modular con organización hexagonal en los módulos que presentan dependencias externas relevantes**. Esta estrategia busca mantener una arquitectura sencilla para el MVP, evitando la complejidad operativa de una arquitectura distribuida, mientras establece límites que permitan evolucionar el sistema y sustituir dependencias externas cuando sea necesario.

## 4.1. Estilo arquitectónico

El sistema se implementará como un único monolito desplegable, dividido en módulos con responsabilidades claramente definidas.

Dentro de los módulos que interactúan con sistemas externos se utilizará el principio de **puertos y adaptadores**. Los puertos definirán las interfaces que necesita la lógica de negocio, mientras que los adaptadores contendrán los detalles específicos de tecnologías y proveedores externos.

Las principales dependencias externas consideradas son:

- Telegram Bot API como canal de comunicación.
- Gemini como proveedor inicial de inteligencia artificial.
- PostgreSQL como mecanismo de persistencia.

La lógica de negocio no dependerá directamente de las APIs concretas de estos proveedores cuando exista una probabilidad relevante de sustitución.

## 4.2. Principios arquitectónicos

### Separación de responsabilidades

Cada módulo tendrá una responsabilidad definida y deberá evitar dependencias innecesarias sobre otros módulos.

### Aislamiento de dependencias externas

Las integraciones con servicios externos se realizarán mediante interfaces y adaptadores cuando su sustitución o evolución sea relevante para el sistema.

### Dominio independiente de infraestructura

Las reglas de negocio no deberán depender directamente de detalles de Telegram, Gemini o PostgreSQL.

### Validación antes de persistencia

La información interpretada por el servicio de inteligencia artificial deberá ser validada por el backend antes de modificar la información persistida.

### Seguridad por contexto de usuario

Las operaciones sobre información académica deberán ejecutarse dentro del contexto del estudiante correspondiente, evitando el acceso cruzado entre usuarios.

## 4.3. Estrategia orientada a la calidad

Las principales decisiones arquitectónicas se relacionan con los escenarios de calidad definidos para TAIA:

| Quality Goal | Estrategia arquitectónica |
|---|---|
| **S1 — Exactitud** | Separación entre interpretación de IA, validación y reglas de negocio antes de persistir información. |
| **S2 — Puntualidad** | Módulo de recordatorios separado de la lógica de interacción, permitiendo gestionar su programación y entrega de forma independiente. |
| **S3 — Rendimiento** | Mantener una arquitectura monolítica con comunicación interna directa y evitar complejidad distribuida innecesaria. |
| **S4 — Seguridad** | Centralizar las reglas de autorización y mantener el acceso a información académica dentro del contexto del estudiante. |
| **S5 — Mantenibilidad** | Utilizar puertos y adaptadores para aislar las dependencias externas, especialmente el proveedor de inteligencia artificial. |

## 4.4. Estrategia de despliegue

Durante esta etapa TAIA se mantendrá como una **única unidad desplegable**. Esta decisión reduce la complejidad operacional del MVP y evita introducir comunicación entre servicios, despliegues independientes y mecanismos de observabilidad distribuida que no son necesarios para el alcance actual.

La modularización interna permitirá evolucionar posteriormente partes específicas del sistema si el crecimiento del dominio, la carga o las necesidades de operación justifican una separación adicional.
