import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/academic/subjects_screen.dart';
import 'package:taia/features/tasks/subjects_service.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

Map<String, dynamic> subjectJson({
  String id = 's1',
  String name = 'Física',
  String? teacher = 'Ana Gómez',
  bool archived = false,
  int pending = 2,
  List<Map<String, dynamic>> aliases = const [],
}) => {
  'id': id,
  'name': name,
  'teacher': teacher,
  'archived': archived,
  'archived_at': archived ? '2026-10-01T15:00:00Z' : null,
  'aliases': aliases,
  'pending_tasks': pending,
  'created_at': '2026-09-01T15:00:00Z',
};

FakeResponse _detail(RequestOptions _) => FakeResponse(200, subjectJson());

Future<void> _pump(WidgetTester tester, FakeApi api) async {
  useTallScreen(tester);
  await tester.pumpWidget(
    MaterialApp(home: SubjectsScreen(service: SubjectsService(api.dio()))),
  );
  await pumpFrames(tester);
}

/// Abre el detalle de la primera asignatura.
Future<void> _openFirst(WidgetTester tester) async {
  await tester.tap(find.text('Física').first);
  await pumpFrames(tester);
}

List<RecordedRequest> _writes(FakeApi api) =>
    api.requests.where((r) => r.method != 'GET').toList();

void main() {
  testWidgets(
    'RF-ASG-02 · lista las activas y, a pedido, también las archivadas',
    (tester) async {
      final api = FakeApi(
        routes({
          'GET /academic/subjects': (request) => FakeResponse(200, [
            subjectJson(),
            if (request.queryParameters['include_archived'] == true)
              subjectJson(
                id: 's2',
                name: 'Química',
                teacher: null,
                archived: true,
                pending: 0,
              ),
          ]),
        }),
      );
      await _pump(tester, api);

      expect(api.requests.single.query, isEmpty);
      expect(find.text('Ana Gómez · 2 pendientes'), findsOneWidget);
      expect(find.text('Química'), findsNothing);

      await tester.tap(find.text('Con archivadas'));
      await pumpFrames(tester);

      expect(api.requests.last.query, {'include_archived': true});
      expect(find.text('0 pendientes · Archivada'), findsOneWidget);
    },
  );

  testWidgets('RF-ASG-02 · el detalle muestra las tareas pendientes', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'GET /academic/subjects': (_) => FakeResponse(200, [subjectJson()]),
        'GET /academic/subjects/s1': (_) =>
            FakeResponse(200, subjectJson(pending: 3)),
      }),
    );
    await _pump(tester, api);
    await _openFirst(tester);

    expect(api.requests.last.path, '/academic/subjects/s1');
    expect(find.text('Tiene 3 tareas pendientes.'), findsOneWidget);
  });

  testWidgets('RF-ASG-01 · crea una asignatura y muestra el 409', (
    tester,
  ) async {
    var status = 409;
    final api = FakeApi(
      routes({
        'GET /academic/subjects': (_) => FakeResponse(200, [subjectJson()]),
        'POST /academic/subjects': (_) => status == 409
            ? const FakeResponse(409, {
                'detail': 'Ya existe una asignatura con ese nombre.',
              })
            : FakeResponse(201, subjectJson(id: 's3', name: 'Cálculo')),
      }),
    );
    await _pump(tester, api);

    await tester.tap(find.text('Nueva asignatura'));
    await pumpFrames(tester);
    await tester.enterText(find.byType(TextFormField).first, 'física');
    await tester.tap(find.text('Crear materia'));
    await pumpFrames(tester);

    expect(
      find.text('Ya existe una asignatura con ese nombre.'),
      findsOneWidget,
    );

    status = 201;
    await tester.enterText(find.byType(TextFormField).first, 'Cálculo');
    await tester.tap(find.text('Crear materia'));
    await pumpFrames(tester);

    expect(_writes(api).last.body, {'name': 'Cálculo'});
    expect(find.text('Crear materia'), findsNothing);
    // Al cerrar el diálogo se vuelve a pedir la lista.
    expect(api.requests.last.method, 'GET');
  });

  testWidgets('RF-ASG-03 · edita el nombre y borra el docente', (tester) async {
    final api = FakeApi(
      routes({
        'GET /academic/subjects': (_) => FakeResponse(200, [subjectJson()]),
        'GET /academic/subjects/s1': _detail,
        'PATCH /academic/subjects/s1': (_) =>
            FakeResponse(200, subjectJson(name: 'Física II', teacher: null)),
      }),
    );
    await _pump(tester, api);
    await _openFirst(tester);

    await tester.enterText(
      find.widgetWithText(TextFormField, 'Física'),
      'Física II',
    );
    await tester.enterText(find.widgetWithText(TextFormField, 'Ana Gómez'), '');
    await tester.tap(find.text('Guardar cambios'));
    await pumpFrames(tester);

    final patch = _writes(api).single;
    expect(patch.path, '/academic/subjects/s1');
    expect(patch.body, {'name': 'Física II', 'teacher': ''});
    expect(find.text('Guardar cambios'), findsNothing);
  });

  testWidgets('RF-ASG-04 · eliminar pide confirmación y muestra el 409 con las '
      'actividades', (tester) async {
    final api = FakeApi(
      routes({
        'GET /academic/subjects': (_) => FakeResponse(200, [subjectJson()]),
        'GET /academic/subjects/s1': _detail,
        'DELETE /academic/subjects/s1': (_) => const FakeResponse(409, {
          'detail':
              'La asignatura tiene 4 actividad(es) asociada(s); archívala '
              'en lugar de eliminarla.',
        }),
      }),
    );
    await _pump(tester, api);
    await _openFirst(tester);

    await tester.tap(find.text('Eliminar asignatura'));
    await pumpFrames(tester);
    await tester.tap(find.text('Cancelar'));
    await pumpFrames(tester);
    expect(_writes(api), isEmpty);

    await tester.tap(find.text('Eliminar asignatura'));
    await pumpFrames(tester);
    await tester.tap(find.text('Eliminar'));
    await pumpFrames(tester);

    expect(_writes(api).single.method, 'DELETE');
    expect(find.textContaining('tiene 4 actividad(es)'), findsOneWidget);
  });

  testWidgets('RF-ASG-04 · eliminar una asignatura sin actividades', (
    tester,
  ) async {
    var deleted = false;
    final api = FakeApi(
      routes({
        'GET /academic/subjects': (_) =>
            FakeResponse(200, [if (!deleted) subjectJson()]),
        'GET /academic/subjects/s1': _detail,
        'DELETE /academic/subjects/s1': (_) {
          deleted = true;
          return const FakeResponse(204);
        },
      }),
    );
    await _pump(tester, api);
    await _openFirst(tester);

    await tester.tap(find.text('Eliminar asignatura'));
    await pumpFrames(tester);
    await tester.tap(find.text('Eliminar'));
    await pumpFrames(tester);

    expect(find.text('Eliminar asignatura'), findsNothing);
    expect(
      find.text('Todavía no tienes asignaturas. Crea la primera.'),
      findsOneWidget,
    );
  });

  testWidgets('RF-ASG-05 · archiva y muestra el 409 al desarchivar', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'GET /academic/subjects': (_) => FakeResponse(200, [subjectJson()]),
        'GET /academic/subjects/s1': _detail,
        'POST /academic/subjects/s1/archive': (_) =>
            FakeResponse(200, subjectJson(archived: true)),
        'POST /academic/subjects/s1/unarchive': (_) => const FakeResponse(409, {
          'detail': 'El horario de la asignatura choca con el actual.',
        }),
      }),
    );
    await _pump(tester, api);
    await _openFirst(tester);

    await tester.tap(find.text('Archivar asignatura'));
    await pumpFrames(tester);

    expect(_writes(api).single.path, '/academic/subjects/s1/archive');
    expect(find.text('ASIGNATURA ARCHIVADA'), findsOneWidget);

    await tester.tap(find.text('Desarchivar asignatura'));
    await pumpFrames(tester);

    expect(_writes(api).last.path, '/academic/subjects/s1/unarchive');
    expect(
      find.text('El horario de la asignatura choca con el actual.'),
      findsOneWidget,
    );
  });

  testWidgets('RF-ASG-09 · agrega y quita alias', (tester) async {
    final withAlias = subjectJson(
      aliases: [
        {'id': 'a1', 'alias': 'FM'},
      ],
    );
    final api = FakeApi(
      routes({
        'GET /academic/subjects': (_) => FakeResponse(200, [subjectJson()]),
        'GET /academic/subjects/s1': _detail,
        'POST /academic/subjects/s1/aliases': (_) =>
            FakeResponse(201, withAlias),
        'DELETE /academic/subjects/s1/aliases/a1': _detail,
      }),
    );
    await _pump(tester, api);
    await _openFirst(tester);

    await tester.enterText(find.widgetWithText(TextField, 'Nuevo alias'), 'FM');
    await tester.tap(find.byTooltip('Agregar alias'));
    await pumpFrames(tester);

    expect(_writes(api).single.body, {'alias': 'FM'});
    expect(find.widgetWithText(InputChip, 'FM'), findsOneWidget);

    await tester.tap(find.byTooltip('Quitar alias'));
    await pumpFrames(tester);

    expect(_writes(api).last.method, 'DELETE');
    expect(find.widgetWithText(InputChip, 'FM'), findsNothing);
  });
}
