import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/tasks/task.dart';
import 'package:taia/features/tasks/task_filters.dart';

/// H-15: la lista de tareas pide los filtros al servidor (RF-TAR-04).
void main() {
  // Miércoles 7 de octubre de 2026, 10:00 en Colombia.
  final now = DateTime(2026, 10, 7, 10);

  TaskListQuery query(
    TaskFilter status, {
    String search = '',
    DateFilter date = DateFilter.any,
    DateTime? pickedDay,
  }) => taskQueryFor(
    status: status,
    search: search,
    date: date,
    pickedDay: pickedDay,
    now: now,
  );

  test('Pendientes pide pendientes y atrasadas juntas', () {
    expect(query(TaskFilter.pending).statuses, [
      TaskStatus.pending,
      TaskStatus.overdue,
    ]);
  });

  test('Todas no filtra por estado', () {
    expect(query(TaskFilter.all).statuses, isEmpty);
  });

  test('Urgentes son las pendientes que vencen en 48 h (RF-TAR-03)', () {
    final urgent = query(TaskFilter.urgent);

    expect(urgent.statuses, [TaskStatus.pending]);
    expect(urgent.dueTo, DateTime(2026, 10, 9, 10));
  });

  test('Urgentes dentro de hoy se queda con el fin del día', () {
    final urgent = query(TaskFilter.urgent, date: DateFilter.today);

    expect(urgent.dueFrom, DateTime(2026, 10, 7));
    expect(urgent.dueTo, DateTime(2026, 10, 7, 23, 59, 59));
  });

  test('Esta semana va de lunes a domingo', () {
    final week = query(TaskFilter.all, date: DateFilter.thisWeek);

    expect(week.dueFrom, DateTime(2026, 10, 5));
    expect(week.dueTo, DateTime(2026, 10, 11, 23, 59, 59));
  });

  test('Este mes va del 1 al último día', () {
    final month = query(TaskFilter.all, date: DateFilter.thisMonth);

    expect(month.dueFrom, DateTime(2026, 10));
    expect(month.dueTo, DateTime(2026, 10, 31, 23, 59, 59));
  });

  test('Un día elegido cubre ese día completo', () {
    final day = query(
      TaskFilter.all,
      date: DateFilter.day,
      pickedDay: DateTime(2026, 10, 20, 15),
    );

    expect(day.dueFrom, DateTime(2026, 10, 20));
    expect(day.dueTo, DateTime(2026, 10, 20, 23, 59, 59));
  });

  test('La búsqueda viaja recortada y vacía no se envía', () {
    expect(query(TaskFilter.all, search: '  física ').text, 'física');
    expect(query(TaskFilter.all, search: '   ').text, isNull);
  });
}
