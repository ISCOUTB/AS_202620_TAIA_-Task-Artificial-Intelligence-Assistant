import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/api_error.dart';
import 'package:taia/features/tasks/task.dart';
import 'package:taia/features/tasks/tasks_service.dart';

import '../support/fake_api.dart';

void main() {
  group('RT-03 · fechas de las actividades', () {
    test('la fecha límite se lee en hora de Colombia', () async {
      final api = FakeApi(
        (_) => FakeResponse(200, taskJson(dueAt: '2026-10-06T02:00:00Z')),
      );

      final task = await TasksService(api.dio()).complete('t1');

      expect(task.dueAt, DateTime(2026, 10, 5, 21));
      expect(task.createdAt, DateTime(2026, 10, 1, 10));
    });

    test('al crear, la fecha límite viaja con -05:00', () async {
      final api = FakeApi((_) => FakeResponse(201, taskJson()));

      await TasksService(api.dio()).create(
        subjectId: 's1',
        title: 'Taller 3',
        description: '',
        dueAt: DateTime(2026, 10, 5, 23, 59),
        type: TaskType.task,
      );

      final body = api.requests.single.body as Map<String, dynamic>;
      expect(body['due_at'], '2026-10-05T23:59:00-05:00');
    });

    test('los filtros de fecha viajan con -05:00', () async {
      final api = FakeApi(
        (_) => const FakeResponse(200, {
          'items': [],
          'total': 0,
          'limit': 20,
          'offset': 0,
        }),
      );

      await TasksService(api.dio()).list(
        dueFrom: DateTime(2026, 10, 5),
        dueTo: DateTime(2026, 10, 5, 23, 59, 59),
      );

      final query = api.requests.single.query;
      expect(query['due_from'], '2026-10-05T00:00:00-05:00');
      expect(query['due_to'], '2026-10-05T23:59:59-05:00');
    });
  });

  test('RF-TAR-04 · varios estados viajan como status=a&status=b', () async {
    final api = FakeApi(
      (_) => const FakeResponse(200, {
        'items': [],
        'total': 0,
        'limit': 50,
        'offset': 0,
      }),
    );
    final dio = api.dio();

    await TasksService(dio)
        .list(statuses: const [TaskStatus.pending, TaskStatus.overdue]);

    expect(api.requests.single.query['status'], ['pending', 'overdue']);
    // Dio repite la clave por cada valor de la lista.
    expect(dio.options.listFormat, ListFormat.multi);
  });

  test('un error de la API llega con el detail en español', () async {
    final api = FakeApi(
      (_) => const FakeResponse(404, {'detail': 'La tarea no existe.'}),
    );

    await expectLater(
      TasksService(api.dio()).delete('t1'),
      throwsA(
        isA<ApiException>().having(
          (e) => e.message,
          'message',
          'La tarea no existe.',
        ),
      ),
    );
  });
}
