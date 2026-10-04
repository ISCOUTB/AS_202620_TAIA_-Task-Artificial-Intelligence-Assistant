# 11. Riesgos y deudas técnicas

Los siguientes riesgos y deudas técnicas se identifican a partir del estado actual de la línea base ejecutable.

## 11.1. Integraciones externas y funcionalidades pendientes

**Riesgo:** Ni Gemini ni Telegram están configurados **en el despliegue** (faltan `GEMINI_API_KEY` y `TAIA_TELEGRAM_BOT_TOKEN` en el entorno de la VM). PostgreSQL ya está integrado (Supabase, ADR-0004). La credencial de Gemini sí está configurada en el entorno local del desarrollador, y eso permitió medir S1, S3 y S5; el recorrido desplegado sigue sin ejercitarse.

**Impacto:** La solución ejecutable actual no demuestra todavía persistencia definitiva ni el recorrido completo con un proveedor LLM configurado.

**Mitigación:** Mantener las integraciones detrás de adaptadores y sustituir los repositorios en memoria por implementaciones persistentes cuando corresponda.

**Estado:** Parcialmente atendido. La integración de PostgreSQL y la lectura del LLM quedaron probadas en local; el despliegue con las tres credenciales sigue pendiente.

## 11.2. Persistencia temporal en memoria

**Deuda técnica:** `InMemoryTaskRepository` se utiliza actualmente en lugar de PostgreSQL.

**Impacto:** Los datos no tienen persistencia permanente y no se pueden validar todavía aspectos propios de una base de datos real, como concurrencia, conexiones y persistencia entre ejecuciones.

**Mitigación:** Implementar un adaptador PostgreSQL que cumpla el contrato de `TaskRepository`, evitando modificar los casos de uso y las reglas del dominio.

**Estado:** Resuelta. Todos los módulos persisten en PostgreSQL con migraciones de Alembic; los repositorios en memoria quedan solo para las pruebas unitarias.

## 11.3. Proveedor de IA pendiente de aislamiento completo

**Riesgo:** El adaptador Gemini existe, pero el recorrido real depende de configurar la credencial del proveedor.

**Impacto:** Todavía no se ha validado en código la sustitución de un proveedor de IA sin modificar la lógica de negocio.

**Mitigación:** Mantener el puerto `LLM` y encapsular la API del proveedor en `GeminiLLM`; habilitar la credencial en el entorno y validar el recorrido real.

**Relación:** S5 — Sustitución del modelo de IA.

**Estado:** Parcialmente atendido. El recorrido real **sí** se validó con credencial y contra la API de Google: 39 llamadas reales a `gemini-3.5-flash-lite`. Lo que sigue sin probarse es la **sustitución completa** de proveedor, que exigiría un segundo adaptador y sus pruebas. Se comprobó además que cambiar de modelo no requiere tocar el dominio ni los casos de uso: se cambia `GEMINI_MODEL` o la constante del adaptador.

## 11.4. Disponibilidad de infraestructura gratuita

**Riesgo:** Supabase Free pausa el proyecto tras una semana sin actividad. La API ya no se suspende, porque corre en una VM propia (ADR-0003).

**Impacto:** Las funcionalidades que dependan de ejecución programada, especialmente los recordatorios, podrían no ejecutarse exactamente en el horario esperado.

**Mitigación:** Diseñar el mecanismo de notificaciones teniendo en cuenta las restricciones del entorno gratuito y evaluar posteriormente una estrategia de ejecución programada más adecuada.

**Relación:** S2 — Entrega puntual de recordatorios.

**Estado:** Riesgo abierto.

## 11.5. Aislamiento de información entre estudiantes

**Riesgo:** Al incorporar persistencia real y el contexto del LLM, debe mantenerse el aislamiento entre estudiantes.

**Impacto:** Exposición de información académica y fallo del requisito de seguridad.

**Mitigación:** Mantener el control de acceso en el backend, asociar cada operación con el estudiante autenticado y validar la autorización antes de acceder a la persistencia. Las pruebas actuales cubren Academic y Reminders.

**Relación:** S4 — Acceso únicamente a datos del propio estudiante.

**Estado:** Implementado en los módulos actuales; pendiente de validación del contexto LLM real.

## 11.6. Cuotas y límites del proveedor LLM

**Riesgo:** El uso de Gemini bajo restricciones gratuitas puede limitar la cantidad de solicitudes y tokens disponibles.

**Impacto:** Solicitudes con demasiado contexto pueden superar las cuotas disponibles o aumentar el tiempo de respuesta.

**Mitigación:** Limitar y controlar el contexto enviado al modelo, estructurar las solicitudes y mantener el proveedor aislado para permitir su sustitución.

**Relación:** S1 — Registro correcto de información académica; S3 — Respuesta del asistente ante un mensaje; S5 — Sustitución del modelo de IA.

**Estado:** Riesgo abierto.

**Riesgo:** El nivel gratuito de Gemini impone un **límite de llamadas por minuto**, y una ráfaga de peticiones produce LLMError. Es un riesgo distinto del de 11.6: no es un límite de cuota mensual ni de contexto, sino de **cadencia**.

**Impacto:** El asistente falla sin explicar nada al estudiante. `GeminiLLM` convierte el `429` en `LLMError` con el código de estado (`gemini_llm.py:156`), y un fallo de transporte en un `LLMError` que solo registra el **tipo** de excepción, no su mensaje (`gemini_llm.py:153`). El estudiante ve que el asistente no responde, sin ningún motivo.

**Mitigación:** Tres medidas, dos aplicadas y una pendiente. Aplicadas: pausar entre llamadas en `tools/eval_llm.py` (`PAUSA_ENTRE_LLAMADAS = 6`) y registrar el mensaje completo del error, no solo su tipo. Pendiente: **reintentar con espera ante `429`** y devolver un mensaje accionable al estudiante en lugar de un fallo opaco.

**Evidencia:** En la primera corrida de 	ools/eval_llm.py, 10 de 39 llamadas fallaron con LLMError y la exactitud cayó a 64,1 %. Los nueve primeros fallos eran **consecutivos** en el orden del dataset, lo que un defecto del modelo no explica. Un diagnóstico con pausa de 6 segundos respondió **7 de 7** correctamente sobre esos mismos casos, y la corrida con pausa dio 39 llamadas sin ningún error y 82,05 % de exactitud. La causa exacta —límite por minuto o saturación del servicio— **no se confirmó**, porque el arnés solo guardaba el nombre del error; lo que sí quedó probado es que el ritmo de las llamadas era la variable.

**Relación:** S1 — Registro correcto de información académica; S3 — Respuesta del asistente ante un mensaje.

**Estado:** **Abierto.** La evaluación sortea el problema con una pausa; el producto no lo sortea, porque la aplicación no reintenta ni explica el `429`.

## 11.7. Retirada de modelos del proveedor

**Riesgo:** El proveedor retira modelos. `gemini-2.5-flash`, que era el valor por defecto de `GeminiLLM`, devolvió **404** a una credencial recién obtenida. Google limita el acceso a los modelos 2.5 a las cuentas que ya los usaban.

**Impacto:** Sin cambios, un clon nuevo del repositorio nace roto: `_DEFAULT_MODEL` apunta a un modelo al que esa cuenta no tiene acceso, y falla en la primera petición real con un error que no dice «modelo retirado» sino «404». Un despliegue existente con `GEMINI_MODEL` explícito en su entorno habría seguido funcionando, lo que hace el fallo más difícil de detectar: funciona en el entorno de quien lo configuró y no en el de nadie más.

**Mitigación:** Fijar el modelo por defecto en el código a uno accesible —ahora `gemini-3.5-flash-lite`— en vez de dejarlo en el proveedor implícito, y permitir la sustitución por `GEMINI_MODEL` sin tocar el adaptador. El puerto `LLM` sigue encapsulando al proveedor, así que cambiar de modelo es cambiar una constante.

**Relación:** S5 — Sustitución del modelo de IA.

**Estado:** **Atendido en S8** para el modelo concreto. El riesgo de fondo —que el proveedor retire el que sea— sigue abierto: no hay comprobación automática que detecte un 404 por modelo.

## 11.8. Evolución del monolito modular

**Deuda técnica:** El sistema se mantiene como un único despliegue.

**Impacto:** Si aumenta significativamente la complejidad o la carga, los módulos podrían requerir un mayor aislamiento.

**Mitigación:** Mantener límites claros entre módulos y dependencias mediante interfaces. Si el crecimiento futuro lo justifica, los módulos podrán evolucionar hacia componentes desplegables de forma independiente.

**Estado:** Decisión aceptada para el MVP.

## 11.8. Costo de la VM fuera de la capa gratuita

**Riesgo:** La VM `VM.Standard.E5.Flex` no es Always Free y se cobra a la tarjeta registrada en OCI: 39,42 USD/mes a precio de lista.

**Impacto:** Rompe el límite de costo cero de la sección 2 mientras la VM siga encendida.

**Mitigación:** Reducir la memoria de 12 GB a 2 GB (24,82 USD/mes) y pasar a `VM.Standard.A1.Flex` (Always Free) cuando haya capacidad, construyendo la imagen también para ARM64. Ver [costo_mensual.md](../costo_mensual.md) y ADR-0003.

**Estado:** Riesgo abierto.

## 11.9. API sin HTTPS

**Deuda técnica:** La API se expone por HTTP en el puerto 8000 de la VM.

**Impacto:** Incumple RNF-04; los tokens JWT viajan sin cifrar.

**Mitigación:** Configurar un dominio y un proxy inverso con TLS delante del contenedor.

**Estado:** Pendiente.

## 11.10. Red de OCI fuera de Terraform

**Deuda técnica:** Terraform describe la VM, pero no la VCN, la subred, la IP pública ni las reglas de seguridad, que se administran desde la consola.

**Impacto:** El entorno no se puede recrear por completo desde el repositorio; un cambio en la red no queda versionado.

**Mitigación:** Declarar e importar esos recursos en `terraform/` con sus valores actuales.

**Estado:** Pendiente.
