import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/calendar/calendar_logic.dart';
import 'package:taia/features/calendar/calendar_service.dart';
import 'package:taia/features/calendar/widgets/week_timeline.dart';
import 'package:taia/features/tasks/task.dart';

import '../support/fake_api.dart';

/// RF-TAR-11: la vista de semana de la Agenda junta horario y actividades.
void main() {
  // Lunes 5 de octubre de 2026. La tarea vence el viernes 9 a las 23:59 (Colombia).
  final monday = DateTime(2026, 10, 5);
  final friday = DateTime(2026, 10, 9);
  final task = AcademicTask.fromJson(taskJson(title: 'Taller 3'));
  final physics = ClassOccurrence(
    subjectName: 'Física',
    startsAt: DateTime(2026, 10, 9, 8),
    endsAt: DateTime(2026, 10, 9, 10),
    room: 'A-101',
  );

  Future<List<AcademicTask>> pump(
    WidgetTester tester, {
    List<DateTime>? days,
  }) async {
    final tapped = <AcademicTask>[];
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: WeekTimeline(
              days: days ?? weekDays(monday),
              classes: [physics],
              tasks: [task],
              selected: friday,
              today: monday,
              onSelectDay: (_) {},
              onTapTask: tapped.add,
            ),
          ),
        ),
      ),
    );
    return tapped;
  }

  testWidgets('RF-TAR-11 · un día con clase y actividad muestra las dos', (
    tester,
  ) async {
    await pump(tester);

    expect(find.text('Física'), findsOneWidget);
    expect(find.text('Taller 3'), findsOneWidget);
    // Las dos quedan en la columna del viernes.
    final classX = tester.getTopLeft(find.text('Física')).dx;
    final taskX = tester.getTopLeft(find.text('Taller 3')).dx;
    expect((classX - taskX).abs(), lessThan(8));
  });

  testWidgets('RF-TAR-11 · tocar la actividad la abre', (tester) async {
    final tapped = await pump(tester);

    await tester.ensureVisible(find.text('Taller 3'));
    await tester.tap(find.text('Taller 3'));

    expect(tapped.single.title, 'Taller 3');
  });

  testWidgets(
    'RF-TAR-11 · la vista de día muestra el nombre, la hora y el aula a todo el ancho',
    (tester) async {
      await pump(tester, days: [friday]);

      expect(find.text('Física'), findsOneWidget);
      expect(find.textContaining('A-101'), findsOneWidget);
      expect(find.textContaining('Taller 3'), findsOneWidget);
    },
  );

  group('RF-TAR-11 · rango de horas', () {
    test('va de una hora antes de lo primero a una después de lo último', () {
      expect(timelineHours([friday], [physics], const []), (7, 11));
      // La entrega de las 23:59 alarga el día hasta medianoche.
      expect(timelineHours([friday], [physics], [task]), (7, 24));
    });

    test('solo cuenta los días que se muestran', () {
      expect(timelineHours([monday], [physics], [task]), (8, 12));
    });

    test('la semana compacta solo agrega el fin de semana si tiene algo', () {
      final week = weekDays(monday);
      expect(compactWeek(week, const [], const []), week.sublist(0, 5));
      final saturday = ClassOccurrence(
        subjectName: 'Inglés',
        startsAt: DateTime(2026, 10, 10, 9),
        endsAt: DateTime(2026, 10, 10, 11),
      );
      expect(compactWeek(week, [saturday], const []), week.sublist(0, 6));
    });
  });
}
