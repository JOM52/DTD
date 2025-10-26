# Guide d'Installation DTD v2.0.0

## Prérequis Matériel

### Terminal Afficheur (TA)
- **Carte**: LilyGO T-Display-S3
- **Écran**: 320x170 IPS (ST7789)
- **CPU**: ESP32-S3 @ 160-240MHz
- **Mémoire**: 8MB Flash + 2MB PSRAM
- **Module Radio**: GT38 433MHz (UART)

### Détecteurs Distants (DD)
- **Carte**: ESP32-WROOM-32
- **Module Radio**: 433MHz
- **Capteur**: GPIO + réseau diviseur tension

## Prérequis Logiciels

### Outils
```bash
pip install esptool mpremote
```

### Firmware MicroPython
Télécharger depuis: https://micropython.org/download/
- **TA**: ESP32-S3 (latest stable)
- **DD**: ESP32 (latest stable)

## Installation TA (Terminal Afficheur)

### Étape 1: Connexion USB
```bash
# Identifier le port série
# Linux/Mac:
ls /dev/tty.*
# Windows:
# Vérifier dans Gestionnaire de périphériques

# Exemple de port détecté:
# /dev/ttyUSB0 (Linux)
# /dev/tty.usbserial-XXX (Mac)
# COM3 (Windows)
```

### Étape 2: Flash MicroPython
```bash
# Effacer la flash
esptool.py --chip esp32s3 --port /dev/ttyUSB0 erase_flash

# Flasher MicroPython
esptool.py --chip esp32s3 --port /dev/ttyUSB0 \
  write_flash -z 0x0 ESP32_GENERIC_S3-20240222-v1.22.2.bin

# Attendre ~30 secondes
```

### Étape 3: Vérification
```bash
# Se connecter au REPL
mpremote connect /dev/ttyUSB0

# Tester Python
>>> print("Hello DTD")
Hello DTD
>>> import sys
>>> sys.implementation
(name='micropython', version=(1, 22, 2), ...)

# Quitter: Ctrl+] ou Ctrl+X
```

### Étape 4: Upload Fichiers
```bash
cd dtd_improved/

# Copier tous les fichiers Python
mpremote connect /dev/ttyUSB0 cp boot.py :boot.py
mpremote connect /dev/ttyUSB0 cp main.py :main.py
mpremote connect /dev/ttyUSB0 cp ta_*.py :

# Créer dossier utils et copier drivers
mpremote connect /dev/ttyUSB0 mkdir :utils
mpremote connect /dev/ttyUSB0 cp utils/tft_config.py :utils/
mpremote connect /dev/ttyUSB0 cp utils/vga1_8x16.py :utils/

# Vérifier
mpremote connect /dev/ttyUSB0 ls
```

### Étape 5: Configuration
```bash
# Éditer ta_config.py selon vos besoins
nano ta_config.py

# Paramètres importants:
RADIO["SIMULATE"] = True  # Commencer en simulation
RADIO["GROUP_IDS"] = [1, 2, 3, 4, 5]  # IDs de vos DDs
MAIN["DEBUG_MODE"] = True  # Pour les premiers tests

# Sauvegarder et copier
mpremote connect /dev/ttyUSB0 cp ta_config.py :ta_config.py
```

### Étape 6: Test
```bash
# Redémarrer
mpremote connect /dev/ttyUSB0 reset

# Observer les logs
mpremote connect /dev/ttyUSB0

# Logs attendus:
# [boot] WiFi désactivé
# [boot] Bluetooth désactivé
# [boot] Watchdog activé (30s)
# [config] Validation OK
# [main] Démarrage DTD v2.0.0
# [ui] UI initialisée (320x170)
# [radio] Mode simulation actif
# [app] Application initialisée
```

## Installation DD (Détecteur Distant)

### Note
Le code des DD n'est pas inclus dans cette archive.
Contactez le développeur pour le firmware DD.

### Connexions DD Typiques
```
ESP32-WROOM-32:
- VCC (3.3V) → Alimentation
- GND → Masse
- GPIO4 → Module Radio TX
- GPIO5 → Module Radio RX
- GPIO12 → Détection tension (via diviseur)
```

## Câblage TA ↔ GT38

### Connexions UART
```
T-Display-S3     GT38 (433MHz)
GPIO17 (TX)  →   RXD
GPIO18 (RX)  ←   TXD
GPIO4        →   SET (mode control)
3V3          →   VCC
GND          →   GND
```

### Schéma
```
     ┌─────────────┐         ┌──────────┐
     │T-Display-S3 │         │  GT38    │
     │             │         │  Radio   │
     │         TX17├────────→┤RXD       │
     │         RX18├←────────┤TXD       │
     │        SET4 ├────────→┤SET       │
     │             │         │          │
     │        3V3  ├────────→┤VCC       │
     │        GND  ├────────→┤GND       │
     └─────────────┘         └──────────┘
```

## Configuration Avancée

### Mode Production
Après tests réussis, activer mode réel:
```python
# ta_config.py
RADIO["SIMULATE"] = False
MAIN["DEBUG_MODE"] = False
```

### Optimisation Performance
```python
# CPU haute performance
APP["POWER"]["CPU_FREQ_NORMAL"] = 240000000

# Ou économie d'énergie
APP["POWER"]["CPU_FREQ_NORMAL"] = 80000000
```

### Logs vers Fichier
```python
# Ajouter dans main.py
from ta_logger import FileHandler
logger.add_handler(FileHandler("/logs.txt", max_size=10240))
```

## Dépannage Installation

### Problème: Port non trouvé
```bash
# Linux: Ajouter user au groupe dialout
sudo usermod -a -G dialout $USER
# Déconnexion/reconnexion requise

# Mac: Installer drivers CP210x si nécessaire
# Windows: Installer drivers CH340/CP210x
```

### Problème: Échec flash
```bash
# Maintenir bouton BOOT pendant connexion
# Ou forcer mode download:
esptool.py --chip esp32s3 --port /dev/ttyUSB0 \
  --before default_reset --after hard_reset \
  write_flash ...
```

### Problème: Import errors
```bash
# Vérifier structure:
mpremote connect /dev/ttyUSB0 ls
# Doit contenir:
# boot.py
# main.py
# ta_*.py
# utils/

# Si manquant, re-uploader
```

### Problème: Écran noir
1. Vérifier alimentation USB (>500mA)
2. Tester backlight:
```python
from machine import Pin, PWM
pwm = PWM(Pin(38), freq=1000)
pwm.duty_u16(32768)  # 50%
```

### Problème: Watchdog reset
```bash
# Désactiver temporairement
# ta_config.py:
MAIN["WATCHDOG_ENABLED"] = False
```

## Test Final

### Checklist
- [ ] Écran affiche "DTD (v2.0.0)"
- [ ] 5 boîtes pour les détecteurs visibles
- [ ] États affichés (ON/OFF/UNK)
- [ ] Barre de statut en bas "Prêt"
- [ ] Pas d'erreurs dans les logs
- [ ] Bouton UP responsive
- [ ] Bouton DOWN responsive

### Test Boutons
```
Appui court UP → Changement sélection
Appui long DOWN → Test DD activé (barre orange)
```

### Test Simulation
En mode SIMULATE=True:
- États changent aléatoirement
- Pas d'erreurs timeout
- Loop count augmente

### Test Réel
En mode SIMULATE=False:
- Module GT38 détecté au boot
- Communication avec DDs
- États réels affichés

## Support Post-Installation

### Logs Utiles
```bash
# Monitoring continu
mpremote connect /dev/ttyUSB0

# Ou rediriger vers fichier
mpremote connect /dev/ttyUSB0 > dtd_logs.txt 2>&1
```

### Mise à Jour
```bash
# Sauvegarder config
mpremote connect /dev/ttyUSB0 cat :ta_config.py > ta_config_backup.py

# Uploader nouvelle version
mpremote connect /dev/ttyUSB0 cp ta_*.py :

# Restaurer config si nécessaire
mpremote connect /dev/ttyUSB0 cp ta_config_backup.py :ta_config.py
```

### Sauvegarde Complète
```bash
# Télécharger tous les fichiers
mkdir backup_$(date +%Y%m%d)
cd backup_$(date +%Y%m%d)
mpremote connect /dev/ttyUSB0 cat :boot.py > boot.py
mpremote connect /dev/ttyUSB0 cat :main.py > main.py
# etc...
```

## Aide

### Documentation
- README.md: Guide utilisateur
- CHANGELOG.md: Historique versions
- Code source: Docstrings détaillées

### Contact
- **Email**: jom52.dev@gmail.com
- **GitHub**: https://github.com/JOM52/esp32-dtd
- **Issues**: Créer une issue sur GitHub

---

**Installation réussie?** Consultez README.md pour l'utilisation! 🎉
