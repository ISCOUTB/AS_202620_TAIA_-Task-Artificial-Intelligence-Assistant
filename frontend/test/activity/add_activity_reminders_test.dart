import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/bogota_time.dart';
import 'package:taia/features/activity/add_activity_screen.dart';
import 'package:taia/features/reminders/reminder_option.dart';
import 'package:taia/features/tasks/subjects_service.dart';
import 'package:taia/features/tasks/tasks_service.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

Map<String, dynamic> _created(RequestOptions request) {
  final body = request.data as Map<String, dynamic>;
  return {
    'id': 't1',
    'subject_id': 's1',
    'subject_name': 'Física',
    'type': body['type'],
    'title': body['title'],
    'description': body['description'],
    'due_at': body['due_at'],
    'completed_at': null,
    'created_at': '2026-10-05T15:00:00Z',
    'status': 'pending',
    'priority': 'low',
  };
}

Future<FakeApi> _pump(WidgetTester tester) async {
  useTallScreen(tester);
  final api = FakeApi(
    routes({
      'GET /academic/subjects': (_) => const FakeResponse(200, [
        {'id': 's1', 'name': 'Física'},
      ]),
      'GET /notifications/unread-count': (_) =>
          const FakeResponse(200, {'unread_count': 0}),
      'POST /academic/tasks': (r) => FakeResponse(201, _created(r)),
    }),
  );
  final dio = api.dio();
  await tester.pumpWidget(
    MaterialApp(
      home: AddActivityScreen(
        tasksService: TasksService(dio),
        subjectsService: SubjectsService(dio),
      ),
    ),
  );
  await pumpFrames(tester);
  await tester.enterText(find.byType(TextFormField).first, 'Informe');
  return api;
}

Map<String, dynamic>? _postedReminders(FakeApi api) {
  final post = api.requests.where((r) => r.method == 'POST').single;
  return (post.body as Map<String, dynamic>)['reminders']
      as Map<String, dynamic>?;
}

void main() {
  // 10:00 del 5 de octubre de 2026 en Colombia.
  setUp(() => clock = () => DateTime.utc(2026, 10, 5, 15));
  tearDown(() => clock = DateTime.now);

  testWidgets('RF-TAR-02 · la política por defecto va preseleccionada', (
    tester,
  ) async {
    final api = await _pump(tester);

    await tester.tap(find.text('Crear actividad'));
    await pumpFrames(tester);

    expect(_postedReminders(api), {'mode': 'default'});
  });

  testWidgets('RF-TAR-02 · crear sin recordatorios', (tester) async {
    final api = await _pump(tester);

    await tester.tap(find.text('Ninguno'));
    await pumpFrames(tester);
    await tester.tap(find.text('Crear actividad'));
    await pumpFrames(tester);

    expect(_postedReminders(api), {'mode': 'none'});
  });

  testWidgets(
    'RF-TAR-02 · con fechas propias exige al menos una antes de crear',
    (tester) async {
      final api = await _pump(tester);

      await tester.tap(find.text('Elegir fechas'));
      await pumpFrames(tester);
      await tester.tap(find.text('Crear actividad'));
      await pumpFrames(tester);

      expect(
        find.text('Agrega al menos una fecha de recordatorio.'),
        findsOneWidget,
      );
      expect(api.requests.where((r) => r.method == 'POST'), isEmpty);
    },
  );

  test('RF-TAR-02 · las fechas propias se envían en hora de Colombia', () {
    final option = ReminderOption(ReminderMode.custom, [
      DateTime(2026, 10, 6, 18),
      DateTime(2026, 10, 7, 8, 30),
    ]);

    expect(option.toJson(), {
      'mode': 'custom',
      'custom_at': ['2026-10-06T18:00:00-05:00', '2026-10-07T08:30:00-05:00'],
    });
  });
}
