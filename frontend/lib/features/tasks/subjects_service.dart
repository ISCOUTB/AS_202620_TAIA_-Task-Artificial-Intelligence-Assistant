import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
import 'subject.dart';

class SubjectsService {
  SubjectsService(this._dio);

  final Dio _dio;

  Subject _subject(Response<Map<String, dynamic>> response) =>
      Subject.fromJson(response.data!);

  /// GET /academic/subjects: las activas, o también las archivadas
  /// (RF-ASG-02).
  Future<List<Subject>> list({bool includeArchived = false}) =>
      apiGuard(() async {
        final response = await _dio.get<List<dynamic>>(
          '/academic/subjects',
          queryParameters: {if (includeArchived) 'include_archived': true},
        );
        return (response.data ?? const [])
            .map((e) => Subject.fromJson(e as Map<String, dynamic>))
            .toList();
      });

  /// GET /academic/subjects/{id}: detalle con las tareas pendientes
  /// (RF-ASG-02).
  Future<Subject> get(String id) => apiGuard(
    () async => _subject(
      await _dio.get<Map<String, dynamic>>('/academic/subjects/$id'),
    ),
  );

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
        return _subject(response);
      });

  /// PATCH /academic/subjects/{id} (RF-ASG-03). Un docente vacío lo borra.
  Future<Subject> update(
    String id, {
    required String name,
    required String teacher,
  }) => apiGuard(
    () async => _subject(
      await _dio.patch<Map<String, dynamic>>(
        '/academic/subjects/$id',
        data: {'name': name, 'teacher': teacher},
      ),
    ),
  );

  /// DELETE /academic/subjects/{id} (RF-ASG-04). Responde 409 si tiene
  /// actividades.
  Future<void> delete(String id) =>
      apiGuard(() => _dio.delete<void>('/academic/subjects/$id'));

  /// POST /academic/subjects/{id}/archive (RF-ASG-05).
  Future<Subject> archive(String id) => apiGuard(
    () async => _subject(
      await _dio.post<Map<String, dynamic>>('/academic/subjects/$id/archive'),
    ),
  );

  /// POST /academic/subjects/{id}/unarchive (RF-ASG-05). Responde 409 si su
  /// horario choca con el actual.
  Future<Subject> unarchive(String id) => apiGuard(
    () async => _subject(
      await _dio.post<Map<String, dynamic>>('/academic/subjects/$id/unarchive'),
    ),
  );

  /// POST /academic/subjects/{id}/aliases (RF-ASG-09).
  Future<Subject> addAlias(String id, String alias) => apiGuard(
    () async => _subject(
      await _dio.post<Map<String, dynamic>>(
        '/academic/subjects/$id/aliases',
        data: {'alias': alias},
      ),
    ),
  );

  /// DELETE /academic/subjects/{id}/aliases/{aliasId} (RF-ASG-09).
  Future<Subject> removeAlias(String id, String aliasId) => apiGuard(
    () async => _subject(
      await _dio.delete<Map<String, dynamic>>(
        '/academic/subjects/$id/aliases/$aliasId',
      ),
    ),
  );
}

final SubjectsService subjectsService = SubjectsService(apiDio);
