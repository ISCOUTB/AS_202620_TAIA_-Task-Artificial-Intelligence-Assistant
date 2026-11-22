import 'package:flutter/material.dart';

import '../../../theme/taia_colors.dart';
import '../../auth/auth_service.dart';
import '../../auth/auth_shell.dart';
import '../../tasks/subject.dart';
import '../../tasks/widgets/task_form_widgets.dart';
import '../schedule_block.dart';
import '../schedule_service.dart';
import '../../shell/page_header.dart';

/// Diálogo para crear (RF-ASG-06) o editar y eliminar (RF-ASG-07) un bloque
/// del horario. [subjects] son las asignaturas activas. Devuelve true si algo
/// cambió.
Future<bool> showScheduleBlockDialog(
  BuildContext context, {
  required ScheduleService service,
  required List<Subject> subjects,
  ScheduleBlock? block,
}) async {
  final changed = await showDialog<bool>(
    context: context,
    builder: (context) =>
        _BlockDialog(service: service, subjects: subjects, block: block),
  );
  return changed ?? false;
}

/// Diálogo para fijar el período académico (RF-ASG-08). Devuelve el período
/// guardado, o null si se cancela.
Future<AcademicPeriod?> showPeriodDialog(
  BuildContext context, {
  required ScheduleService service,
  required DateTime today,
  AcademicPeriod? current,
}) {
  return showDialog<AcademicPeriod>(
    context: context,
    builder: (context) =>
        _PeriodDialog(service: service, today: today, current: current),
  );
}

/// Campo que muestra un valor y abre un selector al tocarlo.
class _PickerField extends StatelessWidget {
  const _PickerField({
    required this.value,
    required this.icon,
    required this.onTap,
  });

  final String value;
  final IconData icon;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: onTap,
      child: InputDecorator(
        decoration: taskFieldDecoration(
          suffix: Icon(icon, size: 20, color: taiaInk),
        ),
        child: Text(value, style: taskValueStyle),
      ),
    );
  }
}

Widget _dialogTitle(String text) => Text(
  text,
  style: const TextStyle(color: taiaInk, fontWeight: FontWeight.w900),
);

Widget _saveButton({required bool busy, required VoidCallback onPressed}) {
  return FilledButton(
    style: FilledButton.styleFrom(backgroundColor: TaiaColors.fieryRose),
    onPressed: busy ? null : onPressed,
    child: busy
        ? const SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: Colors.white,
            ),
          )
        : const Text('Guardar'),
  );
}

class _BlockDialog extends StatefulWidget {
  const _BlockDialog({
    required this.service,
    required this.subjects,
    required this.block,
  });

  final ScheduleService service;
  final List<Subject> subjects;
  final ScheduleBlock? block;

  @override
  State<_BlockDialog> createState() => _BlockDialogState();
}

class _BlockDialogState extends State<_BlockDialog> {
  late String? _subjectId =
      widget.block?.subjectId ??
      (widget.subjects.isEmpty ? null : widget.subjects.first.id);
  late Weekday _weekday = widget.block?.weekday ?? Weekday.monday;
  late TimeOfDay _start =
      widget.block?.start ?? const TimeOfDay(hour: 8, minute: 0);
  late TimeOfDay _end =
      widget.block?.end ?? const TimeOfDay(hour: 10, minute: 0);
  late final TextEditingController _room = TextEditingController(
    text: widget.block?.room ?? '',
  );
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _room.dispose();
    super.dispose();
  }

  /// Las asignaturas activas; la del bloque se agrega si ya no está.
  List<Subject> get _options {
    final block = widget.block;
    final options = [...widget.subjects];
    if (block != null && !options.any((s) => s.id == block.subjectId)) {
      options.insert(0, Subject(id: block.subjectId, name: block.subjectName));
    }
    return options;
  }

  Future<void> _pick({required bool start}) async {
    final picked = await showTimePicker(
      context: context,
      initialTime: start ? _start : _end,
    );
    if (picked == null || !mounted) return;
    setState(() => start ? _start = picked : _end = picked);
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await action();
      if (mounted) Navigator.of(context).pop(true);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _submit() async {
    final subjectId = _subjectId;
    if (subjectId == null) {
      setState(() => _error = 'Primero crea una asignatura.');
      return;
    }
    final timeError = blockTimeError(_start, _end);
    if (timeError != null) {
      setState(() => _error = timeError);
      return;
    }
    final block = widget.block;
    final room = _room.text.trim();
    await _run(
      () => block == null
          ? widget.service.create(
              subjectId: subjectId,
              weekday: _weekday,
              start: _start,
              end: _end,
              room: room,
            )
          : widget.service.update(
              block.id,
              subjectId: subjectId,
              weekday: _weekday,
              start: _start,
              end: _end,
              room: room,
            ),
    );
  }

  Future<void> _delete(ScheduleBlock block) async {
    final confirmed = await confirmAction(
      context,
      title: '¿Eliminar este bloque?',
      message:
          'Se quitará ${block.subjectName} del ${block.weekday.label.toLowerCase()} '
          'a las ${formatBlockTime(block.start)}.',
      confirmLabel: 'Eliminar',
    );
    if (!confirmed || !mounted) return;
    await _run(() => widget.service.delete(block.id));
  }

  @override
  Widget build(BuildContext context) {
    final block = widget.block;
    return AlertDialog(
      backgroundColor: TaiaColors.ivoryMist,
      title: _dialogTitle(block == null ? 'Nuevo bloque' : 'Editar bloque'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const FormLabel('Materia'),
            DropdownButtonFormField<String>(
              initialValue: _subjectId,
              isExpanded: true,
              style: taskValueStyle,
              decoration: taskFieldDecoration(),
              items: [
                for (final subject in _options)
                  DropdownMenuItem(
                    value: subject.id,
                    child: Text(subject.name, overflow: TextOverflow.ellipsis),
                  ),
              ],
              onChanged: _busy ? null : (id) => setState(() => _subjectId = id),
            ),
            const SizedBox(height: 14),
            const FormLabel('Día'),
            DropdownButtonFormField<Weekday>(
              initialValue: _weekday,
              isExpanded: true,
              style: taskValueStyle,
              decoration: taskFieldDecoration(),
              items: [
                for (final day in Weekday.values)
                  DropdownMenuItem(value: day, child: Text(day.label)),
              ],
              onChanged: _busy
                  ? null
                  : (day) => setState(() => _weekday = day ?? _weekday),
            ),
            const SizedBox(height: 14),
            const FormLabel('Inicio'),
            _PickerField(
              value: formatBlockTime(_start),
              icon: Icons.schedule,
              onTap: _busy ? null : () => _pick(start: true),
            ),
            const SizedBox(height: 14),
            const FormLabel('Fin'),
            _PickerField(
              value: formatBlockTime(_end),
              icon: Icons.schedule,
              onTap: _busy ? null : () => _pick(start: false),
            ),
            const SizedBox(height: 14),
            const FormLabel('Aula (opcional)'),
            TextField(
              controller: _room,
              enabled: !_busy,
              maxLength: 50,
              style: taskValueStyle,
              decoration: taskFieldDecoration(hint: 'Ej. A-201')
                  .copyWith(counterText: ''),
            ),
            if (_error != null) ...[
              const SizedBox(height: 8),
              AuthErrorText(_error!),
            ],
          ],
        ),
      ),
      actions: [
        if (block != null)
          TextButton(
            style: TextButton.styleFrom(foregroundColor: Colors.red.shade700),
            onPressed: _busy ? null : () => _delete(block),
            child: const Text('Eliminar bloque'),
          ),
        TextButton(
          onPressed: _busy ? null : () => Navigator.of(context).pop(false),
          child: const Text('Cancelar'),
        ),
        _saveButton(busy: _busy, onPressed: _submit),
      ],
    );
  }
}

class _PeriodDialog extends StatefulWidget {
  const _PeriodDialog({
    required this.service,
    required this.today,
    required this.current,
  });

  final ScheduleService service;
  final DateTime today;
  final AcademicPeriod? current;

  @override
  State<_PeriodDialog> createState() => _PeriodDialogState();
}

class _PeriodDialogState extends State<_PeriodDialog> {
  late DateTime _start = widget.current?.start ?? widget.today;
  late DateTime _end =
      widget.current?.end ?? widget.today.add(const Duration(days: 120));
  bool _busy = false;
  String? _error;

  Future<void> _pick({required bool start}) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: start ? _start : _end,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (picked == null || !mounted) return;
    setState(() => start ? _start = picked : _end = picked);
  }

  Future<void> _submit() async {
    if (!_end.isAfter(_start)) {
      setState(
        () => _error = 'La fecha de fin debe ser posterior a la de inicio.',
      );
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final period = await widget.service.setPeriod(_start, _end);
      if (mounted) Navigator.of(context).pop(period);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: TaiaColors.ivoryMist,
      title: _dialogTitle('Período académico'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const FormLabel('Inicio'),
          _PickerField(
            value: formatPeriodDate(_start),
            icon: Icons.calendar_today_outlined,
            onTap: _busy ? null : () => _pick(start: true),
          ),
          const SizedBox(height: 14),
          const FormLabel('Fin'),
          _PickerField(
            value: formatPeriodDate(_end),
            icon: Icons.calendar_today_outlined,
            onTap: _busy ? null : () => _pick(start: false),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            AuthErrorText(_error!),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancelar'),
        ),
        _saveButton(busy: _busy, onPressed: _submit),
      ],
    );
  }
}
