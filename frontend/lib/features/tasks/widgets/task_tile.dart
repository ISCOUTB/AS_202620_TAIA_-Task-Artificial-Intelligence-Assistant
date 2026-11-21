import 'package:flutter/material.dart';

import '../../../core/spanish_dates.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../task.dart';

/// Fila de la lista: círculo para completar, título, materia, fecha y estado.
class TaskTile extends StatelessWidget {
  const TaskTile({
    super.key,
    required this.task,
    required this.onTap,
    required this.onToggle,
    this.busy = false,
  });

  final AcademicTask task;
  final VoidCallback onTap;
  final VoidCallback onToggle;

  /// Mientras se completa o reabre, el círculo muestra un indicador.
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final completed = task.status == TaskStatus.completed;
    return Material(
      color: Colors.white,
      elevation: 0,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.fromLTRB(12, 12, 14, 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: taiaInk.withValues(alpha: 0.06),
                blurRadius: 14,
                offset: const Offset(0, 5),
              ),
            ],
          ),
          child: Row(
            children: [
              _CheckCircle(
                completed: completed,
                busy: busy,
                onPressed: onToggle,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      task.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
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
                    const SizedBox(height: 4),
                    Wrap(
                      crossAxisAlignment: WrapCrossAlignment.center,
                      spacing: 8,
                      runSpacing: 2,
                      children: [
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 7,
                              height: 7,
                              decoration: const BoxDecoration(
                                color: TaiaColors.fieryRose,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 5),
                            Flexible(
                              child: Text(
                                task.type == TaskType.exam
                                    ? '${task.subjectName} · Examen'
                                    : task.subjectName,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  color: TaiaColors.fieryRose,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                            ),
                          ],
                        ),
                        Text(
                          formatDateTimeShort(task.dueAt),
                          style: TextStyle(
                            color: taiaInk.withValues(alpha: 0.55),
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              _StatusChip(task: task),
            ],
          ),
        ),
      ),
    );
  }
}

class _CheckCircle extends StatelessWidget {
  const _CheckCircle({
    required this.completed,
    required this.busy,
    required this.onPressed,
  });

  final bool completed;
  final bool busy;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: completed ? 'Marcar como pendiente' : 'Marcar como completada',
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: busy ? null : onPressed,
        child: SizedBox(
          width: 44,
          height: 44,
          child: Center(
            child: Container(
              width: 30,
              height: 30,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: completed ? TaiaColors.fieryRose : Colors.transparent,
                border: Border.all(color: TaiaColors.fieryRose, width: 1.6),
              ),
              child: busy
                  ? const Padding(
                      padding: EdgeInsets.all(7),
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: TaiaColors.fieryRose,
                      ),
                    )
                  : completed
                  ? const Icon(Icons.check, size: 18, color: Colors.white)
                  : null,
            ),
          ),
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.task});

  final AcademicTask task;

  @override
  Widget build(BuildContext context) {
    final (label, background, foreground) = switch (task.status) {
      TaskStatus.completed => (
        'completada',
        TaiaColors.apricotWhisper,
        taiaInk,
      ),
      TaskStatus.overdue => ('atrasada', TaiaColors.fieryRose, Colors.white),
      TaskStatus.pending =>
        task.isUrgent
            ? ('urgente', TaiaColors.softPeach, TaiaColors.fieryRose)
            : (
                'pendiente',
                TaiaColors.softPeach.withValues(alpha: 0.5),
                taiaInk.withValues(alpha: 0.7),
              ),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: foreground,
          fontSize: 11,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}