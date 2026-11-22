import 'package:flutter/material.dart';

import '../../core/api_error.dart';
import '../../core/bogota_time.dart';
import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../academic/schedule_block.dart';
import '../academic/widgets/schedule_dialogs.dart';
import '../auth/auth_shell.dart';
import '../shell/page_header.dart';
import '../tasks/subject.dart';
import '../tasks/widgets/task_form_widgets.dart';
import 'onboarding_logic.dart';
import 'onboarding_service.dart';

/// Configuración inicial obligatoria (RF-ASG-10): tipo de estudiante, período
/// académico con fechas sugeridas (RF-ASG-08), asignaturas (RF-ASG-01) y
/// horario de clases (RF-ASG-06, opcional). No se puede saltar.
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key, required this.onDone, this.service});

  /// Se llama al terminar; la app entra a la pantalla principal.
  final VoidCallback onDone;
  final OnboardingService? service;

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  late final OnboardingService _service = widget.service ?? OnboardingService();
  final _subjectName = TextEditingController();

  int _step = 0;
  StudentType _type = StudentType.university;
  AcademicPeriod? _period;
  List<Subject> _subjects = [];
  List<ScheduleBlock> _blocks = [];
  bool _busy = false;
  String? _error;

  static const _titles = [
    '¿Qué estudias?',
    'Tu período académico',
    'Tus asignaturas',
    'Tu horario de clases',
  ];

  @override
  void initState() {
    super.initState();
    _loadExisting();
  }

  @override
  void dispose() {
    _subjectName.dispose();
    super.dispose();
  }

  /// Una cuenta existente puede tener ya asignaturas u horario.
  Future<void> _loadExisting() async {
    try {
      final subjects = await _service.subjects.list();
      final blocks = await _service.schedule.list();
      if (!mounted) return;
      setState(() {
        _subjects = subjects;
        _blocks = blocks;
      });
    } on ApiException {
      // Si falla, el estudiante los agrega en los pasos.
    }
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await action();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _chooseType() {
    setState(() {
      _period = suggestedPeriod(_type, bogotaNow());
      _step = 1;
    });
  }

  Future<void> _savePeriod() => _run(() async {
    final period = _period!;
    final saved = await _service.schedule.setPeriod(period.start, period.end);
    if (mounted) {
      setState(() {
        _period = saved;
        _step = 2;
      });
    }
  });

  Future<void> _adjustPeriod() async {
    final saved = await showPeriodDialog(
      context,
      service: _service.schedule,
      today: bogotaNow(),
      current: _period,
    );
    if (saved != null && mounted) {
      setState(() {
        _period = saved;
        _step = 2;
      });
    }
  }

  Future<void> _addSubject() async {
    final name = _subjectName.text.trim();
    if (name.isEmpty) return;
    await _run(() async {
      final subject = await _service.subjects.create(name: name);
      _subjectName.clear();
      if (mounted) setState(() => _subjects = [..._subjects, subject]);
    });
  }

  Future<void> _addClass() async {
    final changed = await showScheduleBlockDialog(
      context,
      service: _service.schedule,
      subjects: _subjects,
    );
    if (!changed || !mounted) return;
    await _run(() async {
      final blocks = await _service.schedule.list();
      if (mounted) setState(() => _blocks = blocks);
    });
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      // RF-ASG-10: no se puede salir sin terminar.
      canPop: false,
      child: Scaffold(
        backgroundColor: TaiaColors.ivoryMist,
        body: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
            children: [
              PageHeader(
                label: 'PASO ${_step + 1} DE 4',
                title: _titles[_step],
                subtitle: 'Configuremos TAIA para ti 🐙',
                expression: MascotExpression.organizing,
              ),
              const SizedBox(height: 8),
              LinearProgressIndicator(
                value: (_step + 1) / 4,
                color: TaiaColors.fieryRose,
                backgroundColor: TaiaColors.softPeach,
              ),
              const SizedBox(height: 20),
              ...switch (_step) {
                0 => _typeStep(),
                1 => _periodStep(),
                2 => _subjectsStep(),
                _ => _scheduleStep(),
              },
              if (_error != null) ...[
                const SizedBox(height: 12),
                AuthErrorText(_error!),
              ],
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _typeStep() => [
    const Text(
      'Así te sugerimos las fechas de tu ciclo. Cada colegio, universidad o '
      'curso tiene las suyas, y podrás cambiarlas.',
      style: TextStyle(color: taiaInk, fontSize: 15),
    ),
    const SizedBox(height: 16),
    for (final type in StudentType.values)
      Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: ChoiceChip(
          label: SizedBox(width: double.infinity, child: Text(type.label)),
          selected: _type == type,
          selectedColor: TaiaColors.fieryRose,
          labelStyle: TextStyle(
            color: _type == type ? Colors.white : taiaInk,
            fontWeight: FontWeight.w700,
          ),
          showCheckmark: false,
          onSelected: (_) => setState(() => _type = type),
        ),
      ),
    const SizedBox(height: 12),
    AuthSubmitButton(
      label: 'Continuar',
      loading: false,
      onPressed: _chooseType,
    ),
  ];

  List<Widget> _periodStep() {
    final period = _period!;
    return [
      Text(
        _type == StudentType.course || _type == StudentType.other
            ? 'Tu curso no tiene un ciclo fijo: pon las fechas reales de inicio y fin.'
            : 'Te sugerimos estas fechas para ${_type.label.toLowerCase()}. '
                  'Si tu ciclo es distinto, ajústalas.',
        style: const TextStyle(color: taiaInk, fontSize: 15),
      ),
      const SizedBox(height: 16),
      EmptyStateCard(
        'Del ${formatPeriodDate(period.start)} al ${formatPeriodDate(period.end)}',
      ),
      const SizedBox(height: 16),
      AuthSubmitButton(
        label: 'Usar estas fechas',
        loading: _busy,
        onPressed: _savePeriod,
      ),
      const SizedBox(height: 8),
      OutlinedButton(
        onPressed: _busy ? null : _adjustPeriod,
        child: const Text('Ajustar fechas'),
      ),
      TextButton(
        onPressed: _busy ? null : () => setState(() => _step = 0),
        child: const Text('Atrás'),
      ),
    ];
  }

  List<Widget> _subjectsStep() => [
    const Text(
      'Escribe las asignaturas que cursas en este período. Necesitas al menos una.',
      style: TextStyle(color: taiaInk, fontSize: 15),
    ),
    const SizedBox(height: 16),
    Row(
      children: [
        Expanded(
          child: TextField(
            controller: _subjectName,
            enabled: !_busy,
            style: taskValueStyle,
            textCapitalization: TextCapitalization.sentences,
            onSubmitted: (_) => _addSubject(),
            decoration: taskFieldDecoration(hint: 'Por ejemplo: Cálculo'),
          ),
        ),
        const SizedBox(width: 8),
        IconButton.filled(
          tooltip: 'Agregar asignatura',
          onPressed: _busy ? null : _addSubject,
          style: IconButton.styleFrom(backgroundColor: TaiaColors.fieryRose),
          icon: const Icon(Icons.add),
        ),
      ],
    ),
    const SizedBox(height: 12),
    for (final subject in _subjects)
      ListTile(
        dense: true,
        leading: const Icon(
          Icons.menu_book_outlined,
          color: TaiaColors.fieryRose,
        ),
        title: Text(subject.name, style: taskValueStyle),
      ),
    const SizedBox(height: 12),
    AuthSubmitButton(
      label: 'Continuar',
      loading: _busy,
      onPressed: _subjects.isEmpty
          ? () => setState(() => _error = 'Agrega al menos una asignatura.')
          : () => setState(() {
              _error = null;
              _step = 3;
            }),
    ),
  ];

  List<Widget> _scheduleStep() => [
    const Text(
      'Agrega tus clases de la semana. TAIA las usa para no ponerte a estudiar '
      'encima de ellas. Si no tienes clases fijas, puedes terminar.',
      style: TextStyle(color: taiaInk, fontSize: 15),
    ),
    const SizedBox(height: 16),
    for (final block in _blocks)
      ListTile(
        dense: true,
        leading: const Icon(Icons.schedule, color: TaiaColors.fieryRose),
        title: Text(block.subjectName, style: taskValueStyle),
        subtitle: Text(
          '${block.weekday.label} · ${formatBlockTime(block.start)} a '
          '${formatBlockTime(block.end)}',
        ),
      ),
    OutlinedButton.icon(
      onPressed: _busy ? null : _addClass,
      icon: const Icon(Icons.add),
      label: const Text('Agregar clase'),
    ),
    const SizedBox(height: 16),
    AuthSubmitButton(
      label: 'Terminar',
      loading: _busy,
      onPressed: widget.onDone,
    ),
  ];
}
