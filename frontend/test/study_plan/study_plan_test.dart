import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/academic/schedule_block.dart';
import 'package:taia/features/calendar/calendar_service.dart';
import 'package:taia/features/study_plan/study_plan_form_screen.dart';
import 'package:taia/features/study_plan/study_plan_screen.dart';
import 'package:taia/features/study_plan/study_plan_service.dart';
import 'package:taia/features/tasks/subjects_service.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

Map<String, dynamic> _plan({String status = 'proposed'}) => {
  'id': 'p1',
  'status': status,
  'start_date': '2027-03-01',
  'preference': 'both',
  'days': ['monday', 'tuesday'],
  'window_start': '06:00:00',
  'window_end': '22:00:00',
  'session_minutes': 60,
  'subject_ids': ['s1'],
  'busy_blocks': [
    {
      'kind': 'work',
      'weekday': 'saturday',
      'start_time': '08:00:00',
      'end_time': '14:00:00',
    },
  ],
  'max_daily_minutes': 120,
  'preferred_time': 'evening',
  'sessions': [
    {
      'id': 'x1',
      'starts_at': '2027-03-01T18:00:00-05:00',
      'ends_at': '2027-03-01T19:00:00-05:00',
      'task_id': 't1',
      'subject_id': null,
      'title': 'Parcial de cálculo',
      'subject_name': 'Cálculo',
    },
  ],
  'unscheduled': [
    {'task_id': 't2', 'title': 'Ensayo'},
  ],
};

void main() {
  testWidgets('RF-EST-03 · sin plan ofrece crearlo desde un botón', (
    tester,
  ) async {
    useTallScreen(tester);
    final api = FakeApi(
      routes({
        'GET /academic/study-plans/current': (_) =>
            const FakeResponse(404, {'detail': 'Aún no tienes un plan.'}),
      }),
    );
    await tester.pumpWidget(
      MaterialApp(home: StudyPlanScreen(service: StudyPlanService(api.dio()))),
    );
    await pumpFrames(tester);

    expect(find.text('Crear mi plan'), findsOneWidget);
  });

  testWidgets('RF-EST-03 · muestra la propuesta, lo que no cupo y la acepta', (
    tester,
  ) async {
    useTallScreen(tester);
    final api = FakeApi(
      routes({
        'GET /academic/study-plans/current': (_) => FakeResponse(200, _plan()),
        'POST /academic/study-plans/p1/accept': (_) =>
            FakeResponse(200, _plan(status: 'accepted')),
      }),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: StudyPlanScreen(
          service: StudyPlanService(api.dio()),
          subjects: SubjectsService(api.dio()),
        ),
      ),
    );
    await pumpFrames(tester);

    expect(find.text('Parcial de cálculo'), findsOneWidget);
    expect(find.textContaining('No cupieron: Ensayo'), findsOneWidget);

    await tester.tap(find.text('Aceptar plan'));
    await pumpFrames(tester);

    expect(api.requests.last.path, '/academic/study-plans/p1/accept');
    expect(find.text('Aceptar plan'), findsNothing);
    expect(find.text('Plan aceptado: está en tu calendario.'), findsOneWidget);
  });

  test(
    'RF-EST-01 · el formulario se envía con los nombres del diccionario',
    () {
      final form = StudyPlan.fromJson(_plan()).form;

      expect(form.toJson(), {
        'preference': 'both',
        'days': ['monday', 'tuesday'],
        'window_start': '06:00:00',
        'window_end': '22:00:00',
        'session_minutes': 60,
        'subject_ids': ['s1'],
        'busy_blocks': [
          {
            'kind': 'work',
            'weekday': 'saturday',
            'start_time': '08:00:00',
            'end_time': '14:00:00',
          },
        ],
        'max_daily_minutes': 120,
        'preferred_time': 'evening',
      });
    },
  );

  testWidgets(
    'RF-EST-01 · regenerar llena el formulario con el plan anterior',
    (tester) async {
      useTallScreen(tester);
      final initial = StudyPlan.fromJson(_plan()).form;
      StudyPlanForm? result;
      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (context) => TextButton(
              onPressed: () async {
                result = await Navigator.of(context).push<StudyPlanForm>(
                  MaterialPageRoute(
                    builder: (_) => StudyPlanFormScreen(
                      subjects: const [],
                      initial: initial,
                    ),
                  ),
                );
              },
              child: const Text('abrir'),
            ),
          ),
        ),
      );
      await tester.tap(find.text('abrir'));
      await pumpFrames(tester);

      expect(find.text('Sábado · 08:00 a. m. a 02:00 p. m.'), findsOneWidget);
      await tester.tap(find.text('Generar plan'));
      await pumpFrames(tester);

      expect(result!.busyBlocks.single.weekday, Weekday.saturday);
      expect(result!.preferredTime, StudyTime.evening);
      expect(result!.maxDailyMinutes, 120);
    },
  );

  test(
    'RF-EST-03 · el calendario incluye las sesiones del plan aceptado',
    () async {
      final api = FakeApi(
        routes({
          'GET /academic/calendar': (_) => FakeResponse(200, {
            'start': '2027-03-01',
            'end': '2027-03-01',
            'tasks': [],
            'classes': [
              {
                'subject_id': 's1',
                'subject_name': 'Cálculo',
                'starts_at': '2027-03-01T08:00:00-05:00',
                'ends_at': '2027-03-01T10:00:00-05:00',
                'room': null,
              },
            ],
            'study_sessions': [_plan()['sessions'][0]],
          }),
        }),
      );

      final range = await CalendarService(api.dio())
          .range(DateTime(2027, 3, 1), DateTime(2027, 3, 1));

      expect(range.classes.map((c) => c.isStudy), [false, true]);
      expect(range.classes.last.studyTitle, 'Parcial de cálculo');
    },
  );
}
