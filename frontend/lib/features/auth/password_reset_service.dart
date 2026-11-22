import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';

/// Recuperación de contraseña con un código enviado al correo (RF-USR-08).
/// Las dos rutas son públicas (RT-01).
class PasswordResetService {
  PasswordResetService(this._dio);

  final Dio _dio;

  /// POST /users/password-reset. Responde igual exista o no la cuenta; `429`
  /// si el correo agotó sus 3 solicitudes del día (RNF-03).
  Future<void> request(String email) => apiGuard(
    () => _dio.post<void>('/users/password-reset', data: {'email': email}),
  );

  /// POST /users/password-reset/confirm. Un correo, código o vencimiento
  /// incorrecto responde el mismo `400`.
  Future<void> confirm({
    required String email,
    required String code,
    required String newPassword,
  }) => apiGuard(
    () => _dio.post<void>(
      '/users/password-reset/confirm',
      data: {'email': email, 'code': code, 'new_password': newPassword},
    ),
  );
}

final PasswordResetService passwordResetService = PasswordResetService(apiDio);
