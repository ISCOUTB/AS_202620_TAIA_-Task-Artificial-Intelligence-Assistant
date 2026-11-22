import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/token_storage.dart';
import 'package:taia/features/auth/auth_service.dart';
import 'package:taia/features/profile/profile_screen.dart';
import 'package:taia/features/profile/statistics_service.dart';

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
      'GET /academic/statistics': (_) => FakeResponse(200, {
        'period': 'month',
        'start': '2026-11-01',
        'end': '2026-11-30',
        'by_status': {'pending': 2, 'completed': 3, 'overdue': 0},
        'completed_by_week': [
          for (var i = 0; i < 8; i++)
            {'week_start': '2026-10-0${i + 1}', 'completed': i},
        ],
        'on_time': {'completed': 3, 'on_time': 3, 'percentage': 100.0},
        'pending_by_subject': [],
        'upcoming': [],
      }),
    }),
  );
  await tester.pumpWidget(
    MaterialApp(
      home: ProfileScreen(
        service: AuthService(dio: api.dio(), tokens: TokenStorage()),
        statisticsService: StatisticsService(api.dio()),
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

  testWidgets('RF-PRF-01 · las gráficas se ven al entrar al perfil', (
    tester,
  ) async {
    await _pump(tester, telegramLinked: false);

    expect(find.text('TU PROGRESO'), findsOneWidget);
    expect(find.text('Estadísticas'), findsNothing);
  });

  testWidgets(
    'RF-USR-11 · la cuenta, Telegram y la sesión están en Configuración',
    (tester) async {
      await _pump(tester, telegramLinked: false);

      expect(find.text('Configuración'), findsOneWidget);
      expect(find.text('Cerrar sesión'), findsNothing);
      expect(find.text('Editar perfil'), findsNothing);
      expect(find.text('Telegram'), findsNothing);
    },
  );
}
