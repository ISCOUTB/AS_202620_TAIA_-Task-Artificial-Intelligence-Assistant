import 'package:animations/animations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Movimiento de la app (RNF-14): entradas cortas, de 300 ms o menos, que se
/// apagan si el sistema pide reducir el movimiento.

/// Duración de las entradas y transiciones.
const motionDuration = Duration(milliseconds: 260);

/// ¿El sistema pidió reducir el movimiento?
bool reduceMotion(BuildContext context) =>
    MediaQuery.maybeOf(context)?.disableAnimations ?? false;

extension TaiaAppear on Widget {
  /// Aparece subiendo un poco. [index] escalona las entradas de una lista; a
  /// partir del octavo elemento ya no espera más.
  Widget appear(BuildContext context, {int index = 0}) {
    if (reduceMotion(context)) return this;
    final delay = Duration(milliseconds: 45 * index.clamp(0, 8));
    return animate(delay: delay)
        .fadeIn(duration: motionDuration, curve: Curves.easeOut)
        .slideY(
          begin: 0.06,
          end: 0,
          duration: motionDuration,
          curve: Curves.easeOutCubic,
        );
  }
}

/// Transición entre pantallas: deslizamiento horizontal con desvanecido, de la
/// librería `animations` de Google.
const taiaPageTransitions = PageTransitionsTheme(
  builders: {
    TargetPlatform.android: SharedAxisPageTransitionsBuilder(
      transitionType: SharedAxisTransitionType.horizontal,
    ),
    TargetPlatform.iOS: SharedAxisPageTransitionsBuilder(
      transitionType: SharedAxisTransitionType.horizontal,
    ),
  },
);
