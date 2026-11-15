import 'package:flutter/material.dart';

import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';

/// Grupo de opciones con un título pequeño y una tarjeta blanca.
class ProfileSection extends StatelessWidget {
  const ProfileSection({super.key, required this.title, required this.tiles});

  final String title;
  final List<Widget> tiles;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 6, bottom: 8),
          child: Text(
            title,
            style: TextStyle(
              color: taiaInk.withValues(alpha: 0.55),
              fontSize: 12,
              letterSpacing: 1.4,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
        Material(
          color: Colors.white,
          borderRadius: BorderRadius.circular(22),
          clipBehavior: Clip.antiAlias,
          elevation: 0,
          child: Column(
            children: [
              for (var i = 0; i < tiles.length; i++) ...[
                if (i > 0)
                  Divider(
                    height: 1,
                    indent: 68,
                    color: TaiaColors.softPeach.withValues(alpha: 0.6),
                  ),
                tiles[i],
              ],
            ],
          ),
        ),
      ],
    );
  }
}

/// Una fila de opciones: icono, título, subtítulo y algo al final (flecha,
/// botón o la etiqueta "Próximamente").
class ProfileTile extends StatelessWidget {
  const ProfileTile({
    super.key,
    required this.icon,
    required this.title,
    required this.onTap,
    this.subtitle,
    this.trailing,
    this.comingSoon = false,
    this.danger = false,
  });

  final IconData icon;
  final String title;
  final String? subtitle;
  final VoidCallback? onTap;

  /// Widget al final; si es null se muestra una flecha (o la etiqueta si es
  /// [comingSoon]).
  final Widget? trailing;
  final bool comingSoon;
  final bool danger;

  @override
  Widget build(BuildContext context) {
    final color = danger ? Colors.red.shade700 : taiaInk;
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: danger
                    ? Colors.red.shade50
                    : TaiaColors.softPeach.withValues(alpha: 0.6),
                borderRadius: BorderRadius.circular(13),
              ),
              child: Icon(
                icon,
                size: 22,
                color: danger ? Colors.red.shade700 : TaiaColors.fieryRose,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      color: comingSoon ? color.withValues(alpha: 0.6) : color,
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  if (subtitle != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      subtitle!,
                      style: TextStyle(
                        color: taiaInk.withValues(alpha: 0.6),
                        fontSize: 12.5,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            trailing ??
                (comingSoon
                    ? const _SoonBadge()
                    : Icon(
                        Icons.chevron_right,
                        color: taiaInk.withValues(alpha: 0.4),
                      )),
          ],
        ),
      ),
    );
  }
}

class _SoonBadge extends StatelessWidget {
  const _SoonBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: TaiaColors.apricotWhisper.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Text(
        'Próximamente',
        style: TextStyle(
          color: taiaInk,
          fontSize: 11,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}