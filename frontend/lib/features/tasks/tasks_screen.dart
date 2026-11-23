import '../agent/taia_chat_button.dart';
import '../study_plan/study_plan_card.dart';

import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/bogota_time.dart';
import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../notifications/notifications_bell.dart';
import 'subjects_service.dart';
import 'task.dart';
import 'task_filters.dart';
import 'tasks_service.dart';
import 'widgets/task_edit_sheet.dart';
import 'widgets/task_tile.dart';
import 'widgets/tasks_filter_bar.dart';

/// Pestaña de tareas: lista agrupada por día, con búsqueda y filtros. Al tocar
/// una tarea se abre la hoja de edición. El servidor filtra y pagina
/// (RF-TAR-04, H-15); la app pide más páginas al llegar al final.
class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key, this.tasksService, this.subjectsService});

  final TasksService? tasksService;
  final SubjectsService? subjectsService;

  @override
  State<TasksScreen> createState() => TasksScreenState();
}

/// Tamaño de cada página que se pide al servidor (máximo 100, RF-TAR-04).
const tasksPageSize = 50;

class TasksScreenState extends State<TasksScreen> {
  List<AcademicTask>? _items;
  String? _error;
  bool _loading = true;
  int _total = 0;
  int _unfinished = 0;
  bool _loadingMore = false;
  Timer? _searchDebounce;
  // Cada carga lleva un número: una respuesta vieja no pisa a una nueva.
  int _generation = 0;

  final _search = TextEditingController();
  TaskFilter _status = TaskFilter.pending;
  DateFilter _date = DateFilter.any;
  DateTime? _pickedDay;

  final Set<String> _busy = {};
  bool _celebrating = false;
  Timer? _celebrationTimer;

  TasksService get _tasks => widget.tasksService ?? tasksService;
  SubjectsService get _subjects => widget.subjectsService ?? subjectsService;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    _celebrationTimer?.cancel();
    _searchDebounce?.cancel();
    super.dispose();
  }

  TaskListQuery get _query => taskQueryFor(
    status: _status,
    search: _search.text,
    date: _date,
    pickedDay: _pickedDay,
    now: bogotaNow(),
  );

  Future<TaskPage> _fetch(int offset) {
    final query = _query;
    return _tasks.list(
      statuses: query.statuses,
      dueFrom: query.dueFrom,
      dueTo: query.dueTo,
      query: query.text,
      limit: tasksPageSize,
      offset: offset,
    );
  }

  /// Pendientes y atrasadas, para el encabezado: solo interesa el total.
  Future<int> _countUnfinished() async {
    final page = await _tasks.list(
      statuses: const [TaskStatus.pending, TaskStatus.overdue],
      limit: 1,
    );
    return page.total;
  }

  /// Cambió un filtro: se vuelve a pedir la primera página.
  void _filtersChanged(VoidCallback change) {
    setState(change);
    _load(silent: _items != null);
  }

  /// La búsqueda espera a que se deje de escribir para no pedir por cada letra.
  void _searchChanged() {
    _searchDebounce?.cancel();
    _searchDebounce = Timer(
      const Duration(milliseconds: 350),
      () => _load(silent: _items != null),
    );
  }

  Future<void> _loadMore() async {
    final items = _items;
    if (_loadingMore || items == null || items.length >= _total) return;
    final generation = _generation;
    setState(() => _loadingMore = true);
    try {
      final page = await _fetch(items.length);
      if (!mounted || generation != _generation) return;
      setState(() {
        _items = [...items, ...page.items];
        _total = page.total;
      });
    } on ApiException catch (e) {
      if (mounted) _toast(e.message);
    } finally {
      if (mounted) setState(() => _loadingMore = false);
    }
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
    final generation = ++_generation;
    try {
      final (page, unfinished) = await (_fetch(0), _countUnfinished()).wait;
      if (!mounted || generation != _generation) return;
      setState(() {
        _items = page.items;
        _total = page.total;
        _unfinished = unfinished;
        _error = null;
        _loading = false;
      });
    } on ParallelWaitError<
      (TaskPage?, int?),
      (AsyncError?, AsyncError?)
    > catch (e) {
      final error = e.errors.$1?.error ?? e.errors.$2?.error;
      if (!mounted || generation != _generation) return;
      setState(() {
        if (_items == null) {
          _error = error is ApiException
              ? error.message
              : 'No se pudieron cargar tus tareas.';
        }
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!mounted || generation != _generation) return;
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
      unawaited(refresh());
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
      unawaited(refresh());
      return;
    }
    final saved = result.task!;
    _replace(saved);
    _toast('Cambios guardados');
    unawaited(refresh());
    if (saved.status == TaskStatus.completed &&
        task.status != TaskStatus.completed) {
      _celebrate();
    }
  }

  bool get _hasActiveFilters =>
      _search.text.trim().isNotEmpty || _date != DateFilter.any;

  void _clearFilters() {
    _search.clear();
    _filtersChanged(() {
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
    final visible = items;
    final groups = groupTasks(visible, now);
    final unfinished = _unfinished;

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
          _Header(unfinished: unfinished, expression: expression),
          const SizedBox(height: 16),
          // RNF-14: el plan de estudio también se abre desde Tareas.
          const StudyPlanCard(),
          const SizedBox(height: 20),
          TasksFilterBar(
            searchController: _search,
            onSearchChanged: (_) => _searchChanged(),
            dateFilter: _date,
            pickedDay: _pickedDay,
            onDateChanged: (filter, day) => _filtersChanged(() {
              _date = filter;
              _pickedDay = day;
            }),
            status: _status,
            onStatusChanged: (filter) =>
                _filtersChanged(() => _status = filter),
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
          if (items.length < _total)
            Center(
              child: _loadingMore
                  ? const Padding(
                      padding: EdgeInsets.all(12),
                      child: CircularProgressIndicator(),
                    )
                  : TextButton(
                      onPressed: _loadMore,
                      child: Text('Ver más (${_total - items.length})'),
                    ),
            ),
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.unfinished, required this.expression});

  final int unfinished;
  final MascotExpression expression;

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
            const NotificationsBell(),
            TaiaChatButton(expression: expression, size: 84),
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
            SizedBox(
              width: 168,
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
