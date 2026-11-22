import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../mascot/mascot_expression.dart';
import '../../../mascot/taia_mascot.dart';
import '../../../theme/taia_colors.dart';
import '../../auth/auth_service.dart';
import '../../auth/auth_shell.dart';
import '../profile_service.dart';

/// Abre el enlace en la app de Telegram.
Future<bool> _openExternally(Uri uri) =>
    launchUrl(uri, mode: LaunchMode.externalApplication);

/// Hoja para vincular la cuenta con Telegram (RF-TEL-01). Devuelve true si al
/// final la cuenta quedó vinculada. [openLink] reemplaza la apertura del
/// enlace en las pruebas.
Future<bool?> showTelegramSheet(
  BuildContext context, {
  required ProfileService service,
  required Future<bool> Function() onCheckLinked,
  Future<bool> Function(Uri uri) openLink = _openExternally,
}) {
  return showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    backgroundColor: TaiaColors.ivoryMist,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (context) => _TelegramSheet(
      service: service,
      onCheckLinked: onCheckLinked,
      openLink: openLink,
    ),
  );
}

class _TelegramSheet extends StatefulWidget {
  const _TelegramSheet({
    required this.service,
    required this.onCheckLinked,
    required this.openLink,
  });

  final ProfileService service;
  final Future<bool> Function() onCheckLinked;
  final Future<bool> Function(Uri uri) openLink;

  @override
  State<_TelegramSheet> createState() => _TelegramSheetState();
}

class _TelegramSheetState extends State<_TelegramSheet> {
  TelegramLink? _link;
  bool _busy = false;
  String? _message;
  MascotExpression _expression = MascotExpression.wink;

  Future<void> _createAndOpen() async {
    setState(() {
      _busy = true;
      _message = null;
      _expression = MascotExpression.thinking;
    });
    try {
      final link = await widget.service.createTelegramLink();
      if (!mounted) return;
      setState(() => _link = link);
      await _open(link);
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _message = e.message;
        _expression = MascotExpression.surprised;
      });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _open(TelegramLink link) async {
    try {
      final opened = await widget.openLink(Uri.parse(link.deepLink));
      if (!mounted) return;
      setState(() {
        _expression = MascotExpression.happy;
        if (!opened) {
          _message = 'No pude abrir Telegram. Copia el enlace y ábrelo a mano.';
        }
      });
    } on Exception {
      if (!mounted) return;
      setState(() {
        _expression = MascotExpression.surprised;
        _message = 'No pude abrir Telegram. Copia el enlace y ábrelo a mano.';
      });
    }
  }

  Future<void> _copy(TelegramLink link) async {
    await Clipboard.setData(ClipboardData(text: link.deepLink));
    if (!mounted) return;
    setState(() => _message = 'Enlace copiado. Ábrelo en Telegram.');
  }

  Future<void> _check() async {
    setState(() {
      _busy = true;
      _message = null;
      _expression = MascotExpression.thinking;
    });
    final linked = await widget.onCheckLinked();
    if (!mounted) return;
    if (linked) {
      Navigator.of(context).pop(true);
      return;
    }
    setState(() {
      _busy = false;
      _expression = MascotExpression.surprised;
      _message =
          'Todavía no veo el vínculo. En Telegram pulsa «Iniciar» (Start) en '
          'el chat con el bot y vuelve a intentarlo.';
    });
  }

  @override
  Widget build(BuildContext context) {
    final link = _link;
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'INTEGRACIÓN',
                      style: TextStyle(
                        color: TaiaColors.fieryRose,
                        fontSize: 12,
                        letterSpacing: 1.6,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    SizedBox(height: 6),
                    Text(
                      'Vincula tu Telegram',
                      style: TextStyle(
                        color: taiaInk,
                        fontSize: 28,
                        height: 1.1,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Container(
                width: 74,
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: TaiaColors.fieryRose,
                  borderRadius: BorderRadius.circular(22),
                ),
                child: TaiaMascot(motion: 0.5, expression: _expression),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            link == null
                ? 'Con Telegram podrás hablar con TAIA desde el chat, sin '
                      'abrir la app.'
                : 'Te abrí Telegram. Sigue estos pasos:',
            style: TextStyle(color: taiaInk.withValues(alpha: 0.8)),
          ),
          const SizedBox(height: 14),
          if (link == null)
            const _Steps(
              steps: [
                'Genero un enlace personal que dura unos 10 minutos.',
                'Se abre el chat con el bot de TAIA en Telegram.',
                'Pulsas «Iniciar» y listo: tu cuenta queda vinculada.',
              ],
            )
          else
            const _Steps(
              steps: [
                'En el chat con el bot, pulsa «Iniciar» (Start).',
                'Vuelve a TAIA.',
                'Toca «Ya lo vinculé» para confirmar.',
              ],
            ),
          if (_message != null) ...[
            const SizedBox(height: 14),
            Text(
              _message!,
              style: const TextStyle(
                color: taiaInk,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
          const SizedBox(height: 20),
          if (link == null)
            AuthSubmitButton(
              label: 'Generar enlace y abrir Telegram',
              loading: _busy,
              onPressed: _createAndOpen,
            )
          else ...[
            AuthSubmitButton(
              label: 'Ya lo vinculé',
              loading: _busy,
              onPressed: _check,
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextButton.icon(
                    style: TextButton.styleFrom(
                      foregroundColor: TaiaColors.fieryRose,
                    ),
                    onPressed: _busy ? null : () => _open(link),
                    icon: const Icon(Icons.open_in_new, size: 18),
                    label: const Text('Abrir otra vez'),
                  ),
                ),
                Expanded(
                  child: TextButton.icon(
                    style: TextButton.styleFrom(
                      foregroundColor: TaiaColors.fieryRose,
                    ),
                    onPressed: _busy ? null : () => _copy(link),
                    icon: const Icon(Icons.copy, size: 18),
                    label: const Text('Copiar enlace'),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _Steps extends StatelessWidget {
  const _Steps({required this.steps});

  final List<String> steps;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        children: [
          for (var i = 0; i < steps.length; i++)
            Padding(
              padding: EdgeInsets.only(top: i == 0 ? 0 : 10),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 24,
                    height: 24,
                    alignment: Alignment.center,
                    decoration: const BoxDecoration(
                      color: TaiaColors.fieryRose,
                      shape: BoxShape.circle,
                    ),
                    child: Text(
                      '${i + 1}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      steps[i],
                      style: const TextStyle(color: taiaInk, fontSize: 14),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
