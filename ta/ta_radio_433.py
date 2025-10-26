"""
project : DTD
Component : TA
file: ta_radio_433.py

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/JOM52/esp32-dtd

v1.1.0 : 23.10.2025 --> simulation complète + ready-for-GT38
v2.0.0 : 24.10.2025 --> retry logic, stats, queue, improved error handling
"""

import ta_config as config
from ta_logger import get_logger

try:
    from machine import UART, Pin
except Exception:
    class Pin:
        OUT = 1
        def __init__(self, *a, **k): pass
        def value(self, v): pass
    class UART:
        def __init__(self, *a, **k): pass
        def write(self, b): return len(b)
        def any(self): return 0
        def read(self, n): return b""

try:
    import uasyncio as asyncio
except Exception:
    import asyncio

import time
try:
    import urandom as _rand
except Exception:
    import random as _rand

logger = get_logger()

# Aliases de config
HW = config.HARDWARE
UART_C = HW["UART_RADIO"]
PIN_SET = UART_C["PIN_GT38_SET"]

RAD = config.RADIO
SIMULATE = bool(RAD.get("SIMULATE", True))
GROUP_IDS = RAD["GROUP_IDS"]
POLL_PERIOD_MS = int(RAD["POLL_PERIOD_MS"])
REPLY_TIMEOUT_MS = int(RAD["REPLY_TIMEOUT_MS"])

STATE_UNKNOWN = RAD["STATE_UNKNOWN"]
STATE_PRESENT = RAD["STATE_PRESENT"]
STATE_ABSENT = RAD["STATE_ABSENT"]

FRAME = RAD["FRAME"]
START_BYTE = FRAME["START_BYTE"]
END_BYTE = FRAME["END_BYTE"]
PROTO_VER = FRAME["PROTO_VER"]
MAX_LEN = FRAME["MAX_LEN"]

RETRY_CFG = RAD["RETRY"]

# Outils
def _ticks():
    return time.ticks_ms()

def _diff(a, b):
    return time.ticks_diff(a, b)

def _sleep_ms(ms):
    time.sleep_ms(ms)

def _randbits(n=1):
    try:
        return _rand.getrandbits(n)
    except Exception:
        return int(_rand.random() * (1 << n))

# Trames
CMD_PING = 0x10
CMD_GET_STS = 0x20
CMD_SET_MODE = 0x30

def _chk(ver, cmd, grp, payload):
    s = (ver ^ cmd ^ (grp & 0xFF) ^ len(payload)) & 0xFF
    for b in payload:
        s ^= (b & 0xFF)
    return s & 0xFF

def _mk_frame(cmd, gid=0, payload=b""):
    if payload is None:
        payload = b""
    if len(payload) > (MAX_LEN - 7):
        raise ValueError("Payload trop long")
    ver = PROTO_VER & 0xFF
    gid = gid & 0xFF
    ln = len(payload) & 0xFF
    chk = _chk(ver, cmd, gid, payload)
    return bytes([START_BYTE, ver, cmd, gid, ln]) + payload + bytes([chk, END_BYTE])

def _parse_frame(buf):
    if not buf or len(buf) < 7:
        return None
    if buf[0] != START_BYTE or buf[-1] != END_BYTE:
        return None
    ver = buf[1]
    cmd = buf[2]
    gid = buf[3]
    ln = buf[4]
    if 5 + ln + 2 != len(buf):
        return None
    payload = buf[5:5+ln]
    chk = buf[5+ln]
    if _chk(ver, cmd, gid, payload) != chk:
        return None
    return (cmd, gid, payload)

# Statistiques
class RadioStats:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.tx_count = 0
        self.rx_count = 0
        self.tx_errors = 0
        self.rx_errors = 0
        self.timeouts = 0
        self.avg_rssi = 0
        self.last_update = _ticks()
    
    def update_tx(self, success):
        self.tx_count += 1
        if not success:
            self.tx_errors += 1
    
    def update_rx(self, success, rssi=0):
        self.rx_count += 1
        if success:
            self.avg_rssi = (self.avg_rssi * 0.9) + (rssi * 0.1)
        else:
            self.rx_errors += 1
    
    def update_timeout(self):
        self.timeouts += 1
    
    def get_success_rate(self):
        total = self.tx_count + self.rx_count
        if total == 0:
            return 0.0
        errors = self.tx_errors + self.rx_errors
        return 100.0 * (1.0 - errors / total)
    
    def __str__(self):
        return "TX:{} RX:{} Err:{} TO:{} RSSI:{:.1f} Rate:{:.1f}%".format(
            self.tx_count, self.rx_count,
            self.tx_errors + self.rx_errors,
            self.timeouts, self.avg_rssi,
            self.get_success_rate())

# Structure DDStatus
class DDStatus:
    __slots__ = ("dd_id", "state", "battery", "rssi", "flags")
    def __init__(self, dd_id, state, battery=100, rssi=0, flags=0):
        self.dd_id = int(dd_id)
        self.state = int(state)
        self.battery = int(battery)
        self.rssi = int(rssi)
        self.flags = int(flags)

# Radio améliorée
class Radio:
    def __init__(self):
        self.simulate = SIMULATE
        self._tick = 0
        self._sim_states = {gid: (STATE_PRESENT if (_randbits(1) == 1) else STATE_ABSENT) for gid in GROUP_IDS}
        
        # Stats
        self.stats = RadioStats() if RAD.get("STATS_ENABLED", True) else None
        
        # Cache pour frames
        self._frame_cache = {}
        
        # Buffers pré-alloués
        self._rx_buffer = bytearray(MAX_LEN)
        
        # Pin SET
        try:
            self.pin_set = Pin(PIN_SET, Pin.OUT)
            self.run_mode()
        except Exception as e:
            logger.warning("Erreur init pin SET: {}".format(e), "radio")
            self.pin_set = None
        
        # UART réel si non-simulation
        self.uart = None
        if not self.simulate:
            try:
                self.uart = UART(UART_C["INDEX"],
                               baudrate=UART_C["BAUD"],
                               tx=UART_C["TX"],
                               rx=UART_C["RX"],
                               timeout=UART_C["TIMEOUT_MS"])
                logger.info("UART initialisé", "radio")
                
                # Vérifier hardware
                if not self.check_hardware():
                    logger.error("Module GT38 introuvable, basculement en simulation", "radio")
                    self.simulate = True
            except Exception as e:
                logger.error("Erreur init UART: {}, basculement en simulation".format(e), "radio")
                self.simulate = True
        
        if self.simulate:
            logger.info("Mode simulation actif", "radio")
    
    def run_mode(self):
        if self.pin_set:
            self.pin_set.value(1)
    
    def config_mode(self):
        if self.pin_set:
            self.pin_set.value(0)
    
    def _write(self, data: bytes):
        if self.simulate or not self.uart:
            return len(data)
        try:
            written = self.uart.write(data)
            if self.stats:
                self.stats.update_tx(written == len(data))
            return written
        except Exception as e:
            logger.error("Erreur écriture UART: {}".format(e), "radio")
            if self.stats:
                self.stats.update_tx(False)
            return 0
    
    def _read_all(self) -> bytes:
        if self.simulate or not self.uart:
            return b""
        try:
            n = self.uart.any()
            if not n:
                return b""
            data = self.uart.read(n) or b""
            if self.stats and data:
                self.stats.update_rx(True)
            return data
        except Exception as e:
            logger.error("Erreur lecture UART: {}".format(e), "radio")
            if self.stats:
                self.stats.update_rx(False)
            return b""
    
    def _exchange_with_retry(self, cmd, gid, payload=b""):
        """Envoie avec retry exponentiel"""
        for attempt in range(RETRY_CFG["MAX_RETRIES"]):
            timeout = int(RETRY_CFG["TIMEOUT_BASE_MS"] *
                         (RETRY_CFG["TIMEOUT_MULTIPLIER"] ** attempt))
            
            result = self._exchange(cmd, gid, payload, timeout)
            if result:
                return result
            
            logger.debug("Tentative {}/{} échouée pour DD {}".format(
                attempt + 1, RETRY_CFG["MAX_RETRIES"], gid), "radio")
            
            if RETRY_CFG["BACKOFF_ENABLED"] and attempt < RETRY_CFG["MAX_RETRIES"] - 1:
                backoff = RETRY_CFG["BACKOFF_MS"] * (attempt + 1)
                _sleep_ms(backoff)
        
        logger.warning("Échec après {} tentatives pour DD {}".format(
            RETRY_CFG["MAX_RETRIES"], gid), "radio")
        return None
    
    def _exchange(self, cmd, gid, payload=b"", timeout_ms=REPLY_TIMEOUT_MS):
        if self.simulate:
            if cmd == CMD_PING:
                _sleep_ms(50 + (_randbits(6) & 0x3F))
                return (CMD_PING, gid, b"OK")
            elif cmd == CMD_GET_STS:
                _sleep_ms(50 + (_randbits(7)))  # Réduit de 1.5s à ~150ms max
                st = self._sim_states.get(gid, STATE_UNKNOWN)
                if (_randbits(4) == 0) and st != STATE_UNKNOWN:
                    st = STATE_PRESENT if (st == STATE_ABSENT) else STATE_ABSENT
                    self._sim_states[gid] = st
                return (CMD_GET_STS, gid, bytes([st]))
            elif cmd == CMD_SET_MODE:
                return (CMD_SET_MODE, gid, b"ACK")
            return None
        
        # Matériel réel
        frame = _mk_frame(cmd, gid, payload)
        self._write(frame)
        
        t0 = _ticks()
        buf = b""
        while _diff(_ticks(), t0) < timeout_ms:
            chunk = self._read_all()
            if chunk:
                buf += chunk
                s = buf.find(bytes([START_BYTE]))
                e = buf.find(bytes([END_BYTE]), s+1)
                if s >= 0 and e > s:
                    pkt = buf[s:e+1]
                    parsed = _parse_frame(pkt)
                    if parsed:
                        return parsed
            _sleep_ms(5)
        
        if self.stats:
            self.stats.update_timeout()
        return None
    
    def poll_status(self):
        out = []
        self._tick += 1
        period = max(1, int(POLL_PERIOD_MS // 200) or 1)
        if (self._tick % period) == 0:
            for gid in GROUP_IDS:
                if self.simulate:
                    st = self._sim_states.get(gid, STATE_UNKNOWN)
                    batt = 75 + (_randbits(5) % 25)
                    rssi = 110 - (_randbits(5) % 30)
                else:
                    resp = self._exchange_with_retry(CMD_GET_STS, gid)
                    if resp and resp[0] == CMD_GET_STS and len(resp[2]) == 1:
                        st = resp[2][0]
                    else:
                        st = STATE_UNKNOWN
                    batt = 90
                    rssi = 90
                out.append(DDStatus(gid, st, batt, rssi, 0))
        return out
    
    def request_status(self, dd_id: int):
        if dd_id not in GROUP_IDS:
            return STATE_UNKNOWN
        resp = self._exchange_with_retry(CMD_GET_STS, dd_id)
        if resp and resp[0] == CMD_GET_STS and len(resp[2]) == 1:
            return resp[2][0]
        return STATE_UNKNOWN
    
    def ping(self) -> bool:
        resp = self._exchange(CMD_PING, 0)
        return bool(resp and resp[0] == CMD_PING and resp[2] == b"OK")
    
    def check_hardware(self):
        """Vérifie que le module GT38 répond"""
        if self.simulate:
            return True
        
        for _ in range(3):
            if self.ping():
                logger.info("Module GT38 détecté", "radio")
                return True
            _sleep_ms(100)
        
        logger.error("Module GT38 introuvable", "radio")
        return False
    
    def get_stats(self):
        """Retourne les statistiques"""
        return self.stats

logger.info("ta_radio_433.py v2.0.0 chargé", "radio")
