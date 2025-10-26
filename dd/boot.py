# boot.py - Configuration système pour Détecteur Distant
# Exécuté avant main.py - Garder MINIMAL et RAPIDE

import esp
import esp32
from machine import freq

# ==================== OPTIMISATIONS SYSTÈME ====================

# 1. Désactiver logs de debug ESP32 (gain de perf)
esp.osdebug(None)

# 2. Fréquence CPU (optionnel - par défaut 160MHz est bon)
# freq(240000000)  # 240MHz si besoin de plus de puissance
# freq(80000000)   # 80MHz si économie d'énergie prioritaire

# 3. Désactiver WiFi/Bluetooth (économie énergie critique)
try:
    import network
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    sta_if.active(False)
    ap_if.active(False)
except:
    pass

# 4. Désactiver Bluetooth si disponible
try:
    import bluetooth
    bt = bluetooth.BLE()
    bt.active(False)
except:
    pass

# ==================== CONFIGURATION SÉCURITÉ ====================

# 5. Pins critiques en état sûr AVANT main.py
try:
    from machine import Pin
    # Exemple : forcer pin sensible à LOW au boot
    # safe_pin = Pin(XX, Pin.OUT)
    # safe_pin.value(0)
except:
    pass

# ==================== FIN BOOT.PY ====================
# Durée totale doit rester < 50ms
# main.py démarre immédiatement après