import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_service.dart';
import '../onboarding/onboarding_screen.dart';
import '../onboarding/onboarding_service.dart';
import 'main_shell.dart';
import 'mascot_message.dart';

/// Entrada con la sesión abierta: si falta la configuración inicial, la pide
/// antes de la pantalla principal (RF-ASG-10).
class AppEntry extends StatefulWidget {
  const AppEntry({super.key, this.service, this.onboarding, this.home});

  final AuthService? service;
  final OnboardingService? onboarding;

  /// Pantalla principal. Por defecto, [MainShell].
  final WidgetBuilder? home;

  @override
  State<AppEntry> createState() => _AppEntryState();
}

class _AppEntryState extends State<AppEntry> {
  bool? _complete;

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    bool complete;
    try {
      complete = await (widget.onboarding ?? OnboardingService()).isComplete();
    } catch (_) {
      // Sin red no se bloquea la app: se entra y se revisa en la próxima apertura.
      complete = true;
    }
    if (mounted) setState(() => _complete = complete);
  }

  @override
  Widget build(BuildContext context) {
    return switch (_complete) {
      null => const Scaffold(
        backgroundColor: TaiaColors.ivoryMist,
        body: MascotMessage(
          expression: MascotExpression.thinking,
          text: 'Preparando tu espacio…',
          showSpinner: true,
        ),
      ),
      false => OnboardingScreen(
        service: widget.onboarding,
        onDone: () => setState(() => _complete = true),
      ),
      true => widget.home?.call(context) ?? MainShell(service: widget.service),
    };
  }
}
