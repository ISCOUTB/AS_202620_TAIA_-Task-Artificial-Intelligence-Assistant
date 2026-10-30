import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/mascot/taia_mascot.dart';
import 'package:taia/splash/splash_screen.dart';
import 'package:taia/splash/taia_wordmark.dart';
import 'package:taia/welcome/welcome_screen.dart';

void main() {
  testWidgets('el splash muestra la mascota y el logotipo', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: SplashScreen()));
    await tester.pump(const Duration(milliseconds: 1800));

    expect(find.byType(TaiaMascot), findsOneWidget);
    expect(find.byType(TaiaWordmark), findsOneWidget);
    expect(find.byType(WelcomeScreen), findsNothing);

    // Deja correr el tiempo mínimo para que no quede un temporizador pendiente.
    await tester.pump(const Duration(seconds: 3));
  });

  testWidgets('el splash pasa a la bienvenida al terminar la carga', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: SplashScreen(minDisplay: Duration(milliseconds: 500)),
      ),
    );
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pump(const Duration(milliseconds: 1000));

    expect(find.byType(WelcomeScreen), findsOneWidget);
    expect(find.text('Te damos la bienvenida a TAIA'), findsOneWidget);
  });

  testWidgets('el splash espera a que termine la carga', (tester) async {
    final loading = Future<void>.delayed(const Duration(seconds: 5));
    await tester.pumpWidget(
      MaterialApp(
        home: SplashScreen(
          minDisplay: const Duration(milliseconds: 500),
          loading: loading,
        ),
      ),
    );
    await tester.pump(const Duration(seconds: 2));
    expect(find.byType(WelcomeScreen), findsNothing);

    await tester.pump(const Duration(seconds: 4));
    await tester.pump(const Duration(milliseconds: 1000));
    expect(find.byType(WelcomeScreen), findsOneWidget);
  });
}
