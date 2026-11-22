import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../theme/taia_colors.dart';
import 'mascot_expression.dart';
import 'mascot_geometry.dart';

/// Mascota TAIA con los tentáculos en movimiento.
///
/// Cada tentáculo se dobla a lo largo de su eje con una onda que va de la base
/// a la punta, y la mascota sube y baja levemente. [motion] escala el
/// movimiento: 0 la deja quieta y 1 aplica la amplitud completa.
///
/// [expression] cambia el rostro (y los útiles escolares). Al cambiar, la
/// mascota da un pequeño rebote para que se note la reacción.
///
/// Por defecto muestra la pose ilustrada de `assets/mascot/`, que flota y se
/// balancea. Con [silhouette] dibuja la silueta vectorial clara, la que se usa
/// sobre el fondo rosado del splash, la bienvenida y el inicio de sesión.
class TaiaMascot extends StatefulWidget {
  const TaiaMascot({
    super.key,
    this.motion = 1,
    this.expression = MascotExpression.normal,
    this.silhouette = false,
  });

  final double motion;
  final MascotExpression expression;
  final bool silhouette;

  /// Proporción ancho / alto del lienzo, incluido el margen para el movimiento.
  static const aspectRatio = _viewWidth / _viewHeight;

  @override
  State<TaiaMascot> createState() => _TaiaMascotState();
}

const double _viewLeft = -30, _viewTop = -40;
const double _viewWidth = 1260, _viewHeight = 1170;

class _TaiaMascotState extends State<TaiaMascot> with TickerProviderStateMixin {
  late final AnimationController _cycle = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 2),
  )..repeat();

  // Rebote al cambiar de expresión. Empieza en 1 (reposo).
  late final AnimationController _pop = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 600),
    value: 1,
  );

  @override
  void didUpdateWidget(TaiaMascot oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.expression != widget.expression) {
      _pop.forward(from: 0);
    }
  }

  @override
  void dispose() {
    _cycle.dispose();
    _pop.dispose();
    super.dispose();
  }

  Widget _pose(BuildContext context) {
    final asset = widget.expression.asset;
    final image = AnimatedSwitcher(
      duration: const Duration(milliseconds: 220),
      child: Image.asset(
        asset,
        key: ValueKey(asset),
        fit: BoxFit.contain,
        gaplessPlayback: true,
        filterQuality: FilterQuality.medium,
      ),
    );
    final still = MediaQuery.maybeDisableAnimationsOf(context) ?? false;
    final motion = still ? 0.0 : widget.motion;
    return AnimatedBuilder(
      animation: Listenable.merge([_cycle, _pop]),
      builder: (context, child) {
        final t = _cycle.value * 2 * math.pi;
        final bounce = Curves.elasticOut.transform(_pop.value);
        // Flota, se balancea desde la base y "respira" un poco.
        return FractionalTranslation(
          translation: Offset(0, -0.025 * motion * math.sin(t)),
          child: Transform.rotate(
            angle: 0.04 * motion * math.sin(t + 0.9),
            alignment: Alignment.bottomCenter,
            child: Transform.scale(
              scale:
                  (0.9 + 0.1 * bounce) * (1 + 0.02 * motion * math.sin(2 * t)),
              alignment: Alignment.bottomCenter,
              child: child,
            ),
          ),
        );
      },
      child: AspectRatio(aspectRatio: 1, child: image),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.silhouette) return _pose(context);
    return AnimatedBuilder(
      animation: _pop,
      builder: (context, child) {
        final bounce = Curves.elasticOut.transform(_pop.value);
        return Transform.scale(
          scale: 0.92 + 0.08 * bounce,
          alignment: Alignment.bottomCenter,
          child: child,
        );
      },
      child: AspectRatio(
        aspectRatio: TaiaMascot.aspectRatio,
        child: CustomPaint(
          painter: _MascotPainter(
            cycle: _cycle,
            motion: widget.motion,
            expression: widget.expression.silhouette,
          ),
        ),
      ),
    );
  }
}

class _MascotPainter extends CustomPainter {
  _MascotPainter({
    required this.cycle,
    required this.motion,
    required this.expression,
  }) : super(repaint: cycle);

  final Animation<double> cycle;
  final double motion;
  final MascotExpression expression;

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
  static final _white = Paint()..color = Colors.white;
  static final _apricot = Paint()..color = TaiaColors.apricotWhisper;
  static final _lens = Paint()
    ..color = TaiaColors.mascotRed
    ..style = PaintingStyle.stroke
    ..strokeWidth = 38;
  static final _eyeStroke = Paint()
    ..color = TaiaColors.mascotRed
    ..style = PaintingStyle.stroke
    ..strokeWidth = 37
    ..strokeCap = StrokeCap.round
    ..strokeJoin = StrokeJoin.round;
  static final _mouthStroke = _line(TaiaColors.mascotRed, 30);
  static final _wavyStroke = _line(TaiaColors.mascotRed, 28);
  static final _sparkle = _line(TaiaColors.ivoryMist, 30);
  static final _peachLine = _line(TaiaColors.softPeach, 14);
  static final _redLine = _line(TaiaColors.mascotRed, 14);

  static Paint _line(Color color, double width) => Paint()
    ..color = color
    ..style = PaintingStyle.stroke
    ..strokeWidth = width
    ..strokeCap = StrokeCap.round
    ..strokeJoin = StrokeJoin.round;

  // Centros de los ojos dentro de los lentes.
  static const double _leftEyeX = 442.5, _rightEyeX = 824, _eyeY = 482;

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
      ..drawRect(const Rect.fromLTWH(606, 434, 46, 35), _red);

    _paintFace(canvas, _blink(t));

    canvas
      ..drawPath(_bowTop, _red)
      ..drawPath(_bowBack, _red)
      ..drawPath(_bowPink, _pink)
      ..drawCircle(const Offset(297, 218), 52, _cream);

    _paintExtras(canvas);
    canvas.restore();
  }

  /// 1 con el ojo abierto; baja un instante una vez por ciclo (parpadeo).
  double _blink(double t) {
    final d = (t - 0.95).abs();
    return d < 0.025 ? 0.15 + 0.85 * (d / 0.025) : 1;
  }

  void _paintFace(Canvas canvas, double blink) {
    // Las poses que solo existen ilustradas usan la silueta más parecida.
    switch (expression.silhouette) {
      case MascotExpression.normal:
        canvas.drawPath(_eyes, _eyeStroke);
      case MascotExpression.happy:
      case MascotExpression.studying:
      case MascotExpression.organizing:
        canvas
          ..drawPath(_arch(_leftEyeX, 510), _eyeStroke)
          ..drawPath(_arch(_rightEyeX, 510), _eyeStroke);
      case MascotExpression.reading:
        // Ojos hacia abajo: lee con una sonrisa tranquila.
        canvas
          ..drawPath(_arch(_leftEyeX, 470, down: true), _eyeStroke)
          ..drawPath(_arch(_rightEyeX, 470, down: true), _eyeStroke);
      case MascotExpression.thinking:
        _pupil(canvas, const Offset(_leftEyeX + 26, _eyeY - 30), 66, blink);
        _pupil(canvas, const Offset(_rightEyeX + 26, _eyeY - 30), 66, blink);
      case MascotExpression.surprised:
        _pupil(canvas, const Offset(_leftEyeX, _eyeY), 82, blink);
        _pupil(canvas, const Offset(_rightEyeX, _eyeY), 82, blink);
      case MascotExpression.wink:
        canvas.drawPath(_arch(_leftEyeX, 510), _eyeStroke);
        _pupil(canvas, const Offset(_rightEyeX, _eyeY), 72, blink);
      case MascotExpression.excited:
        canvas
          ..drawPath(
            _chevron(_leftEyeX - 5, _eyeY, pointsRight: true),
            _eyeStroke,
          )
          ..drawPath(
            _chevron(_rightEyeX + 5, _eyeY, pointsRight: false),
            _eyeStroke,
          );
      case MascotExpression.laptop:
      case MascotExpression.resting:
      case MascotExpression.books:
        break;
    }

    switch (expression.silhouette) {
      case MascotExpression.normal:
      case MascotExpression.laptop:
      case MascotExpression.resting:
      case MascotExpression.books:
        break;
      case MascotExpression.happy:
        _openMouth(canvas, 62);
      case MascotExpression.excited:
        _openMouth(canvas, 74);
      case MascotExpression.surprised:
        canvas.drawOval(
          Rect.fromCenter(
            center: const Offset(629, 722),
            width: 66,
            height: 82,
          ),
          _red,
        );
      case MascotExpression.thinking:
        final wavy = Path()
          ..moveTo(575, 728)
          ..cubicTo(605, 696, 650, 750, 686, 712);
        canvas.drawPath(wavy, _wavyStroke);
      case MascotExpression.wink:
      case MascotExpression.studying:
      case MascotExpression.organizing:
      case MascotExpression.reading:
        final smile = Path()
          ..moveTo(570, 702)
          ..quadraticBezierTo(629, 758, 688, 702);
        canvas.drawPath(smile, _mouthStroke);
    }
  }

  /// Destellos, signo de pregunta y útiles escolares.
  void _paintExtras(Canvas canvas) {
    switch (expression.silhouette) {
      case MascotExpression.surprised:
      case MascotExpression.wink:
      case MascotExpression.excited:
        _paintSparkles(canvas);
      case MascotExpression.thinking:
        _paintQuestionMark(canvas);
      case MascotExpression.studying:
        _paintNotebook(canvas);
        _paintPencil(canvas);
      case MascotExpression.organizing:
        _paintChecklist(canvas);
      case MascotExpression.reading:
        _paintBook(canvas);
      case MascotExpression.normal:
      case MascotExpression.happy:
      case MascotExpression.laptop:
      case MascotExpression.resting:
      case MascotExpression.books:
        break;
    }
  }

  Path _arch(double cx, double base, {bool down = false}) {
    final f = down ? -1.0 : 1.0;
    return Path()
      ..moveTo(cx - 68.4, base)
      ..cubicTo(
        cx - 61.3,
        base - 32.1 * f,
        cx - 32.9,
        base - 55 * f,
        cx,
        base - 55 * f,
      )
      ..cubicTo(
        cx + 32.9,
        base - 55 * f,
        cx + 61.3,
        base - 32.1 * f,
        cx + 68.4,
        base,
      );
  }

  Path _chevron(double cx, double cy, {required bool pointsRight}) {
    final s = pointsRight ? 1.0 : -1.0;
    return Path()
      ..moveTo(cx - s * 45, cy - 45)
      ..lineTo(cx + s * 35, cy)
      ..lineTo(cx - s * 45, cy + 45);
  }

  void _pupil(Canvas canvas, Offset center, double r, double blink) {
    canvas.drawOval(
      Rect.fromCenter(center: center, width: 2 * r, height: 2 * r * blink),
      _red,
    );
    if (blink >= 1) {
      canvas.drawCircle(
        center + Offset(-r * 0.32, -r * 0.34),
        r * 0.28,
        _cream,
      );
    }
  }

  void _openMouth(Canvas canvas, double r) {
    const cx = 629.0, cy = 692.0;
    final mouth = Path()
      ..moveTo(cx + r, cy)
      ..arcTo(
        Rect.fromCircle(center: const Offset(cx, cy), radius: r),
        0,
        math.pi,
        false,
      )
      ..close();
    canvas
      ..drawPath(mouth, _red)
      ..drawOval(
        Rect.fromCenter(
          center: Offset(cx, cy + r * 0.62),
          width: r,
          height: r * 0.55,
        ),
        _pink,
      );
  }

  void _paintSparkles(Canvas canvas) {
    const origin = Offset(1040, 185);
    for (final deg in const [-75.0, -40.0, -5.0]) {
      final a = deg * math.pi / 180;
      final dir = Offset(math.cos(a), math.sin(a));
      canvas.drawLine(origin + dir * 50, origin + dir * 125, _sparkle);
    }
  }

  void _paintQuestionMark(Canvas canvas) {
    const cx = 1085.0, cy = 175.0;
    final q = Path();
    for (var deg = -200; deg <= 50; deg += 6) {
      final a = deg * math.pi / 180;
      final x = cx + 52 * math.cos(a);
      final y = cy - 40 + 52 * math.sin(a);
      deg == -200 ? q.moveTo(x, y) : q.lineTo(x, y);
    }
    q
      ..lineTo(cx + 14, cy + 42)
      ..lineTo(cx, cy + 66);
    canvas
      ..drawPath(q, _sparkle)
      ..drawCircle(const Offset(cx, cy + 118), 20, _cream);
  }

  void _paintBook(Canvas canvas) {
    for (final side in const [-1.0, 1.0]) {
      final cover = Path()
        ..moveTo(629, 805)
        ..lineTo(629 + side * 250, 772)
        ..lineTo(629 + side * 250, 935)
        ..lineTo(629, 972)
        ..close();
      final page = Path()
        ..moveTo(629, 792)
        ..lineTo(629 + side * 232, 760)
        ..lineTo(629 + side * 232, 915)
        ..lineTo(629, 952)
        ..close();
      canvas
        ..drawPath(cover, _red)
        ..drawPath(page, _white);
      for (var k = 0; k < 3; k++) {
        final y = 815.0 + k * 38;
        canvas.drawLine(
          Offset(629 + side * 26, y),
          Offset(629 + side * 195, y - 26),
          _peachLine,
        );
      }
    }
  }

  void _paintNotebook(Canvas canvas) {
    canvas
      ..save()
      ..translate(320, 800)
      ..rotate(-12 * math.pi / 180)
      ..translate(-320, -800)
      ..drawRRect(
        RRect.fromRectAndRadius(
          const Rect.fromLTWH(225, 690, 190, 240),
          const Radius.circular(16),
        ),
        _white,
      );
    for (var k = 0; k < 5; k++) {
      canvas.drawCircle(Offset(225, 722.0 + k * 42), 11, _red);
    }
    for (var k = 0; k < 4; k++) {
      final y = 740.0 + k * 44;
      canvas.drawLine(Offset(262, y), Offset(385, y), _peachLine);
    }
    canvas.restore();
  }

  void _paintPencil(Canvas canvas) {
    canvas
      ..save()
      ..translate(980, 720)
      ..rotate(35 * math.pi / 180)
      ..translate(-980, -720)
      ..drawRect(const Rect.fromLTWH(950, 560, 64, 230), _apricot)
      ..drawRect(const Rect.fromLTWH(950, 535, 64, 34), _pink)
      ..drawPath(
        Path()
          ..moveTo(950, 790)
          ..lineTo(1014, 790)
          ..lineTo(982, 858)
          ..close(),
        _cream,
      )
      ..drawPath(
        Path()
          ..moveTo(972, 832)
          ..lineTo(992, 832)
          ..lineTo(982, 858)
          ..close(),
        _red,
      )
      ..restore();
  }

  void _paintChecklist(Canvas canvas) {
    canvas
      ..save()
      ..translate(920, 780)
      ..rotate(8 * math.pi / 180)
      ..translate(-920, -780)
      ..drawRRect(
        RRect.fromRectAndRadius(
          const Rect.fromLTWH(790, 640, 250, 290),
          const Radius.circular(16),
        ),
        _white,
      )
      ..drawRRect(
        RRect.fromRectAndRadius(
          const Rect.fromLTWH(850, 620, 130, 44),
          const Radius.circular(12),
        ),
        _red,
      );
    for (var k = 0; k < 3; k++) {
      final y = 725.0 + k * 64;
      final check = Path()
        ..moveTo(815, y)
        ..lineTo(833, y + 17)
        ..lineTo(862, y - 17);
      canvas
        ..drawPath(check, _redLine)
        ..drawLine(Offset(885, y), Offset(1008, y), _peachLine);
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(_MascotPainter oldDelegate) =>
      oldDelegate.motion != motion ||
      oldDelegate.cycle != cycle ||
      oldDelegate.expression != expression;
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
