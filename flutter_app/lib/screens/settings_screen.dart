import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../theme.dart';
import '../models/skill.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _api = ApiService();
  bool _backupBusy = false;
  Map<String, dynamic> _settings = {};
  List<Map<String, dynamic>> _tools = [];
  List<Skill> _skills = [];
  List<Skill> _presets = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final results = await Future.wait([
        _api.getSettings(),
        _api.getTools(),
        _api.getSkills(),
        _api.getPresets(),
      ]);
      setState(() {
        _settings = results[0] as Map<String, dynamic>;
        _tools = (results[1] as List).cast<Map<String, dynamic>>();
        _skills = (results[2] as List<Skill>);
        _presets = (results[3] as List<Skill>);
      });
    } catch (e) {
      _showError(e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  void _showError(String msg) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  Future<void> _setApiKey(String provider) async {
    final controller = TextEditingController();
    try {
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          title: Text('Clé API $provider'),
          content: TextField(
            controller: controller,
            obscureText: true,
            decoration: const InputDecoration(hintText: 'sk-…'),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
            FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Enregistrer')),
          ],
        ),
      );
      if (confirmed != true || controller.text.trim().isEmpty) return;
      try {
        final key = provider == 'anthropic'
            ? 'anthropic_api_key'
            : provider == 'groq'
                ? 'groq_api_key'
                : 'glm_api_key';
        await _api.updateSettings({key: controller.text.trim()});
        await _load();
      } catch (e) {
        _showError(e.toString());
      }
    } finally {
      controller.dispose();
    }
  }

  Future<void> _addSkill({Skill? preset}) async {
    final nameCtrl = TextEditingController(text: preset?.name ?? '');
    final instrCtrl = TextEditingController(text: preset?.instructions ?? '');
    try {
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          title: Text(preset != null ? 'Ajouter ${preset.name}' : 'Nouveau skill'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (preset == null)
                TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: 'Nom')),
              const SizedBox(height: 8),
              TextField(
                controller: instrCtrl,
                maxLines: 5,
                decoration: const InputDecoration(labelText: 'Instructions'),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
            FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Ajouter')),
          ],
        ),
      );
      if (confirmed != true) return;
      try {
        await _api.upsertSkill(nameCtrl.text.trim(), instrCtrl.text.trim());
        await _load();
      } catch (e) {
        _showError(e.toString());
      }
    } finally {
      nameCtrl.dispose();
      instrCtrl.dispose();
    }
  }

  Future<void> _setServerUrl() async {
    final controller = TextEditingController(text: _api.baseUrl);
    try {
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text('URL du serveur'),
          content: TextField(
            controller: controller,
            keyboardType: TextInputType.url,
            decoration: const InputDecoration(hintText: 'http://192.168.x.x:8000'),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
            FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Enregistrer')),
          ],
        ),
      );
      if (confirmed != true || controller.text.trim().isEmpty) return;
      await _api.setBaseUrl(controller.text.trim());
      await _load();
    } finally {
      controller.dispose();
    }
  }

  Future<void> _exportBackup() async {
    if (_backupBusy) return;
    setState(() => _backupBusy = true);
    try {
      final bytes = await _api.exportBackup();
      final dir = await getTemporaryDirectory();
      final now = DateTime.now();
      final name = 'spark_backup_${now.year}-'
          '${now.month.toString().padLeft(2, '0')}-'
          '${now.day.toString().padLeft(2, '0')}.json';
      final file = File('${dir.path}/$name');
      await file.writeAsBytes(bytes);
      await Share.shareXFiles([XFile(file.path)], subject: 'Sauvegarde Spark');
    } catch (e) {
      if (mounted) _showError(e.toString());
    } finally {
      if (mounted) setState(() => _backupBusy = false);
    }
  }

  Future<void> _importBackup() async {
    if (_backupBusy) return;
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['json'],
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;
    final bytes = result.files.first.bytes;
    if (bytes == null) return;
    if (!mounted) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Importer la sauvegarde'),
        content: const Text(
          'Cette opération remplace toutes les données actuelles (notes, habitudes, agents, crypto).\n\nContinuer ?',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Importer')),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => _backupBusy = true);
    try {
      final data = await _api.importBackup(bytes);
      final imp = data['imported'] as Map<String, dynamic>;
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(
            'Import réussi — ${imp['notes']} notes · ${imp['habits']} habitudes · '
            '${imp['agents']} agents · ${imp['skills']} skills',
          ),
        ));
      }
    } catch (e) {
      if (mounted) _showError(e.toString());
    } finally {
      if (mounted) setState(() => _backupBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return Scaffold(
      appBar: AppBar(
        title: const Text('Paramètres'),
        bottom: notionAppBarDivider(context),
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: 8),
        children: [
          _section('Connexion', [
            _row(
              title: 'Serveur',
              subtitle: _api.baseUrl,
              trailing: _actionBtn('Modifier', _setServerUrl),
            ),
          ]),
          _section('Clés API', [
            _keyRow('Anthropic', _settings['has_anthropic_key'] == true),
            _keyRow('Groq', _settings['has_groq_key'] == true),
            _keyRow('GLM', _settings['has_glm_key'] == true),
          ]),
          _section('Outils', [
            for (final tool in _tools)
              _switchRow(
                title: tool['name'] as String,
                subtitle: tool['description'] as String,
                value: tool['enabled'] as bool,
                onChanged: (val) async {
                  try {
                    await _api.setTool(tool['name'] as String, val);
                    await _load();
                  } catch (e) {
                    _showError(e.toString());
                  }
                },
              ),
          ]),
          _section('Skills actifs', [
            if (_skills.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Text('Aucun skill actif.',
                    style: TextStyle(fontSize: 14,
                        color: Theme.of(context).colorScheme.onSurfaceVariant)),
              ),
            for (final skill in _skills)
              _row(
                title: skill.name,
                subtitle: skill.instructions,
                maxSubtitleLines: 1,
                trailing: IconButton(
                  icon: Icon(Icons.delete_outline, size: 18,
                      color: theme.colorScheme.onSurfaceVariant),
                  visualDensity: VisualDensity.compact,
                  onPressed: () async {
                    await _api.deleteSkill(skill.name);
                    await _load();
                  },
                ),
              ),
            _row(
              title: 'Ajouter un skill',
              leading: Icon(Icons.add, size: 18, color: theme.colorScheme.onSurfaceVariant),
              onTap: () => _addSkill(),
            ),
          ]),
          _section('Presets disponibles', [
            for (final preset in _presets)
              _row(
                title: preset.name,
                subtitle: preset.instructions.split('\n').first,
                maxSubtitleLines: 1,
                trailing: _skills.any((s) => s.name == preset.name)
                    ? Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: kNotionGreen.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(5),
                          border: Border.all(color: kNotionGreen.withValues(alpha: 0.3)),
                        ),
                        child: const Text('actif',
                            style: TextStyle(
                              fontSize: 11,
                              color: kNotionGreen,
                              fontWeight: FontWeight.w500,
                            )),
                      )
                    : _actionBtn('Ajouter', () => _addSkill(preset: preset)),
              ),
          ]),
          _section('Sauvegarde', [
            _row(
              title: 'Exporter',
              subtitle: 'Télécharger toutes les données Spark dans un fichier JSON',
              leading: Icon(Icons.upload_outlined, size: 18,
                  color: theme.colorScheme.onSurfaceVariant),
              trailing: _backupBusy
                  ? const SizedBox(width: 20, height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : _actionBtn('Exporter', _exportBackup),
            ),
            _row(
              title: 'Importer',
              subtitle: 'Restaurer depuis un fichier spark_backup_*.json',
              leading: Icon(Icons.download_outlined, size: 18,
                  color: theme.colorScheme.onSurfaceVariant),
              trailing: _backupBusy
                  ? const SizedBox(width: 20, height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : _actionBtn('Importer', _importBackup),
            ),
          ]),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _section(String title, List<Widget> rows) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 6),
          child: Text(
            title.toUpperCase(),
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.8,
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Card(
            child: Column(
              children: [
                for (int i = 0; i < rows.length; i++) ...[
                  rows[i],
                  if (i < rows.length - 1)
                    Divider(height: 1, indent: 16, color: theme.colorScheme.outline),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _row({
    required String title,
    String? subtitle,
    int maxSubtitleLines = 2,
    Widget? trailing,
    Widget? leading,
    VoidCallback? onTap,
  }) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            if (leading != null) ...[leading, const SizedBox(width: 10)],
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: TextStyle(
                        fontSize: 14,
                        color: theme.colorScheme.onSurface,
                      )),
                  if (subtitle != null && subtitle.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      maxLines: maxSubtitleLines,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 12,
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            if (trailing != null) ...[const SizedBox(width: 8), trailing],
          ],
        ),
      ),
    );
  }

  Widget _switchRow({
    required String title,
    required String subtitle,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: TextStyle(fontSize: 14, color: theme.colorScheme.onSurface)),
                const SizedBox(height: 2),
                Text(subtitle,
                    style: TextStyle(
                      fontSize: 12,
                      color: theme.colorScheme.onSurfaceVariant,
                    )),
              ],
            ),
          ),
          Switch(value: value, onChanged: onChanged),
        ],
      ),
    );
  }

  Widget _keyRow(String provider, bool hasKey) {
    return _row(
      title: provider,
      subtitle: hasKey ? 'Clé enregistrée' : 'Aucune clé',
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8, height: 8,
            decoration: BoxDecoration(
              color: hasKey ? kNotionGreen : Theme.of(context).colorScheme.outline,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 10),
          _actionBtn(hasKey ? 'Modifier' : 'Ajouter',
              () => _setApiKey(provider.toLowerCase())),
        ],
      ),
    );
  }

  Widget _actionBtn(String label, VoidCallback onTap) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(5),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: theme.colorScheme.surfaceContainerLow,
          borderRadius: BorderRadius.circular(5),
          border: Border.all(color: theme.colorScheme.outline),
        ),
        child: Text(label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: theme.colorScheme.onSurface,
            )),
      ),
    );
  }
}
