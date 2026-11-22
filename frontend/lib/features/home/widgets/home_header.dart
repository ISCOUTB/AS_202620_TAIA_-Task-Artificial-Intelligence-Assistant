import 'package:flutter/material.dart';

import '../../../core/bogota_time.dart';
import '../../../core/spanish_dates.dart';
import '../../auth/auth_shell.dart';
import '../../notifications/notifications_bell.dart';
import '../../notifications/notifications_service.dart';

/// Fecha, saludo y campanita con el número de notificaciones sin leer.
class HomeHeader extends StatelessWidget {
  const HomeHeader({
    super.key,
    required this.firstName,
    this.notificationsService,
  });

  final String firstName;
  final NotificationsService? notificationsService;

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
                formatLongDate(bogotaNow()),
                style: TextStyle(
                  color: taiaInk.withValues(alpha: 0.7),
                  fontSize: 15,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Hola, $firstName ',
                style: const TextStyle(
                  color: taiaInk,
                  fontSize: 28,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
        ),
        NotificationsBell(service: notificationsService),
      ],
    );
  }
}
