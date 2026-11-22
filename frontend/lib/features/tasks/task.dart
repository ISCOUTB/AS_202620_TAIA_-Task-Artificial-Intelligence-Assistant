import '../../core/bogota_time.dart';

/// Estado derivado de la tarea (lo calcula el backend).
enum TaskStatus { pending, completed, overdue }

enum TaskType { task, exam }

/// Tarea o examen devuelto por `/academic/tasks`.
class AcademicTask {
  const AcademicTask({
    required this.id,
    required this.subjectId,
    required this.subjectName,
    required this.type,
    required this.title,
    required this.dueAt,
    required this.status,
    this.description,
    this.completedAt,
    this.createdAt,
    this.priority,
  });

  factory AcademicTask.fromJson(Map<String, dynamic> json) {
    return AcademicTask(
      id: json['id'] as String,
      subjectId: json['subject_id'] as String,
      subjectName: json['subject_name'] as String,
      type: json['type'] == 'exam' ? TaskType.exam : TaskType.task,
      title: json['title'] as String,
      description: json['description'] as String?,
      dueAt: parseApiDateTime(json['due_at'] as String),
      completedAt: parseApiDateTimeOrNull(json['completed_at']),
      createdAt: parseApiDateTimeOrNull(json['created_at']),
      status: switch (json['status']) {
        'completed' => TaskStatus.completed,
        'overdue' => TaskStatus.overdue,
        _ => TaskStatus.pending,
      },
      priority: json['priority'] as String?,
    );
  }

  final String id;
  final String subjectId;
  final String subjectName;
  final TaskType type;
  final String title;
  final String? description;
  final DateTime dueAt;
  final DateTime? completedAt;

  /// Cuándo se creó la actividad.
  final DateTime? createdAt;
  final TaskStatus status;

  /// "high", "medium" o "low"; solo las pendientes tienen prioridad.
  final String? priority;

  /// Urgente: pendiente y con menos de 48 horas para la entrega.
  bool get isUrgent => priority == 'high';
}