import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
import '../../core/bogota_time.dart';
import 'reminder.dart';

class RemindersService {
  RemindersService(this._dio);

  final Dio _dio;

  /// GET /reminders.
  Future<List<Reminder>> list() => apiGuard(() async {
    final response = await _dio.get<List<dynamic>>('/reminders');
    return (response.data ?? const [])
        .map((e) => Reminder.fromJson(e as Map<String, dynamic>))
        .toList();
  });

  /// Recordatorios de una actividad, del más cercano al más lejano.
  ///
  /// `GET /reminders` todavía no filtra por actividad (RF-REC-03), así que el
  /// filtro se hace aquí.
  Future<List<Reminder>> listForTask(String taskId) async {
    final all = await list();
    return all.where((r) => r.taskId == taskId).toList()
      ..sort((a, b) => a.scheduledAt.compareTo(b.scheduledAt));
  }

  /// POST /reminders (RF-REC-01).
  Future<Reminder> create({
    required String taskId,
    required String message,
    required DateTime scheduledAt,
  }) => apiGuard(() async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/reminders',
      data: {
        'task_id': taskId,
        'message': message,
        'scheduled_at': formatApiDateTime(scheduledAt),
      },
    );
    return Reminder.fromJson(response.data!);
  });

  /// PATCH /reminders/{id} (RF-REC-04).
  Future<Reminder> update(
    String id, {
    required String message,
    required DateTime scheduledAt,
  }) => apiGuard(() async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/reminders/$id',
      data: {
        'message': message,
        'scheduled_at': formatApiDateTime(scheduledAt),
      },
    );
    return Reminder.fromJson(response.data!);
  });

  /// DELETE /reminders/{id} (RF-REC-05).
  Future<void> delete(String id) =>
      apiGuard(() => _dio.delete<void>('/reminders/$id'));
}

final RemindersService remindersService = RemindersService(apiDio);
