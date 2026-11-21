import 'package:flutter/material.dart';

import '../../../core/spanish_dates.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../../tasks/task.dart';
import '../calendar_logic.dart';

/// Tarjeta con el calendario: mes completo o una semana, con un punto en los
/// días que tienen actividades. Se cambia de mes o semana con las flechas o
/// deslizando hacia los lados.
class CalendarCard extends StatelessWidget {
  const CalendarCard({
    super.key,
    required this.mode,
    required this.focused,
    required this.selected,
    required this.today,
    required this.tasksByDay,
    required this.onSelect,
    required this.onPrevious,
    required this.onNext,
    required this.onToday,
  });

  final CalendarMode mode;

  /// Cualquier día del mes o de la semana que se está viendo.
  final DateTime focused;
  final DateTime selected;
  final DateTime today;
  final Map<DateTime, List<AcademicTask>> tasksByDay;
  final ValueChanged<DateTime> onSelect;
  final VoidCallback onPrevious;
  final VoidCallback onNext;
  final VoidCallback onToday;

  static const _initials = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];

  @override
  Widget build(BuildContext context) {
    final isMonth = mode == CalendarMode.month;
    final rows = isMonth
        ? monthRows(focused)
        : <List<DateTime?>>[weekDays(focused)];
    final gridKey = isMonth
        ? 'm-${focused.year}-${focused.month}'
        : 'w-${startOfWeek(focused).toIso8601String()}';

    return GestureDetector(
      onHorizontalDragEnd: (details) {
        final velocity = details.primaryVelocity ?? 0;
        if (velocity < -250) {
          onNext();
        } else if (velocity > 250) {
          onPrevious();
        }
      },
      child: Container(
        padding: const EdgeInsets.fromLTRB(10, 6, 10, 14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(28),
          boxShadow: [
            BoxShadow(
              color: taiaInk.withValues(alpha: 0.07),
              blurRadius: 18,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Column(
          children: [
            Row(
              children: [
                IconButton(
                  tooltip: isMonth ? 'Mes anterior' : 'Semana anterior',
                  color: taiaInk,
                  onPressed: onPrevious,
                  icon: const Icon(Icons.chevron_left),
                ),
                Expanded(
                  child: Center(
                    child: isSameDay(selected, today)
                        ? const SizedBox(height: 48)
                        : TextButton(
                            style: TextButton.styleFrom(
                              foregroundColor: TaiaColors.fieryRose,
                            ),
                            onPressed: onToday,
                            child: const Text(
                              'Ir a hoy',
                              style: TextStyle(fontWeight: FontWeight.w800),
                            ),
                          ),
                  ),
                ),
                IconButton(
                  tooltip: isMonth ? 'Mes siguiente' : 'Semana siguiente',
                  color: taiaInk,
                  onPressed: onNext,
                  icon: const Icon(Icons.chevron_right),
                ),
              ],
            ),
            Row(
              children: [
                for (final letter in _initials)
                  Expanded(
                    child: Center(
                      child: Text(
                        letter,
                        style: TextStyle(
                          color: TaiaColors.sunsetCoral.withValues(alpha: 0.9),
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            AnimatedSize(
              duration: const Duration(milliseconds: 200),
              alignment: Alignment.topCenter,
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 200),
                child: Column(
                  key: ValueKey(gridKey),
                  children: [
                    for (final row in rows)
                      Row(
                        children: [
                          for (final day in row)
                            Expanded(
                              child: day == null
                                  ? const SizedBox(height: 52)
                                  : _DayCell(
                                      day: day,
                                      isSelected: isSameDay(day, selected),
                                      isToday: isSameDay(day, today),
                                      tasks: tasksByDay[day],
                                      onTap: () => onSelect(day),
                                    ),
                            ),
                        ],
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DayCell extends StatelessWidget {
  const _DayCell({
    required this.day,
    required this.isSelected,
    required this.isToday,
    required this.tasks,
    required this.onTap,
  });

  final DateTime day;
  final bool isSelected;
  final bool isToday;
  final List<AcademicTask>? tasks;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final count = tasks?.length ?? 0;
    final marker = markerFor(tasks);
    final dotColor = isSelected
        ? Colors.transparent
        : switch (marker) {
            DayMarker.pending => TaiaColors.fieryRose,
            DayMarker.doneOnly => TaiaColors.softPeach,
            DayMarker.none => Colors.transparent,
          };
    final description = count == 0
        ? formatDayMonth(day)
        : '${formatDayMonth(day)}, '
              '${count == 1 ? '1 actividad' : '$count actividades'}';

    return Semantics(
      button: true,
      selected: isSelected,
      label: description,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onTap,
        child: SizedBox(
          height: 52,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 38,
                height: 38,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: isSelected ? TaiaColors.fieryRose : Colors.transparent,
                  border: isToday && !isSelected
                      ? Border.all(color: TaiaColors.sunsetCoral, width: 1.8)
                      : null,
                ),
                child: Text(
                  '${day.day}',
                  style: TextStyle(
                    color: isSelected ? Colors.white : taiaInk,
                    fontSize: 16,
                    fontWeight: isSelected || isToday
                        ? FontWeight.w800
                        : FontWeight.w500,
                  ),
                ),
              ),
              const SizedBox(height: 3),
              Container(
                width: 5,
                height: 5,
                decoration: BoxDecoration(
                  color: dotColor,
                  shape: BoxShape.circle,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}