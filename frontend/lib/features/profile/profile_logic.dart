/// Iniciales para el avatar: "Valeria Ríos Pérez" → "VR".
String initialsOf(String fullName) {
  final words = fullName
      .trim()
      .split(RegExp(r'\s+'))
      .where((w) => w.isNotEmpty)
      .toList();
  if (words.isEmpty) return '?';
  final first = words.first[0];
  final second = words.length > 1 ? words[1][0] : '';
  return (first + second).toUpperCase();
}
