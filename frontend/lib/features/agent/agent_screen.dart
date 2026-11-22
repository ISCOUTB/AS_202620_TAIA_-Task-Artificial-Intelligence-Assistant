import 'package:flutter/material.dart';

import '../../mascot/mascot_expression.dart';
import '../../theme/taia_colors.dart';
import '../auth/auth_shell.dart';
import '../shell/page_header.dart';
import '../tasks/widgets/task_form_widgets.dart';
import 'agent_conversation.dart';
import 'agent_service.dart';

/// Conversación con el agente desde la app (RF-AGT-01): burbujas, botones
/// "Sí" y "No" cuando propone una acción (RF-AGT-04) y el aviso del límite de
/// uso (RF-AGT-19).
class AgentScreen extends StatefulWidget {
  const AgentScreen({super.key, this.service});

  final AgentService? service;

  @override
  State<AgentScreen> createState() => _AgentScreenState();
}

class _AgentScreenState extends State<AgentScreen> {
  late final AgentConversation _chat = AgentConversation(
    widget.service ?? agentService,
  );
  final _input = TextEditingController();
  final _scroll = ScrollController();

  @override
  void initState() {
    super.initState();
    _chat.addListener(_onChange);
  }

  @override
  void dispose() {
    _chat
      ..removeListener(_onChange)
      ..dispose();
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _onChange() {
    setState(() {});
    // Lleva la lista al último mensaje después de pintarlo.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.jumpTo(_scroll.position.maxScrollExtent);
      }
    });
  }

  Future<void> _send() async {
    if (await _chat.send(_input.text)) _input.clear();
  }

  MascotExpression get _expression {
    if (_chat.sending) return MascotExpression.thinking;
    if (_chat.error != null) return MascotExpression.surprised;
    return MascotExpression.happy;
  }

  @override
  Widget build(BuildContext context) {
    final messages = _chat.messages;
    final askConfirmation = _chat.awaitingConfirmation && !_chat.sending;
    return Scaffold(
      backgroundColor: TaiaColors.ivoryMist,
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: PageHeader(
                label: 'ASISTENTE',
                title: 'Habla con TAIA',
                subtitle: 'Crea, consulta y completa tus actividades.',
                expression: _expression,
              ),
            ),
            Expanded(
              child: messages.isEmpty && !_chat.sending
                  ? const Padding(
                      padding: EdgeInsets.all(16),
                      child: Align(
                        alignment: Alignment.topCenter,
                        child: EmptyStateCard(
                          'Escríbeme, por ejemplo: «¿Qué clases tengo '
                          'mañana?» o «Dame el resumen de tareas de este '
                          'mes».',
                        ),
                      ),
                    )
                  : ListView(
                      controller: _scroll,
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                      children: [
                        for (final message in messages)
                          _Bubble(message: message),
                        if (_chat.sending) const _TypingBubble(),
                      ],
                    ),
            ),
            if (askConfirmation)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                child: Row(
                  children: [
                    Expanded(
                      child: FilledButton(
                        style: FilledButton.styleFrom(
                          backgroundColor: TaiaColors.fieryRose,
                        ),
                        onPressed: () => _chat.confirm(true),
                        child: const Text('Sí, confirmo'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: taiaInk,
                          side: const BorderSide(
                            color: TaiaColors.softPeach,
                            width: 1.5,
                          ),
                        ),
                        onPressed: () => _chat.confirm(false),
                        child: const Text('No'),
                      ),
                    ),
                  ],
                ),
              ),
            if (_chat.error != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: AuthErrorText(_chat.error!),
                ),
              ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _input,
                      enabled: !_chat.sending,
                      maxLength: agentMaxLength,
                      minLines: 1,
                      maxLines: 4,
                      style: taskValueStyle,
                      textCapitalization: TextCapitalization.sentences,
                      onSubmitted: (_) => _send(),
                      decoration: taskFieldDecoration(
                        hint: 'Escribe tu mensaje',
                      ).copyWith(counterText: ''),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    tooltip: 'Enviar',
                    onPressed: _chat.sending ? null : _send,
                    style: IconButton.styleFrom(
                      backgroundColor: TaiaColors.fieryRose,
                      foregroundColor: Colors.white,
                    ),
                    icon: const Icon(Icons.send_rounded),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Burbuja de un mensaje: las del usuario a la derecha en rosa y las de TAIA a
/// la izquierda en blanco.
class _Bubble extends StatelessWidget {
  const _Bubble({required this.message});

  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final mine = message.fromUser;
    return Align(
      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.sizeOf(context).width * 0.78,
        ),
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: mine ? TaiaColors.fieryRose : Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(18),
            topRight: const Radius.circular(18),
            bottomLeft: Radius.circular(mine ? 18 : 4),
            bottomRight: Radius.circular(mine ? 4 : 18),
          ),
        ),
        child: Text(
          message.text,
          style: TextStyle(
            color: mine ? Colors.white : taiaInk,
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

/// Burbuja de TAIA mientras responde.
class _TypingBubble extends StatelessWidget {
  const _TypingBubble();

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
        ),
        child: const SizedBox(
          width: 18,
          height: 18,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            color: TaiaColors.fieryRose,
          ),
        ),
      ),
    );
  }
}
