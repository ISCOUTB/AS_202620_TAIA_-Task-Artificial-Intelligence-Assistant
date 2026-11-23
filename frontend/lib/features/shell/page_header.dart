import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../theme/taia_colors.dart';
import '../agent/taia_chat_button.dart';
import '../auth/auth_shell.dart';

/// Cabecera de las pantallas que se abren encima de las pestañas: botón para
/// volver, etiqueta, título, subtítulo y la mascota (mismo estilo que las
/// pestañas).
class PageHeader extends StatelessWidget {
  const PageHeader({
    super.key,
    required this.label,
    required this.title,
    required this.subtitle,
    this.expression = MascotExpression.studying,
    this.opensChat = true,
  });

  final String label;
  final String title;
  final String subtitle;
  final MascotExpression expression;

  /// La mascota abre el chat (RF-AGT-23), salvo dentro del propio chat.
  final bool opensChat;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        IconButton.filled(
          tooltip: 'Volver',
          onPressed: () => Navigator.of(context).maybePop(),
          style: IconButton.styleFrom(
            backgroundColor: Colors.white,
            foregroundColor: taiaInk,
          ),
          icon: const Icon(Icons.arrow_back),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  color: TaiaColors.fieryRose,
                  fontSize: 12,
                  letterSpacing: 1.6,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                title,
                style: const TextStyle(
                  color: taiaInk,
                  fontSize: 30,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: TextStyle(
                  color: taiaInk.withValues(alpha: 0.65),
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ),
        opensChat
            ? TaiaChatButton(expression: expression, size: 72)
            : SizedBox.square(
                dimension: 72,
                child: TaiaMascot(motion: 0.6, expression: expression),
              ),
      ],
    );
  }
}

/// Mensaje sobre una tarjeta clara cuando una lista está vacía.
class EmptyStateCard extends StatelessWidget {
  const EmptyStateCard(this.message, {super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: TaiaColors.softPeach),
      ),
      child: Text(
        message,
        textAlign: TextAlign.center,
        style: const TextStyle(
          color: taiaInk,
          fontSize: 15,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

/// Diálogo de confirmación con el estilo de la app. Devuelve true si el
/// usuario confirma.
Future<bool> confirmAction(
  BuildContext context, {
  required String title,
  required String message,
  required String confirmLabel,
}) async {
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      backgroundColor: TaiaColors.ivoryMist,
      title: Text(
        title,
        style: const TextStyle(color: taiaInk, fontWeight: FontWeight.w900),
      ),
      content: Text(message, style: const TextStyle(color: taiaInk)),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          style: FilledButton.styleFrom(backgroundColor: TaiaColors.fieryRose),
          onPressed: () => Navigator.of(context).pop(true),
          child: Text(confirmLabel),
        ),
      ],
    ),
  );
  return confirmed ?? false;
}
