"""
project : DTD
Component : TA
file: main.py 

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/JOM52/dtd

v1.0.0 : 22.10.2025 --> first prototype
v2.0.0 : 24.10.2025 --> improved version with better error handling
"""

try:
    import uasyncio as asyncio
except Exception:
    import asyncio

import ta_config as config
from ta_app import TaApp
from ta_logger import get_logger

logger = get_logger()

# Valider la configuration au démarrage
logger.info("Validation de la configuration...", "main")
config.ConfigValidator.validate_or_exit()

async def _demo(app):
    """Mode démo pour tester les détecteurs"""
    while True:
        for d in config.RADIO["GROUP_IDS"]:
            logger.debug("Test DD {}".format(d), "demo")
            app.set_testing(d)
            await asyncio.sleep_ms(1500)
        app.set_testing(None)
        await asyncio.sleep_ms(1200)

async def _main():
    logger.info("="*60, "main")
    logger.info("Démarrage DTD v{} du {}".format(
        config.MAIN["VERSION_NO"], 
        config.MAIN["VERSION_DATE"]), "main")
    logger.info("Mode simulation: {}".format(config.RADIO["SIMULATE"]), "main")
    logger.info("Mode debug: {}".format(config.MAIN.get("DEBUG_MODE", False)), "main")
    logger.info("="*60, "main")
    
    try:
        app = TaApp()
        
        # Démarrer la tâche principale
        app_task = asyncio.create_task(app.run())
        
        # Démarrer la démo si en mode simulation
        if config.RADIO["SIMULATE"]:
            demo_task = asyncio.create_task(_demo(app))
            await asyncio.gather(app_task, demo_task)
        else:
            await app_task
            
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur", "main")
    except Exception as e:
        logger.critical("Erreur fatale: {}".format(e), "main")
        raise
    finally:
        logger.info("Application terminée", "main")

# Point d'entrée
if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except Exception as e:
        logger.critical("Échec du démarrage: {}".format(e), "main")
        import sys
        sys.exit(1)
