import 'package:flutter/material.dart';

import '../../../core/spanish_dates.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';

/// "Resumen semanal": barras con las tareas que vencen cada día (L a D).
class WeeklySummary extends StatelessWidget {
  const WeeklySummary({super.key, required this.counts, required this.total});

  /// Tareas por día, de lunes (0) a domingo (6).
  final List<int> counts;
  final int total;

  static const double _maxBar = 100;
  static const double _minBar = 12;

  @override
  Widget build(BuildContext context) {
    final maxCount = counts.fold<int>(0, (m, n) => n > m ? n : m);
    final todayIndex = DateTime.now().weekday - 1;
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 18, 20, 16),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: TaiaColors.softPeach),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Resumen semanal',
                style: TextStyle(
                  color: taiaInk,
                  fontSize: 18,
                  fontWeight: FontWeight.w900,
                ),
              ),
              Text(
                total == 1 ? '1 tarea' : '$total tareas',
                style: TextStyle(
                  color: taiaInk.withValues(alpha: 0.6),
                  fontSize: 13,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          SizedBox(
            height: _maxBar + 24,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                for (var i = 0; i < 7; i++)
                  Expanded(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Semantics(
                          label: '${weekdayInitials[i]}: ${counts[i]}',
                          child: Container(
                            width: 26,
                            height: maxCount == 0 || counts[i] == 0
                                ? _minBar
                                : _minBar +
                                      (_maxBar - _minBar) *
                                          counts[i] /
                                          maxCount,
                            decoration: BoxDecoration(
                              color: i == todayIndex
                                  ? TaiaColors.fieryRose
                                  : TaiaColors.sunsetCoral,
                              borderRadius: BorderRadius.circular(9),
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          weekdayInitials[i],
                          style: TextStyle(
                            color: taiaInk.withValues(alpha: 0.6),
                            fontSize: 12,
                            fontWeight: i == todayIndex
                                ? FontWeight.w900
                                : FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}