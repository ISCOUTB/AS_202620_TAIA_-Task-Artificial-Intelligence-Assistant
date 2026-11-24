import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/spanish_dates.dart';
import '../../../theme/taia_colors.dart';
import '../../academic/widgets/class_composer.dart' show subjectPalette;
import '../../auth/auth_shell.dart';
import '../../tasks/task.dart';
import '../calendar_logic.dart';
import '../calendar_service.dart';

/// Línea de tiempo de la Agenda: clases, sesiones de estudio y actividades en
/// la misma grilla (RF-TAR-11). Con un solo día ocupa todo el ancho y muestra
/// los nombres completos (vista de día); con varios, una columna por día
/// (vista de semana). Las horas se ajustan a lo que hay en esos días.
class WeekTimeline extends StatelessWidget {
  const WeekTimeline({
    super.key,
    required this.days,
    required this.classes,
    required this.tasks,
    required this.selected,
    required this.today,
    required this.onSelectDay,
    required this.onTapTask,
  });

  /// Los días que se muestran, en orden.
  final List<DateTime> days;
  final List<ClassOccurrence> classes;
  final List<AcademicTask> tasks;
  final DateTime selected;
  final DateTime today;
  final ValueChanged<DateTime> onSelectDay;
  final ValueChanged<AcademicTask> onTapTask;

  static const _hoursWidth = 30.0;
  static const _headerHeight = 34.0;

  bool get _single => days.length == 1;

  double get _hourHeight => _single ? 56.0 : 40.0;

  /// Un color por materia, estable dentro de la semana.
  Map<String, Color> _colors() {
    final names = {for (final c in classes) c.subjectName}.toList()..sort();
    return {
      for (final (i, name) in names.indexed)
        name: subjectPalette[i % subjectPalette.length],
    };
  }

  double _y(DateTime t, int firstHour, int lastHour) {
    final hours = t.hour + t.minute / 60 - firstHour;
    return (hours.clamp(0, (lastHour - firstHour).toDouble())) * _hourHeight;
  }

  @override
  Widget build(BuildContext context) {
    final (firstHour, lastHour) = timelineHours(days, classes, tasks);
    final colors = _colors();
    final header = _single ? 0.0 : _headerHeight;
    final gridHeight = (lastHour - firstHour) * _hourHeight;
    final pinHeight = _single ? 26.0 : 18.0;
    final empty =
        !classes.any((c) => days.any((d) => isSameDay(d, c.startsAt))) &&
        !tasks.any((t) => days.any((d) => isSameDay(d, t.dueAt)));

    return LayoutBuilder(
      builder: (context, constraints) {
        final columnWidth =
            (constraints.maxWidth - _hoursWidth) / math.max(1, days.length);
        double x(DateTime day) =>
            _hoursWidth +
            days.indexWhere((d) => isSameDay(d, day)) * columnWidth;

        final children = <Widget>[
          // Líneas de cada hora y su etiqueta.
          for (var h = firstHour; h <= lastHour; h++)
            Positioned(
              top: header + (h - firstHour) * _hourHeight,
              left: 0,
              right: 0,
              child: Row(
                children: [
                  SizedBox(
                    width: _hoursWidth,
                    child: Transform.translate(
                      offset: const Offset(0, -7),
                      child: Text(
                        h == 24 ? '' : '$h',
                        style: TextStyle(
                          color: taiaInk.withValues(alpha: 0.45),
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ),
                  Expanded(
                    child: Container(height: 1, color: const Color(0x143B2A2A)),
                  ),
                ],
              ),
            ),
          // Cabecera de cada día: tocarla elige el día.
          if (!_single)
            for (final day in days)
              Positioned(
                top: 0,
                left: x(day),
                width: columnWidth,
                height: gridHeight + header,
                child: GestureDetector(
                  behavior: HitTestBehavior.translucent,
                  onTap: () => onSelectDay(day),
                  child: Container(
                    decoration: BoxDecoration(
                      color: isSameDay(day, selected)
                          ? TaiaColors.softPeach.withValues(alpha: 0.45)
                          : Colors.transparent,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    alignment: Alignment.topCenter,
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      '${_weekdayInitial(day)}\n${day.day}',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: isSameDay(day, today)
                            ? TaiaColors.fieryRose
                            : taiaInk,
                        fontSize: 11,
                        height: 1.15,
                        fontWeight: isSameDay(day, today)
                            ? FontWeight.w900
                            : FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ),
          // Clases y sesiones de estudio.
          for (final item in classes)
            if (days.any((d) => isSameDay(d, item.startsAt)))
              Positioned(
                top: header + _y(item.startsAt, firstHour, lastHour),
                left: x(item.startsAt) + 2,
                width: columnWidth - 4,
                height: math.max(
                  18,
                  _y(item.endsAt, firstHour, lastHour) -
                      _y(item.startsAt, firstHour, lastHour),
                ),
                child: _ClassBlock(
                  item: item,
                  wide: _single,
                  color: colors[item.subjectName] ?? subjectPalette.first,
                ),
              ),
          // Actividades en su hora de entrega.
          for (final task in tasks)
            if (days.any((d) => isSameDay(d, task.dueAt)))
              Positioned(
                top:
                    header +
                    math.max(
                      0,
                      _y(task.dueAt, firstHour, lastHour) - pinHeight / 2,
                    ),
                left: x(task.dueAt) + 3,
                width: columnWidth - 6,
                height: pinHeight,
                child: _TaskPin(
                  task: task,
                  wide: _single,
                  onTap: () => onTapTask(task),
                ),
              ),
          if (empty && !_single)
            Positioned(
              top: header,
              left: _hoursWidth,
              right: 0,
              height: gridHeight,
              child: Center(
                child: Text(
                  'Aquí aparecerán tus clases',
                  style: TextStyle(
                    color: taiaInk.withValues(alpha: 0.5),
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),
        ];

        return SizedBox(
          height: gridHeight + header + 8,
          child: Stack(clipBehavior: Clip.none, children: children),
        );
      },
    );
  }

  static String _weekdayInitial(DateTime day) =>
      const ['L', 'M', 'X', 'J', 'V', 'S', 'D'][day.weekday - 1];
}

class _ClassBlock extends StatelessWidget {
  const _ClassBlock({
    required this.item,
    required this.wide,
    required this.color,
  });

  final ClassOccurrence item;
  final bool wide;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final study = item.isStudy;
    final label = study ? item.studyTitle! : item.subjectName;
    final room = item.room;
    final hours =
        '${formatClockTime(item.startsAt)} – ${formatClockTime(item.endsAt)}';
    final textColor = study ? taiaInk : Colors.white;
    return Semantics(
      label: '${study ? 'Estudio' : 'Clase'}: $label, $hours',
      excludeSemantics: true,
      child: Container(
        padding: wide
            ? const EdgeInsets.symmetric(horizontal: 10, vertical: 6)
            : const EdgeInsets.symmetric(horizontal: 3, vertical: 2),
        decoration: BoxDecoration(
          color: study ? color.withValues(alpha: 0.22) : color,
          borderRadius: BorderRadius.circular(wide ? 12 : 8),
          border: study ? Border.all(color: color, width: 1.2) : null,
        ),
        child: wide
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    study ? 'Estudiar: $label' : label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: textColor,
                      fontSize: 14,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  Flexible(
                    child: Text(
                      [
                        hours,
                        if (study) item.subjectName,
                        if (!study && room != null) room,
                      ].join(' · '),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: textColor.withValues(alpha: 0.85),
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              )
            : Text(
                label,
                maxLines: 3,
                overflow: TextOverflow.fade,
                style: TextStyle(
                  color: textColor,
                  fontSize: 9.5,
                  height: 1.1,
                  fontWeight: FontWeight.w700,
                ),
              ),
      ),
    );
  }
}

class _TaskPin extends StatelessWidget {
  const _TaskPin({required this.task, required this.wide, required this.onTap});

  final AcademicTask task;
  final bool wide;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final done = task.status == TaskStatus.completed;
    final exam = task.type == TaskType.exam;
    final color = done
        ? const Color(0xFF9E9E9E)
        : exam
        ? const Color(0xFFB3261E)
        : TaiaColors.sunsetCoral;
    return Semantics(
      button: true,
      label: '${exam ? 'Examen' : 'Tarea'}: ${task.title}',
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: wide ? 10 : 3),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(wide ? 10 : 6),
            border: Border.all(color: color, width: 1.4),
          ),
          alignment: Alignment.centerLeft,
          child: Row(
            children: [
              if (wide) ...[
                Icon(
                  exam ? Icons.assignment_late_outlined : Icons.flag_outlined,
                  size: 14,
                  color: color,
                ),
                const SizedBox(width: 6),
                Text(
                  '${formatClockTime(task.dueAt)} · ',
                  style: TextStyle(
                    color: color,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
              Expanded(
                child: Text(
                  task.title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: color,
                    fontSize: wide ? 12 : 9,
                    fontWeight: FontWeight.w800,
                    decoration: done ? TextDecoration.lineThrough : null,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
