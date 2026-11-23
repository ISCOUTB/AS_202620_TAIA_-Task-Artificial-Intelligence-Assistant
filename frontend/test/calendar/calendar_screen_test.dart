import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/bogota_time.dart';
import 'package:taia/features/calendar/calendar_screen.dart';
import 'package:taia/features/calendar/calendar_service.dart';
import 'package:taia/features/tasks/subjects_service.dart';
import 'package:taia/features/tasks/tasks_service.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

Future<FakeApi> _pump(WidgetTester tester) async {
  useTallScreen(tester);
  final api = FakeApi(
    routes({
      'GET /notifications/unread-count': (_) =>
          const FakeResponse(200, {'unread_count': 0}),
      'GET /academic/calendar': (r) => FakeResponse(200, {
        'start': r.queryParameters['start'],
        'end': r.queryParameters['end'],
        'tasks':
            const {
              '2026-10-01',
              '2026-10-05',
            }.contains(r.queryParameters['start'])
            ? [taskJson(title: 'Informe', dueAt: '2026-10-06T04:59:00Z')]
            : [],
        'classes': [
          {
            'subject_id': 's1',
            'subject_name': 'Cálculo',
            'starts_at': '2026-10-05T08:00:00-05:00',
            'ends_at': '2026-10-05T10:00:00-05:00',
            'room': 'A-201',
          },
        ],
      }),
    }),
  );
  final dio = api.dio();
  await tester.pumpWidget(
    MaterialApp(
      home: CalendarScreen(
        tasksService: TasksService(dio),
        subjectsService: SubjectsService(dio),
        calendarService: CalendarService(dio),
      ),
    ),
  );
  await pumpFrames(tester);
  return api;
}

List<Map<String, dynamic>> _ranges(FakeApi api) => [
  for (final r in api.requests.where((r) => r.path == '/academic/calendar'))
    r.query,
];

void main() {
  // 10:00 del 5 de octubre de 2026 en Colombia.
  setUp(() => clock = () => DateTime.utc(2026, 10, 5, 15));
  tearDown(() => clock = DateTime.now);

  testWidgets(
    'RF-TAR-11 · la Agenda abre en la semana y junta clases y tareas',
    (tester) async {
      final api = await _pump(tester);

      expect(_ranges(api), [
        {'start': '2026-10-05', 'end': '2026-10-11'},
      ]);
      expect(find.text('Tu agenda'), findsOneWidget);
      // En la línea de tiempo de la semana y en la agenda del día.
      expect(find.text('Cálculo'), findsWidgets);
      expect(find.text('Clase hasta las 10:00 a. m. · A-201'), findsOneWidget);
      expect(find.text('Informe'), findsWidgets);
      expect(find.text('Editar horario'), findsOneWidget);
    },
  );

  testWidgets('RF-TAR-11 · al pasar de mes pide el rango nuevo', (
    tester,
  ) async {
    final api = await _pump(tester);
    await tester.tap(find.text('Mes'));
    await pumpFrames(tester);
    expect(_ranges(api).last, {'start': '2026-10-01', 'end': '2026-10-31'});

    await tester.tap(find.byTooltip('Mes siguiente'));
    await pumpFrames(tester);

    expect(_ranges(api).last, {'start': '2026-11-01', 'end': '2026-11-30'});
  });
}
