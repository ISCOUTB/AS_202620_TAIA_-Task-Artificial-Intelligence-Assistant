# Contexto acerca del modulo de IA

## Responsabilidad del Agente IA 
El agente de inteligencia artificial deberá interpretar mediante lenguaje natural la intención que tiene el usuario, esto se debe traducir a algo que TAIA pueda procesar. 

Primero, hay que definir que modelo de intelegencia se utilizará. Este modelo será Gemini, aunque, el programa será capaz de adaptarse a cualquier provedoor de modelos de lenguaje grandes (LLM, por sus siglas en inglés), esto debido a si algún día falla o cambian los costos de tokens y demás, para eso se eligío la arquitectura hexagonal y los modulos.

La IA será responsable de la visualización e importación de datos a la base de datos. Está no será capaz de crear tareas sin que un usuario se lo pida, tampoco tocará nada más de la aplicación que no se especifique en los casos de uso.

## Que componente es responsable de comnicarse con gemini? 

A la fecha, se piensa usar LangChain como framework para la creación del agente y la conección con el modelo brindado por gemini. LangChain es un marco de trabajo de codigo abierto que permite la creación dde aplicaciones basadas en llm. 

LangChain funciona como una capa intermedia o un pegamento entre los modelos de inteligencia artificial y los datos o herramientas externas, permitiendo pasar de una simple consulta de texto a flujos de trabajo complejos y conectados
### ¿Algo está implementado actualmente? 

A la fecha, nada está implementado, pero, se tiene la api key de gemini, el siguiente trabajo que se hará es codificar, por lo menos una funcionalidad del modulo.

### Casos de uso
El agente de inteligencia aritificial es una de las funcionalidades que le añadé un plus a nuestro sistema. El Agente se encargará de:

1)  Usar telegram para conectarse con el usuario: Esto se hará mediante la funcionalidad de Telegram Bot API. La idea es usar un adaptador para esto, tambíen, usar Anti-Corruption Layer (ACL).

2) El ACL, servirá para frenar la entrada de codigo malicioso en el sistema, debido a que el llm estará conectado a la base de datos. Entonces el ACL, funcionará como un filtro para evitar sql inyection en nuestro programa.

3) A partir de estas funcionalidades, el agente podrá consultar, modificar y postear una tarea. El agente no podrá borrar una tarea, esto debido a que puede ser peligro para la base de datos.

4) El Agente será capaz de estructurar la información que le llega para así, mandarla a un query a la base de datos

5) El Agente será capaz de generar un respuesta a partir de lo que el usuario le solicitó. Ya sea una respuesta confirmando la publicación o modificación de la tarea, o un mensaje en donde se muestre información de la tarea.

6) El modelo será capaz (dentro de la aplicación) de crear opciones y horarios de estudio dependiendo a lo que pida el usuario. Acá no se utilizará que el usuario ingrese un pront, si no que medíante un formulario ya predefinido en la aplicación, el llm sea capaz de interpretar esto y entregar opciones de horarios en las que el usuario puede estudiar

Actualmente, ninguno de estos casos de uso están implementados, ese será el siguiente paso

 #### ¿Comó será el flujo de la 1 hasta la 5? 

El usuario mandará un pront al bot de telegram, este bot se conectará con el Agente y el Agente interpretará si el usuario quiere hacer una consulta, si quiere modificar o si quiere subir una nueva tarea. Cuando el agente interprete, hará una query bien estructurada a la base de datos, después lanzará un mensaje donde diga lo que hizo (Sin mostrar el comando). Ahí termina el flujo.

## Que información puede consultar y modificar la IA?
La IA puede modificar, consultar y subir información con respecto a las tareas en la base de datos, además tambíen podrá consultar la informacíon de los horarios de los usuarios para hacer el horario sugerido de estudio. 

La IA no podrá, modificar, consultar información acerca los demás usuarios diferentes al usuario que está atendiendo. Tampoco podrá ver información personal del usuario, información como correo electronico, numero de telefono y demás, no estará disponible para la IA.

## Relación con el modulo Academico

Como ya fue descrito anteriormente, el agente solo será capaz de modificar, consultar y subir información acerca de las tareas, está es la relación directa de la IA con el modulo academico, la IA no será propietaria de la entidad academica task debido a que esta no podrá eliminar de la base de datos ningun tipo de información. Toda acción que se dictamine como riesgosa tendrá que ser manipulada solo y exclusivamente por el usuario. 



