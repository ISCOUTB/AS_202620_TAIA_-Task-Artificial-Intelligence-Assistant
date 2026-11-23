import 'package:flutter/material.dart';

import '../../core/bogota_time.dart';
import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../agent/taia_chat_button.dart';
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
import 'widgets/activity_form_widgets.dart';
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

  /// La descripción es opcional: se abre con "Añadir detalles" (RNF-14).
  bool _showDetails = false;

  TasksService get _tasks => widget.tasksService ?? tasksService;
  SubjectsService get _subjectService =>
      widget.subjectsService ?? subjectsService;

  @override
  void initState() {
    super.initState();
    _loadSubjects();
    // El resumen en vivo sigue lo que se escribe en el título.
    _title.addListener(_titleChanged);
  }

  void _titleChanged() => setState(() {});

  String? get _subjectName {
    final id = _subjectId;
    if (id == null) return null;
    for (final s in _subjects ?? const <Subject>[]) {
      if (s.id == id) return s.name;
    }
    return null;
  }

  void _useSuggestion(String word) {
    final title = suggestedTitle(word, _subjectName);
    _title.value = TextEditingValue(
      text: title,
      selection: TextSelection.collapsed(offset: title.length),
    );
    _onEdited();
  }

  void _setDue(DateTime due) {
    setState(() {
      _due = due;
      _error = null;
    });
    _onEdited();
  }

  Future<void> _pickTime() async {
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_due),
    );
    if (time == null || !mounted) return;
    _setDue(withTime(_due, time.hour, time.minute));
  }

  @override
  void dispose() {
    _title.removeListener(_titleChanged);
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
    final suggestionSubject = _subjectName;
    return Form(
      key: _formKey,
      onChanged: _onEdited,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const FormLabel('¿Qué vas a registrar?'),
          ActivityTypeCards(
            value: _type,
            enabled: !_saving,
            onChanged: (v) {
              setState(() => _type = v);
              _onEdited();
            },
          ),
          const SizedBox(height: 18),
          const FormLabel('Materia'),
          _subjectField(),
          const SizedBox(height: 18),
          const FormLabel('Título'),
          TextFormField(
            controller: _title,
            enabled: !_saving,
            maxLength: 200,
            style: taskValueStyle,
            textCapitalization: TextCapitalization.sentences,
            decoration: taskFieldDecoration(
              hint: _type == TaskType.exam
                  ? 'Ej. Parcial de cálculo'
                  : 'Ej. Informe de laboratorio',
            ).copyWith(counterText: ''),
            validator: (v) =>
                (v == null || v.trim().isEmpty) ? 'Escribe un título.' : null,
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 4,
            children: [
              for (final word in titleSuggestions(_type))
                TaiaChoiceChip(
                  label: word,
                  selected:
                      _title.text == suggestedTitle(word, suggestionSubject),
                  onSelected: _saving ? null : () => _useSuggestion(word),
                ),
            ],
          ),
          AnimatedSize(
            duration: const Duration(milliseconds: 200),
            alignment: Alignment.topCenter,
            child: _showDetails
                ? Padding(
                    padding: const EdgeInsets.only(top: 14),
                    child: TextFormField(
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
                  )
                : Align(
                    alignment: Alignment.centerLeft,
                    child: TextButton.icon(
                      style: TextButton.styleFrom(
                        foregroundColor: TaiaColors.fieryRose,
                      ),
                      onPressed: _saving
                          ? null
                          : () => setState(() => _showDetails = true),
                      icon: const Icon(Icons.add, size: 18),
                      label: const Text(
                        'Añadir detalles',
                        style: TextStyle(fontWeight: FontWeight.w800),
                      ),
                    ),
                  ),
          ),
          const SizedBox(height: 14),
          const FormLabel('¿Para cuándo?'),
          QuickDateChips(
            due: _due,
            enabled: !_saving,
            onChanged: _setDue,
            onOther: _saving ? null : _pickDue,
          ),
          const SizedBox(height: 8),
          QuickTimeChips(
            due: _due,
            enabled: !_saving,
            onChanged: _setDue,
            onOther: _pickTime,
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              const Icon(
                Icons.event_outlined,
                size: 18,
                color: TaiaColors.fieryRose,
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  dueSentence(_due, bogotaNow()),
                  style: const TextStyle(
                    color: taiaInk,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
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
          const SizedBox(height: 20),
          ActivitySummaryCard(
            expression: _expression,
            text: activitySummary(
              type: _type,
              title: _title.text,
              subjectName: _subjectName,
              due: _due,
              reminders: _reminderMode,
              customReminders: _customAt.length,
            ),
          ),
          const SizedBox(height: 16),
          if (_error != null) AuthErrorText(_error!),
          AuthSubmitButton(
            label: _type == TaskType.exam ? 'Crear examen' : 'Crear tarea',
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
        SubjectChips(
          subjects: subjects,
          selectedId: _subjectId,
          enabled: !_saving,
          onNew: _newSubject,
          onSelected: (id) {
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
      ],
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.expression});

  final MascotExpression expression;

  @override
  Widget build(BuildContext context) {
    // Se abre desde el "+" central como pantalla aparte (RNF-14).
    final canPop = Navigator.of(context).canPop();
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (canPop) ...[
          IconButton.filled(
            tooltip: 'Volver',
            onPressed: () => Navigator.of(context).maybePop(),
            style: IconButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: taiaInk,
            ),
            icon: const Icon(Icons.arrow_back),
          ),
          const SizedBox(width: 12),
        ],
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
            TaiaChatButton(expression: expression, size: 84),
          ],
        ),
      ],
    );
  }
}
