
import '../agent/taia_chat_button.dart';
import 'dart:async';

import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../academic/schedule_screen.dart';
import '../academic/subjects_screen.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../notifications/notifications_bell.dart';
import '../shell/mascot_message.dart';
import 'profile_service.dart';
import 'statistics_screen.dart';
import '../study_plan/study_plan_screen.dart';
import 'settings_screen.dart';
import 'statistics_service.dart';
import 'widgets/profile_card.dart';
import 'widgets/profile_tile.dart';

/// Pestaña de perfil: datos de la cuenta (RF-USR-06, 07 y 09), asignaturas y
/// horario, integración con Telegram (RF-TEL-01 y 03) y cierre de sesión.
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({
    super.key,
    this.service,
    this.profileService,
    this.statisticsService,
  });

  /// Servicio de autenticación; si es null se usa el compartido de la app.
  final AuthService? service;
  final ProfileService? profileService;
  final StatisticsService? statisticsService;

  @override
  State<ProfileScreen> createState() => ProfileScreenState();
}

class ProfileScreenState extends State<ProfileScreen>
    with WidgetsBindingObserver {
  UserProfile? _user;
  String? _error;
  bool _loading = true;
  final MascotExpression _expression = MascotExpression.wink;
  Timer? _celebrationTimer;

  AuthService get _auth => widget.service ?? authService;

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

  final _statisticsKey = GlobalKey<StatisticsSectionState>();

  /// Vuelve a pedir los datos sin ocultar lo que ya se muestra.
  Future<void> refresh() async {
    await Future.wait([
      _load(silent: _user != null),
      if (_statisticsKey.currentState != null)
        _statisticsKey.currentState!.refresh(),
    ]);
  }

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

  Future<void> _openSettings() async {
    await _push(
      SettingsScreen(
        service: widget.service,
        profileService: widget.profileService,
      ),
    );
    // Al volver, el nombre o la vinculación pueden haber cambiado.
    if (mounted) await _load(silent: true);
  }

  Future<void> _push(Widget screen) =>
      Navigator.of(context)
          .push(MaterialPageRoute<void>(builder: (_) => screen));

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
    return RefreshIndicator(
      color: TaiaColors.fieryRose,
      onRefresh: refresh,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          _Header(expression: _expression),
          const SizedBox(height: 20),
          ProfileCard(user: user),
          const SizedBox(height: 24),
          // RF-PRF-01: las gráficas se ven al entrar al perfil.
          StatisticsSection(
            key: _statisticsKey,
            service: widget.statisticsService,
          ),
          const SizedBox(height: 24),
          ProfileSection(
            title: 'ACADÉMICO',
            tiles: [
              ProfileTile(
                icon: Icons.auto_stories_outlined,
                title: 'Plan de estudio',
                subtitle: 'TAIA te sugiere cuándo estudiar',
                onTap: () => _push(const StudyPlanScreen()),
              ),
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
            title: 'CUENTA',
            tiles: [
              ProfileTile(
                icon: Icons.settings_outlined,
                title: 'Configuración',
                subtitle: 'Cuenta, Telegram y sesión',
                onTap: _openSettings,
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
            TaiaChatButton(expression: expression, size: 84),
          ],
        ),
      ],
    );
  }
}
