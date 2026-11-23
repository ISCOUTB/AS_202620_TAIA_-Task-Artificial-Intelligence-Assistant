import 'package:flutter/material.dart';

import '../../../core/bogota_time.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../activity_logic.dart';

/// Atajos "Hoy", "Mañana", "El viernes" y "En 1 semana" para la fecha límite,
/// más "Otro día…" si se pasa [onOther] (RNF-14).
class QuickDateChips extends StatelessWidget {
  const QuickDateChips({
    super.key,
    required this.due,
    required this.onChanged,
    this.enabled = true,
    this.onOther,
  });

  final DateTime due;
  final ValueChanged<DateTime> onChanged;
  final bool enabled;
  final VoidCallback? onOther;

  @override
  Widget build(BuildContext context) {
    final options = quickDates(bogotaNow());
    return Wrap(
      spacing: 8,
      runSpacing: 4,
      children: [
        for (final option in options)
          ChoiceChip(
            label: Text(option.label),
            selected: sameDay(due, option.date),
            onSelected: enabled
                ? (_) => onChanged(withDate(due, option.date))
                : null,
            showCheckmark: false,
            shape: const StadiumBorder(),
            side: BorderSide.none,
            selectedColor: TaiaColors.fieryRose,
            backgroundColor: TaiaColors.softPeach.withValues(alpha: 0.6),
            labelStyle: TextStyle(
              color: sameDay(due, option.date) ? Colors.white : taiaInk,
              fontWeight: FontWeight.w800,
            ),
          ),
        if (onOther != null)
          ActionChip(
            avatar: const Icon(
              Icons.calendar_today_outlined,
              size: 16,
              color: taiaInk,
            ),
            label: const Text('Otro día…'),
            onPressed: enabled ? onOther : null,
            shape: const StadiumBorder(),
            side: BorderSide.none,
            backgroundColor: TaiaColors.softPeach.withValues(alpha: 0.6),
            labelStyle: const TextStyle(
              color: taiaInk,
              fontWeight: FontWeight.w800,
            ),
          ),
      ],
    );
  }
}
