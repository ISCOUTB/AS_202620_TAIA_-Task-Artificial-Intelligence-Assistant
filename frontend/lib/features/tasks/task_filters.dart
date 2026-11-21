import 'task.dart';

/// Filtro por estado (las pestañas de la lista).
enum TaskFilter {
  all('Todas'),
  pending('Pendientes'),
  completed('Completadas'),
  overdue('Atrasadas'),
  urgent('Urgentes');

  const TaskFilter(this.label);

  final String label;
}

/// Filtro por fecha límite.
enum DateFilter {
  any('Cualquier fecha'),
  today('Hoy'),
  tomorrow('Mañana'),
  thisWeek('Esta semana'),
  thisMonth('Este mes'),
  day('Elegir un día…');

  const DateFilter(this.label);

  final String label;
}

/// Minúsculas y sin tildes, para buscar sin importar cómo se escribió.
String normalizeText(String text) {
  const from = 'áàäâéèëêíìïîóòöôúùüûñ';
  const to = 'aaaaeeeeiiiioooouuuun';
  final buffer = StringBuffer();
  for (final rune in text.toLowerCase().runes) {
    final char = String.fromCharCode(rune);
    final index = from.indexOf(char);
    buffer.write(index >= 0 ? to[index] : char);
  }
  return buffer.toString();
}

DateTime _day(DateTime d) => DateTime(d.year, d.month, d.day);

/// Aplica búsqueda, estado y fecha. La búsqueda mira título, descripción y
/// nombre de la materia.
///
/// - Pendientes: todo lo que no está completado (incluye las atrasadas).
/// - Urgentes: pendientes con prioridad alta (menos de 48 h).
List<AcademicTask> applyTaskFilters(
  List<AcademicTask> tasks, {
  required TaskFilter status,
  required String search,
  required DateFilter date,
  required DateTime now,
  DateTime? pickedDay,
}) {
  final needle = normalizeText(search.trim());
  final today = _day(now);
  final tomorrow = DateTime(today.year, today.month, today.day + 1);
  final weekStart = DateTime(
    today.year,
    today.month,
    today.day - (today.weekday - 1),
  );
  final weekEnd = DateTime(weekStart.year, weekStart.month, weekStart.day + 7);

  return tasks.where((task) {
    final statusOk = switch (status) {
      TaskFilter.all => true,
      TaskFilter.pending => task.status != TaskStatus.completed,
      TaskFilter.completed => task.status == TaskStatus.completed,
      TaskFilter.overdue => task.status == TaskStatus.overdue,
      TaskFilter.urgent => task.isUrgent,
    };
    if (!statusOk) return false;

    if (needle.isNotEmpty) {
      final text = normalizeText(
        '${task.title} ${task.subjectName} ${task.description ?? ''}',
      );
      if (!text.contains(needle)) return false;
    }

    final due = task.dueAt;
    final dueDay = _day(due);
    return switch (date) {
      DateFilter.any => true,
      DateFilter.today => dueDay == today,
      DateFilter.tomorrow => dueDay == tomorrow,
      DateFilter.thisWeek =>
        !dueDay.isBefore(weekStart) && dueDay.isBefore(weekEnd),
      DateFilter.thisMonth =>
        due.year == today.year && due.month == today.month,
      DateFilter.day => pickedDay != null && dueDay == _day(pickedDay),
    };
  }).toList();
}

/// Tareas sin completar (pendientes y atrasadas).
int unfinishedCount(List<AcademicTask> tasks) =>
    tasks.where((t) => t.status != TaskStatus.completed).length;

class TaskGroup {
  const TaskGroup(this.title, this.tasks);

  final String title;
  final List<AcademicTask> tasks;
}

const _groupOrder = [
  'Atrasadas',
  'Hoy',
  'Mañana',
  'Esta semana',
  'Más adelante',
  'Completadas',
];

String _groupOf(AcademicTask task, DateTime today, DateTime nextMonday) {
  if (task.status == TaskStatus.completed) return 'Completadas';
  final dueDay = _day(task.dueAt);
  if (task.status == TaskStatus.overdue || dueDay.isBefore(today)) {
    return 'Atrasadas';
  }
  if (dueDay == today) return 'Hoy';
  if (dueDay == DateTime(today.year, today.month, today.day + 1)) {
    return 'Mañana';
  }
  if (dueDay.isBefore(nextMonday)) return 'Esta semana';
  return 'Más adelante';
}

/// Agrupa por día de entrega, en el orden: atrasadas, hoy, mañana, esta
/// semana, más adelante y completadas. Dentro de cada grupo van por fecha.
List<TaskGroup> groupTasks(List<AcademicTask> tasks, DateTime now) {
  final today = _day(now);
  final nextMonday = DateTime(
    today.year,
    today.month,
    today.day + (8 - today.weekday),
  );
  final buckets = {for (final title in _groupOrder) title: <AcademicTask>[]};
  for (final task in tasks) {
    buckets[_groupOf(task, today, nextMonday)]!.add(task);
  }
  return [
    for (final title in _groupOrder)
      if (buckets[title]!.isNotEmpty)
        TaskGroup(
          title,
          buckets[title]!..sort(
            (a, b) => title == 'Completadas'
                ? b.dueAt.compareTo(a.dueAt)
                : a.dueAt.compareTo(b.dueAt),
          ),
        ),
  ];
}