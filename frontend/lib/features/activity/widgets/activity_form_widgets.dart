import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../mascot/mascot_expression.dart';
import '../../../mascot/taia_mascot.dart';
import '../../../theme/taia_colors.dart';
import '../../academic/widgets/class_composer.dart' show subjectPalette;
import '../../auth/auth_shell.dart';
import '../../tasks/subject.dart';
import '../../tasks/task.dart';
import '../activity_logic.dart';

/// Chip de selección con el estilo de TAIA y una vibración corta (RNF-14).
class TaiaChoiceChip extends StatelessWidget {
  const TaiaChoiceChip({
    super.key,
    required this.label,
    required this.selected,
    required this.onSelected,
    this.color = TaiaColors.fieryRose,
    this.avatar,
  });

  final String label;
  final bool selected;
  final VoidCallback? onSelected;
  final Color color;
  final Widget? avatar;

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Text(label),
      avatar: avatar,
      selected: selected,
      onSelected: onSelected == null
          ? null
          : (_) {
              HapticFeedback.selectionClick();
              onSelected!();
            },
      showCheckmark: false,
      shape: const StadiumBorder(),
      side: BorderSide.none,
      selectedColor: color,
      backgroundColor: TaiaColors.softPeach.withValues(alpha: 0.6),
      labelStyle: TextStyle(
        color: selected ? Colors.white : taiaInk,
        fontWeight: FontWeight.w800,
      ),
    );
  }
}

/// Tarea o examen, en dos tarjetas grandes (RNF-14).
class ActivityTypeCards extends StatelessWidget {
  const ActivityTypeCards({
    super.key,
    required this.value,
    required this.onChanged,
    this.enabled = true,
  });

  final TaskType value;
  final ValueChanged<TaskType> onChanged;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    Widget card(TaskType type, IconData icon, String label) {
      final selected = value == type;
      return Expanded(
        child: Semantics(
          selected: selected,
          button: true,
          label: label,
          child: GestureDetector(
            onTap: enabled
                ? () {
                    HapticFeedback.selectionClick();
                    onChanged(type);
                  }
                : null,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              curve: Curves.easeOut,
              padding: const EdgeInsets.symmetric(vertical: 14),
              decoration: BoxDecoration(
                color: selected ? TaiaColors.fieryRose : Colors.white,
                borderRadius: BorderRadius.circular(18),
                boxShadow: selected
                    ? const [
                        BoxShadow(
                          color: Color(0x33F26A6C),
                          blurRadius: 12,
                          offset: Offset(0, 4),
                        ),
                      ]
                    : null,
              ),
              child: Column(
                children: [
                  Icon(icon, color: selected ? Colors.white : taiaInk),
                  const SizedBox(height: 4),
                  Text(
                    label,
                    style: TextStyle(
                      color: selected ? Colors.white : taiaInk,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    }

    return Row(
      children: [
        card(TaskType.task, Icons.assignment_outlined, 'Tarea'),
        const SizedBox(width: 12),
        card(TaskType.exam, Icons.school_outlined, 'Examen'),
      ],
    );
  }
}

/// Las materias como chips de color, más "Nueva" (RNF-14). Un toque elige.
class SubjectChips extends StatelessWidget {
  const SubjectChips({
    super.key,
    required this.subjects,
    required this.selectedId,
    required this.onSelected,
    required this.onNew,
    this.enabled = true,
  });

  final List<Subject> subjects;
  final String? selectedId;
  final ValueChanged<String> onSelected;
  final VoidCallback onNew;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 6,
      children: [
        for (final (index, subject) in subjects.indexed)
          TaiaChoiceChip(
            label: subject.name,
            selected: subject.id == selectedId,
            color: subjectPalette[index % subjectPalette.length],
            avatar: CircleAvatar(
              radius: 5,
              backgroundColor: subject.id == selectedId
                  ? Colors.white
                  : subjectPalette[index % subjectPalette.length],
            ),
            onSelected: enabled ? () => onSelected(subject.id) : null,
          ),
        ActionChip(
          avatar: const Icon(Icons.add, size: 18, color: TaiaColors.fieryRose),
          label: const Text('Nueva'),
          onPressed: enabled ? onNew : null,
          shape: const StadiumBorder(
            side: BorderSide(color: TaiaColors.fieryRose),
          ),
          backgroundColor: Colors.white,
          labelStyle: const TextStyle(
            color: TaiaColors.fieryRose,
            fontWeight: FontWeight.w800,
          ),
        ),
      ],
    );
  }
}

/// Atajos de hora: "8:00 a. m.", "12:00 m.", "6:00 p. m.", "11:59 p. m." y
/// "Otra hora…" (RNF-14).
class QuickTimeChips extends StatelessWidget {
  const QuickTimeChips({
    super.key,
    required this.due,
    required this.onChanged,
    required this.onOther,
    this.enabled = true,
  });

  final DateTime due;
  final ValueChanged<DateTime> onChanged;
  final VoidCallback onOther;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    final isQuick = quickTimes.any(
      (t) => t.hour == due.hour && t.minute == due.minute,
    );
    return Wrap(
      spacing: 8,
      runSpacing: 4,
      children: [
        for (final time in quickTimes)
          TaiaChoiceChip(
            label: time.label,
            selected: due.hour == time.hour && due.minute == time.minute,
            onSelected: enabled
                ? () => onChanged(withTime(due, time.hour, time.minute))
                : null,
          ),
        TaiaChoiceChip(
          label: 'Otra hora…',
          selected: !isQuick,
          onSelected: enabled ? onOther : null,
        ),
      ],
    );
  }
}

/// TAIA cuenta lo que va a crear, y se actualiza mientras se llena el
/// formulario (RNF-14).
class ActivitySummaryCard extends StatelessWidget {
  const ActivitySummaryCard({
    super.key,
    required this.text,
    required this.expression,
  });

  final String text;
  final MascotExpression expression;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: TaiaColors.softPeach, width: 1.5),
      ),
      child: Row(
        children: [
          SizedBox.square(
            dimension: 52,
            child: TaiaMascot(motion: 0.5, expression: expression),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 200),
              child: Text(
                text,
                key: ValueKey(text),
                style: const TextStyle(
                  color: taiaInk,
                  fontSize: 14,
                  height: 1.35,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
