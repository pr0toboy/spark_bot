import 'package:flutter/material.dart';
import '../models/habit.dart';
import '../services/api_service.dart';

const _kPurple = Color(0xFF9C7CF5);
const _kGreen  = Color(0xFF7CF5A9);
const _kOrange = Color(0xFFF5A97C);
const _kPink   = Color(0xFFF57CAA);

const _kDays = ['Lu', 'Ma', 'Me', 'Je', 'Ve', 'Sa', 'Di'];

class HabitScreen extends StatefulWidget {
  const HabitScreen({super.key});

  @override
  State<HabitScreen> createState() => _HabitScreenState();
}

class _HabitScreenState extends State<HabitScreen>
    with SingleTickerProviderStateMixin {
  final _api = ApiService();
  late final TabController _tab;

  List<Habit> _habits = [];
  bool _loading = true;

  HabitStats? _selectedStats;
  int? _selectedId;
  bool _loadingStats = false;

  @override
  void initState() {
    super.initState();
    _tab = TabController(length: 2, vsync: this);
    _tab.addListener(() {
      if (_tab.indexIsChanging) return;
      if (_tab.index == 1 && _selectedId == null && _habits.isNotEmpty) {
        _loadStats(_habits.first.id);
      }
    });
    _loadHabits();
  }

  @override
  void dispose() {
    _tab.dispose();
    super.dispose();
  }

  Future<void> _loadHabits() async {
    setState(() => _loading = true);
    try {
      final h = await _api.getHabits();
      if (!mounted) return;
      setState(() => _habits = h);
    } catch (e) {
      _showErr(e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadStats(int id) async {
    setState(() { _loadingStats = true; _selectedId = id; });
    try {
      final s = await _api.getHabitStats(id);
      if (!mounted) return;
      setState(() => _selectedStats = s);
    } catch (e) {
      _showErr(e.toString());
    } finally {
      if (mounted) setState(() => _loadingStats = false);
    }
  }

  Future<void> _toggleHabit(Habit h) async {
    try {
      final res = h.doneToday
          ? await _api.uncheckHabit(h.id)
          : await _api.checkHabit(h.id);
      setState(() {
        final i = _habits.indexWhere((x) => x.id == h.id);
        if (i >= 0) {
          _habits[i] = h.copyWith(
            doneToday: res['done_today'] as bool? ?? !h.doneToday,
            streak: res['streak'] as int? ?? h.streak,
            bestStreak: res['best_streak'] as int? ?? h.bestStreak,
          );
        }
      });
    } catch (e) {
      _showErr(e.toString());
    }
  }

  Future<void> _addHabit() async {
    final nameCtrl = TextEditingController();
    int freqNum = 1;
    int freqDen = 1;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          title: const Text('Nouvelle habitude'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: nameCtrl,
                autofocus: true,
                decoration: const InputDecoration(hintText: 'Nom (ex: Sport, Lecture…)'),
                textInputAction: TextInputAction.done,
              ),
              const SizedBox(height: 16),
              const Text('Fréquence', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: '1/1', label: Text('Quotidien')),
                  ButtonSegment(value: '3/7', label: Text('3×/sem')),
                  ButtonSegment(value: '5/7', label: Text('5×/sem')),
                ],
                selected: {'$freqNum/$freqDen'},
                onSelectionChanged: (s) {
                  final parts = s.first.split('/');
                  setS(() {
                    freqNum = int.parse(parts[0]);
                    freqDen = int.parse(parts[1]);
                  });
                },
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Annuler')),
            FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Créer')),
          ],
        ),
      ),
    );

    final name = nameCtrl.text.trim();
    nameCtrl.dispose();
    if (confirmed != true || name.isEmpty) return;

    try {
      final h = await _api.createHabit(name, freqNum: freqNum, freqDen: freqDen);
      setState(() => _habits.add(h));
    } on ApiException catch (e) {
      _showErr(e.message);
    }
  }

  Future<void> _deleteHabit(Habit h) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('Archiver cette habitude ?'),
        content: Text('« ${h.name} » sera archivée (données conservées).'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogCtx, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(dialogCtx, true), child: const Text('Archiver')),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await _api.deleteHabit(h.id);
      setState(() => _habits.removeWhere((x) => x.id == h.id));
      if (_selectedId == h.id) setState(() { _selectedId = null; _selectedStats = null; });
    } on ApiException catch (e) {
      _showErr(e.message);
    }
  }

  void _showErr(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Habitudes'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              if (_tab.index == 0) _loadHabits();
              if (_tab.index == 1 && _selectedId != null) _loadStats(_selectedId!);
            },
          ),
        ],
        bottom: TabBar(
          controller: _tab,
          tabs: const [
            Tab(icon: Icon(Icons.check_circle_outline), text: 'Aujourd\'hui'),
            Tab(icon: Icon(Icons.bar_chart_outlined),   text: 'Stats'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tab,
        children: [_buildToday(), _buildStats()],
      ),
      floatingActionButton: ListenableBuilder(
        listenable: _tab,
        builder: (_, __) => _tab.index == 0
            ? FloatingActionButton(
                onPressed: _addHabit,
                child: const Icon(Icons.add),
              )
            : const SizedBox.shrink(),
      ),
    );
  }

  Widget _buildToday() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_habits.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: const [
            Icon(Icons.self_improvement, size: 52, color: Colors.white24),
            SizedBox(height: 12),
            Text('Aucune habitude — appuie sur + pour commencer.'),
          ],
        ),
      );
    }
    final done   = _habits.where((h) => h.doneToday).length;
    final total  = _habits.length;
    return RefreshIndicator(
      onRefresh: _loadHabits,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(12, 16, 12, 80),
        children: [
          _ProgressHeader(done: done, total: total),
          const SizedBox(height: 16),
          ..._habits.map((h) => _HabitTile(
                habit: h,
                onToggle: () => _toggleHabit(h),
                onDelete: () => _deleteHabit(h),
                onStats: () {
                  _tab.animateTo(1);
                  _loadStats(h.id);
                },
              )),
        ],
      ),
    );
  }

  Widget _buildStats() {
    if (_habits.isEmpty && !_loading) {
      return const Center(child: Text('Aucune habitude à afficher.'));
    }
    return Column(
      children: [
        if (_habits.isNotEmpty)
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
            child: Row(
              children: _habits.map((h) {
                final selected = h.id == _selectedId;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(h.name),
                    selected: selected,
                    onSelected: (_) => _loadStats(h.id),
                  ),
                );
              }).toList(),
            ),
          ),
        const SizedBox(height: 8),
        Expanded(child: _statsBody()),
      ],
    );
  }

  Widget _statsBody() {
    if (_loadingStats) return const Center(child: CircularProgressIndicator());
    if (_selectedStats == null) {
      return const Center(child: Text('Sélectionne une habitude ci-dessus.'));
    }
    final s = _selectedStats!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(s.name,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        Row(
          children: [
            _StatCard(label: 'Streak', value: '${s.streak}', icon: Icons.local_fire_department, color: _kOrange),
            const SizedBox(width: 8),
            _StatCard(label: 'Record', value: '${s.bestStreak}', icon: Icons.emoji_events_outlined, color: _kPurple),
            const SizedBox(width: 8),
            _StatCard(label: 'Total', value: '${s.total}', icon: Icons.done_all, color: _kGreen),
          ],
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            _StatCard(label: 'Cette semaine', value: '${s.weekDone}/7', icon: Icons.calendar_view_week_outlined, color: _kGreen),
            const SizedBox(width: 8),
            _StatCard(label: 'Ce mois', value: '${s.monthDone}/30', icon: Icons.calendar_month_outlined, color: _kPurple),
          ],
        ),
        const SizedBox(height: 20),
        _WeekRow(week: s.week),
      ],
    );
  }
}

class _ProgressHeader extends StatelessWidget {
  final int done;
  final int total;
  const _ProgressHeader({required this.done, required this.total});

  @override
  Widget build(BuildContext context) {
    final pct = total == 0 ? 0.0 : done / total;
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      color: _kPurple.withOpacity(0.1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: _kPurple.withOpacity(0.25)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Aujourd\'hui',
                    style: TextStyle(fontSize: 12, color: _kPurple.withOpacity(0.8))),
                Text('$done / $total',
                    style: const TextStyle(fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: pct,
                minHeight: 6,
                backgroundColor: theme.colorScheme.surfaceContainerHighest,
                valueColor: AlwaysStoppedAnimation(
                  pct == 1.0 ? _kGreen : _kPurple,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HabitTile extends StatelessWidget {
  final Habit habit;
  final VoidCallback onToggle;
  final VoidCallback onDelete;
  final VoidCallback onStats;
  const _HabitTile({
    required this.habit,
    required this.onToggle,
    required this.onDelete,
    required this.onStats,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final done  = habit.doneToday;
    final color = done ? _kGreen : _kPurple;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Card(
        elevation: 0,
        color: theme.colorScheme.surfaceContainerLow,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(4, 10, 8, 10),
          child: Row(
            children: [
              IconButton(
                onPressed: onToggle,
                icon: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 200),
                  child: Icon(
                    done ? Icons.check_circle : Icons.radio_button_unchecked,
                    key: ValueKey(done),
                    color: color,
                    size: 28,
                  ),
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(habit.name,
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                          color: done ? theme.disabledColor : null,
                          decoration: done ? TextDecoration.lineThrough : null,
                        )),
                    const SizedBox(height: 4),
                    _WeekRow(week: habit.week, compact: true),
                    if (habit.streak >= 2)
                      Padding(
                        padding: const EdgeInsets.only(top: 3),
                        child: Row(
                          children: [
                            Icon(Icons.local_fire_department, size: 13, color: _kOrange),
                            const SizedBox(width: 2),
                            Text('${habit.streak}',
                                style: TextStyle(
                                  fontSize: 11,
                                  color: _kOrange,
                                  fontWeight: FontWeight.w600,
                                )),
                            const SizedBox(width: 8),
                            Text(habit.freqLabel,
                                style: TextStyle(
                                  fontSize: 11,
                                  color: theme.colorScheme.onSurfaceVariant,
                                )),
                          ],
                        ),
                      )
                    else
                      Padding(
                        padding: const EdgeInsets.only(top: 3),
                        child: Text(habit.freqLabel,
                            style: TextStyle(
                              fontSize: 11,
                              color: theme.colorScheme.onSurfaceVariant,
                            )),
                      ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.bar_chart_outlined, size: 20),
                visualDensity: VisualDensity.compact,
                onPressed: onStats,
              ),
              IconButton(
                icon: const Icon(Icons.delete_outline, size: 20),
                visualDensity: VisualDensity.compact,
                onPressed: onDelete,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _WeekRow extends StatelessWidget {
  final List<bool> week;
  final bool compact;
  const _WeekRow({required this.week, this.compact = false});

  @override
  Widget build(BuildContext context) {
    final size = compact ? 20.0 : 28.0;
    final fontSize = compact ? 8.0 : 10.0;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(7, (i) {
        final done = i < week.length && week[i];
        return Padding(
          padding: const EdgeInsets.only(right: 4),
          child: Column(
            children: [
              Container(
                width: size,
                height: size,
                decoration: BoxDecoration(
                  color: done ? _kGreen.withOpacity(0.25) : Colors.white10,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                    color: done ? _kGreen.withOpacity(0.6) : Colors.white12,
                    width: 1,
                  ),
                ),
                child: done
                    ? Icon(Icons.check, size: size * 0.55, color: _kGreen)
                    : null,
              ),
              if (!compact) ...[
                const SizedBox(height: 2),
                Text(_kDays[i],
                    style: TextStyle(
                      fontSize: fontSize,
                      color: Colors.white38,
                    )),
              ],
            ],
          ),
        );
      }),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  const _StatCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Expanded(
      child: Card(
        elevation: 0,
        color: color.withOpacity(0.1),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: color.withOpacity(0.25)),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, size: 18, color: color),
              const SizedBox(height: 6),
              Text(value,
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: color,
                  )),
              Text(label,
                  style: TextStyle(
                    fontSize: 11,
                    color: theme.colorScheme.onSurfaceVariant,
                  )),
            ],
          ),
        ),
      ),
    );
  }
}
