import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../mascot/taia_mascot.dart';
import '../../theme/taia_colors.dart';
import '../agent/agent_service.dart';
import '../auth/auth_service.dart';
import '../auth/auth_shell.dart';
import '../study_plan/study_plan_card.dart';
import 'home_data.dart';
import 'home_service.dart';
import 'widgets/home_header.dart';
import 'widgets/today_card.dart';
import 'widgets/upcoming_deliveries.dart';
import 'widgets/weekly_summary.dart';
import 'widgets/taia_bubble.dart';

/// Pestaña de inicio: resumen del día, próximas entregas, resumen semanal y el
/// botón con la mascota que abre la conversación con el agente (RF-AGT-01).
class HomeScreen extends StatefulWidget {
  const HomeScreen({
    super.key,
    this.service,
    this.agentService,
    this.onSeeAllTasks,
  });

  /// Origen de los datos; si es null se usa el compartido de la app.
  final HomeService? service;

  /// Servicio del agente; si es null se usa el compartido de la app.
  final AgentService? agentService;

  /// Se llama al pulsar "Ver todas" (lleva a la pestaña de tareas).
  final VoidCallback? onSeeAllTasks;

  @override
  State<HomeScreen> createState() => HomeScreenState();
}

class HomeScreenState extends State<HomeScreen> {
  HomeData? _data;
  String? _error;
  bool _loading = true;

  /// Cambia en cada carga para que la tarjeta del plan también se actualice.
  int _version = 0;

  HomeService get _service => widget.service ?? homeService;

  @override
  void initState() {
    super.initState();
    _load();
  }

  /// Vuelve a pedir los datos sin ocultar lo que ya se muestra.
  Future<void> refresh() => _load(silent: _data != null);

  Future<void> _load({bool silent = false}) async {
    if (!silent) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final data = await _service.load();
      if (!mounted) return;
      setState(() {
        _data = data;
        _error = null;
        _loading = false;
        _version++;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        // Si ya había datos, se conservan y se ignora el fallo.
        if (_data == null) _error = e.message;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final data = _data;
    return Scaffold(
      backgroundColor: TaiaColors.ivoryMist,
      // RF-AGT-23: TAIA con su burbuja, sin botón flotante blanco.
      floatingActionButton: TaiaBubble(
        text: data?.taiaBubble ?? '¿Te ayudo con algo hoy?',
        service: widget.agentService,
        // El agente pudo crear o completar actividades.
        onClosed: () => refresh(),
      ),
      body: SafeArea(
        child: data != null
            ? _content(data)
            : _loading
            ? const _Message(
                expression: MascotExpression.thinking,
                text: 'Preparando tu día…',
                showSpinner: true,
              )
            : _Message(
                expression: MascotExpression.surprised,
                text: _error ?? 'No se pudo cargar tu inicio.',
                onRetry: _load,
              ),
      ),
    );
  }

  Widget _content(HomeData data) {
    return RefreshIndicator(
      color: TaiaColors.fieryRose,
      onRefresh: () => _load(silent: true),
      child: ListView(
        // Espacio abajo para que el botón del agente no tape el resumen.
        padding: const EdgeInsets.fromLTRB(0, 16, 0, 112),
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: HomeHeader(firstName: data.firstName),
          ),
          const SizedBox(height: 16),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: TodayCard(data: data),
          ),
          const SizedBox(height: 16),
          // RNF-14: el plan de estudio, a la vista desde el Inicio.
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: StudyPlanCard(version: _version),
          ),
          const SizedBox(height: 24),
          UpcomingDeliveries(
            tasks: data.upcoming,
            onSeeAll: widget.onSeeAllTasks ?? () {},
          ),
          const SizedBox(height: 24),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: WeeklySummary(
              counts: data.weekCounts,
              total: data.weekTotal,
            ),
          ),
        ],
      ),
    );
  }
}

/// Estado de carga o de error, con la mascota.
class _Message extends StatelessWidget {
  const _Message({
    required this.expression,
    required this.text,
    this.showSpinner = false,
    this.onRetry,
  });

  final MascotExpression expression;
  final String text;
  final bool showSpinner;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              width: 168,
              child: TaiaMascot(motion: 0.6, expression: expression),
            ),
            const SizedBox(height: 16),
            Text(
              text,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: taiaInk,
                fontSize: 16,
                fontWeight: FontWeight.w700,
              ),
            ),
            if (showSpinner) ...[
              const SizedBox(height: 16),
              const CircularProgressIndicator(color: TaiaColors.fieryRose),
            ],
            if (onRetry != null) ...[
              const SizedBox(height: 16),
              FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: TaiaColors.fieryRose,
                ),
                onPressed: onRetry,
                child: const Text('Reintentar'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
