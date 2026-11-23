import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:showcaseview/showcaseview.dart';
import 'package:taia/features/tutorial/tutorial.dart';

/// RF-USR-12: tutorial de la primera vez.
void main() {
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  test('la marca de "ya se vio" empieza vacía y queda guardada', () async {
    final store = TutorialStore();

    expect(await store.seen(), isFalse);
    await store.markSeen();
    expect(await store.seen(), isTrue);
  });

  testWidgets('sin tutorial registrado, el paso muestra solo su contenido', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: TutorialTarget(
          showcaseKey: GlobalKey(),
          title: 'Crear',
          description: 'Desde aquí agregas actividades.',
          child: const Text('+'),
        ),
      ),
    );

    expect(find.text('+'), findsOneWidget);
    expect(find.byType(Showcase), findsNothing);
  });

  testWidgets('el recorrido muestra cada paso y "Saltar" lo termina', (
    tester,
  ) async {
    var finished = 0;
    final first = GlobalKey();
    final second = GlobalKey();
    registerTutorial(onFinish: () => finished++);
    addTearDown(unregisterTutorial);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Column(
            children: [
              TutorialTarget(
                showcaseKey: first,
                title: 'Esta soy yo, TAIA',
                description: 'Tócame cuando quieras.',
                child: const Text('TAIA'),
              ),
              TutorialTarget(
                showcaseKey: second,
                title: 'Tus tareas',
                description: 'Desliza para completar.',
                child: const Text('Tareas'),
              ),
            ],
          ),
        ),
      ),
    );
    ShowcaseView.get().startShowCase([first, second]);
    // El globo flota sin parar: se avanza el tiempo en vez de esperar quietud.
    await tester.pump(const Duration(milliseconds: 600));

    expect(find.text('Esta soy yo, TAIA'), findsOneWidget);
    expect(find.text('Siguiente'), findsOneWidget);

    await tester.tap(find.text('Saltar'));
    await tester.pump(const Duration(milliseconds: 600));

    expect(find.text('Esta soy yo, TAIA'), findsNothing);
    expect(find.text('Tus tareas'), findsNothing);
    expect(finished, greaterThanOrEqualTo(1));
  });
}
