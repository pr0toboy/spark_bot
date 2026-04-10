class Skill {
  final String name;
  final String instructions;
  final bool isPreset;

  Skill({required this.name, required this.instructions, this.isPreset = false});

  factory Skill.fromJson(Map<String, dynamic> json) {
    return Skill(
      name: json['name'] as String,
      instructions: json['instructions'] as String,
      isPreset: json['is_preset'] as bool? ?? false,
    );
  }
}
