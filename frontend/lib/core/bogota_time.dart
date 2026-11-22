/// Hora de Colombia (RT-03).
///
/// Toda fecha que el usuario ve o escribe está en hora de Colombia, sin
/// importar la zona del teléfono. Colombia está en UTC−5 todo el año (no tiene
/// horario de verano), así que basta con un desplazamiento fijo.
///
/// Dentro de la app las fechas son "de pared": un [DateTime] sin zona cuyos
/// campos (año, mes, día, hora...) son los de Colombia. Se convierten al leer
/// la API ([parseApiDateTime]) y al enviarla ([formatApiDateTime]).
library;

const Duration _bogotaOffset = Duration(hours: -5);

/// Reloj de la app. Las pruebas lo reemplazan para fijar el "ahora".
DateTime Function() clock = DateTime.now;

/// Fecha y hora de Colombia que corresponden al instante [instant].
DateTime toBogota(DateTime instant) {
  final wall = instant.toUtc().add(_bogotaOffset);
  return DateTime(
    wall.year,
    wall.month,
    wall.day,
    wall.hour,
    wall.minute,
    wall.second,
    wall.millisecond,
  );
}

/// El momento actual en hora de Colombia.
DateTime bogotaNow() => toBogota(clock());

/// Lee una fecha ISO 8601 con desplazamiento de la API y la pasa a hora de
/// Colombia.
DateTime parseApiDateTime(String value) => toBogota(DateTime.parse(value));

/// Versión de [parseApiDateTime] para campos que pueden venir nulos.
DateTime? parseApiDateTimeOrNull(Object? value) =>
    value is String ? parseApiDateTime(value) : null;

String _two(int n) => n.toString().padLeft(2, '0');

/// Escribe una fecha de Colombia con su desplazamiento:
/// `2026-10-05T23:59:00-05:00`.
String formatApiDateTime(DateTime bogota) =>
    '${bogota.year.toString().padLeft(4, '0')}-${_two(bogota.month)}-'
    '${_two(bogota.day)}T${_two(bogota.hour)}:${_two(bogota.minute)}:'
    '${_two(bogota.second)}-05:00';
