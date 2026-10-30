import 'package:flutter/painting.dart';

/// Paleta de colores del equipo, con los papeles del tablero de diseño
/// (Trabajo/vocetos/Paleta_colores.txt).
abstract final class TaiaColors {
  /// Principal (Acento 2): fondo del splash.
  static const fieryRose = Color(0xFFF26A6C);

  /// Fondo: cuerpo de la mascota, logotipo y textos sobre el principal.
  static const ivoryMist = Color(0xFFF8EBE2);

  /// Acento 1.
  static const softPeach = Color(0xFFF3C4BE);

  /// Secundario.
  static const sunsetCoral = Color(0xFFEC8366);

  /// Acento 3.
  static const apricotWhisper = Color(0xFFFEC6A3);

  /// Gafas, ojos y lazo de la mascota, tomados de su dibujo original. Son un
  /// poco más oscuros que el principal para que el lazo se distinga del fondo.
  static const mascotRed = Color(0xFFF65D59);

  /// Lóbulo claro del lazo, tomado del dibujo original de la mascota.
  static const mascotPink = Color(0xFFFCA094);
}
