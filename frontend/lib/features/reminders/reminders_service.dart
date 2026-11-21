import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
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
}

final RemindersService remindersService = RemindersService(apiDio);