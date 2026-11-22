import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/token_storage.dart';
import 'package:taia/features/auth/auth_service.dart';
import 'package:taia/features/auth/privacy_policy.dart';
import 'package:taia/features/auth/register_screen.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

Future<FakeApi> _pump(
  WidgetTester tester, {
  required Future<bool> Function(Uri uri) openLink,
}) async {
  useTallScreen(tester);
  final api = FakeApi((_) => const FakeResponse(201));
  await tester.pumpWidget(
    MaterialApp(
      home: RegisterScreen(
        service: AuthService(dio: api.dio(), tokens: TokenStorage()),
        openLink: openLink,
      ),
    ),
  );
  await pumpFrames(tester);
  return api;
}

void main() {
  test('RF-USR-10 · la política enlazada es la de TAIA', () {
    expect(
      privacyPolicyUrl,
      'https://github.com/ISCOUTB/AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant/blob/main/docs/politica_privacidad.md',
    );
  });

  testWidgets(
    'RF-USR-10 · el registro deja leer la política antes de aceptarla',
    (tester) async {
      final opened = <Uri>[];
      await _pump(
        tester,
        openLink: (uri) async {
          opened.add(uri);
          return true;
        },
      );

      await tester.tap(find.text('Leer la política de datos'));
      await pumpFrames(tester);

      expect(opened, [Uri.parse(privacyPolicyUrl)]);
      expect(find.text('No se pudo abrir la política de datos.'), findsNothing);
    },
  );

  testWidgets('RF-USR-10 · avisa si no se pudo abrir la política', (
    tester,
  ) async {
    await _pump(tester, openLink: (_) async => false);

    await tester.tap(find.text('Leer la política de datos'));
    await pumpFrames(tester);

    expect(find.text('No se pudo abrir la política de datos.'), findsOneWidget);
  });

  testWidgets('RF-USR-10 · sin aceptar la política no se envía el registro', (
    tester,
  ) async {
    final api = await _pump(tester, openLink: (_) async => true);

    final fields = find.byType(TextFormField);
    await tester.enterText(fields.at(0), 'Valeria Ríos');
    await tester.enterText(fields.at(1), 'valeria@example.com');
    await tester.enterText(fields.at(2), 'secreta123');
    await tester.enterText(fields.at(3), 'secreta123');
    await tester.tap(find.text('Crear cuenta').last);
    await pumpFrames(tester);

    expect(
      find.text('Debes aceptar la política para crear tu cuenta.'),
      findsOneWidget,
    );
    expect(api.requests, isEmpty);
  });
}
