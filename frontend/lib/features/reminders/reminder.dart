import '../../core/bogota_time.dart';

/// Recordatorio devuelto por `/reminders`.
class Reminder {
  const Reminder({
    required this.id,
    required this.message,
    required this.scheduledAt,
    required this.isCompleted,
    required this.taskId,
  });

  factory Reminder.fromJson(Map<String, dynamic> json) => Reminder(
    id: json['id'] as String,
    message: json['message'] as String,
    scheduledAt: parseApiDateTime(json['scheduled_at'] as String),
    isCompleted: json['is_completed'] as bool? ?? false,
    taskId: json['task_id'] as String,
  );

  final String id;
  final String message;
  final DateTime scheduledAt;
  final bool isCompleted;
  final String taskId;
}