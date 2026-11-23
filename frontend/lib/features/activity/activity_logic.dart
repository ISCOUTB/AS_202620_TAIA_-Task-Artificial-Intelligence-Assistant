import '../../core/spanish_dates.dart';
import '../reminders/reminder_option.dart';
import '../tasks/task.dart';

/// Fecha límite por defecto: mañana a las 11:59 p. m.
DateTime defaultDueDate(DateTime now) =>
    DateTime(now.year, now.month, now.day + 1, 23, 59);

/// Cambia el día de [due] sin tocar la hora.
DateTime withDate(DateTime due, DateTime date) =>
    DateTime(date.year, date.month, date.day, due.hour, due.minute);

/// Cambia la hora de [due] sin tocar el día.
DateTime withTime(DateTime due, int hour, int minute) =>
    DateTime(due.year, due.month, due.day, hour, minute);

/// El backend solo acepta fechas límite posteriores al momento actual.
bool isFutureDue(DateTime due, DateTime now) => due.isAfter(now);

/// Atajos de fecha: hoy, mañana, el próximo viernes y dentro de una semana
/// (RNF-14). El viernes no se repite si ya es hoy o mañana.
List<({String label, DateTime date})> quickDates(DateTime now) {
  final today = DateTime(now.year, now.month, now.day);
  final tomorrow = DateTime(now.year, now.month, now.day + 1);
  var friday = DateTime(
    now.year,
    now.month,
    now.day + (DateTime.friday - now.weekday) % 7,
  );
  if (!friday.isAfter(tomorrow)) {
    friday = DateTime(friday.year, friday.month, friday.day + 7);
  }
  final week = DateTime(now.year, now.month, now.day + 7);
  return [
    (label: 'Hoy', date: today),
    (label: 'Mañana', date: tomorrow),
    if (!sameDay(friday, week)) (label: 'El viernes', date: friday),
    (label: 'En 1 semana', date: week),
  ];
}

/// Atajos de hora más comunes para una entrega o un examen (RNF-14).
const quickTimes = [
  (label: '8:00 a. m.', hour: 8, minute: 0),
  (label: '12:00 m.', hour: 12, minute: 0),
  (label: '6:00 p. m.', hour: 18, minute: 0),
  (label: '11:59 p. m.', hour: 23, minute: 59),
];

bool sameDay(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;

/// Palabras para empezar el título con un toque (RNF-14).
List<String> titleSuggestions(TaskType type) => type == TaskType.exam
    ? const ['Parcial', 'Quiz', 'Examen final', 'Sustentación']
    : const ['Taller', 'Informe', 'Lectura', 'Proyecto', 'Exposición'];

/// "Parcial de Cálculo", o solo "Parcial" si aún no hay materia.
String suggestedTitle(String word, String? subjectName) =>
    subjectName == null ? word : '$word de $subjectName';

/// "Vence el viernes 10 de octubre a las 11:59 p. m. · en 3 días".
String dueSentence(DateTime due, DateTime now) {
  final day = formatLongDate(due).replaceFirst(', ', ' ').toLowerCase();
  return 'Vence el $day a las ${formatTime(due)} · '
      '${formatRelative(due, now)}';
}

/// Lo que TAIA va a crear, en una frase que se actualiza mientras se llena el
/// formulario (RNF-14), con su voz (RF-AGT-22).
String activitySummary({
  required TaskType type,
  required String title,
  required String? subjectName,
  required DateTime due,
  required ReminderMode reminders,
  required int customReminders,
}) {
  final kind = type == TaskType.exam ? 'el examen' : 'la tarea';
  final name = title.trim();
  if (name.isEmpty) return 'Ponle un título y yo armo el resto.';
  if (subjectName == null) return 'Elige la materia de "$name".';
  final day = formatLongDate(due).replaceFirst(', ', ' ').toLowerCase();
  final reminderText = switch (reminders) {
    ReminderMode.defaults =>
      'con recordatorios la tarde anterior y cada 2 días',
    ReminderMode.none => 'sin recordatorios',
    ReminderMode.custom =>
      customReminders == 1
          ? 'con 1 recordatorio tuyo'
          : 'con $customReminders recordatorios tuyos',
  };
  // Si el título ya nombra la materia, no se repite.
  final ofSubject = name.toLowerCase().contains(subjectName.toLowerCase())
      ? ''
      : ' de $subjectName';
  return 'Voy a crear $kind "$name"$ofSubject para el $day a las '
      '${formatTime(due)}, $reminderText.';
}
