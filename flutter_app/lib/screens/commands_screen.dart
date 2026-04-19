import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/notion_section_label.dart';

// ─── Modèles internes ────────────────────────────────────────────────────────

enum _Input { none, text, two }

class _Cmd {
  final String command;
  final String label;
  final String description;
  final IconData icon;
  final _Input input;
  final String? hint1;
  final String? hint2;

  const _Cmd(
    this.command,
    this.label,
    this.description,
    this.icon, {
    this.input = _Input.none,
    this.hint1,
    this.hint2,
  });
}

class _Section {
  final String title;
  final IconData icon;
  final List<_Cmd> commands;
  const _Section(this.title, this.icon, this.commands);
}

// ─── Catalogue de commandes ──────────────────────────────────────────────────

const _sections = [
  _Section('IA', Icons.psychology_outlined, [
    _Cmd('/recall',      'Recall',           'Afficher la mémoire',          Icons.memory),
    _Cmd('/remember',    'Remember',          'Mémoriser une information',    Icons.bookmark_add,
         input: _Input.text, hint1: 'Info à mémoriser…'),
    _Cmd('/ai compact',  'Compacter',         'Résumer l\'historique',        Icons.compress),
    _Cmd('/ai clear',    'Vider historique',  'Effacer la conversation',      Icons.delete_sweep),
    _Cmd('/ai history',  'Historique',        'Voir la conversation en cours',Icons.history),
  ]),
  _Section('Organisation', Icons.task_alt, [
    _Cmd('/note',        'Nouvelle note',     'Créer une note rapide',        Icons.note_add,
         input: _Input.text, hint1: 'Contenu de la note…'),
    _Cmd('/note list',   'Lister les notes',  'Voir les 50 dernières notes',  Icons.list_alt),
    _Cmd('/note export', 'Exporter vault',    'Exporter vers Obsidian',       Icons.upload_file),
    _Cmd('/remind',      'Rappel',            'Créer un rappel minuté',       Icons.alarm_add,
         input: _Input.two, hint1: 'Message du rappel…', hint2: 'Durée (10min, 2h, 30s…)'),
    _Cmd('/todo',        'Todo — listes',     'Voir toutes les listes',       Icons.checklist),
    _Cmd('/todo new',    'Nouvelle liste',    'Créer une liste de tâches',    Icons.playlist_add,
         input: _Input.text, hint1: 'Nom de la liste…'),
    _Cmd('/todo show',   'Voir une liste',    'Afficher une liste todo',      Icons.format_list_bulleted,
         input: _Input.text, hint1: 'Nom de la liste…'),
    _Cmd('/todo add',    'Ajouter une tâche', 'Ajouter à une liste',          Icons.add_task,
         input: _Input.two, hint1: 'Nom de la liste…', hint2: 'Tâche à ajouter…'),
  ]),
  _Section('Info', Icons.explore_outlined, [
    _Cmd('/weather',     'Météo',             'Météo basée sur l\'IP',        Icons.cloud_outlined),
    _Cmd('/quote',       'Citation',          'Citation inspirante',          Icons.format_quote),
    _Cmd('/localize',    'Localisation',      'Ma position géographique',     Icons.location_on_outlined),
    _Cmd('/crypto',      'Portfolio crypto',  'Résumé wallets + marché',      Icons.currency_bitcoin),
    _Cmd('/crypto price','Prix crypto',       'Prix + variation 24h',         Icons.show_chart,
         input: _Input.text, hint1: 'Coin (btc, eth, sol…)'),
    _Cmd('/crypto news', 'Tendances',         'Tendances CoinGecko',          Icons.trending_up),
  ]),
  _Section('Système', Icons.settings_applications_outlined, [
    _Cmd('/model',       'Modèles actifs',    'Voir les modèles configurés',  Icons.smart_toy_outlined),
    _Cmd('/model list',  'Lister modèles',    'Tous les modèles disponibles', Icons.list),
    _Cmd('/tools',       'Outils',            'Statut des outils actifs',     Icons.construction_outlined),
    _Cmd('/log',         'Journal',           'Dernières actions enregistrées',Icons.history_edu),
    _Cmd('/help',        'Aide',              'Liste complète des commandes',  Icons.help_outline),
    _Cmd('/skills',      'Skills',            'Skills IA actifs',             Icons.auto_awesome),
  ]),
];

// ─── Écran ───────────────────────────────────────────────────────────────────

class CommandsScreen extends StatefulWidget {
  const CommandsScreen({super.key});

  @override
  State<CommandsScreen> createState() => _CommandsScreenState();
}

class _CommandsScreenState extends State<CommandsScreen> {
  final _api = ApiService();
  bool _running = false;

  Future<void> _run(_Cmd cmd) async {
    String finalCommand;

    if (cmd.input == _Input.none) {
      finalCommand = cmd.command;
    } else if (cmd.input == _Input.text) {
      final text = await _promptOne(cmd.label, cmd.hint1 ?? '');
      if (text == null) return;
      finalCommand = '${cmd.command} $text';
    } else {
      final pair = await _promptTwo(cmd.label, cmd.hint1 ?? '', cmd.hint2 ?? '');
      if (pair == null) return;
      if (cmd.command == '/remind') {
        finalCommand = '/remind ${pair.$1}, ${pair.$2}';
      } else {
        finalCommand = '${cmd.command} ${pair.$1} ${pair.$2}';
      }
    }

    setState(() => _running = true);
    try {
      final result = await _api.sendMessage(finalCommand);
      if (!mounted) return;
      _showResult(cmd.label, result.reply);
    } on ApiException catch (e) {
      if (!mounted) return;
      _showResult(cmd.label, '⚠ ${e.message}');
    } finally {
      if (mounted) setState(() => _running = false);
    }
  }

  Future<String?> _promptOne(String title, String hint) async {
    final ctrl = TextEditingController();
    try {
      return await showDialog<String>(
        context: context,
        builder: (_) => AlertDialog(
          title: Text(title),
          content: TextField(
            controller: ctrl,
            autofocus: true,
            decoration: InputDecoration(hintText: hint),
            textInputAction: TextInputAction.done,
            onSubmitted: (v) => Navigator.pop(context, v.trim()),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Annuler')),
            FilledButton(
              onPressed: () => Navigator.pop(context, ctrl.text.trim()),
              child: const Text('Lancer'),
            ),
          ],
        ),
      );
    } finally {
      ctrl.dispose();
    }
  }

  Future<(String, String)?> _promptTwo(String title, String hint1, String hint2) async {
    final c1 = TextEditingController();
    final c2 = TextEditingController();
    try {
      return await showDialog<(String, String)>(
        context: context,
        builder: (_) => AlertDialog(
          title: Text(title),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: c1,
                autofocus: true,
                decoration: InputDecoration(hintText: hint1),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: c2,
                decoration: InputDecoration(hintText: hint2),
                textInputAction: TextInputAction.done,
                onSubmitted: (_) => Navigator.pop(context, (c1.text.trim(), c2.text.trim())),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Annuler')),
            FilledButton(
              onPressed: () => Navigator.pop(context, (c1.text.trim(), c2.text.trim())),
              child: const Text('Lancer'),
            ),
          ],
        ),
      );
    } finally {
      c1.dispose();
      c2.dispose();
    }
  }

  void _showResult(String title, String text) {
    final theme = Theme.of(context);
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.5,
        minChildSize: 0.25,
        maxChildSize: 0.9,
        builder: (_, scroll) => Column(
          children: [
            const SizedBox(height: 10),
            Container(
              width: 36, height: 4,
              decoration: BoxDecoration(
                color: theme.colorScheme.outlineVariant,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 8, 8),
              child: Row(
                children: [
                  Text(title,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                        color: theme.colorScheme.onSurface,
                      )),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close, size: 18),
                    visualDensity: VisualDensity.compact,
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),
            Divider(height: 1, color: theme.colorScheme.outline),
            Expanded(
              child: SingleChildScrollView(
                controller: scroll,
                padding: const EdgeInsets.all(16),
                child: SelectableText(
                  text,
                  style: TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 13,
                    height: 1.6,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Commandes'),
        bottom: _running
            ? PreferredSize(
                preferredSize: const Size.fromHeight(2),
                child: LinearProgressIndicator(
                  minHeight: 2,
                  color: theme.colorScheme.primary,
                  backgroundColor: Colors.transparent,
                ),
              )
            : notionAppBarDivider(context),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.only(bottom: 24),
        itemCount: _sections.fold<int>(0, (sum, s) => sum + 1 + s.commands.length),
        itemBuilder: (context, index) {
          int offset = 0;
          for (final section in _sections) {
            if (index == offset) {
              return Padding(
                padding: const EdgeInsets.fromLTRB(16, 20, 16, 6),
                child: NotionSectionLabel(section.title, section.icon),
              );
            }
            offset++;
            final cmdIndex = index - offset;
            if (cmdIndex < section.commands.length) {
              return _CommandTile(
                cmd: section.commands[cmdIndex],
                onTap: _running ? null : () => _run(section.commands[cmdIndex]),
              );
            }
            offset += section.commands.length;
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }
}

// ─── Widgets ─────────────────────────────────────────────────────────────────

class _CommandTile extends StatelessWidget {
  final _Cmd cmd;
  final VoidCallback? onTap;
  const _CommandTile({required this.cmd, this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme    = Theme.of(context);
    final disabled = onTap == null;
    final iconColor = disabled
        ? theme.colorScheme.onSurfaceVariant.withValues(alpha: 0.4)
        : theme.colorScheme.onSurfaceVariant;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 1),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(8),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
            child: Row(
              children: [
                Container(
                  width: 32, height: 32,
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surfaceContainerLow,
                    borderRadius: BorderRadius.circular(7),
                    border: Border.all(color: theme.colorScheme.outline),
                  ),
                  child: Icon(cmd.icon, color: iconColor, size: 16),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        cmd.label,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w500,
                          fontSize: 14,
                          color: disabled
                              ? theme.colorScheme.onSurfaceVariant.withValues(alpha: 0.5)
                              : theme.colorScheme.onSurface,
                        ),
                      ),
                      Text(
                        cmd.description,
                        style: TextStyle(
                          fontSize: 12,
                          color: disabled
                              ? theme.colorScheme.onSurfaceVariant.withValues(alpha: 0.4)
                              : theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Icon(
                  cmd.input != _Input.none
                      ? Icons.chevron_right
                      : Icons.play_arrow_rounded,
                  size: 16,
                  color: theme.colorScheme.onSurfaceVariant.withValues(alpha: disabled ? 0.3 : 0.5),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
