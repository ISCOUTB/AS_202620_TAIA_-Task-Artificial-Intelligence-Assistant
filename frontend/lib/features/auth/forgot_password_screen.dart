import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../mascot/mascot_expression.dart';
import 'auth_service.dart';
import 'auth_shell.dart';
import 'password_reset_service.dart';

/// "Olvidé mi contraseña" (RF-USR-08): primero se pide el código al correo y
/// luego se escribe el código con la contraseña nueva. Devuelve true si la
/// contraseña se restableció.
class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key, this.service, this.initialEmail});

  final PasswordResetService? service;
  final String? initialEmail;

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  late final _email = TextEditingController(text: widget.initialEmail ?? '');
  final _code = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();

  /// Ya se pidió el código: se muestra el segundo paso.
  bool _codeSent = false;
  bool _loading = false;
  bool _obscure = true;
  String? _error;
  MascotExpression _expression = MascotExpression.thinking;

  PasswordResetService get _service => widget.service ?? passwordResetService;

  @override
  void dispose() {
    _email.dispose();
    _code.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _run(
    Future<void> Function() action, {
    bool validate = true,
  }) async {
    if (validate && !_formKey.currentState!.validate()) {
      setState(() => _expression = MascotExpression.surprised);
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await action();
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

  Future<void> _requestCode() => _run(() async {
    await _service.request(_email.text.trim());
    if (!mounted) return;
    setState(() {
      _codeSent = true;
      _expression = MascotExpression.wink;
    });
  });

  /// Pide otro código para el mismo correo; invalida los anteriores.
  Future<void> _resendCode() => _run(() async {
    await _service.request(_email.text.trim());
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(const SnackBar(content: Text('Te enviamos otro código.')));
  }, validate: false);

  Future<void> _reset() => _run(() async {
    await _service.confirm(
      email: _email.text.trim(),
      code: _code.text.trim(),
      newPassword: _password.text,
    );
    if (!mounted) return;
    Navigator.of(context).pop(true);
  });

  @override
  Widget build(BuildContext context) {
    return AuthShell(
      title: 'Recuperar contraseña',
      subtitle: _codeSent
          ? 'Si el correo tiene una cuenta, te enviamos un código de 6 '
                'dígitos. Vence en 15 minutos.'
          : 'Te enviaremos un código a tu correo.',
      expression: _expression,
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextFormField(
              controller: _email,
              enabled: !_codeSent,
              keyboardType: TextInputType.emailAddress,
              autofillHints: const [AutofillHints.email],
              decoration: authInputDecoration('Correo', Icons.mail_outline),
              validator: validateEmail,
            ),
            if (_codeSent) ...[
              const SizedBox(height: 16),
              TextFormField(
                controller: _code,
                keyboardType: TextInputType.number,
                maxLength: 6,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                autofillHints: const [AutofillHints.oneTimeCode],
                decoration: authInputDecoration(
                  'Código de 6 dígitos',
                  Icons.pin_outlined,
                ).copyWith(counterText: ''),
                validator: (v) => RegExp(r'^\d{6}$').hasMatch(v ?? '')
                    ? null
                    : 'El código tiene 6 dígitos.',
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _password,
                obscureText: _obscure,
                autofillHints: const [AutofillHints.newPassword],
                decoration:
                    authInputDecoration(
                      'Contraseña nueva',
                      Icons.lock_outline,
                    ).copyWith(
                      helperText: 'Mínimo 8 caracteres.',
                      suffixIcon: IconButton(
                        tooltip: _obscure ? 'Mostrar contraseña' : 'Ocultar',
                        icon: Icon(
                          _obscure ? Icons.visibility : Icons.visibility_off,
                        ),
                        onPressed: () => setState(() => _obscure = !_obscure),
                      ),
                    ),
                validator: (v) {
                  if (v == null || v.isEmpty) return 'Ingresa una contraseña.';
                  if (v.length < 8) return 'Debe tener al menos 8 caracteres.';
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _confirm,
                obscureText: _obscure,
                decoration: authInputDecoration(
                  'Confirmar contraseña',
                  Icons.lock_outline,
                ),
                validator: (v) => v != _password.text
                    ? 'Las contraseñas no coinciden.'
                    : null,
              ),
            ],
            const SizedBox(height: 20),
            if (_error != null) AuthErrorText(_error!),
            AuthSubmitButton(
              label: _codeSent ? 'Cambiar contraseña' : 'Enviar código',
              loading: _loading,
              onPressed: _codeSent ? _reset : _requestCode,
            ),
            if (_codeSent) ...[
              const SizedBox(height: 8),
              TextButton(
                style: TextButton.styleFrom(foregroundColor: taiaInk),
                onPressed: _loading ? null : _resendCode,
                child: const Text('Enviar otro código'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
