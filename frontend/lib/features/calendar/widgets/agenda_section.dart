import 'package:flutter/material.dart';

import '../../../core/spanish_dates.dart';
import '../../../mascot/mascot_expression.dart';
import '../../../mascot/taia_mascot.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../../tasks/task.dart';
import '../calendar_logic.dart';
import '../calendar_service.dart';

/// "Agenda del 3 de noviembre": las clases y las actividades del día
/// seleccionado (RF-TAR-11), o un mensaje con la mascota si el día está libre.
class AgendaSection extends StatelessWidget {
  const AgendaSection({
    super.key,
    required this.day,
    required this.today,
    required this.tasks,
    this.classes = const [],
    required this.expression,
    required this.onTapTask,
  });

  final DateTime day;
  final DateTime today;
  final List<AcademicTask> tasks;
  final List<ClassOccurrence> classes;
  final MascotExpression expression;
  final ValueChanged<AcademicTask> onTapTask;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                'Agenda del ${formatDayMonth(day)}',
                style: const TextStyle(
                  color: taiaInk,
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
            if (tasks.isNotEmpty)
              Container(
                width: 56,
                padding: const EdgeInsets.all(5),
                decoration: BoxDecoration(
                  color: TaiaColors.fieryRose,
                  borderRadius: BorderRadius.circular(18),
                ),
                child: TaiaMascot(motion: 0.5, expression: expression),
              ),
          ],
        ),
        const SizedBox(height: 12),
        if (tasks.isEmpty && classes.isEmpty)
          _EmptyDay(day: day, today: today, expression: expression),
        for (final item in classes) ...[
          _ClassItem(item: item),
          const SizedBox(height: 10),
        ],
        if (tasks.isNotEmpty)
          for (final task in tasks) ...[
            _AgendaItem(task: task, onTap: () => onTapTask(task)),
            const SizedBox(height: 10),
          ],
      ],
    );
  }
}

class _AgendaItem extends StatelessWidget {
  const _AgendaItem({required this.task, required this.onTap});

  final AcademicTask task;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final completed = task.status == TaskStatus.completed;
    final accent = switch (task.status) {
      TaskStatus.completed => TaiaColors.apricotWhisper,
      TaskStatus.overdue => TaiaColors.mascotRed,
      TaskStatus.pending => TaiaColors.fieryRose,
    };
    final statusLabel = switch (task.status) {
      TaskStatus.completed => 'completada',
      TaskStatus.overdue => 'atrasada',
      TaskStatus.pending => task.isUrgent ? 'urgente' : 'pendiente',
    };

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 62,
          child: Padding(
            padding: const EdgeInsets.only(top: 14, right: 8),
            child: Text(
              formatClockTime(task.dueAt),
              style: TextStyle(
                color: TaiaColors.fieryRose.withValues(alpha: 0.85),
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ),
        Expanded(
          child: Material(
            color: Colors.white,
            borderRadius: BorderRadius.circular(18),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: onTap,
              child: IntrinsicHeight(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Container(width: 4, color: accent),
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 10,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: TaiaColors.softPeach.withValues(
                                  alpha: 0.7,
                                ),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Text(
                                task.type == TaskType.exam
                                    ? '${task.subjectName} · Examen'
                                    : task.subjectName,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  color: taiaInk,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              task.title,
                              style: TextStyle(
                                color: completed
                                    ? taiaInk.withValues(alpha: 0.5)
                                    : taiaInk,
                                fontSize: 16,
                                fontWeight: FontWeight.w800,
                                decoration: completed
                                    ? TextDecoration.lineThrough
                                    : null,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              '${formatShortDate(task.dueAt)} · $statusLabel',
                              style: TextStyle(
                                color: taiaInk.withValues(alpha: 0.6),
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/// Una clase del horario en la agenda del día.
class _ClassItem extends StatelessWidget {
  const _ClassItem({required this.item});

  final ClassOccurrence item;

  @override
  Widget build(BuildContext context) {
    final room = item.room;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 62,
          child: Padding(
            padding: const EdgeInsets.only(top: 12, right: 8),
            child: Text(
              formatClockTime(item.startsAt),
              style: TextStyle(
                color: taiaInk.withValues(alpha: 0.6),
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ),
        Expanded(
          child: Container(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
            decoration: BoxDecoration(
              color: TaiaColors.softPeach.withValues(alpha: 0.45),
              borderRadius: BorderRadius.circular(18),
            ),
            child: Row(
              children: [
                const Icon(Icons.school_outlined, color: taiaInk, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.subjectName,
                        style: const TextStyle(
                          color: taiaInk,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      Text(
                        room == null
                            ? 'Clase hasta las ${formatClockTime(item.endsAt)}'
                            : 'Clase hasta las ${formatClockTime(item.endsAt)}'
                                  ' · $room',
                        style: TextStyle(
                          color: taiaInk.withValues(alpha: 0.65),
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _EmptyDay extends StatelessWidget {
  const _EmptyDay({
    required this.day,
    required this.today,
    required this.expression,
  });

  final DateTime day;
  final DateTime today;
  final MascotExpression expression;

  @override
  Widget build(BuildContext context) {
    final String title;
    final String subtitle;
    if (isSameDay(day, today)) {
      title = '¡Día libre!';
      subtitle = 'No tienes nada para hoy. Puedes relajarte y descansar.';
    } else if (day.isBefore(today)) {
      title = 'Sin actividades';
      subtitle = 'No tenías entregas este día.';
    } else {
      title = 'Todo tranquilo';
      subtitle = 'Nada programado para este día. Puedes relajarte.';
    }
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 22),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: TaiaColors.softPeach),
      ),
      child: Column(
        children: [
          Container(
            width: 130,
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: TaiaColors.fieryRose,
              borderRadius: BorderRadius.circular(28),
            ),
            child: TaiaMascot(motion: 0.6, expression: expression),
          ),
          const SizedBox(height: 14),
          Text(
            title,
            style: const TextStyle(
              color: taiaInk,
              fontSize: 18,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            subtitle,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: taiaInk.withValues(alpha: 0.7),
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }
}