import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../theme/taia_colors.dart';
import '../academic/schedule_block.dart';
import '../activity/widgets/activity_form_widgets.dart';
import '../auth/auth_shell.dart';
import '../tasks/subject.dart';
import '../tasks/widgets/task_form_widgets.dart';
import 'study_plan_service.dart';

/// Franjas para elegir con un toque (RNF-14).
const _windowPresets = [
  (
    label: 'Mañana',
    start: TimeOfDay(hour: 6, minute: 0),
    end: TimeOfDay(hour: 12, minute: 0),
  ),
  (
    label: 'Tarde',
    start: TimeOfDay(hour: 12, minute: 0),
    end: TimeOfDay(hour: 18, minute: 0),
  ),
  (
    label: 'Noche',
    start: TimeOfDay(hour: 18, minute: 0),
    end: TimeOfDay(hour: 22, minute: 0),
  ),
  (
    label: 'Todo el día',
    start: TimeOfDay(hour: 6, minute: 0),
    end: TimeOfDay(hour: 22, minute: 0),
  ),
];

/// Formulario fijo del plan de estudio (RF-EST-01), paso a paso: TAIA hace
/// una o dos preguntas por pantalla (RNF-14). Nunca por texto libre. Devuelve
/// las respuestas con `Navigator.pop`.
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

  /// Paso actual del formulario (0 a [_steps] - 1).
  int _step = 0;
  static const _steps = 5;

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

  String? _windowError() {
    if (_min(_windowStart) < _min(_earliest) ||
        _min(_windowEnd) > _min(_latest)) {
      return 'La franja debe estar entre las 5:00 a. m. y las 11:00 p. m.';
    }
    if (_min(_windowEnd) <= _min(_windowStart)) {
      return 'El fin de la franja debe ser después del inicio.';
    }
    return null;
  }

  void _next() {
    if (_step == 1) {
      final error = _windowError();
      if (error != null) {
        setState(() => _error = error);
        return;
      }
    }
    HapticFeedback.selectionClick();
    if (_step == _steps - 1) {
      _submit();
      return;
    }
    setState(() {
      _error = null;
      _step++;
    });
  }

  void _back() {
    if (_step == 0) {
      Navigator.of(context).maybePop();
      return;
    }
    setState(() {
      _error = null;
      _step--;
    });
  }

  void _submit() {
    final error = _windowError();
    if (error != null) {
      setState(() => _error = error);
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

  /// Lo que TAIA pregunta en cada paso.
  static const _questions = [
    '¿Cuándo te gusta estudiar?',
    '¿Qué días y a qué horas?',
    '¿Cuánto estudias de una sentada?',
    '¿Tienes compromisos fijos?',
    '¿Qué materias incluimos?',
  ];

  static const _expressions = [
    MascotExpression.thinking,
    MascotExpression.organizing,
    MascotExpression.studying,
    MascotExpression.laptop,
    MascotExpression.books,
  ];

  bool _sameTime(TimeOfDay a, TimeOfDay b) =>
      a.hour == b.hour && a.minute == b.minute;

  Widget _chips<T>(
    Map<T, String> options,
    bool Function(T) selected,
    void Function(T) onTap,
  ) => Wrap(
    spacing: 8,
    runSpacing: 6,
    children: [
      for (final entry in options.entries)
        TaiaChoiceChip(
          label: entry.value,
          selected: selected(entry.key),
          onSelected: () => setState(() => onTap(entry.key)),
        ),
    ],
  );

  List<Widget> _stepContent() {
    switch (_step) {
      case 0:
        return [
          const FormLabel('Prefiero estudiar…'),
          _chips<StudyPreference>(
            {for (final p in StudyPreference.values) p: p.label},
            (p) => p == _preference,
            (p) => _preference = p,
          ),
          const SizedBox(height: 18),
          const FormLabel('Rindo mejor en la…'),
          _chips<StudyTime>(
            {for (final s in StudyTime.values) s: s.label},
            (s) => s == _time,
            (s) => _time = s,
          ),
        ];
      case 1:
        const weekdays = {
          Weekday.monday,
          Weekday.tuesday,
          Weekday.wednesday,
          Weekday.thursday,
          Weekday.friday,
        };
        const weekend = {Weekday.saturday, Weekday.sunday};
        bool sameSet(Set<Weekday> s) =>
            _days.length == s.length && _days.containsAll(s);
        final customWindow = !_windowPresets.any(
          (w) =>
              _sameTime(w.start, _windowStart) && _sameTime(w.end, _windowEnd),
        );
        return [
          const FormLabel('Días'),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: [
              TaiaChoiceChip(
                label: 'Todos',
                selected: _days.isEmpty,
                onSelected: () => setState(_days.clear),
              ),
              TaiaChoiceChip(
                label: 'Lun a Vie',
                selected: sameSet(weekdays),
                onSelected: () => setState(() {
                  _days
                    ..clear()
                    ..addAll(weekdays);
                }),
              ),
              TaiaChoiceChip(
                label: 'Fin de semana',
                selected: sameSet(weekend),
                onSelected: () => setState(() {
                  _days
                    ..clear()
                    ..addAll(weekend);
                }),
              ),
            ],
          ),
          const SizedBox(height: 8),
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
          const SizedBox(height: 18),
          const FormLabel('Franja para estudiar'),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: [
              for (final w in _windowPresets)
                TaiaChoiceChip(
                  label: w.label,
                  selected:
                      _sameTime(w.start, _windowStart) &&
                      _sameTime(w.end, _windowEnd),
                  onSelected: () => setState(() {
                    _windowStart = w.start;
                    _windowEnd = w.end;
                    _error = null;
                  }),
                ),
              TaiaChoiceChip(
                label: 'Otra franja…',
                selected: customWindow,
                onSelected: () async {
                  final start = await _pickTime(_windowStart);
                  if (start == null || !mounted) return;
                  final end = await _pickTime(_windowEnd);
                  if (end == null || !mounted) return;
                  setState(() {
                    _windowStart = start;
                    _windowEnd = end;
                    _error = null;
                  });
                },
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            'De ${formatBlockTime(_windowStart)} a ${formatBlockTime(_windowEnd)}',
            style: const TextStyle(color: taiaInk, fontWeight: FontWeight.w700),
          ),
        ];
      case 2:
        return [
          const FormLabel('Cada sesión dura'),
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
          const SizedBox(height: 18),
          const FormLabel('Como máximo al día'),
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
        ];
      case 3:
        return [
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
        ];
      default:
        return [
          if (widget.subjects.isEmpty)
            const Text(
              'Incluyo todas tus materias.',
              style: TextStyle(color: taiaInk),
            )
          else ...[
            const FormLabel('Sin marcar: todas'),
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
        ];
    }
  }

  @override
  Widget build(BuildContext context) {
    final last = _step == _steps - 1;
    return Scaffold(
      backgroundColor: TaiaColors.ivoryMist,
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 8, 16, 0),
              child: Row(
                children: [
                  IconButton(
                    tooltip: 'Volver',
                    onPressed: _back,
                    icon: const Icon(Icons.arrow_back_rounded, color: taiaInk),
                  ),
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: TweenAnimationBuilder<double>(
                        tween: Tween(end: (_step + 1) / _steps),
                        duration: const Duration(milliseconds: 250),
                        builder: (context, value, _) => LinearProgressIndicator(
                          value: value,
                          minHeight: 8,
                          color: TaiaColors.fieryRose,
                          backgroundColor: TaiaColors.softPeach,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    '${_step + 1} de $_steps',
                    style: const TextStyle(
                      color: taiaInk,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 250),
                transitionBuilder: (child, animation) => FadeTransition(
                  opacity: animation,
                  child: SlideTransition(
                    position: Tween(
                      begin: const Offset(0.08, 0),
                      end: Offset.zero,
                    ).animate(animation),
                    child: child,
                  ),
                ),
                child: ListView(
                  key: ValueKey(_step),
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
                  children: [
                    Row(
                      children: [
                        SizedBox.square(
                          dimension: 72,
                          child: TaiaMascot(
                            motion: 0.6,
                            expression: _expressions[_step],
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'PLAN DE ESTUDIO',
                                style: TextStyle(
                                  color: TaiaColors.fieryRose,
                                  fontSize: 12,
                                  letterSpacing: 1.6,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                _questions[_step],
                                style: const TextStyle(
                                  color: taiaInk,
                                  fontSize: 24,
                                  height: 1.15,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 18),
                    ..._stepContent(),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Column(
                children: [
                  if (_error != null) AuthErrorText(_error!),
                  AuthSubmitButton(
                    label: last ? 'Generar plan' : 'Siguiente',
                    loading: false,
                    onPressed: _next,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
