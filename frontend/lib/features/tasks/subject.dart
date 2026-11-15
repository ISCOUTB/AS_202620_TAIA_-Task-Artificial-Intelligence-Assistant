/// Asignatura devuelta por `/academic/subjects`.
class Subject {
  const Subject({required this.id, required this.name});

  factory Subject.fromJson(Map<String, dynamic> json) =>
      Subject(id: json['id'] as String, name: json['name'] as String);

  final String id;
  final String name;
}