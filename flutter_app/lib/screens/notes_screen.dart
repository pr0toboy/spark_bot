import 'package:flutter/material.dart';
import '../models/note.dart';
import '../services/api_service.dart';
import '../widgets/graph_view.dart';

class NotesScreen extends StatefulWidget {
  const NotesScreen({super.key});

  @override
  State<NotesScreen> createState() => _NotesScreenState();
}

class _NotesScreenState extends State<NotesScreen> {
  final _api = ApiService();
  List<Note> _notes = [];
  List<Map<String, dynamic>> _graphNodes = [];
  List<Map<String, dynamic>> _graphEdges = [];
  bool _loading = true;
  bool _graphMode = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      if (_graphMode) {
        final graph = await _api.getGraph();
        setState(() {
          _graphNodes = (graph['nodes'] as List).cast<Map<String, dynamic>>();
          _graphEdges = (graph['edges'] as List).cast<Map<String, dynamic>>();
        });
      } else {
        _notes = await _api.getNotes();
      }
    } catch (e) {
      _showError(e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _toggleMode() async {
    _graphMode = !_graphMode;
    await _load();
  }

  Future<void> _addNote() async {
    final controller = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Nouvelle note'),
        content: TextField(
          controller: controller,
          autofocus: true,
          maxLines: 4,
          decoration: const InputDecoration(hintText: 'Contenu de la note…'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Ajouter')),
        ],
      ),
    );
    if (confirmed != true || controller.text.trim().isEmpty) return;
    try {
      await _api.createNote(controller.text.trim());
      await _load();
    } catch (e) {
      _showError(e.toString());
    }
  }

  Future<void> _deleteNote(Note note) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Supprimer la note ?'),
        content: Text(note.content, maxLines: 3, overflow: TextOverflow.ellipsis),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Supprimer')),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await _api.deleteNote(note.id);
      await _load();
    } catch (e) {
      _showError(e.toString());
    }
  }

  void _showNodeDetail(String id, String label) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: Text('Note #$id'),
        content: Text(label),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Fermer'),
          ),
        ],
      ),
    );
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notes'),
        actions: [
          IconButton(
            icon: Icon(_graphMode ? Icons.list : Icons.grain),
            tooltip: _graphMode ? 'Vue liste' : 'Vue graph',
            onPressed: _toggleMode,
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _graphMode
              ? GraphView(
                  nodes: _graphNodes,
                  edges: _graphEdges,
                  onNodeTap: _showNodeDetail,
                )
              : _buildList(),
      floatingActionButton: _graphMode
          ? null
          : FloatingActionButton(
              onPressed: _addNote,
              child: const Icon(Icons.add),
            ),
    );
  }

  Widget _buildList() {
    if (_notes.isEmpty) {
      return const Center(child: Text('Aucune note. Appuie sur + pour en créer une.'));
    }
    return ListView.builder(
      itemCount: _notes.length,
      itemBuilder: (_, i) {
        final note = _notes[i];
        return ListTile(
          title: Text(note.content, maxLines: 2, overflow: TextOverflow.ellipsis),
          subtitle: Text(note.timestamp, style: const TextStyle(fontSize: 11)),
          trailing: IconButton(
            icon: const Icon(Icons.delete_outline),
            onPressed: () => _deleteNote(note),
          ),
        );
      },
    );
  }
}
