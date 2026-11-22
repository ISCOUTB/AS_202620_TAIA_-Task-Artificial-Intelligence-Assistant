import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fake_api.dart';

/// Responde según `"MÉTODO /ruta"`. Una ruta no prevista responde 500, para
/// que la prueba falle con un mensaje claro.
FakeResponse Function(RequestOptions) routes(
  Map<String, FakeResponse Function(RequestOptions request)> table,
) {
  return (request) {
    final handler = table['${request.method} ${request.path}'];
    if (handler == null) {
      return FakeResponse(500, {
        'detail': 'Ruta no prevista: ${request.method} ${request.path}',
      });
    }
    return handler(request);
  };
}

/// La mascota se anima sin parar, así que `pumpAndSettle` nunca termina: se
/// avanzan unos cuadros.
Future<void> pumpFrames(WidgetTester tester, [int frames = 8]) async {
  for (var i = 0; i < frames; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

/// Pantalla alta para que las hojas y formularios quepan sin desplazarse.
void useTallScreen(WidgetTester tester) {
  tester.view.physicalSize = const Size(900, 2400);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

/// Una app mínima con un botón que ejecuta [open] (por ejemplo, abrir una hoja)
/// y guarda lo que devuelve en [result].
class Launcher<T> extends StatelessWidget {
  const Launcher({super.key, required this.open, required this.result});

  final Future<T?> Function(BuildContext context) open;
  final List<T?> result;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        body: Builder(
          builder: (context) => Center(
            child: TextButton(
              onPressed: () async => result.add(await open(context)),
              child: const Text('abrir'),
            ),
          ),
        ),
      ),
    );
  }
}
