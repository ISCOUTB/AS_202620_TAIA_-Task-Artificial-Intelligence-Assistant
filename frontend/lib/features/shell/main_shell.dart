import 'package:flutter/material.dart';

import '../../core/motion.dart';
import '../../theme/taia_colors.dart';
import '../academic/schedule_service.dart';
import '../academic/widgets/class_composer.dart';
import '../activity/add_activity_screen.dart';
import '../activity/widgets/new_subject_dialog.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../calendar/calendar_screen.dart';
import '../home/home_screen.dart';
import '../notifications/push_registration.dart';
import '../profile/profile_screen.dart';
import '../tasks/subjects_service.dart';
import '../tasks/tasks_screen.dart';
import 'create_sheet.dart';

/// Pestañas de la barra inferior (RNF-14). El botón central "+" no es una
/// pestaña: abre la hoja para crear.
enum ShellTab { home, agenda, tasks, profile }

/// Contenedor de la app con la barra de navegación inferior: Inicio, Agenda,
/// "+", Tareas y Perfil (RNF-14). Las pestañas conservan su estado al cambiar
/// entre ellas.
class MainShell extends StatefulWidget {
  const MainShell({super.key, this.service});

  /// Servicio de autenticación; si es null se usa el compartido de la app.
  final AuthService? service;

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell>
    with SingleTickerProviderStateMixin {
  ShellTab _tab = ShellTab.home;
  final _homeKey = GlobalKey<HomeScreenState>();
  final _tasksKey = GlobalKey<TasksScreenState>();
  final _calendarKey = GlobalKey<CalendarScreenState>();
  final _profileKey = GlobalKey<ProfileScreenState>();

  /// Posición del "+" entre los destinos de la barra.
  static const _createSlot = 2;

  /// Desvanecido corto al cambiar de pestaña (RNF-14). Anima la pila entera,
  /// así las pestañas conservan su estado.
  late final AnimationController _tabFade = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 200),
    value: 1,
  );

  /// Con la sesión abierta se registra el dispositivo para push (RF-NOT-01).
  final PushRegistration? _push = buildPushRegistration();

  @override
  void initState() {
    super.initState();
    _push?.onForegroundMessage = _showForegroundNotification;
    _push?.start();
  }

  /// Con la app abierta, Android no muestra la notificación: se avisa aquí.
  void _showForegroundNotification(String message) {
    if (!mounted || message.isEmpty) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        backgroundColor: TaiaColors.fieryRose,
        duration: const Duration(seconds: 6),
      ),
    );
  }

  @override
  void dispose() {
    _tabFade.dispose();
    _push?.stop();
    super.dispose();
  }

  void _goTo(ShellTab tab) {
    if (tab != _tab) {
      switch (tab) {
        case ShellTab.home:
          _homeKey.currentState?.refresh();
        case ShellTab.agenda:
          _calendarKey.currentState?.refresh();
        case ShellTab.tasks:
          _tasksKey.currentState?.refresh();
        case ShellTab.profile:
          _profileKey.currentState?.refresh();
      }
    }
    if (tab != _tab && !reduceMotion(context)) _tabFade.forward(from: 0.3);
    setState(() => _tab = tab);
  }

  /// Algo nuevo puede cambiar el inicio, la agenda y las tareas.
  void _refreshAfterCreate() {
    _homeKey.currentState?.refresh();
    _calendarKey.currentState?.refresh();
    _tasksKey.currentState?.refresh();
  }

  void _toast(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _create() async {
    final option = await showCreateSheet(context);
    if (!mounted || option == null) return;
    switch (option) {
      case CreateOption.activity:
        await Navigator.of(context).push(
          MaterialPageRoute<void>(
            builder: (routeContext) => AddActivityScreen(
              onSeeTasks: () {
                Navigator.of(routeContext).pop();
                _goTo(ShellTab.tasks);
              },
            ),
          ),
        );
        if (mounted) _refreshAfterCreate();
      case CreateOption.classBlock:
        await _createClass();
      case CreateOption.subject:
        final subject = await showNewSubjectDialog(context);
        if (!mounted || subject == null) return;
        _toast('Listo, agregué ${subject.name}.');
        _refreshAfterCreate();
    }
  }

  Future<void> _createClass() async {
    try {
      final subjects = await subjectsService.list();
      if (!mounted) return;
      if (subjects.isEmpty) {
        _toast('Primero crea una asignatura para ponerla en tu horario.');
        return;
      }
      final result = await showClassComposer(
        context,
        service: scheduleService,
        subjects: subjects,
      );
      if (!mounted || result == null) return;
      _toast(describeComposerResult(result));
      _refreshAfterCreate();
    } on ApiException catch (e) {
      if (mounted) _toast(e.message);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: FadeTransition(
        opacity: CurvedAnimation(parent: _tabFade, curve: Curves.easeOut),
        child: IndexedStack(
          index: _tab.index,
          children: [
            HomeScreen(
              key: _homeKey,
              onSeeAllTasks: () => _goTo(ShellTab.tasks),
            ),
            CalendarScreen(key: _calendarKey),
            TasksScreen(key: _tasksKey),
            ProfileScreen(key: _profileKey, service: widget.service),
          ],
        ),
      ),
      bottomNavigationBar: NavigationBar(
        backgroundColor: TaiaColors.ivoryMist,
        indicatorColor: TaiaColors.softPeach,
        selectedIndex: _tab.index < _createSlot ? _tab.index : _tab.index + 1,
        onDestinationSelected: (i) {
          if (i == _createSlot) {
            _create();
            return;
          }
          // Al entrar a una pestaña se actualizan sus datos.
          _goTo(ShellTab.values[i < _createSlot ? i : i - 1]);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined, color: taiaInk),
            selectedIcon: Icon(Icons.home, color: TaiaColors.fieryRose),
            label: 'Inicio',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_month_outlined, color: taiaInk),
            selectedIcon: Icon(
              Icons.calendar_month,
              color: TaiaColors.fieryRose,
            ),
            label: 'Agenda',
          ),
          NavigationDestination(
            icon: _CreateButton(),
            tooltip: 'Crear',
            label: 'Crear',
          ),
          NavigationDestination(
            icon: Icon(Icons.checklist_outlined, color: taiaInk),
            selectedIcon: Icon(Icons.checklist, color: TaiaColors.fieryRose),
            label: 'Tareas',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline, color: taiaInk),
            selectedIcon: Icon(Icons.person, color: TaiaColors.fieryRose),
            label: 'Perfil',
          ),
        ],
      ),
    );
  }
}

/// El "+" central: un círculo de color, distinto de las pestañas.
class _CreateButton extends StatelessWidget {
  const _CreateButton();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 52,
      height: 52,
      decoration: const BoxDecoration(
        color: TaiaColors.fieryRose,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: Color(0x40F26A6C),
            blurRadius: 12,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: const Icon(Icons.add, color: Colors.white, size: 30),
    );
  }
}
