import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';
import '../models/message.dart';
import '../models/note.dart';
import '../models/skill.dart';

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => message;
}

class ApiService {
  static final ApiService _instance = ApiService._();
  factory ApiService() => _instance;
  ApiService._();

  final _client = http.Client();

  Uri _url(String path) => Uri.parse('$kBaseUrl$path');

  Future<Map<String, dynamic>> _get(String path) async {
    final res = await _client.get(_url(path));
    _checkStatus(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<dynamic> _getList(String path) async {
    final res = await _client.get(_url(path));
    _checkStatus(res);
    return jsonDecode(res.body);
  }

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body) async {
    final res = await _client.post(
      _url(path),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    _checkStatus(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<void> _delete(String path) async {
    final res = await _client.delete(_url(path));
    _checkStatus(res);
  }

  void _checkStatus(http.Response res) {
    if (res.statusCode >= 400) {
      final body = jsonDecode(res.body) as Map<String, dynamic>;
      throw ApiException(body['detail']?.toString() ?? 'Erreur ${res.statusCode}');
    }
  }

  // --- AI ---

  Future<({String reply, List<String> actions})> sendMessage(String message) async {
    final data = await _post('/api/ai', {'message': message});
    return (
      reply: data['reply'] as String,
      actions: List<String>.from(data['actions'] as List),
    );
  }

  Future<List<Message>> getHistory() async {
    final data = await _get('/api/ai/history');
    final list = data['history'] as List;
    return list.map((e) => Message.fromHistory(e as Map<String, dynamic>)).toList();
  }

  Future<void> clearHistory() => _delete('/api/ai/history');

  Future<String> compactHistory() async {
    final data = await _post('/api/ai/compact', {});
    return data['message'] as String;
  }

  // --- Notes ---

  Future<List<Note>> getNotes() async {
    final list = await _getList('/api/notes') as List;
    return list.map((e) => Note.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Note> createNote(String content) async {
    final data = await _post('/api/notes', {'content': content});
    return Note.fromJson(data);
  }

  Future<void> deleteNote(int id) => _delete('/api/notes/$id');

  Future<String> exportNotes() async {
    final data = await _post('/api/notes/export', {});
    return data['message'] as String;
  }

  // --- Tools ---

  Future<List<Map<String, dynamic>>> getTools() async {
    final list = await _getList('/api/tools') as List;
    return list.cast<Map<String, dynamic>>();
  }

  Future<void> setTool(String name, bool enabled) =>
      _post('/api/tools', {'name': name, 'enabled': enabled});

  // --- Skills ---

  Future<List<Skill>> getSkills() async {
    final list = await _getList('/api/skills') as List;
    return list.map((e) => Skill.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<Skill>> getPresets() async {
    final list = await _getList('/api/skills/presets') as List;
    return list.map((e) => Skill.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Skill> upsertSkill(String name, String instructions) async {
    final data = await _post('/api/skills', {'name': name, 'instructions': instructions});
    return Skill.fromJson(data);
  }

  Future<void> deleteSkill(String name) => _delete('/api/skills/$name');

  // --- Settings ---

  Future<Map<String, dynamic>> getSettings() => _get('/api/settings');

  Future<Map<String, dynamic>> getModels() => _get('/api/settings/models');

  Future<void> updateSettings(Map<String, dynamic> updates) =>
      _post('/api/settings', updates);
}
