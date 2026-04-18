import 'package:flutter/material.dart';
import '../models/agent.dart';
import '../services/api_service.dart';
import '../theme.dart';

class AgentsScreen extends StatefulWidget {
  const AgentsScreen({super.key});

  @override
  State<AgentsScreen> createState() => _AgentsScreenState();
}

class _AgentsScreenState extends State<AgentsScreen> {
  final _api = ApiService();
  List<Agent> _agents = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await _api.getAgents();
      setState(() => _agents = data.map(Agent.fromJson).toList());
    } catch (e) {
      _showError(e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  void _showError(String msg) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  Future<void> _createAgent() async {
    final nameCtrl = TextEditingController();
    final urlCtrl = TextEditingController();
    final kwCtrl = TextEditingController();
    String type = 'rss';
    int interval = 60;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          title: const Text('Nouvel agent'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(
                  controller: nameCtrl,
                  decoration: const InputDecoration(labelText: 'Nom'),
                ),
                const SizedBox(height: 12),
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'rss', label: Text('RSS')),
                    ButtonSegment(value: 'web', label: Text('Web')),
                  ],
                  selected: {type},
                  onSelectionChanged: (s) => setS(() => type = s.first),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: urlCtrl,
                  keyboardType: TextInputType.url,
                  decoration: InputDecoration(
                    labelText: 'URL',
                    hintText: type == 'rss'
                        ? 'https://example.com/feed.xml'
                        : 'https://example.com/changelog',
                  ),
                ),
                if (type == 'rss') ...[
                  const SizedBox(height: 12),
                  TextField(
                    controller: kwCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Mots-clés (séparés par des virgules)',
                      hintText: 'AI, LLM, Claude',
                    ),
                  ),
                ],
                const SizedBox(height: 12),
                DropdownButtonFormField<int>(
                  value: interval,
                  decoration: const InputDecoration(labelText: 'Intervalle'),
                  items: const [
                    DropdownMenuItem(value: 15, child: Text('15 min')),
                    DropdownMenuItem(value: 30, child: Text('30 min')),
                    DropdownMenuItem(value: 60, child: Text('1 heure')),
                    DropdownMenuItem(value: 120, child: Text('2 heures')),
                    DropdownMenuItem(value: 360, child: Text('6 heures')),
                    DropdownMenuItem(value: 720, child: Text('12 heures')),
                    DropdownMenuItem(value: 1440, child: Text('24 heures')),
                  ],
                  onChanged: (v) => setS(() => interval = v!),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Annuler'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Créer'),
            ),
          ],
        ),
      ),
    );

    final name = nameCtrl.text.trim();
    final url = urlCtrl.text.trim();
    final kw = kwCtrl.text
        .split(',')
        .map((s) => s.trim())
        .where((s) => s.isNotEmpty)
        .toList();
    nameCtrl.dispose();
    urlCtrl.dispose();
    kwCtrl.dispose();

    if (confirmed != true) return;

    try {
      await _api.createAgent({
        'name': name,
        'type': type,
        'url': url,
        'keywords': kw,
        'interval_minutes': interval,
      });
      await _load();
    } catch (e) {
      _showError(e.toString());
    }
  }

  Future<void> _deleteAgent(Agent agent) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Supprimer l\'agent ?'),
        content: Text(agent.name),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await _api.deleteAgent(agent.id);
      await _load();
    } catch (e) {
      _showError(e.toString());
    }
  }

  Future<void> _showRuns(Agent agent) async {
    List<AgentRun> runs = [];
    bool loading = true;

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => StatefulBuilder(
        builder: (ctx, setS) {
          if (loading) {
            _api.getAgentRuns(agent.id).then((data) {
              setS(() {
                runs = data.map(AgentRun.fromJson).toList();
                loading = false;
              });
            }).catchError((e) {
              setS(() => loading = false);
            });
          }
          return DraggableScrollableSheet(
            initialChildSize: 0.6,
            maxChildSize: 0.92,
            minChildSize: 0.3,
            expand: false,
            builder: (_, ctrl) => Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                  child: Row(
                    children: [
                      Text(
                        'Historique · ${agent.name}',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                      ),
                      const Spacer(),
                      IconButton(
                        icon: const Icon(Icons.close, size: 20),
                        onPressed: () => Navigator.pop(ctx),
                        visualDensity: VisualDensity.compact,
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1),
                Expanded(
                  child: loading
                      ? const Center(child: CircularProgressIndicator())
                      : runs.isEmpty
                          ? const Center(child: Text('Aucune exécution.'))
                          : ListView.separated(
                              controller: ctrl,
                              padding: const EdgeInsets.all(12),
                              itemCount: runs.length,
                              separatorBuilder: (_, __) => const SizedBox(height: 6),
                              itemBuilder: (_, i) => _RunTile(run: runs[i]),
                            ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Future<void> _triggerRun(Agent agent) async {
    try {
      final result = await _api.runAgent(agent.id);
      final summary = result['summary'] as String? ?? '';
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${agent.name} : $summary')),
        );
      }
      await _load();
    } catch (e) {
      _showError(e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Agents'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
        bottom: notionAppBarDivider(context),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _agents.isEmpty
              ? _buildEmpty()
              : _buildList(),
      floatingActionButton: FloatingActionButton(
        onPressed: _createAgent,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildEmpty() {
    final subtle = Theme.of(context).colorScheme.onSurfaceVariant;
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.smart_toy_outlined, size: 48, color: subtle),
          const SizedBox(height: 12),
          Text(
            'Aucun agent. Appuie sur + pour en créer un.',
            style: TextStyle(color: subtle),
          ),
        ],
      ),
    );
  }

  Widget _buildList() {
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 80),
      itemCount: _agents.length,
      separatorBuilder: (_, __) => const SizedBox(height: 6),
      itemBuilder: (_, i) => _AgentTile(
        agent: _agents[i],
        onToggle: (val) async {
          await _api.toggleAgent(_agents[i].id, val);
          await _load();
        },
        onRun: () => _triggerRun(_agents[i]),
        onHistory: () => _showRuns(_agents[i]),
        onDelete: () => _deleteAgent(_agents[i]),
      ),
    );
  }
}

// ── Tiles ─────────────────────────────────────────────────────────────────────

class _AgentTile extends StatelessWidget {
  final Agent agent;
  final ValueChanged<bool> onToggle;
  final VoidCallback onRun;
  final VoidCallback onHistory;
  final VoidCallback onDelete;

  const _AgentTile({
    required this.agent,
    required this.onToggle,
    required this.onRun,
    required this.onHistory,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final subtle = theme.colorScheme.onSurfaceVariant;
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: onHistory,
        onLongPress: onDelete,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 12, 8, 12),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          agent.name,
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            color: theme.colorScheme.onSurface,
                          ),
                        ),
                        const SizedBox(width: 8),
                        _TypeBadge(agent.type),
                      ],
                    ),
                    const SizedBox(height: 3),
                    Text(
                      agent.url,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 12, color: subtle),
                    ),
                    if (agent.lastRun != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        'Dernière exécution · ${_fmtDate(agent.lastRun!)}',
                        style: TextStyle(fontSize: 11, color: subtle),
                      ),
                    ],
                  ],
                ),
              ),
              IconButton(
                icon: Icon(Icons.play_arrow_outlined, size: 20, color: subtle),
                visualDensity: VisualDensity.compact,
                onPressed: onRun,
                tooltip: 'Exécuter',
              ),
              Switch(
                value: agent.enabled,
                onChanged: onToggle,
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _fmtDate(String iso) {
    try {
      final d = DateTime.parse(iso).toLocal();
      return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')} ${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return iso;
    }
  }
}

class _TypeBadge extends StatelessWidget {
  final String type;
  const _TypeBadge(this.type);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: kNotionGreenBg,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: kNotionGreenBorder),
      ),
      child: Text(
        type.toUpperCase(),
        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: kNotionGreen),
      ),
    );
  }
}

class _RunTile extends StatelessWidget {
  final AgentRun run;
  const _RunTile({required this.run});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final statusColor = switch (run.status) {
      'ok' => kNotionGreen,
      'error' => theme.colorScheme.error,
      _ => theme.colorScheme.onSurfaceVariant,
    };
    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 7,
                  height: 7,
                  decoration: BoxDecoration(color: statusColor, shape: BoxShape.circle),
                ),
                const SizedBox(width: 8),
                Text(
                  _fmtDate(run.timestamp),
                  style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurfaceVariant),
                ),
                const Spacer(),
                Text(
                  run.summary,
                  style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface),
                ),
              ],
            ),
            if (run.items.isNotEmpty) ...[
              const SizedBox(height: 8),
              ...run.items.take(5).map(
                    (item) => Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text(
                        '· ${item['title'] ?? item['link'] ?? ''}',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 12,
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ),
                  ),
            ],
          ],
        ),
      ),
    );
  }

  String _fmtDate(String iso) {
    try {
      final d = DateTime.parse(iso).toLocal();
      return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')} '
          '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return iso;
    }
  }
}
