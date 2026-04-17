import 'package:flutter/material.dart';
import 'screens/chat_screen.dart';
import 'screens/commands_screen.dart';
import 'screens/crypto_screen.dart';
import 'screens/habit_screen.dart';
import 'screens/notes_screen.dart';
import 'screens/settings_screen.dart';
import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiService().init();
  runApp(const SparkApp());
}

class SparkApp extends StatelessWidget {
  const SparkApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Spark',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6C63FF)),
        useMaterial3: true,
      ),
      home: const _Shell(),
    );
  }
}

class _Shell extends StatefulWidget {
  const _Shell();

  @override
  State<_Shell> createState() => _ShellState();
}

class _ShellState extends State<_Shell> {
  int _index = 0;

  static const _screens = [
    ChatScreen(),
    CommandsScreen(),
    CryptoScreen(),
    HabitScreen(),
    NotesScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _index, children: _screens),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: 'Chat'),
          NavigationDestination(icon: Icon(Icons.terminal_outlined), selectedIcon: Icon(Icons.terminal), label: 'Commandes'),
          NavigationDestination(icon: Icon(Icons.currency_bitcoin), selectedIcon: Icon(Icons.currency_bitcoin), label: 'Crypto'),
          NavigationDestination(icon: Icon(Icons.self_improvement_outlined), selectedIcon: Icon(Icons.self_improvement), label: 'Habitudes'),
          NavigationDestination(icon: Icon(Icons.note_outlined), selectedIcon: Icon(Icons.note), label: 'Notes'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'Paramètres'),
        ],
      ),
    );
  }
}
