# Estimación de costo mensual del despliegue

Estimación del costo de operar TAIA tal como está desplegado (ver [arc42 §7](arc42/07-vista-de-despliegue.md)), calculada a partir del volumen supuesto para el MVP y no del catálogo de cada proveedor. Precios y cuotas consultados en septiembre de 2026.

## 1. Volumen supuesto

| Supuesto | Valor |
|---|---|
| Estudiantes activos | 100 |
| Operaciones CRUD por estudiante y día (tareas, materias, recordatorios, consultas) | 40 |
| Mensajes al agente por estudiante y día | 10 |
| Peticiones HTTP a la API por día | 100 × (40 + 10) = **5 000** |
| Peticiones HTTP a la API por mes (30 días) | **150 000** |
| Llamadas al LLM por mes (RNF-10: máximo una por mensaje) | 100 × 10 × 30 = **30 000** (1 000 por día) |
| Hora pico | 30 % del tráfico diario en 2 horas: 1 500 peticiones, unas 0,2 peticiones por segundo |
| Tamaño medio de una respuesta HTTP | 2 KB |
| Datos leídos de la base por petición | 5 KB |
| Datos por estudiante y semestre (tareas, recordatorios, conversaciones) | 1,5 MB |

## 2. Costo por pieza

| Pieza | Dónde se ejecuta | Qué consume con este volumen | Capa gratuita | Costo mensual |
|---|---|---|---|---|
| API TAIA | VM `VM.Standard.E5.Flex` de OCI, 1 OCPU y 12 GB | Se cobra por hora encendida, no por petición: 730 h/mes | No es Always Free (ver ADR-0003) | 730 h × (1 × 0,03 + 12 × 0,002) USD = **39,42 USD** |
| Disco de arranque de la VM | Block Volume de OCI | Un volumen de arranque | 200 GB de Block Volume Always Free | 0 USD |
| Tráfico de salida de la VM | OCI | 150 000 × 2 KB = 0,3 GB/mes | 10 TB/mes Always Free | 0 USD |
| Base de datos | Supabase PostgreSQL, plan Free | Tamaño: 100 × 1,5 MB = 150 MB por semestre. Salida hacia la API: 150 000 × 5 KB = 0,75 GB/mes | 500 MB de base de datos y 5 GB de salida por mes | 0 USD |
| Registro de imágenes | GitHub Container Registry | Una imagen por despliegue | Gratis para paquetes públicos | 0 USD |
| CI/CD | GitHub Actions | Un run de CI y uno de CD por push a `main` | Minutos gratuitos en repositorios públicos | 0 USD |
| LLM | Gemini API (`gemini-3.5-flash-lite`), cuando se configure `GEMINI_API_KEY` | 1 000 llamadas por día | Cuota gratuita por proyecto, visible en Google AI Studio | 0 USD dentro de la cuota |
| Telegram Bot API | Servidores de Telegram | Mensajes del bot | Gratuita | 0 USD |
| **Total** | | | | **39,42 USD/mes** |

Precio de lista de la VM: 0,03 USD por OCPU-hora y 0,002 USD por GB-hora para la serie E5 (ver [Holori, E5.Flex](https://calculator.holori.com/oci/vm/VM.Standard.E5.Flex-4c32g): 4 OCPU y 32 GB = 0,184 USD/h). El valor real se confirma en *Billing & Cost Management > Cost Analysis* de la cuenta de OCI.

### El costo del LLM ya no es una estimación

La fila del LLM decía «cuando se configure `GEMINI_API_KEY`». La clave está
configurada en local y la llamada se midió: el **2026-10-04**, 39 llamadas a
`gemini-3.5-flash-lite` costaron **0,012178 USD** en total, es decir **0,000312
USD por operación** —418 tokens de entrada y 75 de salida de media—, a los
precios declarados de 0,30 USD y 2,50 USD por millón de tokens. La fuente y la
fecha de consulta están en
[`entrega_s8.md`](entrega_s8.md) y el detalle en
[`evaluacion_ia/resultado_s1_s3.json`](evaluacion_ia/resultado_s1_s3.json).

Los precios **no** están en el código: `tools/eval_llm.py` los recibe por
argumento, porque cambian con frecuencia y una tabla desactualizada daría un
costo falsamente preciso.

Con el volumen supuesto de 1 000 llamadas al día, el costo del LLM seguiría
dentro de la cuota gratuita: 1 000 × 0,000312 USD son 0,31 USD al día, y solo
importa si la cuota del proyecto se agota. Aun así, **la cuota se mide por
cadencia, no solo por volumen**: el nivel gratuito tiene un límite de llamadas
por minuto que el producto todavía no maneja. Ver la sección 11.6 de
[`arc42/11`](arc42/11-riesgos-y-deudas-tecnicas.md).

## 3. Punto de ruptura de cada capa gratuita

| Pieza | Límite | Consumo con el volumen supuesto | Se rompe con |
|---|---|---|---|
| VM de OCI | La E5.Flex no tiene capa gratuita | Cuesta desde la primera hora | Ya está fuera de la capa gratuita |
| Tráfico de salida de OCI | 10 TB/mes | 0,3 GB/mes | Más de 30 000 veces el volumen supuesto; no es una restricción real |
| Supabase: tamaño | 500 MB | 150 MB por semestre | Unos 330 estudiantes activos durante un semestre, o 3 semestres sin depurar datos con 100 estudiantes |
| Supabase: salida | 5 GB/mes | 0,75 GB/mes | Unos 660 estudiantes con el mismo uso |
| Supabase: inactividad | Pausa tras 1 semana sin actividad | La API recibe peticiones a diario | Una semana sin uso (por ejemplo, vacaciones); se reactiva desde el panel |
| Gemini | Peticiones por día del proyecto (según AI Studio) | 1 000 llamadas por día | Cuando las llamadas diarias superen la cuota del proyecto; es la primera cuota que se rompe al crecer, porque crece con cada mensaje |
| Gemini | Peticiones por **minuto** del nivel gratuito | 1 000 al día, pero en ráfaga | Mucho antes que la cuota diaria: una ráfaga produce `LLMError` aunque el día entero lleve pocas llamadas. Es el límite que ya se rompió una vez al medir S1 |

La pieza que se rompe primero por volumen es el tamaño de la base de datos en Supabase (500 MB), seguida de la cuota diaria de Gemini. La VM no depende del volumen: con 0,2 peticiones por segundo en hora pico, 1 OCPU no se satura.

Lo que ya se rompió no fue por volumen, sino por **cadencia**: las diez llamadas
consecutivas del arnés de evaluación superaron el límite por minuto. Ese es un
límite que no aparece en la tabla de quotas por volumen, y por eso tiene su
propio riesgo documentado.

## 4. Cómo bajar el costo

- Reducir la memoria de la VM de 12 GB a 2 GB, que es suficiente para un contenedor de FastAPI sin base de datos local: 730 × (0,03 + 2 × 0,002) = **24,82 USD/mes**.
- Pasar a `VM.Standard.A1.Flex` (Always Free, hasta 2 OCPU y 12 GB) cuando la región tenga capacidad. La imagen tendría que construirse también para ARM64.
- Usar Render Free, la alternativa descartada en ADR-0003, que cuesta 0 USD pero suspende el servicio tras 15 minutos sin tráfico.
