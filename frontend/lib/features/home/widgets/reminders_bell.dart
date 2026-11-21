import 'package:flutter/material.dart';

import '../../auth/auth_service.dart';
import '../../auth/auth_shell.dart';
import '../../reminders/reminders_service.dart';
import 'notifications_sheet.dart';

/// Campanita que abre la hoja con los recordatorios pendientes.
class RemindersBell extends StatelessWidget {
  const RemindersBell({super.key, this.service});

  final RemindersService? service;

  Future<void> _open(BuildContext context) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      final all = await (service ?? remindersService).list();
      if (!context.mounted) return;
      final pending = all.where((r) => !r.isCompleted).toList()
        ..sort((a, b) => a.scheduledAt.compareTo(b.scheduledAt));
      await showNotificationsSheet(context, pending);
    } on ApiException catch (e) {
      messenger
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Recordatorios',
      iconSize: 28,
      color: taiaInk,
      onPressed: () => _open(context),
      icon: const Icon(Icons.notifications_none_rounded),
    );
  }
}