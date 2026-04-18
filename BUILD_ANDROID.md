# Build Android APK — Spark

À faire sur ton PC (Windows/Mac/Linux x64).

## Prérequis

- Flutter SDK installé → https://docs.flutter.dev/get-started/install
- Java JDK 17 installé → https://adoptium.net
- Android SDK (via Android Studio ou ligne de commande)

Vérifie que tout est OK :
```bash
flutter doctor
```

---

## 1. Récupérer le projet

```bash
git clone <url-du-repo> spark_bot
cd spark_bot/flutter_app
```

## 2. Placer google-services.json

Copie le fichier `google-services.json` (déjà sur le Pi à `/home/protoboy/ProtoDocs/google-services.json`)
dans :
```
flutter_app/android/app/google-services.json
```

## 3. Configurer Gradle pour Firebase

Le projet utilise le format Kotlin DSL (`.kts`). Les fichiers sont déjà configurés dans le repo :
- `android/settings.gradle.kts` — contient le plugin `com.google.gms.google-services`
- `android/app/build.gradle.kts` — applique le plugin

Rien à faire manuellement.

## 4. Installer les dépendances Flutter

```bash
cd flutter_app
flutter pub get
```

## 5. Compiler l'APK

```bash
flutter build apk --release
```

L'APK généré sera dans :
```
flutter_app/build/app/outputs/flutter-apk/app-release.apk
```

## 6. Installer sur Android

Branche ton téléphone en USB (mode développeur activé) :
```bash
flutter install
```

Ou transfère l'APK manuellement et installe-le.

---

## Notes

- `applicationId` : `com.example.spark`
- Firebase project : `spark-668cb`
- Le service account backend est déjà en place sur le Pi (`~/.local/share/spark/firebase-service-account.json`)
- Le Pi envoie les push via Firebase Admin SDK — pas besoin de le toucher
