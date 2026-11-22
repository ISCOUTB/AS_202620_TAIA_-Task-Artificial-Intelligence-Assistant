import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';
import '../auth/auth_service.dart';

/// Enlace temporal para vincular la cuenta con el bot de Telegram.
class TelegramLink {
  const TelegramLink({required this.deepLink});

  final String deepLink;
}

class ProfileService {
  ProfileService(this._dio);

  final Dio _dio;

  /// POST /users/me/telegram/link. Responde 409 si la cuenta ya está
  /// vinculada. El enlace dura unos 10 minutos.
  Future<TelegramLink> createTelegramLink() => apiGuard(() async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/users/me/telegram/link',
    );
    return TelegramLink(
      deepLink: response.data!['telegram_deep_link'] as String,
    );
  });

  /// PATCH /users/me (RF-USR-06). Cambiar el correo exige [currentPassword].
  Future<UserProfile> updateProfile({
    String? fullName,
    String? email,
    String? currentPassword,
  }) => apiGuard(() async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/users/me',
      data: {
        'full_name': ?fullName,
        'email': ?email,
        'current_password': ?currentPassword,
      },
    );
    return UserProfile.fromJson(response.data!);
  });

  /// PUT /users/me/password (RF-USR-07). Cierra las demás sesiones.
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) => apiGuard(
    () => _dio.put<void>(
      '/users/me/password',
      data: {'current_password': currentPassword, 'new_password': newPassword},
    ),
  );

  /// POST /users/me/deactivate (RF-USR-09). Revoca todas las sesiones.
  Future<void> deactivate(String currentPassword) => apiGuard(
    () => _dio.post<void>(
      '/users/me/deactivate',
      data: {'current_password': currentPassword},
    ),
  );

  /// DELETE /users/me/telegram (RF-TEL-03).
  Future<void> unlinkTelegram() =>
      apiGuard(() => _dio.delete<void>('/users/me/telegram'));
}

final ProfileService profileService = ProfileService(apiDio);
