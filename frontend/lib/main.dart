import 'package:flutter/material.dart';

import 'splash/splash_screen.dart';
import 'theme/taia_colors.dart';

void main() {
  runApp(const TaiaApp());
}

class TaiaApp extends StatelessWidget {
  const TaiaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TAIA',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: TaiaColors.coral),
      ),
      home: const SplashScreen(),
    );
  }
}
