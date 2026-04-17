class Habit {
  final int id;
  final String name;
  final int freqNum;
  final int freqDen;
  final bool doneToday;
  final int streak;
  final int bestStreak;
  final List<bool> week;

  const Habit({
    required this.id,
    required this.name,
    required this.freqNum,
    required this.freqDen,
    required this.doneToday,
    required this.streak,
    required this.bestStreak,
    required this.week,
  });

  factory Habit.fromJson(Map<String, dynamic> j) => Habit(
        id: j['id'] as int,
        name: j['name'] as String,
        freqNum: j['freq_num'] as int,
        freqDen: j['freq_den'] as int,
        doneToday: j['done_today'] as bool,
        streak: j['streak'] as int,
        bestStreak: j['best_streak'] as int,
        week: (j['week'] as List).cast<bool>(),
      );

  Habit copyWith({bool? doneToday, int? streak, int? bestStreak}) => Habit(
        id: id,
        name: name,
        freqNum: freqNum,
        freqDen: freqDen,
        doneToday: doneToday ?? this.doneToday,
        streak: streak ?? this.streak,
        bestStreak: bestStreak ?? this.bestStreak,
        week: week,
      );

  String get freqLabel {
    if (freqDen == 1) return 'quotidien';
    if (freqDen == 7) return '$freqNum×/sem';
    return '$freqNum/${freqDen}j';
  }
}

class HabitStats {
  final int id;
  final String name;
  final int streak;
  final int bestStreak;
  final int weekDone;
  final int monthDone;
  final int total;
  final List<bool> week;

  const HabitStats({
    required this.id,
    required this.name,
    required this.streak,
    required this.bestStreak,
    required this.weekDone,
    required this.monthDone,
    required this.total,
    required this.week,
  });

  factory HabitStats.fromJson(Map<String, dynamic> j) => HabitStats(
        id: j['id'] as int,
        name: j['name'] as String,
        streak: j['streak'] as int,
        bestStreak: j['best_streak'] as int,
        weekDone: j['week_done'] as int,
        monthDone: j['month_done'] as int,
        total: j['total'] as int,
        week: (j['week'] as List).cast<bool>(),
      );
}
