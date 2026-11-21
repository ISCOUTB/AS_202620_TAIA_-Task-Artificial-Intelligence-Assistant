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
    scheduledAt: DateTime.parse(json['scheduled_at'] as String).toLocal(),
    isCompleted: json['is_completed'] as bool? ?? false,
    taskId: json['task_id'] as String,
  );

  final String id;
  final String message;
  final DateTime scheduledAt;
  final bool isCompleted;
  final String taskId;
}