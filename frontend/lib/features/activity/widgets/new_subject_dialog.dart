import 'package:flutter/material.dart';

import '../../../theme/taia_colors.dart';
import '../../auth/auth_service.dart';
import '../../auth/auth_shell.dart';
import '../../tasks/subject.dart';
import '../../tasks/subjects_service.dart';
import '../../tasks/widgets/task_form_widgets.dart';

/// Diálogo para crear una materia sin salir del formulario. Devuelve la materia
/// creada, o null si se cancela.
Future<Subject?> showNewSubjectDialog(
  BuildContext context, {
  SubjectsService? service,
}) {
  return showDialog<Subject>(
    context: context,
    builder: (context) => _NewSubjectDialog(service: service ?? subjectsService),
  );
}

class _NewSubjectDialog extends StatefulWidget {
  const _NewSubjectDialog({required this.service});

  final SubjectsService service;

  @override
  State<_NewSubjectDialog> createState() => _NewSubjectDialogState();
}

class _NewSubjectDialogState extends State<_NewSubjectDialog> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _teacher = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    _teacher.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final subject = await widget.service.create(
        name: _name.text.trim(),
        teacher: _teacher.text.trim(),
      );
      if (!mounted) return;
      Navigator.of(context).pop(subject);
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: TaiaColors.ivoryMist,
      title: const Text(
        'Nueva materia',
        style: TextStyle(color: taiaInk, fontWeight: FontWeight.w900),
      ),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const FormLabel('Nombre'),
            TextFormField(
              controller: _name,
              enabled: !_busy,
              autofocus: true,
              maxLength: 100,
              style: taskValueStyle,
              textCapitalization: TextCapitalization.words,
              decoration: taskFieldDecoration(
                hint: 'Ej. Física Mecánica',
              ).copyWith(counterText: ''),
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
            if (_error != null) ...[
              const SizedBox(height: 8),
              AuthErrorText(_error!),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          style: FilledButton.styleFrom(backgroundColor: TaiaColors.fieryRose),
          onPressed: _busy ? null : _submit,
          child: _busy
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : const Text('Crear materia'),
        ),
      ],
    );
  }
}