"""
Project: DTD - ta_app.py v2.0.0
Improved with watchdog, better error handling, and stats
"""

import ta_config as config
from ta_logger import get_logger

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

try:
    from machine import WDT
except ImportError:
    WDT = None

from ta_ui import UI
from ta_radio_433 import Radio, STATE_PRESENT, STATE_ABSENT, STATE_UNKNOWN

logger = get_logger()

class TaApp:
    def __init__(self, tft=None, ui=None, radio=None):
        logger.info("Initialisation de l'application DTD v{}".format(
            config.MAIN["VERSION_NO"]), "app")
        
        self.ui = ui if ui else UI()
        self.radio = radio if radio else Radio()
        self.states = {dd_id: STATE_UNKNOWN for dd_id in config.RADIO["GROUP_IDS"]}
        self.testing_id = None
        self.req_period = max(150, config.RADIO.get("POLL_PERIOD_MS", 1500))
        
        # Watchdog
        self.wdt = None
        if config.MAIN.get("WATCHDOG_ENABLED", True) and WDT:
            try:
                self.wdt = WDT(timeout=config.MAIN.get("WATCHDOG_TIMEOUT_MS", 30000))
                logger.info("Watchdog activé", "app")
            except Exception as e:
                logger.error("Erreur watchdog: {}".format(e), "app")
        
        # Compteurs et stats
        self.loop_count = 0
        self.error_count = 0
        
        self.ui.status("Initialisation terminée")
        logger.info("Application initialisée", "app")

    def feed_watchdog(self):
        """Alimente le watchdog"""
        if self.wdt:
            try:
                self.wdt.feed()
            except Exception as e:
                logger.error("Erreur feed watchdog: {}".format(e), "app")

    def set_testing(self, dd_id: int | None) -> None:
        self.testing_id = dd_id
        try:
            if dd_id is None:
                self.ui.progress(None)
            else:
                self.ui.progress(int(dd_id), color=config.COLORS["C_PGR"])
        except Exception as e:
            logger.warning("set_testing erreur UI: {}".format(e), "app")

    def _refresh_ui(self) -> None:
        """Met à jour l'affichage avec dirty tracking"""
        try:
            for idx, dd_id in enumerate(config.RADIO["GROUP_IDS"]):
                st = self.states.get(dd_id, STATE_UNKNOWN)
                
                if st == STATE_PRESENT:
                    state = True
                elif st == STATE_ABSENT:
                    state = False
                else:
                    state = None
                
                self.ui.update_group(idx, state=state)
            
            # Rafraîchir uniquement les éléments modifiés
            if config.UI.get("DIRTY_TRACKING", True):
                self.ui.render_dirty()
        except Exception as e:
            logger.error("_refresh_ui erreur: {}".format(e), "app")
            self.error_count += 1

    def _update_states(self) -> None:
        """Lit les états depuis la radio"""
        try:
            for st in self.radio.poll_status():
                self.states[st.dd_id] = st.state
        except Exception as e:
            logger.error("_update_states erreur: {}".format(e), "app")
            self.error_count += 1

    async def _handle_testing(self) -> None:
        """Gère la requête rapide si test actif"""
        try:
            if self.testing_id:
                self.radio.request_status(self.testing_id)
                await asyncio.sleep_ms(self.req_period)
            else:
                await asyncio.sleep_ms(200)
        except Exception as e:
            logger.error("_handle_testing erreur: {}".format(e), "app")

    async def _print_stats(self):
        """Tâche périodique pour afficher les statistiques"""
        if not config.MAIN.get("DEBUG_MODE", False):
            return
        
        while True:
            await asyncio.sleep_ms(30000)  # Toutes les 30s
            
            try:
                logger.info("=== STATISTIQUES ===", "app")
                logger.info("Boucles: {} | Erreurs: {}".format(
                    self.loop_count, self.error_count), "app")
                
                if self.radio.stats:
                    logger.info("Radio: {}".format(self.radio.stats), "app")
                
                # Stats logger
                log_stats = logger.get_stats()
                logger.info("Logs: {}".format(log_stats), "app")
                
            except Exception as e:
                logger.error("Erreur affichage stats: {}".format(e), "app")

    async def run(self) -> None:
        """Boucle principale de l'application"""
        logger.info("Démarrage de la boucle principale", "app")
        
        # Lancer tâche stats si debug
        if config.MAIN.get("DEBUG_MODE", False):
            asyncio.create_task(self._print_stats())
        
        while True:
            try:
                # Alimenter watchdog
                self.feed_watchdog()
                
                # Traitement principal
                self._update_states()
                self._refresh_ui()
                await self._handle_testing()
                
                self.loop_count += 1
                
            except Exception as e:
                logger.critical("Erreur critique dans boucle principale: {}".format(e), "app")
                self.error_count += 1
                self.ui.status("ERREUR: {}".format(str(e)[:30]))
                await asyncio.sleep_ms(1000)

logger.info("ta_app.py v2.0.0 chargé", "app")
