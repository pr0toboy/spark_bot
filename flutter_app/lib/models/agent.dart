class Agent {
  final int id;
  final String name;
  final String type;
  final String url;
  final List<String> keywords;
  final bool enabled;
  final int intervalMinutes;
  final String? lastRun;
  final String aiContext;
  final String imapHost;
  final int imapPort;
  final String imapUsername;
  final String imapFolder;

  const Agent({
    required this.id,
    required this.name,
    required this.type,
    required this.url,
    required this.keywords,
    required this.enabled,
    required this.intervalMinutes,
    this.lastRun,
    this.aiContext = '',
    this.imapHost = 'imap.gmail.com',
    this.imapPort = 993,
    this.imapUsername = '',
    this.imapFolder = 'INBOX',
  });

  factory Agent.fromJson(Map<String, dynamic> j) => Agent(
        id: j['id'] as int,
        name: j['name'] as String,
        type: j['type'] as String,
        url: j['url'] as String? ?? '',
        keywords: List<String>.from(j['keywords'] as List),
        enabled: j['enabled'] as bool,
        intervalMinutes: j['interval_minutes'] as int,
        lastRun: j['last_run'] as String?,
        aiContext: j['ai_context'] as String? ?? '',
        imapHost: j['imap_host'] as String? ?? 'imap.gmail.com',
        imapPort: j['imap_port'] as int? ?? 993,
        imapUsername: j['imap_username'] as String? ?? '',
        imapFolder: j['imap_folder'] as String? ?? 'INBOX',
      );
}

class AgentRun {
  final int id;
  final String timestamp;
  final String status;
  final String summary;
  final List<Map<String, dynamic>> items;

  const AgentRun({
    required this.id,
    required this.timestamp,
    required this.status,
    required this.summary,
    required this.items,
  });

  factory AgentRun.fromJson(Map<String, dynamic> j) => AgentRun(
        id: j['id'] as int,
        timestamp: j['timestamp'] as String,
        status: j['status'] as String,
        summary: j['summary'] as String,
        items: (j['items'] as List).cast<Map<String, dynamic>>(),
      );
}
