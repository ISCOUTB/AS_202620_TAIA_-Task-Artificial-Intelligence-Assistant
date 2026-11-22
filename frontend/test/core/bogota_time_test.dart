import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/bogota_time.dart';

void main() {
  tearDown(() => clock = DateTime.now);

  group('RT-03 · hora de Colombia', () {
    test('un instante en UTC se muestra en hora de Colombia', () {
      // 02:00 UTC del 6 de octubre son las 21:00 del 5 de octubre en Bogotá.
      final bogota = parseApiDateTime('2026-10-06T02:00:00Z');

      expect(bogota, DateTime(2026, 10, 5, 21));
    });

    test('un desplazamiento distinto se convierte igual', () {
      final bogota = parseApiDateTime('2026-10-05T23:59:00-05:00');

      expect(bogota, DateTime(2026, 10, 5, 23, 59));
    });

    test('se envía con el desplazamiento de Colombia', () {
      expect(
        formatApiDateTime(DateTime(2026, 10, 5, 23, 59)),
        '2026-10-05T23:59:00-05:00',
      );
    });

    test('el "ahora" no depende de la zona del teléfono', () {
      clock = () => DateTime.utc(2026, 10, 6, 2, 30);

      expect(bogotaNow(), DateTime(2026, 10, 5, 21, 30));
    });

    test('un campo nulo queda nulo', () {
      expect(parseApiDateTimeOrNull(null), isNull);
    });
  });
}
