import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/bogota_time.dart';
import 'package:taia/features/academic/schedule_block.dart';
import 'package:taia/features/academic/schedule_screen.dart';
import 'package:taia/features/academic/schedule_service.dart';
import 'package:taia/features/tasks/subjects_service.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

Map<String, dynamic> blockJson({
  String id = 'b1',
  String subjectName = 'Física',
  String weekday = 'monday',
  String start = '08:00:00',
  String end = '10:00:00',
  String? room = 'A-201',
}) => {
  'id': id,
  'subject_id': 's1',
  'subject_name': subjectName,
  'weekday': weekday,
  'start_time': start,
  'end_time': end,
  'room': room,
};

FakeResponse _subjects(RequestOptions _) => const FakeResponse(200, [
  {'id': 's1', 'name': 'Física'},
]);

FakeResponse _noPeriod(RequestOptions _) =>
    const FakeResponse(404, {'detail': 'No hay período académico definido.'});

Future<void> _pump(WidgetTester tester, FakeApi api) async {
  useTallScreen(tester);
  final dio = api.dio();
  await tester.pumpWidget(
    MaterialApp(
      home: ScheduleScreen(
        service: ScheduleService(dio),
        subjectsService: SubjectsService(dio),
      ),
    ),
  );
  await pumpFrames(tester);
}

List<RecordedRequest> _writes(FakeApi api) =>
    api.requests.where((r) => r.method != 'GET').toList();

void main() {
  // 10:00 del 5 de octubre de 2026 en Colombia.
  setUp(() => clock = () => DateTime.utc(2026, 10, 5, 15));
  tearDown(() => clock = DateTime.now);

  testWidgets(
    'RF-ASG-07 · muestra el horario semanal por día, con la asignatura',
    (tester) async {
      final api = FakeApi(
        routes({
          'GET /academic/schedule-blocks': (_) => FakeResponse(200, [
            blockJson(),
            blockJson(
              id: 'b2',
              subjectName: 'Cálculo',
              weekday: 'wednesday',
              start: '14:00:00',
              end: '16:00:00',
              room: null,
            ),
          ]),
          'GET /academic/period': _noPeriod,
          'GET /academic/subjects': _subjects,
        }),
      );
      await _pump(tester, api);

      expect(find.text('LUNES'), findsOneWidget);
      expect(find.text('MIÉRCOLES'), findsOneWidget);
      expect(find.text('MARTES'), findsNothing);
      expect(find.text('08:00 a. m. – 10:00 a. m. · A-201'), findsOneWidget);
      expect(find.text('02:00 p. m. – 04:00 p. m.'), findsOneWidget);
      // Sin período, el 404 no es un error: se ofrece definirlo.
      expect(find.text('Sin definir'), findsOneWidget);
    },
  );

  test('RF-ASG-07 · consulta el horario de un día', () async {
    final api = FakeApi((_) => const FakeResponse(200, []));
    await ScheduleService(api.dio()).list(weekday: Weekday.friday);

    expect(api.requests.single.query, {'weekday': 'friday'});
  });

  testWidgets(
    'RF-ASG-06 · una clase en varios días crea un bloque por día y avisa el que choca',
    (tester) async {
      final api = FakeApi(
        routes({
          'GET /academic/schedule-blocks': (_) => const FakeResponse(200, []),
          'GET /academic/period': _noPeriod,
          'GET /academic/subjects': _subjects,
          'POST /academic/schedule-blocks': (r) =>
              (r.data as Map)['weekday'] == 'tuesday'
              ? const FakeResponse(409, {
                  'detail': 'El bloque se solapa con otro del mismo día.',
                })
              : FakeResponse(201, {
                  'id': 'b9',
                  'subject_id': 's1',
                  'subject_name': 'Física',
                  'weekday': 'monday',
                  'start_time': '07:00:00',
                  'end_time': '09:00:00',
                  'room': 'B-3',
                }),
        }),
      );
      await _pump(tester, api);

      await tester.tap(find.text('Nuevo bloque'));
      await pumpFrames(tester);
      await tester.tap(find.byTooltip('Lunes'));
      await tester.tap(find.byTooltip('Martes'));
      await tester.enterText(
        find.widgetWithText(TextField, 'Aula (opcional)'),
        'B-3',
      );
      await pumpFrames(tester);
      await tester.ensureVisible(find.text('Agregar en 2 días'));
      await tester.tap(find.text('Agregar en 2 días'));
      await pumpFrames(tester);

      expect(
        [for (final r in _writes(api)) r.body],
        [
          {
            'subject_id': 's1',
            'weekday': 'monday',
            'start_time': '07:00:00',
            'end_time': '09:00:00',
            'room': 'B-3',
          },
          {
            'subject_id': 's1',
            'weekday': 'tuesday',
            'start_time': '07:00:00',
            'end_time': '09:00:00',
            'room': 'B-3',
          },
        ],
      );
      expect(find.textContaining('No se pudo el martes'), findsOneWidget);
    },
  );

  testWidgets('RF-ASG-06 · si ningún día se puede agregar, muestra el 409', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'GET /academic/schedule-blocks': (_) => const FakeResponse(200, []),
        'GET /academic/period': _noPeriod,
        'GET /academic/subjects': _subjects,
        'POST /academic/schedule-blocks': (_) => const FakeResponse(409, {
          'detail': 'El bloque se solapa con otro del mismo día.',
        }),
      }),
    );
    await _pump(tester, api);

    await tester.tap(find.text('Nuevo bloque'));
    await pumpFrames(tester);
    await tester.tap(find.byTooltip('Lunes'));
    await pumpFrames(tester);
    await tester.ensureVisible(find.text('Agregar clase'));
    await tester.tap(find.text('Agregar clase'));
    await pumpFrames(tester);

    expect(
      find.text('El bloque se solapa con otro del mismo día.'),
      findsOneWidget,
    );
  });

  test('RF-ASG-06 · un fin anterior o igual al inicio no se envía', () {
    const ten = TimeOfDay(hour: 10, minute: 0);
    const eight = TimeOfDay(hour: 8, minute: 0);

    expect(blockTimeError(ten, eight), isNotNull);
    expect(blockTimeError(ten, ten), isNotNull);
    expect(blockTimeError(eight, ten), isNull);
  });

  testWidgets('RF-ASG-07 · edita el día de un bloque y lo elimina', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'GET /academic/schedule-blocks': (_) =>
            FakeResponse(200, [blockJson()]),
        'GET /academic/period': _noPeriod,
        'GET /academic/subjects': _subjects,
        'PATCH /academic/schedule-blocks/b1': (_) =>
            FakeResponse(200, blockJson(weekday: 'tuesday')),
        'DELETE /academic/schedule-blocks/b1': (_) => const FakeResponse(204),
      }),
    );
    await _pump(tester, api);

    await tester.tap(find.text('Física'));
    await pumpFrames(tester);
    await tester.tap(find.text('Lunes'));
    await pumpFrames(tester);
    await tester.tap(find.text('Martes').last);
    await pumpFrames(tester);
    await tester.tap(find.text('Guardar'));
    await pumpFrames(tester);

    final patch = _writes(api).single;
    expect(patch.path, '/academic/schedule-blocks/b1');
    expect(patch.body, containsPair('weekday', 'tuesday'));
    expect(patch.body, containsPair('room', 'A-201'));

    await tester.tap(find.text('Física'));
    await pumpFrames(tester);
    await tester.tap(find.text('Eliminar bloque'));
    await pumpFrames(tester);
    await tester.tap(find.text('Eliminar'));
    await pumpFrames(tester);

    expect(_writes(api).last.method, 'DELETE');
    expect(find.text('Editar bloque'), findsNothing);
  });

  testWidgets('RF-ASG-08 · muestra y reemplaza el período académico', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'GET /academic/schedule-blocks': (_) => const FakeResponse(200, []),
        'GET /academic/period': (_) => const FakeResponse(200, {
          'start_date': '2026-08-03',
          'end_date': '2026-11-28',
        }),
        'GET /academic/subjects': _subjects,
        'PUT /academic/period': (request) => FakeResponse(200, request.data),
      }),
    );
    await _pump(tester, api);

    expect(
      find.text('3 de agosto de 2026 – 28 de noviembre de 2026'),
      findsOneWidget,
    );

    await tester.tap(find.text('Semestre'));
    await pumpFrames(tester);
    await tester.tap(find.text('Guardar'));
    await pumpFrames(tester);

    expect(_writes(api).single.body, {
      'start_date': '2026-08-03',
      'end_date': '2026-11-28',
    });
    expect(find.text('Período académico'), findsNothing);
  });
}
