import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

/// Petición registrada por [FakeApi].
class RecordedRequest {
  const RecordedRequest(this.method, this.path, this.query, this.body);

  final String method;
  final String path;
  final Map<String, dynamic> query;
  final Object? body;
}

/// Respuesta preparada: código y cuerpo JSON.
class FakeResponse {
  const FakeResponse(this.status, [this.body]);

  final int status;
  final Object? body;
}

/// Adaptador HTTP de prueba: no sale a la red, registra cada petición y
/// responde lo que devuelva [handler].
class FakeApi implements HttpClientAdapter {
  FakeApi(this.handler);

  final FakeResponse Function(RequestOptions request) handler;
  final List<RecordedRequest> requests = [];

  /// Un [Dio] que usa este adaptador.
  Dio dio() => Dio(BaseOptions(baseUrl: 'http://test'))..httpClientAdapter = this;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(
      RecordedRequest(
        options.method,
        options.path,
        Map.of(options.queryParameters),
        options.data,
      ),
    );
    final response = handler(options);
    return ResponseBody.fromString(
      response.body == null ? '' : jsonEncode(response.body),
      response.status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

/// Una actividad con el formato de `TaskResponse`.
Map<String, dynamic> taskJson({
  String id = 't1',
  String title = 'Taller 3',
  String status = 'pending',
  String dueAt = '2026-10-10T04:59:00Z',
  String? completedAt,
  String createdAt = '2026-10-01T15:00:00Z',
  String? priority = 'low',
}) => {
  'id': id,
  'subject_id': 's1',
  'subject_name': 'Física',
  'type': 'task',
  'title': title,
  'description': 'Ejercicios',
  'due_at': dueAt,
  'completed_at': completedAt,
  'status': status,
  'priority': priority,
  'created_at': createdAt,
};
