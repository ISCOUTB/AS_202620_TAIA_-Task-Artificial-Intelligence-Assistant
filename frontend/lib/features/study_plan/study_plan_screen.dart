import 'package:flutter/material.dart';

import '../../core/api_error.dart';
import '../../core/spanish_dates.dart';
import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_shell.dart';
import '../shell/mascot_message.dart';
import '../shell/page_header.dart';
import '../tasks/subject.dart';
import '../tasks/subjects_service.dart';
import 'study_plan_form_screen.dart';
import 'study_plan_service.dart';

/// Plan de estudio (RF-EST-01…03): se pide con el formulario, se ve por días y
/// se acepta (queda en el calendario), se descarta o se regenera.
class StudyPlanScreen extends StatefulWidget {
  const StudyPlanScreen({super.key, this.service, this.subjects});

  final StudyPlanService? service;
  final SubjectsService? subjects;

  @override
  State<StudyPlanScreen> createState() => _StudyPlanScreenState();
}

class _StudyPlanScreenState extends State<StudyPlanScreen> {
  StudyPlan? _plan;
  bool _loading = true;
  bool _busy = false;
  String? _error;

  StudyPlanService get _service => widget.service ?? studyPlanService;
  SubjectsService get _subjects => widget.subjects ?? subjectsService;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final plan = await _service.current();
      if (mounted) setState(() => _plan = plan);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _run(Future<StudyPlan?> Function() action) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final plan = await action();
      if (mounted) setState(() => _plan = plan);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _request() async {
    List<Subject> subjects = const [];
    try {
      subjects = await _subjects.list();
    } on ApiException {
      // Sin la lista se generan con todas las asignaturas activas.
    }
    if (!mounted) return;
    final form = await Navigator.of(context).push<StudyPlanForm>(
      MaterialPageRoute(
        builder: (_) => StudyPlanFormScreen(
          subjects: subjects,
          initial: _plan?.form ?? const StudyPlanForm(),
        ),
      ),
    );
    if (form == null || !mounted) return;
    await _run(() => _service.generate(form));
  }

  Future<void> _accept() async {
    await _run(() => _service.accept(_plan!.id));
    if (mounted && _error == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Plan aceptado: ya está en tu calendario 🐙'),
        ),
      );
    }
  }

  Future<void> _discard() async {
    await _run(() async {
      await _service.discard(_plan!.id);
      return _service.current();
    });
  }

  @override
  Widget build(BuildContext context) {
    final plan = _plan;
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
              label: 'ACADÉMICO',
              title: 'Plan de estudio',
              subtitle: 'Sesiones para los próximos 7 días, sin chocar con tus clases.',
              expression: MascotExpression.organizing,
            ),
            const SizedBox(height: 16),
            if (_loading || _busy)
              MascotMessage(
                expression: MascotExpression.thinking,
                text: _busy ? 'Armando tu plan…' : 'Cargando tu plan…',
                showSpinner: true,
              )
            else if (plan == null) ...[
              const EmptyStateCard(
                'Aún no tienes un plan. Respóndeme unas preguntas y te propongo '
                'cuándo estudiar cada actividad 🐙',
              ),
              const SizedBox(height: 16),
              AuthSubmitButton(
                label: 'Crear mi plan',
                loading: false,
                onPressed: _request,
              ),
            ] else
              ..._planView(plan),
            if (_error != null) ...[
              const SizedBox(height: 12),
              AuthErrorText(_error!),
            ],
          ],
        ),
      ),
    );
  }

  List<Widget> _planView(StudyPlan plan) {
    final byDay = <DateTime, List<StudySession>>{};
    for (final session in plan.sessions) {
      final day = DateTime(
        session.startsAt.year,
        session.startsAt.month,
        session.startsAt.day,
      );
      byDay.putIfAbsent(day, () => []).add(session);
    }
    return [
      Text(
        plan.proposed
            ? 'Propuesta: revísala y acéptala si te sirve.'
            : 'Plan aceptado: está en tu calendario.',
        style: const TextStyle(color: taiaInk, fontWeight: FontWeight.w800),
      ),
      const SizedBox(height: 12),
      if (plan.sessions.isEmpty)
        const EmptyStateCard(
          'No encontré huecos libres con esas preferencias. Prueba con otra franja u otros días.',
        ),
      for (final entry in byDay.entries) ...[
        Padding(
          padding: const EdgeInsets.only(top: 8, bottom: 4),
          child: Text(
            formatLongDate(entry.key),
            style: const TextStyle(
              color: TaiaColors.fieryRose,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
        for (final session in entry.value)
          Card(
            color: Colors.white,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            child: ListTile(
              leading: const Icon(
                Icons.auto_stories_outlined,
                color: TaiaColors.fieryRose,
              ),
              title: Text(
                session.title,
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
              subtitle: Text(
                '${formatTime(session.startsAt)} a ${formatTime(session.endsAt)} · ${session.subjectName}',
              ),
            ),
          ),
      ],
      if (plan.unscheduled.isNotEmpty) ...[
        const SizedBox(height: 12),
        EmptyStateCard(
          'No cupieron: ${plan.unscheduled.join(', ')}. Prueba con más días o una franja más amplia.',
        ),
      ],
      const SizedBox(height: 16),
      if (plan.proposed)
        AuthSubmitButton(
          label: 'Aceptar plan',
          loading: false,
          onPressed: _accept,
        ),
      const SizedBox(height: 8),
      Row(
        children: [
          Expanded(
            child: OutlinedButton(
              onPressed: _request,
              child: const Text('Regenerar'),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: OutlinedButton(
              onPressed: _discard,
              child: const Text('Descartar'),
            ),
          ),
        ],
      ),
    ];
  }
}
