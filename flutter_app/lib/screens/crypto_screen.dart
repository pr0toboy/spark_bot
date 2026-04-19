import 'package:flutter/material.dart';
import '../theme.dart';
import '../models/crypto.dart';
import '../services/api_service.dart';
import '../widgets/notion_section_label.dart';

String _fmtUsd(double v) {
  if (v == 0) return '\$0.00';
  if (v >= 1e9) return '\$${(v / 1e9).toStringAsFixed(2)}B';
  if (v >= 1e6) return '\$${(v / 1e6).toStringAsFixed(2)}M';
  if (v >= 1)   return '\$${v.toStringAsFixed(2)}';
  if (v >= 0.0001) return '\$${v.toStringAsFixed(6)}';
  return '\$${v.toStringAsExponential(2)}';
}

String _fmtEur(double v) {
  if (v == 0) return '€0.00';
  if (v >= 1e9) return '€${(v / 1e9).toStringAsFixed(2)}B';
  if (v >= 1e6) return '€${(v / 1e6).toStringAsFixed(2)}M';
  if (v >= 1)   return '€${v.toStringAsFixed(2)}';
  if (v >= 0.0001) return '€${v.toStringAsFixed(6)}';
  return '€${v.toStringAsExponential(2)}';
}

String _fmtFiat(double v, bool useEur) => useEur ? _fmtEur(v) : _fmtUsd(v);

const _kChainTicker = {
  'btc': 'BTC', 'xpub': 'BTC', 'eth': 'ETH',
  'avax': 'AVAX', 'sol': 'SOL', 'dot': 'DOT',
};

String _fmtBal(double bal, String chain) {
  final ticker = _kChainTicker[chain] ?? chain.toUpperCase();
  final decimals = (chain == 'btc' || chain == 'xpub') ? 6 : 4;
  return '${bal.toStringAsFixed(decimals)} $ticker';
}

class CryptoScreen extends StatefulWidget {
  const CryptoScreen({super.key});

  @override
  State<CryptoScreen> createState() => _CryptoScreenState();
}

class _CryptoScreenState extends State<CryptoScreen>
    with SingleTickerProviderStateMixin {
  final _api = ApiService();
  late final TabController _tab;

  List<CryptoMarketItem> _market = [];
  List<CryptoTrend> _trending = [];
  bool _loadingMarket = true;

  CryptoPortfolio? _portfolio;
  bool _loadingPortfolio = false;
  bool _useEur = false;

  List<CryptoAlert> _alerts = [];
  bool _loadingAlerts = true;

  @override
  void initState() {
    super.initState();
    _tab = TabController(length: 3, vsync: this);
    _tab.addListener(_onTabChange);
    _loadMarket();
    _loadAlerts();
  }

  @override
  void dispose() {
    _tab.removeListener(_onTabChange);
    _tab.dispose();
    super.dispose();
  }

  void _onTabChange() {
    if (_tab.index == 1 && _portfolio == null) _loadPortfolio();
  }

  Future<void> _loadMarket() async {
    setState(() => _loadingMarket = true);
    try {
      final results = await Future.wait([
        _api.getCryptoMarket(),
        _api.getCryptoTrending(),
      ]);
      if (!mounted) return;
      setState(() {
        _market   = results[0] as List<CryptoMarketItem>;
        _trending = results[1] as List<CryptoTrend>;
      });
    } catch (e) {
      _showErr(e.toString());
    } finally {
      if (mounted) setState(() => _loadingMarket = false);
    }
  }

  Future<void> _loadPortfolio() async {
    setState(() => _loadingPortfolio = true);
    try {
      final p = await _api.getCryptoPortfolio();
      if (!mounted) return;
      setState(() => _portfolio = p);
    } catch (e) {
      _showErr(e.toString());
    } finally {
      if (mounted) setState(() => _loadingPortfolio = false);
    }
  }

  Future<void> _loadAlerts() async {
    setState(() => _loadingAlerts = true);
    try {
      final a = await _api.getCryptoAlerts();
      if (!mounted) return;
      setState(() => _alerts = a);
    } catch (e) {
      _showErr(e.toString());
    } finally {
      if (mounted) setState(() => _loadingAlerts = false);
    }
  }

  Future<void> _addWallet() async {
    final addrCtrl  = TextEditingController();
    final labelCtrl = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Ajouter un wallet'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: addrCtrl,
              autofocus: true,
              decoration: const InputDecoration(hintText: 'Adresse (BTC, ETH 0x…, SOL, DOT)'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: labelCtrl,
              decoration: const InputDecoration(hintText: 'Label (ex: Cold BTC)'),
              textInputAction: TextInputAction.done,
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(context, true),  child: const Text('Ajouter')),
        ],
      ),
    );
    final addr  = addrCtrl.text.trim();
    final label = labelCtrl.text.trim();
    addrCtrl.dispose();
    labelCtrl.dispose();
    if (confirmed != true || addr.isEmpty || label.isEmpty) return;
    try {
      await _api.addCryptoWallet(addr, label);
      setState(() => _portfolio = null);
      await _loadPortfolio();
    } on ApiException catch (e) {
      _showErr(e.message);
    }
  }

  Future<void> _renameWallet(CryptoWallet w) async {
    final ctrl = TextEditingController(text: w.label);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Renommer le wallet'),
        content: TextField(
          controller: ctrl,
          autofocus: true,
          decoration: const InputDecoration(hintText: 'Nouveau nom'),
          textInputAction: TextInputAction.done,
          onSubmitted: (_) => Navigator.pop(context, true),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Renommer')),
        ],
      ),
    );
    final newLabel = ctrl.text.trim();
    ctrl.dispose();
    if (confirmed != true || newLabel.isEmpty || newLabel == w.label) return;
    try {
      await _api.renameCryptoWallet(w.label, newLabel);
      setState(() => _portfolio = null);
      await _loadPortfolio();
    } on ApiException catch (e) {
      _showErr(e.message);
    }
  }

  Future<void> _deleteWallet(CryptoWallet w) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Supprimer le wallet ?'),
        content: Text('${w.label} (${w.chain.toUpperCase()})'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(context, true),  child: const Text('Supprimer')),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await _api.deleteCryptoWallet(w.label);
      setState(() => _portfolio = null);
      await _loadPortfolio();
    } on ApiException catch (e) {
      _showErr(e.message);
    }
  }

  Future<void> _addAlert() async {
    final coinCtrl  = TextEditingController();
    final priceCtrl = TextEditingController();
    String direction = 'above';

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          title: const Text('Nouvelle alerte'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: coinCtrl,
                autofocus: true,
                decoration: const InputDecoration(hintText: 'Coin (btc, eth, sol…)'),
              ),
              const SizedBox(height: 12),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'above', label: Text('Au-dessus'), icon: Icon(Icons.arrow_upward, size: 14)),
                  ButtonSegment(value: 'below', label: Text('En-dessous'), icon: Icon(Icons.arrow_downward, size: 14)),
                ],
                selected: {direction},
                onSelectionChanged: (s) => setS(() => direction = s.first),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: priceCtrl,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(hintText: 'Prix cible (USD)'),
                textInputAction: TextInputAction.done,
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Annuler')),
            FilledButton(onPressed: () => Navigator.pop(ctx, true),  child: const Text('Créer')),
          ],
        ),
      ),
    );
    final coin  = coinCtrl.text.trim();
    final price = double.tryParse(priceCtrl.text.trim().replaceAll(',', '.'));
    coinCtrl.dispose();
    priceCtrl.dispose();
    if (confirmed != true || coin.isEmpty || price == null) return;
    try {
      await _api.addCryptoAlert(coin, direction, price);
      await _loadAlerts();
    } on ApiException catch (e) {
      _showErr(e.message);
    }
  }

  Future<void> _deleteAlert(CryptoAlert alert) async {
    try {
      await _api.deleteCryptoAlert(alert.id);
      await _loadAlerts();
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
        title: const Text('Crypto'),
        actions: [
          TextButton(
            onPressed: () => setState(() => _useEur = !_useEur),
            child: Text(
              _useEur ? '€' : '\$',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              if (_tab.index == 0) _loadMarket();
              if (_tab.index == 1) { setState(() => _portfolio = null); _loadPortfolio(); }
              if (_tab.index == 2) _loadAlerts();
            },
          ),
        ],
        bottom: TabBar(
          controller: _tab,
          tabs: const [
            Tab(text: 'Marché'),
            Tab(text: 'Portfolio'),
            Tab(text: 'Alertes'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tab,
        children: [
          _buildMarket(),
          _buildPortfolio(),
          _buildAlerts(),
        ],
      ),
      floatingActionButton: ListenableBuilder(
        listenable: _tab,
        builder: (_, __) {
          if (_tab.index == 1) {
            return FloatingActionButton(
              heroTag: 'wallet_fab',
              onPressed: _addWallet,
              child: const Icon(Icons.add),
            );
          }
          if (_tab.index == 2) {
            return FloatingActionButton(
              heroTag: 'alert_fab',
              onPressed: _addAlert,
              child: const Icon(Icons.add),
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }

  Widget _buildMarket() {
    if (_loadingMarket) return const Center(child: CircularProgressIndicator());
    return RefreshIndicator(
      onRefresh: _loadMarket,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(12, 16, 12, 80),
        children: [
          const NotionSectionLabel('Cours', Icons.show_chart),
          const SizedBox(height: 8),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              childAspectRatio: 2.4,
              crossAxisSpacing: 8,
              mainAxisSpacing: 8,
            ),
            itemCount: _market.length,
            itemBuilder: (_, i) => _MarketCard(_market[i], useEur: _useEur),
          ),
          if (_trending.isNotEmpty) ...[
            const SizedBox(height: 20),
            const NotionSectionLabel('Tendances', Icons.local_fire_department_outlined),
            const SizedBox(height: 8),
            ..._trending.map((t) => _TrendTile(t)),
          ],
        ],
      ),
    );
  }

  Widget _buildPortfolio() {
    if (_loadingPortfolio) return const Center(child: CircularProgressIndicator());
    if (_portfolio == null) {
      return Center(
        child: FilledButton.icon(
          onPressed: _loadPortfolio,
          icon: const Icon(Icons.download_outlined, size: 16),
          label: const Text('Charger le portfolio'),
        ),
      );
    }
    final p = _portfolio!;
    return RefreshIndicator(
      onRefresh: () async { setState(() => _portfolio = null); await _loadPortfolio(); },
      child: ListView(
        padding: const EdgeInsets.fromLTRB(12, 16, 12, 80),
        children: [
          if (p.totalUsd != null || p.totalEur != null)
            _TotalCard(
              totalUsd: p.totalUsd ?? 0,
              totalEur: p.totalEur ?? 0,
              useEur: _useEur,
            ),
          const SizedBox(height: 12),
          if (p.wallets.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 40),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.account_balance_wallet_outlined,
                        size: 40, color: Theme.of(context).colorScheme.onSurfaceVariant),
                    const SizedBox(height: 12),
                    Text(
                      'Aucun wallet — appuie sur + pour en ajouter un.',
                      style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
                    ),
                  ],
                ),
              ),
            )
          else ...[
            const NotionSectionLabel('Wallets', Icons.account_balance_wallet_outlined),
            const SizedBox(height: 8),
            ...p.wallets.map((w) => _WalletTile(w,
                useEur: _useEur,
                onRename: () => _renameWallet(w),
                onDelete: () => _deleteWallet(w))),
          ],
        ],
      ),
    );
  }

  Widget _buildAlerts() {
    if (_loadingAlerts) return const Center(child: CircularProgressIndicator());
    if (_alerts.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.notifications_off_outlined,
                size: 40, color: Theme.of(context).colorScheme.onSurfaceVariant),
            const SizedBox(height: 12),
            Text(
              'Aucune alerte — appuie sur + pour en créer une.',
              style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _loadAlerts,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(12, 16, 12, 80),
        children: _alerts.map((a) => _AlertTile(a, onDelete: () => _deleteAlert(a))).toList(),
      ),
    );
  }

}

class _MarketCard extends StatelessWidget {
  final CryptoMarketItem item;
  final bool useEur;
  const _MarketCard(this.item, {this.useEur = false});

  @override
  Widget build(BuildContext context) {
    final up    = item.change24h >= 0;
    final color = up ? kNotionGreen : kNotionRed;
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(item.symbol,
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 13,
                  color: theme.colorScheme.onSurface,
                )),
            const SizedBox(height: 2),
            Text(_fmtFiat(useEur ? item.priceEur : item.priceUsd, useEur),
                style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface)),
            const SizedBox(height: 2),
            Row(
              children: [
                Icon(up ? Icons.arrow_upward : Icons.arrow_downward, size: 11, color: color),
                Text(
                  '${item.change24h.abs().toStringAsFixed(2)}%',
                  style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _TrendTile extends StatelessWidget {
  final CryptoTrend trend;
  const _TrendTile(this.trend);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
          child: Row(
            children: [
              const Icon(Icons.local_fire_department_outlined,
                  size: 16, color: kNotionOrange),
              const SizedBox(width: 12),
              Expanded(
                child: Text(trend.name,
                    style: TextStyle(
                      fontWeight: FontWeight.w500,
                      fontSize: 13,
                      color: theme.colorScheme.onSurface,
                    )),
              ),
              Text(trend.symbol,
                  style: TextStyle(
                    fontSize: 12,
                    color: theme.colorScheme.onSurfaceVariant,
                  )),
              if (trend.rank != null) ...[
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surfaceContainerLow,
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: theme.colorScheme.outline),
                  ),
                  child: Text('#${trend.rank}',
                      style: TextStyle(
                        fontSize: 11,
                        color: theme.colorScheme.onSurfaceVariant,
                      )),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _TotalCard extends StatelessWidget {
  final double totalUsd;
  final double totalEur;
  final bool useEur;
  const _TotalCard({required this.totalUsd, required this.totalEur, this.useEur = false});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Total portfolio',
                style: TextStyle(
                  fontSize: 12,
                  color: theme.colorScheme.onSurfaceVariant,
                )),
            const SizedBox(height: 4),
            Text(
              _fmtFiat(useEur ? totalEur : totalUsd, useEur),
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.w700,
                letterSpacing: -0.5,
                color: theme.colorScheme.onSurface,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _WalletTile extends StatelessWidget {
  final CryptoWallet wallet;
  final bool useEur;
  final VoidCallback onRename;
  final VoidCallback onDelete;
  const _WalletTile(this.wallet, {this.useEur = false, required this.onRename, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final short = '${wallet.address.substring(0, 8)}…${wallet.address.substring(wallet.address.length - 4)}';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 12, 8, 12),
          child: Row(
            children: [
              Container(
                width: 34, height: 34,
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceContainerLow,
                  borderRadius: BorderRadius.circular(7),
                  border: Border.all(color: theme.colorScheme.outline),
                ),
                child: Icon(Icons.account_balance_wallet_outlined,
                    size: 16, color: theme.colorScheme.onSurfaceVariant),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(wallet.label,
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                          color: theme.colorScheme.onSurface,
                        )),
                    Text(short,
                        style: TextStyle(
                          fontSize: 11,
                          color: theme.colorScheme.onSurfaceVariant,
                          fontFamily: 'monospace',
                        )),
                    if (wallet.balance != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        _fmtBal(wallet.balance!, wallet.chain) + (() {
                          final fiatVal = useEur ? wallet.balanceEur : wallet.balanceUsd;
                          return fiatVal != null ? '  ≈ ${_fmtFiat(fiatVal, useEur)}' : '';
                        })(),
                        style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface),
                      ),
                    ],
                  ],
                ),
              ),
              IconButton(
                icon: Icon(Icons.edit_outlined, size: 18,
                    color: theme.colorScheme.onSurfaceVariant),
                visualDensity: VisualDensity.compact,
                onPressed: onRename,
              ),
              IconButton(
                icon: Icon(Icons.delete_outline, size: 18,
                    color: theme.colorScheme.onSurfaceVariant),
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

class _AlertTile extends StatelessWidget {
  final CryptoAlert alert;
  final VoidCallback onDelete;
  const _AlertTile(this.alert, {required this.onDelete});

  @override
  Widget build(BuildContext context) {
    final theme   = Theme.of(context);
    final up      = alert.direction == 'above';
    final color   = up ? kNotionGreen : kNotionRed;
    final label   = up ? '>' : '<';
    // Pre-computed opacity colors for the icon container
    final iconBg     = alert.active ? color.withValues(alpha: 0.10) : color.withValues(alpha: 0.05);
    final iconBorder = alert.active ? color.withValues(alpha: 0.30) : color.withValues(alpha: 0.15);
    final iconColor  = alert.active ? color : color.withValues(alpha: 0.4);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 12, 8, 12),
          child: Row(
            children: [
              Container(
                width: 34, height: 34,
                decoration: BoxDecoration(
                  color: iconBg,
                  borderRadius: BorderRadius.circular(7),
                  border: Border.all(color: iconBorder),
                ),
                child: Icon(
                  up ? Icons.arrow_upward : Icons.arrow_downward,
                  size: 16,
                  color: iconColor,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${alert.coin.toUpperCase()}  $label  ${_fmtUsd(alert.price)}',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 13,
                        color: alert.active
                            ? theme.colorScheme.onSurface
                            : theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                    Text(
                      alert.active ? 'Active' : 'Déclenchée',
                      style: TextStyle(
                        fontSize: 11,
                        color: alert.active ? color : theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: Icon(Icons.delete_outline, size: 18,
                    color: theme.colorScheme.onSurfaceVariant),
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
