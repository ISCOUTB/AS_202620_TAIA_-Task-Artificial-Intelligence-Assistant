import '../reminders/reminder.dart';
import '../tasks/task.dart';

/// Estado del día para la tarjeta principal.
enum DayState { free, pending, done }

/// Todo lo que muestra la pantalla de inicio, ya calculado.
class HomeData {
  const HomeData({
    required this.firstName,
    required this.todayTotal,
    required this.todayDone,
    required this.upcoming,
    required this.weekCounts,
    required this.weekTotal,
    required this.reminders,
  });

  /// Arma los datos a partir de lo que devuelve la API.
  ///
  /// [weekTasks] son las tareas con entrega entre [weekStart] (lunes) y el
  /// domingo; [reminders] se filtran a los pendientes.
  factory HomeData.build({
    required String fullName,
    required List<AcademicTask> todayTasks,
    required List<AcademicTask> upcoming,
    required List<AcademicTask> weekTasks,
    required DateTime weekStart,
    required List<Reminder> reminders,
  }) {
    final weekEnd = DateTime(
      weekStart.year,
      weekStart.month,
      weekStart.day + 7,
    );
    final counts = List<int>.filled(7, 0);
    for (final task in weekTasks) {
      final due = task.dueAt;
      if (!due.isBefore(weekStart) && due.isBefore(weekEnd)) {
        counts[due.weekday - 1]++;
      }
    }
    final pending = reminders.where((r) => !r.isCompleted).toList()
      ..sort((a, b) => a.scheduledAt.compareTo(b.scheduledAt));
    final parts = fullName.trim().split(RegExp(r'\s+'));
    return HomeData(
      firstName: parts.first,
      todayTotal: todayTasks.length,
      todayDone: todayTasks
          .where((t) => t.status == TaskStatus.completed)
          .length,
      upcoming: upcoming,
      weekCounts: counts,
      weekTotal: counts.fold(0, (sum, n) => sum + n),
      reminders: pending,
    );
  }

  final String firstName;

  /// Tareas con entrega hoy y cuántas ya están completadas.
  final int todayTotal;
  final int todayDone;

  /// Próximas entregas pendientes, ordenadas por fecha.
  final List<AcademicTask> upcoming;

  /// Tareas por día de la semana actual, de lunes (0) a domingo (6).
  final List<int> weekCounts;
  final int weekTotal;

  /// Recordatorios pendientes, del más cercano al más lejano.
  final List<Reminder> reminders;

  int get todayPending => todayTotal - todayDone;

  DayState get dayState {
    if (todayTotal == 0) return DayState.free;
    return todayPending > 0 ? DayState.pending : DayState.done;
  }
}