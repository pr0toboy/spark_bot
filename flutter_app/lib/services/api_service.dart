import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/crypto.dart';
import '../models/message.dart';
import '../models/note.dart';
import '../models/skill.dart';

const String _kBaseUrlKey = 'server_url';
const String kDefaultBaseUrl = 'http://192.168.1.26:8000';

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
  String _baseUrl = kDefaultBaseUrl;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString(_kBaseUrlKey) ?? kDefaultBaseUrl;
  }

  Future<void> setBaseUrl(String url) async {
    _baseUrl = url.trimRight().replaceAll(RegExp(r'/$'), '');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kBaseUrlKey, _baseUrl);
  }

  String get baseUrl => _baseUrl;

  Uri _url(String path) => Uri.parse('$_baseUrl$path');

  Future<Map<String, dynamic>> _get(String path) async {
    final res = await _client.get(_url(path));
    _checkStatus(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> _getList(String path) async {
    final res = await _client.get(_url(path));
    _checkStatus(res);
    return jsonDecode(res.body) as List<dynamic>;
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
    final list = await _getList('/api/notes');
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

  Future<Map<String, dynamic>> getGraph() => _get('/api/notes/graph');

  // --- Tools ---

  Future<List<Map<String, dynamic>>> getTools() async {
    final list = await _getList('/api/tools');
    return list.cast<Map<String, dynamic>>();
  }

  Future<void> setTool(String name, bool enabled) =>
      _post('/api/tools', {'name': name, 'enabled': enabled});

  // --- Skills ---

  Future<List<Skill>> getSkills() async {
    final list = await _getList('/api/skills');
    return list.map((e) => Skill.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<Skill>> getPresets() async {
    final list = await _getList('/api/skills/presets');
    return list.map((e) => Skill.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Skill> upsertSkill(String name, String instructions) async {
    final data = await _post('/api/skills', {'name': name, 'instructions': instructions});
    return Skill.fromJson(data);
  }

  Future<void> deleteSkill(String name) => _delete('/api/skills/$name');

  // --- Claude Code ---

  Future<({String reply, bool ok})> runClaude(String prompt, {bool useContinue = false}) async {
    final data = await _post('/api/claude', {
      'prompt': prompt,
      'use_continue': useContinue,
    });
    return (reply: data['reply'] as String, ok: data['ok'] as bool);
  }

  // --- Crypto ---

  Future<List<CryptoMarketItem>> getCryptoMarket() async {
    final list = await _getList('/api/crypto/market');
    return list.map((e) => CryptoMarketItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<CryptoTrend>> getCryptoTrending() async {
    final list = await _getList('/api/crypto/trending');
    return list.map((e) => CryptoTrend.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<CryptoPortfolio> getCryptoPortfolio() async {
    final data = await _get('/api/crypto/portfolio');
    return CryptoPortfolio.fromJson(data);
  }

  Future<CryptoWallet> addCryptoWallet(String address, String label) async {
    final data = await _post('/api/crypto/wallets', {'address': address, 'label': label});
    return CryptoWallet.fromJson(data);
  }

  Future<void> deleteCryptoWallet(String label) =>
      _delete('/api/crypto/wallets/${Uri.encodeComponent(label)}');

  Future<List<CryptoAlert>> getCryptoAlerts() async {
    final list = await _getList('/api/crypto/alerts');
    return list.map((e) => CryptoAlert.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<CryptoAlert> addCryptoAlert(String coin, String direction, double price) async {
    final data = await _post('/api/crypto/alerts', {
      'coin': coin, 'direction': direction, 'price': price,
    });
    return CryptoAlert.fromJson(data);
  }

  Future<void> deleteCryptoAlert(int id) => _delete('/api/crypto/alerts/$id');

  // --- Settings ---

  Future<Map<String, dynamic>> getSettings() => _get('/api/settings');

  Future<Map<String, dynamic>> getModels() => _get('/api/settings/models');

  Future<void> updateSettings(Map<String, dynamic> updates) =>
      _post('/api/settings', updates);
}
