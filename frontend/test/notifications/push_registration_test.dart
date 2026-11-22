import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/notifications/notifications_service.dart';
import 'package:taia/features/notifications/push_registration.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

void main() {
  test(
    'RF-NOT-01 · registra el token del dispositivo y su renovación',
    () async {
      final api = FakeApi(
        routes({'PUT /users/me/fcm-token': (_) => const FakeResponse(204)}),
      );
      final refresh = StreamController<String>();
      var asked = false;
      final push = PushRegistration(
        api.dio(),
        getToken: () async => 'token-1',
        onTokenRefresh: refresh.stream,
        requestPermission: () async => asked = true,
      );

      await push.start();
      refresh.add('token-2');
      await Future<void>.delayed(const Duration(milliseconds: 50));

      expect(asked, isTrue);
      expect(
        [for (final r in api.requests) r.body],
        [
          {'fcm_token': 'token-1'},
          {'fcm_token': 'token-2'},
        ],
      );
      await push.stop();
      await refresh.close();
    },
  );

  test('RF-NOT-04 · sin token ni servidor, la app sigue sin push', () async {
    final api = FakeApi((_) => const FakeResponse(500));
    final push = PushRegistration(
      api.dio(),
      getToken: () async => null,
      onTokenRefresh: const Stream.empty(),
    );

    await push.start();
    await push.stop();

    expect(api.requests, isEmpty);
  });

  test('RF-NOT-02 · una notificación con la app abierta se avisa y actualiza la campana', () async {
    final api = FakeApi((_) => const FakeResponse(204));
    final messages = StreamController<String>();
    final shown = <String>[];
    final before = inboxChanges.value;
    final push = PushRegistration(
      api.dio(),
      getToken: () async => null,
      onTokenRefresh: const Stream.empty(),
      foregroundMessages: messages.stream,
    )..onForegroundMessage = shown.add;

    await push.start();
    messages.add('Recuerda: Informe (Cálculo) vence el 23/11/2026 08:00');
    await Future<void>.delayed(const Duration(milliseconds: 20));

    expect(shown, ['Recuerda: Informe (Cálculo) vence el 23/11/2026 08:00']);
    expect(inboxChanges.value, before + 1);
    await push.stop();
    await messages.close();
  });
}
