import 'package:flutter/material.dart';

/// Uppercase section label with leading icon — shared across screens.
class NotionSectionLabel extends StatelessWidget {
  final String label;
  final IconData icon;

  const NotionSectionLabel(this.label, this.icon, {super.key});

  @override
  Widget build(BuildContext context) {
    final subtle = Theme.of(context).colorScheme.onSurfaceVariant;
    return Row(
      children: [
        Icon(icon, size: 13, color: subtle),
        const SizedBox(width: 6),
        Text(
          label.toUpperCase(),
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.8,
            color: subtle,
          ),
        ),
      ],
    );
  }
}
