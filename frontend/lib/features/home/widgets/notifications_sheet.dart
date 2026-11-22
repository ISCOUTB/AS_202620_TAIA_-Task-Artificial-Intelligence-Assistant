import 'package:flutter/material.dart';

import '../../../core/bogota_time.dart';
import '../../../core/spanish_dates.dart';
import '../../../mascot/mascot_expression.dart';
import '../../../mascot/taia_mascot.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../../reminders/reminder.dart';

/// Hoja inferior de la campanita: lista los recordatorios pendientes.
Future<void> showNotificationsSheet(
  BuildContext context,
  List<Reminder> reminders,
) {
  return showModalBottomSheet<void>(
    context: context,
    backgroundColor: TaiaColors.ivoryMist,
    showDragHandle: true,
    isScrollControlled: true,
    builder: (context) => _NotificationsSheet(reminders: reminders),
  );
}

class _NotificationsSheet extends StatelessWidget {
  const _NotificationsSheet({required this.reminders});

  final List<Reminder> reminders;

  @override
  Widget build(BuildContext context) {
    final now = bogotaNow();
    return SafeArea(
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.sizeOf(context).height * 0.7,
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Recordatorios',
                style: TextStyle(
                  color: taiaInk,
                  fontSize: 22,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 12),
              if (reminders.isEmpty)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.symmetric(vertical: 16),
                    child: Column(
                      children: [
                        SizedBox(
                          width: 150,
                          child: TaiaMascot(
                            motion: 0.6,
                            expression: MascotExpression.happy,
                          ),
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Estás al día. No tienes recordatorios pendientes.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: taiaInk),
                        ),
                      ],
                    ),
                  ),
                )
              else
                Flexible(
                  child: ListView.separated(
                    shrinkWrap: true,
                    itemCount: reminders.length,
                    separatorBuilder: (context, index) =>
                        const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final reminder = reminders[index];
                      return Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.notifications_active_outlined,
                              color: TaiaColors.fieryRose,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    reminder.displayMessage,
                                    style: const TextStyle(
                                      color: taiaInk,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    formatDueLabel(reminder.scheduledAt, now),
                                    style: TextStyle(
                                      color: taiaInk.withValues(alpha: 0.6),
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}