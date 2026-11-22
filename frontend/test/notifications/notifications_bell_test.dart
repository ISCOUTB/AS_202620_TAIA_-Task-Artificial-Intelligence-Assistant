import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/bogota_time.dart';
import 'package:taia/features/notifications/notifications_bell.dart';
import 'package:taia/features/notifications/notifications_service.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

Map<String, dynamic> _notification(
  String id,
  String message, {
  bool read = false,
}) => {
  'id': id,
  'reminder_id': 'r-$id',
  'message': message,
  'created_at': '2026-10-04T23:00:00Z',
  'read_at': read ? '2026-10-05T01:00:00Z' : null,
  'read': read,
};

Future<FakeApi> _pump(WidgetTester tester, {int unread = 2}) async {
  final api = FakeApi(
    routes({
      'GET /notifications/unread-count': (_) =>
          FakeResponse(200, {'unread_count': unread}),
      'GET /notifications': (_) => FakeResponse(200, {
        'items': [
          _notification('n1', 'Recuerda: Informe de física'),
          _notification('n2', 'Repasar capítulo 3'),
          _notification('n3', 'Parcial de cálculo', read: true),
        ],
        'total': 3,
        'limit': 50,
        'offset': 0,
      }),
      'PATCH /notifications/n1/read': (_) =>
          FakeResponse(200, _notification('n1', 'x', read: true)),
      'PATCH /notifications/read-all': (_) => const FakeResponse(204),
    }),
  );
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: NotificationsBell(service: NotificationsService(api.dio())),
      ),
    ),
  );
  await pumpFrames(tester);
  return api;
}

void main() {
  setUp(() => clock = () => DateTime.utc(2026, 10, 5, 15));
  tearDown(() => clock = DateTime.now);

  testWidgets('RF-NOT-03 · la campana muestra cuántas no se han leído', (
    tester,
  ) async {
    await _pump(tester, unread: 12);

    expect(find.text('9+'), findsOneWidget);
  });

  testWidgets(
    'RF-NOT-03 · la bandeja lista las notificaciones y marca una leída',
    (tester) async {
      useTallScreen(tester);
      final api = await _pump(tester);

      await tester.tap(find.byTooltip('Notificaciones'));
      await pumpFrames(tester);

      expect(find.text('Recuerda: Informe de física'), findsOneWidget);
      expect(find.text('Parcial de cálculo'), findsOneWidget);

      await tester.tap(find.text('Recuerda: Informe de física'));
      await pumpFrames(tester);

      expect(
        api.requests.where((r) => r.method == 'PATCH').single.path,
        '/notifications/n1/read',
      );
    },
  );

  testWidgets('RF-NOT-03 · marcar todas como leídas', (tester) async {
    useTallScreen(tester);
    final api = await _pump(tester);

    await tester.tap(find.byTooltip('Notificaciones'));
    await pumpFrames(tester);
    await tester.tap(find.text('Marcar todas como leídas'));
    await pumpFrames(tester);

    expect(
      api.requests.where((r) => r.method == 'PATCH').single.path,
      '/notifications/read-all',
    );
    expect(find.text('Marcar todas como leídas'), findsNothing);
  });

  testWidgets(
    'RF-NOT-03 · sin contador disponible, la campana no muestra número',
    (tester) async {
      final api = FakeApi((_) => const FakeResponse(500));
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: NotificationsBell(service: NotificationsService(api.dio())),
          ),
        ),
      );
      await pumpFrames(tester);

      expect(find.byTooltip('Notificaciones'), findsOneWidget);
      expect(find.text('0'), findsNothing);
    },
  );
}
