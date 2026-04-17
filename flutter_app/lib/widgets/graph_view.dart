import 'dart:math';
import 'package:flutter/material.dart';

class GraphNode {
  final String id;
  final String label;
  Offset position;
  GraphNode({required this.id, required this.label, required this.position});
}

class GraphEdge {
  final String source;
  final String target;
  GraphEdge({required this.source, required this.target});
}

class GraphView extends StatefulWidget {
  final List<Map<String, dynamic>> nodes;
  final List<Map<String, dynamic>> edges;
  final void Function(String id, String label)? onNodeTap;

  const GraphView({
    super.key,
    required this.nodes,
    required this.edges,
    this.onNodeTap,
  });

  @override
  State<GraphView> createState() => _GraphViewState();
}

class _GraphViewState extends State<GraphView> {
  late List<GraphNode> _nodes;
  late List<GraphEdge> _edges;
  final _transformCtrl = TransformationController();

  static const double _canvasSize = 1400;
  static const double _nodeRadius = 18;

  @override
  void initState() {
    super.initState();
    _init();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final size = context.size;
      if (size != null) _fitToNodes(size);
    });
  }

  @override
  void didUpdateWidget(GraphView old) {
    super.didUpdateWidget(old);
    if (old.nodes != widget.nodes || old.edges != widget.edges) {
      _init();
      WidgetsBinding.instance.addPostFrameCallback((_) {
        final size = context.size;
        if (size != null) _fitToNodes(size);
      });
    }
  }

  @override
  void dispose() {
    _transformCtrl.dispose();
    super.dispose();
  }

  void _init() {
    final rng = Random(42);
    _nodes = widget.nodes
        .map((n) => GraphNode(
              id: n['id'] as String,
              label: n['label'] as String,
              position: Offset(
                100 + rng.nextDouble() * (_canvasSize - 200),
                100 + rng.nextDouble() * (_canvasSize - 200),
              ),
            ))
        .toList();

    _edges = widget.edges
        .map((e) => GraphEdge(
              source: e['source'] as String,
              target: e['target'] as String,
            ))
        .toList();

    _forceLayout();
  }

  void _forceLayout() {
    if (_nodes.length < 2) return;

    const k = 160.0;
    const repulsion = 12000.0;
    double temp = _canvasSize / 4;

    // Build index map once — avoids O(n) indexOf and O(n) map rebuild per iteration.
    final nodeIndex = <String, int>{};
    for (int i = 0; i < _nodes.length; i++) {
      nodeIndex[_nodes[i].id] = i;
    }

    for (int iter = 0; iter < 120; iter++) {
      final forces = List.generate(_nodes.length, (_) => Offset.zero);

      // répulsion
      for (int i = 0; i < _nodes.length; i++) {
        for (int j = i + 1; j < _nodes.length; j++) {
          final d = _nodes[i].position - _nodes[j].position;
          final dist = d.distance.clamp(1.0, double.infinity);
          final f = repulsion / (dist * dist);
          final dir = d / dist;
          forces[i] = forces[i] + dir * f;
          forces[j] = forces[j] - dir * f;
        }
      }

      // attraction sur les arêtes
      for (final edge in _edges) {
        final si = nodeIndex[edge.source];
        final ti = nodeIndex[edge.target];
        if (si == null || ti == null) continue;
        final d = _nodes[ti].position - _nodes[si].position;
        final dist = d.distance.clamp(1.0, double.infinity);
        final f = (dist * dist) / k;
        final dir = d / dist;
        forces[si] = forces[si] + dir * f;
        forces[ti] = forces[ti] - dir * f;
      }

      // application
      for (int i = 0; i < _nodes.length; i++) {
        final fv = forces[i];
        final mag = fv.distance;
        if (mag > 0) {
          final clamped = min(mag, temp);
          _nodes[i].position += (fv / mag) * clamped;
          _nodes[i].position = Offset(
            _nodes[i].position.dx.clamp(_nodeRadius, _canvasSize - _nodeRadius),
            _nodes[i].position.dy.clamp(_nodeRadius, _canvasSize - _nodeRadius),
          );
        }
      }
      temp *= 0.94;
    }
  }

  void _fitToNodes(Size viewSize) {
    if (_nodes.isEmpty) return;
    var minX = _nodes.first.position.dx;
    var maxX = minX;
    var minY = _nodes.first.position.dy;
    var maxY = minY;
    for (final n in _nodes) {
      if (n.position.dx < minX) minX = n.position.dx;
      if (n.position.dx > maxX) maxX = n.position.dx;
      if (n.position.dy < minY) minY = n.position.dy;
      if (n.position.dy > maxY) maxY = n.position.dy;
    }
    const padding = 80.0;
    minX -= padding; maxX += padding;
    minY -= padding; maxY += padding;
    final contentW = max(maxX - minX, 1.0);
    final contentH = max(maxY - minY, 1.0);
    final s = min(viewSize.width / contentW, viewSize.height / contentH)
        .clamp(0.15, 2.0);
    final cx = (minX + maxX) / 2;
    final cy = (minY + maxY) / 2;
    _transformCtrl.value = Matrix4.identity()
      ..translate(viewSize.width / 2 - cx * s, viewSize.height / 2 - cy * s)
      ..scale(s);
  }

  GraphNode? _nodeAt(Offset canvasPos) {
    for (final node in _nodes) {
      if ((node.position - canvasPos).distance <= _nodeRadius + 10) return node;
    }
    return null;
  }

  Offset _toCanvas(Offset screenPos) {
    final inv = Matrix4.inverted(_transformCtrl.value);
    return MatrixUtils.transformPoint(inv, screenPos);
  }

  @override
  Widget build(BuildContext context) {
    if (_nodes.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: const [
            Icon(Icons.grain, size: 48, color: Colors.white24),
            SizedBox(height: 12),
            Text('Aucune note — crée des notes avec [[liens]] pour voir le graph.'),
          ],
        ),
      );
    }

    return GestureDetector(
      onTapUp: (details) {
        final canvasPos = _toCanvas(details.localPosition);
        final node = _nodeAt(canvasPos);
        if (node != null) widget.onNodeTap?.call(node.id, node.label);
      },
      child: InteractiveViewer(
        transformationController: _transformCtrl,
        boundaryMargin: const EdgeInsets.all(200),
        minScale: 0.15,
        maxScale: 4.0,
        child: SizedBox(
          width: _canvasSize,
          height: _canvasSize,
          child: CustomPaint(
            painter: _GraphPainter(
              nodes: _nodes,
              edges: _edges,
              nodeRadius: _nodeRadius,
            ),
          ),
        ),
      ),
    );
  }
}


class _GraphPainter extends CustomPainter {
  final List<GraphNode> nodes;
  final List<GraphEdge> edges;
  final double nodeRadius;

  _GraphPainter({
    required this.nodes,
    required this.edges,
    required this.nodeRadius,
  });

  static const _palette = [
    Color(0xFF7C9CF5),
    Color(0xFFB07CF5),
    Color(0xFF7CF5C0),
    Color(0xFFF5A97C),
    Color(0xFFF57CAA),
    Color(0xFF7CDDF5),
    Color(0xFFF5E17C),
  ];

  Color _colorFor(String id) => _palette[id.hashCode.abs() % _palette.length];

  @override
  void paint(Canvas canvas, Size size) {
    final nodeMap = {for (final n in nodes) n.id: n};

    final edgePaint = Paint()
      ..color = Colors.white.withOpacity(0.18)
      ..strokeWidth = 1.2
      ..style = PaintingStyle.stroke;

    for (final edge in edges) {
      final src = nodeMap[edge.source];
      final tgt = nodeMap[edge.target];
      if (src == null || tgt == null) continue;
      canvas.drawLine(src.position, tgt.position, edgePaint);
    }

    for (final node in nodes) {
      final color = _colorFor(node.id);

      // halo
      canvas.drawCircle(
        node.position,
        nodeRadius + 4,
        Paint()
          ..color = color.withOpacity(0.15)
          ..style = PaintingStyle.fill,
      );

      // disque
      canvas.drawCircle(
        node.position,
        nodeRadius,
        Paint()
          ..color = color.withOpacity(0.85)
          ..style = PaintingStyle.fill,
      );

      // label
      final short = node.label.length > 18
          ? '${node.label.substring(0, 18)}…'
          : node.label;
      final tp = TextPainter(
        text: TextSpan(
          text: short,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 9.5,
            fontWeight: FontWeight.w500,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: 120);

      tp.paint(
        canvas,
        node.position + Offset(-tp.width / 2, nodeRadius + 5),
      );
    }
  }

  @override
  bool shouldRepaint(_GraphPainter old) =>
      old.nodes != nodes || old.edges != edges;
}
