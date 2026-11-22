import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
import '../../core/bogota_time.dart';
import '../academic/schedule_block.dart';

/// Dónde se buscan huecos (RF-EST-01).
enum StudyPreference {
  betweenClasses('between_classes', 'Entre clases'),
  afterClasses('after_classes', 'Después de clases'),
  both('both', 'Ambas');

  const StudyPreference(this.api, this.label);
  final String api;
  final String label;

  static StudyPreference parse(String value) =>
      values.firstWhere((p) => p.api == value);
}

/// Momento del día en que el estudiante rinde mejor (RF-EST-01).
enum StudyTime {
  any('any', 'Cualquiera'),
  morning('morning', 'Mañana'),
  afternoon('afternoon', 'Tarde'),
  evening('evening', 'Noche');

  const StudyTime(this.api, this.label);
  final String api;
  final String label;

  static StudyTime parse(String value) =>
      values.firstWhere((t) => t.api == value);
}

/// Trabajo o compromiso fijo semanal: ninguna sesión cae encima (RF-EST-02).
class BusyBlock {
  const BusyBlock({
    required this.work,
    required this.weekday,
    required this.start,
    required this.end,
  });

  factory BusyBlock.fromJson(Map<String, dynamic> json) => BusyBlock(
    work: json['kind'] == 'work',
    weekday: Weekday.parse(json['weekday'] as String),
    start: parseApiTime(json['start_time'] as String),
    end: parseApiTime(json['end_time'] as String),
  );

  final bool work;
  final Weekday weekday;
  final TimeOfDay start;
  final TimeOfDay end;

  Map<String, dynamic> toJson() => {
    'kind': work ? 'work' : 'commitment',
    'weekday': weekday.name,
    'start_time': formatApiTime(start),
    'end_time': formatApiTime(end),
  };
}

/// Respuestas del formulario de RF-EST-01.
class StudyPlanForm {
  const StudyPlanForm({
    this.preference = StudyPreference.both,
    this.days = const {},
    this.windowStart = const TimeOfDay(hour: 6, minute: 0),
    this.windowEnd = const TimeOfDay(hour: 22, minute: 0),
    this.sessionMinutes = 60,
    this.subjectIds = const {},
    this.busyBlocks = const [],
    this.maxDailyMinutes,
    this.preferredTime = StudyTime.any,
  });

  final StudyPreference preference;
  final Set<Weekday> days;
  final TimeOfDay windowStart;
  final TimeOfDay windowEnd;
  final int sessionMinutes;
  final Set<String> subjectIds;
  final List<BusyBlock> busyBlocks;
  final int? maxDailyMinutes;
  final StudyTime preferredTime;

  Map<String, dynamic> toJson() => {
    'preference': preference.api,
    'days': [for (final day in days) day.name],
    'window_start': formatApiTime(windowStart),
    'window_end': formatApiTime(windowEnd),
    'session_minutes': sessionMinutes,
    'subject_ids': subjectIds.toList(),
    'busy_blocks': [for (final block in busyBlocks) block.toJson()],
    'max_daily_minutes': maxDailyMinutes,
    'preferred_time': preferredTime.api,
  };
}

class StudySession {
  const StudySession({
    required this.startsAt,
    required this.endsAt,
    required this.title,
    required this.subjectName,
  });

  factory StudySession.fromJson(Map<String, dynamic> json) => StudySession(
    startsAt: parseApiDateTime(json['starts_at'] as String),
    endsAt: parseApiDateTime(json['ends_at'] as String),
    title: json['title'] as String,
    subjectName: json['subject_name'] as String,
  );

  final DateTime startsAt;
  final DateTime endsAt;
  final String title;
  final String subjectName;
}

class StudyPlan {
  const StudyPlan({
    required this.id,
    required this.status,
    required this.form,
    required this.sessions,
    required this.unscheduled,
  });

  factory StudyPlan.fromJson(Map<String, dynamic> json) => StudyPlan(
    id: json['id'] as String,
    status: json['status'] as String,
    form: StudyPlanForm(
      preference: StudyPreference.parse(json['preference'] as String),
      days: {
        for (final day in json['days'] as List<dynamic>)
          Weekday.parse(day as String),
      },
      windowStart: parseApiTime(json['window_start'] as String),
      windowEnd: parseApiTime(json['window_end'] as String),
      sessionMinutes: json['session_minutes'] as int,
      subjectIds: {
        for (final id in json['subject_ids'] as List<dynamic>) id as String,
      },
      busyBlocks: [
        for (final block in json['busy_blocks'] as List<dynamic>)
          BusyBlock.fromJson(block as Map<String, dynamic>),
      ],
      maxDailyMinutes: json['max_daily_minutes'] as int?,
      preferredTime: StudyTime.parse(json['preferred_time'] as String),
    ),
    sessions: [
      for (final session in json['sessions'] as List<dynamic>)
        StudySession.fromJson(session as Map<String, dynamic>),
    ],
    unscheduled: [
      for (final item in json['unscheduled'] as List<dynamic>)
        (item as Map<String, dynamic>)['title'] as String,
    ],
  );

  final String id;

  /// `proposed`, `accepted` o `discarded`.
  final String status;
  final StudyPlanForm form;
  final List<StudySession> sessions;

  /// Títulos de las actividades que no cupieron (solo al generar).
  final List<String> unscheduled;

  bool get proposed => status == 'proposed';
}

/// `/academic/study-plans` (RF-EST-01…03).
class StudyPlanService {
  StudyPlanService(this._dio);

  final Dio _dio;

  /// El plan activo, o null si no hay.
  Future<StudyPlan?> current() => apiGuard(() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/academic/study-plans/current',
      );
      return StudyPlan.fromJson(response.data!);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  });

  Future<StudyPlan> generate(StudyPlanForm form) => apiGuard(() async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/academic/study-plans',
      data: form.toJson(),
    );
    return StudyPlan.fromJson(response.data!);
  });

  Future<StudyPlan> accept(String id) => _action(id, 'accept');

  Future<StudyPlan> discard(String id) => _action(id, 'discard');

  Future<StudyPlan> _action(String id, String action) => apiGuard(() async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/academic/study-plans/$id/$action',
    );
    return StudyPlan.fromJson(response.data!);
  });
}

final StudyPlanService studyPlanService = StudyPlanService(apiDio);
