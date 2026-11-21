import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Guarda los tokens de sesión en el almacenamiento seguro del dispositivo
/// (Keystore en Android). Nunca se escriben en preferencias ni en logs.
class TokenStorage {
  TokenStorage([FlutterSecureStorage? storage])
    : _storage = storage ?? const FlutterSecureStorage();

  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';

  final FlutterSecureStorage _storage;

  /// Token de acceso (dura poco; va en cada petición).
  Future<String?> read() => _storage.read(key: _accessKey);

  /// Token de renovación (dura 30 días; solo sirve para pedir otro par).
  Future<String?> readRefresh() => _storage.read(key: _refreshKey);

    /// Guarda el token de acceso y, si el servidor lo entrega, el de renovación.
  Future<void> save({required String access, String? refresh}) async {
    await _storage.write(key: _accessKey, value: access);
    if (refresh == null) {
      await _storage.delete(key: _refreshKey);
    } else {
      await _storage.write(key: _refreshKey, value: refresh);
    }
  }

  Future<void> clear() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }
}