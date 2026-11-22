import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/profile/profile_service.dart';
import 'package:taia/features/profile/widgets/telegram_sheet.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

const _deepLink = 'https://t.me/taia_bot?start=abc123';

Future<List<bool?>> _open(
  WidgetTester tester,
  FakeApi api,
  Future<bool> Function() onCheckLinked, {
  List<Uri>? opened,
}) async {
  useTallScreen(tester);
  final result = <bool?>[];
  await tester.pumpWidget(
    Launcher<bool>(
      result: result,
      open: (context) => showTelegramSheet(
        context,
        service: ProfileService(api.dio()),
        onCheckLinked: onCheckLinked,
        openLink: (uri) async {
          opened?.add(uri);
          return true;
        },
      ),
    ),
  );
  await tester.tap(find.text('abrir'));
  await pumpFrames(tester);
  return result;
}

void main() {
  group('RF-TEL-01 · vincular Telegram', () {
    testWidgets('genera el enlace, lo abre y confirma la vinculación', (
      tester,
    ) async {
      final api = FakeApi(
        routes({
          'POST /users/me/telegram/link': (_) => const FakeResponse(200, {
            'telegram_deep_link': _deepLink,
            'expires_at': '2026-10-05T15:10:00Z',
          }),
        }),
      );
      var linked = false;
      final opened = <Uri>[];
      final result = await _open(
        tester,
        api,
        () async => linked,
        opened: opened,
      );

      await tester.tap(find.text('Generar enlace y abrir Telegram'));
      await pumpFrames(tester);

      expect(api.requests.single.path, '/users/me/telegram/link');
      expect(opened, [Uri.parse(_deepLink)]);

      // Todavía no pulsó «Iniciar» en el bot.
      await tester.tap(find.text('Ya lo vinculé'));
      await pumpFrames(tester);
      expect(find.textContaining('Todavía no veo el vínculo'), findsOneWidget);
      expect(result, isEmpty);

      linked = true;
      await tester.tap(find.text('Ya lo vinculé'));
      await pumpFrames(tester);
      expect(result, [true]);
    });

    testWidgets('muestra el 409 de una cuenta ya vinculada', (tester) async {
      final api = FakeApi(
        routes({
          'POST /users/me/telegram/link': (_) => const FakeResponse(409, {
            'detail': 'La cuenta ya tiene Telegram vinculado.',
          }),
        }),
      );
      await _open(tester, api, () async => false);

      await tester.tap(find.text('Generar enlace y abrir Telegram'));
      await pumpFrames(tester);

      expect(
        find.text('La cuenta ya tiene Telegram vinculado.'),
        findsOneWidget,
      );
      expect(find.text('Ya lo vinculé'), findsNothing);
    });

    testWidgets('no promete recordatorios por Telegram (§8)', (tester) async {
      final api = FakeApi((_) => const FakeResponse(500));
      await _open(tester, api, () async => false);

      expect(find.textContaining('recordatorios'), findsNothing);
    });
  });
}
