import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_shell.dart';

/// Estado de carga o de error de una pantalla, con la mascota sobre un fondo
/// rosa (la mascota es crema y se perdería sobre el fondo claro).
class MascotMessage extends StatelessWidget {
  const MascotMessage({
    super.key,
    required this.expression,
    required this.text,
    this.showSpinner = false,
    this.onRetry,
  });

  final MascotExpression expression;
  final String text;
  final bool showSpinner;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 200,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: TaiaColors.fieryRose,
                borderRadius: BorderRadius.circular(32),
              ),
              child: TaiaMascot(motion: 0.6, expression: expression),
            ),
            const SizedBox(height: 16),
            Text(
              text,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: taiaInk,
                fontSize: 16,
                fontWeight: FontWeight.w700,
              ),
            ),
            if (showSpinner) ...[
              const SizedBox(height: 16),
              const CircularProgressIndicator(color: TaiaColors.fieryRose),
            ],
            if (onRetry != null) ...[
              const SizedBox(height: 16),
              FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: TaiaColors.fieryRose,
                ),
                onPressed: onRetry,
                child: const Text('Reintentar'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}