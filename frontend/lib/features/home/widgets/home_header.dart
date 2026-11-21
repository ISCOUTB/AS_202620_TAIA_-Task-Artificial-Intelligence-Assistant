import 'package:flutter/material.dart';

import '../../../core/spanish_dates.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';

/// Fecha, saludo y campanita con el número de recordatorios pendientes.
class HomeHeader extends StatelessWidget {
  const HomeHeader({
    super.key,
    required this.firstName,
    required this.pendingReminders,
    required this.onBellPressed,
  });

  final String firstName;
  final int pendingReminders;
  final VoidCallback onBellPressed;

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
                formatLongDate(DateTime.now()),
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
        Stack(
          clipBehavior: Clip.none,
          children: [
            IconButton(
              tooltip: 'Recordatorios',
              iconSize: 28,
              color: taiaInk,
              onPressed: onBellPressed,
              icon: const Icon(Icons.notifications_none_rounded),
            ),
            if (pendingReminders > 0)
              Positioned(
                top: 4,
                right: 2,
                child: IgnorePointer(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 5,
                      vertical: 2,
                    ),
                    constraints: const BoxConstraints(minWidth: 18),
                    decoration: BoxDecoration(
                      color: TaiaColors.fieryRose,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      pendingReminders > 9 ? '9+' : '$pendingReminders',
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
        ),
      ],
    );
  }
}