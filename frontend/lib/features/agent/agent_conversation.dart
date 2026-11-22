import 'package:flutter/foundation.dart';

import '../../core/api_error.dart';
import 'agent_service.dart';

/// Largo máximo de un mensaje al agente (RF-AGT-16).
const int agentMaxLength = 1000;

/// Un mensaje de la conversación.
class ChatMessage {
  const ChatMessage({required this.text, required this.fromUser});

  final String text;
  final bool fromUser;
}

/// Estado de la conversación con el agente en la app (RF-AGT-01). Vive solo
/// mientras la pantalla está abierta; el contexto lo guarda el backend
/// (RF-AGT-15).
class AgentConversation extends ChangeNotifier {
  AgentConversation(this._service);

  final AgentService _service;

  final List<ChatMessage> _messages = [];
  bool _sending = false;
  bool _awaitingConfirmation = false;
  String? _error;

  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get sending => _sending;

  /// El último mensaje del agente propuso una acción (RF-AGT-04).
  bool get awaitingConfirmation => _awaitingConfirmation;
  String? get error => _error;

  /// Envía [text]. Devuelve false si no se envió (vacío, muy largo o con otro
  /// envío en curso).
  Future<bool> send(String text) async {
    final clean = text.trim();
    if (clean.isEmpty || _sending) return false;
    if (clean.length > agentMaxLength) {
      _error = 'El mensaje no puede superar $agentMaxLength caracteres.';
      notifyListeners();
      return false;
    }
    _messages.add(ChatMessage(text: clean, fromUser: true));
    _sending = true;
    _awaitingConfirmation = false;
    _error = null;
    notifyListeners();
    try {
      final reply = await _service.send(clean);
      _messages.add(ChatMessage(text: reply.text, fromUser: false));
      _awaitingConfirmation = reply.awaitingConfirmation;
    } on ApiException catch (e) {
      _error = e.message;
    } finally {
      _sending = false;
      notifyListeners();
    }
    return true;
  }

  /// Responde a la acción propuesta. El backend evalúa la respuesta sin el LLM
  /// (RF-AGT-04).
  Future<bool> confirm(bool yes) => send(yes ? 'sí' : 'no');
}
