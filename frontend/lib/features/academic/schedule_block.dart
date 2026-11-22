import 'package:flutter/material.dart';

import '../../core/spanish_dates.dart';

/// Día de la semana con los valores del `ENUM` `weekday` de la API.
enum Weekday {
  monday('Lunes'),
  tuesday('Martes'),
  wednesday('Miércoles'),
  thursday('Jueves'),
  friday('Viernes'),
  saturday('Sábado'),
  sunday('Domingo');

  const Weekday(this.label);

  final String label;

  static Weekday parse(String value) =>
      Weekday.values.firstWhere((day) => day.name == value);
}

/// Lee `"08:00:00"` (o `"08:00"`). Las horas del horario son de Colombia y no
/// llevan zona (RF-ASG-06).
TimeOfDay parseApiTime(String value) {
  final parts = value.split(':');
  return TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1]));
}

/// Escribe `"08:00:00"`.
String formatApiTime(TimeOfDay time) =>
    '${time.hour.toString().padLeft(2, '0')}:'
    '${time.minute.toString().padLeft(2, '0')}:00';

/// "08:00 a. m.".
String formatBlockTime(TimeOfDay time) =>
    formatClockTime(DateTime(2000, 1, 1, time.hour, time.minute));

int _minutes(TimeOfDay time) => time.hour * 60 + time.minute;

/// La hora de fin debe ser posterior a la de inicio (RF-ASG-06). Devuelve el
/// mensaje de error, o null si es válida.
String? blockTimeError(TimeOfDay start, TimeOfDay end) =>
    _minutes(end) > _minutes(start)
    ? null
    : 'La hora de fin debe ser posterior a la hora de inicio.';

/// Bloque del horario semanal de `/academic/schedule-blocks`.
class ScheduleBlock {
  const ScheduleBlock({
    required this.id,
    required this.subjectId,
    required this.subjectName,
    required this.weekday,
    required this.start,
    required this.end,
    this.room,
  });

  factory ScheduleBlock.fromJson(Map<String, dynamic> json) => ScheduleBlock(
    id: json['id'] as String,
    subjectId: json['subject_id'] as String,
    subjectName: json['subject_name'] as String,
    weekday: Weekday.parse(json['weekday'] as String),
    start: parseApiTime(json['start_time'] as String),
    end: parseApiTime(json['end_time'] as String),
    room: json['room'] as String?,
  );

  final String id;
  final String subjectId;
  final String subjectName;
  final Weekday weekday;
  final TimeOfDay start;
  final TimeOfDay end;
  final String? room;
}

/// Período académico (RF-ASG-08). Son fechas sin hora.
class AcademicPeriod {
  const AcademicPeriod({required this.start, required this.end});

  factory AcademicPeriod.fromJson(Map<String, dynamic> json) => AcademicPeriod(
    start: DateTime.parse(json['start_date'] as String),
    end: DateTime.parse(json['end_date'] as String),
  );

  final DateTime start;
  final DateTime end;
}

/// Escribe `"2026-08-03"`.
String formatApiDate(DateTime date) =>
    '${date.year.toString().padLeft(4, '0')}-'
    '${date.month.toString().padLeft(2, '0')}-'
    '${date.day.toString().padLeft(2, '0')}';

/// "3 de agosto de 2026".
String formatPeriodDate(DateTime date) =>
    '${formatDayMonth(date)} de ${date.year}';
