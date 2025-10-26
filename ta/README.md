# DTD v2.0.0 - Détecteur de Tension Distant

Version améliorée avec gestion d'erreurs robuste, logging, watchdog et optimisations.

## 🆕 Nouveautés v2.0.0

### Robustesse
- ✅ **Watchdog Timer**: Redémarrage automatique en cas de blocage
- ✅ **Retry avec backoff exponentiel**: 3 tentatives avec délai progressif
- ✅ **Gestion d'erreurs améliorée**: Try/except dans toutes les fonctions critiques
- ✅ **Validation de configuration**: Vérification au démarrage

### Performance
- ✅ **Dirty Tracking UI**: Rafraîchit uniquement les éléments modifiés
- ✅ **Buffers pré-alloués**: Réduit la fragmentation mémoire
- ✅ **Optimisation radio**: Timeout de simulation réduit (1.5s → 150ms)

### Fonctionnalités
- ✅ **Système de logging structuré**: Niveaux DEBUG/INFO/WARNING/ERROR/CRITICAL
- ✅ **Statistiques radio**: Taux de succès, RSSI, timeouts
- ✅ **Boutons non-bloquants**: Machine à états pour détection court/long
- ✅ **Mode debug**: Métriques et statistiques détaillées

## 📁 Structure des Fichiers

```
dtd_improved/
├── boot.py              # Init système (watchdog, config)
├── main.py              # Point d'entrée
├── ta_config.py         # Configuration centrale + validation
├── ta_logger.py         # Système de logging (NOUVEAU)
├── ta_app.py            # Logique application
├── ta_ui.py             # Interface graphique
├── ta_buttons.py        # Gestion boutons (non-bloquant)
├── ta_radio_433.py      # Communication radio
└── README.md            # Ce fichier
```

## 🚀 Installation

### 1. Flasher MicroPython
```bash
esptool.py --chip esp32s3 erase_flash
esptool.py --chip esp32s3 write_flash -z 0x0 firmware.bin
```

### 2. Uploader les fichiers
```bash
# Copier tous les fichiers
mpremote cp *.py :
mpremote cp utils/*.py :utils/
```

### 3. Configuration
Éditer `ta_config.py` selon vos besoins :
```python
RADIO = {
    "SIMULATE": False,           # True pour tests sans radio
    "GROUP_IDS": [1, 2, 3, 4, 5],  # IDs des détecteurs
}

MAIN = {
    "DEBUG_MODE": False,         # True pour logs détaillés
    "WATCHDOG_ENABLED": True,    # False pour désactiver
}
```

## 🎮 Utilisation

### Démarrage
Le système démarre automatiquement au boot. Les 5 détecteurs sont affichés avec leur état (ON/OFF/UNK).

### Boutons
- **UP court**: Cycle entre les détecteurs
- **DOWN long**: Test du détecteur sélectionné

### Modes

#### Mode Normal
```python
RADIO["SIMULATE"] = False
```
Communication réelle avec les modules GT38 via UART.

#### Mode Simulation
```python
RADIO["SIMULATE"] = True
```
États générés aléatoirement, idéal pour tests sans matériel.

#### Mode Debug
```python
MAIN["DEBUG_MODE"] = True
```
Affiche les statistiques toutes les 30 secondes :
- Nombre de boucles exécutées
- Taux d'erreurs
- Statistiques radio (TX/RX/Erreurs/RSSI)
- Stats de logging

## 🔧 Configuration Avancée

### Timeouts et Retry
```python
RADIO = {
    "REPLY_TIMEOUT_MS": 500,
    "RETRY": {
        "MAX_RETRIES": 3,
        "TIMEOUT_BASE_MS": 500,
        "TIMEOUT_MULTIPLIER": 1.5,
        "BACKOFF_ENABLED": True,
    }
}
```

### Watchdog
```python
MAIN = {
    "WATCHDOG_ENABLED": True,
    "WATCHDOG_TIMEOUT_MS": 30000,  # 30 secondes
}
```

### UI
```python
UI = {
    "DIRTY_TRACKING": True,    # Optimisation rafraîchissement
    "REFRESH_RATE_MS": 100,    # Période de rafraîchissement
}
```

## 📊 Monitoring

### Logs
Les logs sont affichés sur le port série avec format:
```
[timestamp][LEVEL][module] message
```

Exemple:
```
[00012345][INFO][radio] Module GT38 détecté
[00023456][WARN][radio] Tentative 2/3 échouée pour DD 3
[00034567][ERROR][app] _update_states erreur: timeout
```

### Statistiques Radio
En mode debug, affichage toutes les 30s:
```
TX:150 RX:145 Err:5 TO:2 RSSI:92.3 Rate:96.7%
```

## 🐛 Dépannage

### Problème: Redémarrages fréquents
```python
# Désactiver temporairement le watchdog
MAIN["WATCHDOG_ENABLED"] = False
```

### Problème: Erreurs UART
1. Vérifier connexions (TX=17, RX=18, SET=4)
2. Vérifier alimentation GT38 (3.3V, GND)
3. Activer logs debug:
```python
MAIN["DEBUG_MODE"] = True
```

### Problème: UI lente
```python
# Désactiver dirty tracking si problèmes
UI["DIRTY_TRACKING"] = False
```

### Problème: Mémoire insuffisante
```python
# Réduire la taille du buffer
ui = UI(buffer_size=32*32*2)
```

## 📈 Performance

### Mesures Typiques
- **Boot**: < 3 secondes
- **Polling cycle**: 1.5 secondes
- **Réponse DD**: 50-150ms
- **Rafraîchissement UI**: < 20ms
- **Heap libre**: > 100KB

### Consommation
- **Normal**: ~80mA @ 160MHz
- **Performance**: ~120mA @ 240MHz
- **Économie**: ~50mA @ 80MHz

## 🔄 Mises à Jour

### Changelog v2.0.0
- Watchdog timer pour robustesse
- Système de logging structuré
- Retry avec backoff exponentiel
- Dirty tracking UI
- Boutons non-bloquants
- Statistiques radio
- Validation de configuration
- Mode debug avec métriques

### Migration depuis v1.x
1. Sauvegarder votre `ta_config.py`
2. Remplacer tous les fichiers
3. Adapter les paramètres de config si nécessaire
4. Tester en mode simulation d'abord

## 📝 Notes de Développement

### Ajout d'un Détecteur
```python
# Dans ta_config.py
RADIO["GROUP_IDS"] = [1, 2, 3, 4, 5, 6]  # Ajouter 6
```

### Personnalisation Couleurs
```python
COLORS = {
    "C_ON": st7789.color565(0, 255, 0),    # RGB
    "C_OFF": st7789.color565(255, 0, 0),
}
```

### Logs vers Fichier
```python
from ta_logger import FileHandler
logger.add_handler(FileHandler("/logs.txt", max_size=10240))
```

## 📧 Support

- **Email**: jom52.dev@gmail.com
- **GitHub**: https://github.com/JOM52/esp32-dtd
- **Issues**: Créer une issue sur GitHub

## 📄 Licence

Propriétaire - Tous droits réservés © 2025

---

**Version**: 2.0.0  
**Date**: 24.10.2025  
**Auteur**: jom52
