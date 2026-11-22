import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../shell/main_shell.dart';
import 'auth_service.dart';
import 'auth_shell.dart';
import 'forgot_password_screen.dart';
import 'register_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, this.service});

  /// Servicio de autenticación; si es null se usa el compartido de la app.
  final AuthService? service;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _obscure = true;
  bool _loading = false;
  String? _error;
  MascotExpression _expression = MascotExpression.happy;

  AuthService get _service => widget.service ?? authService;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

    /// Al editar un campo la mascota vuelve a su expresión de reposo.
  void _onEdited() {
    if (!_loading && _expression != MascotExpression.happy) {
      setState(() => _expression = MascotExpression.happy);
    }
  }

  /// RF-USR-08: al volver con la contraseña cambiada, se pide iniciar sesión.
  Future<void> _forgotPassword() async {
    final reset = await Navigator.of(context).push<bool>(
      MaterialPageRoute<bool>(
        builder: (_) => ForgotPasswordScreen(initialEmail: _email.text.trim()),
      ),
    );
    if (!mounted || reset != true) return;
    _password.clear();
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        const SnackBar(
          content: Text('Contraseña actualizada. Inicia sesión con la nueva.'),
        ),
      );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      setState(() => _expression = MascotExpression.surprised);
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
      _expression = MascotExpression.thinking;
    });
    try {
      await _service.login(_email.text.trim(), _password.text);
      if (!mounted) return;
      setState(() => _expression = MascotExpression.excited);
      await Future<void>.delayed(const Duration(milliseconds: 700));
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute<void>(
          builder: (_) => MainShell(service: widget.service),
        ),
        (route) => false,
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _expression = MascotExpression.surprised;
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AuthShell(
      title: 'Iniciar sesión',
      subtitle: 'Qué bueno verte de nuevo.',
      expression: _expression,
      child: Form(
        key: _formKey,
        onChanged: _onEdited,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextFormField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              autofillHints: const [AutofillHints.email],
              textInputAction: TextInputAction.next,
              decoration: authInputDecoration('Correo', Icons.mail_outline),
              validator: validateEmail,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _password,
              obscureText: _obscure,
              autofillHints: const [AutofillHints.password],
              textInputAction: TextInputAction.done,
              onFieldSubmitted: (_) => _submit(),
              decoration: authInputDecoration('Contraseña', Icons.lock_outline)
                  .copyWith(
                    suffixIcon: IconButton(
                      tooltip: _obscure ? 'Mostrar contraseña' : 'Ocultar',
                      icon: Icon(
                        _obscure ? Icons.visibility : Icons.visibility_off,
                      ),
                      onPressed: () => setState(() => _obscure = !_obscure),
                    ),
                  ),
              validator: (v) =>
                  (v == null || v.isEmpty) ? 'Ingresa tu contraseña.' : null,
            ),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                style: TextButton.styleFrom(foregroundColor: taiaInk),
                onPressed: _loading ? null : _forgotPassword,
                child: const Text('¿Olvidaste tu contraseña?'),
              ),
            ),
            const SizedBox(height: 8),
            if (_error != null) AuthErrorText(_error!),
            AuthSubmitButton(
              label: 'Iniciar sesión',
              loading: _loading,
              onPressed: _submit,
            ),
            const SizedBox(height: 8),
            TextButton(
              style: TextButton.styleFrom(foregroundColor: taiaInk),
              onPressed: _loading
                  ? null
                  : () => Navigator.of(context).pushReplacement(
                      MaterialPageRoute<void>(
                        builder: (_) => RegisterScreen(service: widget.service),
                      ),
                    ),
              child: const Text.rich(
                TextSpan(
                  text: '¿No tienes cuenta? ',
                  children: [
                    TextSpan(
                      text: 'Regístrate',
                      style: TextStyle(
                        color: TaiaColors.fieryRose,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
