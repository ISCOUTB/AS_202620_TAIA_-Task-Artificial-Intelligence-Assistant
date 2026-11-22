import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/bogota_time.dart';
import 'package:taia/features/reminders/reminders_service.dart';
import 'package:taia/features/tasks/subjects_service.dart';
import 'package:taia/features/tasks/task.dart';
import 'package:taia/features/tasks/tasks_service.dart';
import 'package:taia/features/tasks/widgets/task_edit_sheet.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

Map<String, dynamic> reminderJson({
  String id = 'r1',
  String taskId = 't1',
  String message = 'Repasar',
  String scheduledAt = '2026-10-08T23:00:00Z',
  bool completed = false,
}) => {
  'id': id,
  'user_id': 'u1',
  'message': message,
  'scheduled_at': scheduledAt,
  'is_completed': completed,
  'task_id': taskId,
};

FakeResponse _subjects(RequestOptions _) => const FakeResponse(200, [
  {'id': 's1', 'name': 'Física'},
]);

/// Abre la hoja de una actividad con la API falsa y devuelve el resultado.
Future<List<TaskEditResult?>> _open(
  WidgetTester tester,
  FakeApi api, {
  Map<String, dynamic>? task,
}) async {
  useTallScreen(tester);
  final dio = api.dio();
  final result = <TaskEditResult?>[];
  await tester.pumpWidget(
    Launcher<TaskEditResult>(
      result: result,
      open: (context) => showTaskEditSheet(
        context,
        AcademicTask.fromJson(task ?? taskJson()),
        tasksService: TasksService(dio),
        subjectsService: SubjectsService(dio),
        remindersService: RemindersService(dio),
      ),
    ),
  );
  await tester.tap(find.text('abrir'));
  await pumpFrames(tester);
  return result;
}

List<RecordedRequest> _writes(FakeApi api) =>
    api.requests.where((r) => r.method != 'GET').toList();

void main() {
  // 10:00 del 5 de octubre de 2026 en Colombia.
  setUp(() => clock = () => DateTime.utc(2026, 10, 5, 15));
  tearDown(() => clock = DateTime.now);

  testWidgets('RF-TAR-05 · el detalle muestra la creación y sus recordatorios', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'GET /academic/subjects': _subjects,
        'GET /reminders': (_) => FakeResponse(200, [
          reminderJson(message: 'Repasar capítulo 3'),
          reminderJson(id: 'r2', taskId: 'otra', message: 'De otra tarea'),
        ]),
      }),
    );

    await _open(
      tester,
      api,
      task: taskJson(
        status: 'completed',
        completedAt: '2026-10-04T20:30:00Z',
        priority: null,
      ),
    );

    expect(find.text('Creada el 1 de oct · 10:00 a. m.'), findsOneWidget);
    expect(find.text('Completada el 4 de oct · 03:30 p. m.'), findsOneWidget);
    expect(find.text('Repasar capítulo 3'), findsOneWidget);
    expect(find.text('De otra tarea'), findsNothing);
  });

  testWidgets('RF-TAR-06 · editar envía los cambios sin reenviar la fecha', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'GET /academic/subjects': _subjects,
        'GET /reminders': (_) => const FakeResponse(200, []),
        'PATCH /academic/tasks/t1': (_) =>
            FakeResponse(200, taskJson(title: 'Taller 4')),
      }),
    );
    final result = await _open(tester, api);

    await tester.enterText(find.byType(TextFormField).first, 'Taller 4');
    await tester.tap(find.text('Guardar cambios'));
    await pumpFrames(tester);

    final body = _writes(api).single.body as Map<String, dynamic>;
    expect(body['title'], 'Taller 4');
    expect(body.containsKey('due_at'), isFalse);
    expect(result.single?.task?.title, 'Taller 4');
  });

  testWidgets('RF-TAR-07 · marcar como completada llama a complete', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'GET /academic/subjects': _subjects,
        'GET /reminders': (_) => const FakeResponse(200, []),
        'PATCH /academic/tasks/t1': (_) => FakeResponse(200, taskJson()),
        'PATCH /academic/tasks/t1/complete': (_) =>
            FakeResponse(200, taskJson(status: 'completed')),
      }),
    );
    final result = await _open(tester, api);

    await tester.tap(find.text('Completada'));
    await tester.tap(find.text('Guardar cambios'));
    await pumpFrames(tester);

    expect(_writes(api).map((r) => r.path), [
      '/academic/tasks/t1',
      '/academic/tasks/t1/complete',
    ]);
    expect(result.single?.task?.status, TaskStatus.completed);
  });

  testWidgets('RF-TAR-08 · volver a pendiente llama a reopen', (tester) async {
    final api = FakeApi(
      routes({
        'GET /academic/subjects': _subjects,
        'GET /reminders': (_) => const FakeResponse(200, []),
        'PATCH /academic/tasks/t1': (_) =>
            FakeResponse(200, taskJson(status: 'completed')),
        'PATCH /academic/tasks/t1/reopen': (_) => FakeResponse(200, taskJson()),
      }),
    );
    await _open(
      tester,
      api,
      task: taskJson(status: 'completed', completedAt: '2026-10-04T20:30:00Z'),
    );

    await tester.tap(find.text('Pendiente'));
    await tester.tap(find.text('Guardar cambios'));
    await pumpFrames(tester);

    expect(_writes(api).last.path, '/academic/tasks/t1/reopen');
  });

  testWidgets('RF-TAR-10 · eliminar pide confirmación antes de enviar', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'GET /academic/subjects': _subjects,
        'GET /reminders': (_) => const FakeResponse(200, []),
        'DELETE /academic/tasks/t1': (_) => const FakeResponse(204),
      }),
    );
    final result = await _open(tester, api);

    await tester.tap(find.text('Eliminar tarea'));
    await pumpFrames(tester);
    expect(find.text('¿Eliminar esta tarea?'), findsOneWidget);
    expect(_writes(api), isEmpty);

    await tester.tap(find.text('Cancelar'));
    await pumpFrames(tester);
    expect(_writes(api), isEmpty);

    await tester.tap(find.text('Eliminar tarea'));
    await pumpFrames(tester);
    await tester.tap(find.widgetWithText(FilledButton, 'Eliminar'));
    await pumpFrames(tester);

    expect(_writes(api).single.method, 'DELETE');
    expect(result.single?.deleted, isTrue);
  });

  testWidgets('RF-TAR-10 · un error al eliminar se muestra en español', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'GET /academic/subjects': _subjects,
        'GET /reminders': (_) => const FakeResponse(200, []),
        'DELETE /academic/tasks/t1': (_) =>
            const FakeResponse(404, {'detail': 'La tarea no existe.'}),
      }),
    );
    await _open(tester, api);

    await tester.tap(find.text('Eliminar tarea'));
    await pumpFrames(tester);
    await tester.tap(find.widgetWithText(FilledButton, 'Eliminar'));
    await pumpFrames(tester);

    expect(find.text('La tarea no existe.'), findsOneWidget);
  });

  group('recordatorios de la actividad', () {
    testWidgets('RF-REC-01 · crear un recordatorio en hora de Colombia', (
      tester,
    ) async {
      final api = FakeApi(
        routes({
          'GET /academic/subjects': _subjects,
          'GET /reminders': (_) => const FakeResponse(200, []),
          'POST /reminders': (r) => FakeResponse(
            201,
            reminderJson(
              id: 'r9',
              message: 'Imprimir',
              scheduledAt: '2026-10-05T16:00:00Z',
            ),
          ),
        }),
      );
      await _open(tester, api);

      await tester.tap(find.text('Agregar recordatorio'));
      await pumpFrames(tester);
      await tester.enterText(
        find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(TextFormField),
        ),
        'Imprimir',
      );
      await tester.tap(find.text('Guardar'));
      await pumpFrames(tester);

      final body = _writes(api).single.body as Map<String, dynamic>;
      expect(body, {
        'task_id': 't1',
        'message': 'Imprimir',
        // La hora propuesta es la siguiente en punto: 11:00 de Colombia.
        'scheduled_at': '2026-10-05T11:00:00-05:00',
      });
      expect(find.text('Imprimir'), findsOneWidget);
    });

    testWidgets('RF-REC-01 · no se crean recordatorios tras la fecha límite', (
      tester,
    ) async {
      final api = FakeApi(
        routes({
          'GET /academic/subjects': _subjects,
          'GET /reminders': (_) => const FakeResponse(200, []),
        }),
      );
      // Vence hoy a las 10:30, antes de la hora propuesta (11:00).
      await _open(tester, api, task: taskJson(dueAt: '2026-10-05T15:30:00Z'));

      await tester.tap(find.text('Agregar recordatorio'));
      await pumpFrames(tester);
      await tester.enterText(
        find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(TextFormField),
        ),
        'Tarde',
      );
      await tester.tap(find.text('Guardar'));
      await pumpFrames(tester);

      expect(
        find.text('El recordatorio debe ser antes de la fecha límite.'),
        findsOneWidget,
      );
      expect(_writes(api), isEmpty);
    });

    testWidgets('RF-REC-01 · una actividad completada no admite nuevos', (
      tester,
    ) async {
      final api = FakeApi(
        routes({
          'GET /academic/subjects': _subjects,
          'GET /reminders': (_) => const FakeResponse(200, []),
        }),
      );
      await _open(
        tester,
        api,
        task: taskJson(status: 'completed', completedAt: '2026-10-04T20:30:00Z'),
      );

      expect(find.text('Agregar recordatorio'), findsNothing);
    });

    testWidgets('RF-REC-04 · editar el mensaje de uno pendiente', (
      tester,
    ) async {
      final api = FakeApi(
        routes({
          'GET /academic/subjects': _subjects,
          'GET /reminders': (_) => FakeResponse(200, [reminderJson()]),
          'PATCH /reminders/r1': (_) =>
              FakeResponse(200, reminderJson(message: 'Repasar todo')),
        }),
      );
      await _open(tester, api);

      await tester.tap(find.byTooltip('Editar recordatorio'));
      await pumpFrames(tester);
      await tester.enterText(
        find.descendant(
          of: find.byType(AlertDialog),
          matching: find.byType(TextFormField),
        ),
        'Repasar todo',
      );
      await tester.tap(find.text('Guardar'));
      await pumpFrames(tester);

      final body = _writes(api).single.body as Map<String, dynamic>;
      expect(body['message'], 'Repasar todo');
      expect(body['scheduled_at'], '2026-10-08T18:00:00-05:00');
      expect(find.text('Repasar todo'), findsOneWidget);
    });

    testWidgets('RF-REC-05 · eliminar uno pendiente; el enviado no se toca', (
      tester,
    ) async {
      final api = FakeApi(
        routes({
          'GET /academic/subjects': _subjects,
          'GET /reminders': (_) => FakeResponse(200, [
            reminderJson(),
            reminderJson(
              id: 'r2',
              message: 'Ya avisó',
              scheduledAt: '2026-10-04T23:00:00Z',
              completed: true,
            ),
          ]),
          'DELETE /reminders/r1': (_) => const FakeResponse(204),
        }),
      );
      await _open(tester, api);

      // Solo el pendiente tiene acciones.
      expect(find.byTooltip('Eliminar recordatorio'), findsOneWidget);
      expect(find.text('4 de oct · 06:00 p. m. · enviado'), findsOneWidget);

      await tester.tap(find.byTooltip('Eliminar recordatorio'));
      await pumpFrames(tester);

      expect(_writes(api).single.path, '/reminders/r1');
      expect(find.text('Repasar'), findsNothing);
      expect(find.text('Ya avisó'), findsOneWidget);
    });
  });
}
