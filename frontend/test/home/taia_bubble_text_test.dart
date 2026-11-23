import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/home/home_data.dart';

/// RF-AGT-23: la burbuja de TAIA en el Inicio cambia según el día.
void main() {
  HomeData data({int overdue = 0, int today = 0, int done = 0}) => HomeData(
    firstName: 'Ana',
    todayTotal: today,
    todayDone: done,
    upcoming: const [],
    weekCounts: const [0, 0, 0, 0, 0, 0, 0],
    weekTotal: 0,
    overdueCount: overdue,
  );

  test('con vencidas, la burbuja las menciona primero', () {
    expect(
      data(overdue: 2, today: 3).taiaBubble,
      'Tienes 2 actividades vencidas. ¿Las organizamos juntas?',
    );
    expect(data(overdue: 1).taiaBubble, contains('1 actividad vencida'));
  });

  test('sin vencidas, habla de lo pendiente de hoy', () {
    expect(
      data(today: 3, done: 1).taiaBubble,
      'Hoy te quedan 2 pendientes. ¿Te ayudo a empezar?',
    );
  });

  test('al día, invita a planear la semana', () {
    expect(data(today: 2, done: 2).taiaBubble, startsWith('¡Vas al día!'));
  });
}
