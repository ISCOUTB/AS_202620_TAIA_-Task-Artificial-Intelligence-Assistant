import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import 'agent_screen.dart';
import 'agent_service.dart';

/// Abre el chat con TAIA (RF-AGT-23). Devuelve cuando el estudiante vuelve,
/// para que la pantalla actualice lo que el agente pudo haber cambiado.
Future<void> openTaiaChat(BuildContext context, {AgentService? service}) {
  HapticFeedback.selectionClick();
  return Navigator.of(context).push(
    MaterialPageRoute<void>(builder: (_) => AgentScreen(service: service)),
  );
}

/// TAIA pequeña, sin recuadro, que abre el chat al tocarla (RF-AGT-23). Va en
/// la cabecera de las pantallas principales.
class TaiaChatButton extends StatelessWidget {
  const TaiaChatButton({
    super.key,
    this.expression = MascotExpression.normal,
    this.size = 64,
    this.service,
    this.onClosed,
  });

  final MascotExpression expression;
  final double size;
  final AgentService? service;

  /// Se llama al volver del chat.
  final VoidCallback? onClosed;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: 'Habla con TAIA',
      child: Semantics(
        button: true,
        label: 'Habla con TAIA',
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () async {
            await openTaiaChat(context, service: service);
            onClosed?.call();
          },
          child: SizedBox.square(
            dimension: size,
            child: TaiaMascot(motion: 0.6, expression: expression),
          ),
        ),
      ),
    );
  }
}
