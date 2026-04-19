import 'package:flutter/material.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import '../models/message.dart';
import '../services/api_service.dart';
import '../theme.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;
  final _api = ApiService();
  final _controller = TextEditingController();
  final _scroll = ScrollController();
  final List<Message> _messages = [];
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    try {
      final history = await _api.getHistory();
      setState(() => _messages.addAll(history));
      _scrollToBottom();
    } catch (_) {}
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _loading) return;

    setState(() {
      _messages.add(Message(role: 'user', content: text));
      _loading = true;
    });
    _controller.clear();
    _scrollToBottom();

    try {
      final result = await _api.sendMessage(text);
      setState(() {
        _messages.add(Message(
          role: 'assistant',
          content: result.reply,
          actions: result.actions,
        ));
      });
    } on ApiException catch (e) {
      setState(() {
        _messages.add(Message(role: 'assistant', content: '⚠ ${e.message}'));
      });
    } finally {
      setState(() => _loading = false);
      _scrollToBottom();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _clearHistory() async {
    await _api.clearHistory();
    setState(() => _messages.clear());
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 14,
        title: Row(
          children: [
            ClipOval(
              child: Image.asset(
                'assets/logo.jpg',
                width: 34,
                height: 34,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 10),
            const Text('Spark'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline),
            tooltip: 'Vider l\'historique',
            onPressed: _clearHistory,
          ),
        ],
        bottom: notionAppBarDivider(context),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scroll,
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              itemCount: _messages.length,
              itemBuilder: (_, i) => _MessageBubble(message: _messages[i]),
            ),
          ),
          if (_loading)
            LinearProgressIndicator(
              minHeight: 2,
              color: theme.colorScheme.primary,
              backgroundColor: Colors.transparent,
            ),
          _InputBar(controller: _controller, onSend: _send, loading: _loading),
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final Message message;
  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.isUser;
    final theme  = Theme.of(context);

    final bubbleColor = isUser
        ? theme.colorScheme.primary
        : theme.colorScheme.surfaceContainerLow;

    final mdStyle = MarkdownStyleSheet.fromTheme(theme).copyWith(
      p: TextStyle(
        color: theme.colorScheme.onSurface,
        fontSize: 14,
        height: 1.5,
      ),
      pPadding: EdgeInsets.zero,
      code: TextStyle(
        backgroundColor: theme.colorScheme.outline.withValues(alpha: 0.15),
        color: kSparkOrange,
        fontSize: 13,
        fontFamily: 'monospace',
      ),
      codeblockDecoration: BoxDecoration(
        color: theme.colorScheme.outline.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
      ),
      codeblockPadding: const EdgeInsets.all(12),
      blockquoteDecoration: const BoxDecoration(
        border: Border(
          left: BorderSide(color: kSparkOrange, width: 3),
        ),
      ),
      blockquotePadding: const EdgeInsets.only(left: 12, top: 4, bottom: 4),
      a: const TextStyle(color: kSparkOrange),
      listIndent: 16,
      h1: TextStyle(
        color: theme.colorScheme.onSurface,
        fontSize: 17,
        fontWeight: FontWeight.w700,
        height: 1.4,
      ),
      h2: TextStyle(
        color: theme.colorScheme.onSurface,
        fontSize: 15,
        fontWeight: FontWeight.w600,
        height: 1.4,
      ),
      h3: TextStyle(
        color: theme.colorScheme.onSurface,
        fontSize: 14,
        fontWeight: FontWeight.w600,
        height: 1.4,
      ),
      strong: const TextStyle(fontWeight: FontWeight.w700),
      em: const TextStyle(fontStyle: FontStyle.italic),
      blockSpacing: 8,
    );

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.78),
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 4),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: bubbleColor,
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(14),
              topRight: const Radius.circular(14),
              bottomLeft: Radius.circular(isUser ? 14 : 4),
              bottomRight: Radius.circular(isUser ? 4 : 14),
            ),
            border: isUser
                ? null
                : Border.all(color: theme.colorScheme.outline),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (message.actions.isNotEmpty) ...[
                for (final a in message.actions)
                  Text(
                    a,
                    style: TextStyle(
                      fontSize: 11,
                      color: isUser
                          ? theme.colorScheme.onPrimary.withValues(alpha: 0.65)
                          : kSparkOrange.withValues(alpha: 0.8),
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                const SizedBox(height: 6),
              ],
              if (isUser)
                Text(
                  message.content,
                  style: TextStyle(
                    color: theme.colorScheme.onPrimary,
                    fontSize: 14,
                    height: 1.5,
                  ),
                )
              else
                MarkdownBody(
                  data: message.content,
                  styleSheet: mdStyle,
                  softLineBreak: true,
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _InputBar extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;
  final bool loading;

  const _InputBar({
    required this.controller,
    required this.onSend,
    required this.loading,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(top: BorderSide(color: theme.colorScheme.outline)),
      ),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  textInputAction: TextInputAction.send,
                  onSubmitted: (_) => onSend(),
                  enabled: !loading,
                  maxLines: 5,
                  minLines: 1,
                  style: TextStyle(fontSize: 14, color: theme.colorScheme.onSurface),
                  decoration: InputDecoration(
                    hintText: 'Message à Spark…',
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    fillColor: theme.colorScheme.surfaceContainerLow,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                width: 38,
                height: 38,
                child: Material(
                  color: loading
                      ? theme.colorScheme.surfaceContainerHighest
                      : theme.colorScheme.primary,
                  borderRadius: BorderRadius.circular(10),
                  child: InkWell(
                    onTap: loading ? null : onSend,
                    borderRadius: BorderRadius.circular(10),
                    child: Icon(
                      Icons.arrow_upward_rounded,
                      size: 18,
                      color: loading
                          ? theme.colorScheme.onSurfaceVariant
                          : theme.colorScheme.onPrimary,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
