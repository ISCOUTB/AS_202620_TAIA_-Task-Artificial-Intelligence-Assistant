import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/token_storage.dart';
import 'package:taia/features/auth/auth_service.dart';
import 'package:taia/features/profile/profile_screen.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

Future<void> _pump(WidgetTester tester, {required bool telegramLinked}) async {
  useTallScreen(tester);
  final api = FakeApi(
    routes({
      'GET /users/me': (_) => FakeResponse(200, {
        'id': 'u1',
        'full_name': 'Valeria Ríos',
        'email': 'valeria@example.com',
        'telegram_linked': telegramLinked,
        'created_at': '2026-09-01T15:00:00Z',
        'consent_policy_version': '2026-11-v1',
      }),
    }),
  );
  await tester.pumpWidget(
    MaterialApp(
      home: ProfileScreen(
        service: AuthService(dio: api.dio(), tokens: TokenStorage()),
      ),
    ),
  );
  await pumpFrames(tester);
}

void main() {
  for (final linked in [false, true]) {
    testWidgets(
      'D-10 · el perfil no ofrece recibir los recordatorios por Telegram '
      '(Telegram vinculado: $linked)',
      (tester) async {
        await _pump(tester, telegramLinked: linked);

        expect(find.text('Valeria Ríos'), findsOneWidget);
        expect(find.text('PREFERENCIAS'), findsNothing);
        expect(find.text('Notificaciones'), findsNothing);
        expect(find.textContaining('Por Telegram'), findsNothing);
        expect(find.textContaining('recordatorios'), findsNothing);
      },
    );
  }

  testWidgets(
    'RF-ASG-02 y RF-ASG-07 · el perfil lleva a asignaturas y horario',
    (tester) async {
      await _pump(tester, telegramLinked: false);

      expect(find.text('ACADÉMICO'), findsOneWidget);
      expect(find.text('Asignaturas'), findsOneWidget);
      expect(find.text('Horario'), findsOneWidget);
    },
  );
}
