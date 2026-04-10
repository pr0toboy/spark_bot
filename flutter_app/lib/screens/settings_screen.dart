import 'package:flutter/material.dart';
import '../models/skill.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _api = ApiService();
  Map<String, dynamic> _settings = {};
  Map<String, dynamic> _models = {};
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
        _api.getModels(),
        _api.getTools(),
        _api.getSkills(),
        _api.getPresets(),
      ]);
      setState(() {
        _settings = results[0] as Map<String, dynamic>;
        _models = results[1] as Map<String, dynamic>;
        _tools = (results[2] as List).cast<Map<String, dynamic>>();
        _skills = (results[3] as List<Skill>);
        _presets = (results[4] as List<Skill>);
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
        final key = provider == 'anthropic' ? 'anthropic_api_key' : 'groq_api_key';
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
          title: Text(preset != null ? 'Ajouter le preset ${preset.name}' : 'Nouveau skill'),
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

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));

    return Scaffold(
      appBar: AppBar(title: const Text('Paramètres')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _section('Clés API', [
            _keyTile('Anthropic', _settings['has_anthropic_key'] == true),
            _keyTile('Groq', _settings['has_groq_key'] == true),
          ]),
          _section('Outils', [
            for (final tool in _tools)
              SwitchListTile(
                title: Text(tool['name'] as String),
                subtitle: Text(tool['description'] as String),
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
              const ListTile(title: Text('Aucun skill actif.')),
            for (final skill in _skills)
              ListTile(
                title: Text(skill.name),
                subtitle: Text(skill.instructions, maxLines: 1, overflow: TextOverflow.ellipsis),
                trailing: IconButton(
                  icon: const Icon(Icons.delete_outline),
                  onPressed: () async {
                    await _api.deleteSkill(skill.name);
                    await _load();
                  },
                ),
              ),
            ListTile(
              leading: const Icon(Icons.add),
              title: const Text('Ajouter un skill'),
              onTap: () => _addSkill(),
            ),
          ]),
          _section('Presets disponibles', [
            for (final preset in _presets)
              ListTile(
                title: Text(preset.name),
                subtitle: Text(preset.instructions.split('\n').first, maxLines: 1, overflow: TextOverflow.ellipsis),
                trailing: _skills.any((s) => s.name == preset.name)
                    ? const Chip(label: Text('actif'))
                    : FilledButton.tonal(
                        onPressed: () => _addSkill(preset: preset),
                        child: const Text('Ajouter'),
                      ),
              ),
          ]),
        ],
      ),
    );
  }

  Widget _section(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        ),
        Card(child: Column(children: children)),
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _keyTile(String provider, bool hasKey) {
    return ListTile(
      title: Text('$provider ${hasKey ? '✅' : '⭕'}'),
      subtitle: Text(hasKey ? 'Clé enregistrée' : 'Aucune clé'),
      trailing: TextButton(
        onPressed: () => _setApiKey(provider.toLowerCase()),
        child: Text(hasKey ? 'Modifier' : 'Ajouter'),
      ),
    );
  }
}
