import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
import 'subject.dart';

class SubjectsService {
  SubjectsService(this._dio);

  final Dio _dio;

  /// GET /academic/subjects: asignaturas activas del usuario.
  Future<List<Subject>> list() => apiGuard(() async {
    final response = await _dio.get<List<dynamic>>('/academic/subjects');
    return (response.data ?? const [])
        .map((e) => Subject.fromJson(e as Map<String, dynamic>))
        .toList();
  });

  /// POST /academic/subjects. Responde 409 si ya existe una con ese nombre.
  Future<Subject> create({required String name, String? teacher}) =>
      apiGuard(() async {
        final response = await _dio.post<Map<String, dynamic>>(
          '/academic/subjects',
          data: {
            'name': name,
            if (teacher != null && teacher.isNotEmpty) 'teacher': teacher,
          },
        );
        return Subject.fromJson(response.data!);
      });
}

final SubjectsService subjectsService = SubjectsService(apiDio);