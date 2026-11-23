import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/shell/create_sheet.dart';

/// RNF-14: el "+" central abre una hoja con lo que se puede crear.
void main() {
  Future<CreateOption?> openAndPick(WidgetTester tester, String? label) async {
    CreateOption? picked;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () async => picked = await showCreateSheet(context),
              child: const Text('abrir'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('abrir'));
    await tester.pumpAndSettle();
    if (label != null) {
      await tester.tap(find.text(label));
      await tester.pumpAndSettle();
    }
    return picked;
  }

  testWidgets('RNF-14 · la hoja ofrece actividad, clase y asignatura', (
    tester,
  ) async {
    await openAndPick(tester, null);

    expect(find.text('¿Qué quieres crear?'), findsOneWidget);
    expect(find.text('Nueva actividad'), findsOneWidget);
    expect(find.text('Nueva clase'), findsOneWidget);
    expect(find.text('Nueva asignatura'), findsOneWidget);
  });

  testWidgets('RNF-14 · elegir una opción la devuelve y cierra la hoja', (
    tester,
  ) async {
    final picked = await openAndPick(tester, 'Nueva clase');

    expect(picked, CreateOption.classBlock);
    expect(find.text('¿Qué quieres crear?'), findsNothing);
  });
}
