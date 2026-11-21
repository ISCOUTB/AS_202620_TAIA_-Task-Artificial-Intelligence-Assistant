import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'splash/splash_screen.dart';
import 'theme/taia_colors.dart';
import 'welcome/welcome_screen.dart';

/// Permite navegar desde fuera de un widget (por ejemplo, al vencer la sesión).
final GlobalKey<NavigatorState> appNavigatorKey = GlobalKey<NavigatorState>();

void main() {
  // Si la sesión no se puede renovar, se vuelve a la bienvenida.
  sessionEvents.onExpired = () {
    appNavigatorKey.currentState?.pushAndRemoveUntil(
      MaterialPageRoute<void>(builder: (_) => const WelcomeScreen()),
      (route) => false,
    );
  };
  runApp(const TaiaApp());
}

class TaiaApp extends StatelessWidget {
  const TaiaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TAIA',
      navigatorKey: appNavigatorKey,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: TaiaColors.fieryRose),
      ),
      home: const SplashScreen(),
    );
  }
}