import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
import '../../core/bogota_time.dart';
import 'task.dart';

class TaskPage {
  const TaskPage({required this.items, required this.total});

  final List<AcademicTask> items;
  final int total;
}

class TasksService {
  TasksService(this._dio);

  final Dio _dio;

  /// GET /academic/tasks. Viene ordenada por fecha límite.
  Future<TaskPage> list({
    TaskStatus? status,
    DateTime? dueFrom,
    DateTime? dueTo,
    String? query,
    String? subjectId,
    int limit = 20,
    int offset = 0,
  }) => apiGuard(() async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/academic/tasks',
      queryParameters: {
        if (status != null) 'status': status.name,
        if (dueFrom != null) 'due_from': formatApiDateTime(dueFrom),
        if (dueTo != null) 'due_to': formatApiDateTime(dueTo),
        if (query != null && query.isNotEmpty) 'q': query,
        'subject_id': ?subjectId,
        'limit': limit,
        'offset': offset,
      },
    );
    final data = response.data!;
    return TaskPage(
      items: (data['items'] as List<dynamic>)
          .map((e) => AcademicTask.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: data['total'] as int,
    );
  });

  /// Todas las tareas del usuario, pidiendo páginas de 100 (hasta 500).
  Future<List<AcademicTask>> listAll() => apiGuard(() async {
    final all = <AcademicTask>[];
    var offset = 0;
    while (true) {
      final page = await list(limit: 100, offset: offset);
      all.addAll(page.items);
      offset += page.items.length;
      if (page.items.isEmpty || offset >= page.total || offset >= 500) break;
    }
    return all;
  });

  /// POST /academic/tasks. La fecha límite debe ser posterior a ahora.
  Future<AcademicTask> create({
    required String subjectId,
    required String title,
    required String description,
    required DateTime dueAt,
    required TaskType type,
  }) => apiGuard(() async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/academic/tasks',
      data: {
        'subject_id': subjectId,
        'title': title,
        'description': description,
        'due_at': formatApiDateTime(dueAt),
        'type': type.name,
      },
    );
    return AcademicTask.fromJson(response.data!);
  });

  /// PATCH /academic/tasks/{id}.
  ///
  /// [dueAt] solo se envía si cambió: el backend rechaza cualquier fecha que
  /// no sea futura, así que reenviar la de una tarea atrasada o completada
  /// haría fallar la edición.
  Future<AcademicTask> update(
    String id, {
    required String title,
    required String description,
    required String subjectId,
    required TaskType type,
    DateTime? dueAt,
  }) => apiGuard(() async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/academic/tasks/$id',
      data: {
        'title': title,
        'description': description,
        'subject_id': subjectId,
        'type': type.name,
        if (dueAt != null) 'due_at': formatApiDateTime(dueAt),
      },
    );
    return AcademicTask.fromJson(response.data!);
  });

  /// PATCH /academic/tasks/{id}/complete.
  Future<AcademicTask> complete(String id) => apiGuard(() async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/academic/tasks/$id/complete',
    );
    return AcademicTask.fromJson(response.data!);
  });

  /// PATCH /academic/tasks/{id}/reopen.
  Future<AcademicTask> reopen(String id) => apiGuard(() async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/academic/tasks/$id/reopen',
    );
    return AcademicTask.fromJson(response.data!);
  });

  /// DELETE /academic/tasks/{id}.
  Future<void> delete(String id) =>
      apiGuard(() => _dio.delete<void>('/academic/tasks/$id'));
}

final TasksService tasksService = TasksService(apiDio);