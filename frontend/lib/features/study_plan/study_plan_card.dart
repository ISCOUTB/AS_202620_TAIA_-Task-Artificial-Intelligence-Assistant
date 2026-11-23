import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/bogota_time.dart';
import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import 'study_plan_screen.dart';
import 'study_plan_service.dart';

/// Lo que dice la tarjeta del plan según su estado (RNF-14, RF-EST-01 a 03).
class StudyPlanSummary {
  const StudyPlanSummary(this.title, this.detail, this.action);

  final String title;
  final String detail;
  final String action;
}

String _hm(DateTime t) =>
    '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

/// Resume el plan para la tarjeta, con la voz de TAIA (RF-AGT-22).
StudyPlanSummary summarizeStudyPlan(StudyPlan? plan, DateTime now) {
  if (plan == null) {
    return const StudyPlanSummary(
      'Arma tu plan de estudio',
      'Te sugiero cuándo estudiar cada materia esta semana, según tu horario.',
      'Crear mi plan',
    );
  }
  if (plan.proposed) {
    return const StudyPlanSummary(
      'Tu plan está listo para revisar',
      'Lo armé con tus preferencias. Míralo y acéptalo si te sirve.',
      'Revisar plan',
    );
  }
  final today = DateTime(now.year, now.month, now.day);
  final tomorrow = today.add(const Duration(days: 1));
  final todaySessions =
      plan.sessions
          .where(
            (s) => !s.startsAt.isBefore(today) && s.startsAt.isBefore(tomorrow),
          )
          .toList()
        ..sort((a, b) => a.startsAt.compareTo(b.startsAt));
  if (todaySessions.isNotEmpty) {
    final first = todaySessions.first;
    final more = todaySessions.length - 1;
    return StudyPlanSummary(
      'Hoy estudias ${first.subjectName}',
      '${_hm(first.startsAt)} · ${first.title}'
          '${more > 0 ? ' · y $more sesión${more == 1 ? '' : 'es'} más' : ''}',
      'Ver mi plan',
    );
  }
  final next = plan.sessions.where((s) => s.startsAt.isAfter(now)).toList()
    ..sort((a, b) => a.startsAt.compareTo(b.startsAt));
  if (next.isEmpty) {
    return const StudyPlanSummary(
      'Tu plan de esta semana terminó',
      '¡Lo lograste! Armemos el de la próxima.',
      'Nuevo plan',
    );
  }
  return StudyPlanSummary(
    'Hoy descansas del plan',
    'Tu próxima sesión: ${next.first.subjectName}, '
        '${next.first.startsAt.day}/${next.first.startsAt.month} a las '
        '${_hm(next.first.startsAt)}.',
    'Ver mi plan',
  );
}

/// Tarjeta del plan de estudio, en el Inicio y en Tareas (RNF-14). Al tocarla
/// se abre el plan. Si cambia [version], vuelve a pedirlo.
class StudyPlanCard extends StatefulWidget {
  const StudyPlanCard({super.key, this.service, this.version = 0});

  final StudyPlanService? service;
  final int version;

  @override
  State<StudyPlanCard> createState() => _StudyPlanCardState();
}

class _StudyPlanCardState extends State<StudyPlanCard> {
  StudyPlan? _plan;
  bool _loaded = false;

  StudyPlanService get _service => widget.service ?? studyPlanService;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(StudyPlanCard old) {
    super.didUpdateWidget(old);
    if (old.version != widget.version) _load();
  }

  Future<void> _load() async {
    try {
      final plan = await _service.current();
      if (mounted) {
        setState(() {
          _plan = plan;
          _loaded = true;
        });
      }
    } on ApiException {
      // Sin el plan, la tarjeta invita a crearlo igual.
      if (mounted) setState(() => _loaded = true);
    }
  }

  Future<void> _open() async {
    HapticFeedback.selectionClick();
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => StudyPlanScreen(service: widget.service),
      ),
    );
    if (mounted) await _load();
  }

  @override
  Widget build(BuildContext context) {
    final summary = summarizeStudyPlan(_plan, bogotaNow());
    return AnimatedOpacity(
      opacity: _loaded ? 1 : 0.6,
      duration: const Duration(milliseconds: 200),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _open,
          borderRadius: BorderRadius.circular(24),
          child: Ink(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(24),
              gradient: const LinearGradient(
                colors: [TaiaColors.apricotWhisper, TaiaColors.softPeach],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: Row(
              children: [
                const SizedBox.square(
                  dimension: 64,
                  child: TaiaMascot(
                    motion: 0.5,
                    expression: MascotExpression.books,
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
                          fontSize: 11,
                          letterSpacing: 1.4,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        summary.title,
                        style: const TextStyle(
                          color: taiaInk,
                          fontSize: 17,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        summary.detail,
                        style: TextStyle(
                          color: taiaInk.withValues(alpha: 0.75),
                          fontSize: 13,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '${summary.action} →',
                        style: const TextStyle(
                          color: TaiaColors.fieryRose,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
