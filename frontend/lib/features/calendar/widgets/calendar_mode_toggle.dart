import 'package:flutter/material.dart';

import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../calendar_logic.dart';

/// Selector "Mes | Semana".
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
          _Segment(
            label: 'Mes',
            selected: mode == CalendarMode.month,
            onTap: () => onChanged(CalendarMode.month),
          ),
          _Segment(
            label: 'Semana',
            selected: mode == CalendarMode.week,
            onTap: () => onChanged(CalendarMode.week),
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