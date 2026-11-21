/// Formato de fechas en español, sin depender de `intl`.
library;

const _weekdays = [
  'lunes',
  'martes',
  'miércoles',
  'jueves',
  'viernes',
  'sábado',
  'domingo',
];
const _shortWeekdays = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
const _months = [
  'enero',
  'febrero',
  'marzo',
  'abril',
  'mayo',
  'junio',
  'julio',
  'agosto',
  'septiembre',
  'octubre',
  'noviembre',
  'diciembre',
];
const _shortMonths = [
  'ene',
  'feb',
  'mar',
  'abr',
  'may',
  'jun',
  'jul',
  'ago',
  'sep',
  'oct',
  'nov',
  'dic',
];

/// Inicial de cada día de la semana, de lunes a domingo (la miércoles es "X").
const weekdayInitials = ['L', 'M', 'X', 'J', 'V', 'S', 'D'];

String _capitalize(String s) => s[0].toUpperCase() + s.substring(1);

/// "Miércoles, 22 de octubre".
String formatLongDate(DateTime d) =>
    '${_capitalize(_weekdays[d.weekday - 1])}, ${d.day} de ${_months[d.month - 1]}';

/// "8:00 a. m." / "11:59 p. m.".
String formatTime(DateTime d) {
  final hour = d.hour % 12 == 0 ? 12 : d.hour % 12;
  final minute = d.minute.toString().padLeft(2, '0');
  final suffix = d.hour < 12 ? 'a. m.' : 'p. m.';
  return '$hour:$minute $suffix';
}

/// "Hoy, 8:00 a. m.", "Mañana, 11:59 p. m.", "Vie, 5:00 p. m." o "12 nov, ...".
String formatDueLabel(DateTime due, DateTime now) {
  final today = DateTime(now.year, now.month, now.day);
  final dueDay = DateTime(due.year, due.month, due.day);
  final days = dueDay.difference(today).inDays;
  final time = formatTime(due);
  if (days == 0) return 'Hoy, $time';
  if (days == 1) return 'Mañana, $time';
  if (days > 1 && days < 7) return '${_shortWeekdays[due.weekday - 1]}, $time';
  return '${due.day} ${_shortMonths[due.month - 1]}, $time';
}

/// "en 25 min", "en 4 horas", "en 2 días" (o "venció" si ya pasó).
String formatRelative(DateTime due, DateTime now) {
  final diff = due.difference(now);
  if (diff.isNegative) return 'venció';
  if (diff.inMinutes < 60) {
    final minutes = diff.inMinutes < 1 ? 1 : diff.inMinutes;
    return 'en $minutes min';
  }
  if (diff.inHours < 24) {
    final hours = diff.inHours;
    return hours == 1 ? 'en 1 hora' : 'en $hours horas';
  }
  final days = (diff.inHours / 24).round();
  return days <= 1 ? 'en 1 día' : 'en $days días';
}

String formatShortDate(DateTime d) =>
    '${d.day} de ${_shortMonths[d.month - 1]}';

/// "3 de nov · 06:00 p. m.".
String formatDateTimeShort(DateTime d) {
  final hour = (d.hour % 12 == 0 ? 12 : d.hour % 12).toString().padLeft(2, '0');
  final minute = d.minute.toString().padLeft(2, '0');
  final suffix = d.hour < 12 ? 'a. m.' : 'p. m.';
  return '${formatShortDate(d)} · $hour:$minute $suffix';
}

/// "noviembre".
String formatMonthName(DateTime d) => _months[d.month - 1];

/// "3 de noviembre".
String formatDayMonth(DateTime d) => '${d.day} de ${_months[d.month - 1]}';

/// "noviembre 2026".
String formatMonthYear(DateTime d) => '${_months[d.month - 1]} ${d.year}';

/// "06:00 p. m.".
String formatClockTime(DateTime d) {
  final hour = (d.hour % 12 == 0 ? 12 : d.hour % 12).toString().padLeft(2, '0');
  final minute = d.minute.toString().padLeft(2, '0');
  final suffix = d.hour < 12 ? 'a. m.' : 'p. m.';
  return '$hour:$minute $suffix';
}