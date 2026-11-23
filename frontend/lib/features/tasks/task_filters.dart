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

DateTime _day(DateTime d) => DateTime(d.year, d.month, d.day);

/// Filtros de la lista traducidos a `GET /academic/tasks` (RF-TAR-04, H-15).
class TaskListQuery {
  const TaskListQuery({
    this.statuses = const [],
    this.dueFrom,
    this.dueTo,
    this.text,
  });

  final List<TaskStatus> statuses;
  final DateTime? dueFrom;
  final DateTime? dueTo;
  final String? text;
}

/// El servidor filtra; la app solo arma los parámetros. La búsqueda del
/// servidor mira título, descripción y nombre de la materia.
///
/// - Pendientes: pendientes y atrasadas juntas (las no completadas).
/// - Urgentes: pendientes que vencen en menos de 48 h, que es la prioridad
///   alta de RF-TAR-03.
TaskListQuery taskQueryFor({
  required TaskFilter status,
  required String search,
  required DateFilter date,
  required DateTime now,
  DateTime? pickedDay,
}) {
  final today = _day(now);
  DateTime endOf(DateTime day) =>
      DateTime(day.year, day.month, day.day, 23, 59, 59);

  final (DateTime?, DateTime?) range = switch (date) {
    DateFilter.any => (null, null),
    DateFilter.today => (today, endOf(today)),
    DateFilter.tomorrow => (
      DateTime(today.year, today.month, today.day + 1),
      endOf(DateTime(today.year, today.month, today.day + 1)),
    ),
    DateFilter.thisWeek => (
      DateTime(today.year, today.month, today.day - (today.weekday - 1)),
      endOf(DateTime(today.year, today.month, today.day + (7 - today.weekday))),
    ),
    DateFilter.thisMonth => (
      DateTime(today.year, today.month),
      endOf(DateTime(today.year, today.month + 1, 0)),
    ),
    DateFilter.day =>
      pickedDay == null ? (null, null) : (_day(pickedDay), endOf(pickedDay)),
  };
  var (dueFrom, dueTo) = range;

  final statuses = switch (status) {
    TaskFilter.all => const <TaskStatus>[],
    TaskFilter.pending => const [TaskStatus.pending, TaskStatus.overdue],
    TaskFilter.completed => const [TaskStatus.completed],
    TaskFilter.overdue => const [TaskStatus.overdue],
    TaskFilter.urgent => const [TaskStatus.pending],
  };
  if (status == TaskFilter.urgent) {
    final limit = now.add(const Duration(hours: 48));
    if (dueTo == null || limit.isBefore(dueTo)) dueTo = limit;
  }

  final text = search.trim();
  return TaskListQuery(
    statuses: statuses,
    dueFrom: dueFrom,
    dueTo: dueTo,
    text: text.isEmpty ? null : text,
  );
}

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
