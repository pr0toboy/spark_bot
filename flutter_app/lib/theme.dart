import 'package:flutter/material.dart';

// ─── Spark palette ───────────────────────────────────────────────────────────

const kSparkOrange = Color(0xFFF97316);
const kSparkYellow = Color(0xFFF59E0B);
const kSparkTeal   = Color(0xFF0D9488);
const kSparkCoral  = Color(0xFFF43F5E);
const kSparkBlue   = Color(0xFF3B82F6);

// Light
const kBgLight   = Color(0xFFF5EFE6);
const kSurfLight = Color(0xFFFDFAF5);
const kTextLight = Color(0xFF2B1D0E);
const kSubtLight = Color(0xFF9C856A);
const kBordLight = Color(0xFFE8DDD0);
const kSubLight  = Color(0xFFEEE6DA);

// Dark
const kBgDark    = Color(0xFF1C1208);
const kSurfDark  = Color(0xFF261A0E);
const kTextDark  = Color(0xFFF5EFE6);
const kSubtDark  = Color(0xFF9C856A);
const kBordDark  = Color(0xFF3D2D1E);
const kSubDark   = Color(0xFF301E10);

// ─── Semantic aliases (backward compat with screen files) ────────────────────

const kNotionGreen       = kSparkTeal;
const kNotionRed         = kSparkCoral;
const kNotionAccent      = kSparkBlue;
const kNotionOrange      = kSparkOrange;
const kNotionGreenBg     = Color(0x260D9488); // kSparkTeal @ 15%
const kNotionGreenBorder = Color(0x660D9488); // kSparkTeal @ 40%

// ─── Helpers ─────────────────────────────────────────────────────────────────

PreferredSize notionAppBarDivider(BuildContext context) => PreferredSize(
      preferredSize: const Size.fromHeight(1),
      child: Divider(height: 1, color: Theme.of(context).colorScheme.outline),
    );

// ─── Theme builder ───────────────────────────────────────────────────────────

ThemeData buildNotionTheme(Brightness brightness) {
  final isDark  = brightness == Brightness.dark;
  final bg      = isDark ? kBgDark   : kBgLight;
  final surface = isDark ? kSurfDark : kSurfLight;
  final text    = isDark ? kTextDark : kTextLight;
  final subtle  = isDark ? kSubtDark : kSubtLight;
  final border  = isDark ? kBordDark : kBordLight;
  final sub     = isDark ? kSubDark  : kSubLight;

  const primary   = kSparkOrange;
  const onPrimary = Colors.white;

  final scheme = ColorScheme(
    brightness: brightness,
    primary: primary,
    onPrimary: onPrimary,
    secondary: subtle,
    onSecondary: surface,
    error: kSparkCoral,
    onError: Colors.white,
    surface: surface,
    onSurface: text,
    surfaceContainerLow: sub,
    surfaceContainerHighest: border,
    onSurfaceVariant: subtle,
    outline: border,
    outlineVariant: sub,
  );

  return ThemeData(
    colorScheme: scheme,
    useMaterial3: true,
    scaffoldBackgroundColor: bg,
    appBarTheme: AppBarTheme(
      backgroundColor: surface,
      foregroundColor: text,
      elevation: 0,
      scrolledUnderElevation: 0,
      surfaceTintColor: Colors.transparent,
      titleTextStyle: TextStyle(
        color: text,
        fontSize: 15,
        fontWeight: FontWeight.w600,
        letterSpacing: -0.1,
      ),
      iconTheme: IconThemeData(color: subtle, size: 20),
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      color: surface,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: BorderSide(color: border),
      ),
    ),
    dividerTheme: DividerThemeData(color: border, space: 1, thickness: 1),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: primary, width: 1.5),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      fillColor: surface,
      filled: true,
      hintStyle: TextStyle(color: subtle, fontSize: 14),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: primary,
        textStyle: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: primary,
        foregroundColor: onPrimary,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: surface,
      elevation: 0,
      shadowColor: Colors.transparent,
      surfaceTintColor: Colors.transparent,
      indicatorColor: const Color(0x26F97316), // orange @ 15%
      iconTheme: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return const IconThemeData(color: primary, size: 22);
        }
        return IconThemeData(color: subtle, size: 22);
      }),
      height: 58,
    ),
    chipTheme: ChipThemeData(
      backgroundColor: sub,
      selectedColor: isDark ? const Color(0xFF3D2D1E) : const Color(0xFFE8DDD0),
      labelStyle: TextStyle(color: text, fontSize: 13),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: border),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      side: BorderSide(color: border),
    ),
    tabBarTheme: TabBarThemeData(
      labelColor: primary,
      unselectedLabelColor: subtle,
      indicatorColor: primary,
      dividerColor: border,
      indicatorSize: TabBarIndicatorSize.tab,
      labelStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
      unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w400, fontSize: 13),
      tabAlignment: TabAlignment.fill,
    ),
    floatingActionButtonTheme: FloatingActionButtonThemeData(
      backgroundColor: primary,
      foregroundColor: onPrimary,
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: text,
      contentTextStyle: TextStyle(
        color: isDark ? kBgDark : Colors.white,
        fontSize: 13,
      ),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      behavior: SnackBarBehavior.floating,
    ),
    progressIndicatorTheme: ProgressIndicatorThemeData(
      color: primary,
      linearTrackColor: border,
      circularTrackColor: border,
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((s) =>
          s.contains(WidgetState.selected) ? Colors.white : subtle),
      trackColor: WidgetStateProperty.resolveWith((s) =>
          s.contains(WidgetState.selected) ? primary : border),
      trackOutlineColor: WidgetStateProperty.all(Colors.transparent),
    ),
    listTileTheme: ListTileThemeData(
      tileColor: Colors.transparent,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
      subtitleTextStyle: TextStyle(fontSize: 12, color: subtle),
      titleTextStyle: TextStyle(fontSize: 14, color: text),
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: SegmentedButton.styleFrom(
        backgroundColor: sub,
        selectedBackgroundColor: isDark ? const Color(0xFF3D2D1E) : const Color(0xFFE8DDD0),
        foregroundColor: subtle,
        selectedForegroundColor: text,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        side: BorderSide(color: border),
        textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: surface,
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      titleTextStyle: TextStyle(
        color: text,
        fontSize: 15,
        fontWeight: FontWeight.w600,
      ),
    ),
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(14)),
      ),
      dragHandleColor: border,
    ),
  );
}
