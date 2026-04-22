# Fix72 — App Android

## Ouvrir dans Android Studio

1. Lance Android Studio
2. File → Open → sélectionne ce dossier `fix72-android/`
3. Attends que Gradle synchronise (barre en bas)

## Ajouter ton icône

Remplace les fichiers dans `app/src/main/res/mipmap-*/` :
- `ic_launcher.png` et `ic_launcher_round.png`
- Tailles : hdpi=72px, mdpi=48px, xhdpi=96px, xxhdpi=144px, xxxhdpi=192px

Ou utilise : **Android Studio → clic droit sur `res/` → New → Image Asset**
Importe ton logo Fix72 et Android génère toutes les tailles automatiquement.

## Créer le keystore (signature)

Dans Android Studio, ouvre un terminal (View → Tool Windows → Terminal) :

```bash
keytool -genkeypair -v \
  -keystore fix72-release.keystore \
  -alias fix72 \
  -keyalg RSA -keysize 2048 \
  -validity 10000
```

Remplis les infos demandées (nom, organisation, ville = Le Mans, pays = FR).
**Garde ce fichier précieusement — tu en auras besoin pour toutes les mises à jour.**

## Configurer la signature

Copie `keystore.properties.example` → `keystore.properties` et remplis :

```
storeFile=fix72-release.keystore
storePassword=le_mot_de_passe_choisi
keyAlias=fix72
keyPassword=le_mot_de_passe_choisi
```

## Générer l'AAB (Play Store)

```
Build → Generate Signed Bundle / APK → Android App Bundle → Release
```

## Générer l'APK (installation directe)

```
Build → Generate Signed Bundle / APK → APK → Release
```

## Fonctionnalités de l'app

- Charge fix72.com dans une WebView
- Splash screen rouge Fix72 (1.5s)
- Barre de progression pendant le chargement
- Glisser vers le bas pour rafraîchir
- Numéros de téléphone ouverts dans l'app Téléphone
- Emails ouverts dans l'app Mail
- Page "Pas de connexion" avec bouton Réessayer
- Bouton Retour navigue dans l'historique du site
