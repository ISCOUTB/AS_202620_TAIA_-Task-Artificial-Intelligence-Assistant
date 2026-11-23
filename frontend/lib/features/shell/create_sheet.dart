import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../theme/taia_colors.dart';
import '../auth/auth_shell.dart';

/// Lo que se puede crear desde el botón central (RNF-14).
enum CreateOption {
  activity(
    Icons.assignment_outlined,
    'Nueva actividad',
    'Una tarea o un examen, con sus recordatorios.',
  ),
  classBlock(
    Icons.schedule_outlined,
    'Nueva clase',
    'Una materia en tu horario, uno o varios días.',
  ),
  subject(
    Icons.menu_book_outlined,
    'Nueva asignatura',
    'Una materia nueva, con su profesor.',
  );

  const CreateOption(this.icon, this.title, this.hint);

  final IconData icon;
  final String title;
  final String hint;
}

/// Hoja del botón central: un solo lugar para crear (RNF-14). Devuelve la
/// opción elegida, o null si se cierra.
Future<CreateOption?> showCreateSheet(BuildContext context) {
  HapticFeedback.selectionClick();
  return showModalBottomSheet<CreateOption>(
    context: context,
    isScrollControlled: true,
    backgroundColor: TaiaColors.ivoryMist,
    showDragHandle: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (context) => const _CreateSheet(),
  );
}

class _CreateSheet extends StatelessWidget {
  const _CreateSheet();

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.of(context).disableAnimations;
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              '¿Qué quieres crear?',
              style: TextStyle(
                color: taiaInk,
                fontSize: 22,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 16),
            for (final (index, option) in CreateOption.values.indexed) ...[
              _Appear(
                delay: Duration(milliseconds: reduceMotion ? 0 : 60 * index),
                enabled: !reduceMotion,
                child: _OptionCard(option: option),
              ),
              const SizedBox(height: 10),
            ],
          ],
        ),
      ),
    );
  }
}

class _OptionCard extends StatelessWidget {
  const _OptionCard({required this.option});

  final CreateOption option;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: () {
          HapticFeedback.lightImpact();
          Navigator.of(context).pop(option);
        },
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: TaiaColors.softPeach,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(option.icon, color: TaiaColors.fieryRose),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      option.title,
                      style: const TextStyle(
                        color: taiaInk,
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      option.hint,
                      style: const TextStyle(
                        color: Color(0xA63B2A2A),
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: taiaInk),
            ],
          ),
        ),
      ),
    );
  }
}

/// Entrada corta: sube un poco y aparece (300 ms o menos, RNF-14).
class _Appear extends StatelessWidget {
  const _Appear({
    required this.delay,
    required this.enabled,
    required this.child,
  });

  final Duration delay;
  final bool enabled;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    if (!enabled) return child;
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: const Duration(milliseconds: 260) + delay,
      curve: Interval(
        delay.inMilliseconds / (260 + delay.inMilliseconds),
        1,
        curve: Curves.easeOutCubic,
      ),
      builder: (context, t, child) => Opacity(
        opacity: t,
        child: Transform.translate(
          offset: Offset(0, 16 * (1 - t)),
          child: child,
        ),
      ),
      child: child,
    );
  }
}
