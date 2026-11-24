import 'package:flutter/material.dart';

import '../../../core/api_error.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../../tasks/subject.dart';
import '../../tasks/widgets/task_form_widgets.dart';
import '../schedule_block.dart';
import '../schedule_service.dart';

/// Colores de las asignaturas en la vista semanal, por orden de la lista.
const subjectPalette = [
  Color(0xFFF26A6C),
  Color(0xFF6FA8DC),
  Color(0xFF7BBF7A),
  Color(0xFFF2B35B),
  Color(0xFFB48EDB),
  Color(0xFF4FBDB8),
  Color(0xFFEC8366),
  Color(0xFF8E9BD8),
];

Color subjectColor(List<Subject> subjects, String subjectId) {
  final index = subjects.indexWhere((s) => s.id == subjectId);
  return subjectPalette[(index < 0 ? 0 : index) % subjectPalette.length];
}

/// Atajos de días que se repiten en muchos horarios. Tocar uno agrega sus
/// días a los ya marcados; si ya estaban todos, los quita.
const _dayPresets = {
  'Lun y Mié': {Weekday.monday, Weekday.wednesday},
  'Mar y Jue': {Weekday.tuesday, Weekday.thursday},
  'Lun a Vie': {
    Weekday.monday,
    Weekday.tuesday,
    Weekday.wednesday,
    Weekday.thursday,
    Weekday.friday,
  },
};

String _short(Weekday day) => switch (day) {
  Weekday.monday => 'L',
  Weekday.tuesday => 'M',
  Weekday.wednesday => 'X',
  Weekday.thursday => 'J',
  Weekday.friday => 'V',
  Weekday.saturday => 'S',
  Weekday.sunday => 'D',
};

/// Resultado de agregar una clase en varios días.
class ClassComposerResult {
  const ClassComposerResult({required this.created, required this.failed});

  /// Cuántos bloques se crearon (uno por día).
  final int created;

  /// Días que no se pudieron agregar, con el motivo del servidor.
  final Map<Weekday, String> failed;
}

/// Hoja para agregar una clase en uno o varios días a la vez (RF-ASG-06).
/// Crea un bloque por día; si un día choca con otra clase, los demás se
/// agregan igual y se informa cuál falló.
Future<ClassComposerResult?> showClassComposer(
  BuildContext context, {
  required ScheduleService service,
  required List<Subject> subjects,
}) {
  return showModalBottomSheet<ClassComposerResult>(
    context: context,
    isScrollControlled: true,
    backgroundColor: TaiaColors.ivoryMist,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (context) =>
        _ClassComposerSheet(service: service, subjects: subjects),
  );
}

/// Mensaje corto con lo que pasó al agregar la clase.
String describeComposerResult(ClassComposerResult result) {
  final failed = result.failed.keys.map((d) => d.label.toLowerCase()).toList();
  if (failed.isEmpty) {
    return result.created == 1
        ? 'Clase agregada'
        : 'Clase agregada en ${result.created} días';
  }
  final reason = result.failed.values.first;
  return 'Se agregó en ${result.created} día(s). No se pudo el '
      '${failed.join(', ')}: $reason';
}

class _ClassComposerSheet extends StatefulWidget {
  const _ClassComposerSheet({required this.service, required this.subjects});

  final ScheduleService service;
  final List<Subject> subjects;

  @override
  State<_ClassComposerSheet> createState() => _ClassComposerSheetState();
}

class _ClassComposerSheetState extends State<_ClassComposerSheet> {
  late String? _subjectId = widget.subjects.isEmpty
      ? null
      : widget.subjects.first.id;
  final Set<Weekday> _days = {};
  // Sin hora por defecto: cada clase empieza y termina cuando el estudiante
  // diga, a cualquier hora y minuto (RF-ASG-06).
  TimeOfDay? _start;
  TimeOfDay? _end;
  final _room = TextEditingController();
  bool _saving = false;
  String? _error;

  @override
  void dispose() {
    _room.dispose();
    super.dispose();
  }

  String? get _timeError {
    final start = _start, end = _end;
    return start == null || end == null ? null : blockTimeError(start, end);
  }

  bool get _ready =>
      _subjectId != null &&
      _days.isNotEmpty &&
      _start != null &&
      _end != null &&
      _timeError == null;

  /// El reloj abre en la hora ya elegida; el fin, si falta, dos horas después
  /// del inicio. Es solo el punto de partida del reloj, no un valor guardado.
  Future<void> _pick({required bool start}) async {
    final from = _start;
    final initial = start
        ? from ?? const TimeOfDay(hour: 7, minute: 0)
        : _end ??
              (from == null
                  ? const TimeOfDay(hour: 9, minute: 0)
                  : TimeOfDay(hour: (from.hour + 2) % 24, minute: from.minute));
    final picked = await showTimePicker(
      context: context,
      initialTime: initial,
      helpText: start ? '¿A qué hora empieza?' : '¿A qué hora termina?',
    );
    if (picked == null || !mounted) return;
    setState(() => start ? _start = picked : _end = picked);
  }

  /// Agrega los días del atajo, o los quita si ya estaban todos.
  void _togglePreset(Set<Weekday> preset) => setState(() {
    if (_days.containsAll(preset)) {
      _days.removeAll(preset);
    } else {
      _days.addAll(preset);
    }
  });

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    var created = 0;
    final failed = <Weekday, String>{};
    final ordered = Weekday.values.where(_days.contains);
    for (final day in ordered) {
      try {
        await widget.service.create(
          subjectId: _subjectId!,
          weekday: day,
          start: _start!,
          end: _end!,
          room: _room.text.trim(),
        );
        created++;
      } on ApiException catch (e) {
        failed[day] = e.message;
      }
    }
    if (!mounted) return;
    if (created == 0) {
      setState(() {
        _saving = false;
        _error = failed.values.first;
      });
      return;
    }
    Navigator.of(context)
        .pop(ClassComposerResult(created: created, failed: failed));
  }

  @override
  Widget build(BuildContext context) {
    final subject = widget.subjects
        .where((s) => s.id == _subjectId)
        .firstOrNull;
    final color = subject == null
        ? TaiaColors.fieryRose
        : subjectColor(widget.subjects, subject.id);
    final days = Weekday.values.where(_days.contains).toList();
    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 12,
        bottom: MediaQuery.viewInsetsOf(context).bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: TaiaColors.softPeach,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'Nueva clase',
              style: TextStyle(
                color: taiaInk,
                fontSize: 22,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 16),
            const FormLabel('¿Qué materia?'),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final s in widget.subjects)
                  ChoiceChip(
                    avatar: CircleAvatar(
                      backgroundColor: subjectColor(widget.subjects, s.id),
                      radius: 6,
                    ),
                    label: Text(s.name),
                    selected: s.id == _subjectId,
                    showCheckmark: false,
                    selectedColor: TaiaColors.softPeach,
                    onSelected: (_) => setState(() => _subjectId = s.id),
                  ),
              ],
            ),
            const SizedBox(height: 18),
            const FormLabel('¿Qué días? Toca todos los que tengas'),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                for (final day in Weekday.values)
                  _DayToggle(
                    letter: _short(day),
                    tooltip: day.label,
                    selected: _days.contains(day),
                    color: color,
                    onTap: () => setState(
                      () => _days.contains(day)
                          ? _days.remove(day)
                          : _days.add(day),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final preset in _dayPresets.entries)
                  FilterChip(
                    label: Text(preset.key),
                    selected: _days.containsAll(preset.value),
                    showCheckmark: false,
                    selectedColor: color.withValues(alpha: 0.25),
                    onSelected: (_) => _togglePreset(preset.value),
                  ),
              ],
            ),
            const SizedBox(height: 18),
            const FormLabel('¿A qué hora?'),
            Row(
              children: [
                Expanded(
                  child: _TimeField(
                    label: 'Desde',
                    time: _start,
                    onTap: () => _pick(start: true),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _TimeField(
                    label: 'Hasta',
                    time: _end,
                    onTap: () => _pick(start: false),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _room,
              style: taskValueStyle,
              decoration: taskFieldDecoration(hint: 'Aula (opcional)'),
            ),
            const SizedBox(height: 16),
            AnimatedContainer(
              duration: const Duration(milliseconds: 250),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: color.withValues(alpha: 0.6)),
              ),
              child: Text(
                subject == null
                    ? 'Primero agrega una asignatura.'
                    : days.isEmpty
                    ? '${subject.name}: elige los días.'
                    : _start == null || _end == null
                    ? '${subject.name} · '
                          '${days.map((d) => d.label).join(', ')}: '
                          'elige la hora.'
                    : '${subject.name} · '
                          '${days.map((d) => d.label).join(', ')} · '
                          '${formatBlockTime(_start!)} – '
                          '${formatBlockTime(_end!)}',
                style: const TextStyle(
                  color: taiaInk,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            if (_timeError != null) ...[
              const SizedBox(height: 8),
              AuthErrorText(_timeError!),
            ],
            if (_error != null) ...[
              const SizedBox(height: 8),
              AuthErrorText(_error!),
            ],
            const SizedBox(height: 12),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: TaiaColors.fieryRose,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              onPressed: _ready && !_saving ? _save : null,
              child: _saving
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : Text(
                      days.length > 1
                          ? 'Agregar en ${days.length} días'
                          : 'Agregar clase',
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Campo de hora: muestra la hora elegida o "Elegir" y abre el reloj.
class _TimeField extends StatelessWidget {
  const _TimeField({
    required this.label,
    required this.time,
    required this.onTap,
  });

  final String label;
  final TimeOfDay? time;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final value = time;
    return Semantics(
      button: true,
      label: '$label: ${value == null ? 'sin elegir' : formatBlockTime(value)}',
      excludeSemantics: true,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: InputDecorator(
          decoration: taskFieldDecoration(
            suffix: const Icon(Icons.schedule, color: TaiaColors.fieryRose),
          ).copyWith(labelText: label),
          child: Text(
            value == null ? 'Elegir' : formatBlockTime(value),
            style: value == null
                ? taskValueStyle.copyWith(color: taiaInk.withValues(alpha: 0.4))
                : taskValueStyle,
          ),
        ),
      ),
    );
  }
}

class _DayToggle extends StatelessWidget {
  const _DayToggle({
    required this.letter,
    required this.tooltip,
    required this.selected,
    required this.color,
    required this.onTap,
  });

  final String letter;
  final String tooltip;
  final bool selected;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: InkResponse(
        onTap: onTap,
        radius: 24,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOutBack,
          width: 40,
          height: 40,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: selected ? color : Colors.white,
            border: Border.all(
              color: selected ? color : TaiaColors.softPeach,
              width: 1.5,
            ),
          ),
          child: Text(
            letter,
            style: TextStyle(
              color: selected ? Colors.white : taiaInk,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
      ),
    );
  }
}

/// Vista semanal del horario: columnas de lunes a domingo y un bloque de color
/// por clase. Tocar un bloque llama a [onTapBlock].
class WeekScheduleView extends StatelessWidget {
  const WeekScheduleView({
    super.key,
    required this.blocks,
    required this.subjects,
    this.onTapBlock,
  });

  final List<ScheduleBlock> blocks;
  final List<Subject> subjects;
  final ValueChanged<ScheduleBlock>? onTapBlock;

  static const _hourHeight = 30.0;

  @override
  Widget build(BuildContext context) {
    int minutes(TimeOfDay t) => t.hour * 60 + t.minute;
    var first = 7, last = 18;
    for (final b in blocks) {
      first = first < b.start.hour ? first : b.start.hour;
      final endHour = (minutes(b.end) + 59) ~/ 60;
      last = last > endHour ? last : endHour;
    }
    final height = (last - first) * _hourHeight;
    return Container(
      padding: const EdgeInsets.fromLTRB(4, 8, 8, 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: TaiaColors.softPeach),
      ),
      child: Column(
        children: [
          Row(
            children: [
              const SizedBox(width: 30),
              for (final day in Weekday.values)
                Expanded(
                  child: Center(
                    child: Text(
                      _short(day),
                      style: const TextStyle(
                        color: taiaInk,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 6),
          SizedBox(
            height: height,
            child: LayoutBuilder(
              builder: (context, constraints) {
                final column = (constraints.maxWidth - 30) / 7;
                return Stack(
                  children: [
                    for (var h = first; h < last; h++)
                      Positioned(
                        top: (h - first) * _hourHeight,
                        left: 0,
                        right: 0,
                        child: Row(
                          children: [
                            SizedBox(
                              width: 30,
                              child: Text(
                                '$h',
                                style: TextStyle(
                                  color: taiaInk.withValues(alpha: 0.45),
                                  fontSize: 10,
                                ),
                              ),
                            ),
                            Expanded(
                              child: Container(
                                height: 1,
                                color: TaiaColors.softPeach.withValues(
                                  alpha: 0.5,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    for (final b in blocks)
                      Positioned(
                        left:
                            30 + Weekday.values.indexOf(b.weekday) * column + 1,
                        width: column - 2,
                        top: (minutes(b.start) - first * 60) / 60 * _hourHeight,
                        height:
                            (minutes(b.end) - minutes(b.start)) /
                            60 *
                            _hourHeight,
                        child: Tooltip(
                          message:
                              '${b.subjectName} · ${b.weekday.label} '
                              '${formatBlockTime(b.start)} – '
                              '${formatBlockTime(b.end)}',
                          child: GestureDetector(
                            onTap: onTapBlock == null
                                ? null
                                : () => onTapBlock!(b),
                            child: TweenAnimationBuilder<double>(
                              tween: Tween(begin: 0, end: 1),
                              duration: const Duration(milliseconds: 350),
                              curve: Curves.easeOutBack,
                              builder: (context, t, child) =>
                                  Transform.scale(scale: t, child: child),
                              child: Container(
                                padding: const EdgeInsets.all(3),
                                decoration: BoxDecoration(
                                  color: subjectColor(subjects, b.subjectId),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  b.subjectName,
                                  maxLines: 3,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 9,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    if (blocks.isEmpty)
                      Center(
                        child: Text(
                          'Aquí aparecerán tus clases',
                          style: TextStyle(
                            color: taiaInk.withValues(alpha: 0.5),
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
