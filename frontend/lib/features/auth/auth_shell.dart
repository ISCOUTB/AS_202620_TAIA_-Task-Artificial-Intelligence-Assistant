import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../splash/splash_background.dart';
import '../../theme/taia_colors.dart';

/// Color de texto sobre las tarjetas claras.
const Color taiaInk = Color(0xFF3B2A2A);

/// Estilo común de los campos de los formularios.
InputDecoration authInputDecoration(String label, IconData icon) {
  return InputDecoration(
    labelText: label,
    prefixIcon: Icon(icon),
    filled: true,
    fillColor: Colors.white,
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: BorderSide.none,
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: const BorderSide(color: TaiaColors.fieryRose, width: 2),
    ),
  );
}

/// Marco compartido por inicio de sesión y registro: fondo de la marca, título
/// y una tarjeta clara con el formulario.
class AuthShell extends StatelessWidget {
  const AuthShell({
    super.key,
    required this.title,
    required this.subtitle,
    required this.child,
    this.expression = MascotExpression.normal,
    this.mascotWidth = 150,
  });

  final String title;
  final String subtitle;
  final Widget child;

  /// Expresión de la mascota que acompaña la pantalla.
  final MascotExpression expression;

  /// Ancho de la mascota en la parte superior.
  final double mascotWidth;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        extendBodyBehindAppBar: true,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          scrolledUnderElevation: 0,
          foregroundColor: TaiaColors.ivoryMist,
        ),
        body: Stack(
          children: [
            const SplashBackground(),
            SafeArea(
              child: Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(
                    24,
                    kToolbarHeight,
                    24,
                    24,
                  ),
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 440),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        SizedBox(
                          width: mascotWidth,
                          child: Hero(
                            tag: 'taia-mascot',
                            child: TaiaMascot(
                              motion: 0.6,
                              expression: expression,
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          title,
                          textAlign: TextAlign.center,
                          style: text.headlineMedium?.copyWith(
                            color: TaiaColors.ivoryMist,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          subtitle,
                          textAlign: TextAlign.center,
                          style: text.bodyLarge?.copyWith(
                            color: TaiaColors.ivoryMist,
                          ),
                        ),
                        const SizedBox(height: 24),
                        Container(
                          padding: const EdgeInsets.all(24),
                          decoration: BoxDecoration(
                            color: TaiaColors.ivoryMist,
                            borderRadius: BorderRadius.circular(24),
                          ),
                          child: child,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Botón principal de los formularios, con indicador de carga.
class AuthSubmitButton extends StatelessWidget {
  const AuthSubmitButton({
    super.key,
    required this.label,
    required this.loading,
    required this.onPressed,
  });

  final String label;
  final bool loading;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: FilledButton(
        style: FilledButton.styleFrom(
          backgroundColor: TaiaColors.fieryRose,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
        onPressed: loading ? null : onPressed,
        child: loading
            ? const SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              )
            : Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
      ),
    );
  }
}

/// Mensaje de error del servidor mostrado sobre el botón.
class AuthErrorText extends StatelessWidget {
  const AuthErrorText(this.message, {super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        message,
        style: TextStyle(
          color: Theme.of(context).colorScheme.error,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

final RegExp _emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

String? validateEmail(String? value) {
  final email = value?.trim() ?? '';
  if (email.isEmpty) return 'Ingresa tu correo.';
  if (!_emailPattern.hasMatch(email)) return 'Ingresa un correo válido.';
  return null;
}