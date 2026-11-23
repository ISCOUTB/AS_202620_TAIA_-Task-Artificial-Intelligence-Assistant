import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/study_plan/study_plan_card.dart';
import 'package:taia/features/study_plan/study_plan_service.dart';

/// RNF-14: la tarjeta del plan de estudio en el Inicio y en Tareas.
void main() {
  // Miércoles 7 de octubre de 2026, 10:00 en Colombia.
  final now = DateTime(2026, 10, 7, 10);

  StudySession session(DateTime start, String subject) => StudySession(
    startsAt: start,
    endsAt: start.add(const Duration(hours: 1)),
    title: 'Repasar',
    subjectName: subject,
  );

  StudyPlan plan(String status, List<StudySession> sessions) => StudyPlan(
    id: 'p1',
    status: status,
    form: StudyPlanForm(
      preference: StudyPreference.values.first,
      days: const {},
      windowStart: const TimeOfDay(hour: 6, minute: 0),
      windowEnd: const TimeOfDay(hour: 22, minute: 0),
      sessionMinutes: 60,
      subjectIds: const {},
      busyBlocks: const [],
      preferredTime: StudyTime.values.first,
    ),
    sessions: sessions,
    unscheduled: const [],
  );

  test('sin plan invita a crearlo', () {
    final summary = summarizeStudyPlan(null, now);
    expect(summary.title, 'Arma tu plan de estudio');
    expect(summary.action, 'Crear mi plan');
  });

  test('un plan propuesto invita a revisarlo', () {
    expect(
      summarizeStudyPlan(plan('proposed', []), now).action,
      'Revisar plan',
    );
  });

  test('con sesiones hoy dice qué se estudia y a qué hora', () {
    final summary = summarizeStudyPlan(
      plan('accepted', [
        session(DateTime(2026, 10, 7, 16), 'Cálculo'),
        session(DateTime(2026, 10, 7, 18), 'Física'),
      ]),
      now,
    );
    expect(summary.title, 'Hoy estudias Cálculo');
    expect(summary.detail, '16:00 · Repasar · y 1 sesión más');
  });

  test('sin sesiones hoy dice cuál es la próxima', () {
    final summary = summarizeStudyPlan(
      plan('accepted', [session(DateTime(2026, 10, 9, 15), 'Física')]),
      now,
    );
    expect(summary.title, 'Hoy descansas del plan');
    expect(summary.detail, contains('Física, 9/10 a las 15:00'));
  });
}
