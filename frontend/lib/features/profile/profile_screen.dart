import 'dart:async';

import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../theme/taia_colors.dart';
import '../../welcome/welcome_screen.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../home/widgets/reminders_bell.dart';
import '../shell/mascot_message.dart';
import 'notification_prefs.dart';
import 'profile_logic.dart';
import 'profile_service.dart';
import 'widgets/notification_sheet.dart';
import 'widgets/profile_card.dart';
import 'widgets/profile_tile.dart';
import 'widgets/telegram_sheet.dart';

/// Pestaña de perfil: datos de la cuenta, integración con Telegram, preferencia
/// de notificaciones y cierre de sesión.
///
/// Editar el perfil y eliminar la cuenta aparecen como "Próximamente": el
/// backend todavía no tiene esos endpoints.
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({
    super.key,
    this.service,
    this.profileService,
    this.prefs,
  });

  /// Servicio de autenticación; si es null se usa el compartido de la app.
  final AuthService? service;
  final ProfileService? profileService;
  final NotificationPrefs? prefs;

  @override
  State<ProfileScreen> createState() => ProfileScreenState();
}

class ProfileScreenState extends State<ProfileScreen>
    with WidgetsBindingObserver {
  UserProfile? _user;
  String? _error;
  bool _loading = true;
  NotificationChannel _preferred = NotificationChannel.app;
  MascotExpression _expression = MascotExpression.wink;
  Timer? _celebrationTimer;

  AuthService get _auth => widget.service ?? authService;
  ProfileService get _profile => widget.profileService ?? profileService;
  NotificationPrefs get _prefs => widget.prefs ?? notificationPrefs;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _load();
    _loadPreference();
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

  Future<void> _loadPreference() async {
    final preferred = await _prefs.read();
    if (mounted) setState(() => _preferred = preferred);
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
      await _showInfo(
        'Telegram vinculado',
        'Tu cuenta ya está vinculada con el bot de TAIA.',
      );
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

  Future<void> _openNotifications() async {
    final linked = _user?.telegramLinked ?? false;
    final result = await showNotificationSheet(
      context,
      current: effectiveChannel(_preferred, telegramLinked: linked),
      telegramLinked: linked,
    );
    if (!mounted || result == null) return;
    switch (result) {
      case NotificationSheetResult.linkTelegram:
        await _openTelegram();
      case NotificationSheetResult.app:
        await _savePreference(NotificationChannel.app);
      case NotificationSheetResult.telegram:
        await _savePreference(NotificationChannel.telegram);
    }
  }

  Future<void> _savePreference(NotificationChannel channel) async {
    await _prefs.save(channel);
    if (!mounted) return;
    setState(() => _preferred = channel);
    _toast(
      channel == NotificationChannel.telegram
          ? 'Listo: tus recordatorios irán por Telegram.'
          : 'Listo: verás tus recordatorios en la aplicación.',
    );
  }

  Future<void> _showInfo(String title, String message) {
    return showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: TaiaColors.ivoryMist,
        title: Text(
          title,
          style: const TextStyle(color: taiaInk, fontWeight: FontWeight.w900),
        ),
        content: Text(message, style: const TextStyle(color: taiaInk)),
        actions: [
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: TaiaColors.fieryRose,
            ),
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Entendido'),
          ),
        ],
      ),
    );
  }

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
    await _prefs.clear();
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
    final channel = effectiveChannel(
      _preferred,
      telegramLinked: user.telegramLinked,
    );
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
                subtitle: 'Nombre y foto',
                comingSoon: true,
                onTap: () => _showInfo(
                  'Editar perfil',
                  'Todavía no se puede cambiar el nombre ni la foto desde la '
                      'app: el servidor aún no lo permite. Lo dejaremos listo '
                      'en cuanto esté disponible.',
                ),
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
            title: 'INTEGRACIONES',
            tiles: [
              ProfileTile(
                icon: Icons.send_outlined,
                title: 'Telegram',
                subtitle: user.telegramLinked
                    ? 'Cuenta vinculada'
                    : 'Habla con TAIA y recibe avisos en el chat',
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
            title: 'PREFERENCIAS',
            tiles: [
              ProfileTile(
                icon: Icons.notifications_none_rounded,
                title: 'Notificaciones',
                subtitle: channel.label,
                onTap: _openNotifications,
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
                icon: Icons.delete_outline,
                title: 'Eliminar cuenta',
                subtitle: 'Borra tu cuenta y tus datos',
                danger: true,
                comingSoon: true,
                onTap: () => _showInfo(
                  'Eliminar cuenta',
                  'La eliminación de la cuenta todavía no está disponible en '
                      'el servidor. Cuando lo esté, la encontrarás aquí.',
                ),
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
                'Tus datos y cómo quieres que te avise.',
                style: TextStyle(color: Color(0xA63B2A2A), fontSize: 14),
              ),
            ],
          ),
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            const RemindersBell(),
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