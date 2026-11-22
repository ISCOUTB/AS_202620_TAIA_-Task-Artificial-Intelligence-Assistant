import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../activity/widgets/new_subject_dialog.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../profile/widgets/profile_tile.dart';
import '../shell/mascot_message.dart';
import '../tasks/subject.dart';
import '../tasks/subjects_service.dart';
import '../tasks/widgets/task_form_widgets.dart';
import '../shell/page_header.dart';
import 'widgets/subject_sheet.dart';

/// Asignaturas del usuario (RF-ASG-02): las activas por defecto o también las
/// archivadas. Desde aquí se crean (RF-ASG-01) y se abre el detalle de cada
/// una.
class SubjectsScreen extends StatefulWidget {
  const SubjectsScreen({super.key, this.service});

  final SubjectsService? service;

  @override
  State<SubjectsScreen> createState() => _SubjectsScreenState();
}

class _SubjectsScreenState extends State<SubjectsScreen> {
  List<Subject>? _items;
  String? _error;
  bool _includeArchived = false;

  SubjectsService get _service => widget.service ?? subjectsService;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _error = null);
    try {
      final items = await _service.list(includeArchived: _includeArchived);
      if (mounted) setState(() => _items = items);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _create() async {
    final created = await showNewSubjectDialog(context, service: _service);
    if (created != null && mounted) await _load();
  }

  Future<void> _open(Subject subject) async {
    await showSubjectSheet(context, subject, service: _service);
    if (mounted) await _load();
  }

  static String _subtitle(Subject subject) {
    final pending = subject.pendingTasks;
    return [
      if (subject.teacher != null) subject.teacher!,
      pending == 1 ? '1 pendiente' : '$pending pendientes',
      if (subject.archived) 'Archivada',
    ].join(' · ');
  }

  @override
  Widget build(BuildContext context) {
    final items = _items;
    return Scaffold(
      backgroundColor: TaiaColors.ivoryMist,
      body: SafeArea(
        child: items == null
            ? MascotMessage(
                expression: _error == null
                    ? MascotExpression.thinking
                    : MascotExpression.surprised,
                text: _error ?? 'Cargando tus asignaturas…',
                showSpinner: _error == null,
                onRetry: _error == null ? null : _load,
              )
            : RefreshIndicator(
                color: TaiaColors.fieryRose,
                onRefresh: _load,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                  children: [
                    const PageHeader(
                      label: 'ACADÉMICO',
                      title: 'Asignaturas',
                      subtitle: 'Tus materias, sus alias y su estado.',
                    ),
                    const SizedBox(height: 20),
                    TaskSegments<bool>(
                      value: _includeArchived,
                      options: const {false: 'Activas', true: 'Con archivadas'},
                      onChanged: (value) {
                        setState(() => _includeArchived = value);
                        _load();
                      },
                    ),
                    const SizedBox(height: 16),
                    if (items.isEmpty)
                      const EmptyStateCard(
                        'Todavía no tienes asignaturas. Crea la primera.',
                      )
                    else
                      ProfileSection(
                        title: 'MATERIAS',
                        tiles: [
                          for (final subject in items)
                            ProfileTile(
                              icon: subject.archived
                                  ? Icons.inventory_2_outlined
                                  : Icons.menu_book_outlined,
                              title: subject.name,
                              subtitle: _subtitle(subject),
                              onTap: () => _open(subject),
                            ),
                        ],
                      ),
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      AuthErrorText(_error!),
                    ],
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      style: FilledButton.styleFrom(
                        backgroundColor: TaiaColors.fieryRose,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      onPressed: _create,
                      icon: const Icon(Icons.add),
                      label: const Text(
                        'Nueva asignatura',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                  ],
                ),
              ),
      ),
    );
  }
}
