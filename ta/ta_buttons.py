"""
project : DTD
Component : TA
file: ta_buttons.py 

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/JOM52/esp32-airsens-v2

v1.0.0 : 22.10.2025 --> first prototype
v2.0.0 : 24.10.2025 --> non-blocking button handling with state machine
"""

import time
import ta_config as config
from ta_logger import get_logger

try:
    import machine
except ImportError:
    machine = None

logger = get_logger()

__MOD_NAME__ = "ta_buttons.py"
__VERSION__ = "2.0.0"

logger.info("{} version {} du {}".format(__MOD_NAME__, __VERSION__, config.MAIN["VERSION_DATE"]), "buttons")


class Buttons:
    """
    Gestionnaire de boutons non-bloquant avec détection appui court/long.
    
    Version améliorée qui utilise une machine à états pour détecter
    les appuis courts et longs SANS bloquer la boucle principale.
    
    Usage:
        buttons = Buttons()
        
        # Dans la boucle principale:
        event = buttons.check()
        if event == "up_short":
            # Action sur appui court du bouton UP
        elif event == "down_long":
            # Action sur appui long du bouton DOWN
    
    Événements générés:
        - "up_short": Appui court sur bouton UP
        - "up_long": Appui long sur bouton UP
        - "down_short": Appui court sur bouton DOWN
        - "down_long": Appui long sur bouton DOWN
        - None: Aucun événement
    """
    
    def __init__(self):
        """Initialise le gestionnaire de boutons"""
        # Configuration
        self.pins = {
            "up": config.HARDWARE["BUTTONS"]["PIN_UP"],
            "down": config.HARDWARE["BUTTONS"]["PIN_DOWN"]
        }
        self.debounce = config.BUTTONS["DEBOUNCE_MS"]
        self.long_ms = config.BUTTONS["LONG_MS"]
        
        # États actuels (1 = relâché, 0 = appuyé)
        self.state = {"up": 1, "down": 1}
        
        # Timestamps du dernier changement d'état
        self.last_change = {"up": 0, "down": 0}
        
        # Timestamps du début d'appui
        self.press_start = {"up": 0, "down": 0}
        
        # Drapeaux indiquant qu'un événement "long" a déjà été déclenché
        self.long_fired = {"up": False, "down": False}
        
        # Initialiser les pins hardware
        if machine:
            self._pins = {
                name: machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP) 
                for name, pin in self.pins.items()
            }
            logger.info("Boutons initialisés sur pins: UP={}, DOWN={}".format(
                self.pins["up"], self.pins["down"]), "buttons")
        else:
            self._pins = {}
            logger.warning("Mode simulation: hardware non disponible", "buttons")
    
    def _read(self, name):
        """
        Lit l'état d'un bouton (0 = appuyé, 1 = relâché).
        
        Args:
            name: Nom du bouton ("up" ou "down")
        
        Returns:
            int: 0 si appuyé, 1 si relâché
        """
        if machine and name in self._pins:
            return self._pins[name].value()
        return 1  # Simulation: toujours relâché
    
    def check(self):
        """
        Vérifie l'état des boutons et retourne un événement si détecté.
        
        Cette méthode doit être appelée régulièrement (toutes les 10-50ms)
        dans la boucle principale. Elle ne bloque jamais.
        
        Returns:
            str or None: Événement détecté ("up_short", "up_long", etc.) ou None
        """
        now = time.ticks_ms()
        event = None
        
        for name in ("up", "down"):
            val = self._read(name)
            
            # Détection front descendant (appui du bouton)
            if val == 0 and self.state[name] == 1:
                # Vérifier le debounce
                if time.ticks_diff(now, self.last_change[name]) > self.debounce:
                    # Début d'un nouvel appui
                    self.press_start[name] = now
                    self.long_fired[name] = False
                    self.state[name] = 0
                    self.last_change[name] = now
                    logger.debug("Bouton {} appuyé".format(name), "buttons")
            
            # Bouton maintenu appuyé: vérifier appui long
            elif val == 0 and self.state[name] == 0:
                if not self.long_fired[name]:
                    duration = time.ticks_diff(now, self.press_start[name])
                    if duration >= self.long_ms:
                        # Appui long détecté
                        event = "{}_long".format(name)
                        self.long_fired[name] = True
                        logger.debug("Bouton {} appui long détecté".format(name), "buttons")
            
            # Détection front montant (relâchement du bouton)
            elif val == 1 and self.state[name] == 0:
                # Vérifier le debounce
                if time.ticks_diff(now, self.last_change[name]) > self.debounce:
                    duration = time.ticks_diff(now, self.press_start[name])
                    
                    # Si pas d'événement "long" déjà déclenché et durée courte
                    if not self.long_fired[name] and duration < self.long_ms:
                        # Appui court détecté
                        event = "{}_short".format(name)
                        logger.debug("Bouton {} appui court détecté ({}ms)".format(
                            name, duration), "buttons")
                    
                    # Réinitialiser l'état
                    self.state[name] = 1
                    self.last_change[name] = now
                    logger.debug("Bouton {} relâché".format(name), "buttons")
        
        return event
    
    def reset(self):
        """
        Réinitialise tous les états (utile après traitement d'événement).
        """
        for name in ("up", "down"):
            self.state[name] = 1
            self.long_fired[name] = False
        logger.debug("États des boutons réinitialisés", "buttons")
    
    def get_state(self, name):
        """
        Retourne l'état actuel d'un bouton.
        
        Args:
            name: Nom du bouton ("up" ou "down")
        
        Returns:
            int: 0 si appuyé, 1 si relâché, -1 si nom invalide
        """
        if name in self.state:
            return self.state[name]
        return -1
    
    def is_pressed(self, name):
        """
        Vérifie si un bouton est actuellement appuyé.
        
        Args:
            name: Nom du bouton ("up" ou "down")
        
        Returns:
            bool: True si appuyé, False sinon
        """
        return self.get_state(name) == 0


# Test du module si exécuté directement
if __name__ == "__main__":
    print("=== Test du module ta_buttons.py ===")
    buttons = Buttons()
    
    print("Appuyez sur les boutons pour tester...")
    print("Appui court: < {}ms".format(buttons.long_ms))
    print("Appui long: >= {}ms".format(buttons.long_ms))
    print("Ctrl+C pour quitter\n")
    
    try:
        while True:
            ev = buttons.check()
            if ev:
                print("Événement détecté: {}".format(ev))
            time.sleep_ms(10)
    except KeyboardInterrupt:
        print("\nTest terminé")
