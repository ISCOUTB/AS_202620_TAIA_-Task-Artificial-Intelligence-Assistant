import 'package:flutter/material.dart';

import '../../../core/spanish_dates.dart';
import '../../../mascot/mascot_expression.dart';
import '../../../mascot/taia_mascot.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../../tasks/task.dart';

/// Pantalla de "¡Actividad creada!" con la mascota celebrando.
class ActivitySuccess extends StatelessWidget {
  const ActivitySuccess({
    super.key,
    required this.task,
    required this.onAddAnother,
    required this.onSeeTasks,
  });

  final AcademicTask task;
  final VoidCallback onAddAnother;
  final VoidCallback? onSeeTasks;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 20),
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
          Container(
            width: 160,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: TaiaColors.fieryRose,
              borderRadius: BorderRadius.circular(32),
            ),
            child: const TaiaMascot(
              motion: 0.8,
              expression: MascotExpression.excited,
            ),
          ),
          const SizedBox(height: 18),
          const Text(
            '¡Actividad creada!',
            style: TextStyle(
              color: taiaInk,
              fontSize: 24,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '«${task.title}» quedó guardada para el '
            '${formatDateTimeShort(task.dueAt)}.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: taiaInk.withValues(alpha: 0.75),
              fontSize: 15,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            task.subjectName,
            style: const TextStyle(
              color: TaiaColors.fieryRose,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 22),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              style: FilledButton.styleFrom(
                backgroundColor: TaiaColors.fieryRose,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              onPressed: onAddAnother,
              icon: const Icon(Icons.add),
              label: const Text(
                'Añadir otra',
                style: TextStyle(fontWeight: FontWeight.w700),
              ),
            ),
          ),
          if (onSeeTasks != null) ...[
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                style: OutlinedButton.styleFrom(
                  foregroundColor: TaiaColors.fieryRose,
                  side: const BorderSide(
                    color: TaiaColors.fieryRose,
                    width: 1.5,
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                onPressed: onSeeTasks,
                child: const Text(
                  'Ver mis tareas',
                  style: TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}