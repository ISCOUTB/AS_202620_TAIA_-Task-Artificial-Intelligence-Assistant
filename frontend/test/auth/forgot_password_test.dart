import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/auth/forgot_password_screen.dart';
import 'package:taia/features/auth/password_reset_service.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

Future<List<bool?>> _open(WidgetTester tester, FakeApi api) async {
  useTallScreen(tester);
  final result = <bool?>[];
  await tester.pumpWidget(
    Launcher<bool>(
      result: result,
      open: (context) => Navigator.of(context).push<bool>(
        MaterialPageRoute<bool>(
          builder: (_) => ForgotPasswordScreen(
            service: PasswordResetService(api.dio()),
            initialEmail: 'valeria@example.com',
          ),
        ),
      ),
    ),
  );
  await tester.tap(find.text('abrir'));
  await pumpFrames(tester);
  return result;
}

Finder _field(int index) => find.byType(TextFormField).at(index);

void main() {
  testWidgets('RF-USR-08 · pedir el código y restablecer la contraseña', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'POST /users/password-reset': (_) => const FakeResponse(202),
        'POST /users/password-reset/confirm': (_) => const FakeResponse(200),
      }),
    );
    final result = await _open(tester, api);

    await tester.tap(find.text('Enviar código'));
    await pumpFrames(tester);
    expect(api.requests.single.body, {'email': 'valeria@example.com'});

    await tester.enterText(_field(1), '123456');
    await tester.enterText(_field(2), 'nueva-12345');
    await tester.enterText(_field(3), 'nueva-12345');
    await tester.tap(find.text('Cambiar contraseña'));
    await pumpFrames(tester);

    expect(api.requests.last.body, {
      'email': 'valeria@example.com',
      'code': '123456',
      'new_password': 'nueva-12345',
    });
    expect(result, [true]);
  });

  testWidgets('RF-USR-08 · un código que no es de 6 dígitos no se envía', (
    tester,
  ) async {
    final api = FakeApi(
      routes({'POST /users/password-reset': (_) => const FakeResponse(202)}),
    );
    await _open(tester, api);

    await tester.tap(find.text('Enviar código'));
    await pumpFrames(tester);
    await tester.enterText(_field(1), '123');
    await tester.enterText(_field(2), 'nueva-12345');
    await tester.enterText(_field(3), 'nueva-12345');
    await tester.tap(find.text('Cambiar contraseña'));
    await pumpFrames(tester);

    expect(find.text('El código tiene 6 dígitos.'), findsOneWidget);
    expect(api.requests, hasLength(1));
  });

  testWidgets('RNF-03 · la cuarta solicitud del día muestra el aviso', (
    tester,
  ) async {
    const message =
        'Agotaste las solicitudes de recuperación de contraseña por hoy. '
        'Intenta de nuevo en 24 horas.';
    final api = FakeApi(
      routes({
        'POST /users/password-reset': (_) =>
            const FakeResponse(429, {'detail': message}),
      }),
    );
    await _open(tester, api);

    await tester.tap(find.text('Enviar código'));
    await pumpFrames(tester);

    expect(find.text(message), findsOneWidget);
    expect(find.text('Cambiar contraseña'), findsNothing);
  });

  testWidgets('RF-USR-08 · un código incorrecto muestra el mismo error', (
    tester,
  ) async {
    final api = FakeApi(
      routes({
        'POST /users/password-reset': (_) => const FakeResponse(202),
        'POST /users/password-reset/confirm': (_) => const FakeResponse(400, {
          'detail': 'El correo o el código no son válidos.',
        }),
      }),
    );
    final result = await _open(tester, api);

    await tester.tap(find.text('Enviar código'));
    await pumpFrames(tester);
    await tester.enterText(_field(1), '000000');
    await tester.enterText(_field(2), 'nueva-12345');
    await tester.enterText(_field(3), 'nueva-12345');
    await tester.tap(find.text('Cambiar contraseña'));
    await pumpFrames(tester);

    expect(find.text('El correo o el código no son válidos.'), findsOneWidget);
    expect(result, isEmpty);
  });
}
