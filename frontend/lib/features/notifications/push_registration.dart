import 'dart:async';

import 'package:dio/dio.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

import '../../core/api_client.dart';
import 'notifications_service.dart';

/// Registra el token FCM del dispositivo en la sesión actual (RF-NOT-01) y lo
/// vuelve a enviar si Firebase lo renueva. Al cerrar sesión el servidor lo
/// borra (RF-USR-04).
class PushRegistration {
  PushRegistration(
    this._dio, {
    required this.getToken,
    required this.onTokenRefresh,
    this.requestPermission,
    this.foregroundMessages,
  });

  final Dio _dio;
  final Future<String?> Function() getToken;
  final Stream<String> onTokenRefresh;

  /// En Android 13 o superior pide el permiso de notificaciones.
  final Future<void> Function()? requestPermission;

  /// Texto de las notificaciones que llegan con la app abierta. Android no las
  /// muestra solo en ese caso, así que la app las avisa ([onForegroundMessage]).
  final Stream<String>? foregroundMessages;

  /// Lo asigna la pantalla principal para mostrar el aviso.
  void Function(String message)? onForegroundMessage;

  StreamSubscription<String>? _subscription;
  StreamSubscription<String>? _foreground;

  /// Sin token o sin red, la app sigue funcionando: solo no habrá push y las
  /// notificaciones quedan en la bandeja (RF-NOT-04).
  Future<void> start() async {
    try {
      await requestPermission?.call();
      final token = await getToken();
      if (token != null) await _send(token);
    } catch (error) {
      debugPrint('push_registration_failed: $error');
    }
    _subscription ??= onTokenRefresh.listen(_send);
    _foreground ??= foregroundMessages?.listen((message) {
      // La bandeja ya tiene la notificación: la campana vuelve a contar.
      notifyInboxChanged();
      onForegroundMessage?.call(message);
    });
  }

  Future<void> stop() async {
    await _subscription?.cancel();
    await _foreground?.cancel();
    _subscription = null;
    _foreground = null;
  }

  Future<void> _send(String token) async {
    try {
      await _dio.put<void>('/users/me/fcm-token', data: {'fcm_token': token});
    } on DioException catch (error) {
      debugPrint('push_registration_failed: ${error.response?.statusCode}');
    }
  }
}

/// Solo Android tiene Firebase configurado (`firebase_options.dart`).
bool get pushSupported =>
    !kIsWeb &&
    defaultTargetPlatform == TargetPlatform.android &&
    Firebase.apps.isNotEmpty;

/// Registro con FirebaseMessaging, o null si la plataforma no tiene push.
PushRegistration? buildPushRegistration() {
  if (!pushSupported) return null;
  final messaging = FirebaseMessaging.instance;
  // El backend envía con `firebase_admin.messaging.Message(token=...)`, que
  // espera el token de registro. `register()` y `onRegistered` entregan otro
  // identificador (el FID), así que se usan getToken y onTokenRefresh.
  return PushRegistration(
    apiDio,
    // ignore: deprecated_member_use
    getToken: messaging.getToken,
    // ignore: deprecated_member_use
    onTokenRefresh: messaging.onTokenRefresh,
    requestPermission: () => messaging.requestPermission(),
    foregroundMessages: FirebaseMessaging.onMessage.map(
      (message) => message.notification?.body ?? '',
    ),
  );
}
