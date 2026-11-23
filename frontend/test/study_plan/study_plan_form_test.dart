import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/study_plan/study_plan_form_screen.dart';
import 'package:taia/features/study_plan/study_plan_service.dart';

import '../support/test_app.dart';

/// RNF-14: el formulario del plan va paso a paso, con atajos de un toque.
void main() {
  testWidgets('RF-EST-01 · la franja "Noche" se elige con un toque', (
    tester,
  ) async {
    StudyPlanForm? result;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => TextButton(
            onPressed: () async {
              result = await Navigator.of(context).push<StudyPlanForm>(
                MaterialPageRoute(
                  builder: (_) => const StudyPlanFormScreen(subjects: []),
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

    expect(find.text('1 de 5'), findsOneWidget);
    await tester.tap(find.text('Siguiente'));
    await pumpFrames(tester);
    await tester.tap(find.text('Noche'));
    await pumpFrames(tester);
    expect(find.text('De 06:00 p. m. a 10:00 p. m.'), findsOneWidget);

    for (var i = 0; i < 3; i++) {
      await tester.tap(find.text('Siguiente'));
      await pumpFrames(tester);
    }
    await tester.tap(find.text('Generar plan'));
    await pumpFrames(tester);

    expect(result!.windowStart, const TimeOfDay(hour: 18, minute: 0));
    expect(result!.windowEnd, const TimeOfDay(hour: 22, minute: 0));
  });
}
