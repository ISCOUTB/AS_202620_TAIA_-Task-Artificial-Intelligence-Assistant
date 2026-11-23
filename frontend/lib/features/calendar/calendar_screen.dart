import '../../core/motion.dart';

import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/bogota_time.dart';
import '../../core/spanish_dates.dart';
import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../academic/schedule_screen.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../notifications/notifications_bell.dart';
import '../shell/mascot_message.dart';
import '../tasks/subjects_service.dart';
import '../tasks/task.dart';
import '../tasks/tasks_service.dart';
import '../tasks/widgets/task_edit_sheet.dart';
import 'calendar_logic.dart';
import 'calendar_service.dart';
import 'widgets/agenda_section.dart';
import 'widgets/calendar_card.dart';
import 'widgets/calendar_mode_toggle.dart';
import 'widgets/week_timeline.dart';

/// Pestaña Agenda: el horario y las actividades juntos (RF-TAR-11). La vista
/// de semana pone clases, sesiones de estudio y actividades en la misma línea
/// de tiempo; la de mes marca los días con entregas. Al tocar una actividad se
/// abre la hoja de edición, y el horario se edita desde aquí.
class CalendarScreen extends StatefulWidget {
  const CalendarScreen({
    super.key,
    this.tasksService,
    this.subjectsService,
    this.calendarService,
  });

  final TasksService? tasksService;
  final SubjectsService? subjectsService;
  final CalendarService? calendarService;

  @override
  State<CalendarScreen> createState() => CalendarScreenState();
}

class CalendarScreenState extends State<CalendarScreen> {
  List<AcademicTask>? _items;
  List<ClassOccurrence> _classes = const [];

  /// Rango que se pidió por última vez (RF-TAR-11).
  ({DateTime start, DateTime end})? _loadedRange;
  String? _error;
  bool _loading = true;

  CalendarMode _mode = CalendarMode.week;
  late DateTime _selected = dateOnly(bogotaNow());
  late DateTime _focused = _selected;

  bool _celebrating = false;
  Timer? _celebrationTimer;

  TasksService get _tasks => widget.tasksService ?? tasksService;
  SubjectsService get _subjects => widget.subjectsService ?? subjectsService;
  CalendarService get _calendar => widget.calendarService ?? calendarService;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _celebrationTimer?.cancel();
    super.dispose();
  }

  /// Vuelve a pedir el rango visible sin ocultar lo que ya se muestra.
  Future<void> refresh() => _load(silent: _items != null);

  Future<void> _load({bool silent = false}) async {
    if (!silent) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    final range = visibleRange(_mode, _focused);
    try {
      final data = await _calendar.range(range.start, range.end);
      if (!mounted) return;
      setState(() {
        _items = data.tasks;
        _classes = data.classes;
        _loadedRange = range;
        _error = null;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        // Si ya había tareas, se conservan y se ignora el fallo.
        if (_items == null) _error = e.message;
        _loading = false;
      });
    }
  }

  void _toast(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  void _celebrate() {
    _celebrationTimer?.cancel();
    setState(() => _celebrating = true);
    _celebrationTimer = Timer(const Duration(milliseconds: 2200), () {
      if (mounted) setState(() => _celebrating = false);
    });
  }

  /// Si cambió el mes o la semana a la vista, pide su rango.
  void _reloadIfRangeChanged() {
    if (visibleRange(_mode, _focused) != _loadedRange) _load(silent: true);
  }

  void _setMode(CalendarMode mode) {
    if (mode == _mode) return;
    setState(() {
      _mode = mode;
      _focused = _selected;
    });
    _reloadIfRangeChanged();
  }

  /// Avanza ([delta] = 1) o retrocede ([delta] = -1) un mes o una semana y deja
  /// seleccionado el día de hoy (si está a la vista) o el primer día.
  void _go(int delta) {
    final today = dateOnly(bogotaNow());
    setState(() {
      if (_mode == CalendarMode.month) {
        final month = addMonths(_focused, delta);
        _focused = month;
        _selected = (month.year == today.year && month.month == today.month)
            ? today
            : month;
      } else {
        final week = addWeeks(_focused, delta);
        _focused = week;
        final days = weekDays(week);
        _selected = days.any((d) => isSameDay(d, today)) ? today : days.first;
      }
    });
    _reloadIfRangeChanged();
  }

  void _goToday() {
    final today = dateOnly(bogotaNow());
    setState(() {
      _selected = today;
      _focused = today;
    });
    _reloadIfRangeChanged();
  }

  Future<void> _edit(AcademicTask task) async {
    final result = await showTaskEditSheet(
      context,
      task,
      tasksService: _tasks,
      subjectsService: _subjects,
    );
    if (!mounted || result == null) return;
    if (result.deleted) {
      setState(() {
        _items = (_items ?? []).where((t) => t.id != task.id).toList();
      });
      _toast('Tarea eliminada');
      return;
    }
    final saved = result.task!;
    setState(() {
      _items = [
        for (final t in _items ?? <AcademicTask>[])
          t.id == saved.id ? saved : t,
      ];
    });
    _toast('Cambios guardados');
    if (saved.status == TaskStatus.completed &&
        task.status != TaskStatus.completed) {
      _celebrate();
    }
  }

  /// El horario se edita desde la Agenda (RF-TAR-11); al volver se recarga.
  Future<void> _editSchedule() async {
    await Navigator.of(context)
        .push(MaterialPageRoute<void>(builder: (_) => const ScheduleScreen()));
    if (mounted) await _load(silent: true);
  }

  /// "NOVIEMBRE 2026" o, en la vista semanal, "2 – 8 DE NOVIEMBRE".
  String get _rangeLabel {
    if (_mode == CalendarMode.month) {
      return formatMonthYear(_focused).toUpperCase();
    }
    final days = weekDays(_focused);
    final first = days.first;
    final last = days.last;
    final text = first.month == last.month
        ? '${first.day} – ${last.day} de ${formatMonthName(first)}'
        : '${formatShortDate(first)} – ${formatShortDate(last)}';
    return text.toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final items = _items;
    return Scaffold(
      backgroundColor: TaiaColors.ivoryMist,
      body: SafeArea(
        child: items != null
            ? _content(items)
            : _loading
            ? const MascotMessage(
                expression: MascotExpression.thinking,
                text: 'Preparando tu calendario…',
                showSpinner: true,
              )
            : MascotMessage(
                expression: MascotExpression.surprised,
                text: _error ?? 'No se pudo cargar tu calendario.',
                onRetry: _load,
              ),
      ),
    );
  }

  Widget _content(List<AcademicTask> items) {
    final today = dateOnly(bogotaNow());
    final byDay = tasksByDay(items);
    final dayTasks = byDay[_selected] ?? const <AcademicTask>[];
    final dayClasses =
        classesByDay(_classes)[_selected] ?? const <ClassOccurrence>[];

    final MascotExpression expression;
    if (_celebrating) {
      expression = MascotExpression.excited;
    } else if (dayTasks.isEmpty && dayClasses.isEmpty) {
      expression = MascotExpression.happy;
    } else {
      expression = MascotExpression.organizing;
    }

    return RefreshIndicator(
      color: TaiaColors.fieryRose,
      onRefresh: () => _load(silent: true),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _rangeLabel,
                      style: const TextStyle(
                        color: TaiaColors.fieryRose,
                        fontSize: 12,
                        letterSpacing: 1.6,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Tu agenda',
                      style: TextStyle(
                        color: taiaInk,
                        fontSize: 32,
                        height: 1.1,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const NotificationsBell(),
                  CalendarModeToggle(mode: _mode, onChanged: _setMode),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton.icon(
              onPressed: _editSchedule,
              style: TextButton.styleFrom(
                foregroundColor: TaiaColors.fieryRose,
              ),
              icon: const Icon(Icons.edit_calendar_outlined),
              label: const Text('Editar horario'),
            ),
          ),
          const SizedBox(height: 8),
          CalendarCard(
            mode: _mode,
            focused: _focused,
            selected: _selected,
            today: today,
            tasksByDay: byDay,
            onSelect: (day) => setState(() => _selected = day),
            onPrevious: () => _go(-1),
            onNext: () => _go(1),
            onToday: _goToday,
          ),
          if (_mode == CalendarMode.week) ...[
            const SizedBox(height: 16),
            WeekTimeline(
              days: weekDays(_focused),
              classes: _classes,
              tasks: items,
              selected: _selected,
              today: today,
              onSelectDay: (day) => setState(() => _selected = day),
              onTapTask: _edit,
            ).appear(context, index: 1),
          ],
          const SizedBox(height: 24),
          // RNF-14: al cambiar de día, su agenda vuelve a entrar.
          KeyedSubtree(
            key: ValueKey(_selected),
            child: AgendaSection(
              day: _selected,
              today: today,
              tasks: dayTasks,
              classes: dayClasses,
              expression: expression,
              onTapTask: _edit,
            ).appear(context, index: 2),
          ),
        ],
      ),
    );
  }
}
