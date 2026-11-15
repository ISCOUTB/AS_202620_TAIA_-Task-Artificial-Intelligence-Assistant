import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/spanish_dates.dart';
import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../home/widgets/notifications_sheet.dart';
import '../reminders/reminders_service.dart';
import '../shell/mascot_message.dart';
import '../tasks/subjects_service.dart';
import '../tasks/task.dart';
import '../tasks/tasks_service.dart';
import '../tasks/widgets/task_edit_sheet.dart';
import 'calendar_logic.dart';
import 'widgets/agenda_section.dart';
import 'widgets/calendar_card.dart';
import 'widgets/calendar_mode_toggle.dart';

/// Pestaña de calendario: vista por mes o por semana. Al elegir un día se ven
/// sus actividades, y al tocar una se abre la hoja de edición.
class CalendarScreen extends StatefulWidget {
  const CalendarScreen({
    super.key,
    this.tasksService,
    this.subjectsService,
    this.remindersService,
  });

  final TasksService? tasksService;
  final SubjectsService? subjectsService;
  final RemindersService? remindersService;

  @override
  State<CalendarScreen> createState() => CalendarScreenState();
}

class CalendarScreenState extends State<CalendarScreen> {
  List<AcademicTask>? _items;
  String? _error;
  bool _loading = true;

  CalendarMode _mode = CalendarMode.month;
  late DateTime _selected = dateOnly(DateTime.now());
  late DateTime _focused = _selected;

  bool _celebrating = false;
  Timer? _celebrationTimer;

  TasksService get _tasks => widget.tasksService ?? tasksService;
  SubjectsService get _subjects => widget.subjectsService ?? subjectsService;
  RemindersService get _reminders =>
      widget.remindersService ?? remindersService;

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

  /// Vuelve a pedir las tareas sin ocultar las que ya se muestran.
  Future<void> refresh() => _load(silent: _items != null);

  Future<void> _load({bool silent = false}) async {
    if (!silent) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final items = await _tasks.listAll();
      if (!mounted) return;
      setState(() {
        _items = items;
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

  void _setMode(CalendarMode mode) {
    if (mode == _mode) return;
    setState(() {
      _mode = mode;
      _focused = _selected;
    });
  }

  /// Avanza ([delta] = 1) o retrocede ([delta] = -1) un mes o una semana y deja
  /// seleccionado el día de hoy (si está a la vista) o el primer día.
  void _go(int delta) {
    final today = dateOnly(DateTime.now());
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
  }

  void _goToday() {
    final today = dateOnly(DateTime.now());
    setState(() {
      _selected = today;
      _focused = today;
    });
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

  Future<void> _openReminders() async {
    try {
      final all = await _reminders.list();
      if (!mounted) return;
      final pending = all.where((r) => !r.isCompleted).toList()
        ..sort((a, b) => a.scheduledAt.compareTo(b.scheduledAt));
      await showNotificationsSheet(context, pending);
    } on ApiException catch (e) {
      if (mounted) _toast(e.message);
    }
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
    final today = dateOnly(DateTime.now());
    final byDay = tasksByDay(items);
    final dayTasks = byDay[_selected] ?? const <AcademicTask>[];

    final MascotExpression expression;
    if (_celebrating) {
      expression = MascotExpression.excited;
    } else if (dayTasks.isEmpty) {
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
                      'Tu calendario',
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
                  IconButton(
                    tooltip: 'Recordatorios',
                    iconSize: 28,
                    color: taiaInk,
                    onPressed: _openReminders,
                    icon: const Icon(Icons.notifications_none_rounded),
                  ),
                  CalendarModeToggle(mode: _mode, onChanged: _setMode),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
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
          const SizedBox(height: 24),
          AgendaSection(
            day: _selected,
            today: today,
            tasks: dayTasks,
            expression: expression,
            onTapTask: _edit,
          ),
        ],
      ),
    );
  }
}