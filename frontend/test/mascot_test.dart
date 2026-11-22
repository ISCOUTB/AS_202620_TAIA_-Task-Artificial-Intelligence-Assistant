import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/mascot/mascot_expression.dart';
import 'package:taia/mascot/taia_mascot.dart';

void main() {
  testWidgets('la mascota usa la pose ilustrada de cada expresión', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: SizedBox(
          width: 120,
          child: TaiaMascot(expression: MascotExpression.thinking),
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 100));

    final image = tester.widget<Image>(find.byType(Image));
    expect((image.image as AssetImage).assetName, 'assets/mascot/thinking.png');
  });

  testWidgets('con silhouette dibuja la silueta, sin imagen', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: SizedBox(width: 120, child: TaiaMascot(silhouette: true)),
      ),
    );
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(Image), findsNothing);
  });

  test('cada expresión tiene su archivo y una silueta de respaldo', () {
    for (final expression in MascotExpression.values) {
      expect(expression.asset, 'assets/mascot/${expression.name}.png');
      expect(
        MascotExpression.values.indexOf(expression.silhouette),
        lessThan(9),
      );
    }
  });
}
