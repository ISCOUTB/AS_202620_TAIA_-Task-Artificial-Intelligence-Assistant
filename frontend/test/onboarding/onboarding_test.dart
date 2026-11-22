import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/bogota_time.dart';
import 'package:taia/features/academic/schedule_service.dart';
import 'package:taia/features/onboarding/onboarding_logic.dart';
import 'package:taia/features/onboarding/onboarding_screen.dart';
import 'package:taia/features/onboarding/onboarding_service.dart';
import 'package:taia/features/shell/app_entry.dart';
import 'package:taia/features/tasks/subjects_service.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

OnboardingService _service(FakeApi api) => OnboardingService(
  schedule: ScheduleService(api.dio()),
  subjects: SubjectsService(api.dio()),
);

Map<String, dynamic> _subject(String id, String name) => {
  'id': id,
  'name': name,
  'teacher': null,
  'archived': false,
  'aliases': [],
  'pending_tasks': 0,
};

void main() {
  group('RF-ASG-08 · fechas sugeridas según el tipo de estudiante', () {
    test('colegio: de febrero a noviembre', () {
      final period = suggestedPeriod(StudentType.school, DateTime(2026, 5, 10));
      expect(period.start, DateTime(2026, 2, 1));
      expect(period.end, DateTime(2026, 11, 30));
    });

    test('universidad en el segundo semestre: de agosto a noviembre', () {
      final period = suggestedPeriod(
        StudentType.university,
        DateTime(2026, 9, 1),
      );
      expect(period.start, DateTime(2026, 8, 1));
      expect(period.end, DateTime(2026, 11, 30));
    });

    test('universidad en el primer semestre: de febrero a junio', () {
      final period = suggestedPeriod(
        StudentType.university,
        DateTime(2027, 3, 1),
      );
      expect(period.start, DateTime(2027, 2, 1));
      expect(period.end, DateTime(2027, 6, 30));
    });

    test('pasado noviembre se sugiere el ciclo siguiente', () {
      final today = DateTime(2026, 12, 10);
      expect(
        suggestedPeriod(StudentType.school, today).start,
        DateTime(2027, 2, 1),
      );
      expect(
        suggestedPeriod(StudentType.university, today).start,
        DateTime(2027, 2, 1),
      );
    });

    test('curso: desde hoy y tres meses después, para ajustar', () {
      final period = suggestedPeriod(
        StudentType.course,
        DateTime(2026, 11, 22),
      );
      expect(period.start, DateTime(2026, 11, 22));
      expect(period.end, DateTime(2027, 2, 22));
    });
  });

  testWidgets(
    'RF-ASG-10 · una cuenta sin período entra a la configuración inicial',
    (tester) async {
      useTallScreen(tester);
      final api = FakeApi(
        routes({
          'GET /academic/period': (_) =>
              const FakeResponse(404, {'detail': 'Sin período'}),
          'GET /academic/subjects': (_) => const FakeResponse(200, []),
          'GET /academic/schedule-blocks': (_) => const FakeResponse(200, []),
        }),
      );
      await tester.pumpWidget(
        MaterialApp(
          home: AppEntry(
            onboarding: _service(api),
            home: (_) => const Text('principal'),
          ),
        ),
      );
      await pumpFrames(tester);

      expect(find.byType(OnboardingScreen), findsOneWidget);
      expect(find.text('principal'), findsNothing);
    },
  );

  testWidgets('RF-ASG-10 · con período y asignaturas entra directo a la app', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'GET /academic/period': (_) => const FakeResponse(200, {
          'start_date': '2026-08-01',
          'end_date': '2026-11-30',
        }),
        'GET /academic/subjects': (_) =>
            FakeResponse(200, [_subject('s1', 'Cálculo')]),
      }),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: AppEntry(
          onboarding: _service(api),
          home: (_) => const Text('principal'),
        ),
      ),
    );
    await pumpFrames(tester);

    expect(find.text('principal'), findsOneWidget);
  });

  testWidgets(
    'RF-ASG-10 · tipo, período sugerido, asignatura obligatoria y horario opcional',
    (tester) async {
      useTallScreen(tester);
      clock = () => DateTime.utc(2026, 9, 1, 15);
      addTearDown(() => clock = DateTime.now);
      var done = false;
      final api = FakeApi(
        routes({
          'GET /academic/subjects': (_) => const FakeResponse(200, []),
          'GET /academic/schedule-blocks': (_) => const FakeResponse(200, []),
          'PUT /academic/period': (r) => FakeResponse(200, r.data as Map),
          'POST /academic/subjects': (_) =>
              FakeResponse(201, _subject('s1', 'Cálculo')),
        }),
      );
      await tester.pumpWidget(
        MaterialApp(
          home: OnboardingScreen(
            service: _service(api),
            onDone: () => done = true,
          ),
        ),
      );
      await pumpFrames(tester);

      await tester.tap(find.text('Universidad'));
      await tester.tap(find.text('Continuar'));
      await pumpFrames(tester);
      expect(find.textContaining('1 de agosto de 2026'), findsOneWidget);

      await tester.tap(find.text('Usar estas fechas'));
      await pumpFrames(tester);
      final put = api.requests.singleWhere((r) => r.method == 'PUT');
      expect(put.body, {'start_date': '2026-08-01', 'end_date': '2026-11-30'});

      // Sin asignaturas no se puede seguir.
      await tester.tap(find.text('Continuar'));
      await pumpFrames(tester);
      expect(find.text('Agrega al menos una asignatura.'), findsOneWidget);

      await tester.enterText(find.byType(TextField), 'Cálculo');
      await tester.tap(find.byTooltip('Agregar asignatura'));
      await pumpFrames(tester);
      await tester.tap(find.text('Continuar'));
      await pumpFrames(tester);

      expect(find.text('Tu horario de clases'), findsOneWidget);
      await tester.tap(find.text('Terminar'));
      expect(done, isTrue);
    },
  );
}
