/// Fecha límite por defecto: mañana a las 11:59 p. m.
DateTime defaultDueDate(DateTime now) =>
    DateTime(now.year, now.month, now.day + 1, 23, 59);

/// Cambia el día de [due] sin tocar la hora.
DateTime withDate(DateTime due, DateTime date) =>
    DateTime(date.year, date.month, date.day, due.hour, due.minute);

/// El backend solo acepta fechas límite posteriores al momento actual.
bool isFutureDue(DateTime due, DateTime now) => due.isAfter(now);

/// Atajos de fecha: hoy, mañana y dentro de una semana.
List<({String label, DateTime date})> quickDates(DateTime now) => [
  (label: 'Hoy', date: DateTime(now.year, now.month, now.day)),
  (label: 'Mañana', date: DateTime(now.year, now.month, now.day + 1)),
  (label: 'En 1 semana', date: DateTime(now.year, now.month, now.day + 7)),
];

bool sameDay(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;