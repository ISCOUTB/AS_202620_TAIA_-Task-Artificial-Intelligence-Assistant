import 'package:flutter/material.dart';

import '../../../core/bogota_time.dart';
import '../../../core/spanish_dates.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../../tasks/task.dart';

/// "Próximas entregas": carrusel horizontal con las tareas pendientes.
class UpcomingDeliveries extends StatelessWidget {
  const UpcomingDeliveries({
    super.key,
    required this.tasks,
    required this.onSeeAll,
  });

  final List<AcademicTask> tasks;
  final VoidCallback onSeeAll;

  @override
  Widget build(BuildContext context) {
    final now = bogotaNow();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Próximas entregas',
                style: TextStyle(
                  color: taiaInk,
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                ),
              ),
              TextButton(
                style: TextButton.styleFrom(foregroundColor: taiaInk),
                onPressed: onSeeAll,
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'Ver todas',
                      style: TextStyle(fontWeight: FontWeight.w700),
                    ),
                    Icon(Icons.chevron_right, size: 18),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        if (tasks.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: _cardDecoration,
              child: Text(
                'No tienes entregas pendientes. ¡Disfruta tu tiempo libre!',
                style: TextStyle(color: taiaInk.withValues(alpha: 0.8)),
              ),
            ),
          )
        else
          SizedBox(
            height: 200,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: tasks.length,
              separatorBuilder: (context, index) => const SizedBox(width: 12),
              itemBuilder: (context, index) =>
                  _DeliveryCard(task: tasks[index], now: now),
            ),
          ),
      ],
    );
  }
}

final BoxDecoration _cardDecoration = BoxDecoration(
  color: const Color(0xFFFFFBF8),
  borderRadius: BorderRadius.circular(22),
  boxShadow: [
    BoxShadow(
      color: taiaInk.withValues(alpha: 0.08),
      blurRadius: 16,
      offset: const Offset(0, 6),
    ),
  ],
);

class _DeliveryCard extends StatelessWidget {
  const _DeliveryCard({required this.task, required this.now});

  final AcademicTask task;
  final DateTime now;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 190,
      decoration: _cardDecoration,
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Franja de acento para las entregas urgentes.
          Container(
            height: 4,
            color: task.isUrgent ? TaiaColors.fieryRose : Colors.transparent,
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 5,
                    ),
                    decoration: BoxDecoration(
                      color: TaiaColors.softPeach,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      task.type == TaskType.exam
                          ? '${task.subjectName} · Examen'
                          : task.subjectName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: taiaInk,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  Expanded(
                    child: Text(
                      task.title,
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: taiaInk,
                        fontSize: 18,
                        height: 1.15,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                  Text(
                    formatDueLabel(task.dueAt, now),
                    style: TextStyle(
                      color: taiaInk.withValues(alpha: 0.6),
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    formatRelative(task.dueAt, now),
                    style: const TextStyle(
                      color: taiaInk,
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}