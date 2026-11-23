import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../theme/taia_colors.dart';
import '../../academic/widgets/class_composer.dart' show subjectPalette;
import '../../auth/auth_shell.dart';
import '../../tasks/task.dart';
import '../calendar_logic.dart';
import '../calendar_service.dart';

/// Línea de tiempo de la semana: clases, sesiones de estudio y actividades en
/// la misma grilla (RF-TAR-11, vista de semana de la Agenda).
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

  /// Los siete días, de lunes a domingo.
  final List<DateTime> days;
  final List<ClassOccurrence> classes;
  final List<AcademicTask> tasks;
  final DateTime selected;
  final DateTime today;
  final ValueChanged<DateTime> onSelectDay;
  final ValueChanged<AcademicTask> onTapTask;

  static const hourHeight = 46.0;
  static const _hoursWidth = 30.0;
  static const _headerHeight = 34.0;

  /// Horas visibles: de 7 a 22 como mínimo, y más si hay algo fuera.
  (int, int) _hourRange() {
    var first = 7;
    var last = 22;
    for (final c in classes) {
      first = math.min(first, c.startsAt.hour);
      last = math.max(last, c.endsAt.hour + (c.endsAt.minute > 0 ? 1 : 0));
    }
    for (final t in tasks) {
      first = math.min(first, t.dueAt.hour);
      // Una entrega a las 23:59 se ve al final del día, no en la línea de las 22.
      last = math.max(last, t.dueAt.hour + 1);
    }
    return (first, math.min(last, 24));
  }

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
    return (hours.clamp(0, (lastHour - firstHour).toDouble())) * hourHeight;
  }

  @override
  Widget build(BuildContext context) {
    final (firstHour, lastHour) = _hourRange();
    final colors = _colors();
    final gridHeight = (lastHour - firstHour) * hourHeight;

    return LayoutBuilder(
      builder: (context, constraints) {
        final columnWidth = (constraints.maxWidth - _hoursWidth) / 7;
        double x(DateTime day) =>
            _hoursWidth +
            days.indexWhere((d) => isSameDay(d, day)) * columnWidth;

        final children = <Widget>[
          // Líneas de cada hora y su etiqueta.
          for (var h = firstHour; h <= lastHour; h++)
            Positioned(
              top: _headerHeight + (h - firstHour) * hourHeight,
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
          for (final day in days)
            Positioned(
              top: 0,
              left: x(day),
              width: columnWidth,
              height: gridHeight + _headerHeight,
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
                top: _headerHeight + _y(item.startsAt, firstHour, lastHour),
                left: x(item.startsAt) + 2,
                width: columnWidth - 4,
                height: math.max(
                  18,
                  _y(item.endsAt, firstHour, lastHour) -
                      _y(item.startsAt, firstHour, lastHour),
                ),
                child: _ClassBlock(
                  item: item,
                  color: colors[item.subjectName] ?? subjectPalette.first,
                ),
              ),
          // Actividades en su hora de entrega.
          for (final task in tasks)
            if (days.any((d) => isSameDay(d, task.dueAt)))
              Positioned(
                top:
                    _headerHeight +
                    math.max(0, _y(task.dueAt, firstHour, lastHour) - 9),
                left: x(task.dueAt) + 3,
                width: columnWidth - 6,
                height: 18,
                child: _TaskPin(task: task, onTap: () => onTapTask(task)),
              ),
        ];

        return SizedBox(
          height: gridHeight + _headerHeight + 8,
          child: Stack(clipBehavior: Clip.none, children: children),
        );
      },
    );
  }

  static String _weekdayInitial(DateTime day) =>
      const ['L', 'M', 'X', 'J', 'V', 'S', 'D'][day.weekday - 1];
}

class _ClassBlock extends StatelessWidget {
  const _ClassBlock({required this.item, required this.color});

  final ClassOccurrence item;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final study = item.isStudy;
    final label = study ? item.studyTitle! : item.subjectName;
    return Semantics(
      label:
          '${study ? 'Estudio' : 'Clase'}: $label, '
          '${_hm(item.startsAt)} a ${_hm(item.endsAt)}',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 3, vertical: 2),
        decoration: BoxDecoration(
          color: study ? color.withValues(alpha: 0.22) : color,
          borderRadius: BorderRadius.circular(8),
          border: study ? Border.all(color: color, width: 1.2) : null,
        ),
        child: Text(
          study ? '\u{1F4D6} $label' : label,
          maxLines: 3,
          overflow: TextOverflow.fade,
          style: TextStyle(
            color: study ? taiaInk : Colors.white,
            fontSize: 9.5,
            height: 1.1,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }

  static String _hm(DateTime t) =>
      '${t.hour}:${t.minute.toString().padLeft(2, '0')}';
}

class _TaskPin extends StatelessWidget {
  const _TaskPin({required this.task, required this.onTap});

  final AcademicTask task;
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
          padding: const EdgeInsets.symmetric(horizontal: 3),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: color, width: 1.4),
          ),
          alignment: Alignment.centerLeft,
          child: Text(
            task.title,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: color,
              fontSize: 9,
              fontWeight: FontWeight.w800,
              decoration: done ? TextDecoration.lineThrough : null,
            ),
          ),
        ),
      ),
    );
  }
}
