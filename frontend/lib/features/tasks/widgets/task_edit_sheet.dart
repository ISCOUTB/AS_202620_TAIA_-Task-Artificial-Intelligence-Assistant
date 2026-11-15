import 'package:flutter/material.dart';

import '../../../core/spanish_dates.dart';
import '../../../mascot/mascot_expression.dart';
import '../../../mascot/taia_mascot.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_service.dart';
import '../../auth/auth_shell.dart';
import '../subject.dart';
import '../subjects_service.dart';
import '../task.dart';
import '../tasks_service.dart';

/// Resultado de la hoja: la tarea guardada o el aviso de que se eliminó.
class TaskEditResult {
  const TaskEditResult.saved(this.task) : deleted = false;
  const TaskEditResult.deleted() : task = null, deleted = true;

  final AcademicTask? task;
  final bool deleted;
}

/// Abre la hoja de edición sobre la pantalla actual.
Future<TaskEditResult?> showTaskEditSheet(
  BuildContext context,
  AcademicTask task, {
  TasksService? tasksService,
  SubjectsService? subjectsService,
}) {
  return showModalBottomSheet<TaskEditResult>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    backgroundColor: TaiaColors.ivoryMist,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (context) => TaskEditSheet(
      task: task,
      tasksService: tasksService,
      subjectsService: subjectsService,
    ),
  );
}

InputDecoration _fieldDecoration({Widget? suffix}) {
  OutlineInputBorder border(Color color, [double width = 1.5]) =>
      OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: color, width: width),
      );
  return InputDecoration(
    filled: true,
    fillColor: Colors.white,
    suffixIcon: suffix,
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
    border: border(TaiaColors.softPeach),
    enabledBorder: border(TaiaColors.softPeach),
    focusedBorder: border(TaiaColors.fieryRose, 2),
    errorBorder: border(Colors.red.shade400),
    focusedErrorBorder: border(Colors.red.shade400, 2),
  );
}

const TextStyle _valueStyle = TextStyle(
  color: taiaInk,
  fontWeight: FontWeight.w700,
  fontSize: 15,
);

class TaskEditSheet extends StatefulWidget {
  const TaskEditSheet({
    super.key,
    required this.task,
    this.tasksService,
    this.subjectsService,
  });

  final AcademicTask task;
  final TasksService? tasksService;
  final SubjectsService? subjectsService;

  @override
  State<TaskEditSheet> createState() => _TaskEditSheetState();
}

class _TaskEditSheetState extends State<TaskEditSheet> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _title = TextEditingController(
    text: widget.task.title,
  );
  late final TextEditingController _description = TextEditingController(
    text: widget.task.description ?? '',
  );
  late String _subjectId = widget.task.subjectId;
  late DateTime _due = widget.task.dueAt;
  late TaskType _type = widget.task.type;
  late bool _completed = widget.task.status == TaskStatus.completed;

  List<Subject>? _subjects;
  bool _busy = false;
  String? _error;
  MascotExpression _expression = MascotExpression.studying;

  TasksService get _tasks => widget.tasksService ?? tasksService;
  SubjectsService get _subjectService =>
      widget.subjectsService ?? subjectsService;

  @override
  void initState() {
    super.initState();
    _loadSubjects();
  }

  @override
  void dispose() {
    _title.dispose();
    _description.dispose();
    super.dispose();
  }

  Future<void> _loadSubjects() async {
    try {
      final subjects = await _subjectService.list();
      if (mounted) setState(() => _subjects = subjects);
    } on ApiException {
      // Sin la lista, se deja solo la materia actual de la tarea.
      if (mounted) setState(() => _subjects = const []);
    }
  }

  /// Las materias del usuario; si la actual ya no está (por ejemplo, archivada)
  /// se agrega para que el selector no quede sin valor.
  List<Subject> get _subjectOptions {
    final options = [...?_subjects];
    if (!options.any((s) => s.id == widget.task.subjectId)) {
      options.insert(
        0,
        Subject(id: widget.task.subjectId, name: widget.task.subjectName),
      );
    }
    return options;
  }

  Future<void> _pickDue() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _due,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_due),
    );
    if (time == null || !mounted) return;
    setState(() {
      _due = DateTime(date.year, date.month, date.day, time.hour, time.minute);
    });
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) {
      setState(() => _expression = MascotExpression.surprised);
      return;
    }
        // El backend exige una fecha futura; solo se envía si el usuario la cambió.
    final dueChanged = _due != widget.task.dueAt;
    if (dueChanged && !_due.isAfter(DateTime.now())) {
      setState(() {
        _error = 'La fecha límite debe ser posterior al momento actual.';
        _expression = MascotExpression.surprised;
      });
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
      _expression = MascotExpression.thinking;
    });
    try {
      var updated = await _tasks.update(
        widget.task.id,
        title: _title.text.trim(),
        description: _description.text.trim(),
        subjectId: _subjectId,
        dueAt: dueChanged ? _due : null,
        type: _type,
      );
      final wasCompleted = widget.task.status == TaskStatus.completed;
      if (_completed && !wasCompleted) {
        updated = await _tasks.complete(widget.task.id);
      } else if (!_completed && wasCompleted) {
        updated = await _tasks.reopen(widget.task.id);
      }
      if (!mounted) return;
      Navigator.of(context).pop(TaskEditResult.saved(updated));
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _expression = MascotExpression.surprised;
      });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _delete() async {
    setState(() => _expression = MascotExpression.surprised);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('¿Eliminar esta tarea?'),
        content: Text(
          'Se eliminará "${widget.task.title}". Esta acción no se puede '
          'deshacer.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: TaiaColors.fieryRose,
            ),
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
    if (!mounted) return;
    if (confirmed != true) {
      setState(() => _expression = MascotExpression.studying);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await _tasks.delete(widget.task.id);
      if (!mounted) return;
      Navigator.of(context).pop(const TaskEditResult.deleted());
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  static String _priorityLabel(String priority) => switch (priority) {
    'high' => 'Alta',
    'medium' => 'Media',
    _ => 'Baja',
  };

  @override
  Widget build(BuildContext context) {
    final priority = widget.task.priority;
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'EDITAR TAREA',
                          style: TextStyle(
                            color: TaiaColors.fieryRose,
                            fontSize: 12,
                            letterSpacing: 1.6,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          'Revisemos tu tarea',
                          style: TextStyle(
                            color: taiaInk,
                            fontSize: 28,
                            height: 1.1,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    width: 70,
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: TaiaColors.fieryRose,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: TaiaMascot(motion: 0.5, expression: _expression),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    tooltip: 'Cerrar',
                    onPressed: _busy ? null : () => Navigator.of(context).pop(),
                    style: IconButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: taiaInk,
                    ),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              const _Label('Título'),
              TextFormField(
                controller: _title,
                enabled: !_busy,
                maxLength: 200,
                style: _valueStyle,
                textCapitalization: TextCapitalization.sentences,
                decoration: _fieldDecoration().copyWith(counterText: ''),
                validator: (v) => (v == null || v.trim().isEmpty)
                    ? 'Escribe un título.'
                    : null,
              ),
              const SizedBox(height: 16),
              const _Label('Descripción'),
              TextFormField(
                controller: _description,
                enabled: !_busy,
                minLines: 3,
                maxLines: 5,
                maxLength: 2000,
                style: _valueStyle,
                textCapitalization: TextCapitalization.sentences,
                decoration: _fieldDecoration().copyWith(counterText: ''),
              ),
              const SizedBox(height: 16),
              const _Label('Materia'),
              DropdownButtonFormField<String>(
                key: ValueKey(_subjects == null),
                initialValue: _subjectId,
                isExpanded: true,
                style: _valueStyle,
                decoration: _fieldDecoration(),
                items: [
                  for (final subject in _subjectOptions)
                    DropdownMenuItem(
                      value: subject.id,
                      child: Text(subject.name, overflow: TextOverflow.ellipsis),
                    ),
                ],
                onChanged: _busy || _subjects == null
                    ? null
                    : (id) => setState(() => _subjectId = id ?? _subjectId),
              ),
              const SizedBox(height: 16),
              const _Label('Fecha y hora límite'),
              InkWell(
                borderRadius: BorderRadius.circular(14),
                onTap: _busy ? null : _pickDue,
                child: InputDecorator(
                  decoration: _fieldDecoration(
                    suffix: const Icon(
                      Icons.calendar_today_outlined,
                      size: 20,
                      color: taiaInk,
                    ),
                  ),
                  child: Text(formatDateTimeShort(_due), style: _valueStyle),
                ),
              ),
              const SizedBox(height: 16),
              const _Label('Tipo'),
              _Segments<TaskType>(
                value: _type,
                enabled: !_busy,
                options: const {
                  TaskType.task: 'Tarea',
                  TaskType.exam: 'Examen',
                },
                onChanged: (v) => setState(() => _type = v),
              ),
              const SizedBox(height: 16),
              const _Label('Estado'),
              _Segments<bool>(
                value: _completed,
                enabled: !_busy,
                options: const {false: 'Pendiente', true: 'Completada'},
                onChanged: (v) => setState(() => _completed = v),
              ),
              if (priority != null) ...[
                const SizedBox(height: 16),
                Row(
                  children: [
                    const Text(
                      'Prioridad',
                      style: TextStyle(
                        color: taiaInk,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 5,
                      ),
                      decoration: BoxDecoration(
                        color: TaiaColors.softPeach,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        _priorityLabel(priority),
                        style: const TextStyle(
                          color: taiaInk,
                          fontWeight: FontWeight.w800,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  'Se calcula sola según la fecha límite.',
                  style: TextStyle(
                    color: taiaInk.withValues(alpha: 0.6),
                    fontSize: 12,
                  ),
                ),
              ],
              const SizedBox(height: 24),
              if (_error != null) AuthErrorText(_error!),
              AuthSubmitButton(
                label: 'Guardar cambios',
                loading: _busy,
                onPressed: _save,
              ),
              const SizedBox(height: 4),
              TextButton.icon(
                style: TextButton.styleFrom(
                  foregroundColor: Colors.red.shade700,
                ),
                onPressed: _busy ? null : _delete,
                icon: const Icon(Icons.delete_outline),
                label: const Text('Eliminar tarea'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Label extends StatelessWidget {
  const _Label(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        text,
        style: const TextStyle(
          color: taiaInk,
          fontSize: 14,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

/// Selector de una opción entre pocas, con el estilo de la marca.
class _Segments<T> extends StatelessWidget {
  const _Segments({
    required this.value,
    required this.options,
    required this.onChanged,
    required this.enabled,
  });

  final T value;
  final Map<T, String> options;
  final ValueChanged<T> onChanged;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return SegmentedButton<T>(
      showSelectedIcon: false,
      expandedInsets: EdgeInsets.zero,
      segments: [
        for (final entry in options.entries)
          ButtonSegment<T>(value: entry.key, label: Text(entry.value)),
      ],
      selected: {value},
      onSelectionChanged: enabled ? (s) => onChanged(s.first) : null,
      style: SegmentedButton.styleFrom(
        backgroundColor: Colors.white,
        foregroundColor: taiaInk,
        selectedBackgroundColor: TaiaColors.fieryRose,
        selectedForegroundColor: Colors.white,
        side: const BorderSide(color: TaiaColors.softPeach, width: 1.5),
      ),
    );
  }
}