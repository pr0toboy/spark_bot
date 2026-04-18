class Agent {
  final int id;
  final String name;
  final String type;
  final String url;
  final List<String> keywords;
  final bool enabled;
  final int intervalMinutes;
  final String? lastRun;

  const Agent({
    required this.id,
    required this.name,
    required this.type,
    required this.url,
    required this.keywords,
    required this.enabled,
    required this.intervalMinutes,
    this.lastRun,
  });

  factory Agent.fromJson(Map<String, dynamic> j) => Agent(
        id: j['id'] as int,
        name: j['name'] as String,
        type: j['type'] as String,
        url: j['url'] as String,
        keywords: List<String>.from(j['keywords'] as List),
        enabled: j['enabled'] as bool,
        intervalMinutes: j['interval_minutes'] as int,
        lastRun: j['last_run'] as String?,
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
