import 'package:flutter/material.dart';

import '../../../core/bogota_time.dart';
import '../../../core/spanish_dates.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_service.dart';
import '../../auth/auth_shell.dart';
import '../../reminders/reminder.dart';
import '../../reminders/reminder_rules.dart';
import '../../reminders/reminders_service.dart';
import '../task.dart';
import 'task_form_widgets.dart';

/// Recordatorios de una actividad dentro de su detalle (RF-TAR-05): permite
/// agregar (RF-REC-01), editar (RF-REC-04) y eliminar (RF-REC-05) los que
/// siguen pendientes.
class TaskReminders extends StatefulWidget {
  const TaskReminders({super.key, required this.task, this.service});

  final AcademicTask task;
  final RemindersService? service;

  @override
  State<TaskReminders> createState() => _TaskRemindersState();
}

class _TaskRemindersState extends State<TaskReminders> {
  List<Reminder>? _items;
  String? _error;
  final Set<String> _busy = {};

  RemindersService get _service => widget.service ?? remindersService;

  /// Solo una actividad pendiente admite recordatorios nuevos (RF-REC-01).
  bool get _canAdd => widget.task.status == TaskStatus.pending;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final items = await _service.listForTask(widget.task.id);
      if (mounted) setState(() => _items = items);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _openDialog([Reminder? reminder]) async {
    final saved = await showDialog<Reminder>(
      context: context,
      builder: (context) => _ReminderDialog(
        task: widget.task,
        reminder: reminder,
        service: _service,
      ),
    );
    if (saved == null || !mounted) return;
    setState(() {
      _items = [
        for (final r in _items ?? <Reminder>[])
          if (r.id != saved.id) r,
        saved,
      ]..sort((a, b) => a.scheduledAt.compareTo(b.scheduledAt));
    });
  }

  Future<void> _delete(Reminder reminder) async {
    setState(() {
      _busy.add(reminder.id);
      _error = null;
    });
    try {
      await _service.delete(reminder.id);
      if (!mounted) return;
      setState(() {
        _items = (_items ?? []).where((r) => r.id != reminder.id).toList();
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy.remove(reminder.id));
    }
  }

  @override
  Widget build(BuildContext context) {
    final items = _items;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const FormLabel('Recordatorios'),
        if (items == null && _error == null)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Center(
              child: CircularProgressIndicator(color: TaiaColors.fieryRose),
            ),
          )
        else if (items != null && items.isEmpty)
          Text(
            'Esta actividad no tiene recordatorios.',
            style: TextStyle(color: taiaInk.withValues(alpha: 0.7)),
          )
        else
          for (final reminder in items ?? <Reminder>[]) ...[
            _ReminderRow(
              reminder: reminder,
              busy: _busy.contains(reminder.id),
              onEdit: () => _openDialog(reminder),
              onDelete: () => _delete(reminder),
            ),
            const SizedBox(height: 8),
          ],
        if (_error != null) ...[
          const SizedBox(height: 8),
          AuthErrorText(_error!),
        ],
        if (_canAdd)
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton.icon(
              style: TextButton.styleFrom(
                foregroundColor: TaiaColors.fieryRose,
              ),
              onPressed: _openDialog,
              icon: const Icon(Icons.add_alarm_outlined),
              label: const Text('Agregar recordatorio'),
            ),
          ),
      ],
    );
  }
}

class _ReminderRow extends StatelessWidget {
  const _ReminderRow({
    required this.reminder,
    required this.busy,
    required this.onEdit,
    required this.onDelete,
  });

  final Reminder reminder;
  final bool busy;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    // Con el modelo actual, `is_completed` marca el que ya avisó: no se edita
    // ni se elimina (RF-REC-04 y RF-REC-05).
    final pending = !reminder.isCompleted;
    final when = formatDateTimeShort(reminder.scheduledAt);
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 8, 4, 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Icon(
            pending
                ? Icons.notifications_active_outlined
                : Icons.notifications_off_outlined,
            color: TaiaColors.fieryRose,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  reminder.message,
                  style: const TextStyle(
                    color: taiaInk,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  pending ? when : '$when · enviado',
                  style: TextStyle(
                    color: taiaInk.withValues(alpha: 0.6),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          if (busy)
            const Padding(
              padding: EdgeInsets.all(12),
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: TaiaColors.fieryRose,
                ),
              ),
            )
          else if (pending) ...[
            IconButton(
              tooltip: 'Editar recordatorio',
              color: taiaInk,
              onPressed: onEdit,
              icon: const Icon(Icons.edit_outlined),
            ),
            IconButton(
              tooltip: 'Eliminar recordatorio',
              color: Colors.red.shade700,
              onPressed: onDelete,
              icon: const Icon(Icons.delete_outline),
            ),
          ],
        ],
      ),
    );
  }
}

/// Diálogo para crear o editar un recordatorio. Devuelve el recordatorio
/// guardado, o null si se cancela.
class _ReminderDialog extends StatefulWidget {
  const _ReminderDialog({
    required this.task,
    required this.reminder,
    required this.service,
  });

  final AcademicTask task;
  final Reminder? reminder;
  final RemindersService service;

  @override
  State<_ReminderDialog> createState() => _ReminderDialogState();
}

class _ReminderDialogState extends State<_ReminderDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _message = TextEditingController(
    text: widget.reminder?.message ?? '',
  );
  late DateTime _at =
      widget.reminder?.scheduledAt ?? suggestedReminderTime(bogotaNow());
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _message.dispose();
    super.dispose();
  }

  Future<void> _pickTime() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _at,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_at),
    );
    if (time == null || !mounted) return;
    setState(() {
      _at = DateTime(date.year, date.month, date.day, time.hour, time.minute);
    });
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final timeError = reminderTimeError(
      _at,
      due: widget.task.dueAt,
      now: bogotaNow(),
    );
    if (timeError != null) {
      setState(() => _error = timeError);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final reminder = widget.reminder;
      final saved = reminder == null
          ? await widget.service.create(
              taskId: widget.task.id,
              message: _message.text.trim(),
              scheduledAt: _at,
            )
          : await widget.service.update(
              reminder.id,
              message: _message.text.trim(),
              scheduledAt: _at,
            );
      if (!mounted) return;
      Navigator.of(context).pop(saved);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: TaiaColors.ivoryMist,
      title: Text(
        widget.reminder == null ? 'Nuevo recordatorio' : 'Editar recordatorio',
        style: const TextStyle(color: taiaInk, fontWeight: FontWeight.w900),
      ),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const FormLabel('Mensaje'),
            TextFormField(
              controller: _message,
              enabled: !_busy,
              maxLength: 500,
              style: taskValueStyle,
              textCapitalization: TextCapitalization.sentences,
              decoration: taskFieldDecoration(
                hint: 'Ej. Repasar el capítulo 3',
              ).copyWith(counterText: ''),
              validator: (v) => (v == null || v.trim().isEmpty)
                  ? 'Escribe el mensaje del recordatorio.'
                  : null,
            ),
            const SizedBox(height: 14),
            const FormLabel('Fecha y hora'),
            InkWell(
              borderRadius: BorderRadius.circular(14),
              onTap: _busy ? null : _pickTime,
              child: InputDecorator(
                decoration: taskFieldDecoration(
                  suffix: const Icon(
                    Icons.calendar_today_outlined,
                    size: 20,
                    color: taiaInk,
                  ),
                ),
                child: Text(formatDateTimeShort(_at), style: taskValueStyle),
              ),
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
              : const Text('Guardar'),
        ),
      ],
    );
  }
}
