import 'dart:async';

import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../theme/taia_colors.dart';
import '../../welcome/welcome_screen.dart';
import '../academic/schedule_screen.dart';
import '../academic/subjects_screen.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../notifications/notifications_bell.dart';
import '../shell/mascot_message.dart';
import 'profile_service.dart';
import 'widgets/account_dialogs.dart';
import 'widgets/profile_card.dart';
import 'widgets/profile_tile.dart';
import 'widgets/telegram_sheet.dart';

/// Pestaña de perfil: datos de la cuenta (RF-USR-06, 07 y 09), asignaturas y
/// horario, integración con Telegram (RF-TEL-01 y 03) y cierre de sesión.
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key, this.service, this.profileService});

  /// Servicio de autenticación; si es null se usa el compartido de la app.
  final AuthService? service;
  final ProfileService? profileService;

  @override
  State<ProfileScreen> createState() => ProfileScreenState();
}

class ProfileScreenState extends State<ProfileScreen>
    with WidgetsBindingObserver {
  UserProfile? _user;
  String? _error;
  bool _loading = true;
  MascotExpression _expression = MascotExpression.wink;
  Timer? _celebrationTimer;

  AuthService get _auth => widget.service ?? authService;
  ProfileService get _profile => widget.profileService ?? profileService;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _load();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _celebrationTimer?.cancel();
    super.dispose();
  }

  /// Al volver de Telegram se actualiza el estado de la vinculación.
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) refresh();
  }

  /// Vuelve a pedir los datos sin ocultar lo que ya se muestra.
  Future<void> refresh() => _load(silent: _user != null);

  Future<void> _load({bool silent = false}) async {
    if (!silent) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
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

  void _celebrate() {
    _celebrationTimer?.cancel();
    setState(() => _expression = MascotExpression.excited);
    _celebrationTimer = Timer(const Duration(milliseconds: 2400), () {
      if (mounted) setState(() => _expression = MascotExpression.wink);
    });
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
    _celebrate();
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

  /// RF-USR-09: el servidor revoca todas las sesiones; aquí se borran los
  /// tokens locales y se vuelve a la bienvenida.
  Future<void> _deactivate() async {
    setState(() => _expression = MascotExpression.surprised);
    final done = await showDeactivateDialog(context, service: _profile);
    if (!mounted) return;
    if (done != true) {
      setState(() => _expression = MascotExpression.wink);
      return;
    }
    await _auth.logout();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute<void>(builder: (_) => const WelcomeScreen()),
      (route) => false,
    );
  }

  Future<void> _push(Widget screen) =>
      Navigator.of(context)
          .push(MaterialPageRoute<void>(builder: (_) => screen));

  Future<void> _logout() async {
    setState(() => _expression = MascotExpression.surprised);
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
    if (!mounted) return;
    if (confirmed != true) {
      setState(() => _expression = MascotExpression.wink);
      return;
    }
    await _auth.logout();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute<void>(builder: (_) => const WelcomeScreen()),
      (route) => false,
    );
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
                text: 'Cargando tu perfil…',
                showSpinner: true,
              )
            : MascotMessage(
                expression: MascotExpression.surprised,
                text: _error ?? 'No se pudo cargar tu perfil.',
                onRetry: _load,
              ),
      ),
    );
  }

  Widget _content(UserProfile user) {
    final policy = user.consentPolicyVersion;
    return RefreshIndicator(
      color: TaiaColors.fieryRose,
      onRefresh: () => _load(silent: true),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          _Header(expression: _expression),
          const SizedBox(height: 20),
          ProfileCard(user: user),
          const SizedBox(height: 24),
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
            title: 'ACADÉMICO',
            tiles: [
              ProfileTile(
                icon: Icons.menu_book_outlined,
                title: 'Asignaturas',
                subtitle: 'Materias, alias y archivo',
                onTap: () => _push(const SubjectsScreen()),
              ),
              ProfileTile(
                icon: Icons.schedule,
                title: 'Horario',
                subtitle: 'Clases de la semana y período académico',
                onTap: () => _push(const ScheduleScreen()),
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
                    ? const Icon(
                        Icons.check_circle,
                        color: TaiaColors.fieryRose,
                      )
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
          const SizedBox(height: 24),
          Center(
            child: Text(
              'TAIA · Tu asistente académico',
              style: TextStyle(
                color: taiaInk.withValues(alpha: 0.4),
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.expression});

  final MascotExpression expression;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'TU CUENTA',
                style: TextStyle(
                  color: TaiaColors.fieryRose,
                  fontSize: 12,
                  letterSpacing: 1.6,
                  fontWeight: FontWeight.w800,
                ),
              ),
              SizedBox(height: 4),
              Text(
                'Mi perfil',
                style: TextStyle(
                  color: taiaInk,
                  fontSize: 32,
                  fontWeight: FontWeight.w900,
                ),
              ),
              SizedBox(height: 4),
              Text(
                'Tus datos, tus materias y tu sesión.',
                style: TextStyle(color: Color(0xA63B2A2A), fontSize: 14),
              ),
            ],
          ),
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            const NotificationsBell(),
            Container(
              width: 84,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: TaiaColors.fieryRose,
                borderRadius: BorderRadius.circular(24),
              ),
              child: TaiaMascot(motion: 0.6, expression: expression),
            ),
          ],
        ),
      ],
    );
  }
}
