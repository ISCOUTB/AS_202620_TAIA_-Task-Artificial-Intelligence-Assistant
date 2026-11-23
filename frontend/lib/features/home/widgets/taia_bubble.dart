import 'package:flutter/material.dart';

import '../../../mascot/mascot_expression.dart';
import '../../agent/agent_service.dart';
import '../../agent/taia_chat_button.dart';
import '../../auth/auth_shell.dart';

/// TAIA en el Inicio con una burbuja que invita a hablarle (RF-AGT-23). Tocar a
/// TAIA o la burbuja abre el chat.
class TaiaBubble extends StatelessWidget {
  const TaiaBubble({
    super.key,
    required this.text,
    this.service,
    this.onClosed,
  });

  final String text;
  final AgentService? service;

  /// Se llama al volver del chat, para actualizar el Inicio.
  final VoidCallback? onClosed;

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.of(context).disableAnimations;
    final bubble = GestureDetector(
      onTap: () async {
        await openTaiaChat(context, service: service);
        onClosed?.call();
      },
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 220),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(18),
              topRight: Radius.circular(18),
              bottomLeft: Radius.circular(18),
              bottomRight: Radius.circular(4),
            ),
            boxShadow: [
              BoxShadow(
                color: Color(0x1F3B2A2A),
                blurRadius: 12,
                offset: Offset(0, 4),
              ),
            ],
          ),
          child: Text(
            text,
            style: const TextStyle(
              color: taiaInk,
              fontSize: 14,
              height: 1.3,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ),
    );

    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 34),
          child: reduceMotion
              ? bubble
              : TweenAnimationBuilder<double>(
                  // Una clave por texto: si cambia la frase, la burbuja vuelve a aparecer.
                  key: ValueKey(text),
                  tween: Tween(begin: 0, end: 1),
                  duration: const Duration(milliseconds: 300),
                  curve: Curves.easeOutBack,
                  builder: (context, t, child) => Opacity(
                    opacity: t.clamp(0, 1),
                    child: Transform.scale(
                      scale: 0.85 + 0.15 * t,
                      alignment: Alignment.bottomRight,
                      child: child,
                    ),
                  ),
                  child: bubble,
                ),
        ),
        const SizedBox(width: 4),
        TaiaChatButton(
          expression: MascotExpression.laptop,
          size: 84,
          service: service,
          onClosed: onClosed,
        ),
      ],
    );
  }
}
