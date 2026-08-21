ESCENARIOS DE CALIDAD 


 # Escenario 1 — Registro correcto de información académica 

 Fuente - El estudiante 

 Estímulo - Escribe en lenguaje natural información correspondiente a una tarea, examen, materia o clase/evento.

 Artefacto - El servicio que interpreta el mensaje con el LLM y registro de TAIA

 Entorno - sistema desplegado, con el servicio de IA disponible.

 Respuesta - TAIA identifica los campos relevantes, solicita confirmación cuando corresponda y registra la información correctamente en PostgreSQL. 

 Medida - Al menos el 90 % de los campos esperados deben ser identificados y registrados correctamente en una muestra de 100 mensajes académicos representativos.

 Restricción relacionada - el contexto que se le manda al LLM no puede ser muy grande porque las cuotas gratuitas son limitadas, así que tampoco se le puede pedir demasiado "razonamiento" extra para mejorar la extracción 

 Justificación - Registrar sin fricción es lo que hace diferente a TAIA; si falla mucho la interpretación, el estudiante deja de confiar y vuelve a anotar las cosas a mano 

 # Escenario 2 — Entrega puntual de recordatorios

 Fuente - sistema de TAIA

 Estímulo - llega el momento programado para un recordatorio.

 Artefacto - servicio de recordatorios/notificaciones.

 Entorno - sistema desplegado y operativo.

 Respuesta - TAIA envía el recordatorio al canal configurado por el estudiante.

 Medida - al menos el 95 % de los recordatorios deben ser entregados dentro de un margen de ±1 minuto respecto a la hora programada, en una prueba de, por ejemplo, 100 recordatorios.

# Escenario 3 — Respuesta del asistente ante un mensaje 

 Fuente - El estudiante 

 Estímulo - El estudiante envía una consulta o instrucción válida al asistente de TAIA.

 Artefacto - Backend de TAIA y servicio de interpretación mediante LLM

 Entorno - Sistema desplegado, con el backend, Telegram y el servicio de IA disponibles.

 Respuesta - Procesa el mensaje y devuelve una respuesta 

 Medida - El 95 % de las solicitudes deberá recibir una respuesta en un tiempo ≤ 7 segundos, medido desde la recepción del mensaje por el backend hasta el envío de la respuesta al canal del estudiante, bajo condiciones normales de operación.

 Restricción relacionada - hosting gratuito, sin garantía de recursos dedicados 

 Justificación - Correr en infraestructura gratuita implica arranques en frío y recursos compartidos, si la respuesta tarda mucho, se rompe la usabilidad de los escenarios 1 y 2 


# Escenario 4 — Acceso unicamente a datos del propio estudiante

 Fuente - El estudiante autenticado

 Estímulo - Manda un mensaje pidiendo, directa o indirectamente, información de otra persona 
 
 Artefacto - La capa que arma el contexto para el LLM, más la persistencia 

 Entorno - Sistema desplegado y con múltiples estudiantes registrados.

 Respuesta - TAIA devuelve únicamente información asociada al estudiante autenticado y rechaza cualquier intento de acceder a información perteneciente a otro estudiante

 Medida - En una prueba de 100 intentos de acceso, incluyendo solicitudes legítimas y solicitudes que intenten consultar información perteneciente a otros estudiantes, el sistema deberá permitir únicamente los accesos autorizados y rechazar el 100 % de los intentos de acceso no autorizados, sin exponer datos de otros usuarios.

 Restricción relacionada - No sale directo de una restricción técnica, sino del objetivo de calidad #3 y del riesgo propio de usar un LLM con contexto en cada petición 

 Justificación - Es un despliegue con datos académicos reales de estudiantes de la universidad, una fuga entre usuarios sería grave y le quitaría toda la confianza al sistema 

# Escenario 5 — Sustitucion del modelo de IA 
 
 Fuente - El equipo de desarrollo 

 Estímulo - Se decide cambiar Gemini por otro proveedor de LLM 

 Artefacto - Componente de integración con el LLM

 Entorno - Sistema implementado y funcionando con un proveedor/modelo de IA.

 Respuesta - El equipo puede incorporar un nuevo proveedor/modelo mediante la implementación o configuración del adaptador correspondiente, sin modificar los componentes principales de TAIA encargados de la lógica académica, persistencia y gestión de usuarios

 Medida - l cambio de proveedor/modelo deberá requerir modificaciones únicamente en el componente adaptador de IA y su configuración, sin modificar la lógica de negocio ni el esquema de persistencia, y deberá poder completarse en ≤ 4 horas de trabajo de desarrollo.

 Restricción relacionada - El proveedor de LLM tiene que ser intercambiable

 Justificación - Los proveedores cambian sus condiciones de tier gratuito seguido, sin esto, un cambio de cuotas en Gemini podría dejar el sistema sin modelo funcional a mitad de semestre 