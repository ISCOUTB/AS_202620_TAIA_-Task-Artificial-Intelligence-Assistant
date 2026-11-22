import 'package:flutter/material.dart';

import '../../../core/bogota_time.dart';
import '../../../core/spanish_dates.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../../reminders/reminder_option.dart';
import '../../reminders/reminder_rules.dart';
import '../../tasks/widgets/task_form_widgets.dart';

/// Elige si la actividad nueva tendrá recordatorios y cuándo (RF-TAR-02):
/// la política por defecto (preseleccionada), fechas propias o ninguno.
class ReminderOptionField extends StatelessWidget {
  const ReminderOptionField({
    super.key,
    required this.mode,
    required this.customAt,
    required this.due,
    required this.onModeChanged,
    required this.onCustomChanged,
    this.enabled = true,
  });

  final ReminderMode mode;
  final List<DateTime> customAt;

  /// Fecha límite de la actividad: los recordatorios van antes (RF-REC-01).
  final DateTime due;
  final ValueChanged<ReminderMode> onModeChanged;
  final ValueChanged<List<DateTime>> onCustomChanged;
  final bool enabled;

  Future<void> _add(BuildContext context) async {
    final messenger = ScaffoldMessenger.of(context);
    final suggested = suggestedReminderTime(bogotaNow());
    final date = await showDatePicker(
      context: context,
      initialDate: suggested,
      firstDate: DateTime(suggested.year, suggested.month, suggested.day),
      lastDate: DateTime(due.year, due.month, due.day),
    );
    if (date == null || !context.mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(suggested),
    );
    if (time == null) return;
    final at = DateTime(
      date.year,
      date.month,
      date.day,
      time.hour,
      time.minute,
    );
    final error = reminderTimeError(at, due: due, now: bogotaNow());
    if (error != null) {
      messenger
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(error)));
      return;
    }
    onCustomChanged([...customAt, at]..sort());
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TaskSegments<ReminderMode>(
          value: mode,
          enabled: enabled,
          options: const {
            ReminderMode.defaults: 'Por defecto',
            ReminderMode.custom: 'Elegir fechas',
            ReminderMode.none: 'Ninguno',
          },
          onChanged: onModeChanged,
        ),
        const SizedBox(height: 6),
        Text(
          switch (mode) {
            ReminderMode.defaults =>
              'Te aviso la tarde anterior y cada 2 días antes de la fecha '
                  'límite, a las 6:00 p. m.',
            ReminderMode.custom =>
              'Hasta $maxCustomReminders fechas, futuras y antes de la fecha '
                  'límite.',
            ReminderMode.none => 'Esta actividad no tendrá recordatorios.',
          },
          style: TextStyle(
            color: taiaInk.withValues(alpha: 0.65),
            fontSize: 12,
          ),
        ),
        if (mode == ReminderMode.custom) ...[
          const SizedBox(height: 8),
          for (final at in customAt)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Container(
                padding: const EdgeInsets.fromLTRB(14, 4, 4, 4),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.notifications_active_outlined,
                      color: TaiaColors.fieryRose,
                      size: 20,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        formatDateTimeShort(at),
                        style: taskValueStyle,
                      ),
                    ),
                    IconButton(
                      tooltip: 'Quitar fecha',
                      onPressed: enabled
                          ? () => onCustomChanged(
                              customAt.where((d) => d != at).toList(),
                            )
                          : null,
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
              ),
            ),
          if (customAt.length < maxCustomReminders)
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                style: TextButton.styleFrom(
                  foregroundColor: TaiaColors.fieryRose,
                ),
                onPressed: enabled ? () => _add(context) : null,
                icon: const Icon(Icons.add_alarm_outlined),
                label: const Text('Agregar fecha'),
              ),
            ),
        ],
      ],
    );
  }
}
