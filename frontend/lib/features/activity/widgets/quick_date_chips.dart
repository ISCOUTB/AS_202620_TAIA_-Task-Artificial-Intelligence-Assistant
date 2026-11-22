import 'package:flutter/material.dart';

import '../../../core/bogota_time.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../activity_logic.dart';

/// Atajos "Hoy", "Mañana" y "En 1 semana" para la fecha límite.
class QuickDateChips extends StatelessWidget {
  const QuickDateChips({
    super.key,
    required this.due,
    required this.onChanged,
    this.enabled = true,
  });

  final DateTime due;
  final ValueChanged<DateTime> onChanged;
  final bool enabled;

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
      ],
    );
  }
}