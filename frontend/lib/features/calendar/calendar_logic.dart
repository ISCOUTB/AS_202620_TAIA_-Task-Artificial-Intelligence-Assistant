import '../tasks/task.dart';

/// Vista del calendario: el mes completo o una sola semana.
enum CalendarMode { month, week }

/// Solo la fecha, sin la hora.
DateTime dateOnly(DateTime d) => DateTime(d.year, d.month, d.day);

bool isSameDay(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;

/// Lunes de la semana que contiene [d].
DateTime startOfWeek(DateTime d) =>
    DateTime(d.year, d.month, d.day - (d.weekday - 1));

/// Los siete días (lunes a domingo) de la semana que contiene [d].
List<DateTime> weekDays(DateTime d) {
  final start = startOfWeek(d);
  return [
    for (var i = 0; i < 7; i++)
      DateTime(start.year, start.month, start.day + i),
  ];
}

/// Primer día del mes que queda [months] meses después (o antes) de [d].
DateTime addMonths(DateTime d, int months) =>
    DateTime(d.year, d.month + months);

DateTime addWeeks(DateTime d, int weeks) =>
    DateTime(d.year, d.month, d.day + 7 * weeks);

/// Filas del mes, de lunes a domingo. Las celdas que no pertenecen al mes son
/// null (quedan en blanco).
List<List<DateTime?>> monthRows(DateTime month) {
  final daysInMonth = DateTime(month.year, month.month + 1, 0).day;
  final leading = DateTime(month.year, month.month).weekday - 1;
  final cells = <DateTime?>[
    for (var i = 0; i < leading; i++) null,
    for (var day = 1; day <= daysInMonth; day++)
      DateTime(month.year, month.month, day),
  ];
  while (cells.length % 7 != 0) {
    cells.add(null);
  }
  return [for (var i = 0; i < cells.length; i += 7) cells.sublist(i, i + 7)];
}

/// Tareas agrupadas por día de entrega, y dentro de cada día por hora.
Map<DateTime, List<AcademicTask>> tasksByDay(List<AcademicTask> tasks) {
  final map = <DateTime, List<AcademicTask>>{};
  for (final task in tasks) {
    map.putIfAbsent(dateOnly(task.dueAt), () => []).add(task);
  }
  for (final list in map.values) {
    list.sort((a, b) => a.dueAt.compareTo(b.dueAt));
  }
  return map;
}

/// Punto bajo el número del día.
enum DayMarker { none, pending, doneOnly }

DayMarker markerFor(List<AcademicTask>? tasks) {
  if (tasks == null || tasks.isEmpty) return DayMarker.none;
  return tasks.any((t) => t.status != TaskStatus.completed)
      ? DayMarker.pending
      : DayMarker.doneOnly;
}