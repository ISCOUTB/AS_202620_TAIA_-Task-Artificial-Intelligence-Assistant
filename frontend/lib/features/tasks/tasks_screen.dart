import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/bogota_time.dart';
import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../home/widgets/notifications_sheet.dart';
import '../reminders/reminders_service.dart';
import 'subjects_service.dart';
import 'task.dart';
import 'task_filters.dart';
import 'tasks_service.dart';
import 'widgets/task_edit_sheet.dart';
import 'widgets/task_tile.dart';
import 'widgets/tasks_filter_bar.dart';

/// Pestaña de tareas: lista agrupada por día, con búsqueda y filtros. Al tocar
/// una tarea se abre la hoja de edición.
class TasksScreen extends StatefulWidget {
  const TasksScreen({
    super.key,
    this.tasksService,
    this.subjectsService,
    this.remindersService,
  });

  final TasksService? tasksService;
  final SubjectsService? subjectsService;
  final RemindersService? remindersService;

  @override
  State<TasksScreen> createState() => TasksScreenState();
}

class TasksScreenState extends State<TasksScreen> {
  List<AcademicTask>? _items;
  String? _error;
  bool _loading = true;

  final _search = TextEditingController();
  TaskFilter _status = TaskFilter.pending;
  DateFilter _date = DateFilter.any;
  DateTime? _pickedDay;

  final Set<String> _busy = {};
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
    _search.dispose();
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

  void _replace(AcademicTask updated) {
    setState(() {
      _items = [
        for (final t in _items ?? <AcademicTask>[])
          t.id == updated.id ? updated : t,
      ];
    });
  }

  void _celebrate() {
    _celebrationTimer?.cancel();
    setState(() => _celebrating = true);
    _celebrationTimer = Timer(const Duration(milliseconds: 2200), () {
      if (mounted) setState(() => _celebrating = false);
    });
  }

  Future<void> _toggle(AcademicTask task) async {
    if (_busy.contains(task.id)) return;
    setState(() => _busy.add(task.id));
    try {
      final updated = task.status == TaskStatus.completed
          ? await _tasks.reopen(task.id)
          : await _tasks.complete(task.id);
      if (!mounted) return;
      _replace(updated);
      if (updated.status == TaskStatus.completed) _celebrate();
    } on ApiException catch (e) {
      if (mounted) _toast(e.message);
    } finally {
      if (mounted) setState(() => _busy.remove(task.id));
    }
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
    _replace(saved);
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
      final pending = all.where((r) => r.isPending).toList()
        ..sort((a, b) => a.scheduledAt.compareTo(b.scheduledAt));
      await showNotificationsSheet(context, pending);
    } on ApiException catch (e) {
      if (mounted) _toast(e.message);
    }
  }

  bool get _hasActiveFilters =>
      _search.text.trim().isNotEmpty || _date != DateFilter.any;

  void _clearFilters() {
    _search.clear();
    setState(() {
      _date = DateFilter.any;
      _pickedDay = null;
      _status = TaskFilter.all;
    });
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
            ? const _Message(
                expression: MascotExpression.thinking,
                text: 'Buscando tus tareas…',
                showSpinner: true,
              )
            : _Message(
                expression: MascotExpression.surprised,
                text: _error ?? 'No se pudieron cargar tus tareas.',
                onRetry: _load,
              ),
      ),
    );
  }

  Widget _content(List<AcademicTask> items) {
    final now = bogotaNow();
    final visible = applyTaskFilters(
      items,
      status: _status,
      search: _search.text,
      date: _date,
      pickedDay: _pickedDay,
      now: now,
    );
    final groups = groupTasks(visible, now);
    final unfinished = unfinishedCount(items);

    final MascotExpression expression;
    if (_celebrating) {
      expression = MascotExpression.excited;
    } else if (visible.isEmpty) {
      expression = _hasActiveFilters
          ? MascotExpression.thinking
          : MascotExpression.happy;
    } else {
      expression = MascotExpression.studying;
    }

    return RefreshIndicator(
      color: TaiaColors.fieryRose,
      onRefresh: () => _load(silent: true),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          _Header(
            unfinished: unfinished,
            expression: expression,
            onBell: _openReminders,
          ),
          const SizedBox(height: 20),
          TasksFilterBar(
            searchController: _search,
            onSearchChanged: (_) => setState(() {}),
            dateFilter: _date,
            pickedDay: _pickedDay,
            onDateChanged: (filter, day) => setState(() {
              _date = filter;
              _pickedDay = day;
            }),
            status: _status,
            onStatusChanged: (filter) => setState(() => _status = filter),
          ),
          const SizedBox(height: 16),
          if (groups.isEmpty)
            _EmptyState(
              filtered: _hasActiveFilters,
              status: _status,
              onClear: _clearFilters,
            )
          else
            for (final group in groups) ...[
              _GroupHeader(title: group.title, count: group.tasks.length),
              const SizedBox(height: 8),
              for (final task in group.tasks) ...[
                TaskTile(
                  task: task,
                  busy: _busy.contains(task.id),
                  onTap: () => _edit(task),
                  onToggle: () => _toggle(task),
                ),
                const SizedBox(height: 10),
              ],
              const SizedBox(height: 8),
            ],
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({
    required this.unfinished,
    required this.expression,
    required this.onBell,
  });

  final int unfinished;
  final MascotExpression expression;
  final VoidCallback onBell;

  @override
  Widget build(BuildContext context) {
    final subtitle = unfinished == 0
        ? 'No tienes pendientes por resolver'
        : unfinished == 1
        ? '1 pendiente por resolver'
        : '$unfinished pendientes por resolver';
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'TU LISTA',
                style: TextStyle(
                  color: TaiaColors.fieryRose,
                  fontSize: 12,
                  letterSpacing: 1.6,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Mis tareas',
                style: TextStyle(
                  color: taiaInk,
                  fontSize: 32,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: TextStyle(
                  color: taiaInk.withValues(alpha: 0.65),
                  fontSize: 14,
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
              onPressed: onBell,
              icon: const Icon(Icons.notifications_none_rounded),
            ),
            Container(
              width: 84,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: TaiaColors.fieryRose,
                borderRadius: BorderRadius.circular(24),
              ),
              child: TaiaMascot(motion: 0.6, expression: expression),
            ),
          ],
        ),
      ],
    );
  }
}

class _GroupHeader extends StatelessWidget {
  const _GroupHeader({required this.title, required this.count});

  final String title;
  final int count;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(
          title,
          style: const TextStyle(
            color: taiaInk,
            fontSize: 18,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(width: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 2),
          decoration: BoxDecoration(
            color: TaiaColors.softPeach,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(
            '$count',
            style: const TextStyle(
              color: taiaInk,
              fontSize: 12,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
      ],
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.filtered,
    required this.status,
    required this.onClear,
  });

  final bool filtered;
  final TaskFilter status;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final message = filtered
        ? 'No encontré tareas con esa búsqueda.'
        : switch (status) {
            TaskFilter.pending => '¡Todo al día! No tienes tareas pendientes.',
            TaskFilter.completed => 'Aún no has completado tareas.',
            TaskFilter.overdue => 'No tienes tareas atrasadas. ¡Bien hecho!',
            TaskFilter.urgent => 'Nada urgente por ahora. Puedes respirar.',
            TaskFilter.all =>
              'Todavía no tienes tareas. Crea una en la pestaña Añadir.',
          };
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: TaiaColors.softPeach),
      ),
      child: Column(
        children: [
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: taiaInk,
              fontSize: 15,
              fontWeight: FontWeight.w700,
            ),
          ),
          if (filtered) ...[
            const SizedBox(height: 12),
            TextButton(
              style: TextButton.styleFrom(
                foregroundColor: TaiaColors.fieryRose,
              ),
              onPressed: onClear,
              child: const Text('Limpiar filtros'),
            ),
          ],
        ],
      ),
    );
  }
}

/// Estado de carga o de error, con la mascota.
class _Message extends StatelessWidget {
  const _Message({
    required this.expression,
    required this.text,
    this.showSpinner = false,
    this.onRetry,
  });

  final MascotExpression expression;
  final String text;
  final bool showSpinner;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 200,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: TaiaColors.fieryRose,
                borderRadius: BorderRadius.circular(32),
              ),
              child: TaiaMascot(motion: 0.6, expression: expression),
            ),
            const SizedBox(height: 16),
            Text(
              text,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: taiaInk,
                fontSize: 16,
                fontWeight: FontWeight.w700,
              ),
            ),
            if (showSpinner) ...[
              const SizedBox(height: 16),
              const CircularProgressIndicator(color: TaiaColors.fieryRose),
            ],
            if (onRetry != null) ...[
              const SizedBox(height: 16),
              FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: TaiaColors.fieryRose,
                ),
                onPressed: onRetry,
                child: const Text('Reintentar'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}