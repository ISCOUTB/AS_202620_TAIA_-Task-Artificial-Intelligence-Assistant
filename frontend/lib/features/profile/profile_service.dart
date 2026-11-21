import 'package:dio/dio.dart';

import '../../core/api_client.dart';
import '../../core/api_error.dart';

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
}

final ProfileService profileService = ProfileService(apiDio);