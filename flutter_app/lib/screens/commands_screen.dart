import 'package:flutter/material.dart';
import '../services/api_service.dart';

// ─── Modèles internes ────────────────────────────────────────────────────────

enum _Input { none, text, two }

class _Cmd {
  final String command;
  final String label;
  final String description;
  final IconData icon;
  final Color color;
  final _Input input;
  final String? hint1;
  final String? hint2;

  const _Cmd(
    this.command,
    this.label,
    this.description,
    this.icon,
    this.color, {
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

const _kBlue   = Color(0xFF7C9CF5);
const _kPurple = Color(0xFFB07CF5);
const _kGreen  = Color(0xFF7CF5A9);
const _kOrange = Color(0xFFF5A97C);
const _kPink   = Color(0xFFF57CAA);
const _kCyan   = Color(0xFF7CDDF5);
const _kYellow = Color(0xFFF5E17C);

const _sections = [
  _Section('IA', Icons.psychology_outlined, [
    _Cmd('/recall',      'Recall',           'Afficher la mémoire',         Icons.memory,        _kPurple),
    _Cmd('/remember',    'Remember',          'Mémoriser une information',    Icons.bookmark_add,  _kPurple,
         input: _Input.text, hint1: 'Info à mémoriser…'),
    _Cmd('/ai compact',  'Compacter',         'Résumer l\'historique',        Icons.compress,      _kBlue),
    _Cmd('/ai clear',    'Vider historique',  'Effacer la conversation',      Icons.delete_sweep,  _kBlue),
    _Cmd('/ai history',  'Historique',        'Voir la conversation en cours',Icons.history,       _kBlue),
  ]),
  _Section('Organisation', Icons.task_alt, [
    _Cmd('/note',        'Nouvelle note',     'Créer une note rapide',        Icons.note_add,      _kGreen,
         input: _Input.text, hint1: 'Contenu de la note…'),
    _Cmd('/note list',   'Lister les notes',  'Voir les 50 dernières notes',  Icons.list_alt,      _kGreen),
    _Cmd('/note export', 'Exporter vault',    'Exporter vers Obsidian',       Icons.upload_file,   _kGreen),
    _Cmd('/remind',      'Rappel',            'Créer un rappel minuté',       Icons.alarm_add,     _kOrange,
         input: _Input.two, hint1: 'Message du rappel…', hint2: 'Durée (10min, 2h, 30s…)'),
    _Cmd('/todo',        'Todo — listes',     'Voir toutes les listes',       Icons.checklist,     _kYellow),
    _Cmd('/todo new',    'Nouvelle liste',    'Créer une liste de tâches',    Icons.playlist_add,  _kYellow,
         input: _Input.text, hint1: 'Nom de la liste…'),
    _Cmd('/todo show',   'Voir une liste',    'Afficher une liste todo',      Icons.format_list_bulleted, _kYellow,
         input: _Input.text, hint1: 'Nom de la liste…'),
    _Cmd('/todo add',    'Ajouter une tâche', 'Ajouter à une liste',          Icons.add_task,      _kYellow,
         input: _Input.two, hint1: 'Nom de la liste…', hint2: 'Tâche à ajouter…'),
  ]),
  _Section('Info', Icons.explore_outlined, [
    _Cmd('/weather',     'Météo',             'Météo basée sur l\'IP',        Icons.cloud_outlined, _kCyan),
    _Cmd('/quote',       'Citation',          'Citation inspirante',          Icons.format_quote,   _kCyan),
    _Cmd('/localize',    'Localisation',      'Ma position géographique',     Icons.location_on_outlined, _kCyan),
    _Cmd('/crypto',      'Portfolio crypto',  'Résumé wallets + marché',      Icons.currency_bitcoin, _kOrange),
    _Cmd('/crypto price','Prix crypto',       'Prix + variation 24h',         Icons.show_chart,     _kOrange,
         input: _Input.text, hint1: 'Coin (btc, eth, sol…)'),
    _Cmd('/crypto news', 'Tendances',         'Tendances CoinGecko',          Icons.trending_up,    _kOrange),
  ]),
  _Section('Système', Icons.settings_applications_outlined, [
    _Cmd('/model',       'Modèles actifs',    'Voir les modèles configurés',  Icons.smart_toy_outlined, _kPink),
    _Cmd('/model list',  'Lister modèles',    'Tous les modèles disponibles', Icons.list,           _kPink),
    _Cmd('/tools',       'Outils',            'Statut des outils actifs',     Icons.construction_outlined, _kPink),
    _Cmd('/log',         'Journal',           'Dernières actions enregistrées',Icons.history_edu,   _kBlue),
    _Cmd('/help',        'Aide',              'Liste complète des commandes',  Icons.help_outline,   _kBlue),
    _Cmd('/skills',      'Skills',            'Skills IA actifs',             Icons.auto_awesome,   _kPurple),
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
      _showResult(cmd.label, '❌ ${e.message}');
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
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.5,
        minChildSize: 0.25,
        maxChildSize: 0.9,
        builder: (_, scroll) => Column(
          children: [
            const SizedBox(height: 8),
            Container(
              width: 40, height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.shade400,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close),
                    visualDensity: VisualDensity.compact,
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: SingleChildScrollView(
                controller: scroll,
                padding: const EdgeInsets.all(16),
                child: SelectableText(
                  text,
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 13, height: 1.5),
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
    return Scaffold(
      appBar: AppBar(
        title: const Text('Commandes'),
        bottom: _running
            ? const PreferredSize(
                preferredSize: Size.fromHeight(3),
                child: LinearProgressIndicator(),
              )
            : null,
      ),
      body: ListView.builder(
        padding: const EdgeInsets.only(bottom: 24),
        itemCount: _sections.fold<int>(0, (sum, s) => sum + 1 + s.commands.length),
        itemBuilder: (context, index) {
          int offset = 0;
          for (final section in _sections) {
            if (index == offset) return _SectionHeader(section);
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

class _SectionHeader extends StatelessWidget {
  final _Section section;
  const _SectionHeader(this.section, {super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 6),
      child: Row(
        children: [
          Icon(section.icon, size: 16, color: theme.colorScheme.primary),
          const SizedBox(width: 6),
          Text(
            section.title.toUpperCase(),
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.2,
            ),
          ),
        ],
      ),
    );
  }
}

class _CommandTile extends StatelessWidget {
  final _Cmd cmd;
  final VoidCallback? onTap;
  const _CommandTile({required this.cmd, this.onTap, super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final disabled = onTap == null;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
      child: Card(
        elevation: 0,
        color: theme.colorScheme.surfaceContainerLow,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            child: Row(
              children: [
                Container(
                  width: 40, height: 40,
                  decoration: BoxDecoration(
                    color: cmd.color.withOpacity(disabled ? 0.1 : 0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(
                    cmd.icon,
                    color: disabled ? cmd.color.withOpacity(0.4) : cmd.color,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        cmd.label,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: disabled ? theme.disabledColor : null,
                        ),
                      ),
                      Text(
                        cmd.description,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: disabled
                              ? theme.disabledColor
                              : theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                if (cmd.input != _Input.none)
                  Icon(
                    Icons.edit_outlined,
                    size: 15,
                    color: theme.colorScheme.onSurfaceVariant.withOpacity(disabled ? 0.3 : 0.6),
                  )
                else
                  Icon(
                    Icons.play_arrow_rounded,
                    size: 18,
                    color: cmd.color.withOpacity(disabled ? 0.3 : 0.8),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
