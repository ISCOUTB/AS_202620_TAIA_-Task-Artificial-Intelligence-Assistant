import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../shell/main_shell.dart';
import 'auth_service.dart';
import 'auth_shell.dart';
import 'login_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key, this.service});

  /// Servicio de autenticación; si es null se usa el compartido de la app.
  final AuthService? service;

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  bool _obscure = true;
  bool _loading = false;
  String? _error;
  MascotExpression _expression = MascotExpression.happy;

  AuthService get _service => widget.service ?? authService;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

    /// Al editar un campo la mascota vuelve a su expresión de reposo.
  void _onEdited() {
    if (!_loading && _expression != MascotExpression.organizing) {
      setState(() => _expression = MascotExpression.organizing);
    }
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
      final email = _email.text.trim();
      await _service.register(
        fullName: _name.text.trim(),
        email: email,
        password: _password.text,
      );
      // La cuenta ya existe: se inicia sesión de una vez.
      await _service.login(email, _password.text);
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
      title: 'Crear cuenta',
      subtitle: 'Organiza tus tareas, exámenes y horarios.',
      expression: _expression,
      child: Form(
        key: _formKey,
        onChanged: _onEdited,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextFormField(
              controller: _name,
              textCapitalization: TextCapitalization.words,
              autofillHints: const [AutofillHints.name],
              textInputAction: TextInputAction.next,
              decoration: authInputDecoration(
                'Nombre completo',
                Icons.person_outline,
              ),
              validator: (v) {
                final name = v?.trim() ?? '';
                if (name.isEmpty) return 'Ingresa tu nombre.';
                if (name.length > 100) return 'Máximo 100 caracteres.';
                return null;
              },
            ),
            const SizedBox(height: 16),
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
              autofillHints: const [AutofillHints.newPassword],
              textInputAction: TextInputAction.next,
              decoration: authInputDecoration('Contraseña', Icons.lock_outline)
                  .copyWith(
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
              textInputAction: TextInputAction.done,
              decoration: authInputDecoration(
                'Confirmar contraseña',
                Icons.lock_outline,
              ),
              validator: (v) =>
                  v != _password.text ? 'Las contraseñas no coinciden.' : null,
            ),
            const SizedBox(height: 8),
            FormField<bool>(
              initialValue: false,
              validator: (accepted) => (accepted ?? false)
                  ? null
                  : 'Debes aceptar la política para crear tu cuenta.',
              builder: (field) => Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    controlAffinity: ListTileControlAffinity.leading,
                    activeColor: TaiaColors.fieryRose,
                    value: field.value ?? false,
                    onChanged: _loading ? null : field.didChange,
                    title: const Text(
                      'Acepto la política de tratamiento de datos personales '
                      '(versión $consentPolicyVersion).',
                      style: TextStyle(color: taiaInk, fontSize: 13),
                    ),
                  ),
                  if (field.hasError)
                    Text(
                      field.errorText!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                        fontSize: 12,
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            if (_error != null) AuthErrorText(_error!),
            AuthSubmitButton(
              label: 'Crear cuenta',
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
                        builder: (_) => LoginScreen(service: widget.service),
                      ),
                    ),
              child: const Text.rich(
                TextSpan(
                  text: '¿Ya tienes cuenta? ',
                  children: [
                    TextSpan(
                      text: 'Inicia sesión',
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
