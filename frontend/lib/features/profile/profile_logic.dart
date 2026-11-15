/// Dónde recibe el usuario sus recordatorios.
enum NotificationChannel {
  /// En la aplicación (la campanita).
  app,

  /// Por el bot de Telegram (requiere la cuenta vinculada).
  telegram;

  /// Lee el valor guardado; si no hay o es desconocido, usa la aplicación.
  static NotificationChannel parse(String? value) => value == 'telegram'
      ? NotificationChannel.telegram
      : NotificationChannel.app;

  String get label => switch (this) {
    NotificationChannel.app => 'En la aplicación',
    NotificationChannel.telegram => 'Por Telegram',
  };
}

/// Canal que realmente se usa: Telegram solo vale con la cuenta vinculada.
NotificationChannel effectiveChannel(
  NotificationChannel preferred, {
  required bool telegramLinked,
}) {
  if (preferred == NotificationChannel.telegram && !telegramLinked) {
    return NotificationChannel.app;
  }
  return preferred;
}

/// Iniciales para el avatar: "Valeria Ríos Pérez" → "VR".
String initialsOf(String fullName) {
  final words = fullName
      .trim()
      .split(RegExp(r'\s+'))
      .where((w) => w.isNotEmpty)
      .toList();
  if (words.isEmpty) return '?';
  final first = words.first[0];
  final second = words.length > 1 ? words[1][0] : '';
  return (first + second).toUpperCase();
}