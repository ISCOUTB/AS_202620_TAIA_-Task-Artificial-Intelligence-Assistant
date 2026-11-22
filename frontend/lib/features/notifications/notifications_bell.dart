import 'package:flutter/material.dart';

import '../../core/api_error.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_shell.dart';
import 'notifications_service.dart';
import 'notifications_sheet.dart';

/// Campanita con el número de notificaciones sin leer; abre la bandeja
/// (RF-NOT-03).
class NotificationsBell extends StatefulWidget {
  const NotificationsBell({super.key, this.service});

  final NotificationsService? service;

  @override
  State<NotificationsBell> createState() => _NotificationsBellState();
}

class _NotificationsBellState extends State<NotificationsBell> {
  int _unread = 0;

  NotificationsService get _service => widget.service ?? notificationsService;

  @override
  void initState() {
    super.initState();
    _loadCount();
  }

  /// Si el contador no carga, la campana se muestra sin número.
  Future<void> _loadCount() async {
    try {
      final count = await _service.unreadCount();
      if (mounted) setState(() => _unread = count);
    } on ApiException {
      if (mounted) setState(() => _unread = 0);
    }
  }

  Future<void> _open() async {
    await showNotificationsSheet(context, _service);
    await _loadCount();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        IconButton(
          tooltip: 'Notificaciones',
          iconSize: 28,
          color: taiaInk,
          onPressed: _open,
          icon: const Icon(Icons.notifications_none_rounded),
        ),
        if (_unread > 0)
          Positioned(
            top: 4,
            right: 2,
            child: IgnorePointer(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                constraints: const BoxConstraints(minWidth: 18),
                decoration: BoxDecoration(
                  color: TaiaColors.fieryRose,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  _unread > 9 ? '9+' : '$_unread',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}
