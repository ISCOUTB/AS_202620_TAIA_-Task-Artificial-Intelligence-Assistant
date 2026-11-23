import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../../welcome/welcome_screen.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../shell/mascot_message.dart';
import '../shell/page_header.dart';
import '../tutorial/tutorial.dart';
import 'profile_service.dart';
import 'widgets/account_dialogs.dart';
import 'widgets/profile_tile.dart';
import 'widgets/telegram_sheet.dart';

/// Configuración (RF-USR-11): cuenta (RF-USR-06, 07 y 10), Telegram (RF-TEL-01
/// y 03) y sesión (RF-USR-04 y 09). Se abre desde el perfil.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key, this.service, this.profileService});

  final AuthService? service;
  final ProfileService? profileService;

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  UserProfile? _user;
  String? _error;
  bool _loading = true;

  AuthService get _auth => widget.service ?? authService;
  ProfileService get _profile => widget.profileService ?? profileService;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool silent = false}) async {
    if (!silent) setState(() => _loading = true);
    try {
      final user = await _auth.me();
      if (!mounted) return;
      setState(() {
        _user = user;
        _error = null;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        if (_user == null) _error = e.message;
        _loading = false;
      });
    }
  }

  void _toast(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  /// Consulta si la cuenta ya quedó vinculada (la usa la hoja de Telegram).
  Future<bool> _checkLinked() async {
    try {
      final user = await _auth.me();
      if (mounted) setState(() => _user = user);
      return user.telegramLinked;
    } on ApiException {
      return false;
    }
  }

  Future<void> _openTelegram() async {
    final user = _user;
    if (user != null && user.telegramLinked) {
      final unlinked = await showUnlinkTelegramDialog(
        context,
        service: _profile,
      );
      if (!mounted || unlinked != true) return;
      await _load(silent: true);
      _toast('Telegram desvinculado');
      return;
    }
    final linked = await showTelegramSheet(
      context,
      service: _profile,
      onCheckLinked: _checkLinked,
    );
    if (!mounted || linked != true) return;
    _toast('¡Telegram vinculado!');
  }

  Future<void> _editProfile(UserProfile user) async {
    final updated = await showEditProfileDialog(
      context,
      service: _profile,
      user: user,
    );
    if (!mounted || updated == null) return;
    setState(() => _user = updated);
    _toast('Perfil actualizado');
  }

  Future<void> _changePassword() async {
    final changed = await showChangePasswordDialog(context, service: _profile);
    if (!mounted || changed != true) return;
    _toast('Contraseña actualizada');
  }

  void _goToWelcome() {
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute<void>(builder: (_) => const WelcomeScreen()),
      (route) => false,
    );
  }

  /// RF-USR-09: el servidor revoca todas las sesiones; aquí se borran los
  /// tokens locales y se vuelve a la bienvenida.
  Future<void> _deactivate() async {
    final done = await showDeactivateDialog(context, service: _profile);
    if (!mounted || done != true) return;
    await _auth.logout();
    if (mounted) _goToWelcome();
  }

  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: TaiaColors.ivoryMist,
        title: const Text(
          '¿Cerrar sesión?',
          style: TextStyle(color: taiaInk, fontWeight: FontWeight.w900),
        ),
        content: const Text(
          'Tendrás que iniciar sesión de nuevo para ver tus tareas.',
          style: TextStyle(color: taiaInk),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: TaiaColors.fieryRose,
            ),
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Cerrar sesión'),
          ),
        ],
      ),
    );
    if (!mounted || confirmed != true) return;
    await _auth.logout();
    if (mounted) _goToWelcome();
  }

  @override
  Widget build(BuildContext context) {
    final user = _user;
    return Scaffold(
      backgroundColor: TaiaColors.ivoryMist,
      body: SafeArea(
        child: user != null
            ? _content(user)
            : _loading
            ? const MascotMessage(
                expression: MascotExpression.thinking,
                text: 'Cargando tu configuración…',
                showSpinner: true,
              )
            : MascotMessage(
                expression: MascotExpression.surprised,
                text: _error ?? 'No se pudo cargar tu configuración.',
                onRetry: _load,
              ),
      ),
    );
  }

  Widget _content(UserProfile user) {
    final policy = user.consentPolicyVersion;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      children: [
        Row(
          children: [
            IconButton(
              tooltip: 'Volver',
              onPressed: () => Navigator.of(context).maybePop(),
              icon: const Icon(Icons.arrow_back_rounded, color: taiaInk),
            ),
          ],
        ),
        const PageHeader(
          label: 'TU CUENTA',
          title: 'Configuración',
          subtitle: 'Cuenta, integraciones y sesión.',
          expression: MascotExpression.organizing,
        ),
        const SizedBox(height: 20),
        ProfileSection(
          title: 'CUENTA',
          tiles: [
            ProfileTile(
              icon: Icons.person_outline,
              title: 'Editar perfil',
              subtitle: 'Nombre y correo',
              onTap: () => _editProfile(user),
            ),
            ProfileTile(
              icon: Icons.lock_outline,
              title: 'Cambiar contraseña',
              onTap: _changePassword,
            ),
            ProfileTile(
              icon: Icons.verified_user_outlined,
              title: 'Política de datos',
              subtitle: policy == null
                  ? 'Aceptada al registrarte'
                  : 'Aceptada al registrarte · versión $policy',
              trailing: const SizedBox.shrink(),
              onTap: null,
            ),
          ],
        ),
        const SizedBox(height: 20),
        ProfileSection(
          title: 'AYUDA',
          tiles: [
            ProfileTile(
              icon: Icons.tour_outlined,
              title: 'Ver el tutorial',
              subtitle: 'TAIA te muestra la app otra vez',
              // RF-USR-12: vuelve al Inicio y repite el recorrido.
              onTap: () {
                Navigator.of(context).popUntil((route) => route.isFirst);
                AppTutorial.replayRequests.value++;
              },
            ),
          ],
        ),
        const SizedBox(height: 20),
        ProfileSection(
          title: 'INTEGRACIONES',
          tiles: [
            ProfileTile(
              icon: Icons.send_outlined,
              title: 'Telegram',
              subtitle: user.telegramLinked
                  ? 'Cuenta vinculada · toca para desvincular'
                  : 'Habla con TAIA desde el chat',
              trailing: user.telegramLinked
                  ? const Icon(Icons.check_circle, color: TaiaColors.fieryRose)
                  : FilledButton(
                      style: FilledButton.styleFrom(
                        backgroundColor: TaiaColors.fieryRose,
                        visualDensity: VisualDensity.compact,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      onPressed: _openTelegram,
                      child: const Text(
                        'Vincular',
                        style: TextStyle(fontWeight: FontWeight.w800),
                      ),
                    ),
              onTap: _openTelegram,
            ),
          ],
        ),
        const SizedBox(height: 20),
        ProfileSection(
          title: 'SESIÓN',
          tiles: [
            ProfileTile(
              icon: Icons.logout,
              title: 'Cerrar sesión',
              onTap: _logout,
            ),
            ProfileTile(
              icon: Icons.no_accounts_outlined,
              title: 'Desactivar cuenta',
              subtitle: 'Puedes reactivarla iniciando sesión en 30 días',
              danger: true,
              onTap: _deactivate,
            ),
          ],
        ),
      ],
    );
  }
}
