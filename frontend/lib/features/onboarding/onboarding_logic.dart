import '../academic/schedule_block.dart';

/// Tipo de estudiante (RF-ASG-08). Solo sirve para sugerir las fechas del
/// período; no se guarda.
enum StudentType {
  school('Colegio'),
  university('Universidad'),
  course('Curso o técnico'),
  other('Otro');

  const StudentType(this.label);

  final String label;
}

/// Fechas sugeridas del período académico según el tipo de estudiante
/// (RF-ASG-08). El estudiante siempre puede cambiarlas.
AcademicPeriod suggestedPeriod(StudentType type, DateTime today) {
  final day = DateTime(today.year, today.month, today.day);
  switch (type) {
    case StudentType.school:
      // De febrero a noviembre; pasado noviembre, el del año siguiente.
      final year = day.isAfter(DateTime(day.year, 11, 30))
          ? day.year + 1
          : day.year;
      return AcademicPeriod(
        start: DateTime(year, 2, 1),
        end: DateTime(year, 11, 30),
      );
    case StudentType.university:
      // Primer semestre de febrero a junio; segundo, de agosto a noviembre.
      if (day.month <= 6) {
        return AcademicPeriod(
          start: DateTime(day.year, 2, 1),
          end: DateTime(day.year, 6, 30),
        );
      }
      if (day.isAfter(DateTime(day.year, 11, 30))) {
        return AcademicPeriod(
          start: DateTime(day.year + 1, 2, 1),
          end: DateTime(day.year + 1, 6, 30),
        );
      }
      return AcademicPeriod(
        start: DateTime(day.year, 8, 1),
        end: DateTime(day.year, 11, 30),
      );
    case StudentType.course:
    case StudentType.other:
      // Sin ciclo fijo: desde hoy y tres meses después, para ajustar.
      return AcademicPeriod(
        start: day,
        end: DateTime(day.year, day.month + 3, day.day),
      );
  }
}
