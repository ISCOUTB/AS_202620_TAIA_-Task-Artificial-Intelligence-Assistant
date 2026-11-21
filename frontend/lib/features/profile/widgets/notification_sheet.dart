import 'package:flutter/material.dart';

import '../../../mascot/mascot_expression.dart';
import '../../../mascot/taia_mascot.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../profile_logic.dart';

/// Qué eligió el usuario en la hoja de notificaciones.
enum NotificationSheetResult { app, telegram, linkTelegram }

/// Hoja para elegir dónde recibir los recordatorios.
Future<NotificationSheetResult?> showNotificationSheet(
  BuildContext context, {
  required NotificationChannel current,
  required bool telegramLinked,
}) {
  return showModalBottomSheet<NotificationSheetResult>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    backgroundColor: TaiaColors.ivoryMist,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (context) =>
        _NotificationSheet(current: current, telegramLinked: telegramLinked),
  );
}

class _NotificationSheet extends StatelessWidget {
  const _NotificationSheet({
    required this.current,
    required this.telegramLinked,
  });

  final NotificationChannel current;
  final bool telegramLinked;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'PREFERENCIAS',
                      style: TextStyle(
                        color: TaiaColors.fieryRose,
                        fontSize: 12,
                        letterSpacing: 1.6,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    SizedBox(height: 6),
                    Text(
                      'Notificaciones',
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
                width: 74,
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: TaiaColors.fieryRose,
                  borderRadius: BorderRadius.circular(22),
                ),
                child: const TaiaMascot(
                  motion: 0.5,
                  expression: MascotExpression.thinking,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            '¿Dónde quieres recibir tus recordatorios?',
            style: TextStyle(color: taiaInk.withValues(alpha: 0.8)),
          ),
          const SizedBox(height: 14),
          _ChannelOption(
            icon: Icons.notifications_active_outlined,
            title: 'En la aplicación',
            subtitle: 'Los verás en la campanita de TAIA.',
            selected: current == NotificationChannel.app,
            onTap: () => Navigator.of(context).pop(NotificationSheetResult.app),
          ),
          const SizedBox(height: 10),
          _ChannelOption(
            icon: Icons.send_outlined,
            title: 'Por Telegram',
            subtitle: telegramLinked
                ? 'El bot de TAIA te los envía al chat.'
                : 'Primero vincula tu cuenta de Telegram.',
            selected: current == NotificationChannel.telegram,
            trailing: telegramLinked
                ? null
                : TextButton(
                    style: TextButton.styleFrom(
                      foregroundColor: TaiaColors.fieryRose,
                    ),
                    onPressed: () => Navigator.of(
                      context,
                    ).pop(NotificationSheetResult.linkTelegram),
                    child: const Text(
                      'Vincular',
                      style: TextStyle(fontWeight: FontWeight.w800),
                    ),
                  ),
            onTap: telegramLinked
                ? () => Navigator.of(
                    context,
                  ).pop(NotificationSheetResult.telegram)
                : null,
          ),
          const SizedBox(height: 14),
          Text(
            'Tu elección se guarda en este teléfono.',
            style: TextStyle(
              color: taiaInk.withValues(alpha: 0.55),
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class _ChannelOption extends StatelessWidget {
  const _ChannelOption({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.selected,
    required this.onTap,
    this.trailing,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final bool selected;
  final VoidCallback? onTap;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null;
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            border: Border.all(
              color: selected ? TaiaColors.fieryRose : TaiaColors.softPeach,
              width: selected ? 2 : 1.5,
            ),
          ),
          child: Row(
            children: [
              Icon(
                icon,
                color: enabled
                    ? TaiaColors.fieryRose
                    : taiaInk.withValues(alpha: 0.35),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        color: enabled
                            ? taiaInk
                            : taiaInk.withValues(alpha: 0.5),
                        fontWeight: FontWeight.w800,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: TextStyle(
                        color: taiaInk.withValues(alpha: 0.6),
                        fontSize: 12.5,
                      ),
                    ),
                  ],
                ),
              ),
              if (trailing != null)
                trailing!
              else if (selected)
                const Icon(Icons.check_circle, color: TaiaColors.fieryRose),
            ],
          ),
        ),
      ),
    );
  }
}