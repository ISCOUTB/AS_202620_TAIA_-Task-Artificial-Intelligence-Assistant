import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
import 'schedule_block.dart';

class ScheduleService {
  ScheduleService(this._dio);

  final Dio _dio;

  /// GET /academic/schedule-blocks: el horario semanal, o el de un día,
  /// ordenado por día y hora (RF-ASG-07).
  Future<List<ScheduleBlock>> list({Weekday? weekday}) => apiGuard(() async {
    final response = await _dio.get<List<dynamic>>(
      '/academic/schedule-blocks',
      queryParameters: {'weekday': ?weekday?.name},
    );
    return (response.data ?? const [])
        .map((e) => ScheduleBlock.fromJson(e as Map<String, dynamic>))
        .toList();
  });

  /// POST /academic/schedule-blocks (RF-ASG-06). Responde 409 si se solapa
  /// con otro bloque del mismo día.
  Future<ScheduleBlock> create({
    required String subjectId,
    required Weekday weekday,
    required TimeOfDay start,
    required TimeOfDay end,
    required String room,
  }) => apiGuard(() async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/academic/schedule-blocks',
      data: {
        'subject_id': subjectId,
        'weekday': weekday.name,
        'start_time': formatApiTime(start),
        'end_time': formatApiTime(end),
        if (room.isNotEmpty) 'room': room,
      },
    );
    return ScheduleBlock.fromJson(response.data!);
  });

  /// PATCH /academic/schedule-blocks/{id} (RF-ASG-07), con las validaciones
  /// de RF-ASG-06. Un aula vacía la borra.
  Future<ScheduleBlock> update(
    String id, {
    required String subjectId,
    required Weekday weekday,
    required TimeOfDay start,
    required TimeOfDay end,
    required String room,
  }) => apiGuard(() async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/academic/schedule-blocks/$id',
      data: {
        'subject_id': subjectId,
        'weekday': weekday.name,
        'start_time': formatApiTime(start),
        'end_time': formatApiTime(end),
        'room': room,
      },
    );
    return ScheduleBlock.fromJson(response.data!);
  });

  /// DELETE /academic/schedule-blocks/{id} (RF-ASG-07).
  Future<void> delete(String id) =>
      apiGuard(() => _dio.delete<void>('/academic/schedule-blocks/$id'));

  /// GET /academic/period (RF-ASG-08). Devuelve null si no hay período.
  Future<AcademicPeriod?> period() => apiGuard(() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/academic/period');
      return AcademicPeriod.fromJson(response.data!);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  });

  /// PUT /academic/period (RF-ASG-08). El fin debe ser posterior al inicio.
  Future<AcademicPeriod> setPeriod(DateTime start, DateTime end) =>
      apiGuard(() async {
        final response = await _dio.put<Map<String, dynamic>>(
          '/academic/period',
          data: {
            'start_date': formatApiDate(start),
            'end_date': formatApiDate(end),
          },
        );
        return AcademicPeriod.fromJson(response.data!);
      });
}

final ScheduleService scheduleService = ScheduleService(apiDio);
