import '../tasks/task.dart';
import 'calendar_service.dart';

/// Vista de la Agenda: un día, una semana o el mes completo (RF-TAR-11).
enum CalendarMode { day, week, month }

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

/// Días que se piden al servidor: el mes completo o la semana (RF-TAR-11). La
/// vista de día pide su semana, porque la barra de días muestra la semana.
({DateTime start, DateTime end}) visibleRange(
  CalendarMode mode,
  DateTime focused,
) {
  if (mode == CalendarMode.month) {
    return (
      start: DateTime(focused.year, focused.month),
      end: DateTime(focused.year, focused.month + 1, 0),
    );
  }
  final days = weekDays(focused);
  return (start: days.first, end: days.last);
}

/// Clases agrupadas por día y ordenadas por hora de inicio.
Map<DateTime, List<ClassOccurrence>> classesByDay(
  List<ClassOccurrence> classes,
) {
  final map = <DateTime, List<ClassOccurrence>>{};
  for (final item in classes) {
    map.putIfAbsent(dateOnly(item.startsAt), () => []).add(item);
  }
  for (final list in map.values) {
    list.sort((a, b) => a.startsAt.compareTo(b.startsAt));
  }
  return map;
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

/// Días que muestra la vista de semana: de lunes a viernes, y el sábado y el
/// domingo solo si tienen una clase o una actividad (RF-TAR-11).
List<DateTime> compactWeek(
  List<DateTime> week,
  List<ClassOccurrence> classes,
  List<AcademicTask> tasks,
) {
  bool busy(DateTime day) =>
      classes.any((c) => isSameDay(c.startsAt, day)) ||
      tasks.any((t) => isSameDay(t.dueAt, day));
  return [
    for (final day in week)
      if (day.weekday <= DateTime.friday || busy(day)) day,
  ];
}

/// Horas visibles de la línea de tiempo de [days]: desde una hora antes de lo
/// primero hasta una hora después de lo último, así el rango se ajusta al
/// horario de cada estudiante. Sin nada en esos días, de 8 a 12 (RF-TAR-11).
(int, int) timelineHours(
  List<DateTime> days,
  List<ClassOccurrence> classes,
  List<AcademicTask> tasks,
) {
  bool shown(DateTime t) => days.any((d) => isSameDay(d, t));
  int? first;
  int? last;
  void include(int start, int end) {
    first = first == null || start < first! ? start : first;
    last = last == null || end > last! ? end : last;
  }

  for (final c in classes.where((c) => shown(c.startsAt))) {
    include(c.startsAt.hour, c.endsAt.hour + (c.endsAt.minute > 0 ? 1 : 0));
  }
  // Una entrega ocupa su hora: la de las 23:59 se ve antes de medianoche.
  for (final t in tasks.where((t) => shown(t.dueAt))) {
    include(t.dueAt.hour, t.dueAt.hour + 1);
  }
  if (first == null) return (8, 12);
  return ((first! - 1).clamp(0, 23), (last! + 1).clamp(1, 24));
}
