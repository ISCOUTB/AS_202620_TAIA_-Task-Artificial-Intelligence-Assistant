import '../academic/schedule_service.dart';
import '../tasks/subjects_service.dart';

/// RF-ASG-10: la configuración inicial está completa cuando hay período
/// académico y al menos una asignatura activa. Se deduce de esos datos.
class OnboardingService {
  OnboardingService({ScheduleService? schedule, SubjectsService? subjects})
    : _schedule = schedule ?? scheduleService,
      _subjects = subjects ?? subjectsService;

  final ScheduleService _schedule;
  final SubjectsService _subjects;

  ScheduleService get schedule => _schedule;
  SubjectsService get subjects => _subjects;

  Future<bool> isComplete() async {
    final period = await _schedule.period();
    if (period == null) return false;
    final active = await _subjects.list();
    return active.isNotEmpty;
  }
}
