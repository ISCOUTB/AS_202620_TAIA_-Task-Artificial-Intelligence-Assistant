import 'package:flutter/material.dart';

import '../../theme/taia_colors.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../activity/add_activity_screen.dart';
import '../calendar/calendar_screen.dart';
import '../profile/profile_screen.dart';
import '../tasks/tasks_screen.dart';
import '../home/home_screen.dart';

/// Contenedor de la app con la barra de navegación inferior.
///
/// Las cinco pestañas conservan su estado al cambiar entre ellas. Mientras se
/// construyen las pantallas reales, cada una muestra un [TabPlaceholder].
class MainShell extends StatefulWidget {
  const MainShell({super.key, this.service});

  /// Servicio de autenticación; si es null se usa el compartido de la app.
  final AuthService? service;

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _index = 0;
  final _homeKey = GlobalKey<HomeScreenState>();
  final _tasksKey = GlobalKey<TasksScreenState>();
  final _calendarKey = GlobalKey<CalendarScreenState>();
  final _addKey = GlobalKey<AddActivityScreenState>();
  final _profileKey = GlobalKey<ProfileScreenState>();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _index,
        children: [
          HomeScreen(
            key: _homeKey,
              onSeeAllTasks: () {
              _tasksKey.currentState?.refresh();
              setState(() => _index = 1);
            },
          ),
          TasksScreen(key: _tasksKey),
          CalendarScreen(key: _calendarKey),
          AddActivityScreen(
            key: _addKey,
            onSeeTasks: () {
              _tasksKey.currentState?.refresh();
              setState(() => _index = 1);
            },
          ),
          ProfileScreen(key: _profileKey, service: widget.service),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        backgroundColor: TaiaColors.ivoryMist,
        indicatorColor: TaiaColors.softPeach,
        selectedIndex: _index,
        onDestinationSelected: (i) {
          // Al entrar a Inicio o a Tareas se actualizan sus datos.
          if (i != _index) {
            if (i == 0) _homeKey.currentState?.refresh();
            if (i == 1) _tasksKey.currentState?.refresh();
            if (i == 2) _calendarKey.currentState?.refresh();
            if (i == 3) _addKey.currentState?.refresh();
            if (i == 4) _profileKey.currentState?.refresh();
          }
          setState(() => _index = i);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined, color: taiaInk),
            selectedIcon: Icon(Icons.home, color: TaiaColors.fieryRose),
            label: 'Inicio',
          ),
          NavigationDestination(
            icon: Icon(Icons.checklist_outlined, color: taiaInk),
            selectedIcon: Icon(Icons.checklist, color: TaiaColors.fieryRose),
            label: 'Tareas',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_month_outlined, color: taiaInk),
            selectedIcon: Icon(
              Icons.calendar_month,
              color: TaiaColors.fieryRose,
            ),
            label: 'Calendario',
          ),
          NavigationDestination(
            icon: Icon(Icons.add_circle_outline, color: taiaInk),
            selectedIcon: Icon(Icons.add_circle, color: TaiaColors.fieryRose),
            label: 'Añadir',
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