import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taia/core/token_storage.dart';
import 'package:taia/features/agent/agent_conversation.dart';
import 'package:taia/features/agent/agent_screen.dart';
import 'package:taia/features/agent/agent_service.dart';
import 'package:taia/features/auth/auth_service.dart';
import 'package:taia/features/home/home_screen.dart';
import 'package:taia/features/home/home_service.dart';
import 'package:taia/features/tasks/tasks_service.dart';

import '../support/fake_api.dart';
import '../support/test_app.dart';

/// Responde con las respuestas de [replies], en orden.
FakeApi _agent(List<FakeResponse> replies) {
  var next = 0;
  return FakeApi(routes({'POST /ai/message': (_) => replies[next++]}));
}

FakeResponse _reply(String text, {bool awaiting = false}) =>
    FakeResponse(200, {'text': text, 'awaiting_confirmation': awaiting});

Future<void> _pump(WidgetTester tester, FakeApi api) async {
  useTallScreen(tester);
  await tester.pumpWidget(
    MaterialApp(home: AgentScreen(service: AgentService(api.dio()))),
  );
  await pumpFrames(tester);
}

Future<void> _write(WidgetTester tester, String text) async {
  await tester.enterText(find.byType(TextField), text);
  await tester.tap(find.byTooltip('Enviar'));
  await pumpFrames(tester);
}

void main() {
  testWidgets(
    'RF-AGT-01 · el chat avisa que TAIA es una IA y que la conversación es temporal',
    (tester) async {
      await _pump(tester, _agent([]));

      expect(find.text(agentDisclaimer), findsOneWidget);
      expect(agentDisclaimer, contains('puede equivocarse'));
      expect(agentDisclaimer, contains('se borra al salir del chat'));
    },
  );

  testWidgets('RF-AGT-01 · envía por el canal app y muestra la respuesta', (
    tester,
  ) async {
    final api = _agent([_reply('Tienes 2 tareas esta semana.')]);
    await _pump(tester, api);

    await _write(tester, '¿Qué tareas tengo esta semana?');

    final request = api.requests.single;
    expect(request.path, '/ai/message');
    expect(request.body, {
      'text': '¿Qué tareas tengo esta semana?',
      'channel': 'app',
    });
    expect(find.text('¿Qué tareas tengo esta semana?'), findsOneWidget);
    expect(find.text('Tienes 2 tareas esta semana.'), findsOneWidget);
    expect(find.text('Sí, confirmo'), findsNothing);
  });

  testWidgets('RF-AGT-04 · "Sí" responde a la acción propuesta', (
    tester,
  ) async {
    final api = _agent([
      _reply(
        'Voy a crear la tarea Taller 3. ¿Confirmas? (sí / no)',
        awaiting: true,
      ),
      _reply('Listo, creé la tarea.'),
    ]);
    await _pump(tester, api);

    await _write(tester, 'Crea el taller 3 de física para el viernes');
    expect(find.text('Sí, confirmo'), findsOneWidget);

    await tester.tap(find.text('Sí, confirmo'));
    await pumpFrames(tester);

    expect(api.requests.last.body, {'text': 'sí', 'channel': 'app'});
    expect(find.text('Listo, creé la tarea.'), findsOneWidget);
    expect(find.text('Sí, confirmo'), findsNothing);
  });

  testWidgets('RF-AGT-04 · "No" cancela la acción propuesta', (tester) async {
    final api = _agent([
      _reply('Voy a completar Taller 3. ¿Confirmas? (sí / no)', awaiting: true),
      _reply('Cancelé la acción.'),
    ]);
    await _pump(tester, api);

    await _write(tester, 'Ya terminé el taller 3');
    await tester.tap(find.text('No'));
    await pumpFrames(tester);

    expect(api.requests.last.body, {'text': 'no', 'channel': 'app'});
    expect(find.text('Cancelé la acción.'), findsOneWidget);
  });

  testWidgets('RF-AGT-19 · el 429 muestra el aviso del límite', (tester) async {
    final api = _agent([
      const FakeResponse(429, {
        'detail':
            'Alcanzaste el límite de mensajes conmigo por ahora. Inténtalo de '
            'nuevo más tarde.',
      }),
    ]);
    await _pump(tester, api);

    await _write(tester, 'Hola');

    expect(find.textContaining('Alcanzaste el límite'), findsOneWidget);
    // El mensaje del usuario queda en la conversación.
    expect(find.text('Hola'), findsOneWidget);
  });

  test('RF-AGT-19 · un 429 sin detalle usa el aviso del cliente', () async {
    final api = _agent([const FakeResponse(429)]);

    await expectLater(
      AgentService(api.dio()).send('Hola'),
      throwsA(
        isA<ApiException>().having(
          (e) => e.message,
          'message',
          agentLimitMessage,
        ),
      ),
    );
  });

  test(
    'RF-AGT-16 · un mensaje de más de 1000 caracteres no se envía',
    () async {
      final api = _agent([]);
      final chat = AgentConversation(AgentService(api.dio()));

      final sent = await chat.send('a' * 1001);

      expect(sent, isFalse);
      expect(api.requests, isEmpty);
      expect(chat.error, contains('1000'));
    },
  );

  testWidgets(
    'RF-AGT-01 · el botón con la mascota del inicio abre la conversación',
    (tester) async {
      useTallScreen(tester);
      final dio = FakeApi((_) => const FakeResponse(500)).dio();
      await tester.pumpWidget(
        MaterialApp(
          home: HomeScreen(
            service: HomeService(
              auth: AuthService(dio: dio, tokens: TokenStorage()),
              tasks: TasksService(dio),
            ),
            agentService: AgentService(dio),
          ),
        ),
      );
      await pumpFrames(tester);
      expect(find.text('Habla con TAIA'), findsNothing);

      await tester.tap(find.byTooltip('Habla con TAIA'));
      await pumpFrames(tester);

      expect(find.byType(AgentScreen), findsOneWidget);
      expect(find.text('Habla con TAIA'), findsOneWidget);
    },
  );
}
