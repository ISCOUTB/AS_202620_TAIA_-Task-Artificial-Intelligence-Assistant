import 'package:flutter/material.dart';

import '../../../mascot/mascot_expression.dart';
import '../../../mascot/taia_mascot.dart';
import '../../auth/auth_shell.dart';
import '../home_data.dart';
import 'progress_ring.dart';

/// Tarjeta principal: cuántas tareas hay hoy, el progreso y la mascota, que
/// cambia de expresión según cómo vaya el día.
class TodayCard extends StatelessWidget {
  const TodayCard({super.key, required this.data});

  final HomeData data;

  @override
  Widget build(BuildContext context) {
    final state = data.dayState;
    final (label, title, subtitle, expression) = switch (state) {
      DayState.free => (
        'Día libre',
        'Hoy no tienes entregas',
        'Puedes relajarte y descansar.',
        MascotExpression.happy,
      ),
      DayState.done => (
        '¡Buen trabajo!',
        'Todo listo por hoy',
        'Te ganaste un respiro.',
        MascotExpression.excited,
      ),
      DayState.pending => (
        'Tu día, bajo control',
        data.todayPending == 1
            ? 'Hoy tienes 1 tarea'
            : 'Hoy tienes ${data.todayPending} tareas',
        'Un paso a la vez. Tú puedes.',
        MascotExpression.organizing,
      ),
    };

    return Container(
      padding: const EdgeInsets.fromLTRB(20, 20, 16, 12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFEC8366), Color(0xFFF7A07F)],
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFFEC8366).withValues(alpha: 0.35),
            blurRadius: 24,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: const TextStyle(
                      color: taiaInk,
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    title,
                    style: const TextStyle(
                      color: taiaInk,
                      fontSize: 30,
                      height: 1.1,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    subtitle,
                    style: TextStyle(
                      color: taiaInk.withValues(alpha: 0.8),
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 8),
                ],
              ),
            ),
            const SizedBox(width: 8),
            SizedBox(
              width: 112,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  if (state == DayState.free)
                    const SizedBox(height: 8)
                  else
                    ProgressRing(done: data.todayDone, total: data.todayTotal),
                  const SizedBox(height: 8),
                  TaiaMascot(motion: 0.6, expression: expression),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}