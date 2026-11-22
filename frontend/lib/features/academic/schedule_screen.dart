import 'package:flutter/material.dart';

import '../../core/bogota_time.dart';
import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../profile/widgets/profile_tile.dart';
import '../shell/mascot_message.dart';
import '../tasks/subject.dart';
import '../tasks/subjects_service.dart';
import 'schedule_block.dart';
import 'schedule_service.dart';
import '../shell/page_header.dart';
import 'widgets/schedule_dialogs.dart';

/// Horario semanal (RF-ASG-06 y RF-ASG-07) y período académico (RF-ASG-08).
class ScheduleScreen extends StatefulWidget {
  const ScheduleScreen({super.key, this.service, this.subjectsService});

  final ScheduleService? service;
  final SubjectsService? subjectsService;

  @override
  State<ScheduleScreen> createState() => _ScheduleScreenState();
}

class _ScheduleScreenState extends State<ScheduleScreen> {
  List<ScheduleBlock>? _blocks;
  List<Subject> _subjects = const [];
  AcademicPeriod? _period;
  String? _error;

  ScheduleService get _service => widget.service ?? scheduleService;
  SubjectsService get _subjectService =>
      widget.subjectsService ?? subjectsService;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _error = null);
    try {
      final blocks = await _service.list();
      final period = await _service.period();
      final subjects = await _subjectService.list();
      if (!mounted) return;
      setState(() {
        _blocks = blocks;
        _period = period;
        _subjects = subjects;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _editBlock([ScheduleBlock? block]) async {
    final changed = await showScheduleBlockDialog(
      context,
      service: _service,
      subjects: _subjects,
      block: block,
    );
    if (changed && mounted) await _load();
  }

  Future<void> _editPeriod() async {
    final period = await showPeriodDialog(
      context,
      service: _service,
      today: bogotaNow(),
      current: _period,
    );
    if (period != null && mounted) setState(() => _period = period);
  }

  static String _blockSubtitle(ScheduleBlock block) {
    final hours =
        '${formatBlockTime(block.start)} – ${formatBlockTime(block.end)}';
    final room = block.room;
    return room == null ? hours : '$hours · $room';
  }

  @override
  Widget build(BuildContext context) {
    final blocks = _blocks;
    return Scaffold(
      backgroundColor: TaiaColors.ivoryMist,
      body: SafeArea(
        child: blocks == null
            ? MascotMessage(
                expression: _error == null
                    ? MascotExpression.thinking
                    : MascotExpression.surprised,
                text: _error ?? 'Cargando tu horario…',
                showSpinner: _error == null,
                onRetry: _error == null ? null : _load,
              )
            : RefreshIndicator(
                color: TaiaColors.fieryRose,
                onRefresh: _load,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                  children: [
                    const PageHeader(
                      label: 'ACADÉMICO',
                      title: 'Horario',
                      subtitle: 'Tus clases de la semana, en hora de Colombia.',
                      expression: MascotExpression.organizing,
                    ),
                    const SizedBox(height: 20),
                    ProfileSection(
                      title: 'PERÍODO ACADÉMICO',
                      tiles: [_periodTile()],
                    ),
                    const SizedBox(height: 20),
                    if (blocks.isEmpty)
                      const EmptyStateCard(
                        'Todavía no tienes clases en tu horario.',
                      )
                    else
                      for (final day in Weekday.values)
                        if (blocks.any((b) => b.weekday == day)) ...[
                          ProfileSection(
                            title: day.label.toUpperCase(),
                            tiles: [
                              for (final block in blocks)
                                if (block.weekday == day)
                                  ProfileTile(
                                    icon: Icons.schedule,
                                    title: block.subjectName,
                                    subtitle: _blockSubtitle(block),
                                    onTap: () => _editBlock(block),
                                  ),
                            ],
                          ),
                          const SizedBox(height: 16),
                        ],
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      AuthErrorText(_error!),
                    ],
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      style: FilledButton.styleFrom(
                        backgroundColor: TaiaColors.fieryRose,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      onPressed: () => _editBlock(),
                      icon: const Icon(Icons.add),
                      label: const Text(
                        'Nuevo bloque',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _periodTile() {
    final period = _period;
    return ProfileTile(
      icon: Icons.date_range_outlined,
      title: period == null ? 'Sin definir' : 'Semestre',
      subtitle: period == null
          ? 'Define el inicio y el fin de tu semestre.'
          : '${formatPeriodDate(period.start)} – '
                '${formatPeriodDate(period.end)}',
      onTap: _editPeriod,
    );
  }
}
