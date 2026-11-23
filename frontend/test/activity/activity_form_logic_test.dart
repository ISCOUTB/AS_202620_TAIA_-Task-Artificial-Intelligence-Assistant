import 'package:flutter_test/flutter_test.dart';
import 'package:taia/features/activity/activity_logic.dart';
import 'package:taia/features/reminders/reminder_option.dart';
import 'package:taia/features/tasks/task.dart';

/// RNF-14: el formulario de actividad se llena con pocos toques.
void main() {
  // Miércoles 7 de octubre de 2026, 10:00 en Colombia.
  final now = DateTime(2026, 10, 7, 10);

  test('los atajos de día incluyen el próximo viernes', () {
    final labels = [for (final d in quickDates(now)) d.label];
    expect(labels, ['Hoy', 'Mañana', 'El viernes', 'En 1 semana']);
    expect(quickDates(now)[2].date, DateTime(2026, 10, 9));
  });

  test('un jueves, "el viernes" sería mañana: salta al de la otra semana', () {
    final thursday = DateTime(2026, 10, 8, 10);
    final friday = quickDates(thursday).where((d) => d.label == 'El viernes');
    expect(friday.single.date, DateTime(2026, 10, 16));
  });

  test('la sugerencia de título usa la materia elegida', () {
    expect(suggestedTitle('Parcial', 'Cálculo'), 'Parcial de Cálculo');
    expect(suggestedTitle('Parcial', null), 'Parcial');
    expect(titleSuggestions(TaskType.exam), contains('Quiz'));
  });

  test('la frase de vencimiento dice el día, la hora y cuánto falta', () {
    expect(
      dueSentence(DateTime(2026, 10, 9, 23, 59), now),
      'Vence el viernes 9 de octubre a las 11:59 p. m. · en 3 días',
    );
  });

  test('el resumen en vivo cuenta lo que se va a crear', () {
    String summary({String title = 'Parcial de Cálculo', String? subject}) =>
        activitySummary(
          type: TaskType.exam,
          title: title,
          subjectName: subject,
          due: DateTime(2026, 10, 9, 8),
          reminders: ReminderMode.defaults,
          customReminders: 0,
        );

    expect(summary(title: ''), 'Ponle un título y yo armo el resto.');
    expect(summary(), 'Elige la materia de "Parcial de Cálculo".');
    expect(
      summary(subject: 'Cálculo'),
      'Voy a crear el examen "Parcial de Cálculo" para el viernes '
      '9 de octubre a las 8:00 a. m., con recordatorios la tarde anterior y '
      'cada 2 días.',
    );
    expect(
      summary(title: 'Quiz 2', subject: 'Física'),
      startsWith('Voy a crear el examen "Quiz 2" de Física para'),
    );
  });
}
