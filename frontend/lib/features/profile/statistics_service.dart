import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
import '../tasks/task.dart';

/// Período de las estadísticas (RF-PRF-01).
enum StatisticsPeriod { week, month, academicPeriod }

class WeeklyCompletion {
  const WeeklyCompletion(this.weekStart, this.completed);

  final DateTime weekStart;
  final int completed;
}

class SubjectLoad {
  const SubjectLoad(this.subjectName, this.pending);

  final String subjectName;
  final int pending;
}

/// Estadísticas ya agregadas por el servidor: el cliente no calcula nada a
/// partir de listados (RF-PRF-01).
class ProfileStatistics {
  const ProfileStatistics({
    required this.completed,
    required this.pending,
    required this.overdue,
    required this.completedByWeek,
    required this.onTimeCompleted,
    required this.onTime,
    required this.onTimePercentage,
    required this.pendingBySubject,
    required this.upcoming,
  });

  factory ProfileStatistics.fromJson(Map<String, dynamic> json) {
    final status = json['by_status'] as Map<String, dynamic>;
    final onTime = json['on_time'] as Map<String, dynamic>;
    return ProfileStatistics(
      completed: status['completed'] as int,
      pending: status['pending'] as int,
      overdue: status['overdue'] as int,
      completedByWeek: [
        for (final w in json['completed_by_week'] as List<dynamic>)
          WeeklyCompletion(
            DateTime.parse((w as Map<String, dynamic>)['week_start'] as String),
            w['completed'] as int,
          ),
      ],
      onTimeCompleted: onTime['completed'] as int,
      onTime: onTime['on_time'] as int,
      onTimePercentage: (onTime['percentage'] as num?)?.toDouble(),
      pendingBySubject: [
        for (final s in json['pending_by_subject'] as List<dynamic>)
          SubjectLoad(
            (s as Map<String, dynamic>)['subject_name'] as String,
            s['pending'] as int,
          ),
      ],
      upcoming: [
        for (final t in json['upcoming'] as List<dynamic>)
          AcademicTask.fromJson(t as Map<String, dynamic>),
      ],
    );
  }

  final int completed;
  final int pending;
  final int overdue;
  final List<WeeklyCompletion> completedByWeek;
  final int onTimeCompleted;
  final int onTime;

  /// Null si no hay completadas en el período.
  final double? onTimePercentage;
  final List<SubjectLoad> pendingBySubject;
  final List<AcademicTask> upcoming;
}

/// GET /academic/statistics (RF-PRF-01).
class StatisticsService {
  StatisticsService(this._dio);

  final Dio _dio;

  /// Con [StatisticsPeriod.academicPeriod] y sin período definido, la API
  /// responde `404` con el motivo.
  Future<ProfileStatistics> load(StatisticsPeriod period) => apiGuard(() async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/academic/statistics',
      queryParameters: {
        'period': switch (period) {
          StatisticsPeriod.week => 'week',
          StatisticsPeriod.month => 'month',
          StatisticsPeriod.academicPeriod => 'academic_period',
        },
      },
    );
    return ProfileStatistics.fromJson(response.data!);
  });
}

final StatisticsService statisticsService = StatisticsService(apiDio);
