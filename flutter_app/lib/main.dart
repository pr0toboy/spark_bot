import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'screens/agents_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/commands_screen.dart';
import 'screens/crypto_screen.dart';
import 'screens/habit_screen.dart';
import 'screens/notes_screen.dart';
import 'screens/settings_screen.dart';
import 'services/api_service.dart';
import 'theme.dart';

@pragma('vm:entry-point')
Future<void> _bgMessageHandler(RemoteMessage _) async {
  await Firebase.initializeApp();
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  FirebaseMessaging.onBackgroundMessage(_bgMessageHandler);
  await ApiService().init();
  await _registerPushToken();
  runApp(const SparkApp());
}

Future<void> _registerPushToken() async {
  try {
    final messaging = FirebaseMessaging.instance;
    await messaging.requestPermission(alert: true, badge: true, sound: true);
    final token = await messaging.getToken();
    if (token != null) {
      await ApiService().registerPushToken(token);
    }
    messaging.onTokenRefresh.listen((t) => ApiService().registerPushToken(t));
  } catch (_) {
    // Firebase not configured yet — silent fail
  }
}

class SparkApp extends StatelessWidget {
  const SparkApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Spark',
      debugShowCheckedModeBanner: false,
      theme: buildNotionTheme(Brightness.light),
      darkTheme: buildNotionTheme(Brightness.dark),
      themeMode: ThemeMode.system,
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
  int _index = 3; // Chat au centre par défaut

  static const _screens = [
    CommandsScreen(),
    AgentsScreen(),
    CryptoScreen(),
    ChatScreen(),   // index 3 = centre
    HabitScreen(),
    NotesScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final border = Theme.of(context).colorScheme.outline;
    return Scaffold(
      body: IndexedStack(index: _index, children: _screens),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(top: BorderSide(color: border)),
        ),
        child: NavigationBar(
          selectedIndex: _index,
          onDestinationSelected: (i) => setState(() => _index = i),
          labelBehavior: NavigationDestinationLabelBehavior.alwaysHide,
          destinations: const [
            NavigationDestination(icon: Icon(Icons.terminal_outlined),      selectedIcon: Icon(Icons.terminal),          label: ''),
            NavigationDestination(icon: Icon(Icons.smart_toy_outlined),     selectedIcon: Icon(Icons.smart_toy),         label: ''),
            NavigationDestination(icon: Icon(Icons.currency_bitcoin),       selectedIcon: Icon(Icons.currency_bitcoin),  label: ''),
            NavigationDestination(icon: Icon(Icons.chat_bubble_outline),    selectedIcon: Icon(Icons.chat_bubble),       label: ''),
            NavigationDestination(icon: Icon(Icons.self_improvement_outlined), selectedIcon: Icon(Icons.self_improvement), label: ''),
            NavigationDestination(icon: Icon(Icons.note_outlined),          selectedIcon: Icon(Icons.note),              label: ''),
            NavigationDestination(icon: Icon(Icons.settings_outlined),      selectedIcon: Icon(Icons.settings),          label: ''),
          ],
        ),
      ),
    );
  }
}
