/// Expresiones de la mascota, según el tablero de diseño.
///
/// Las tres últimas muestran a TAIA con útiles escolares.
enum MascotExpression {
  /// Ojos sonrientes, sin boca (la del splash).
  normal,

  /// Ojos sonrientes y boca abierta.
  happy,

  /// Mira hacia arriba con un signo de pregunta.
  thinking,

  /// Ojos muy abiertos y boca en "o".
  surprised,

  /// Guiña un ojo.
  wink,

  /// Ojos en ">" y "<", boca abierta y destellos.
  excited,

  /// Con cuaderno y lápiz.
  studying,

  /// Con una lista de verificación.
  organizing,

  /// Con un libro abierto.
  reading,

  /// Con un portátil (la del asistente).
  laptop,

  /// Ojos cerrados, en calma (estados vacíos).
  resting,

  /// Con una pila de libros (plan de estudio).
  books;

  /// Pose ilustrada de `assets/mascot/`.
  String get asset => 'assets/mascot/$name.png';

  /// La silueta vectorial solo dibuja las nueve primeras; las demás usan la
  /// más parecida.
  MascotExpression get silhouette => switch (this) {
    laptop => happy,
    resting => normal,
    books => reading,
    _ => this,
  };
}
