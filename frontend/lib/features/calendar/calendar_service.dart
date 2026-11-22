import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
import '../../core/bogota_time.dart';
import '../tasks/task.dart';

/// Un bloque del horario proyectado en una fecha (RF-TAR-11).
class ClassOccurrence {
  const ClassOccurrence({
    required this.subjectName,
    required this.startsAt,
    required this.endsAt,
    this.room,
  });

  factory ClassOccurrence.fromJson(Map<String, dynamic> json) =>
      ClassOccurrence(
        subjectName: json['subject_name'] as String,
        startsAt: parseApiDateTime(json['starts_at'] as String),
        endsAt: parseApiDateTime(json['ends_at'] as String),
        room: json['room'] as String?,
      );

  final String subjectName;
  final DateTime startsAt;
  final DateTime endsAt;
  final String? room;
}

/// Actividades y clases de un rango de fechas.
class CalendarRange {
  const CalendarRange({required this.tasks, required this.classes});

  final List<AcademicTask> tasks;
  final List<ClassOccurrence> classes;
}

/// GET /academic/calendar (RF-TAR-11): como máximo 31 días, extremos
/// incluidos.
class CalendarService {
  CalendarService(this._dio);

  final Dio _dio;

  Future<CalendarRange> range(DateTime start, DateTime end) =>
      apiGuard(() async {
        final response = await _dio.get<Map<String, dynamic>>(
          '/academic/calendar',
          queryParameters: {'start': _date(start), 'end': _date(end)},
        );
        final data = response.data!;
        return CalendarRange(
          tasks: (data['tasks'] as List<dynamic>)
              .map((e) => AcademicTask.fromJson(e as Map<String, dynamic>))
              .toList(),
          classes: (data['classes'] as List<dynamic>)
              .map((e) => ClassOccurrence.fromJson(e as Map<String, dynamic>))
              .toList(),
        );
      });

  static String _date(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';
}

final CalendarService calendarService = CalendarService(apiDio);
