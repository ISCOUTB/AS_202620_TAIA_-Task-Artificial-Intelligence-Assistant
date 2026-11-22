import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';

/// Mensaje que se muestra si el `429` llega sin `detail` (RF-AGT-19).
const String agentLimitMessage =
    'Alcanzaste el límite de mensajes al asistente. Intenta de nuevo más '
    'tarde.';

/// Respuesta del agente a un mensaje.
class AgentReply {
  const AgentReply({required this.text, required this.awaitingConfirmation});

  factory AgentReply.fromJson(Map<String, dynamic> json) => AgentReply(
    text: json['text'] as String,
    awaitingConfirmation: json['awaiting_confirmation'] as bool? ?? false,
  );

  final String text;

  /// El agente propuso una acción de escritura y espera "sí" o "no"
  /// (RF-AGT-04).
  final bool awaitingConfirmation;
}

class AgentService {
  AgentService(this._dio);

  final Dio _dio;

  /// POST /ai/message por el canal de la app (RF-AGT-01). Al superar el límite
  /// de uso el backend responde 429 (RF-AGT-19).
  Future<AgentReply> send(String text) => apiGuard(() async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/ai/message',
        data: {'text': text, 'channel': 'app'},
      );
      return AgentReply.fromJson(response.data!);
    } on DioException catch (e) {
      if (e.response?.statusCode != 429) rethrow;
      final data = e.response?.data;
      final detail = data is Map ? data['detail'] : null;
      throw ApiException(detail is String ? detail : agentLimitMessage);
    }
  });
}

final AgentService agentService = AgentService(apiDio);
