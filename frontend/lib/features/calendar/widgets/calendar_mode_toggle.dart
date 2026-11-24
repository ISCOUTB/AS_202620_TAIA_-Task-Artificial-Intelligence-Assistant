import 'package:flutter/material.dart';

import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../calendar_logic.dart';

/// Selector "Día | Semana | Mes" (RF-TAR-11).
class CalendarModeToggle extends StatelessWidget {
  const CalendarModeToggle({
    super.key,
    required this.mode,
    required this.onChanged,
  });

  final CalendarMode mode;
  final ValueChanged<CalendarMode> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: TaiaColors.softPeach.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          for (final (value, label) in const [
            (CalendarMode.day, 'Día'),
            (CalendarMode.week, 'Semana'),
            (CalendarMode.month, 'Mes'),
          ])
            _Segment(
              label: label,
              selected: mode == value,
              onTap: () => onChanged(value),
            ),
        ],
      ),
    );
  }
}

class _Segment extends StatelessWidget {
  const _Segment({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      selected: selected,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: selected ? Colors.white : Colors.transparent,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: selected ? TaiaColors.fieryRose : taiaInk,
              fontWeight: FontWeight.w800,
              fontSize: 14,
            ),
          ),
        ),
      ),
    );
  }
}
