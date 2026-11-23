import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';

import '../theme/taia_colors.dart';
import 'motion.dart';

/// Esqueleto de carga con brillo (RNF-14): bloques con la forma de lo que va a
/// aparecer, en lugar de un círculo girando. Sin brillo si se reduce el
/// movimiento.
class SkeletonList extends StatelessWidget {
  const SkeletonList({super.key, this.heights = const [56, 150, 96, 96, 96]});

  /// Alto de cada bloque, de arriba abajo.
  final List<double> heights;

  @override
  Widget build(BuildContext context) {
    final blocks = ListView(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 24),
      physics: const NeverScrollableScrollPhysics(),
      children: [
        for (final height in heights) ...[
          Container(
            height: height,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
            ),
          ),
          const SizedBox(height: 14),
        ],
      ],
    );
    return Semantics(
      label: 'Cargando',
      child: reduceMotion(context)
          ? Opacity(opacity: 0.6, child: blocks)
          : Shimmer.fromColors(
              baseColor: TaiaColors.softPeach.withValues(alpha: 0.55),
              highlightColor: Colors.white,
              period: const Duration(milliseconds: 1200),
              child: blocks,
            ),
    );
  }
}
