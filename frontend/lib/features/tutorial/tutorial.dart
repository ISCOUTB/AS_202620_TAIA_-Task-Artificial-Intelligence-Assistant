import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:showcaseview/showcaseview.dart';

import '../../theme/taia_colors.dart';
import '../auth/auth_shell.dart';

/// Tutorial de la primera vez (RF-USR-12): TAIA señala las partes principales
/// de la app, en este orden.
class AppTutorial {
  AppTutorial._();

  static final taia = GlobalKey(debugLabel: 'tutorial-taia');
  static final plan = GlobalKey(debugLabel: 'tutorial-plan');
  static final create = GlobalKey(debugLabel: 'tutorial-create');
  static final agenda = GlobalKey(debugLabel: 'tutorial-agenda');
  static final tasks = GlobalKey(debugLabel: 'tutorial-tasks');

  static List<GlobalKey> get steps => [taia, plan, create, agenda, tasks];

  /// Se incrementa para pedir el tutorial otra vez desde la configuración.
  static final replayRequests = ValueNotifier<int>(0);

  /// Hay un tutorial registrado (lo registra el contenedor de la app). Sin él,
  /// los pasos muestran solo su contenido, por ejemplo en pantallas sueltas.
  static bool registered = false;
}

/// Quita el tutorial registrado con [registerTutorial].
void unregisterTutorial() {
  if (!AppTutorial.registered) return;
  ShowcaseView.get().unregister();
  AppTutorial.registered = false;
}

/// Recuerda en el teléfono si el tutorial ya se vio (RF-USR-12): no es un
/// dato del servidor. Cerrar sesión no lo borra.
class TutorialStore {
  TutorialStore([FlutterSecureStorage? storage])
    : _storage = storage ?? const FlutterSecureStorage();

  static const _key = 'tutorial_seen_v1';

  final FlutterSecureStorage _storage;

  Future<bool> seen() async => await _storage.read(key: _key) == 'true';

  Future<void> markSeen() => _storage.write(key: _key, value: 'true');
}

/// Registra el tutorial con el estilo de TAIA. Cada paso tiene "Siguiente" y
/// "Saltar" (que termina el recorrido); tocar fuera avanza.
ShowcaseView registerTutorial({required VoidCallback onFinish}) {
  const action = TextStyle(color: Colors.white, fontWeight: FontWeight.w800);
  AppTutorial.registered = true;
  // RNF-14: sin flotación ni zoom si el sistema pide reducir el movimiento.
  final reduce = WidgetsBinding
      .instance
      .platformDispatcher
      .accessibilityFeatures
      .disableAnimations;
  return ShowcaseView.register(
    disableMovingAnimation: reduce,
    disableScaleAnimation: reduce,
    onFinish: onFinish,
    onDismiss: (_) => onFinish(),
    // Si un paso no está en pantalla (por ejemplo, el Inicio aún no cargó),
    // se salta en vez de trabar el recorrido.
    skipIfTargetNotPresent: true,
    overlayOpacity: 0.6,
    globalTooltipActionConfig: const TooltipActionConfig(
      alignment: MainAxisAlignment.spaceBetween,
      position: TooltipActionPosition.inside,
    ),
    globalTooltipActions: const [
      TooltipActionButton(
        type: TooltipDefaultActionType.skip,
        name: 'Saltar',
        backgroundColor: Colors.transparent,
        textStyle: TextStyle(color: taiaInk, fontWeight: FontWeight.w700),
      ),
      TooltipActionButton(
        type: TooltipDefaultActionType.next,
        name: 'Siguiente',
        backgroundColor: TaiaColors.fieryRose,
        textStyle: action,
      ),
    ],
  );
}

/// Un paso del tutorial alrededor de [child], con la voz de TAIA (RF-AGT-22).
class TutorialTarget extends StatelessWidget {
  const TutorialTarget({
    super.key,
    required this.showcaseKey,
    required this.title,
    required this.description,
    required this.child,
    this.circle = false,
  });

  final GlobalKey showcaseKey;
  final String title;
  final String description;
  final Widget child;

  /// Recorta el resaltado en círculo, para botones redondos.
  final bool circle;

  @override
  Widget build(BuildContext context) {
    if (!AppTutorial.registered) return child;
    return Showcase(
      key: showcaseKey,
      title: title,
      description: description,
      targetShapeBorder: circle
          ? const CircleBorder()
          : const RoundedRectangleBorder(
              borderRadius: BorderRadius.all(Radius.circular(20)),
            ),
      titleTextStyle: const TextStyle(
        color: taiaInk,
        fontSize: 18,
        fontWeight: FontWeight.w900,
      ),
      descTextStyle: const TextStyle(color: taiaInk, fontSize: 14, height: 1.3),
      tooltipBackgroundColor: TaiaColors.ivoryMist,
      tooltipBorderRadius: const BorderRadius.all(Radius.circular(18)),
      child: child,
    );
  }
}
