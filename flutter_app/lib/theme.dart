import 'package:flutter/material.dart';

// ─── Palette Notion ──────────────────────────────────────────────────────────

const kNotionTextLight   = Color(0xFF37352F);
const kNotionTextDark    = Color(0xFFE3E2E0);
const kNotionGrayLight   = Color(0xFF9B9A97);
const kNotionGrayDark    = Color(0xFF787774);
const kNotionBorderLight = Color(0xFFE3E2E0);
const kNotionBorderDark  = Color(0xFF373737);
const kNotionBgLight     = Color(0xFFF7F6F3);
const kNotionBgDark      = Color(0xFF191919);
const kNotionCardLight   = Color(0xFFFFFFFF);
const kNotionCardDark    = Color(0xFF252525);
const kNotionSubLight    = Color(0xFFF1F1EF);
const kNotionSubDark     = Color(0xFF2F2F2F);
const kNotionAccent      = Color(0xFF2383E2);
const kNotionRed         = Color(0xFFEB5757);
const kNotionGreen       = Color(0xFF0F7B6C);
const kNotionOrange      = Color(0xFFD9730D);

// Pre-computed opacity variants (avoids Color.withOpacity() allocations on hot paths)
const kNotionGreenBg     = Color(0x260F7B6C); // kNotionGreen @ 15%
const kNotionGreenBorder = Color(0x660F7B6C); // kNotionGreen @ 40%

// ─── Helpers ─────────────────────────────────────────────────────────────────

/// Thin divider line for AppBar.bottom, matching the Notion border style.
PreferredSize notionAppBarDivider(BuildContext context) => PreferredSize(
      preferredSize: const Size.fromHeight(1),
      child: Divider(height: 1, color: Theme.of(context).colorScheme.outline),
    );

// ─── Theme builder ───────────────────────────────────────────────────────────

ThemeData buildNotionTheme(Brightness brightness) {
  final isDark  = brightness == Brightness.dark;
  final bg      = isDark ? kNotionBgDark      : kNotionBgLight;
  final surface = isDark ? kNotionCardDark    : kNotionCardLight;
  final text    = isDark ? kNotionTextDark    : kNotionTextLight;
  final subtle  = isDark ? kNotionGrayDark    : kNotionGrayLight;
  final border  = isDark ? kNotionBorderDark  : kNotionBorderLight;
  final sub     = isDark ? kNotionSubDark     : kNotionSubLight;

  final scheme = ColorScheme(
    brightness: brightness,
    primary: text,
    onPrimary: isDark ? kNotionBgDark : Colors.white,
    secondary: subtle,
    onSecondary: surface,
    error: kNotionRed,
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
    cardTheme: CardTheme(
      elevation: 0,
      color: surface,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: border),
      ),
    ),
    dividerTheme: DividerThemeData(color: border, space: 1, thickness: 1),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: text, width: 1.5),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      fillColor: surface,
      filled: true,
      hintStyle: TextStyle(color: subtle, fontSize: 14),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: text,
        textStyle: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: text,
        foregroundColor: isDark ? kNotionBgDark : Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
        textStyle: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: surface,
      elevation: 0,
      shadowColor: Colors.transparent,
      surfaceTintColor: Colors.transparent,
      indicatorColor: sub,
      iconTheme: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return IconThemeData(color: text, size: 22);
        }
        return IconThemeData(color: subtle, size: 22);
      }),
      height: 58,
    ),
    chipTheme: ChipThemeData(
      backgroundColor: sub,
      selectedColor: isDark ? const Color(0xFF454442) : const Color(0xFFE3E2E0),
      labelStyle: TextStyle(color: text, fontSize: 13),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(6),
        side: BorderSide(color: border),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      side: BorderSide(color: border),
    ),
    tabBarTheme: TabBarTheme(
      labelColor: text,
      unselectedLabelColor: subtle,
      indicatorColor: text,
      dividerColor: border,
      indicatorSize: TabBarIndicatorSize.tab,
      labelStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
      unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w400, fontSize: 13),
      tabAlignment: TabAlignment.fill,
    ),
    floatingActionButtonTheme: FloatingActionButtonThemeData(
      backgroundColor: text,
      foregroundColor: isDark ? kNotionBgDark : Colors.white,
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: text,
      contentTextStyle: TextStyle(
        color: isDark ? kNotionBgDark : Colors.white,
        fontSize: 13,
      ),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      behavior: SnackBarBehavior.floating,
    ),
    progressIndicatorTheme: ProgressIndicatorThemeData(
      color: text,
      linearTrackColor: border,
      circularTrackColor: border,
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((s) =>
          s.contains(WidgetState.selected) ? Colors.white : subtle),
      trackColor: WidgetStateProperty.resolveWith((s) =>
          s.contains(WidgetState.selected) ? text : border),
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
        selectedBackgroundColor: isDark ? const Color(0xFF454442) : const Color(0xFFE3E2E0),
        foregroundColor: subtle,
        selectedForegroundColor: text,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
        side: BorderSide(color: border),
        textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      ),
    ),
    dialogTheme: DialogTheme(
      backgroundColor: surface,
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      titleTextStyle: TextStyle(
        color: text,
        fontSize: 15,
        fontWeight: FontWeight.w600,
      ),
    ),
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
      ),
      dragHandleColor: border,
    ),
  );
}
