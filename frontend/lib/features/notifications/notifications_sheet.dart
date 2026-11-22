import 'package:flutter/material.dart';

import '../../core/api_error.dart';
import '../../core/spanish_dates.dart';
import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_shell.dart';
import 'notifications_service.dart';

/// Hoja inferior de la campanita: la bandeja de notificaciones (RF-NOT-03).
Future<void> showNotificationsSheet(
  BuildContext context,
  NotificationsService service,
) {
  return showModalBottomSheet<void>(
    context: context,
    backgroundColor: TaiaColors.ivoryMist,
    showDragHandle: true,
    isScrollControlled: true,
    builder: (context) => _NotificationsSheet(service: service),
  );
}

class _NotificationsSheet extends StatefulWidget {
  const _NotificationsSheet({required this.service});

  final NotificationsService service;

  @override
  State<_NotificationsSheet> createState() => _NotificationsSheetState();
}

class _NotificationsSheetState extends State<_NotificationsSheet> {
  List<AppNotification>? _items;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final items = await widget.service.list();
      if (mounted) setState(() => _items = items);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _markRead(AppNotification item) async {
    if (item.read) return;
    try {
      await widget.service.markRead(item.id);
      if (!mounted) return;
      setState(() {
        _items = [
          for (final n in _items ?? <AppNotification>[])
            n.id == item.id ? n.markedRead() : n,
        ];
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _markAllRead() async {
    try {
      await widget.service.markAllRead();
      if (!mounted) return;
      setState(() {
        _items = [
          for (final n in _items ?? <AppNotification>[]) n.markedRead(),
        ];
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  @override
  Widget build(BuildContext context) {
    final items = _items;
    final hasUnread = items?.any((n) => !n.read) ?? false;
    return SafeArea(
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.sizeOf(context).height * 0.7,
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Notificaciones',
                      style: TextStyle(
                        color: taiaInk,
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                  if (hasUnread)
                    TextButton(
                      style: TextButton.styleFrom(
                        foregroundColor: TaiaColors.fieryRose,
                      ),
                      onPressed: _markAllRead,
                      child: const Text('Marcar todas como leídas'),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              if (_error != null) ...[
                AuthErrorText(_error!),
                const SizedBox(height: 8),
              ],
              if (items == null && _error == null)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.symmetric(vertical: 16),
                    child: CircularProgressIndicator(
                      color: TaiaColors.fieryRose,
                    ),
                  ),
                )
              else if (items != null && items.isEmpty)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.symmetric(vertical: 16),
                    child: Column(
                      children: [
                        SizedBox(
                          width: 150,
                          child: TaiaMascot(
                            motion: 0.6,
                            expression: MascotExpression.happy,
                          ),
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Estás al día. No tienes notificaciones.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: taiaInk),
                        ),
                      ],
                    ),
                  ),
                )
              else if (items != null)
                Flexible(
                  child: ListView.separated(
                    shrinkWrap: true,
                    itemCount: items.length,
                    separatorBuilder: (context, index) =>
                        const SizedBox(height: 8),
                    itemBuilder: (context, index) => _NotificationTile(
                      item: items[index],
                      onTap: () => _markRead(items[index]),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  const _NotificationTile({required this.item, required this.onTap});

  final AppNotification item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: item.read
          ? Colors.white
          : TaiaColors.fieryRose.withValues(alpha: 0.08),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Icon(
                item.read
                    ? Icons.notifications_none_outlined
                    : Icons.notifications_active_outlined,
                color: TaiaColors.fieryRose,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.message,
                      style: TextStyle(
                        color: taiaInk,
                        fontWeight: item.read
                            ? FontWeight.w500
                            : FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      formatDateTimeShort(item.createdAt),
                      style: TextStyle(
                        color: taiaInk.withValues(alpha: 0.6),
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
