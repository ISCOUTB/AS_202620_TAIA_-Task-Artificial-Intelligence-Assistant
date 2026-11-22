import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
import '../../core/bogota_time.dart';

/// Notificación de la bandeja (RF-NOT-03).
class AppNotification {
  const AppNotification({
    required this.id,
    required this.message,
    required this.createdAt,
    required this.read,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) =>
      AppNotification(
        id: json['id'] as String,
        message: json['message'] as String,
        createdAt: parseApiDateTime(json['created_at'] as String),
        read: json['read'] as bool,
      );

  final String id;
  final String message;
  final DateTime createdAt;
  final bool read;

  AppNotification markedRead() => AppNotification(
    id: id,
    message: message,
    createdAt: createdAt,
    read: true,
  );
}

/// Bandeja de notificaciones: `/notifications` (RF-NOT-03).
class NotificationsService {
  NotificationsService(this._dio);

  final Dio _dio;

  /// GET /notifications, de la más reciente a la más antigua.
  Future<List<AppNotification>> list({int limit = 50}) => apiGuard(() async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/notifications',
      queryParameters: {'limit': limit},
    );
    return (response.data!['items'] as List<dynamic>)
        .map((e) => AppNotification.fromJson(e as Map<String, dynamic>))
        .toList();
  });

  /// GET /notifications/unread-count.
  Future<int> unreadCount() => apiGuard(() async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/notifications/unread-count',
    );
    return response.data!['unread_count'] as int;
  });

  /// PATCH /notifications/{id}/read.
  Future<void> markRead(String id) =>
      apiGuard(() => _dio.patch<void>('/notifications/$id/read'));

  /// PATCH /notifications/read-all.
  Future<void> markAllRead() =>
      apiGuard(() => _dio.patch<void>('/notifications/read-all'));
}

final NotificationsService notificationsService = NotificationsService(apiDio);
