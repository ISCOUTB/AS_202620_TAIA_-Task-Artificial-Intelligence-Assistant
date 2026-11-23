import 'package:confetti/confetti.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/taia_colors.dart';
import 'motion.dart';

/// Controlador de confeti con la duración de TAIA (RNF-14).
ConfettiController taiaConfettiController() =>
    ConfettiController(duration: const Duration(milliseconds: 500));

/// Celebra: vibración y confeti, salvo que se reduzca el movimiento (RNF-14).
void celebrate(BuildContext context, ConfettiController controller) {
  HapticFeedback.mediumImpact();
  if (!reduceMotion(context)) controller.play();
}

/// Confeti con los colores de TAIA. Va encima del contenido, arriba al centro.
class TaiaConfetti extends StatelessWidget {
  const TaiaConfetti({super.key, required this.controller});

  final ConfettiController controller;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topCenter,
      child: IgnorePointer(
        child: ConfettiWidget(
          confettiController: controller,
          blastDirectionality: BlastDirectionality.explosive,
          emissionFrequency: 0,
          numberOfParticles: 22,
          minBlastForce: 8,
          maxBlastForce: 22,
          gravity: 0.25,
          shouldLoop: false,
          colors: const [
            TaiaColors.fieryRose,
            TaiaColors.sunsetCoral,
            TaiaColors.apricotWhisper,
            TaiaColors.softPeach,
            TaiaColors.mascotPink,
          ],
        ),
      ),
    );
  }
}
