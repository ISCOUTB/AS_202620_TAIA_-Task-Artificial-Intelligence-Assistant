import 'package:flutter/material.dart';

import '../../core/bogota_time.dart';
import '../../core/spanish_dates.dart';
import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../notifications/notifications_bell.dart';
import '../reminders/reminder_option.dart';
import '../reminders/reminder_rules.dart';
import '../tasks/subject.dart';
import '../tasks/subjects_service.dart';
import '../tasks/task.dart';
import '../tasks/tasks_service.dart';
import '../tasks/widgets/task_form_widgets.dart';
import 'activity_logic.dart';
import 'widgets/activity_success.dart';
import 'widgets/new_subject_dialog.dart';
import 'widgets/quick_date_chips.dart';
import 'widgets/reminder_option_field.dart';

/// Pestaña para añadir una actividad (tarea o examen). Si el usuario aún no
/// tiene materias, puede crear una desde aquí mismo.
class AddActivityScreen extends StatefulWidget {
  const AddActivityScreen({
    super.key,
    this.onSeeTasks,
    this.tasksService,
    this.subjectsService,
  });

  /// Se llama al pulsar "Ver mis tareas" tras crear una actividad.
  final VoidCallback? onSeeTasks;
  final TasksService? tasksService;
  final SubjectsService? subjectsService;

  @override
  State<AddActivityScreen> createState() => AddActivityScreenState();
}

class AddActivityScreenState extends State<AddActivityScreen> {
  final _formKey = GlobalKey<FormState>();
  final _title = TextEditingController();
  final _description = TextEditingController();

  List<Subject>? _subjects;
  String? _subjectsError;
  String? _subjectId;
  String? _subjectFieldError;

  TaskType _type = TaskType.task;
  late DateTime _due = defaultDueDate(bogotaNow());

  // RF-TAR-02: la política por defecto va preseleccionada.
  ReminderMode _reminderMode = ReminderMode.defaults;
  List<DateTime> _customAt = [];

  bool _saving = false;
  String? _error;
  AcademicTask? _created;
  MascotExpression _expression = MascotExpression.wink;

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

  /// Vuelve a pedir las materias (por si se crearon desde otro lado).
  Future<void> refresh() => _loadSubjects();

  Future<void> _loadSubjects() async {
    try {
      final subjects = await _subjectService.list();
      if (!mounted) return;
      setState(() {
        _subjects = subjects;
        _subjectsError = null;
        if (_subjectId != null && !subjects.any((s) => s.id == _subjectId)) {
          _subjectId = null;
        }
        // Con una sola materia no hay nada que elegir.
        if (_subjectId == null && subjects.length == 1) {
          _subjectId = subjects.first.id;
        }
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        if (_subjects == null) _subjectsError = e.message;
      });
    }
  }

  /// Al editar cualquier campo la mascota "piensa" en lo que se está armando.
  void _onEdited() {
    if (_saving || _created != null) return;
    if (_expression == MascotExpression.wink ||
        _expression == MascotExpression.surprised) {
      setState(() => _expression = MascotExpression.thinking);
    }
  }

  Future<void> _newSubject() async {
    final subject = await showNewSubjectDialog(
      context,
      service: _subjectService,
    );
    if (!mounted || subject == null) return;
    setState(() {
      _subjects = [...?_subjects, subject];
      _subjectId = subject.id;
      _subjectFieldError = null;
    });
  }

  Future<void> _pickDue() async {
    final now = bogotaNow();
    final firstDate = DateTime(now.year, now.month, now.day);
    final date = await showDatePicker(
      context: context,
      initialDate: _due.isBefore(firstDate) ? firstDate : _due,
      firstDate: firstDate,
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
      _error = null;
    });
  }

  Future<void> _submit() async {
    final formOk = _formKey.currentState!.validate();
    if (_subjectId == null) {
      setState(() => _subjectFieldError = 'Elige o crea una materia.');
    }
    if (!formOk || _subjectId == null) {
      setState(() => _expression = MascotExpression.surprised);
      return;
    }
    if (!isFutureDue(_due, bogotaNow())) {
      setState(() {
        _error = 'La fecha límite debe ser posterior al momento actual.';
        _expression = MascotExpression.surprised;
      });
      return;
    }
    final reminderError = _reminderError();
    if (reminderError != null) {
      setState(() {
        _error = reminderError;
        _expression = MascotExpression.surprised;
      });
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
      _expression = MascotExpression.thinking;
    });
    try {
      final task = await _tasks.create(
        subjectId: _subjectId!,
        title: _title.text.trim(),
        description: _description.text.trim(),
        dueAt: _due,
        type: _type,
        reminders: ReminderOption(_reminderMode, _customAt),
      );
      if (!mounted) return;
      setState(() {
        _created = task;
        _expression = MascotExpression.excited;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _expression = MascotExpression.surprised;
      });
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  /// Reglas de RF-TAR-02 para las fechas propias: al menos una, como máximo
  /// [maxCustomReminders], y cada una futura y anterior a la fecha límite.
  String? _reminderError() {
    if (_reminderMode != ReminderMode.custom) return null;
    if (_customAt.isEmpty) return 'Agrega al menos una fecha de recordatorio.';
    for (final at in _customAt) {
      final error = reminderTimeError(at, due: _due, now: bogotaNow());
      if (error != null) return error;
    }
    return null;
  }

  /// Limpia el formulario para crear otra actividad (la materia se conserva).
  void _addAnother() {
    _title.clear();
    _description.clear();
    setState(() {
      _created = null;
      _error = null;
      _type = TaskType.task;
      _due = defaultDueDate(bogotaNow());
      _reminderMode = ReminderMode.defaults;
      _customAt = [];
      _expression = MascotExpression.wink;
    });
  }

  bool get _dueInPast => !isFutureDue(_due, bogotaNow());

  @override
  Widget build(BuildContext context) {
    final created = _created;
    return Scaffold(
      backgroundColor: TaiaColors.ivoryMist,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          children: [
            _Header(expression: _expression),
            const SizedBox(height: 20),
            if (created != null)
              ActivitySuccess(
                task: created,
                onAddAnother: _addAnother,
                onSeeTasks: widget.onSeeTasks,
              )
            else
              _form(),
          ],
        ),
      ),
    );
  }

  Widget _form() {
    return Form(
      key: _formKey,
      onChanged: _onEdited,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const FormLabel('¿Qué tipo de actividad es?'),
          TaskSegments<TaskType>(
            value: _type,
            enabled: !_saving,
            options: const {TaskType.task: 'Tarea', TaskType.exam: 'Examen'},
            onChanged: (v) {
              setState(() => _type = v);
              _onEdited();
            },
          ),
          const SizedBox(height: 18),
          const FormLabel('Título'),
          TextFormField(
            controller: _title,
            enabled: !_saving,
            maxLength: 200,
            style: taskValueStyle,
            textCapitalization: TextCapitalization.sentences,
            decoration: taskFieldDecoration(hint: 'Ej. Informe de laboratorio')
                .copyWith(counterText: ''),
            validator: (v) =>
                (v == null || v.trim().isEmpty) ? 'Escribe un título.' : null,
          ),
          const SizedBox(height: 18),
          const FormLabel('Descripción (opcional)'),
          TextFormField(
            controller: _description,
            enabled: !_saving,
            minLines: 3,
            maxLines: 5,
            maxLength: 2000,
            style: taskValueStyle,
            textCapitalization: TextCapitalization.sentences,
            decoration: taskFieldDecoration(
              hint: 'Detalles, páginas, qué hay que entregar…',
            ).copyWith(counterText: ''),
          ),
          const SizedBox(height: 18),
          const FormLabel('Materia'),
          _subjectField(),
          const SizedBox(height: 18),
          const FormLabel('Fecha y hora límite'),
          InkWell(
            borderRadius: BorderRadius.circular(14),
            onTap: _saving ? null : _pickDue,
            child: InputDecorator(
              decoration: taskFieldDecoration(
                suffix: const Icon(
                  Icons.calendar_today_outlined,
                  size: 20,
                  color: taiaInk,
                ),
              ),
              child: Text(formatDateTimeShort(_due), style: taskValueStyle),
            ),
          ),
          const SizedBox(height: 10),
          QuickDateChips(
            due: _due,
            enabled: !_saving,
            onChanged: (due) {
              setState(() {
                _due = due;
                _error = null;
              });
              _onEdited();
            },
          ),
          if (_dueInPast)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                'Esa hora ya pasó: elige una fecha límite futura.',
                style: TextStyle(color: Colors.red.shade700, fontSize: 12),
              ),
            ),
          const SizedBox(height: 18),
          const FormLabel('Recordatorios'),
          ReminderOptionField(
            mode: _reminderMode,
            customAt: _customAt,
            due: _due,
            enabled: !_saving,
            onModeChanged: (mode) {
              setState(() {
                _reminderMode = mode;
                _error = null;
              });
              _onEdited();
            },
            onCustomChanged: (dates) {
              setState(() {
                _customAt = dates;
                _error = null;
              });
              _onEdited();
            },
          ),
          const SizedBox(height: 28),
          if (_error != null) AuthErrorText(_error!),
          AuthSubmitButton(
            label: 'Crear actividad',
            loading: _saving,
            onPressed: _submit,
          ),
        ],
      ),
    );
  }

  Widget _subjectField() {
    final subjects = _subjects;
    if (_subjectsError != null && subjects == null) {
      return Row(
        children: [
          Expanded(
            child: Text(
              _subjectsError!,
              style: TextStyle(color: Colors.red.shade700),
            ),
          ),
          TextButton(onPressed: _loadSubjects, child: const Text('Reintentar')),
        ],
      );
    }
    if (subjects == null) {
      return InputDecorator(
        decoration: taskFieldDecoration(),
        child: Row(
          children: [
            const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: TaiaColors.fieryRose,
              ),
            ),
            const SizedBox(width: 10),
            Text(
              'Cargando tus materias…',
              style: TextStyle(color: taiaInk.withValues(alpha: 0.6)),
            ),
          ],
        ),
      );
    }
    if (subjects.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.6),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: TaiaColors.softPeach, width: 1.5),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Aún no tienes materias. Crea la primera para organizar tus '
              'actividades.',
              style: TextStyle(color: taiaInk),
            ),
            const SizedBox(height: 10),
            FilledButton.icon(
              style: FilledButton.styleFrom(
                backgroundColor: TaiaColors.fieryRose,
              ),
              onPressed: _saving ? null : _newSubject,
              icon: const Icon(Icons.add),
              label: const Text('Crear mi primera materia'),
            ),
            if (_subjectFieldError != null) ...[
              const SizedBox(height: 8),
              Text(
                _subjectFieldError!,
                style: TextStyle(color: Colors.red.shade700, fontSize: 12),
              ),
            ],
          ],
        ),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        DropdownButtonFormField<String>(
          key: ValueKey('${subjects.length}-$_subjectId'),
          initialValue: _subjectId,
          isExpanded: true,
          style: taskValueStyle,
          hint: Text(
            'Elige una materia',
            style: TextStyle(color: taiaInk.withValues(alpha: 0.4)),
          ),
          decoration: taskFieldDecoration(),
          items: [
            for (final subject in subjects)
              DropdownMenuItem(
                value: subject.id,
                child: Text(subject.name, overflow: TextOverflow.ellipsis),
              ),
          ],
          onChanged: _saving
              ? null
              : (id) {
                  setState(() {
                    _subjectId = id;
                    _subjectFieldError = null;
                  });
                  _onEdited();
                },
        ),
        if (_subjectFieldError != null)
          Padding(
            padding: const EdgeInsets.only(top: 6, left: 4),
            child: Text(
              _subjectFieldError!,
              style: TextStyle(color: Colors.red.shade700, fontSize: 12),
            ),
          ),
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton.icon(
            style: TextButton.styleFrom(foregroundColor: TaiaColors.fieryRose),
            onPressed: _saving ? null : _newSubject,
            icon: const Icon(Icons.add, size: 18),
            label: const Text(
              'Nueva materia',
              style: TextStyle(fontWeight: FontWeight.w800),
            ),
          ),
        ),
      ],
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.expression});

  final MascotExpression expression;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'NUEVA ACTIVIDAD',
                style: TextStyle(
                  color: TaiaColors.fieryRose,
                  fontSize: 12,
                  letterSpacing: 1.6,
                  fontWeight: FontWeight.w800,
                ),
              ),
              SizedBox(height: 4),
              Text(
                '¿Qué vamos a organizar?',
                style: TextStyle(
                  color: taiaInk,
                  fontSize: 30,
                  height: 1.1,
                  fontWeight: FontWeight.w900,
                ),
              ),
              SizedBox(height: 6),
              Text(
                'Cuéntame los detalles y yo me encargo del resto.',
                style: TextStyle(color: Color(0xA63B2A2A), fontSize: 14),
              ),
            ],
          ),
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            const NotificationsBell(),
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
