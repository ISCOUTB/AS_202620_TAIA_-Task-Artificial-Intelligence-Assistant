import 'package:dio/dio.dart';

import 'token_storage.dart';

/// URL base de la API. Por defecto apunta al despliegue; para probar contra un
/// backend local se sobrescribe al ejecutar:
///
///     flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
///
/// (10.0.2.2 es el `localhost` de tu PC visto desde el emulador de Android.)
const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'https://taia-sistema.iscoutb.dev',
);

/// Avisa a la app cuando la sesión ya no se puede renovar, para que vuelva a la
/// bienvenida. Lo conecta `main.dart`.
class SessionEvents {
  void Function()? onExpired;
}

final SessionEvents sessionEvents = SessionEvents();

const _retriedKey = 'retriedAfterRefresh';

/// Crea el cliente HTTP.
///
/// - Adjunta `Authorization: Bearer <token>` en cada petición.
/// - Si la API responde 401, renueva el par de tokens con `/users/refresh` y
///   repite la petición una vez. Si la renovación es rechazada, borra la
///   sesión y avisa con [sessionEvents].
///
/// [adapter] reemplaza la red en las pruebas.
Dio buildDio(TokenStorage tokens, {HttpClientAdapter? adapter}) {
  final dio = Dio(
    BaseOptions(
      baseUrl: apiBaseUrl,
      connectTimeout: const Duration(seconds: 15),
      // El asistente de IA puede tardar en responder.
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Accept': 'application/json'},
    ),
  );
  if (adapter != null) dio.httpClientAdapter = adapter;
  final refresher = _TokenRefresher(tokens, adapter);

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await tokens.read();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        final request = error.requestOptions;
        final isAuthCall =
            request.path == '/users/login' || request.path == '/users/refresh';
        if (error.response?.statusCode != 401 ||
            isAuthCall ||
            request.extra[_retriedKey] == true) {
          handler.next(error);
          return;
        }

        final String? access;
        try {
          access = await refresher.refresh();
        } on DioException {
          // Sin red no se cierra la sesión: se devuelve el error original.
          handler.next(error);
          return;
        }
        if (access == null) {
          sessionEvents.onExpired?.call();
          handler.next(error);
          return;
        }

        request.extra[_retriedKey] = true;
        request.headers['Authorization'] = 'Bearer $access';
        try {
          handler.resolve(await dio.fetch<dynamic>(request));
        } on DioException catch (retryError) {
          handler.next(retryError);
        }
      },
    ),
  );

  return dio;
}

/// Renueva los tokens. El token de renovación se invalida al usarlo, así que
/// varias peticiones que fallen a la vez comparten una sola renovación.
class _TokenRefresher {
  _TokenRefresher(this._tokens, HttpClientAdapter? adapter)
    : _bare = Dio(
        BaseOptions(
          baseUrl: apiBaseUrl,
          connectTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 30),
        ),
      ) {
    if (adapter != null) _bare.httpClientAdapter = adapter;
  }

  final TokenStorage _tokens;

  // Cliente sin interceptores, para que renovar no dispare otra renovación.
  final Dio _bare;

  Future<String?>? _inFlight;

  /// Devuelve el nuevo token de acceso, o null si la sesión ya no es válida.
  /// Lanza [DioException] si falla por red (la sesión sigue guardada).
  Future<String?> refresh() =>
      _inFlight ??= _doRefresh().whenComplete(() => _inFlight = null);

  Future<String?> _doRefresh() async {
    final refreshToken = await _tokens.readRefresh();
    if (refreshToken == null) return null;
    try {
      final response = await _bare.post<Map<String, dynamic>>(
        '/users/refresh',
        data: {'refresh_token': refreshToken},
      );
      final access = response.data?['access_token'] as String?;
      final refresh = response.data?['refresh_token'] as String?;
      if (access == null || refresh == null) {
        await _tokens.clear();
        return null;
      }
      await _tokens.save(access: access, refresh: refresh);
      return access;
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        await _tokens.clear();
        return null;
      }
      rethrow;
    }
  }
}

/// Almacén de tokens y cliente HTTP únicos de la app. Todos los servicios usan
/// este mismo [apiDio]: así comparten una sola renovación de sesión.
final TokenStorage appTokenStorage = TokenStorage();
final Dio apiDio = buildDio(appTokenStorage);