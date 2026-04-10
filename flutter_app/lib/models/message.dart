class Message {
  final String role; // 'user' | 'assistant'
  final String content;
  final List<String> actions;
  final DateTime timestamp;

  Message({
    required this.role,
    required this.content,
    this.actions = const [],
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  bool get isUser => role == 'user';

  factory Message.fromHistory(Map<String, dynamic> json) {
    return Message(
      role: json['role'] as String,
      content: json['content'] as String,
    );
  }
}
