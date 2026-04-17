import 'package:flutter/material.dart';
import '../services/api_service.dart';

class _Msg {
  final bool isUser;
  final String text;
  final bool isError;
  _Msg.user(this.text) : isUser = true, isError = false;
  _Msg.claude(this.text, {this.isError = false}) : isUser = false;
}

class ClaudeScreen extends StatefulWidget {
  const ClaudeScreen({super.key});

  @override
  State<ClaudeScreen> createState() => _ClaudeScreenState();
}

class _ClaudeScreenState extends State<ClaudeScreen>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  final _api        = ApiService();
  final _ctrl       = TextEditingController();
  final _scroll     = ScrollController();
  final List<_Msg>  _msgs = [];
  bool _loading     = false;
  bool _useContinue = false;

  @override
  void dispose() {
    _ctrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty || _loading) return;
    setState(() {
      _msgs.add(_Msg.user(text));
      _loading = true;
    });
    _ctrl.clear();
    _scrollToBottom();
    try {
      final result = await _api.runClaude(text, useContinue: _useContinue);
      setState(() => _msgs.add(_Msg.claude(result.reply, isError: !result.ok)));
    } on ApiException catch (e) {
      setState(() => _msgs.add(_Msg.claude('❌ ${e.message}', isError: true)));
    } finally {
      setState(() => _loading = false);
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || !_scroll.hasClients) return;
      _scroll.animateTo(
        _scroll.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Text('Claude Code'),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: const Color(0xFF7C9CF5).withOpacity(0.18),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF7C9CF5).withOpacity(0.4)),
              ),
              child: Text(
                'Pi 5',
                style: TextStyle(
                  fontSize: 11,
                  color: const Color(0xFF7C9CF5),
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
        actions: [
          Tooltip(
            message: _useContinue
                ? 'Continuer la session Claude Code'
                : 'Nouvelle session à chaque message',
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Continue',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: _useContinue
                        ? theme.colorScheme.primary
                        : theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                Switch.adaptive(
                  value: _useContinue,
                  onChanged: (v) => setState(() => _useContinue = v),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline),
            tooltip: 'Effacer l\'affichage',
            onPressed: _msgs.isEmpty
                ? null
                : () => setState(() => _msgs.clear()),
          ),
        ],
      ),
      body: Column(
        children: [
          if (_msgs.isEmpty)
            Expanded(child: _EmptyState(onExample: (t) {
              _ctrl.text = t;
              _send();
            }))
          else
            Expanded(
              child: ListView.builder(
                controller: _scroll,
                padding: const EdgeInsets.fromLTRB(12, 12, 12, 4),
                itemCount: _msgs.length,
                itemBuilder: (_, i) => _Bubble(_msgs[i]),
              ),
            ),
          if (_loading)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Row(
                children: [
                  const SizedBox(
                    width: 14, height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  const SizedBox(width: 10),
                  Text('Claude Code répond…',
                      style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant)),
                ],
              ),
            ),
          _InputBar(ctrl: _ctrl, onSend: _send, loading: _loading),
        ],
      ),
    );
  }
}

// ─── Widgets ─────────────────────────────────────────────────────────────────

class _Bubble extends StatelessWidget {
  final _Msg msg;
  const _Bubble(this.msg, {super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUser = msg.isUser;
    Color bg;
    Color fg;
    if (isUser) {
      bg = theme.colorScheme.primary;
      fg = theme.colorScheme.onPrimary;
    } else if (msg.isError) {
      bg = theme.colorScheme.errorContainer;
      fg = theme.colorScheme.onErrorContainer;
    } else {
      bg = const Color(0xFF7C9CF5).withOpacity(0.12);
      fg = theme.colorScheme.onSurface;
    }
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.88),
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 4),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.circular(16),
          ),
          child: SelectableText(
            msg.text,
            style: TextStyle(
              color: fg,
              fontFamily: isUser ? null : 'monospace',
              fontSize: isUser ? 14 : 13,
              height: 1.5,
            ),
          ),
        ),
      ),
    );
  }
}

class _InputBar extends StatelessWidget {
  final TextEditingController ctrl;
  final VoidCallback onSend;
  final bool loading;
  const _InputBar({required this.ctrl, required this.onSend, required this.loading});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: ctrl,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => onSend(),
                enabled: !loading,
                maxLines: null,
                decoration: InputDecoration(
                  hintText: 'Demande à Claude Code…',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              icon: const Icon(Icons.send),
              onPressed: loading ? null : onSend,
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final void Function(String) onExample;
  const _EmptyState({required this.onExample});

  static const _examples = [
    'Liste les fichiers du projet spark_bot',
    'Quel est l\'espace disque disponible ?',
    'Résume le fichier commands/crypto.py',
    'Vérifie si le serveur FastAPI tourne',
  ];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.terminal, size: 52, color: const Color(0xFF7C9CF5).withOpacity(0.5)),
            const SizedBox(height: 16),
            Text(
              'Claude Code sur Pi 5',
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            Text(
              'Envoie une tâche ou une question à Claude Code\nqui tourne directement sur ton Raspberry Pi.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall
                  ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: 24),
            ..._examples.map((e) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: OutlinedButton.icon(
                onPressed: () => onExample(e),
                icon: const Icon(Icons.bolt_outlined, size: 16),
                label: Text(e, style: const TextStyle(fontSize: 12)),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  alignment: Alignment.centerLeft,
                ),
              ),
            )),
          ],
        ),
      ),
    );
  }
}
