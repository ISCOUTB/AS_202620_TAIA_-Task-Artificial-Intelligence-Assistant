# Ficha del problema

## Nombre del proyecto

**TAIA – Task Artificial Intelligence Assistant**

## Problema

Los estudiantes universitarios reciben y deben gestionar constantemente tareas, cambios de fechas y recordatorios relacionados con su vida académica. En muchas ocasiones no registran esta información porque deben cambiar entre aplicaciones (calendario, notas, gestor de tareas), lo que puede dificultar la organización del estudiante y provocar que información importante no sea registrada oportunamente.


## Usuarios objetivo

Estudiantes universitarios que necesitan una forma rápida de registrar información académica sin interrumpir sus actividades.

## Propuesta de solución

TAIA es una aplicación móvil desarrollada en Flutter con un asistente de inteligencia artificial conectado a un bot de Telegram. Desarrollando un asistente académico inteligente. El estudiante puede enviar mensajes en lenguaje natural, por ejemplo: “Tengo parcial de Cálculo el martes a las 8” o “Recordarme enviar el informe mañana”. El sistema interpreta automáticamente el mensaje mediante un modelo de IA (Gemini), identifica la intención del usuario, extrae la información relevante y la almacena en una base de datos PostgreSQL.

## Funcionalidades iniciales

* Registro de tareas por lenguaje natural.
* Registro de exámenes, eventos académicos, calendario  académico.
* Consulta de tareas pendientes y próximos exámenes.
* Visualización de la información desde una aplicación Flutter.

## Alcance del MVP

El primer incremento implementará el registro de tareas desde Telegram, su almacenamiento en PostgreSQL y la visualización de las tareas pendientes en la aplicación móvil. Este aspecto servirá como corte vertical inicial del sistema y base para la evolución del resto de funcionalidades. En etapas posteriores, el sistema podrá incorporar seguimiento de sesiones de estudio, metas académicas, estadísticas, planificación automática y recomendaciones personalizadas. También se contempla como evolución futura el procesamiento de documentos académicos mediante embeddings y RAG.
