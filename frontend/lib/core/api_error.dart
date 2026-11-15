import 'package:dio/dio.dart';

/// Error de la API con un mensaje listo para mostrar al usuario.
class ApiException implements Exception {
  const ApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

/// Ejecuta una llamada a la API y traduce los errores de red o de la API a
/// [ApiException].
Future<T> apiGuard<T>(Future<T> Function() action) async {
  try {
    return await action();
  } on DioException catch (e) {
    throw ApiException(_messageFor(e));
  }
}

String _messageFor(DioException e) {
  final data = e.response?.data;
  // Errores del dominio: {"detail": "texto"}.
  if (data is Map && data['detail'] is String) {
    return data['detail'] as String;
  }
  if (e.type == DioExceptionType.connectionTimeout ||
      e.type == DioExceptionType.sendTimeout ||
      e.type == DioExceptionType.receiveTimeout ||
      e.type == DioExceptionType.connectionError) {
    return 'No se pudo conectar con el servidor. Revisa tu conexión.';
  }
  // 422 de validación de FastAPI: `detail` llega como lista.
  if (e.response?.statusCode == 422) {
    return 'Revisa los datos ingresados.';
  }
  return 'Ocurrió un error inesperado. Intenta de nuevo.';
}