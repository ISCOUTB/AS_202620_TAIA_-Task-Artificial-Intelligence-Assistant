# ADR-0001 — Monolito modular con organización hexagonal selectiva

## Contexto

TAIA necesita una arquitectura que permita desarrollar el MVP con una complejidad operativa reducida, manteniendo al mismo tiempo la capacidad de evolucionar y sustituir dependencias externas.

El sistema presenta dependencias con servicios externos como **Telegram**, utilizado como canal conversacional y de notificaciones; **Un LLM**, utilizado para la interpretación de lenguaje natural; y **PostgreSQL**, utilizado para la persistencia de la información académica.

Estas dependencias pueden cambiar por razones técnicas, económicas o funcionales. En particular, el proveedor de inteligencia artificial puede modificar sus modelos, cuotas o condiciones de uso. Por esta razón, la arquitectura debe evitar que la lógica de negocio dependa directamente de una implementación concreta.

Al mismo tiempo, TAIA se encuentra en una etapa de MVP y es desarrollado por un equipo de cuatro personas dentro del calendario académico del curso. Por lo tanto, no se considera conveniente introducir desde el inicio una arquitectura distribuida o microservicios, debido a la complejidad adicional de despliegue, comunicación, observabilidad y operación que implicaría.

La arquitectura debe buscar un equilibrio entre **simplicidad para el desarrollo inicial** y **capacidad de evolución ante cambios en las dependencias externas**.

## Comparación de escenarios

| Escenario / Criterio | Capas | Hexagonal | Monolito modular |
|---|---|---|---|
| S1 — Exactitud | Aceptable con costos | Favorable | Favorable |
| S2 — Disponibilidad / Puntualidad| Aceptable con costos | Favorable | Favorable |
| S3 — Rendimiento | Favorable | Aceptable con costos | Favorable |
| S4 — Seguridad | Aceptable con costos | Favorable | Favorable |
| S5 — Mantenibilidad | Desfavorable | Favorable | Favorable |

### S1 — Exactitud

**Hexagonal** y **monolito modular** permiten aislar la interpretación de IA y las reglas de negocio, facilitando pruebas independientes. **Capas** también puede hacerlo, pero tiende a permitir dependencias más rígidas entre presentación, lógica y datos.

### S2 — Disponibilidad / Puntualidad

**Hexagonal** facilita aislar el mecanismo de notificaciones como adaptador, mientras que el **monolito modular** permite mantener el recordatorio como módulo independiente. **Capas** puede implementarlo, pero el mecanismo temporal puede terminar acoplado a infraestructura.

### S3 — Rendimiento

**Capas** y **monolito modular** tienen poca sobrecarga estructural. **Hexagonal** introduce interfaces/adaptadores, aunque esa indirección normalmente no será el factor dominante frente al tiempo del LLM y las APIs externas.

### S4 — Seguridad

**Hexagonal** favorece que las reglas de autorización permanezcan en el núcleo y que la infraestructura no las evada. El **monolito modular** también permite aislar responsabilidades. **Capas** puede conseguirlo, pero requiere disciplina para evitar accesos indebidos entre capas.

### S5 — Mantenibilidad

Con **arquitectura hexagonal** podemos definir, por ejemplo:

```text
       AI Port
          ▲
          │
   ┌──────┴──────┐
   │ AI Adapter  │
   └──────┬──────┘
          │
       Gemini
```
Cambiar Gemini por otro proveedor implica sustituir el adaptador sin modificar el dominio.

## Beneficios y costos

| Patron arquitectonico | Beneficios | Costo |
|---|---|---|
| Capas | Simple, rápido de implementar, fácil de entender inicialmente| Mayor acoplamiento entre responsabilidades; sustituir Gemini y aislar infraestructura requiere más disciplina. |
| Hexagonal | Excelente aislamiento del dominio, testabilidad y sustitución de Telegram/Gemini/PostgreSQL mediante adaptadores. | Mayor número de interfaces y abstracciones; requiere más diseño inicial. |
| Monolito modular | Mantiene un despliegue simple y permite separar dominios funcionales; facilita evolución gradual. | Los límites entre módulos dependen de disciplina; no proporciona por sí solo un mecanismo tan explícito para aislar infraestructura externa. |

## Decisión del Patron arquitectonico inicial

### Monolito modular con organización hexagonal solo en los módulos que tienen dependencias externas.

TAIA presenta un problema arquitectónico importante: **Existen varias dependencias externas que pueden cambiar**

Entre ellas se encuentran *Telegram*, utilizado como canal de comunicación; *Gemini*, utilizado para la interpretación de lenguaje natural; y *PostgreSQL*, utilizado para la persistencia de la información académica. Estas dependencias forman parte de la infraestructura del sistema y podrían cambiar por razones técnicas, económicas o funcionales.

Por ejemplo, el proveedor de IA podría cambiar en el futuro. TAIA podría pasar de Gemini a otro modelo o proveedor sin que las reglas de negocio deban modificarse. De manera similar, podrían incorporarse otros canales de comunicación además de Telegram o cambiar la tecnología utilizada para la persistencia.

Por esta razón, se adopta un **monolito modular** como estructura general. Esta decisión permite mantener todos los componentes dentro de una única aplicación, simplificando el despliegue y la comunicación entre módulos, pero estableciendo límites claros entre las diferentes responsabilidades del sistema. Dentro de este monolito se utilizan **puertos y adaptadores en aquellos puntos donde realmente aportan valor**, principalmente alrededor de las dependencias externas que presentan mayor probabilidad de cambio.

Por ejemplo, la interacción con el servicio de IA puede abstraerse mediante un puerto. De esta manera, la lógica de negocio no necesita conocer directamente los detalles de la API de Gemini. El adaptador se encarga de traducir entre la interfaz definida por TAIA y la API concreta del proveedor. El mismo principio puede aplicarse a otras dependencias cuando sea necesario.

Esta combinación permite obtener un equilibrio entre **simplicidad y capacidad de evolución**. El monolito mantiene la arquitectura sencilla para el MVP, mientras que los puertos y adaptadores reducen el acoplamiento con las dependencias externas más relevantes.

Además, esta decisión permite que la arquitectura **evolucione gradualmente**. Si en el futuro algún módulo alcanza un nivel de complejidad o carga que justifique separarlo, puede extraerse del monolito con menor impacto gracias a los límites establecidos previamente.

## Alternativas descartadas

### Microservicios

Se descarta para la etapa inicial porque TAIA no necesita **microservicios ni una arquitectura distribuida** desde un inicio. El sistema todavía es pequeño, el número de funcionalidades es limitado y el objetivo es comenzar con una base sencilla que permita avanzar rápidamente sin introducir complejidad operativa innecesaria.

Adoptar microservicios desde esta etapa implicaría añadir mecanismos como comunicación entre servicios, gestión de despliegues independientes, observabilidad distribuida, configuración adicional y posibles problemas de consistencia entre servicios. Estos elementos no aportan suficiente valor para las necesidades actuales de TAIA y podrían dificultar el desarrollo y mantenimiento del MVP.

## Consecuencias

### Positivas

- Se mantiene un único despliegue, reduciendo la complejidad operativa del MVP.
- Se establecen límites claros entre los módulos del sistema.
- Las dependencias externas pueden sustituirse mediante puertos y adaptadores.
- La lógica de negocio puede probarse con menor dependencia de infraestructura externa.
- La arquitectura permite una evolución gradual hacia una separación mayor de módulos si el sistema lo requiere.

### Negativas

- La combinación de monolito modular y puertos/adaptadores introduce mayor complejidad que una arquitectura por capas simple.
- Se requiere disciplina para mantener los límites entre módulos y evitar dependencias indebidas.
- No todas las partes del sistema necesitan el mismo nivel de abstracción, por lo que se debe evitar aplicar puertos y adaptadores de forma innecesaria.
- La extracción futura de un módulo a un servicio independiente no está garantizada automáticamente y requerirá trabajo adicional.

### Costos aceptados

Se acepta la complejidad adicional de utilizar puertos y adaptadores únicamente en las dependencias externas que presenten mayor probabilidad de cambio. No se busca aplicar arquitectura hexagonal de forma completa a todo TAIA, con el fin de mantener una relación razonable entre mantenibilidad y simplicidad.