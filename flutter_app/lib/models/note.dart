class Note {
  final int id;
  final String timestamp;
  final String content;

  Note({required this.id, required this.timestamp, required this.content});

  factory Note.fromJson(Map<String, dynamic> json) {
    return Note(
      id: json['id'] as int,
      timestamp: json['timestamp'] as String,
      content: json['content'] as String,
    );
  }
}
