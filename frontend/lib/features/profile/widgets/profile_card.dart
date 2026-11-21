import 'package:flutter/material.dart';

import '../../../core/spanish_dates.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_service.dart';
import '../../auth/auth_shell.dart';
import '../profile_logic.dart';

/// Tarjeta con el avatar (iniciales), nombre, correo y estado de la cuenta.
class ProfileCard extends StatelessWidget {
  const ProfileCard({super.key, required this.user});

  final UserProfile user;

  @override
  Widget build(BuildContext context) {
    final since = user.createdAt;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: taiaInk.withValues(alpha: 0.07),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        children: [
          Container(
            width: 84,
            height: 84,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [TaiaColors.fieryRose, TaiaColors.sunsetCoral],
              ),
              border: Border.all(color: TaiaColors.softPeach, width: 4),
            ),
            child: Text(
              initialsOf(user.fullName),
              style: const TextStyle(
                color: TaiaColors.ivoryMist,
                fontSize: 30,
                fontWeight: FontWeight.w900,
              ),
            ),
          ),
          const SizedBox(height: 14),
          Text(
            user.fullName,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: taiaInk,
              fontSize: 24,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            user.email,
            textAlign: TextAlign.center,
            style: TextStyle(color: taiaInk.withValues(alpha: 0.65)),
          ),
          const SizedBox(height: 14),
          Wrap(
            alignment: WrapAlignment.center,
            spacing: 8,
            runSpacing: 8,
            children: [
              _Chip(
                icon: user.telegramLinked ? Icons.check_circle : Icons.link_off,
                label: user.telegramLinked
                    ? 'Telegram vinculado'
                    : 'Telegram sin vincular',
                highlighted: user.telegramLinked,
              ),
              if (since != null)
                _Chip(
                  icon: Icons.calendar_today_outlined,
                  label: 'Desde ${formatMonthYear(since)}',
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({
    required this.icon,
    required this.label,
    this.highlighted = false,
  });

  final IconData icon;
  final String label;
  final bool highlighted;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: highlighted
            ? TaiaColors.fieryRose
            : TaiaColors.softPeach.withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 15, color: highlighted ? Colors.white : taiaInk),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              color: highlighted ? Colors.white : taiaInk,
              fontSize: 12,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}