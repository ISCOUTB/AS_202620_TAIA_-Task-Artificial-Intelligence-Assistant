import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../features/shell/app_entry.dart';
import '../mascot/taia_mascot.dart';
import '../welcome/welcome_screen.dart';
import 'splash_background.dart';
import 'taia_wordmark.dart';

/// Splash de carga: entrada animada del fondo, la mascota y el logotipo, los
/// tentáculos en movimiento mientras carga y transición a la bienvenida.
///
/// Se muestra al menos [minDisplay] y, si se pasa [loading], hasta que termine.
///
/// Si [sessionCheck] encuentra una sesión guardada, entra directo a la app
/// ([signedIn]); si no, pasa a la bienvenida (RF-USR-03). Un token vencido se
/// renueva solo en la primera petición, y si ya no sirve, `sessionEvents`
/// devuelve a la bienvenida.
class SplashScreen extends StatefulWidget {
  const SplashScreen({
    super.key,
    this.minDisplay = const Duration(milliseconds: 3200),
    this.loading,
    this.sessionCheck,
    this.signedIn,
  });

  final Duration minDisplay;
  final Future<void>? loading;
  final Future<bool> Function()? sessionCheck;

  /// Pantalla con la sesión abierta. Por defecto, [AppEntry].
  final WidgetBuilder? signedIn;

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _intro = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1800),
  );

  @override
  void initState() {
    super.initState();
    _intro.forward();
    _continueWhenReady();
  }

  Future<bool> _hasSession() async {
    final check = widget.sessionCheck;
    if (check == null) return false;
    try {
      return await check();
    } catch (_) {
      // Si el almacenamiento seguro falla, se pide iniciar sesión.
      return false;
    }
  }

  Future<void> _continueWhenReady() async {
    final session = _hasSession();
    await Future.wait([
      Future<void>.delayed(widget.minDisplay),
      if (widget.loading != null) widget.loading!,
    ]);
    final signedIn = await session;
    if (!mounted) return;
    final next = signedIn
        ? (widget.signedIn ?? (_) => const AppEntry())
        : (_) => const WelcomeScreen();
    Navigator.of(context).pushReplacement(
      PageRouteBuilder<void>(
        transitionDuration: const Duration(milliseconds: 900),
        pageBuilder: (context, _, _) => next(context),
        transitionsBuilder: (_, animation, _, child) => FadeTransition(
          opacity: CurvedAnimation(parent: animation, curve: Curves.easeOut),
          child: child,
        ),
      ),
    );
  }

  @override
  void dispose() {
    _intro.dispose();
    super.dispose();
  }

  double _interval(double begin, double end) =>
      ((_intro.value - begin) / (end - begin)).clamp(0.0, 1.0);

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        body: AnimatedBuilder(
          animation: _intro,
          builder: (context, _) => LayoutBuilder(
            builder: (context, constraints) {
              final w = constraints.maxWidth, h = constraints.maxHeight;
              final mascotWidth = w * 0.6;
              final mascotTop = h * 0.3;
              final mascotHeight = mascotWidth / TaiaMascot.aspectRatio;
              final wordmarkWidth = w * 0.36;
              final wordmarkTop = mascotTop + mascotHeight + h * 0.03;

              final pop = Curves.elasticOut.transform(_interval(0.15, 0.7));
              return Stack(
                children: [
                  SplashBackground(progress: _interval(0, 0.45)),
                  Positioned(
                    left: (w - mascotWidth) / 2,
                    top: mascotTop,
                    width: mascotWidth,
                    child: Opacity(
                      opacity: _interval(0.15, 0.3),
                      child: Transform.scale(
                        scale: 0.3 + 0.7 * pop,
                        child: Hero(
                          tag: 'taia-mascot',
                          child: TaiaMascot(
                            motion: _interval(0.5, 1),
                            silhouette: true,
                          ),
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    left: w / 2 + mascotWidth * 0.36,
                    top: mascotTop - w * 0.03,
                    width: w * 0.13,
                    child: Sparkles(progress: _interval(0.7, 1)),
                  ),
                  Positioned(
                    left: (w - wordmarkWidth) / 2,
                    top: wordmarkTop,
                    width: wordmarkWidth,
                    child: TaiaWordmark(progress: _interval(0.45, 0.95)),
                  ),
                  Positioned(
                    left: w / 2 + wordmarkWidth / 2,
                    top: wordmarkTop - w * 0.05,
                    width: w * 0.07,
                    child: Sparkles(progress: _interval(0.82, 1)),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}
