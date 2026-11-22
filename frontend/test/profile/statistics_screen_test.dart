import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/bogota_time.dart';
import 'package:taia/features/profile/statistics_screen.dart';
import 'package:taia/features/profile/statistics_service.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

Map<String, dynamic> _stats({bool empty = false}) => {
  'period': 'month',
  'start': '2026-10-01',
  'end': '2026-10-31',
  'by_status': empty
      ? {'pending': 0, 'completed': 0, 'overdue': 0}
      : {'pending': 3, 'completed': 5, 'overdue': 1},
  'completed_by_week': [
    for (var i = 0; i < 8; i++)
      {
        'week_start': '2026-08-${(10 + 7 * i).clamp(10, 28)}',
        'completed': empty ? 0 : i,
      },
  ],
  'on_time': empty
      ? {'completed': 0, 'on_time': 0, 'percentage': null}
      : {'completed': 5, 'on_time': 4, 'percentage': 80.0},
  'pending_by_subject': empty
      ? []
      : [
          {'subject_id': 's1', 'subject_name': 'Física', 'pending': 3},
          {'subject_id': 's2', 'subject_name': 'Cálculo', 'pending': 1},
        ],
  'upcoming': empty ? [] : [taskJson(title: 'Informe de física')],
};

Future<FakeApi> _pump(
  WidgetTester tester,
  FakeResponse Function(String period) respond,
) async {
  useTallScreen(tester);
  final api = FakeApi(
    routes({
      'GET /academic/statistics': (r) =>
          respond(r.queryParameters['period'] as String),
    }),
  );
  await tester.pumpWidget(
    MaterialApp(home: StatisticsScreen(service: StatisticsService(api.dio()))),
  );
  await pumpFrames(tester);
  return api;
}

void main() {
  setUp(() => clock = () => DateTime.utc(2026, 10, 5, 15));
  tearDown(() => clock = DateTime.now);

  testWidgets('RF-PRF-01 · los cinco gráficos con su pregunta', (tester) async {
    final api = await _pump(tester, (_) => FakeResponse(200, _stats()));

    expect(api.requests.single.query, {'period': 'month'});
    expect(find.text('¿Cómo voy?'), findsOneWidget);
    expect(find.text('¿Estoy siendo constante?'), findsOneWidget);
    expect(find.text('¿Entrego antes de la fecha límite?'), findsOneWidget);
    expect(find.text('¿Qué materia me está cargando más?'), findsOneWidget);
    expect(find.text('¿Qué viene ahora?'), findsOneWidget);
    expect(find.text('80,0 %'), findsOneWidget);
    expect(find.text('4 de 5 completadas a tiempo'), findsOneWidget);
    expect(find.text('Informe de física'), findsOneWidget);
  });

  testWidgets('RF-PRF-01 · cada gráfico tiene su estado vacío', (tester) async {
    await _pump(tester, (_) => FakeResponse(200, _stats(empty: true)));

    expect(
      find.text('No tienes actividades que venzan este mes.'),
      findsOneWidget,
    );
    expect(
      find.text('Aún no has completado tareas en las últimas 8 semanas.'),
      findsOneWidget,
    );
    expect(find.text('Aún no has completado tareas este mes.'), findsOneWidget);
    expect(
      find.text('No tienes pendientes que venzan este mes.'),
      findsOneWidget,
    );
    expect(find.text('Nada vence en los próximos 7 días.'), findsOneWidget);
  });

  testWidgets(
    'RF-PRF-01 · el período se elige y sin período académico se avisa',
    (tester) async {
      final api = await _pump(
        tester,
        (period) => period == 'academic_period'
            ? const FakeResponse(404, {
                'detail':
                    'Define tu período académico para ver estas estadísticas.',
              })
            : FakeResponse(200, _stats()),
      );

      await tester.tap(find.text('Semana'));
      await pumpFrames(tester);
      await tester.tap(find.text('Período'));
      await pumpFrames(tester);

      expect(
        [for (final r in api.requests) r.query['period']],
        ['month', 'week', 'academic_period'],
      );
      expect(
        find.text('Define tu período académico para ver estas estadísticas.'),
        findsOneWidget,
      );
    },
  );
}
