# Ficha del problema

## Nombre del proyecto

**TAIA – Task Artificial Intelligence Assistant**

## Problema

Los estudiantes universitarios reciben constantemente tareas, cambios de fechas, recordatorios y gastos relacionados con su vida académica. En muchas ocasiones no registran esta información porque deben cambiar entre aplicaciones (calendario, notas, gestor de tareas, finanzas), lo que genera olvidos, incumplimientos y una mala organización personal.

## Usuarios objetivo

Estudiantes universitarios que necesitan una forma rápida de registrar información académica y financiera sin interrumpir sus actividades.

## Propuesta de solución

TAIA es una aplicación móvil desarrollada en Flutter con un asistente de inteligencia artificial conectado a un bot de Telegram. El estudiante puede enviar mensajes en lenguaje natural, por ejemplo: “Tengo parcial de Cálculo el martes a las 8”, “Gasté 15.000 en almuerzo”, o “Recordarme enviar el informe mañana”. El sistema interpreta automáticamente el mensaje mediante un modelo de IA (Gemini), identifica la intención del usuario, extrae la información relevante y la almacena en una base de datos PostgreSQL.

## Funcionalidades iniciales

* Registro de tareas por lenguaje natural.
* Registro de exámenes y eventos académicos.
* Registro de gastos personales relacionados con la universidad.
* Consulta de tareas pendientes, próximos exámenes y gastos acumulados.
* Visualización de la información desde una aplicación Flutter.

## Alcance del MVP

El primer incremento implementará el registro de tareas desde Telegram, su almacenamiento en PostgreSQL y la visualización de las tareas pendientes en la aplicación móvil. Este aspecto servirá como corte vertical inicial del sistema y base para la evolución del resto de funcionalidades.
