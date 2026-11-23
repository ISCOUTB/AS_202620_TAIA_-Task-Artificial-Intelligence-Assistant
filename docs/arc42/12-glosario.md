# 12. Glosario

| Término                         | Definición                                                                                                                                                                                                               |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **TAIA**                        | *Task Artificial Intelligence Assistant*. Asistente académico inteligente del proyecto que permite registrar y consultar información académica mediante lenguaje natural y diferentes canales de interacción.            |
| **Estudiante**                  | Usuario principal de TAIA. Registra tareas e información académica, consulta sus datos y recibe recordatorios.                                                                                                           |
| **Tarea (Task)**                | Unidad de información académica que representa una actividad que debe realizar el estudiante y que puede incluir datos como título y fecha de entrega.                                                                   |
| **A-01**                        | Aspecto del sistema correspondiente a la **Captura inteligente de información académica**. Constituye el primer corte vertical del proyecto.                                                                             |
| **Corte vertical**              | Incremento funcional que atraviesa diferentes partes de la arquitectura, desde una interfaz de entrada hasta la lógica de aplicación, el dominio y la persistencia, permitiendo ejecutar y probar un recorrido completo. |
| **Módulo académico (Academic)** | Módulo del backend encargado de la información académica: asignaturas, horario, actividades, calendario, estadísticas y plan de estudio. |
| **Dominio**                     | Parte de la arquitectura que representa las entidades y reglas propias del problema, independientemente de tecnologías externas.                                                                                         |
| **Caso de uso (Use Case)** | Componente de la capa de aplicación que representa una operación que el sistema puede ejecutar, por ejemplo crear una actividad o despachar los recordatorios vencidos. |
| **Puerto (Port)** | Interfaz que define una dependencia requerida por la aplicación sin acoplarla a una implementación concreta. Por ejemplo, `TaskRepository` para la persistencia o `LLM` para el proveedor de lenguaje. |
| **Adaptador (Adapter)**         | Componente que conecta el núcleo de la aplicación con una tecnología o mecanismo externo mediante un puerto.                                                                                                             |
| **TaskRepository**              | Puerto de persistencia utilizado por los casos de uso para almacenar y consultar tareas sin depender de una implementación concreta.                                                                                     |
| **InMemoryTaskRepository** | Adaptador de persistencia en memoria. Se conserva para las pruebas unitarias; el sistema desplegado usa el repositorio SQLAlchemy sobre PostgreSQL. |
| **API** | Interfaz mediante la cual otros componentes se comunican con TAIA: la API HTTP implementada con FastAPI. |
| **FastAPI**                     | Framework utilizado para implementar la API HTTP del backend de TAIA.                                                                                                                                                    |
| **Flutter** | Tecnología de la aplicación móvil de TAIA, en `frontend/`. |
| **Telegram** | Canal conversacional: el estudiante vincula su cuenta y conversa con el asistente. No entrega recordatorios. |
| **Gemini** | Proveedor de modelo de lenguaje de respaldo, detrás de Groq ([ADR-0013](../adr/0013-usar-groq-como-proveedor-llm-principal.md)). |
| **Groq** | Proveedor de modelo de lenguaje principal del asistente ([ADR-0013](../adr/0013-usar-groq-como-proveedor-llm-principal.md)). |
| **FallbackLLM** | Adaptador que prueba Groq con cada clave configurada y después Gemini; si fallan todos, el asistente falla cerrado ([ADR-0007](../adr/0007-comportamiento-ante-fallo-del-proveedor-llm.md)). |
| **FCM (Firebase Cloud Messaging)** | Servicio de Google por el que TAIA envía las notificaciones push de los recordatorios al teléfono. |
| **PostgreSQL** | Sistema de gestión de base de datos donde persisten los cuatro módulos (Supabase en el despliegue). |
| **LLM**                         | *Large Language Model*. Modelo de lenguaje utilizado por TAIA para interpretar mensajes en lenguaje natural y extraer información estructurada.                                                                          |
| **ADR**                         | *Architecture Decision Record*. Registro utilizado para documentar una decisión arquitectónica, su contexto, alternativas y consecuencias.                                                                               |
| **C4**                          | Modelo de documentación de arquitectura utilizado para representar el sistema mediante diferentes niveles de abstracción, incluyendo contexto y contenedores.                                                            |
| **arc42** | Marco de documentación utilizado para estructurar la arquitectura de software de TAIA. |
