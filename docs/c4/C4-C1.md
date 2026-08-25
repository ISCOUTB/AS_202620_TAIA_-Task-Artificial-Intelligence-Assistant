# Diagrama de Contexto - TAIA
### Task Artificial Intelligence Assistant

```mermaid
%%{init: {"flowchart": {"curve": "basis", "nodeSpacing": 55, "rankSpacing": 90}}}%%
flowchart TB
    estudiante(["<b>Estudiante</b><br/><i>[Persona]</i><br/><br/>Estudiante universitario que registra<br/>tareas académicas, consulta su información<br/>y recibe recordatorios y planes de estudio."])

    telegram["<b>Telegram</b><br/><i>[Sistema externo]</i><br/><br/>Plataforma de mensajería usada como canal<br/>conversacional: captura de tareas en lenguaje<br/>natural y entrega de notificaciones."]

    taia["<b>TAIA</b><br/><i>[Sistema]</i><br/><br/>Asistente académico que interpreta lenguaje<br/>natural para registrar tareas, notifica<br/>vencimientos y propone planes de estudio<br/>compatibles con el horario de clases."]

    llm["<b>Proveedor LLM (Gemini)</b><br/><i>[Sistema externo]</i><br/><br/>Servicio externo de lenguaje natural que<br/>interpreta el mensaje del estudiante y extrae<br/>los campos estructurados de una tarea.<br/>Intercambiable mediante un adaptador propio."]

    estudiante -->|"Registra tareas escribiendo en lenguaje<br/>natural y consulta tareas"| telegram
    telegram -->|"Entrega respuestas<br/>y notificaciones"| estudiante

    estudiante -->|"Registra y consulta tareas mediante<br/>la app Flutter (formulario)"| taia

    telegram -->|"Reenvía mensajes del estudiante y solicita<br/>confirmación / entrega notificaciones"| taia
    taia -->|"Envía confirmaciones, respuestas y<br/>recordatorios de tareas próximas a vencer"| telegram

    taia -->|"Envía el texto del mensaje (filtrado por<br/>identidad del usuario) para su interpretación"| llm
    llm -->|"Devuelve los campos estructurados de<br/>la tarea (materia, fecha, tipo, etc.)"| taia

    classDef person fill:#08427b,stroke:#052e56,stroke-width:2px,color:#ffffff
    classDef system fill:#1168bd,stroke:#0b4884,stroke-width:2px,color:#ffffff
    classDef external fill:#999999,stroke:#6b6b6b,stroke-width:2px,color:#ffffff

    class estudiante person
    class taia system
    class telegram,llm external
```

**Convenciones**

| Color | Significado |
| ----- | ----------- |
| Azul oscuro | Persona (actor humano) |
| Azul | Sistema en alcance del proyecto |
| Gris | Sistema externo (no lo construimos ni lo controlamos) |
