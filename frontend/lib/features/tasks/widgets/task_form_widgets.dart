import 'package:flutter/material.dart';

import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';

/// Estilo de los campos de los formularios de tareas: fondo blanco y borde
/// durazno, que se vuelve rosa al enfocar.
InputDecoration taskFieldDecoration({Widget? suffix, String? hint}) {
  OutlineInputBorder border(Color color, [double width = 1.5]) =>
      OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: color, width: width),
      );
  return InputDecoration(
    filled: true,
    fillColor: Colors.white,
    hintText: hint,
    hintStyle: TextStyle(color: taiaInk.withValues(alpha: 0.4)),
    suffixIcon: suffix,
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
    border: border(TaiaColors.softPeach),
    enabledBorder: border(TaiaColors.softPeach),
    focusedBorder: border(TaiaColors.fieryRose, 2),
    errorBorder: border(Colors.red.shade400),
    focusedErrorBorder: border(Colors.red.shade400, 2),
  );
}

const TextStyle taskValueStyle = TextStyle(
  color: taiaInk,
  fontWeight: FontWeight.w700,
  fontSize: 15,
);

/// Etiqueta sobre cada campo.
class FormLabel extends StatelessWidget {
  const FormLabel(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        text,
        style: const TextStyle(
          color: taiaInk,
          fontSize: 14,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

/// Selector de una opción entre pocas, con el estilo de la marca.
class TaskSegments<T> extends StatelessWidget {
  const TaskSegments({
    super.key,
    required this.value,
    required this.options,
    required this.onChanged,
    this.enabled = true,
  });

  final T value;
  final Map<T, String> options;
  final ValueChanged<T> onChanged;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return SegmentedButton<T>(
      showSelectedIcon: false,
      expandedInsets: EdgeInsets.zero,
      segments: [
        for (final entry in options.entries)
          ButtonSegment<T>(value: entry.key, label: Text(entry.value)),
      ],
      selected: {value},
      onSelectionChanged: enabled ? (s) => onChanged(s.first) : null,
      style: SegmentedButton.styleFrom(
        backgroundColor: Colors.white,
        foregroundColor: taiaInk,
        selectedBackgroundColor: TaiaColors.fieryRose,
        selectedForegroundColor: Colors.white,
        side: const BorderSide(color: TaiaColors.softPeach, width: 1.5),
      ),
    );
  }
}