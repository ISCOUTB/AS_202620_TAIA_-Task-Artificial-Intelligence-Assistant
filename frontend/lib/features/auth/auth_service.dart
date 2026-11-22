import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
import '../../core/bogota_time.dart';
import '../../core/token_storage.dart';

export '../../core/api_error.dart' show ApiException;

/// Versión de la política de datos que el backend exige al registrar
/// (RF-USR-10). Si el backend la cambia, hay que actualizarla aquí.
const String consentPolicyVersion = '2026-11-v1';

class UserProfile {
  const UserProfile({
    required this.id,
    required this.fullName,
    required this.email,
    required this.telegramLinked,
    this.createdAt,
    this.consentPolicyVersion,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
    id: json['id'] as String,
    fullName: json['full_name'] as String,
    email: json['email'] as String,
    telegramLinked: json['telegram_linked'] as bool? ?? false,
    createdAt: parseApiDateTimeOrNull(json['created_at']),
    consentPolicyVersion: json['consent_policy_version'] as String?,
  );

  final String id;
  final String fullName;
  final String email;
  final bool telegramLinked;

  /// Cuándo se creó la cuenta.
  final DateTime? createdAt;

  /// Versión de la política de datos aceptada al registrarse.
  final String? consentPolicyVersion;
}

class AuthService {
  AuthService({required this._dio, required this._tokens});

  factory AuthService.create() =>
      AuthService(dio: apiDio, tokens: appTokenStorage);

  final Dio _dio;
  final TokenStorage _tokens;

  Future<bool> hasSession() async => await _tokens.read() != null;

  /// POST /users. Sin `consent_accepted: true` y la versión vigente, el
  /// backend rechaza el registro.
  Future<void> register({
    required String fullName,
    required String email,
    required String password,
  }) => apiGuard(
    () => _dio.post<void>(
      '/users',
      data: {
        'full_name': fullName,
        'email': email,
        'password': password,
        'consent_accepted': true,
        'consent_policy_version': consentPolicyVersion,
      },
    ),
  );

  /// POST /users/login. Guarda el par de tokens si la respuesta es correcta.
  Future<void> login(String email, String password) => apiGuard(() async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/users/login',
      data: {'email': email, 'password': password},
    );
    final access = response.data?['access_token'] as String?;
    // Los servidores anteriores a la renovación de sesión no envían este campo.
    final refresh = response.data?['refresh_token'] as String?;
    if (access == null) {
      throw const ApiException('Respuesta inesperada del servidor.');
    }
    await _tokens.save(access: access, refresh: refresh);
  });

  /// GET /users/me.
  Future<UserProfile> me() => apiGuard(() async {
    final response = await _dio.get<Map<String, dynamic>>('/users/me');
    return UserProfile.fromJson(response.data!);
  });

  /// POST /users/logout invalida la sesión en el servidor (RF-USR-04); luego
  /// se borran los tokens locales aunque el servidor no responda.
  ///
  /// Si el token de acceso ya venció, el cliente lo renueva y repite la
  /// petición: así la sesión también se revoca en el servidor.
  Future<void> logout() async {
    try {
      await _dio.post<void>('/users/logout');
    } on DioException {
      // Se cierra la sesión local de todos modos.
    }
    await _tokens.clear();
  }
}

/// Instancia compartida por la app. Las pantallas aceptan un [AuthService]
/// opcional para poder probarlas con un servicio falso.
final AuthService authService = AuthService.create();