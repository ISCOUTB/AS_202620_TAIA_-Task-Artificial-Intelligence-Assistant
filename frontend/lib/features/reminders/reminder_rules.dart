/// Regla de RF-REC-01: la hora del recordatorio debe ser futura y anterior a
/// la fecha límite de la actividad. Devuelve el mensaje de error o null.
String? reminderTimeError(
  DateTime at, {
  required DateTime due,
  required DateTime now,
}) {
  if (!at.isAfter(now)) return 'El recordatorio debe ser en el futuro.';
  if (!at.isBefore(due)) {
    return 'El recordatorio debe ser antes de la fecha límite.';
  }
  return null;
}

/// Hora propuesta para un recordatorio nuevo: la próxima hora en punto.
DateTime suggestedReminderTime(DateTime now) =>
    DateTime(now.year, now.month, now.day, now.hour + 1);
