import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../features/auth/options_screen.dart';
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
            // El botón va anclado abajo, fuera de la columna, para que en
            // pantallas bajas se superponga en vez de desbordar.
            SafeArea(
              child: Align(
                alignment: Alignment.bottomCenter,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(32, 0, 32, 32),
                  child: _Reveal(
                    parent: _enter,
                    interval: const Interval(0.65, 1),
                    child: const _StartButton(),
                  ),
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

/// "Empezar →": lleva a la pantalla de registro / inicio de sesión.
class _StartButton extends StatelessWidget {
  const _StartButton();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: FilledButton(
        style: FilledButton.styleFrom(
          backgroundColor: TaiaColors.ivoryMist,
          foregroundColor: TaiaColors.fieryRose,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
        ),
        onPressed: () => Navigator.of(context).push(
          PageRouteBuilder<void>(
            transitionDuration: const Duration(milliseconds: 500),
            pageBuilder: (context, animation, secondaryAnimation) =>
                const OptionsScreen(),
            transitionsBuilder: (
              context,
              animation,
              secondaryAnimation,
              child,
            ) => FadeTransition(opacity: animation, child: child),
          ),
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Empezar', style: TextStyle(fontWeight: FontWeight.w800)),
            SizedBox(width: 8),
            Icon(Icons.arrow_forward_rounded),
          ],
        ),
      ),
    );
  }
}