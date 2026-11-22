import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/api_client.dart';
import 'package:taia/core/token_storage.dart';
import 'package:taia/features/auth/auth_service.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

/// Tokens en memoria, sin el almacenamiento seguro del teléfono.
class MemoryTokens extends TokenStorage {
  MemoryTokens({this.access, this.refresh});

  String? access;
  String? refresh;

  @override
  Future<String?> read() async => access;

  @override
  Future<String?> readRefresh() async => refresh;

  @override
  Future<void> save({required String access, String? refresh}) async {
    this.access = access;
    this.refresh = refresh;
  }

  @override
  Future<void> clear() async {
    access = null;
    refresh = null;
  }
}

void main() {
  group('RF-USR-04 · cerrar sesión', () {
    test('con el token de acceso vencido, renueva y revoca la sesión', () async {
      final tokens = MemoryTokens(access: 'vencido', refresh: 'r1');
      final revokedWith = <String?>[];
      final api = FakeApi(
        routes({
          'POST /users/logout': (request) {
            final auth = request.headers['Authorization'];
            if (auth == 'Bearer vencido') {
              return const FakeResponse(401, {'detail': 'Token expirado.'});
            }
            revokedWith.add(auth as String?);
            return const FakeResponse(204);
          },
          'POST /users/refresh': (_) => const FakeResponse(200, {
            'access_token': 'nuevo',
            'refresh_token': 'r2',
            'token_type': 'bearer',
          }),
        }),
      );
      final service = AuthService(
        dio: buildDio(tokens, adapter: api),
        tokens: tokens,
      );

      await service.logout();

      expect(revokedWith, ['Bearer nuevo']);
      expect(tokens.access, isNull);
      expect(tokens.refresh, isNull);
    });

    test('si el servidor falla, borra los tokens locales igual', () async {
      final tokens = MemoryTokens(access: 'a1', refresh: 'r1');
      final api = FakeApi(
        (_) => const FakeResponse(503, {'detail': 'No disponible.'}),
      );
      final service = AuthService(
        dio: buildDio(tokens, adapter: api),
        tokens: tokens,
      );

      await service.logout();

      expect(api.requests.single.path, '/users/logout');
      expect(tokens.access, isNull);
      expect(tokens.refresh, isNull);
    });
  });

  test('RF-USR-03 · una renovación rechazada cierra la sesión local', () async {
    final tokens = MemoryTokens(access: 'vencido', refresh: 'revocado');
    var expired = false;
    sessionEvents.onExpired = () => expired = true;
    addTearDown(() => sessionEvents.onExpired = null);
    final api = FakeApi(
      routes({
        'GET /users/me': (_) =>
            const FakeResponse(401, {'detail': 'Token expirado.'}),
        'POST /users/refresh': (_) =>
            const FakeResponse(401, {'detail': 'Sesión inválida.'}),
      }),
    );
    final service = AuthService(
      dio: buildDio(tokens, adapter: api),
      tokens: tokens,
    );

    await expectLater(service.me(), throwsA(isA<ApiException>()));

    expect(expired, isTrue);
    expect(tokens.access, isNull);
  });
}
