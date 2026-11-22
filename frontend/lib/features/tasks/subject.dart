/// Alias corto de una asignatura (RF-ASG-09).
class SubjectAlias {
  const SubjectAlias({required this.id, required this.alias});

  factory SubjectAlias.fromJson(Map<String, dynamic> json) =>
      SubjectAlias(id: json['id'] as String, alias: json['alias'] as String);

  final String id;
  final String alias;
}

/// Asignatura devuelta por `/academic/subjects`.
class Subject {
  const Subject({
    required this.id,
    required this.name,
    this.teacher,
    this.archived = false,
    this.aliases = const [],
    this.pendingTasks = 0,
  });

  factory Subject.fromJson(Map<String, dynamic> json) => Subject(
    id: json['id'] as String,
    name: json['name'] as String,
    teacher: json['teacher'] as String?,
    archived: json['archived'] as bool? ?? false,
    aliases: [
      for (final alias in json['aliases'] as List<dynamic>? ?? const [])
        SubjectAlias.fromJson(alias as Map<String, dynamic>),
    ],
    pendingTasks: json['pending_tasks'] as int? ?? 0,
  );

  final String id;
  final String name;
  final String? teacher;

  /// Una asignatura archivada no acepta tareas nuevas (RF-ASG-05).
  final bool archived;
  final List<SubjectAlias> aliases;

  /// Tareas pendientes que calcula el backend (RF-ASG-02).
  final int pendingTasks;
}
