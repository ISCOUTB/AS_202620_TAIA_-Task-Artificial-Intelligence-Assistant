import 'package:flutter/material.dart';

import '../../../mascot/mascot_expression.dart';
import '../../../mascot/taia_mascot.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_service.dart';
import '../../auth/auth_shell.dart';
import '../../tasks/subject.dart';
import '../../tasks/subjects_service.dart';
import '../../tasks/widgets/task_form_widgets.dart';
import '../../shell/page_header.dart';

/// Abre el detalle de una asignatura (RF-ASG-02) para editarla (RF-ASG-03),
/// eliminarla (RF-ASG-04), archivarla o desarchivarla (RF-ASG-05) y manejar
/// sus alias (RF-ASG-09).
Future<void> showSubjectSheet(
  BuildContext context,
  Subject subject, {
  SubjectsService? service,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    backgroundColor: TaiaColors.ivoryMist,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (context) =>
        _SubjectSheet(subject: subject, service: service ?? subjectsService),
  );
}

class _SubjectSheet extends StatefulWidget {
  const _SubjectSheet({required this.subject, required this.service});

  final Subject subject;
  final SubjectsService service;

  @override
  State<_SubjectSheet> createState() => _SubjectSheetState();
}

class _SubjectSheetState extends State<_SubjectSheet> {
  final _formKey = GlobalKey<FormState>();
  late Subject _subject = widget.subject;
  late final TextEditingController _name = TextEditingController(
    text: widget.subject.name,
  );
  late final TextEditingController _teacher = TextEditingController(
    text: widget.subject.teacher ?? '',
  );
  final _alias = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  @override
  void dispose() {
    _name.dispose();
    _teacher.dispose();
    _alias.dispose();
    super.dispose();
  }

  /// Pide el detalle para mostrar las tareas pendientes al día (RF-ASG-02).
  Future<void> _refresh() async {
    try {
      final subject = await widget.service.get(_subject.id);
      if (mounted) setState(() => _subject = subject);
    } on ApiException {
      // Se queda con los datos del listado.
    }
  }

  /// Ejecuta una acción sobre la asignatura y muestra su error, si lo hay.
  Future<void> _run(Future<Subject?> Function() action) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final subject = await action();
      if (mounted && subject != null) setState(() => _subject = subject);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    await _run(
      () => widget.service.update(
        _subject.id,
        name: _name.text.trim(),
        teacher: _teacher.text.trim(),
      ),
    );
    if (mounted && _error == null) Navigator.of(context).pop();
  }

  Future<void> _addAlias() async {
    final alias = _alias.text.trim();
    if (alias.isEmpty) return;
    await _run(() => widget.service.addAlias(_subject.id, alias));
    if (_error == null) _alias.clear();
  }

  Future<void> _toggleArchive() => _run(
    () => _subject.archived
        ? widget.service.unarchive(_subject.id)
        : widget.service.archive(_subject.id),
  );

  Future<void> _delete() async {
    final confirmed = await confirmAction(
      context,
      title: '¿Eliminar esta asignatura?',
      message:
          'Se eliminará "${_subject.name}" junto con su horario. Solo se '
          'puede si no tiene actividades; si las tiene, archívala.',
      confirmLabel: 'Eliminar',
    );
    if (!confirmed || !mounted) return;
    var deleted = false;
    await _run(() async {
      await widget.service.delete(_subject.id);
      deleted = true;
      return null;
    });
    if (deleted && mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final subject = _subject;
    final pending = subject.pendingTasks;
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _SheetTitle(archived: subject.archived),
              const SizedBox(height: 8),
              Text(
                pending == 0
                    ? 'No tiene tareas pendientes.'
                    : pending == 1
                    ? 'Tiene 1 tarea pendiente.'
                    : 'Tiene $pending tareas pendientes.',
                style: TextStyle(color: taiaInk.withValues(alpha: 0.7)),
              ),
              if (subject.archived)
                Text(
                  'Archivada: no acepta tareas nuevas y su horario no se '
                  'muestra.',
                  style: TextStyle(color: taiaInk.withValues(alpha: 0.7)),
                ),
              const SizedBox(height: 16),
              const FormLabel('Nombre'),
              TextFormField(
                controller: _name,
                enabled: !_busy,
                maxLength: 100,
                style: taskValueStyle,
                textCapitalization: TextCapitalization.words,
                decoration: taskFieldDecoration().copyWith(counterText: ''),
                validator: (v) => (v == null || v.trim().isEmpty)
                    ? 'Escribe el nombre de la materia.'
                    : null,
              ),
              const SizedBox(height: 14),
              const FormLabel('Profesor (opcional)'),
              TextFormField(
                controller: _teacher,
                enabled: !_busy,
                maxLength: 100,
                style: taskValueStyle,
                textCapitalization: TextCapitalization.words,
                decoration: taskFieldDecoration().copyWith(counterText: ''),
              ),
              const SizedBox(height: 16),
              const FormLabel('Alias'),
              Text(
                'Nombres cortos para que TAIA reconozca la materia, como '
                '"MB".',
                style: TextStyle(
                  color: taiaInk.withValues(alpha: 0.6),
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 4,
                children: [
                  for (final alias in subject.aliases)
                    InputChip(
                      label: Text(alias.alias),
                      onDeleted: _busy
                          ? null
                          : () => _run(
                              () => widget.service.removeAlias(
                                subject.id,
                                alias.id,
                              ),
                            ),
                      deleteButtonTooltipMessage: 'Quitar alias',
                      shape: const StadiumBorder(),
                      side: BorderSide.none,
                      backgroundColor: TaiaColors.softPeach.withValues(
                        alpha: 0.6,
                      ),
                      labelStyle: const TextStyle(
                        color: taiaInk,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _alias,
                enabled: !_busy,
                maxLength: 50,
                style: taskValueStyle,
                onSubmitted: (_) => _addAlias(),
                decoration: taskFieldDecoration(
                  hint: 'Nuevo alias',
                  suffix: IconButton(
                    tooltip: 'Agregar alias',
                    color: TaiaColors.fieryRose,
                    onPressed: _busy ? null : _addAlias,
                    icon: const Icon(Icons.add_circle_outline),
                  ),
                ).copyWith(counterText: ''),
              ),
              const SizedBox(height: 20),
              if (_error != null) AuthErrorText(_error!),
              AuthSubmitButton(
                label: 'Guardar cambios',
                loading: _busy,
                onPressed: _save,
              ),
              const SizedBox(height: 4),
              TextButton.icon(
                style: TextButton.styleFrom(foregroundColor: taiaInk),
                onPressed: _busy ? null : _toggleArchive,
                icon: Icon(
                  subject.archived
                      ? Icons.unarchive_outlined
                      : Icons.archive_outlined,
                ),
                label: Text(
                  subject.archived
                      ? 'Desarchivar asignatura'
                      : 'Archivar asignatura',
                ),
              ),
              TextButton.icon(
                style: TextButton.styleFrom(
                  foregroundColor: Colors.red.shade700,
                ),
                onPressed: _busy ? null : _delete,
                icon: const Icon(Icons.delete_outline),
                label: const Text('Eliminar asignatura'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SheetTitle extends StatelessWidget {
  const _SheetTitle({required this.archived});

  final bool archived;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                archived ? 'ASIGNATURA ARCHIVADA' : 'ASIGNATURA',
                style: const TextStyle(
                  color: TaiaColors.fieryRose,
                  fontSize: 12,
                  letterSpacing: 1.6,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Revisemos tu materia',
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
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
          ),
          child: const TaiaMascot(
            motion: 0.5,
            expression: MascotExpression.studying,
          ),
        ),
        const SizedBox(width: 8),
        IconButton.filled(
          tooltip: 'Cerrar',
          onPressed: () => Navigator.of(context).pop(),
          style: IconButton.styleFrom(
            backgroundColor: Colors.white,
            foregroundColor: taiaInk,
          ),
          icon: const Icon(Icons.close),
        ),
      ],
    );
  }
}
