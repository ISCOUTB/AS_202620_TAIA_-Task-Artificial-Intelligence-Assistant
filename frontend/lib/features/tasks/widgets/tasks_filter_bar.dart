import 'package:flutter/material.dart';

import '../../../core/bogota_time.dart';
import '../../../core/spanish_dates.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_shell.dart';
import '../task_filters.dart';

/// Búsqueda por texto, selector de fecha y chips de estado.
class TasksFilterBar extends StatelessWidget {
  const TasksFilterBar({
    super.key,
    required this.searchController,
    required this.onSearchChanged,
    required this.dateFilter,
    required this.pickedDay,
    required this.onDateChanged,
    required this.status,
    required this.onStatusChanged,
  });

  final TextEditingController searchController;
  final ValueChanged<String> onSearchChanged;
  final DateFilter dateFilter;
  final DateTime? pickedDay;
  final void Function(DateFilter filter, DateTime? day) onDateChanged;
  final TaskFilter status;
  final ValueChanged<TaskFilter> onStatusChanged;

  String get _dateLabel {
    if (dateFilter == DateFilter.any) return 'Fecha';
    if (dateFilter == DateFilter.day && pickedDay != null) {
      return formatShortDate(pickedDay!);
    }
    return dateFilter.label;
  }

  OutlineInputBorder _border(Color color, [double width = 1.5]) =>
      OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: BorderSide(color: color, width: width),
      );

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: ValueListenableBuilder<TextEditingValue>(
                valueListenable: searchController,
                builder: (context, value, child) => TextField(
                  controller: searchController,
                  onChanged: onSearchChanged,
                  textInputAction: TextInputAction.search,
                  style: const TextStyle(color: taiaInk),
                  decoration: InputDecoration(
                    hintText: 'Buscar tarea o materia',
                    hintStyle: TextStyle(color: taiaInk.withValues(alpha: 0.5)),
                    prefixIcon: const Icon(
                      Icons.search,
                      color: TaiaColors.fieryRose,
                    ),
                    suffixIcon: value.text.isEmpty
                        ? null
                        : IconButton(
                            tooltip: 'Borrar búsqueda',
                            icon: const Icon(Icons.close, size: 18),
                            onPressed: () {
                              searchController.clear();
                              onSearchChanged('');
                            },
                          ),
                    filled: true,
                    fillColor: Colors.white,
                    contentPadding: const EdgeInsets.symmetric(vertical: 14),
                    border: _border(TaiaColors.softPeach),
                    enabledBorder: _border(TaiaColors.softPeach),
                    focusedBorder: _border(TaiaColors.fieryRose, 2),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 10),
            PopupMenuButton<DateFilter>(
              tooltip: 'Filtrar por fecha',
              initialValue: dateFilter,
              onSelected: (selected) async {
                if (selected != DateFilter.day) {
                  onDateChanged(selected, null);
                  return;
                }
                final now = bogotaNow();
                final day = await showDatePicker(
                  context: context,
                  initialDate: pickedDay ?? now,
                  firstDate: DateTime(2020),
                  lastDate: DateTime(2100),
                );
                if (day != null) onDateChanged(DateFilter.day, day);
              },
              itemBuilder: (context) => [
                for (final option in DateFilter.values)
                  PopupMenuItem(value: option, child: Text(option.label)),
              ],
              child: Container(
                height: 52,
                padding: const EdgeInsets.symmetric(horizontal: 14),
                decoration: BoxDecoration(
                  color: dateFilter == DateFilter.any
                      ? Colors.white
                      : TaiaColors.softPeach,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(
                    color: dateFilter == DateFilter.any
                        ? TaiaColors.softPeach
                        : TaiaColors.fieryRose,
                    width: 1.5,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      _dateLabel,
                      style: const TextStyle(
                        color: taiaInk,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const Icon(Icons.keyboard_arrow_down, color: taiaInk),
                  ],
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              for (final filter in TaskFilter.values) ...[
                ChoiceChip(
                  label: Text(filter.label),
                  selected: status == filter,
                  onSelected: (_) => onStatusChanged(filter),
                  showCheckmark: false,
                  shape: const StadiumBorder(),
                  side: BorderSide.none,
                  selectedColor: TaiaColors.fieryRose,
                  backgroundColor: TaiaColors.softPeach.withValues(alpha: 0.6),
                  labelStyle: TextStyle(
                    color: status == filter ? Colors.white : taiaInk,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(width: 8),
              ],
            ],
          ),
        ),
      ],
    );
  }
}