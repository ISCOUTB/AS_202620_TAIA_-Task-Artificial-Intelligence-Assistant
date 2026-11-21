import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'profile_logic.dart';

/// Guarda en el teléfono por dónde quiere recibir los recordatorios el usuario.
///
/// El backend todavía no guarda esta preferencia, así que vive solo en el
/// dispositivo. Se usa el almacenamiento seguro que ya tiene la app para no
/// sumar otra dependencia.
class NotificationPrefs {
  NotificationPrefs([FlutterSecureStorage? storage])
    : _storage = storage ?? const FlutterSecureStorage();

  static const _key = 'notification_channel';

  final FlutterSecureStorage _storage;

  Future<NotificationChannel> read() async =>
      NotificationChannel.parse(await _storage.read(key: _key));

  Future<void> save(NotificationChannel channel) =>
      _storage.write(key: _key, value: channel.name);

  Future<void> clear() => _storage.delete(key: _key);
}

final NotificationPrefs notificationPrefs = NotificationPrefs();