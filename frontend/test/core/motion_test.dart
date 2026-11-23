import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shimmer/shimmer.dart';
import 'package:taia/core/motion.dart';
import 'package:taia/core/skeleton.dart';

/// RNF-14: animaciones cortas que respetan "reducir el movimiento".
void main() {
  Future<void> pump(WidgetTester tester, {required bool reduce}) async {
    await tester.pumpWidget(
      MediaQuery(
        data: MediaQueryData(disableAnimations: reduce),
        child: MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (context) => Column(
                children: [
                  const Text('hola').appear(context),
                  const Expanded(child: SkeletonList(heights: [40])),
                ],
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 400));
  }

  testWidgets('con movimiento, la entrada se anima y la carga brilla', (
    tester,
  ) async {
    await pump(tester, reduce: false);

    expect(find.byType(Animate), findsOneWidget);
    expect(find.byType(Shimmer), findsOneWidget);
  });

  testWidgets('al reducir el movimiento, no hay animación ni brillo', (
    tester,
  ) async {
    await pump(tester, reduce: true);

    expect(find.byType(Animate), findsNothing);
    expect(find.byType(Shimmer), findsNothing);
    expect(find.text('hola'), findsOneWidget);
  });

  test('las entradas duran 300 ms o menos', () {
    expect(motionDuration.inMilliseconds, lessThanOrEqualTo(300));
  });
}
