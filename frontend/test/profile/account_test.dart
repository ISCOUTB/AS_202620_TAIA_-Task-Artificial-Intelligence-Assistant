import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/auth/auth_service.dart';
import 'package:taia/features/profile/profile_screen.dart';
import 'package:taia/features/profile/profile_service.dart';
import 'package:taia/welcome/welcome_screen.dart';

import '../auth/auth_service_test.dart' show MemoryTokens;
import '../support/fake_api.dart';
import '../support/test_app.dart';

Map<String, dynamic> _user({
  String name = 'Valeria Ríos',
  String email = 'valeria@example.com',
  bool telegramLinked = false,
}) => {
  'id': 'u1',
  'full_name': name,
  'email': email,
  'telegram_linked': telegramLinked,
  'created_at': '2026-09-01T15:00:00Z',
  'consent_policy_version': '2026-11-v1',
};

Future<FakeApi> _pump(
  WidgetTester tester, {
  bool telegramLinked = false,
  Map<String, FakeResponse Function(dynamic)> extra = const {},
}) async {
  useTallScreen(tester);
  final api = FakeApi(
    routes({
      'GET /users/me': (_) =>
          FakeResponse(200, _user(telegramLinked: telegramLinked)),
      'GET /notifications/unread-count': (_) =>
          const FakeResponse(200, {'unread_count': 0}),
      'POST /users/logout': (_) => const FakeResponse(204),
      ...extra,
    }),
  );
  final dio = api.dio();
  await tester.pumpWidget(
    MaterialApp(
      home: ProfileScreen(
        service: AuthService(
          dio: dio,
          tokens: MemoryTokens(access: 'a'),
        ),
        profileService: ProfileService(dio),
      ),
    ),
  );
  await pumpFrames(tester);
  return api;
}

Finder _dialogField(int index) => find
    .descendant(
      of: find.byType(AlertDialog),
      matching: find.byType(TextFormField),
    )
    .at(index);

List<RecordedRequest> _writes(FakeApi api) => api.requests
    .where((r) => r.method != 'GET' && r.path != '/users/logout')
    .toList();

void main() {
  testWidgets('RF-USR-06 · cambiar el nombre envía solo el nombre', (
    tester,
  ) async {
    final api = await _pump(
      tester,
      extra: {
        'PATCH /users/me': (_) => FakeResponse(200, _user(name: 'Vale Ríos')),
      },
    );

    await tester.tap(find.text('Editar perfil'));
    await pumpFrames(tester);
    await tester.enterText(_dialogField(0), 'Vale Ríos');
    await tester.tap(find.text('Guardar'));
    await pumpFrames(tester);

    expect(_writes(api).single.body, {'full_name': 'Vale Ríos'});
    expect(find.text('Vale Ríos'), findsOneWidget);
  });

  testWidgets('RF-USR-06 · cambiar el correo exige la contraseña actual', (
    tester,
  ) async {
    final api = await _pump(tester);

    await tester.tap(find.text('Editar perfil'));
    await pumpFrames(tester);
    await tester.enterText(_dialogField(1), 'nueva@example.com');
    await tester.tap(find.text('Guardar'));
    await pumpFrames(tester);

    expect(
      find.text('Para cambiar el correo, ingresa tu contraseña actual.'),
      findsOneWidget,
    );
    expect(_writes(api), isEmpty);
  });

  testWidgets('RF-USR-07 · cambiar la contraseña', (tester) async {
    final api = await _pump(
      tester,
      extra: {'PUT /users/me/password': (_) => const FakeResponse(204)},
    );

    await tester.tap(find.text('Cambiar contraseña'));
    await pumpFrames(tester);
    await tester.enterText(_dialogField(0), 'actual-123');
    await tester.enterText(_dialogField(1), 'nueva-12345');
    await tester.enterText(_dialogField(2), 'nueva-12345');
    await tester.tap(find.text('Cambiar'));
    await pumpFrames(tester);

    expect(_writes(api).single.body, {
      'current_password': 'actual-123',
      'new_password': 'nueva-12345',
    });
    expect(find.text('Contraseña actualizada'), findsOneWidget);
  });

  testWidgets('RF-USR-09 · desactivar la cuenta cierra la sesión', (
    tester,
  ) async {
    final api = await _pump(
      tester,
      extra: {'POST /users/me/deactivate': (_) => const FakeResponse(204)},
    );

    await tester.tap(find.text('Desactivar cuenta'));
    await pumpFrames(tester);
    await tester.enterText(_dialogField(0), 'actual-123');
    await tester.tap(find.text('Desactivar'));
    await pumpFrames(tester);

    expect(_writes(api).single.body, {'current_password': 'actual-123'});
    expect(find.byType(WelcomeScreen), findsOneWidget);
  });

  testWidgets('RF-USR-09 · contraseña incorrecta: la cuenta sigue activa', (
    tester,
  ) async {
    await _pump(
      tester,
      extra: {
        'POST /users/me/deactivate': (_) => const FakeResponse(403, {
          'detail': 'La contraseña actual no es correcta.',
        }),
      },
    );

    await tester.tap(find.text('Desactivar cuenta'));
    await pumpFrames(tester);
    await tester.enterText(_dialogField(0), 'otra');
    await tester.tap(find.text('Desactivar'));
    await pumpFrames(tester);

    expect(find.text('La contraseña actual no es correcta.'), findsOneWidget);
    expect(find.byType(WelcomeScreen), findsNothing);
  });

  testWidgets('RF-TEL-03 · desvincular Telegram', (tester) async {
    final api = await _pump(
      tester,
      telegramLinked: true,
      extra: {'DELETE /users/me/telegram': (_) => const FakeResponse(204)},
    );

    await tester.tap(find.text('Telegram'));
    await pumpFrames(tester);
    await tester.tap(find.text('Desvincular'));
    await pumpFrames(tester);

    expect(_writes(api).single.path, '/users/me/telegram');
    expect(find.text('Telegram desvinculado'), findsOneWidget);
  });
}
