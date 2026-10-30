import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../theme/taia_colors.dart';

/// Logotipo "TAIA" dibujado como vector. Con [progress] entre 0 y 1 las letras
/// entran una tras otra, subiendo y apareciendo.
class TaiaWordmark extends StatelessWidget {
  const TaiaWordmark({super.key, this.progress = 1});

  final double progress;

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: _width / _height,
      child: CustomPaint(painter: _WordmarkPainter(progress)),
    );
  }
}

const double _width = 330, _height = 104;

class _WordmarkPainter extends CustomPainter {
  _WordmarkPainter(this.progress);

  final double progress;

  // Trazos de cada letra en un lienzo de 330 x 104.
  static const _letters = [
    [Offset(14, 16), Offset(88, 16), Offset(51, 16), Offset(51, 88)],
    [Offset(108, 88), Offset(144, 16), Offset(144, 16), Offset(180, 88)],
    [Offset(208, 16), Offset(208, 88)],
    [Offset(236, 88), Offset(272, 16), Offset(272, 16), Offset(308, 88)],
  ];

  @override
  void paint(Canvas canvas, Size size) {
    canvas.scale(size.width / _width);
    for (var i = 0; i < _letters.length; i++) {
      final start = i * 0.15;
      final t = Curves.easeOutBack.transform(
        ((progress - start) / 0.55).clamp(0.0, 1.0),
      );
      if (t <= 0) continue;
      final paint = Paint()
        ..color = TaiaColors.ivoryMist.withValues(alpha: t.clamp(0.0, 1.0))
        ..style = PaintingStyle.stroke
        ..strokeWidth = 24
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round;
      final path = Path();
      final points = _letters[i];
      for (var k = 0; k < points.length; k += 2) {
        path
          ..moveTo(points[k].dx, points[k].dy)
          ..lineTo(points[k + 1].dx, points[k + 1].dy);
      }
      canvas
        ..save()
        ..translate(0, (1 - t) * 40)
        ..drawPath(path, paint)
        ..restore();
    }
  }

  @override
  bool shouldRepaint(_WordmarkPainter oldDelegate) =>
      oldDelegate.progress != progress;
}

/// Tres destellos que salen de la esquina inferior izquierda hacia arriba a la
/// derecha. Con [progress] crecen desde el origen.
class Sparkles extends StatelessWidget {
  const Sparkles({super.key, required this.progress});

  final double progress;

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 1,
      child: CustomPaint(painter: _SparklesPainter(progress)),
    );
  }
}

class _SparklesPainter extends CustomPainter {
  _SparklesPainter(this.progress);

  final double progress;

  @override
  void paint(Canvas canvas, Size size) {
    final t = Curves.elasticOut.transform(progress.clamp(0.0, 1.0));
    if (t <= 0) return;
    final s = size.width;
    final paint = Paint()
      ..color = TaiaColors.ivoryMist.withValues(alpha: progress.clamp(0.0, 1.0))
      ..strokeWidth = s * 0.09
      ..strokeCap = StrokeCap.round;
    final origin = Offset(s * 0.1, s * 0.9);
    for (final degrees in const [-80.0, -45.0, -10.0]) {
      final dir = Offset.fromDirection(degrees * math.pi / 180);
      final from = origin + dir * (s * 0.45);
      final to = origin + dir * (s * (0.45 + 0.35 * t));
      canvas.drawLine(from, to, paint);
    }
  }

  @override
  bool shouldRepaint(_SparklesPainter oldDelegate) =>
      oldDelegate.progress != progress;
}
