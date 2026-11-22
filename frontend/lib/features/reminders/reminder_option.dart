import '../../core/bogota_time.dart';

/// Opción de recordatorios al crear una actividad (RF-TAR-02).
enum ReminderMode { defaults, custom, none }

/// Máximo de fechas personalizadas (RF-TAR-02).
const maxCustomReminders = 10;

class ReminderOption {
  const ReminderOption(this.mode, [this.customAt = const []]);

  final ReminderMode mode;

  /// Solo con [ReminderMode.custom].
  final List<DateTime> customAt;

  Map<String, dynamic> toJson() => {
    'mode': switch (mode) {
      ReminderMode.defaults => 'default',
      ReminderMode.custom => 'custom',
      ReminderMode.none => 'none',
    },
    if (mode == ReminderMode.custom)
      'custom_at': [for (final at in customAt) formatApiDateTime(at)],
  };
}
