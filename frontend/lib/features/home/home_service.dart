import '../../core/bogota_time.dart';
import '../auth/auth_service.dart';
import '../tasks/task.dart';
import '../tasks/tasks_service.dart';
import 'home_data.dart';

/// Reúne en paralelo lo que necesita la pantalla de inicio.
class HomeService {
  HomeService({required this._auth, required this._tasks});

  final AuthService _auth;
  final TasksService _tasks;

  Future<HomeData> load() async {
    final now = bogotaNow();
    const oneMs = Duration(milliseconds: 1);
    final dayStart = DateTime(now.year, now.month, now.day);
    final dayEnd = DateTime(now.year, now.month, now.day + 1).subtract(oneMs);
    // La semana empieza el lunes.
    final weekStart = DateTime(
      now.year,
      now.month,
      now.day - (now.weekday - 1),
    );
    final weekEnd = DateTime(
      weekStart.year,
      weekStart.month,
      weekStart.day + 7,
    ).subtract(oneMs);

    final results = await Future.wait<Object?>(
      [
        _auth.me(),
        _tasks.list(dueFrom: dayStart, dueTo: dayEnd, limit: 100),
        _tasks.list(status: TaskStatus.pending, limit: 10),
        _tasks.list(dueFrom: weekStart, dueTo: weekEnd, limit: 100),
      ],
      // Si una falla, se informa de inmediato en vez de esperar a las demás.
      eagerError: true,
    );

    return HomeData.build(
      fullName: (results[0]! as UserProfile).fullName,
      todayTasks: (results[1]! as TaskPage).items,
      upcoming: (results[2]! as TaskPage).items,
      weekTasks: (results[3]! as TaskPage).items,
      weekStart: weekStart,
    );
  }
}

final HomeService homeService = HomeService(
  auth: authService,
  tasks: tasksService,
);
