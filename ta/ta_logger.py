"""
project : DTD
Component : TA
file: ta_logger.py

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/JOM52/esp32-dtd

v2.0.0 : 24.10.2025 --> système de logging amélioré
"""

import time

class Logger:
    """
    Système de logging avec niveaux et timestamps.
    
    Niveaux disponibles:
        DEBUG (0): Informations de débogage détaillées
        INFO (1): Informations générales
        WARNING (2): Avertissements
        ERROR (3): Erreurs non critiques
        CRITICAL (4): Erreurs critiques
    
    Usage:
        logger = Logger(level=Logger.INFO)
        logger.info("Application démarrée", "main")
        logger.warning("Timeout détecté", "radio")
        logger.error("Erreur communication: {}".format(e), "radio")
    """
    
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    
    LEVEL_NAMES = ["DEBUG", "INFO", "WARN", "ERROR", "CRIT"]
    
    def __init__(self, level=INFO, enable_colors=False):
        """
        Initialise le logger.
        
        Args:
            level: Niveau minimum de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_colors: Active les couleurs ANSI (non supporté sur tous les terminaux)
        """
        self.level = level
        self.enable_colors = enable_colors
        self.handlers = []
        self.message_count = {
            self.DEBUG: 0,
            self.INFO: 0,
            self.WARNING: 0,
            self.ERROR: 0,
            self.CRITICAL: 0
        }
    
    def _format_msg(self, level, msg, module=""):
        """
        Formate un message de log.
        
        Format: [timestamp][LEVEL][module] message
        """
        timestamp = time.ticks_ms()
        level_str = self.LEVEL_NAMES[level]
        
        if module:
            return "[{:08d}][{}][{}] {}".format(timestamp, level_str, module, msg)
        else:
            return "[{:08d}][{}] {}".format(timestamp, level_str, msg)
    
    def log(self, level, msg, module=""):
        """
        Enregistre un message si le niveau est suffisant.
        
        Args:
            level: Niveau du message
            msg: Message à enregistrer
            module: Nom du module source (optionnel)
        """
        if level >= self.level:
            formatted = self._format_msg(level, msg, module)
            print(formatted)
            
            # Incrémenter compteur
            self.message_count[level] += 1
            
            # Appeler les handlers custom si définis
            for handler in self.handlers:
                try:
                    handler.write(formatted)
                except Exception as e:
                    print("[logger] Erreur handler: {}".format(e))
    
    def debug(self, msg, module=""):
        """Log niveau DEBUG"""
        self.log(self.DEBUG, msg, module)
    
    def info(self, msg, module=""):
        """Log niveau INFO"""
        self.log(self.INFO, msg, module)
    
    def warning(self, msg, module=""):
        """Log niveau WARNING"""
        self.log(self.WARNING, msg, module)
    
    def error(self, msg, module=""):
        """Log niveau ERROR"""
        self.log(self.ERROR, msg, module)
    
    def critical(self, msg, module=""):
        """Log niveau CRITICAL"""
        self.log(self.CRITICAL, msg, module)
    
    def add_handler(self, handler):
        """
        Ajoute un handler custom pour traiter les logs.
        Le handler doit avoir une méthode write(message).
        """
        self.handlers.append(handler)
    
    def get_stats(self):
        """
        Retourne les statistiques de logging.
        
        Returns:
            dict: Nombre de messages par niveau
        """
        return self.message_count.copy()
    
    def print_stats(self):
        """Affiche les statistiques de logging"""
        print("\n=== STATISTIQUES DE LOGGING ===")
        total = sum(self.message_count.values())
        print("Total de messages: {}".format(total))
        for level, name in enumerate(self.LEVEL_NAMES):
            count = self.message_count[level]
            if count > 0:
                print("  {}: {}".format(name, count))
        print("================================\n")


class FileHandler:
    """
    Handler pour écrire les logs dans un fichier.
    
    Usage:
        handler = FileHandler("/logs.txt", max_size=10240)
        logger.add_handler(handler)
    """
    
    def __init__(self, filepath, max_size=10240):
        """
        Args:
            filepath: Chemin du fichier de log
            max_size: Taille max en octets avant rotation
        """
        self.filepath = filepath
        self.max_size = max_size
    
    def write(self, message):
        """Écrit un message dans le fichier"""
        try:
            # Vérifier la taille
            try:
                import os
                size = os.stat(self.filepath)[6]
                if size > self.max_size:
                    # Rotation simple: suppression du fichier
                    os.remove(self.filepath)
            except Exception:
                pass  # Fichier n'existe pas encore
            
            # Écrire le message
            with open(self.filepath, 'a') as f:
                f.write(message + '\n')
        except Exception as e:
            print("[FileHandler] Erreur écriture: {}".format(e))


class MemoryHandler:
    """
    Handler pour garder les N derniers logs en mémoire.
    Utile pour affichage sur l'écran.
    
    Usage:
        handler = MemoryHandler(max_lines=50)
        logger.add_handler(handler)
        # Plus tard:
        recent_logs = handler.get_logs()
    """
    
    def __init__(self, max_lines=50):
        """
        Args:
            max_lines: Nombre max de lignes gardées en mémoire
        """
        self.max_lines = max_lines
        self.buffer = []
    
    def write(self, message):
        """Ajoute un message au buffer"""
        self.buffer.append(message)
        if len(self.buffer) > self.max_lines:
            self.buffer.pop(0)
    
    def get_logs(self, n=None):
        """
        Récupère les N derniers logs.
        
        Args:
            n: Nombre de logs à récupérer (None = tous)
        
        Returns:
            list: Liste des messages
        """
        if n is None:
            return self.buffer.copy()
        return self.buffer[-n:]
    
    def clear(self):
        """Vide le buffer"""
        self.buffer.clear()


# Instance globale par défaut
_default_logger = None

def get_logger(level=Logger.INFO):
    """
    Retourne l'instance globale du logger (singleton).
    
    Args:
        level: Niveau de log (utilisé uniquement à la première création)
    
    Returns:
        Logger: Instance du logger
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = Logger(level=level)
    return _default_logger


# Fonctions de convenance pour utiliser le logger global
def debug(msg, module=""):
    get_logger().debug(msg, module)

def info(msg, module=""):
    get_logger().info(msg, module)

def warning(msg, module=""):
    get_logger().warning(msg, module)

def error(msg, module=""):
    get_logger().error(msg, module)

def critical(msg, module=""):
    get_logger().critical(msg, module)
