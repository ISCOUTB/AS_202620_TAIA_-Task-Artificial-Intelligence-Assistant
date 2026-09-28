# 2. Restricciones de arquitectura

Para cada restricción se indica su implicación arquitectónica: qué obliga o qué
prohíbe al construir el sistema.

**Restricciones técnicas**

| Restricción | Implicación arquitectónica |
|---|---|
| Stack definido: Flutter (cliente móvil), FastAPI (backend), PostgreSQL (persistencia), Telegram Bot API (canal conversacional y de notificación) y Gemini (proveedor LLM actual) | La elección tecnológica no está en discusión; el diseño se concentra en repartir responsabilidades entre esas piezas, no en sustituirlas |
| Plataforma objetivo: **Android** | iOS y web quedan fuera de esta etapa; no se invierte esfuerzo en abstracciones multiplataforma más allá de lo que Flutter ofrece por defecto |
| El proveedor de LLM debe ser **intercambiable** | El sistema depende de una interfaz propia (puerto) y el SDK del proveedor queda aislado tras un adaptador; ningún otro componente puede acoplarse a Gemini directamente |
| **Capas gratuitas**: los servicios externos (LLM, base de datos, hosting) se usan dentro de sus capas gratuitas | Impone tres límites duros: cuotas de peticiones y tokens del LLM, que obligan a controlar el tamaño del contexto enviado; límites de almacenamiento y conexiones de la base de datos; y un hosting que puede suspender el proceso por inactividad, lo cual afecta a las notificaciones programadas (RF-05) y obliga a un disparo que no dependa de un proceso siempre activo |
| **Límite de costo: 0 USD al mes** por pieza desplegada. La única excepción aceptada es la VM de la API, que cuesta 39,42 USD/mes (ver [costo_mensual.md](../costo_mensual.md)) | Cada pieza se elige dentro de una capa gratuita verificada y cada ADR de plataforma documenta el punto en que se rompe. La VM `VM.Standard.E5.Flex` quedó fuera de Always Free porque A1.Flex no tenía capacidad y E2.1.Micro no estaba disponible (ADR-0003); volver a costo cero exige pasar a A1.Flex cuando haya capacidad |
| **Tarjeta:** Oracle Cloud exige registrar una tarjeta para crear la cuenta; Render y Supabase no la piden en sus planes gratuitos | Como la cuenta de OCI tiene tarjeta, cualquier recurso fuera de Always Free se cobra sin aviso previo. Todo recurso nuevo en OCI se revisa en Cost Analysis antes de crearlo. Las piezas que no pueden generar cobros quedan en proveedores sin tarjeta (Supabase, ADR-0004) |
| Plataforma de despliegue: la API en una VM de OCI con Docker (ADR-0003) y la base de datos en Supabase (ADR-0004) | El sistema depende de Docker y de PostgreSQL estándar, no de servicios propios de un proveedor. Se puede cambiar de plataforma moviendo la misma imagen, como se hizo con Render en el taller |
| El canal de registro depende de un tercero (Telegram) | El equipo no controla su disponibilidad ni sus políticas. Esta acción debe ser realizada por el propietario de la organización. |

**Restricciones organizacionales**

| Restricción | Implicación arquitectónica |
|---|---|
| Equipo de cuatro personas, sin dedicación completa, dentro del calendario académico del curso | Favorece soluciones simples y comprensibles por todo el equipo frente a soluciones óptimas pero costosas de construir |
| El proyecto se desarrolla por **aspectos**: cortes verticales trazados en `docs/aspectos.md` con la cadena Requisito → C4 → ADR → Código → Pruebas → Evidencia | Cada incremento atraviesa todas las capas y deja trazabilidad completa; no se construyen capas horizontales aisladas |
| **Registro obligatorio del uso de IA** en `docs/ia.md`, con el formato de entrada numerada exigido por el curso | Todo uso significativo de IA en el desarrollo queda documentado, revisado y verificado por el equipo |
| Entregables y fechas definidos por el curso | No se documentan fechas concretas por no estar confirmadas; se añadirán cuando el equipo las fije |

**Restricciones legales**

| Restricción | Implicación arquitectónica |
|---|---|
| El sistema debe cumplir con las obligaciones aplicables de protección de datos personales sobre la información académica asociada a cada estudiante | La arquitectura debe limitar el acceso a los datos al usuario correspondiente, evitar la exposición innecesaria de información personal y mantener mecanismos de control que permitan proteger los datos almacenados y transmitidos |

**Convenciones**

| Convención | Implicación arquitectónica |
|---|---|
| Documentación del proyecto en español | Se redacta en español con independencia del idioma de las plantillas empleadas |
| Documentación arquitectónica siguiendo **arc42 v9.0**, organizada en `docs/arc42/` con un archivo índice `arc42.md` y una carpeta de secciones independientes | Se conserva la estructura y numeración de la plantilla arc42 v9.0; el contenido se documenta en español. |
| Diagramas siguiendo el **modelo C4** | Las vistas de contexto, contenedores y componentes se expresan en los niveles de C4 y se enlazan desde el aspecto correspondiente |
| Decisiones arquitectónicas registradas como **ADR** | Toda decisión estructural —proveedor de LLM, plataforma de despliegue, mecanismo de notificaciones— se documenta como ADR enlazado desde `docs/aspectos.md` |
| Código, identificadores y mensajes de commit en inglés; comentarios y documentación en español | Convención propuesta, aún no fijada por el equipo |
