import '../../core/bogota_time.dart';

/// Recordatorio devuelto por `/reminders` (RF-REC-03).
class Reminder {
  const Reminder({
    required this.id,
    required this.taskId,
    required this.scheduledAt,
    required this.customMessage,
    required this.origin,
    required this.status,
  });

  factory Reminder.fromJson(Map<String, dynamic> json) => Reminder(
    id: json['id'] as String,
    taskId: json['task_id'] as String,
    scheduledAt: parseApiDateTime(json['scheduled_at'] as String),
    customMessage: json['custom_message'] as String?,
    origin: json['origin'] as String,
    status: json['status'] as String,
  );

  final String id;
  final String taskId;
  final DateTime scheduledAt;

  /// Mensaje que escribió el estudiante; null si usa el mensaje por defecto.
  final String? customMessage;

  /// `automatic` (política por defecto) o `custom`.
  final String origin;

  /// `pending`, `sent` o `cancelled`.
  final String status;

  /// Solo un recordatorio pendiente se edita o se elimina (RF-REC-04, 05).
  bool get isPending => status == 'pending';

  bool get isAutomatic => origin == 'automatic';

  /// Texto para mostrar: el mensaje propio o, sin él, de dónde viene.
  String get displayMessage =>
      customMessage ??
      (isAutomatic ? 'Recordatorio automático' : 'Recordatorio');
}
