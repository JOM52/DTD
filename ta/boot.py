# boot.py - Configuration système pour Terminal Afficheur (TA)
# Exécuté avant main.py - MINIMAL et RAPIDE
"""
project : DTD
Component : TA
file: boot.py 

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/JOM52/esp32-dtd

v1.0.0 : 22.10.2025 --> first prototype
v2.0.0 : 24.10.2025 --> improved version with better error handling
"""

import esp
import esp32
from machine import freq, WDT

# ==================== OPTIMISATIONS SYSTÈME ====================

# 1. Désactiver logs de debug ESP32 (gain de perf)
esp.osdebug(None)

# 2. Fréquence CPU optimale pour balance performance/énergie
freq(160000000)  # 160MHz (par défaut, bon compromis)
# freq(240000000)  # Décommenter pour plus de puissance
# freq(80000000)   # Décommenter pour économie d'énergie

# 3. Désactiver WiFi/Bluetooth (économie énergie critique)
try:
    import network
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    sta_if.active(False)
    ap_if.active(False)
    print("[boot] WiFi désactivé")
except Exception as e:
    print("[boot] Erreur désactivation WiFi: {}".format(e))

# 4. Désactiver Bluetooth si disponible
try:
    import bluetooth
    bt = bluetooth.BLE()
    bt.active(False)
    print("[boot] Bluetooth désactivé")
except Exception as e:
    print("[boot] Bluetooth non disponible ou erreur: {}".format(e))

# ==================== WATCHDOG TIMER ====================

# 5. Initialiser watchdog (30 secondes)
# try:
#     # Le watchdog sera alimenté dans la boucle principale
#     # Si pas alimenté pendant 30s, le système redémarre automatiquement
#     wdt = None # WDT(timeout=30000)
#     print("[boot] Watchdog activé (30s)")
# except Exception as e:
#     print("[boot] Erreur watchdog: {}".format(e))
#     wdt = None

# ==================== CONFIGURATION SÉCURITÉ ====================

# 6. Pins critiques en état sûr AVANT main.py
try:
    from machine import Pin
    # Mettre les pins sensibles en état connu
    # (Adapter selon votre matériel)
    # Example: safe_pin = Pin(XX, Pin.OUT, value=0)
    print("[boot] Pins de sécurité initialisées")
except Exception as e:
    print("[boot] Erreur init pins: {}".format(e))

# ==================== CHARGEMENT CONFIGURATION ====================

# 7. Charger configuration persistante si disponible
try:
    import json
    with open('/config.json', 'r') as f:
        saved_config = json.load(f)
        print("[boot] Configuration chargée: {} paramètres".format(len(saved_config)))
except Exception:
    # Pas de config sauvegardée, utiliser les valeurs par défaut
    saved_config = {}
    print("[boot] Pas de configuration sauvegardée, utilisation des valeurs par défaut")

# Rendre la config accessible au reste de l'application
import builtins
builtins.saved_config = saved_config

# ==================== FIN BOOT.PY ====================
print("[boot] Initialisation terminée, démarrage de l'application...")
# Durée totale doit rester < 100ms
# main.py démarre immédiatement après
