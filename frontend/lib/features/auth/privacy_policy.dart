import 'package:url_launcher/url_launcher.dart';

/// Política de tratamiento de datos personales que el estudiante acepta al
/// registrarse (RF-USR-10), publicada en el repositorio del proyecto.
const String privacyPolicyUrl =
    'https://github.com/ISCOUTB/AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant/blob/main/docs/politica_privacidad.md';

/// Abre [uri] en el navegador del teléfono.
Future<bool> openInBrowser(Uri uri) =>
    launchUrl(uri, mode: LaunchMode.externalApplication);
