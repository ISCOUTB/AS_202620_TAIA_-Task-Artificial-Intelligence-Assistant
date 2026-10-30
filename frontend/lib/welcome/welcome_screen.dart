import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../mascot/taia_mascot.dart';
import '../splash/splash_background.dart';
import '../theme/taia_colors.dart';

/// Pantalla de bienvenida provisional. Recibe a la mascota desde el splash y
/// muestra el saludo; se reemplaza cuando exista el diseño definitivo.
class WelcomeScreen extends StatefulWidget {
  const WelcomeScreen({super.key});

  @override
  State<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends State<WelcomeScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _enter = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1100),
  )..forward();

  @override
  void dispose() {
    _enter.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        body: Stack(
          children: [
            const SplashBackground(),
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 32),
                child: Column(
                  children: [
                    const Spacer(),
                    FractionallySizedBox(
                      widthFactor: 0.55,
                      child: const Hero(
                        tag: 'taia-mascot',
                        child: TaiaMascot(motion: 0.6),
                      ),
                    ),
                    const SizedBox(height: 32),
                    _Reveal(
                      parent: _enter,
                      interval: const Interval(0.3, 0.75),
                      child: Text(
                        'Te damos la bienvenida a TAIA',
                        textAlign: TextAlign.center,
                        style: text.headlineSmall?.copyWith(
                          color: TaiaColors.ivoryMist,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    _Reveal(
                      parent: _enter,
                      interval: const Interval(0.5, 0.95),
                      child: Text(
                        'Tu asistente académico para organizar tareas, '
                        'exámenes y horarios.',
                        textAlign: TextAlign.center,
                        style: text.bodyLarge?.copyWith(
                          color: TaiaColors.ivoryMist,
                        ),
                      ),
                    ),
                    const Spacer(flex: 2),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Aparece subiendo dentro del intervalo indicado de [parent].
class _Reveal extends StatelessWidget {
  const _Reveal({
    required this.parent,
    required this.interval,
    required this.child,
  });

  final Animation<double> parent;
  final Interval interval;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final curve = CurvedAnimation(
      parent: parent,
      curve: Interval(interval.begin, interval.end, curve: Curves.easeOutCubic),
    );
    return FadeTransition(
      opacity: curve,
      child: SlideTransition(
        position: Tween(
          begin: const Offset(0, 0.4),
          end: Offset.zero,
        ).animate(curve),
        child: child,
      ),
    );
  }
}
