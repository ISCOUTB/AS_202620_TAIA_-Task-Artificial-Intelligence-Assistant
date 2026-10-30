import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../theme/taia_colors.dart';

/// Fondo en el color principal con ondas en las esquinas y trazos decorativos. Con [progress]
/// entre 0 y 1 las ondas entran desde los bordes y los trazos aparecen.
class SplashBackground extends StatelessWidget {
  const SplashBackground({super.key, this.progress = 1});

  final double progress;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: _BackgroundPainter(progress),
      child: const SizedBox.expand(),
    );
  }
}

class _BackgroundPainter extends CustomPainter {
  _BackgroundPainter(this.progress);

  final double progress;

  // Ondas: el principal aclarado con el color de fondo o con el acento 1.
  static final _top = Color.lerp(
    TaiaColors.fieryRose,
    TaiaColors.ivoryMist,
    0.12,
  )!;
  static final _waveSoft = Color.lerp(
    TaiaColors.fieryRose,
    TaiaColors.ivoryMist,
    0.24,
  )!;
  static final _waveLight = Color.lerp(
    TaiaColors.fieryRose,
    TaiaColors.ivoryMist,
    0.38,
  )!;
  static final _wavePeach = Color.lerp(
    TaiaColors.fieryRose,
    TaiaColors.softPeach,
    0.8,
  )!;

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width, h = size.height;
    final p = Curves.easeOutCubic.transform(progress.clamp(0.0, 1.0));
    canvas.drawRect(
      Offset.zero & size,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.center,
          colors: [_top, TaiaColors.fieryRose],
        ).createShader(Offset.zero & size),
    );

    // Ondas superiores izquierdas.
    canvas
      ..save()
      ..translate(-(1 - p) * w * 0.5, -(1 - p) * h * 0.2);
    canvas.drawPath(
      Path()
        ..moveTo(0, 0)
        ..lineTo(w * 0.78, 0)
        ..cubicTo(w * 0.62, h * 0.06, w * 0.5, h * 0.08, w * 0.34, h * 0.13)
        ..cubicTo(w * 0.2, h * 0.17, w * 0.1, h * 0.24, 0, h * 0.27)
        ..close(),
      Paint()..color = _waveSoft,
    );
    canvas.drawPath(
      Path()
        ..moveTo(0, 0)
        ..lineTo(w * 0.55, 0)
        ..cubicTo(w * 0.42, h * 0.05, w * 0.3, h * 0.06, w * 0.2, h * 0.1)
        ..cubicTo(w * 0.1, h * 0.13, w * 0.05, h * 0.17, 0, h * 0.19)
        ..close(),
      Paint()..color = _waveLight,
    );
    canvas.restore();

    // Ondas inferiores.
    canvas
      ..save()
      ..translate(0, (1 - p) * h * 0.25);
    canvas.drawPath(
      Path()
        ..moveTo(0, h * 0.8)
        ..cubicTo(w * 0.25, h * 0.76, w * 0.45, h * 0.86, w * 0.7, h * 0.84)
        ..cubicTo(w * 0.85, h * 0.83, w * 0.95, h * 0.8, w, h * 0.79)
        ..lineTo(w, h)
        ..lineTo(0, h)
        ..close(),
      Paint()..color = _waveSoft,
    );
    canvas.drawPath(
      Path()
        ..moveTo(0, h * 0.86)
        ..cubicTo(w * 0.18, h * 0.85, w * 0.32, h * 0.9, w * 0.36, h)
        ..lineTo(0, h)
        ..close(),
      Paint()..color = _waveLight,
    );
    canvas.drawPath(
      Path()
        ..moveTo(w * 0.5, h)
        ..cubicTo(w * 0.62, h * 0.93, w * 0.8, h * 0.9, w, h * 0.86)
        ..lineTo(w, h)
        ..close(),
      Paint()..color = _wavePeach,
    );
    canvas.restore();

    // Trazos decorativos arriba a la derecha y abajo a la izquierda.
    final fade = ((progress - 0.4) / 0.6).clamp(0.0, 1.0);
    if (fade > 0) {
      final dash = Paint()
        ..color = Colors.white.withValues(alpha: 0.35 * fade)
        ..strokeWidth = w * 0.022
        ..strokeCap = StrokeCap.round;
      _dashes(canvas, dash, Offset(w * 0.8, h * 0.1), w * 0.06);
      _dashes(canvas, dash, Offset(w * 0.12, h * 0.9), w * 0.05);
    }
  }

  // Dos filas de dos trazos inclinados.
  void _dashes(Canvas canvas, Paint paint, Offset center, double length) {
    final dir = Offset.fromDirection(math.pi / 5) * (length / 2);
    for (final row in const [-1.0, 1.0]) {
      for (final col in const [-1.0, 1.0]) {
        final c =
            center +
            Offset(col * length * 0.9 - row * length * 0.3, row * length * 0.7);
        canvas.drawLine(c - dir, c + dir, paint);
      }
    }
  }

  @override
  bool shouldRepaint(_BackgroundPainter oldDelegate) =>
      oldDelegate.progress != progress;
}
