import 'package:flutter/material.dart';

import '../../../theme/taia_colors.dart';
import '../../auth/auth_service.dart';
import '../../auth/auth_shell.dart';
import '../profile_service.dart';

/// Diálogo de cuenta: un formulario, un botón que ejecuta [submit] y el error
/// de la API debajo. Devuelve lo que devuelva [submit], o null si se cancela.
class _AccountDialog<T> extends StatefulWidget {
  const _AccountDialog({
    required this.title,
    required this.action,
    required this.fields,
    required this.submit,
    this.intro,
    this.danger = false,
  });

  final String title;
  final String action;
  final String? intro;
  final bool danger;
  final List<Widget> fields;
  final Future<T> Function() submit;

  @override
  State<_AccountDialog<T>> createState() => _AccountDialogState<T>();
}

class _AccountDialogState<T> extends State<_AccountDialog<T>> {
  final _formKey = GlobalKey<FormState>();
  bool _busy = false;
  String? _error;

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await widget.submit();
      if (mounted) Navigator.of(context).pop(result);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = widget.danger ? Colors.red.shade700 : TaiaColors.fieryRose;
    return AlertDialog(
      backgroundColor: TaiaColors.ivoryMist,
      title: Text(
        widget.title,
        style: const TextStyle(color: taiaInk, fontWeight: FontWeight.w900),
      ),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (widget.intro != null) ...[
                Text(widget.intro!, style: const TextStyle(color: taiaInk)),
                const SizedBox(height: 16),
              ],
              for (final field in widget.fields) ...[
                field,
                const SizedBox(height: 12),
              ],
              if (_error != null) AuthErrorText(_error!),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          style: FilledButton.styleFrom(backgroundColor: color),
          onPressed: _busy ? null : _submit,
          child: _busy
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : Text(widget.action),
        ),
      ],
    );
  }
}

TextFormField _passwordField(
  TextEditingController controller,
  String label, {
  String? Function(String?)? validator,
}) => TextFormField(
  controller: controller,
  obscureText: true,
  decoration: authInputDecoration(label, Icons.lock_outline),
  validator:
      validator ??
      (v) => (v == null || v.isEmpty) ? 'Ingresa tu contraseña actual.' : null,
);

/// Nombre y correo (RF-USR-06). Cambiar el correo pide la contraseña actual.
Future<UserProfile?> showEditProfileDialog(
  BuildContext context, {
  required ProfileService service,
  required UserProfile user,
}) {
  final name = TextEditingController(text: user.fullName);
  final email = TextEditingController(text: user.email);
  final password = TextEditingController();
  bool emailChanged() =>
      email.text.trim().toLowerCase() != user.email.toLowerCase();
  return showDialog<UserProfile>(
    context: context,
    builder: (context) => _AccountDialog<UserProfile>(
      title: 'Editar perfil',
      action: 'Guardar',
      fields: [
        TextFormField(
          controller: name,
          textCapitalization: TextCapitalization.words,
          decoration: authInputDecoration(
            'Nombre completo',
            Icons.person_outline,
          ),
          validator: (v) {
            final value = v?.trim() ?? '';
            if (value.isEmpty) return 'Ingresa tu nombre.';
            if (value.length > 100) return 'Máximo 100 caracteres.';
            return null;
          },
        ),
        TextFormField(
          controller: email,
          keyboardType: TextInputType.emailAddress,
          decoration: authInputDecoration('Correo', Icons.mail_outline),
          validator: validateEmail,
        ),
        _passwordField(
          password,
          'Contraseña actual (solo si cambias el correo)',
          validator: (v) => emailChanged() && (v == null || v.isEmpty)
              ? 'Para cambiar el correo, ingresa tu contraseña actual.'
              : null,
        ),
      ],
      submit: () {
        final newName = name.text.trim();
        final changeEmail = emailChanged();
        return service.updateProfile(
          fullName: newName != user.fullName ? newName : null,
          email: changeEmail ? email.text.trim() : null,
          currentPassword: changeEmail ? password.text : null,
        );
      },
    ),
  );
}

/// Cambio de contraseña (RF-USR-07). Devuelve true si se cambió.
Future<bool?> showChangePasswordDialog(
  BuildContext context, {
  required ProfileService service,
}) {
  final current = TextEditingController();
  final next = TextEditingController();
  final confirm = TextEditingController();
  return showDialog<bool>(
    context: context,
    builder: (context) => _AccountDialog<bool>(
      title: 'Cambiar contraseña',
      action: 'Cambiar',
      intro: 'Se cerrarán las sesiones abiertas en tus otros dispositivos.',
      fields: [
        _passwordField(current, 'Contraseña actual'),
        _passwordField(
          next,
          'Contraseña nueva',
          validator: (v) {
            if (v == null || v.isEmpty) return 'Ingresa la contraseña nueva.';
            if (v.length < 8) return 'Debe tener al menos 8 caracteres.';
            if (v == current.text) return 'Debe ser distinta de la actual.';
            return null;
          },
        ),
        _passwordField(
          confirm,
          'Confirmar contraseña nueva',
          validator: (v) =>
              v != next.text ? 'Las contraseñas no coinciden.' : null,
        ),
      ],
      submit: () async {
        await service.changePassword(
          currentPassword: current.text,
          newPassword: next.text,
        );
        return true;
      },
    ),
  );
}

/// Desactivar la cuenta (RF-USR-09). Devuelve true si se desactivó.
Future<bool?> showDeactivateDialog(
  BuildContext context, {
  required ProfileService service,
}) {
  final password = TextEditingController();
  return showDialog<bool>(
    context: context,
    builder: (context) => _AccountDialog<bool>(
      title: '¿Desactivar tu cuenta?',
      action: 'Desactivar',
      danger: true,
      intro:
          'Se cerrarán todas tus sesiones, se desvinculará Telegram y se '
          'cancelarán tus recordatorios pendientes. Si inicias sesión en los '
          'próximos 30 días, tu cuenta se reactiva; después ya no.',
      fields: [_passwordField(password, 'Contraseña actual')],
      submit: () async {
        await service.deactivate(password.text);
        return true;
      },
    ),
  );
}

/// Desvincular Telegram (RF-TEL-03). Devuelve true si se desvinculó.
Future<bool?> showUnlinkTelegramDialog(
  BuildContext context, {
  required ProfileService service,
}) {
  return showDialog<bool>(
    context: context,
    builder: (context) => _AccountDialog<bool>(
      title: '¿Desvincular Telegram?',
      action: 'Desvincular',
      danger: true,
      intro:
          'El bot de TAIA dejará de reconocerte. Puedes volver a vincularlo '
          'cuando quieras.',
      fields: const [],
      submit: () async {
        await service.unlinkTelegram();
        return true;
      },
    ),
  );
}
