ESCENARIOS DE CALIDAD 


 # Escenario 1 — Registro correcto de información académica 

 

 Fuente - El estudiante 

 Estímulo - Escribe en lenguaje natural una tarea que tiene que hacer (materia, fecha, qué es) 

 Ambiente - Uso normal, con el backend corriendo 

 Artefacto - El servicio que interpreta el mensaje con el LLM 

 Respuesta - Extrae los datos de la tarea y se los muestra al estudiante para que confirme o corrija antes de guardarlos 

 Medida - Al menos el 90% de los campos bien extraídos en una muestra de mensajes de prueba, lo que falla se puede corregir en la confirmación sin perder el registro 

 Restricción relacionada - el contexto que se le manda al LLM no puede ser muy grande porque las cuotas gratuitas son limitadas, así que tampoco se le puede pedir demasiado "razonamiento" extra para mejorar la extracción 

 Justificación - Registrar sin fricción es lo que hace diferente a TAIA; si falla mucho la interpretación, el estudiante deja de confiar y vuelve a anotar las cosas a mano 

 # Escenario 2 — Registro desde telegram sin abrir flutter 

 
 Fuente - El estudiante 

 Estímulo - Quiere anotar o revisar una tarea en un momento donde no puede o no le da tiempo de abrir la app 

 Ambiente - Uso normal, con Telegram disponible 

 Artefacto - El bot de Telegram 

 Respuesta - Puede registrar y consultar tareas completamente desde Telegram, sin necesitar la app 

 Medida - Todas las funciones básicas de registro y consulta funcionan desde Telegram; registrar una tarea toma máximo 3 mensajes 

 Restricción relacionada - El canal de registro depende de Telegram, que es de un tercero 

 Justificación - Como Telegram no lo controla el equipo, si algún día falla, la app en Flutter tiene que poder cubrir lo mismo (RF-04) para que el sistema no quede inutilizable 

# Escenario 3 — Respuesta del asistente ante un mensaje 

 
 Fuente - El estudiante 

 Estímulo - Manda un mensaje para que el bot lo procese 

 Ambiente - Uso normal, carga típica de decenas de usuarios 

 Artefacto - El servicio de interpretación LLM junto con el bot 

 Respuesta - Procesa el mensaje y devuelve una respuesta 

 Medida - Menos de 7 segundos en el 95% de los casos 

 Restricción relacionada - hosting gratuito, sin garantía de recursos dedicados 

 Justificación - Correr en infraestructura gratuita implica arranques en frío y recursos compartidos, si la respuesta tarda mucho, se rompe la usabilidad de los escenarios 1 y 2 


# Escenario 4 — Acceso unicamente a datos del propio estudiante


 Fuente - El estudiante (incluyendo quien intente sacarle info a otro usuario manipulando al LLM) 

 Estímulo - Manda un mensaje pidiendo, directa o indirectamente, información de otra persona 
 
 Ambiente - Uso normal, con varios usuarios usando el sistema a la vez 

 Artefacto - La capa que arma el contexto para el LLM, más la persistencia 

 Respuesta - El contexto que se le manda al LLM ya viene filtrado por usuario antes de cada llamada; ninguna respuesta muestra datos de otro 

 Medida - Cero filtraciones de datos entre usuarios en las pruebas, incluyendo pruebas de prompt injection 

 Restricción relacionada - No sale directo de una restricción técnica, sino del objetivo de calidad #3 y del riesgo propio de usar un LLM con contexto en cada petición 

 Justificación - Es un despliegue con datos académicos reales de estudiantes de la universidad, una fuga entre usuarios sería grave y le quitaría toda la confianza al sistema 

# Escenario 5 — Sustitucion del modelo de IA 

 
 Fuente - El equipo de desarrollo 

 Estímulo - Se decide cambiar Gemini por otro proveedor de LLM 

 Ambiente - Momento de mantenimiento, fuera de producción 

 Artefacto - El adaptador del puerto LLM 

 Respuesta - Se hace un nuevo adaptador que cumple la misma interfaz, sin tocar el resto del sistema 

 Medida - El cambio queda solo en la capa de adaptador, sin tocar dominio ni casos de uso

 Restricción relacionada - El proveedor de LLM tiene que ser intercambiable

 Justificación - Los proveedores cambian sus condiciones de tier gratuito seguido, sin esto, un cambio de cuotas en Gemini podría dejar el sistema sin modelo funcional a mitad de semestre 