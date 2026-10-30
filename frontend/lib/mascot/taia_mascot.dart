import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../theme/taia_colors.dart';
import 'mascot_geometry.dart';

/// Mascota TAIA con los tentáculos en movimiento.
///
/// Cada tentáculo se dobla a lo largo de su eje con una onda que va de la base
/// a la punta, y la mascota sube y baja levemente. [motion] escala el
/// movimiento: 0 la deja quieta y 1 aplica la amplitud completa.
class TaiaMascot extends StatefulWidget {
  const TaiaMascot({super.key, this.motion = 1});

  final double motion;

  /// Proporción ancho / alto del lienzo, incluido el margen para el movimiento.
  static const aspectRatio = _viewWidth / _viewHeight;

  @override
  State<TaiaMascot> createState() => _TaiaMascotState();
}

const double _viewLeft = -30, _viewTop = -40;
const double _viewWidth = 1260, _viewHeight = 1170;

class _TaiaMascotState extends State<TaiaMascot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _cycle = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 2),
  )..repeat();

  @override
  void dispose() {
    _cycle.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: TaiaMascot.aspectRatio,
      child: CustomPaint(
        painter: _MascotPainter(cycle: _cycle, motion: widget.motion),
      ),
    );
  }
}

class _MascotPainter extends CustomPainter {
  _MascotPainter({required this.cycle, required this.motion})
    : super(repaint: cycle);

  final Animation<double> cycle;
  final double motion;

  static final _body = _decode(bodyPath);
  static final _bowTop = _decode(bowTopPath);
  static final _bowBack = _decode(bowBackPath);
  static final _bowPink = _decode(bowPinkPath);
  static final _eyes = _decode(eyeLeftPath)
    ..addPath(_decode(eyeRightPath), Offset.zero);

  // Orden de dibujo: izquierdo, derecho, inferior izquierdo, inferior derecho.
  // La fase desfasa cada tentáculo un cuarto de ciclo para formar una onda.
  static final _tentacles = [
    _Tentacle(
      tentacleLeftSpine,
      tentacleLeftFill,
      tentacleLeftBinds,
      amp: 16,
      curl: 12,
      phase: 0,
      sign: 1,
    ),
    _Tentacle(
      tentacleRightSpine,
      tentacleRightFill,
      tentacleRightBinds,
      amp: 16,
      curl: 12,
      phase: 0.75,
      sign: -1,
    ),
    _Tentacle(
      tentacleBottomLeftSpine,
      tentacleBottomLeftFill,
      tentacleBottomLeftBinds,
      amp: 14,
      curl: 10,
      phase: 0.25,
      sign: 1,
    ),
    _Tentacle(
      tentacleBottomRightSpine,
      tentacleBottomRightFill,
      tentacleBottomRightBinds,
      amp: 14,
      curl: 10,
      phase: 0.5,
      sign: -1,
    ),
  ];

  static final _cream = Paint()..color = TaiaColors.ivoryMist;
  static final _red = Paint()..color = TaiaColors.mascotRed;
  static final _pink = Paint()..color = TaiaColors.mascotPink;
  static final _lens = Paint()
    ..color = TaiaColors.mascotRed
    ..style = PaintingStyle.stroke
    ..strokeWidth = 38;
  static final _eyeStroke = Paint()
    ..color = TaiaColors.mascotRed
    ..style = PaintingStyle.stroke
    ..strokeWidth = 37
    ..strokeCap = StrokeCap.round;

  @override
  void paint(Canvas canvas, Size size) {
    final t = cycle.value;
    final bob = math.sin(2 * math.pi * t) * 8 * motion;
    canvas
      ..save()
      ..scale(size.width / _viewWidth)
      ..translate(-_viewLeft, -_viewTop + bob);

    for (final tentacle in _tentacles) {
      tentacle.paint(canvas, _cream, t, motion);
    }
    canvas
      ..drawPath(_body, _cream)
      ..drawOval(const Rect.fromLTWH(264, 321, 330, 315), _lens)
      ..drawOval(const Rect.fromLTWH(664, 317, 341, 324), _lens)
      ..drawRect(const Rect.fromLTWH(606, 434, 46, 35), _red)
      ..drawPath(_eyes, _eyeStroke)
      ..drawPath(_bowTop, _red)
      ..drawPath(_bowBack, _red)
      ..drawPath(_bowPink, _pink)
      ..drawCircle(const Offset(297, 218), 52, _cream)
      ..restore();
  }

  @override
  bool shouldRepaint(_MascotPainter oldDelegate) =>
      oldDelegate.motion != motion || oldDelegate.cycle != cycle;
}

/// Tentáculo articulado: un eje de segmentos de 3 px y un contorno amarrado a
/// él. Al girar cada segmento un poco más que el anterior, el tentáculo se
/// curva en lugar de rotar como una pieza rígida.
class _Tentacle {
  _Tentacle(
    List<double> spine,
    this._fill,
    this._binds, {
    required this.amp,
    required this.curl,
    required this.phase,
    required this.sign,
  }) : _origin = Offset(spine[0], spine[1]),
       _length = Float64List(spine.length ~/ 2 - 1),
       _angle = Float64List(spine.length ~/ 2 - 1),
       _reach = Float64List(spine.length ~/ 2 - 1) {
    final n = _length.length;
    final mid = Float64List(n);
    var acc = 0.0;
    for (var i = 0; i < n; i++) {
      final dx = spine[2 * i + 2] - spine[2 * i];
      final dy = spine[2 * i + 3] - spine[2 * i + 1];
      _length[i] = math.sqrt(dx * dx + dy * dy);
      _angle[i] = math.atan2(dy, dx);
      mid[i] = acc + _length[i] / 2;
      acc += _length[i];
    }
    // _reach: 0 en la unión con el cuerpo y 1 en la punta. El tramo anterior
    // a la unión queda oculto bajo el cuerpo y no se mueve.
    final last = mid[n - 1];
    for (var i = 0; i < n; i++) {
      _reach[i] = math.max(
        0,
        (mid[i] - _hiddenLength) / (last - _hiddenLength),
      );
    }
  }

  static const double _hiddenLength = 70;
  static const double _waveNumber = 2.4;

  final List<double> _fill;
  final List<double> _binds;
  final double amp, curl, phase, sign;
  final Offset _origin;
  final Float64List _length, _angle, _reach;

  void paint(Canvas canvas, Paint paint, double t, double motion) {
    final n = _length.length;
    final cos = Float64List(n), sin = Float64List(n);
    final qx = Float64List(n + 1), qy = Float64List(n + 1);
    qx[0] = _origin.dx;
    qy[0] = _origin.dy;
    final ph = 2 * math.pi * (t + phase);
    for (var i = 0; i < n; i++) {
      final x = _reach[i];
      final wave = ph - _waveNumber * x;
      final bend =
          amp * math.pow(x, 1.3) * math.sin(wave) +
          curl * x * x * math.sin(wave - 1.2);
      final a = _angle[i] + sign * motion * bend * math.pi / 180;
      cos[i] = math.cos(a);
      sin[i] = math.sin(a);
      qx[i + 1] = qx[i] + _length[i] * cos[i];
      qy[i + 1] = qy[i] + _length[i] * sin[i];
    }

    final outline = Path();
    for (var k = 0; k < _binds.length; k += 3) {
      final j = _binds[k].toInt();
      final u = _binds[k + 1], v = _binds[k + 2];
      final px = qx[j] + u * cos[j] - v * sin[j];
      final py = qy[j] + u * sin[j] + v * cos[j];
      k == 0 ? outline.moveTo(px, py) : outline.lineTo(px, py);
    }
    canvas.drawPath(outline..close(), paint);
    // Relleno de la base: cubre la unión con el cuerpo mientras se dobla.
    for (var j = 0; j < _fill.length; j++) {
      canvas.drawCircle(Offset(qx[j], qy[j]), _fill[j], paint);
    }
  }
}

Path _decode(List<double> data) {
  final path = Path();
  var i = 0;
  while (i < data.length) {
    switch (data[i].toInt()) {
      case 0:
        path.moveTo(data[i + 1], data[i + 2]);
        i += 3;
      case 1:
        path.lineTo(data[i + 1], data[i + 2]);
        i += 3;
      case 2:
        path.cubicTo(
          data[i + 1],
          data[i + 2],
          data[i + 3],
          data[i + 4],
          data[i + 5],
          data[i + 6],
        );
        i += 7;
      default:
        path.close();
        i += 1;
    }
  }
  return path;
}
