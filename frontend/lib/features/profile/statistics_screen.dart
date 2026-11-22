import 'package:flutter/material.dart';

import '../../core/bogota_time.dart';
import '../../core/spanish_dates.dart';
import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../shell/mascot_message.dart';
import '../tasks/widgets/task_form_widgets.dart';
import 'statistics_service.dart';

/// Estadísticas del perfil (RF-PRF-01): cinco gráficos de un período
/// seleccionable, cada uno con su pregunta y su estado vacío. Se muestran
/// directamente en el perfil, sin abrir otra pantalla.
class StatisticsSection extends StatefulWidget {
  const StatisticsSection({super.key, this.service});

  final StatisticsService? service;

  @override
  State<StatisticsSection> createState() => StatisticsSectionState();
}

class StatisticsSectionState extends State<StatisticsSection> {
  StatisticsPeriod _period = StatisticsPeriod.month;
  ProfileStatistics? _data;
  String? _error;
  bool _loading = true;

  StatisticsService get _service => widget.service ?? statisticsService;

  @override
  void initState() {
    super.initState();
    _load();
  }

  /// La usa el perfil al deslizar para actualizar.
  Future<void> refresh() => _load();

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _service.load(_period);
      if (!mounted) return;
      setState(() {
        _data = data;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _data = null;
        _error = e.message;
        _loading = false;
      });
    }
  }

  String get _periodText => switch (_period) {
    StatisticsPeriod.week => 'esta semana',
    StatisticsPeriod.month => 'este mes',
    StatisticsPeriod.academicPeriod => 'este período',
  };

  @override
  Widget build(BuildContext context) {
    final data = _data;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Padding(
          padding: EdgeInsets.only(left: 4, bottom: 8),
          child: Text(
            'TU PROGRESO',
            style: TextStyle(
              color: TaiaColors.fieryRose,
              fontSize: 12,
              letterSpacing: 1.6,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
        TaskSegments<StatisticsPeriod>(
          value: _period,
          enabled: !_loading,
          options: const {
            StatisticsPeriod.week: 'Semana',
            StatisticsPeriod.month: 'Mes',
            StatisticsPeriod.academicPeriod: 'Período',
          },
          onChanged: (period) {
            setState(() => _period = period);
            _load();
          },
        ),
        const SizedBox(height: 16),
        if (_loading)
          const MascotMessage(
            expression: MascotExpression.thinking,
            text: 'Calculando tus estadísticas…',
            showSpinner: true,
          )
        else if (data == null)
          MascotMessage(
            expression: MascotExpression.surprised,
            text: _error ?? 'No se pudieron cargar tus estadísticas.',
            onRetry: _load,
          )
        else ...[
          _StatusCard(data: data, periodText: _periodText),
          _WeeklyCard(weeks: data.completedByWeek),
          _OnTimeCard(data: data, periodText: _periodText),
          _LoadCard(subjects: data.pendingBySubject, periodText: _periodText),
          _UpcomingCard(data: data),
        ],
      ],
    );
  }
}

/// Tarjeta con el título en forma de pregunta (RF-PRF-01).
class _ChartCard extends StatelessWidget {
  const _ChartCard({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              color: taiaInk,
              fontSize: 17,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty(this.text);

  final String text;

  @override
  Widget build(BuildContext context) =>
      Text(text, style: TextStyle(color: taiaInk.withValues(alpha: 0.65)));
}

/// Barra horizontal con su etiqueta y su valor.
class _HBar extends StatelessWidget {
  const _HBar({
    required this.label,
    required this.value,
    required this.max,
    required this.color,
  });

  final String label;
  final int value;
  final int max;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: taiaInk, fontSize: 13),
            ),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: max == 0 ? 0 : value / max,
                minHeight: 14,
                color: color,
                backgroundColor: TaiaColors.softPeach.withValues(alpha: 0.4),
              ),
            ),
          ),
          SizedBox(
            width: 34,
            child: Text(
              '$value',
              textAlign: TextAlign.right,
              style: const TextStyle(
                color: taiaInk,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({required this.data, required this.periodText});

  final ProfileStatistics data;
  final String periodText;

  @override
  Widget build(BuildContext context) {
    final total = data.completed + data.pending + data.overdue;
    return _ChartCard(
      title: '¿Cómo voy?',
      child: total == 0
          ? _Empty('No tienes actividades que venzan $periodText.')
          : Column(
              children: [
                _HBar(
                  label: 'Completadas',
                  value: data.completed,
                  max: total,
                  color: TaiaColors.fieryRose,
                ),
                _HBar(
                  label: 'Pendientes',
                  value: data.pending,
                  max: total,
                  color: TaiaColors.apricotWhisper,
                ),
                _HBar(
                  label: 'Vencidas',
                  value: data.overdue,
                  max: total,
                  color: TaiaColors.mascotRed,
                ),
              ],
            ),
    );
  }
}

class _WeeklyCard extends StatelessWidget {
  const _WeeklyCard({required this.weeks});

  final List<WeeklyCompletion> weeks;

  @override
  Widget build(BuildContext context) {
    final max = weeks.fold(0, (m, w) => w.completed > m ? w.completed : m);
    return _ChartCard(
      title: '¿Estoy siendo constante?',
      child: max == 0
          ? const _Empty(
              'Aún no has completado tareas en las últimas 8 semanas.',
            )
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Completadas por semana',
                  style: TextStyle(
                    color: taiaInk.withValues(alpha: 0.65),
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 8),
                SizedBox(
                  height: 130,
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      for (final week in weeks)
                        Expanded(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.end,
                            children: [
                              Text(
                                '${week.completed}',
                                style: const TextStyle(
                                  color: taiaInk,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Container(
                                height: 80 * week.completed / max,
                                margin: const EdgeInsets.symmetric(
                                  horizontal: 4,
                                ),
                                decoration: BoxDecoration(
                                  color: TaiaColors.fieryRose,
                                  borderRadius: BorderRadius.circular(6),
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${week.weekStart.day}/${week.weekStart.month}',
                                style: TextStyle(
                                  color: taiaInk.withValues(alpha: 0.6),
                                  fontSize: 10,
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}

class _OnTimeCard extends StatelessWidget {
  const _OnTimeCard({required this.data, required this.periodText});

  final ProfileStatistics data;
  final String periodText;

  @override
  Widget build(BuildContext context) {
    final percentage = data.onTimePercentage;
    return _ChartCard(
      title: '¿Entrego antes de la fecha límite?',
      child: percentage == null
          ? _Empty('Aún no has completado tareas $periodText.')
          : Row(
              children: [
                Text(
                  '${percentage.toStringAsFixed(1).replaceAll('.', ',')} %',
                  style: const TextStyle(
                    color: TaiaColors.fieryRose,
                    fontSize: 34,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Text(
                    '${data.onTime} de ${data.onTimeCompleted} completadas a '
                    'tiempo',
                    style: const TextStyle(color: taiaInk),
                  ),
                ),
              ],
            ),
    );
  }
}

class _LoadCard extends StatelessWidget {
  const _LoadCard({required this.subjects, required this.periodText});

  final List<SubjectLoad> subjects;
  final String periodText;

  @override
  Widget build(BuildContext context) {
    final max = subjects.fold(0, (m, s) => s.pending > m ? s.pending : m);
    return _ChartCard(
      title: '¿Qué materia me está cargando más?',
      child: subjects.isEmpty
          ? _Empty('No tienes pendientes que venzan $periodText.')
          : Column(
              children: [
                for (final subject in subjects)
                  _HBar(
                    label: subject.subjectName,
                    value: subject.pending,
                    max: max,
                    color: TaiaColors.fieryRose,
                  ),
              ],
            ),
    );
  }
}

class _UpcomingCard extends StatelessWidget {
  const _UpcomingCard({required this.data});

  final ProfileStatistics data;

  @override
  Widget build(BuildContext context) {
    final now = bogotaNow();
    return _ChartCard(
      title: '¿Qué viene ahora?',
      child: data.upcoming.isEmpty
          ? const _Empty('Nada vence en los próximos 7 días.')
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final task in data.upcoming)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.event_outlined,
                          color: TaiaColors.fieryRose,
                          size: 20,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                task.title,
                                style: const TextStyle(
                                  color: taiaInk,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              Text(
                                '${task.subjectName} · '
                                '${formatDueLabel(task.dueAt, now)}',
                                style: TextStyle(
                                  color: taiaInk.withValues(alpha: 0.65),
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
    );
  }
}
