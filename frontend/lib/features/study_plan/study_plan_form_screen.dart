import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../academic/schedule_block.dart';
import '../auth/auth_shell.dart';
import '../shell/page_header.dart';
import '../tasks/subject.dart';
import '../tasks/widgets/task_form_widgets.dart';
import 'study_plan_service.dart';

/// Formulario fijo del plan de estudio (RF-EST-01). Nunca por texto libre.
/// Devuelve las respuestas con `Navigator.pop`.
class StudyPlanFormScreen extends StatefulWidget {
  const StudyPlanFormScreen({
    super.key,
    required this.subjects,
    this.initial = const StudyPlanForm(),
  });

  /// Asignaturas activas para elegir cuáles incluir.
  final List<Subject> subjects;

  /// Al regenerar, las respuestas del plan anterior.
  final StudyPlanForm initial;

  @override
  State<StudyPlanFormScreen> createState() => _StudyPlanFormScreenState();
}

class _StudyPlanFormScreenState extends State<StudyPlanFormScreen> {
  late StudyPreference _preference = widget.initial.preference;
  late final Set<Weekday> _days = {...widget.initial.days};
  late TimeOfDay _windowStart = widget.initial.windowStart;
  late TimeOfDay _windowEnd = widget.initial.windowEnd;
  late int _sessionMinutes = widget.initial.sessionMinutes;
  late final Set<String> _subjects = {...widget.initial.subjectIds};
  late final List<BusyBlock> _busy = [...widget.initial.busyBlocks];
  late int? _maxDaily = widget.initial.maxDailyMinutes;
  late StudyTime _time = widget.initial.preferredTime;
  late bool _works = widget.initial.busyBlocks.any((b) => b.work);
  String? _error;

  static const _earliest = TimeOfDay(hour: 5, minute: 0);
  static const _latest = TimeOfDay(hour: 23, minute: 0);

  int _min(TimeOfDay t) => t.hour * 60 + t.minute;

  Future<TimeOfDay?> _pickTime(TimeOfDay initial) =>
      showTimePicker(context: context, initialTime: initial);

  Future<void> _addBusy({required bool work}) async {
    var weekday = Weekday.monday;
    var start = const TimeOfDay(hour: 8, minute: 0);
    var end = const TimeOfDay(hour: 12, minute: 0);
    final added = await showDialog<BusyBlock>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialog) => AlertDialog(
          backgroundColor: TaiaColors.ivoryMist,
          title: Text(work ? 'Horario de trabajo' : 'Compromiso fijo'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButton<Weekday>(
                value: weekday,
                isExpanded: true,
                items: [
                  for (final day in Weekday.values)
                    DropdownMenuItem(value: day, child: Text(day.label)),
                ],
                onChanged: (day) => setDialog(() => weekday = day!),
              ),
              ListTile(
                title: const Text('Desde'),
                trailing: Text(formatBlockTime(start)),
                onTap: () async {
                  final t = await _pickTime(start);
                  if (t != null) setDialog(() => start = t);
                },
              ),
              ListTile(
                title: const Text('Hasta'),
                trailing: Text(formatBlockTime(end)),
                onTap: () async {
                  final t = await _pickTime(end);
                  if (t != null) setDialog(() => end = t);
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: TaiaColors.fieryRose,
              ),
              onPressed: _min(end) > _min(start)
                  ? () => Navigator.of(context).pop(
                      BusyBlock(
                        work: work,
                        weekday: weekday,
                        start: start,
                        end: end,
                      ),
                    )
                  : null,
              child: const Text('Agregar'),
            ),
          ],
        ),
      ),
    );
    if (added != null && mounted) setState(() => _busy.add(added));
  }

  void _submit() {
    if (_min(_windowStart) < _min(_earliest) ||
        _min(_windowEnd) > _min(_latest)) {
      setState(
        () => _error =
            'La franja debe estar entre las 5:00 a. m. y las 11:00 p. m.',
      );
      return;
    }
    if (_min(_windowEnd) <= _min(_windowStart)) {
      setState(
        () => _error = 'El fin de la franja debe ser después del inicio.',
      );
      return;
    }
    Navigator.of(context).pop(
      StudyPlanForm(
        preference: _preference,
        days: _days,
        windowStart: _windowStart,
        windowEnd: _windowEnd,
        sessionMinutes: _sessionMinutes,
        subjectIds: _subjects,
        busyBlocks: _works ? _busy : _busy.where((b) => !b.work).toList(),
        maxDailyMinutes: _maxDaily != null && _maxDaily! < _sessionMinutes
            ? _sessionMinutes
            : _maxDaily,
        preferredTime: _time,
      ),
    );
  }

  Widget _busyList(bool work) => Column(
    children: [
      for (final block in _busy.where((b) => b.work == work))
        ListTile(
          dense: true,
          title: Text(
            '${block.weekday.label} · ${formatBlockTime(block.start)} a '
            '${formatBlockTime(block.end)}',
            style: taskValueStyle,
          ),
          trailing: IconButton(
            tooltip: 'Quitar',
            icon: const Icon(Icons.close),
            onPressed: () => setState(() => _busy.remove(block)),
          ),
        ),
      Align(
        alignment: Alignment.centerLeft,
        child: TextButton.icon(
          onPressed: () => _addBusy(work: work),
          icon: const Icon(Icons.add),
          label: Text(
            work ? 'Agregar horario de trabajo' : 'Agregar compromiso',
          ),
        ),
      ),
    ],
  );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: TaiaColors.ivoryMist,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            Align(
              alignment: Alignment.centerLeft,
              child: IconButton(
                tooltip: 'Volver',
                onPressed: () => Navigator.of(context).maybePop(),
                icon: const Icon(Icons.arrow_back_rounded, color: taiaInk),
              ),
            ),
            const PageHeader(
              label: 'PLAN DE ESTUDIO',
              title: 'Cuéntame de tu semana',
              subtitle: 'Con esto armo un plan que sí puedas cumplir.',
              expression: MascotExpression.organizing,
            ),
            const SizedBox(height: 16),
            const FormLabel('¿Cuándo prefieres estudiar?'),
            TaskSegments<StudyPreference>(
              value: _preference,
              options: {for (final p in StudyPreference.values) p: p.label},
              onChanged: (p) => setState(() => _preference = p),
            ),
            const SizedBox(height: 16),
            const FormLabel('Días disponibles (sin marcar: todos)'),
            Wrap(
              spacing: 6,
              children: [
                for (final day in Weekday.values)
                  FilterChip(
                    label: Text(day.label.substring(0, 3)),
                    selected: _days.contains(day),
                    selectedColor: TaiaColors.softPeach,
                    onSelected: (on) =>
                        setState(() => on ? _days.add(day) : _days.remove(day)),
                  ),
              ],
            ),
            const SizedBox(height: 16),
            const FormLabel('Franja horaria'),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () async {
                      final t = await _pickTime(_windowStart);
                      if (t != null) setState(() => _windowStart = t);
                    },
                    child: Text('Desde ${formatBlockTime(_windowStart)}'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton(
                    onPressed: () async {
                      final t = await _pickTime(_windowEnd);
                      if (t != null) setState(() => _windowEnd = t);
                    },
                    child: Text('Hasta ${formatBlockTime(_windowEnd)}'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            const FormLabel('Duración de cada sesión'),
            TaskSegments<int>(
              value: _sessionMinutes,
              options: const {
                30: '30 min',
                45: '45 min',
                60: '1 h',
                90: '1 h 30',
              },
              onChanged: (m) => setState(() => _sessionMinutes = m),
            ),
            const SizedBox(height: 16),
            const FormLabel('Máximo de estudio por día'),
            TaskSegments<int>(
              value: _maxDaily ?? 0,
              options: const {
                0: 'Sin máximo',
                60: '1 h',
                120: '2 h',
                180: '3 h',
                240: '4 h',
              },
              onChanged: (m) => setState(() => _maxDaily = m == 0 ? null : m),
            ),
            const SizedBox(height: 16),
            const FormLabel('¿En qué momento del día rindes mejor?'),
            TaskSegments<StudyTime>(
              value: _time,
              options: {for (final t in StudyTime.values) t: t.label},
              onChanged: (t) => setState(() => _time = t),
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              activeThumbColor: TaiaColors.fieryRose,
              title: const Text('¿Trabajas?', style: taskValueStyle),
              value: _works,
              onChanged: (on) => setState(() => _works = on),
            ),
            if (_works) _busyList(true),
            const FormLabel(
              'Otros compromisos fijos (cursos, deporte, transporte)',
            ),
            _busyList(false),
            if (widget.subjects.isNotEmpty) ...[
              const SizedBox(height: 8),
              const FormLabel('Asignaturas (sin marcar: todas)'),
              Wrap(
                spacing: 6,
                children: [
                  for (final subject in widget.subjects)
                    FilterChip(
                      label: Text(subject.name),
                      selected: _subjects.contains(subject.id),
                      selectedColor: TaiaColors.softPeach,
                      onSelected: (on) => setState(
                        () => on
                            ? _subjects.add(subject.id)
                            : _subjects.remove(subject.id),
                      ),
                    ),
                ],
              ),
            ],
            const SizedBox(height: 20),
            if (_error != null) AuthErrorText(_error!),
            AuthSubmitButton(
              label: 'Generar plan',
              loading: false,
              onPressed: _submit,
            ),
          ],
        ),
      ),
    );
  }
}
