import array
from collections import deque
from datetime import datetime
import json
import math
import os
import random
import socket
import sys
import threading
import pygame

# --- CONFIGURAÇÕES GERAIS ---
WIDTH, HEIGHT = 1200, 700
FPS = 60
CONFIG_FILE = "arcade_smash_config.json"
RECORDS_FILE = "arcade_records.json"
NET_PORT = 5555

# Paleta Arcade
BG_COLOR = (16, 18, 30)
GRID_COLOR = (34, 42, 68)
ARCADE_NEON_PINK = (255, 75, 155)
ARCADE_NEON_CYAN = (65, 225, 255)
ARCADE_NEON_YELLOW = (255, 215, 55)
PANEL_COLOR = (26, 30, 48)
PANEL_BORDER = (95, 115, 165)
BUTTON_IDLE = (42, 50, 76)
BUTTON_HOVER = (225, 70, 140)
MAIN_STAGE_COLOR = (72, 82, 112)
PLATFORM_COLOR = (95, 195, 235)
P1_COLOR = (255, 85, 105)
P2_COLOR = (85, 185, 255)
HITBOX_COLOR = (255, 225, 65)
TEXT_COLOR = (245, 248, 255)
MUTED_TEXT = (155, 170, 200)
COMBO_COLOR = (255, 215, 65)
CPU_COLOR = (110, 245, 165)
METER_READY_COLOR = (255, 220, 60)
PARRY_COLOR = (120, 255, 240)

# Física
GRAVITY = 0.55
MAX_FALL_SPEED = 13.5
FAST_FALL_SPEED = 18.0
GROUND_FRICTION = 0.82
AIR_FRICTION = 0.94

DEFAULT_P1_CONTROLS = {
    "left": pygame.K_a,
    "right": pygame.K_d,
    "down": pygame.K_s,
    "jump": pygame.K_w,
    "up": pygame.K_w,
    "attack": pygame.K_f,
    "dodge": pygame.K_e,
    "grab": pygame.K_g,
    "ultimate": pygame.K_q,
    "cancel": pygame.K_c,
}

DEFAULT_P2_CONTROLS = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "down": pygame.K_DOWN,
    "jump": pygame.K_UP,
    "up": pygame.K_UP,
    "attack": pygame.K_RCTRL,
    "dodge": pygame.K_RSHIFT,
    "grab": pygame.K_m,
    "ultimate": pygame.K_RALT,
    "cancel": pygame.K_n,
}

REMAP_ACTIONS = [
    ("jump", "Pulo"),
    ("attack", "Ataque / Smash"),
    ("dodge", "Escudo / Esquiva"),
    ("grab", "Agarrão"),
    ("ultimate", "Final Smash (100%)"),
    ("cancel", "Roman Cancel (50%)"),
]

# Configuração dos 3 níveis de dificuldade da CPU
CPU_DIFFICULTIES = {
    "Fácil": {
        "decision_range": (16, 28),
        "attack_cooldown_range": (28, 44),
        "jump_cooldown": 32,
        "attack_chance": 0.42,
        "attack_reach_x": 95,
        "attack_reach_y": 75,
        "recovery_jump_vy": -0.5,
        "idle_chance": 0.25,
    },
    "Média": {
        "decision_range": (6, 14),
        "attack_cooldown_range": (14, 24),
        "jump_cooldown": 22,
        "attack_chance": 0.75,
        "attack_reach_x": 115,
        "attack_reach_y": 85,
        "recovery_jump_vy": -2.0,
        "idle_chance": 0.08,
    },
    "Difícil": {
        "decision_range": (2, 6),
        "attack_cooldown_range": (7, 13),
        "jump_cooldown": 14,
        "attack_chance": 0.94,
        "attack_reach_x": 132,
        "attack_reach_y": 98,
        "recovery_jump_vy": -3.2,
        "idle_chance": 0.0,
    },
}
CPU_DIFFICULTY_ORDER = ["Fácil", "Média", "Difícil"]
ARCADE_TOWER_DIFFICULTIES = ["Fácil", "Média", "Média", "Difícil"]

# 4 Cenários com paleta própria, layout e mecânicas dinâmicas
STAGE_PRESETS = [
    {
        "name": "Arena Clássica",
        "subtitle": "Layout Battlefield • 3 plataformas equilibradas",
        "hazard_desc": "Sem perigos ambientais • Ledge grab nas pontas",
        "bg_tint": (16, 18, 30),
        "grid_tint": (34, 42, 68),
        "stage_color": (72, 82, 112),
        "plat_color": (95, 195, 235),
        "wind_force": 0.0,
        "platforms": [
            (220, 535, 760, 42, False, 0.0, 0.0, 0.0),
            (275, 405, 210, 16, True, 0.0, 0.0, 0.0),
            (715, 405, 210, 16, True, 0.0, 0.0, 0.0),
            (495, 275, 210, 16, True, 0.0, 0.0, 0.0),
        ],
    },
    {
        "name": "Torres Altas",
        "subtitle": "Combate vertical • Plataformas laterais elevatórias",
        "hazard_desc": "Plataformas laterais oscilam verticalmente",
        "bg_tint": (14, 24, 38),
        "grid_tint": (28, 52, 78),
        "stage_color": (64, 92, 124),
        "plat_color": (85, 225, 210),
        "wind_force": 0.0,
        "platforms": [
            (190, 545, 820, 42, False, 0.0, 0.0, 0.0),
            (230, 405, 185, 16, True, 0.0, 42.0, 0.032),
            (785, 405, 185, 16, True, 0.0, -42.0, 0.032),
            (370, 275, 180, 16, True, 0.0, 0.0, 0.0),
            (650, 275, 180, 16, True, 0.0, 0.0, 0.0),
        ],
    },
    {
        "name": "Ponte Neon",
        "subtitle": "Palco amplo • Rajadas de vento lateral na arena",
        "hazard_desc": "Vento alterna a direção a cada poucos segundos",
        "bg_tint": (24, 15, 36),
        "grid_tint": (52, 32, 74),
        "stage_color": (88, 68, 118),
        "plat_color": (235, 115, 215),
        "wind_force": 0.24,
        "platforms": [
            (160, 540, 880, 40, False, 0.0, 0.0, 0.0),
            (475, 415, 250, 16, True, 0.0, 0.0, 0.0),
            (310, 305, 165, 16, True, 0.0, 0.0, 0.0),
            (725, 305, 165, 16, True, 0.0, 0.0, 0.0),
        ],
    },
    {
        "name": "Caldeira Sísmica",
        "subtitle": "Palco compacto • Plataforma central deslizante",
        "hazard_desc": "Base menor com KOs rápidos e plataforma móvel",
        "bg_tint": (30, 16, 22),
        "grid_tint": (64, 34, 46),
        "stage_color": (112, 66, 76),
        "plat_color": (255, 165, 75),
        "wind_force": 0.0,
        "platforms": [
            (270, 535, 660, 42, False, 0.0, 0.0, 0.0),
            (490, 400, 220, 16, True, 130.0, 0.0, 0.028),
            (310, 280, 170, 16, True, 0.0, 0.0, 0.0),
            (720, 280, 170, 16, True, 0.0, 0.0, 0.0),
        ],
    },
]


def get_local_ip():
    """Obtém o IP local na rede para facilitar o lobby LAN."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


class NetSession:
    """Gerencia sala Multiplayer TCP (Host = P1, Client = P2) usando JSON por linha."""

    def __init__(self):
        self.role = None  # None | 'host' | 'client'
        self.server_sock = None
        self.conn = None
        self.connected = False
        self.status_msg = "Desconectado"
        self.host_ip = get_local_ip()
        self.lock = threading.Lock()
        self.latest_msg = None
        self.running = False

    def close(self):
        self.running = False
        self.connected = False
        for s in (self.conn, self.server_sock):
            if s:
                try:
                    s.close()
                except OSError:
                    pass
        self.conn = None
        self.server_sock = None
        self.role = None
        with self.lock:
            self.latest_msg = None
        self.status_msg = "Desconectado"

    def start_host(self, port=NET_PORT):
        self.close()
        self.role = "host"
        self.host_ip = get_local_ip()
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("0.0.0.0", port))
            srv.listen(1)
            self.server_sock = srv
            self.running = True
            self.status_msg = f"Aguardando P2 em {self.host_ip}:{port}..."
            threading.Thread(target=self._accept_loop, daemon=True).start()
            return True
        except OSError as exc:
            self.status_msg = f"Erro ao criar sala: {exc}"
            self.role = None
            return False

    def _accept_loop(self):
        try:
            conn, addr = self.server_sock.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.conn = conn
            self.connected = True
            self.status_msg = f"Jogador 2 conectado ({addr[0]})!"
            self._recv_loop(conn)
        except OSError:
            if self.running:
                self.status_msg = "Sala encerrada."
                self.connected = False

    def connect_client(self, ip_str, port=NET_PORT):
        self.close()
        self.role = "client"
        target_ip = ip_str.strip() or "127.0.0.1"
        self.status_msg = f"Conectando a {target_ip}:{port}..."
        self.running = True
        threading.Thread(
            target=self._connect_worker, args=(target_ip, port), daemon=True
        ).start()

    def _connect_worker(self, ip, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(4.0)
            sock.connect((ip, port))
            sock.settimeout(None)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.conn = sock
            self.connected = True
            self.status_msg = f"Conectado à sala ({ip})!"
            self._recv_loop(sock)
        except OSError as exc:
            self.status_msg = f"Falha ao conectar: {exc}"
            self.connected = False
            self.running = False

    def _recv_loop(self, sock):
        buf = b""
        while self.running:
            try:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode("utf-8"))
                        with self.lock:
                            self.latest_msg = data
                    except (ValueError, UnicodeDecodeError):
                        pass
            except OSError:
                break
        self.connected = False
        if self.running:
            self.status_msg = "Conexão perdida com o outro jogador."

    def send(self, payload):
        if not self.connected or not self.conn:
            return
        try:
            raw = (json.dumps(payload, separators=(",", ":")) + "\n").encode(
                "utf-8"
            )
            self.conn.sendall(raw)
        except OSError:
            self.connected = False
            self.status_msg = "Conexão encerrada."

    def pop_latest(self):
        with self.lock:
            msg = self.latest_msg
            self.latest_msg = None
            return msg


class RemoteKeys:
    """Emula o dicionário keys[...] do pygame para comandos vindos da rede."""

    def __init__(self, controls_map):
        self.controls = controls_map
        self.held = {
            "left": False,
            "right": False,
            "down": False,
            "up": False,
            "attack": False,
            "dodge": False,
        }

    def apply_state(self, state_dict):
        if not isinstance(state_dict, dict):
            return
        for k in self.held:
            self.held[k] = bool(state_dict.get(k, False))

    def __getitem__(self, key_code):
        for act, code in self.controls.items():
            if code == key_code and act in self.held:
                return self.held[act]
        return False


def load_saved_config():
    """Carrega preferências e teclas salvas em disco de forma segura."""
    defaults = {
        "volume": 0.6,
        "cpu_enabled": False,
        "cpu_difficulty": "Média",
        "stage_idx": 0,
        "training_mode": False,
        "last_join_ip": "127.0.0.1",
        "p1_controls": dict(DEFAULT_P1_CONTROLS),
        "p2_controls": dict(DEFAULT_P2_CONTROLS),
    }
    if not os.path.exists(CONFIG_FILE):
        return defaults
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        if not isinstance(data, dict):
            return defaults
        vol = data.get("volume", defaults["volume"])
        if isinstance(vol, (int, float)):
            defaults["volume"] = max(0.0, min(1.0, round(float(vol), 2)))
        defaults["cpu_enabled"] = bool(
            data.get("cpu_enabled", defaults["cpu_enabled"])
        )
        diff = data.get("cpu_difficulty", defaults["cpu_difficulty"])
        if diff in CPU_DIFFICULTIES:
            defaults["cpu_difficulty"] = diff
        st = data.get("stage_idx", defaults["stage_idx"])
        if isinstance(st, int):
            defaults["stage_idx"] = st % len(STAGE_PRESETS)
        defaults["training_mode"] = bool(
            data.get("training_mode", defaults["training_mode"])
        )
        j_ip = data.get("last_join_ip", defaults["last_join_ip"])
        if isinstance(j_ip, str) and j_ip.strip():
            defaults["last_join_ip"] = j_ip.strip()[:40]
        for key_name, default_map in (
            ("p1_controls", DEFAULT_P1_CONTROLS),
            ("p2_controls", DEFAULT_P2_CONTROLS),
        ):
            saved_map = data.get(key_name)
            if isinstance(saved_map, dict):
                merged = dict(default_map)
                for act, code in saved_map.items():
                    if act in merged and isinstance(code, int):
                        merged[act] = code
                merged["up"] = merged["jump"]
                defaults[key_name] = merged
    except (OSError, ValueError, TypeError):
        pass
    return defaults


def save_config(
    volume,
    cpu_enabled,
    cpu_difficulty,
    stage_idx,
    training_mode,
    p1_controls,
    p2_controls,
    last_join_ip="127.0.0.1",
):
    """Salva preferências locais e teclas em JSON."""
    payload = {
        "volume": max(0.0, min(1.0, round(float(volume), 2))),
        "cpu_enabled": bool(cpu_enabled),
        "cpu_difficulty": cpu_difficulty
        if cpu_difficulty in CPU_DIFFICULTIES
        else "Média",
        "stage_idx": int(stage_idx) % len(STAGE_PRESETS),
        "training_mode": bool(training_mode),
        "last_join_ip": str(last_join_ip).strip() or "127.0.0.1",
        "p1_controls": {k: int(v) for k, v in p1_controls.items()},
        "p2_controls": {k: int(v) for k, v in p2_controls.items()},
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, indent=2, ensure_ascii=False)
    except OSError:
        pass


def load_arcade_records():
    """Carrega recordes da Torre Arcade (melhor tempo e maior combo)."""
    defaults = {
        "best_time_sec": None,
        "best_time_char": "",
        "best_combo": 0,
        "best_combo_char": "",
        "clears": 0,
    }
    if not os.path.exists(RECORDS_FILE):
        return defaults
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        if isinstance(data, dict):
            defaults.update(data)
    except (OSError, ValueError, TypeError):
        pass
    return defaults


def save_arcade_records(records):
    try:
        with open(RECORDS_FILE, "w", encoding="utf-8") as fp:
            json.dump(records, fp, indent=2, ensure_ascii=False)
    except OSError:
        pass


class SoundFX:
    """Sintetiza efeitos sonoros curtos no pygame sem depender de arquivos."""

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            init_info = pygame.mixer.get_init()
            sample_rate = init_info[0] if init_info else 22050
            self.sounds["blip"] = self._make_tone(
                sample_rate, 520, 0.05, "square", 0.25
            )
            self.sounds["swing"] = self._make_sweep(
                sample_rate, 260, 120, 0.07, 0.25
            )
            self.sounds["hit"] = self._make_sweep(
                sample_rate, 180, 58, 0.12, 0.45
            )
            self.sounds["smash"] = self._make_sweep(
                sample_rate, 240, 42, 0.20, 0.55
            )
            self.sounds["dodge"] = self._make_sweep(
                sample_rate, 340, 620, 0.09, 0.25
            )
            self.sounds["parry"] = self._make_sweep(
                sample_rate, 680, 1180, 0.14, 0.45
            )
            self.sounds["shield_break"] = self._make_sweep(
                sample_rate, 850, 90, 0.30, 0.52
            )
            self.sounds["grab"] = self._make_sweep(
                sample_rate, 420, 210, 0.11, 0.35
            )
            self.sounds["ultimate"] = self._make_sweep(
                sample_rate, 220, 880, 0.24, 0.55
            )
            self.sounds["cancel"] = self._make_sweep(
                sample_rate, 500, 920, 0.10, 0.38
            )
            self.sounds["pickup"] = self._make_sweep(
                sample_rate, 440, 760, 0.10, 0.32
            )
            self.sounds["ko"] = self._make_sweep(
                sample_rate, 320, 45, 0.34, 0.5
            )
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def _make_tone(self, sample_rate, freq, duration, wave_type, gain):
        n_samples = max(1, int(sample_rate * duration))
        buf = array.array("h")
        for i in range(n_samples):
            t = i / sample_rate
            env = 1.0 - (i / n_samples)
            phase = 2.0 * math.pi * freq * t
            if wave_type == "square":
                val = 1.0 if math.sin(phase) >= 0 else -1.0
            else:
                val = math.sin(phase)
            buf.append(int(max(-32767, min(32767, val * env * gain * 32767))))
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _make_sweep(self, sample_rate, f_start, f_end, duration, gain):
        n_samples = max(1, int(sample_rate * duration))
        buf = array.array("h")
        phase = 0.0
        for i in range(n_samples):
            progress = i / n_samples
            env = 1.0 - progress
            freq = f_start + (f_end - f_start) * progress
            phase += 2.0 * math.pi * freq / sample_rate
            val = math.sin(phase)
            buf.append(int(max(-32767, min(32767, val * env * gain * 32767))))
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play(self, name, volume=0.6):
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd:
            snd.set_volume(max(0.0, min(1.0, float(volume))))
            snd.play()


def _build_moveset(prefix, base_dmg=1.0, speed_mult=1.0, heavy=False):
    """Gera um moveset equilibrado e único para cada personagem."""
    lag_bonus = 2 if heavy else 0
    return {
        "neutral": {
            "name": f"Jab {prefix}",
            "input": "Ataque parado",
            "role": "Rápido para interromper e iniciar combos",
            "duration": 16 + lag_bonus,
            "active_start": 4,
            "active_end": 8,
            "end_lag": 4 + lag_bonus,
            "dash_vx": 0.0,
            "dash_vy": 0.0,
            "hb_size": (44, 28),
            "hb_offset": (-4, 0),
            "damage": round(7.0 * base_dmg, 1),
            "base_kb": 3.5,
            "scaling_kb": 0.06,
            "angle_deg": 25,
            "hitstop": 3,
        },
        "side": {
            "name": f"Side Smash {prefix}",
            "input": "Esq/Dir + Ataque (Segure p/ carregar)",
            "role": "Golpe forte carregável + onda de assinatura",
            "duration": 24 + lag_bonus,
            "active_start": 7,
            "active_end": 13,
            "end_lag": 7 + lag_bonus,
            "dash_vx": round(3.2 * speed_mult, 2),
            "dash_vy": 0.0,
            "hb_size": (64, 34),
            "hb_offset": (-4, 4),
            "damage": round(14.0 * base_dmg, 1),
            "base_kb": 8.0,
            "scaling_kb": 0.17,
            "angle_deg": 35,
            "hitstop": 6,
            "projectile": True,
        },
        "rasteira": {
            "name": f"Dash Rasteira {prefix}",
            "input": "Correndo + Ataque",
            "role": "Avanço rasteiro de longo alcance",
            "duration": 24 + lag_bonus,
            "active_start": 5,
            "active_end": 12,
            "end_lag": 15 + lag_bonus,
            "dash_vx": round(10.5 * speed_mult, 2),
            "dash_vy": 0.0,
            "hb_size": (68, 24),
            "hb_offset": (-2, 18),
            "damage": round(11.5 * base_dmg, 1),
            "base_kb": 6.2,
            "scaling_kb": 0.13,
            "angle_deg": 28,
            "hitstop": 5,
        },
        "up": {
            "name": f"Up Tilt {prefix}",
            "input": "Cima + Ataque",
            "role": "Antiaéreo vertical para manter pressão",
            "duration": 22 + lag_bonus,
            "active_start": 6,
            "active_end": 12,
            "end_lag": 8 + lag_bonus,
            "dash_vx": 0.0,
            "dash_vy": -3.1,
            "hb_size": (48, 52),
            "hb_offset": (0, -24),
            "damage": round(12.0 * base_dmg, 1),
            "base_kb": 7.5,
            "scaling_kb": 0.16,
            "angle_deg": 78,
            "hitstop": 5,
        },
        "uppercut": {
            "name": f"Up Smash {prefix}",
            "input": "Pulando / Cima + Ataque",
            "role": "Finalizador vertical com alto knockback",
            "duration": 26 + lag_bonus,
            "active_start": 6,
            "active_end": 13,
            "end_lag": 14 + lag_bonus,
            "dash_vx": 2.2,
            "dash_vy": -6.2,
            "hb_size": (52, 58),
            "hb_offset": (2, -26),
            "damage": round(16.5 * base_dmg, 1),
            "base_kb": 9.2,
            "scaling_kb": 0.19,
            "angle_deg": 74,
            "hitstop": 7,
        },
        "underdive": {
            "name": f"Meteor Spike {prefix}",
            "input": "No ar + Baixo + Ataque",
            "role": "Meteor Smash que arremessa direto para baixo",
            "duration": 26 + lag_bonus,
            "active_start": 5,
            "active_end": 16,
            "end_lag": 19 + lag_bonus,
            "dash_vx": 2.5,
            "dash_vy": 9.6,
            "hb_size": (52, 46),
            "hb_offset": (0, 22),
            "damage": round(13.5 * base_dmg, 1),
            "base_kb": 8.0,
            "scaling_kb": 0.16,
            "angle_deg": -72,
            "hitstop": 7,
        },
    }


CHARACTER_ROSTER = [
    {
        "name": "Eduardo",
        "tag": "Equilibrado • Foguete Final",
        "archetype": "All-Rounder / Versátil",
        "bio": "Lutador completo que domina tanto a curta quanto a média distância com recuperação sólida.",
        "color": (255, 85, 105),
        "ultimate_type": "rush",
        "ultimate_name": "Foguete do Dudu",
        "ultimate_desc": "Final Smash em linha reta com propulsão máxima e impacto explosivo (26% dano).",
        "stats": {
            "max_run_speed": 5.2,
            "jump_force": -13.2,
            "kb_mult": 1.0,
            "lag_mult": 1.0,
            "proj_color": (255, 115, 135),
        },
        "moveset": _build_moveset("do Dudu", base_dmg=1.0, speed_mult=1.0),
    },
    {
        "name": "Artulio",
        "tag": "Ágil • Furacão Rasteiro",
        "archetype": "Rushdown / Mobilidade",
        "bio": "Especialista em entrar rápido com rasteiras e emendar ganchos aéreos com baixo end lag.",
        "color": (85, 185, 255),
        "ultimate_type": "sweep",
        "ultimate_name": "Furacão Artulio",
        "ultimate_desc": "Investida giratória ascendente que varre o chão e lança o alvo para o alto (23% dano).",
        "stats": {
            "max_run_speed": 5.5,
            "jump_force": -13.4,
            "kb_mult": 0.96,
            "lag_mult": 0.92,
            "proj_color": (115, 205, 255),
        },
        "moveset": _build_moveset("do Artulio", base_dmg=0.96, speed_mult=1.05),
    },
    {
        "name": "Felip",
        "tag": "Pesado • Impacto Sísmico",
        "archetype": "Powerhouse / Pesado",
        "bio": "Golpes lentos, porém devastadores. Difícil de ser arremessado para fora da arena.",
        "color": (255, 185, 65),
        "ultimate_type": "rush",
        "ultimate_name": "Impacto Sísmico",
        "ultimate_desc": "Avanço blindado de força bruta que elimina oponentes com pouca porcentagem.",
        "stats": {
            "max_run_speed": 4.7,
            "jump_force": -12.7,
            "kb_mult": 1.14,
            "lag_mult": 1.08,
            "proj_color": (255, 195, 85),
        },
        "moveset": _build_moveset(
            "do Felip", base_dmg=1.15, speed_mult=0.92, heavy=True
        ),
    },
    {
        "name": "DogExuEar",
        "tag": "Veloz • Teleporte Sombrio",
        "archetype": "Assassino / Combo Rápido",
        "bio": "O mais veloz do elenco. Usa dash e Roman Cancel para combos extensos.",
        "color": (135, 240, 145),
        "ultimate_type": "blink",
        "ultimate_name": "Corte Sombrio",
        "ultimate_desc": "Teleporta instantaneamente às costas do oponente e desfere um corte letal (24% dano).",
        "stats": {
            "max_run_speed": 5.8,
            "jump_force": -13.6,
            "kb_mult": 0.94,
            "lag_mult": 0.88,
            "proj_color": (145, 250, 155),
        },
        "moveset": _build_moveset(
            "do DogExuEar", base_dmg=0.92, speed_mult=1.12
        ),
    },
    {
        "name": "Tame Impala",
        "tag": "Psicodélico • Tempestade",
        "archetype": "Zoner / Controle de Espaço",
        "bio": "Controla o ritmo do palco com ondas sonoras amplas e excelente alcance aéreo.",
        "color": (185, 115, 255),
        "ultimate_type": "wave",
        "ultimate_name": "Tempestade Sonora",
        "ultimate_desc": "Dispara 3 ondas psicodélicas em leque que cobrem toda a largura da arena.",
        "stats": {
            "max_run_speed": 5.3,
            "jump_force": -13.5,
            "kb_mult": 1.02,
            "lag_mult": 0.96,
            "proj_color": (205, 135, 255),
        },
        "moveset": _build_moveset("do Tame", base_dmg=1.02, speed_mult=1.02),
    },
    {
        "name": "Link do Zap",
        "tag": "Rápido • Flash do Zap",
        "archetype": "Mix-up / Pressão Constante",
        "bio": "Alterna entre ondas rápidas e aproximação fulminante para punir qualquer brecha.",
        "color": (75, 235, 195),
        "ultimate_type": "blink",
        "ultimate_name": "Flash do Zap",
        "ultimate_desc": "Surge atrás do adversário em um piscar de olhos com golpe de alto knockback.",
        "stats": {
            "max_run_speed": 5.7,
            "jump_force": -13.5,
            "kb_mult": 0.98,
            "lag_mult": 0.9,
            "proj_color": (95, 245, 210),
        },
        "moveset": _build_moveset("do Zap", base_dmg=0.98, speed_mult=1.1),
    },
    {
        "name": "Nikolas",
        "tag": "Técnico • Rajada Tripla",
        "archetype": "Técnico / Punição & Parry",
        "bio": "Brilha com timing preciso, contra-ataques após Parry e controle de projéteis.",
        "color": (255, 130, 195),
        "ultimate_type": "wave",
        "ultimate_name": "Rajada Tripla",
        "ultimate_desc": "Lança três projéteis energizados em ângulos distintos para fechar a saída.",
        "stats": {
            "max_run_speed": 5.4,
            "jump_force": -13.1,
            "kb_mult": 1.03,
            "lag_mult": 0.94,
            "proj_color": (255, 150, 210),
        },
        "moveset": _build_moveset("do Nikolas", base_dmg=1.04, speed_mult=1.03),
    },
    {
        "name": "Beiçola",
        "tag": "Tanque • Pastelaço Supremo",
        "archetype": "Juggernaut / Tanque",
        "bio": "O lutador mais resistente do jogo. Sobrevive a porcentagens altíssimas e bate pesado.",
        "color": (255, 210, 90),
        "ultimate_type": "rush",
        "ultimate_name": "Pastelaço Supremo",
        "ultimate_desc": "Investida imparável com hitbox gigante que manda o rival direto para a blast zone.",
        "stats": {
            "max_run_speed": 4.6,
            "jump_force": -12.6,
            "kb_mult": 1.18,
            "lag_mult": 1.1,
            "proj_color": (255, 220, 110),
        },
        "moveset": _build_moveset(
            "do Beiçola", base_dmg=1.18, speed_mult=0.9, heavy=True
        ),
    },
]


def _is_bg_candidate(rgb, ref_rgb, tolerance=26):
    r, g, b = rgb
    rr, gg, bb = ref_rgb
    near_ref = (
        abs(r - rr) <= tolerance
        and abs(g - gg) <= tolerance
        and abs(b - bb) <= tolerance
    )
    near_pure_white = r > 242 and g > 242 and b > 242
    return near_ref or near_pure_white


def load_fighter_sprite(base_name, width, height, remove_white=True):
    """Carrega (.jpg/.jpeg), remove apenas o fundo conectado às bordas com SRCALPHA e escala."""
    for ext in (".jpg", ".jpeg", ".JPG", ".JPEG"):
        path = f"{base_name}{ext}"
        if os.path.exists(path):
            raw = pygame.image.load(path).convert()

            if not remove_white:
                return pygame.transform.smoothscale(
                    raw, (width, height)
                ).convert_alpha()

            work_w, work_h = width * 3, height * 3
            if raw.get_width() > work_w or raw.get_height() > work_h:
                raw = pygame.transform.smoothscale(raw, (work_w, work_h))

            w, h = raw.get_size()
            px_in = pygame.PixelArray(raw)

            border_pixels = []
            for x in range(w):
                border_pixels.append(raw.unmap_rgb(px_in[x, 0])[:3])
                border_pixels.append(raw.unmap_rgb(px_in[x, h - 1])[:3])
            for y in range(h):
                border_pixels.append(raw.unmap_rgb(px_in[0, y])[:3])
                border_pixels.append(raw.unmap_rgb(px_in[w - 1, y])[:3])

            ref_rgb = (
                max(border_pixels, key=lambda c: sum(c))
                if border_pixels
                else (255, 255, 255)
            )

            visited = [[False] * w for _ in range(h)]
            queue = deque()

            for x in range(w):
                for y in (0, h - 1):
                    rgb = raw.unmap_rgb(px_in[x, y])[:3]
                    if not visited[y][x] and _is_bg_candidate(rgb, ref_rgb):
                        visited[y][x] = True
                        queue.append((x, y))

            for y in range(h):
                for x in (0, w - 1):
                    rgb = raw.unmap_rgb(px_in[x, y])[:3]
                    if not visited[y][x] and _is_bg_candidate(rgb, ref_rgb):
                        visited[y][x] = True
                        queue.append((x, y))

            while queue:
                cx, cy = queue.popleft()
                for nx, ny in (
                    (cx + 1, cy),
                    (cx - 1, cy),
                    (cx, cy + 1),
                    (cx, cy - 1),
                ):
                    if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx]:
                        n_rgb = raw.unmap_rgb(px_in[nx, ny])[:3]
                        if _is_bg_candidate(n_rgb, ref_rgb):
                            visited[ny][nx] = True
                            queue.append((nx, ny))

            alpha_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            px_out = pygame.PixelArray(alpha_surf)

            for y in range(h):
                for x in range(w):
                    r, g, b, _ = raw.unmap_rgb(px_in[x, y])
                    if visited[y][x]:
                        px_out[x, y] = alpha_surf.map_rgb((r, g, b, 0))
                    else:
                        px_out[x, y] = alpha_surf.map_rgb((r, g, b, 255))

            del px_out
            del px_in

            scaled = pygame.transform.smoothscale(alpha_surf, (width, height))
            return scaled.convert_alpha()
    return None


def scan_music_files():
    valid_exts = (".mp3", ".ogg", ".wav")
    tracks = []
    for fname in sorted(os.listdir(".")):
        if os.path.isfile(fname) and fname.lower().endswith(valid_exts):
            tracks.append(fname)
    return tracks


class Jukebox:
    def __init__(self, initial_volume=0.6):
        self.mixer_ready = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.mixer_ready = True
        except pygame.error:
            self.mixer_ready = False

        self.selected_idx = 0
        self.playing_track = None
        self.is_paused = False
        self.volume = max(0.0, min(1.0, round(float(initial_volume), 2)))
        if self.mixer_ready:
            pygame.mixer.music.set_volume(self.volume)

        self.tracks = []
        self.refresh_tracks()

    def refresh_tracks(self):
        self.tracks = scan_music_files()
        if not self.tracks:
            self.selected_idx = 0
        elif self.selected_idx >= len(self.tracks):
            self.selected_idx = len(self.tracks) - 1

    def set_volume(self, value):
        self.volume = max(0.0, min(1.0, round(value, 2)))
        if self.mixer_ready:
            pygame.mixer.music.set_volume(self.volume)

    def play_selected(self):
        if not self.mixer_ready or not self.tracks:
            return
        track = self.tracks[self.selected_idx]
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)
            self.playing_track = track
            self.is_paused = False
        except pygame.error as e:
            print(f"Erro ao tocar '{track}': {e}")

    def toggle_pause_or_play(self):
        if not self.mixer_ready or not self.tracks:
            return
        selected = self.tracks[self.selected_idx]
        if self.playing_track != selected:
            self.play_selected()
        elif self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
        elif pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.is_paused = True
        else:
            self.play_selected()


class Platform:
    """Representa chão sólido e plataformas atravessáveis (estáticas ou móveis)."""

    def __init__(
        self,
        x,
        y,
        w,
        h,
        one_way=False,
        amp_x=0.0,
        amp_y=0.0,
        freq=0.0,
        stage_color=MAIN_STAGE_COLOR,
        plat_color=PLATFORM_COLOR,
    ):
        self.base_x = float(x)
        self.base_y = float(y)
        self.rect = pygame.Rect(x, y, w, h)
        self.one_way = one_way
        self.amp_x = amp_x
        self.amp_y = amp_y
        self.freq = freq
        self.stage_color = stage_color
        self.plat_color = plat_color
        self.dx = 0
        self.dy = 0

    def update(self, tick_count):
        if self.amp_x == 0.0 and self.amp_y == 0.0:
            self.dx = 0
            self.dy = 0
            return
        old_x, old_y = self.rect.x, self.rect.y
        self.rect.x = int(
            round(self.base_x + math.sin(tick_count * self.freq) * self.amp_x)
        )
        self.rect.y = int(
            round(self.base_y + math.sin(tick_count * self.freq) * self.amp_y)
        )
        self.dx = self.rect.x - old_x
        self.dy = self.rect.y - old_y

    def draw(self, surface):
        if self.one_way:
            pygame.draw.rect(surface, self.plat_color, self.rect, border_radius=5)
            pygame.draw.line(
                surface,
                TEXT_COLOR,
                (self.rect.left + 4, self.rect.top + 2),
                (self.rect.right - 4, self.rect.top + 2),
                2,
            )
        else:
            pygame.draw.rect(surface, self.stage_color, self.rect, border_radius=6)
            pygame.draw.rect(
                surface, ARCADE_NEON_PINK, self.rect, width=2, border_radius=6
            )
            pygame.draw.circle(
                surface,
                ARCADE_NEON_YELLOW,
                (self.rect.left + 4, self.rect.top + 4),
                5,
            )
            pygame.draw.circle(
                surface,
                ARCADE_NEON_YELLOW,
                (self.rect.right - 4, self.rect.top + 4),
                5,
            )


class SmashBall:
    """Esfera Smash flutuante que concede Final Smash (100%) a quem quebrá-la."""

    def __init__(self):
        self.x = float(WIDTH // 2)
        self.y = 220.0
        self.vx = random.choice([-2.2, 2.2])
        self.vy = 1.4
        self.hp = 18.0
        self.radius = 20
        self.rect = pygame.Rect(int(self.x - 20), int(self.y - 20), 40, 40)
        self.life = 720
        self.phase = 0.0

    def update(self):
        self.life -= 1
        self.phase += 0.12
        self.x += self.vx
        self.y += self.vy + math.sin(self.phase) * 0.8
        if self.x < 220 or self.x > WIDTH - 220:
            self.vx *= -1
        if self.y < 140 or self.y > 460:
            self.vy *= -1
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surface, offset_x=0, offset_y=0):
        cx = int(self.x + offset_x)
        cy = int(self.y + offset_y)
        pygame.draw.circle(
            surface, ARCADE_NEON_YELLOW, (cx, cy), self.radius + 4, 2
        )
        pygame.draw.circle(surface, (40, 45, 70), (cx, cy), self.radius)
        pygame.draw.line(
            surface,
            ARCADE_NEON_YELLOW,
            (cx - 6, cy - self.radius + 3),
            (cx - 6, cy + self.radius - 3),
            4,
        )
        pygame.draw.line(
            surface,
            ARCADE_NEON_YELLOW,
            (cx - self.radius + 3, cy + 5),
            (cx + self.radius - 3, cy + 5),
            3,
        )


class StagePickup:
    """Item coletável que surge nas plataformas durante a luta."""

    TYPES = [
        ("meter", "+30% ESPECIAL", ARCADE_NEON_CYAN),
        ("heal", "-15% DANO", CPU_COLOR),
        ("boost", "TURBO NEON!", ARCADE_NEON_YELLOW),
    ]

    def __init__(self, x, y, kind_idx=None):
        if kind_idx is None:
            kind_idx = random.randrange(len(self.TYPES))
        self.kind, self.label, self.color = self.TYPES[kind_idx]
        self.rect = pygame.Rect(x - 13, y - 26, 26, 26)
        self.life = 540
        self.bob_phase = random.uniform(0, math.tau)

    def update(self):
        self.life -= 1
        self.bob_phase += 0.1

    def draw(self, surface, offset_x=0, offset_y=0):
        bob = int(math.sin(self.bob_phase) * 4)
        r = self.rect.move(offset_x, offset_y + bob)
        pygame.draw.rect(surface, PANEL_COLOR, r, border_radius=7)
        pygame.draw.rect(surface, self.color, r, width=2, border_radius=7)
        pygame.draw.circle(surface, self.color, r.center, 6)


class Afterimage:
    def __init__(self, rect, color, life=9):
        self.rect = rect.copy()
        self.color = color
        self.life = life
        self.max_life = life

    def update(self):
        self.life -= 1

    def draw(self, surface, offset_x=0, offset_y=0):
        if self.life <= 0:
            return
        alpha = int(125 * (self.life / max(1, self.max_life)))
        ghost = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            ghost,
            (*self.color[:3], alpha),
            ghost.get_rect(),
            border_radius=6,
        )
        surface.blit(ghost, self.rect.move(offset_x, offset_y).topleft)


class Particle:
    def __init__(self, x, y, vx, vy, color, life=16, radius=4):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.life = life
        self.max_life = life
        self.radius = radius

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.92
        self.vy *= 0.92
        self.life -= 1

    def draw(self, surface, offset_x=0, offset_y=0):
        if self.life <= 0:
            return
        r = max(1, int(self.radius * (self.life / max(1, self.max_life))))
        pygame.draw.circle(
            surface,
            self.color,
            (int(self.x + offset_x), int(self.y + offset_y)),
            r,
        )


class KOBlastBeam:
    """Feixe de explosão clássico de Smash Bros quando alguém cruza a blast zone."""

    def __init__(self, x, y, angle_deg, color):
        self.x = float(x)
        self.y = float(y)
        self.angle = math.radians(angle_deg)
        self.color = color
        self.life = 26
        self.max_life = 26

    def update(self):
        self.life -= 1

    def draw(self, surface):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        width_beam = max(4, int(52 * ratio))
        length = 900
        ex = self.x + math.cos(self.angle) * length
        ey = self.y + math.sin(self.angle) * length
        pygame.draw.line(
            surface,
            self.color,
            (int(self.x), int(self.y)),
            (int(ex), int(ey)),
            width_beam,
        )
        pygame.draw.line(
            surface,
            TEXT_COLOR,
            (int(self.x), int(self.y)),
            (int(ex), int(ey)),
            max(2, width_beam // 3),
        )


class DamagePopup:
    def __init__(self, x, y, text, color=ARCADE_NEON_YELLOW, life=38):
        self.x = float(x)
        self.y = float(y)
        self.vy = -1.4
        self.text = text
        self.color = color
        self.life = life

    def update(self):
        self.y += self.vy
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surface, font, offset_x=0, offset_y=0):
        if self.life <= 0:
            return
        surf = font.render(self.text, True, self.color)
        surface.blit(
            surf,
            surf.get_rect(
                center=(int(self.x + offset_x), int(self.y + offset_y))
            ),
        )


class Projectile:
    def __init__(
        self, owner_idx, x, y, vx, color, damage, base_kb, scaling_kb, vy=0.0
    ):
        self.owner_idx = owner_idx
        self.rect = pygame.Rect(x, y, 22, 14)
        self.vx = vx
        self.vy = vy
        self.color = color
        self.damage = damage
        self.base_kb = base_kb
        self.scaling_kb = scaling_kb
        self.life = 60

    def update(self):
        self.rect.x += int(round(self.vx))
        self.rect.y += int(round(self.vy))
        self.life -= 1

    def draw(self, surface, offset_x=0, offset_y=0):
        r = self.rect.move(offset_x, offset_y)
        pygame.draw.rect(surface, self.color, r, border_radius=6)
        pygame.draw.rect(surface, TEXT_COLOR, r, width=1, border_radius=6)


class Fighter:
    def __init__(
        self,
        name,
        x,
        y,
        color,
        controls,
        moveset,
        facing=1,
        sprite=None,
        stats=None,
        ultimate_type="rush",
        ultimate_name="Golpe Final",
    ):
        self.name = name
        self.spawn_pos = (x, y)
        self.color = color
        self.controls = controls
        self.moveset = moveset
        self.ultimate_type = ultimate_type
        self.ultimate_name = ultimate_name

        self.rect = pygame.Rect(x, y, 46, 68)
        self.prev_bottom = self.rect.bottom

        self.sprite = None
        self.sprite_flipped = None
        self.set_sprite(sprite)

        self.vx = 0.0
        self.vy = 0.0
        self.facing = facing

        stats = stats or {}
        self.move_accel = 0.85
        self.max_run_speed = stats.get("max_run_speed", 5.2)
        self.air_accel = 0.50
        self.jump_force = stats.get("jump_force", -13.2)
        self.double_jump_force = self.jump_force * 0.9
        self.kb_mult = stats.get("kb_mult", 1.0)
        self.lag_mult = stats.get("lag_mult", 1.0)
        self.proj_color = stats.get("proj_color", color)
        self.max_jumps = 2
        self.jumps_left = self.max_jumps

        self.on_ground = False
        self.drop_through_timer = 0
        self.jump_rise_timer = 0
        self.damage_pct = 0.0
        self.stocks = 3
        self.hitstun = 0

        self.shield_hp = 100.0
        self.shielding = False
        self.shield_break_stun = 0
        self.charging_smash = False
        self.smash_charge_frames = 0
        self.pending_smash_slot = None
        self.pending_smash_mult = 1.0
        self.ledge_grabbed = False
        self.ledge_side = 0
        self.ledge_cooldown = 0

        self.special_meter = 0.0
        self.power_boost_timer = 0

        self.last_tap_dir = 0
        self.last_tap_frame = -999
        self.dash_burst_timer = 0

        self.dodge_timer = 0
        self.parry_window = 0
        self.dodge_cooldown = 0
        self.invuln_timer = 0

        self.current_move = None
        self.attack_timer = 0
        self.attack_delay = 0
        self.grab_timer = 0
        self.grab_cooldown = 0
        self.grab_registered = False
        self.hit_registered = False
        self.proj_spawned = False
        self.proj_cooldown = 0
        self.combo_count = 0
        self.max_combo = 0
        self.total_damage_dealt = 0.0
        self.combo_display_timer = 0
        self.last_combo_label = ""
        self.ko_moves_scored = []

    def set_sprite(self, sprite):
        self.sprite = sprite
        self.sprite_flipped = (
            pygame.transform.flip(sprite, True, False) if sprite else None
        )

    def set_character(self, char_data, sprite=None):
        self.name = char_data["name"]
        self.color = char_data["color"]
        self.moveset = char_data["moveset"]
        self.ultimate_type = char_data.get("ultimate_type", "rush")
        self.ultimate_name = char_data.get("ultimate_name", "Golpe Final")
        stats = char_data.get("stats", {})
        self.max_run_speed = stats.get("max_run_speed", 5.2)
        self.jump_force = stats.get("jump_force", -13.2)
        self.double_jump_force = self.jump_force * 0.9
        self.kb_mult = stats.get("kb_mult", 1.0)
        self.lag_mult = stats.get("lag_mult", 1.0)
        self.proj_color = stats.get("proj_color", self.color)
        self.set_sprite(sprite)

    def to_net_dict(self):
        hb = self.get_hitbox()
        gb = self.get_grab_box()
        return {
            "x": self.rect.x,
            "y": self.rect.y,
            "facing": self.facing,
            "damage_pct": round(self.damage_pct, 1),
            "stocks": self.stocks,
            "special_meter": round(self.special_meter, 1),
            "hitstun": self.hitstun,
            "invuln_timer": self.invuln_timer,
            "shielding": self.shielding,
            "shield_hp": round(self.shield_hp, 1),
            "shield_break_stun": self.shield_break_stun,
            "charging_smash": self.charging_smash,
            "smash_charge_frames": self.smash_charge_frames,
            "parry_window": self.parry_window,
            "power_boost_timer": self.power_boost_timer,
            "attack_timer": self.attack_timer,
            "attack_delay": self.attack_delay,
            "dash_vx": self.current_move.get("dash_vx", 0.0)
            if self.current_move
            else 0.0,
            "hb": [hb.x, hb.y, hb.w, hb.h] if hb else None,
            "gb": [gb.x, gb.y, gb.w, gb.h] if gb else None,
            "combo_display_timer": self.combo_display_timer,
            "last_combo_label": self.last_combo_label,
            "max_combo": self.max_combo,
            "total_damage_dealt": round(self.total_damage_dealt, 1),
            "ko_moves_scored": list(self.ko_moves_scored),
        }

    def apply_net_dict(self, d):
        if not isinstance(d, dict):
            return
        self.rect.x = int(d.get("x", self.rect.x))
        self.rect.y = int(d.get("y", self.rect.y))
        self.facing = int(d.get("facing", self.facing))
        self.damage_pct = float(d.get("damage_pct", self.damage_pct))
        self.stocks = int(d.get("stocks", self.stocks))
        self.special_meter = float(d.get("special_meter", self.special_meter))
        self.hitstun = int(d.get("hitstun", 0))
        self.invuln_timer = int(d.get("invuln_timer", 0))
        self.shielding = bool(d.get("shielding", False))
        self.shield_hp = float(d.get("shield_hp", 100.0))
        self.shield_break_stun = int(d.get("shield_break_stun", 0))
        self.charging_smash = bool(d.get("charging_smash", False))
        self.smash_charge_frames = int(d.get("smash_charge_frames", 0))
        self.parry_window = int(d.get("parry_window", 0))
        self.power_boost_timer = int(d.get("power_boost_timer", 0))
        self.attack_timer = int(d.get("attack_timer", 0))
        self.attack_delay = int(d.get("attack_delay", 0))
        self._net_dash_vx = float(d.get("dash_vx", 0.0))
        hb_raw = d.get("hb")
        self._net_hb = pygame.Rect(*hb_raw) if hb_raw else None
        gb_raw = d.get("gb")
        self._net_gb = pygame.Rect(*gb_raw) if gb_raw else None
        self.combo_display_timer = int(d.get("combo_display_timer", 0))
        self.last_combo_label = str(d.get("last_combo_label", ""))
        self.max_combo = int(d.get("max_combo", 0))
        self.total_damage_dealt = float(d.get("total_damage_dealt", 0.0))
        self.ko_moves_scored = list(d.get("ko_moves_scored", []))

    def reset(self, respawn_invuln=0):
        self.rect.topleft = self.spawn_pos
        self.vx = 0.0
        self.vy = 0.0
        self.damage_pct = 0.0
        self.hitstun = 0
        self.shield_hp = 100.0
        self.shielding = False
        self.shield_break_stun = 0
        self.charging_smash = False
        self.smash_charge_frames = 0
        self.pending_smash_slot = None
        self.pending_smash_mult = 1.0
        self.ledge_grabbed = False
        self.ledge_cooldown = 0
        self.dodge_timer = 0
        self.parry_window = 0
        self.dodge_cooldown = 0
        self.invuln_timer = max(0, int(respawn_invuln))
        self.jump_rise_timer = 0
        self.dash_burst_timer = 0
        self.power_boost_timer = 0
        self.current_move = None
        self.attack_timer = 0
        self.attack_delay = 0
        self.grab_timer = 0
        self.grab_cooldown = 0
        self.grab_registered = False
        self.hit_registered = False
        self.proj_spawned = False
        self.proj_cooldown = 0
        self.combo_count = 0
        self.combo_display_timer = 0
        self.last_combo_label = ""
        self.jumps_left = self.max_jumps

    def reset_match_stats(self):
        self.stocks = 3
        self.max_combo = 0
        self.total_damage_dealt = 0.0
        self.special_meter = 0.0
        self.ko_moves_scored = []
        self.reset(respawn_invuln=0)

    def add_meter(self, amount):
        self.special_meter = max(0.0, min(100.0, self.special_meter + amount))

    def register_direction_tap(self, direction, tick_count, particles):
        if (
            self.hitstun > 0
            or self.shield_break_stun > 0
            or self.attack_timer > 0
            or self.dodge_timer > 0
            or self.grab_timer > 0
            or self.ledge_grabbed
        ):
            return
        if (
            direction == self.last_tap_dir
            and (tick_count - self.last_tap_frame) <= 13
            and self.dash_burst_timer == 0
        ):
            self.facing = direction
            self.vx = direction * (self.max_run_speed * 1.75)
            self.dash_burst_timer = 12
            spawn_hit_particles(
                particles,
                self.rect.centerx,
                self.rect.bottom - 4,
                ARCADE_NEON_CYAN,
                count=5,
            )
            self.last_tap_dir = 0
        else:
            self.last_tap_dir = direction
            self.last_tap_frame = tick_count

    def dodge(self, sfx=None, volume=0.6):
        """Ativa esquiva/roll com janela inicial de Parry perfeito (5 frames)."""
        if (
            self.hitstun > 0
            or self.shield_break_stun > 0
            or self.attack_timer > 0
            or self.grab_timer > 0
            or self.dodge_cooldown > 0
            or self.dodge_timer > 0
        ):
            return False
        self.ledge_grabbed = False
        self.charging_smash = False
        self.dodge_timer = 11
        self.parry_window = 5
        self.invuln_timer = max(self.invuln_timer, 12)
        self.dodge_cooldown = 40
        self.vx = 9.5 * self.facing
        if not self.on_ground and self.vy > 0:
            self.vy = -2.0
        if sfx:
            sfx.play("dodge", volume)
        return True

    def roman_cancel(self, particles, popups, sfx=None, volume=0.6):
        if (
            self.special_meter < 50.0
            or self.hitstun > 0
            or self.shield_break_stun > 0
        ):
            return False
        if (
            self.attack_timer <= 0
            and self.attack_delay <= 0
            and self.grab_timer <= 0
        ):
            return False

        self.special_meter -= 50.0
        self.current_move = None
        self.attack_timer = 0
        self.attack_delay = 0
        self.grab_timer = 0
        self.hit_registered = False
        self.vx *= 0.45
        if self.vy > 0:
            self.vy = -2.5
        spawn_hit_particles(
            particles,
            self.rect.centerx,
            self.rect.centery,
            ARCADE_NEON_PINK,
            count=14,
        )
        popups.append(
            DamagePopup(
                self.rect.centerx,
                self.rect.top - 16,
                "ROMAN CANCEL!",
                ARCADE_NEON_PINK,
                life=30,
            )
        )
        if sfx:
            sfx.play("cancel", volume)
        return True

    def grab(self, sfx=None, volume=0.6):
        if (
            self.hitstun > 0
            or self.shield_break_stun > 0
            or self.attack_timer > 0
            or self.attack_delay > 0
            or self.dodge_timer > 0
            or self.grab_timer > 0
            or self.grab_cooldown > 0
        ):
            return False
        self.ledge_grabbed = False
        self.charging_smash = False
        self.grab_timer = 12
        self.grab_cooldown = 36
        self.grab_registered = False
        self.vx = 3.6 * self.facing
        if sfx:
            sfx.play("grab", volume)
        return True

    def get_grab_box(self):
        if hasattr(self, "_net_gb"):
            return self._net_gb
        if self.grab_timer <= 0 or self.grab_registered:
            return None
        elapsed = 12 - self.grab_timer
        if 2 <= elapsed <= 8:
            gw, gh = 42, 46
            gx = (
                self.rect.right - 4
                if self.facing == 1
                else self.rect.left - gw + 4
            )
            gy = self.rect.centery - gh // 2
            return pygame.Rect(gx, gy, gw, gh)
        return None

    def trigger_ultimate(
        self,
        owner_idx,
        target,
        projectiles,
        particles,
        popups,
        sfx=None,
        volume=0.6,
    ):
        if (
            self.special_meter < 100.0
            or self.hitstun > 0
            or self.shield_break_stun > 0
            or self.attack_timer > 0
            or self.grab_timer > 0
        ):
            return False

        self.special_meter = 0.0
        self.ledge_grabbed = False
        self.charging_smash = False
        self.invuln_timer = max(self.invuln_timer, 24)
        if sfx:
            sfx.play("ultimate", volume)

        popups.append(
            DamagePopup(
                self.rect.centerx,
                self.rect.top - 22,
                f"FINAL SMASH: {self.ultimate_name.upper()}!",
                METER_READY_COLOR,
                life=46,
            )
        )
        spawn_hit_particles(
            particles,
            self.rect.centerx,
            self.rect.centery,
            METER_READY_COLOR,
            count=18,
        )

        utype = self.ultimate_type
        if utype == "wave":
            for vy_spread in (-2.2, 0.0, 2.2):
                px = (
                    self.rect.right + 8
                    if self.facing == 1
                    else self.rect.left - 30
                )
                projectiles.append(
                    Projectile(
                        owner_idx=owner_idx,
                        x=px,
                        y=self.rect.centery - 7,
                        vx=10.5 * self.facing,
                        vy=vy_spread,
                        color=METER_READY_COLOR,
                        damage=13.5,
                        base_kb=9.5,
                        scaling_kb=0.2,
                    )
                )
            self.attack_delay = 10
        elif utype == "blink":
            offset_behind = -56 if target.facing == 1 else 56
            new_x = max(140, min(WIDTH - 186, target.rect.x + offset_behind))
            self.rect.x = new_x
            self.rect.y = max(120, target.rect.y - 6)
            self.facing = (
                1 if target.rect.centerx >= self.rect.centerx else -1
            )
            self.current_move = {
                "name": self.ultimate_name,
                "duration": 22,
                "active_start": 2,
                "active_end": 14,
                "end_lag": 8,
                "dash_vx": 4.0,
                "dash_vy": -2.0,
                "hb_size": (76, 62),
                "hb_offset": (-8, 0),
                "damage": 24.0,
                "base_kb": 11.5,
                "scaling_kb": 0.24,
                "angle_deg": 55,
                "hitstop": 10,
            }
            self.attack_timer = 22
            self.attack_delay = 8
            self.hit_registered = False
        elif utype == "sweep":
            self.current_move = {
                "name": self.ultimate_name,
                "duration": 26,
                "active_start": 3,
                "active_end": 18,
                "end_lag": 10,
                "dash_vx": 13.5,
                "dash_vy": -3.5,
                "hb_size": (88, 52),
                "hb_offset": (-6, 8),
                "damage": 23.0,
                "base_kb": 11.0,
                "scaling_kb": 0.23,
                "angle_deg": 65,
                "hitstop": 10,
            }
            self.vx = 13.5 * self.facing
            self.vy = -3.5
            self.on_ground = False
            self.attack_timer = 26
            self.attack_delay = 10
            self.hit_registered = False
        else:
            self.current_move = {
                "name": self.ultimate_name,
                "duration": 26,
                "active_start": 3,
                "active_end": 18,
                "end_lag": 10,
                "dash_vx": 14.0,
                "dash_vy": 0.0,
                "hb_size": (86, 58),
                "hb_offset": (-6, 0),
                "damage": 26.0,
                "base_kb": 12.2,
                "scaling_kb": 0.25,
                "angle_deg": 42,
                "hitstop": 11,
            }
            self.vx = 14.0 * self.facing
            self.attack_timer = 26
            self.attack_delay = 10
            self.hit_registered = False

        return True

    def jump(self):
        if (
            self.hitstun > 0
            or self.shield_break_stun > 0
            or self.attack_timer > 0
            or self.attack_delay > 0
            or self.grab_timer > 0
        ):
            return
        if self.ledge_grabbed:
            self.ledge_grabbed = False
            self.ledge_cooldown = 28
            self.vy = self.jump_force * 1.05
            self.vx = 4.2 * self.facing
            self.on_ground = False
            self.jumps_left = self.max_jumps - 1
            return

        self.charging_smash = False
        if self.on_ground:
            self.vy = self.jump_force
            self.on_ground = False
            self.jump_rise_timer = 14
            self.jumps_left = self.max_jumps - 1
        elif self.jumps_left > 0:
            self.vy = self.double_jump_force
            self.jump_rise_timer = 12
            self.jumps_left -= 1

    def trigger_move(self, slot, sfx=None, volume=0.6, smash_mult=1.0):
        if (
            self.hitstun > 0
            or self.shield_break_stun > 0
            or self.attack_timer > 0
            or self.attack_delay > 0
            or self.grab_timer > 0
        ):
            return False

        self.ledge_grabbed = False
        base_move = self.moveset[slot]
        move_data = dict(base_move)
        if smash_mult > 1.05:
            move_data["name"] = f"SMASH {base_move['name']}"
            move_data["damage"] = round(base_move["damage"] * smash_mult, 1)
            move_data["base_kb"] = base_move["base_kb"] * (
                1.0 + (smash_mult - 1.0) * 0.75
            )
            move_data["hitstop"] = base_move["hitstop"] + 3

        self.current_move = move_data
        self.attack_timer = move_data["duration"]
        self.attack_delay = max(
            1, int(round(move_data.get("end_lag", 0) * self.lag_mult))
        )
        self.hit_registered = False
        self.proj_spawned = False

        dash_vx = move_data.get("dash_vx", 0.0)
        dash_vy = move_data.get("dash_vy", 0.0)
        if dash_vx != 0.0:
            self.vx = dash_vx * self.facing
        if dash_vy != 0.0:
            self.vy = dash_vy
            if dash_vy < 0:
                self.on_ground = False

        if sfx:
            sfx.play("smash" if smash_mult > 1.05 else "swing", volume)
        return True

    def begin_attack_or_charge(self, keys, sfx=None, volume=0.6):
        if (
            self.hitstun > 0
            or self.shield_break_stun > 0
            or self.attack_timer > 0
            or self.attack_delay > 0
            or self.grab_timer > 0
        ):
            return

        if self.ledge_grabbed:
            self.ledge_grabbed = False
            self.ledge_cooldown = 28
            self.rect.y -= 18
            self.rect.x += 26 * self.facing
            self.trigger_move("rasteira", sfx, volume, smash_mult=1.1)
            return

        holding_left = bool(keys[self.controls["left"]])
        holding_right = bool(keys[self.controls["right"]])
        holding_up = bool(keys[self.controls["up"]])

        if holding_left:
            self.facing = -1
        elif holding_right:
            self.facing = 1

        if (
            self.on_ground
            and abs(self.vx) < self.max_run_speed * 0.65
            and (holding_left or holding_right or holding_up)
        ):
            self.charging_smash = True
            self.smash_charge_frames = 1
            self.pending_smash_slot = "uppercut" if holding_up else "side"
            return

        self.attack(keys, sfx, volume, smash_mult=1.0)

    def release_smash_charge(self, sfx=None, volume=0.6):
        if not self.charging_smash:
            return
        charge_ratio = min(1.0, self.smash_charge_frames / 36.0)
        mult = 1.0 + charge_ratio * 0.42
        slot = self.pending_smash_slot or "side"
        self.charging_smash = False
        self.smash_charge_frames = 0
        self.pending_smash_slot = None
        self.trigger_move(slot, sfx, volume, smash_mult=mult)

    def attack(self, keys, sfx=None, volume=0.6, smash_mult=1.0):
        if (
            self.hitstun > 0
            or self.shield_break_stun > 0
            or self.attack_timer > 0
            or self.attack_delay > 0
            or self.grab_timer > 0
        ):
            return

        holding_left = bool(keys[self.controls["left"]])
        holding_right = bool(keys[self.controls["right"]])
        holding_up = bool(keys[self.controls["up"]])
        holding_down = bool(keys[self.controls["down"]])

        if holding_left:
            self.facing = -1
        elif holding_right:
            self.facing = 1

        falling_in_air = (not self.on_ground) and (
            self.vy > 1.0 or holding_down
        )
        jumping_up = (
            not self.on_ground
            and (self.jump_rise_timer > 0 or self.vy < -2.0)
        ) or holding_up

        if falling_in_air:
            self.trigger_move("underdive", sfx, volume, smash_mult=smash_mult)
        elif jumping_up:
            self.trigger_move("uppercut", sfx, volume, smash_mult=smash_mult)
        elif holding_left or holding_right:
            if self.on_ground and abs(self.vx) >= self.max_run_speed * 0.65:
                self.trigger_move(
                    "rasteira", sfx, volume, smash_mult=smash_mult
                )
            elif self.on_ground:
                self.trigger_move("side", sfx, volume, smash_mult=smash_mult)
            else:
                self.trigger_move(
                    "rasteira", sfx, volume, smash_mult=smash_mult
                )
        else:
            self.trigger_move("neutral", sfx, volume, smash_mult=smash_mult)

    def register_combo_hit(self, move_name, damage_dealt):
        self.combo_count += 1
        if self.combo_count > self.max_combo:
            self.max_combo = self.combo_count
        self.total_damage_dealt += damage_dealt
        self.add_meter(damage_dealt * 1.45)
        self.combo_display_timer = 75
        self.last_combo_label = f"{move_name} ({self.combo_count}x)"

    def get_hitbox(self):
        if hasattr(self, "_net_hb"):
            return self._net_hb
        if self.attack_timer <= 0 or not self.current_move:
            return None

        move = self.current_move
        elapsed = move["duration"] - self.attack_timer
        if move["active_start"] <= elapsed <= move["active_end"]:
            hb_w, hb_h = move["hb_size"]
            off_x, off_y = move["hb_offset"]

            if self.facing == 1:
                hb_x = self.rect.right + off_x
            else:
                hb_x = self.rect.left - hb_w - off_x

            hb_y = self.rect.centery - hb_h // 2 + off_y
            return pygame.Rect(hb_x, hb_y, hb_w, hb_h)
        return None

    def try_spawn_projectile(self, owner_idx):
        if (
            self.attack_timer <= 0
            or not self.current_move
            or self.proj_spawned
            or self.proj_cooldown > 0
            or not self.current_move.get("projectile")
        ):
            return None

        move = self.current_move
        elapsed = move["duration"] - self.attack_timer
        if elapsed < move["active_start"]:
            return None

        self.proj_spawned = True
        self.proj_cooldown = 55
        px = (
            self.rect.right + 6
            if self.facing == 1
            else self.rect.left - 28
        )
        py = self.rect.centery - 7
        dmg_mult = 1.2 if self.power_boost_timer > 0 else 1.0
        return Projectile(
            owner_idx=owner_idx,
            x=px,
            y=py,
            vx=8.5 * self.facing,
            color=self.proj_color,
            damage=round(move["damage"] * 0.55 * dmg_mult, 1),
            base_kb=move["base_kb"] * 0.65,
            scaling_kb=move["scaling_kb"] * 0.75,
        )

    def take_hit(
        self,
        damage,
        base_kb,
        scaling_kb,
        angle_deg,
        attacker_facing,
        ignore_dodge=False,
        sudden_death=False,
    ):
        if not ignore_dodge and self.parry_window > 0:
            self.parry_window = 0
            self.invuln_timer = max(self.invuln_timer, 14)
            self.add_meter(25.0)
            return "parry"

        if not ignore_dodge and self.shielding and self.shield_hp > 0:
            self.shield_hp -= damage * 1.85
            self.vx = attacker_facing * 3.8
            if self.shield_hp <= 0:
                self.shield_hp = 0.0
                self.shielding = False
                self.shield_break_stun = 135
                self.vy = -12.5
                self.on_ground = False
                return "shield_break"
            return "shield"

        if not ignore_dodge and self.invuln_timer > 0:
            return "blocked"

        self.ledge_grabbed = False
        self.charging_smash = False
        self.damage_pct += damage
        self.add_meter(damage * 0.9)

        sd_mult = 1.25 if sudden_death else 1.0
        total_kb = (
            (base_kb + (self.damage_pct * scaling_kb)) * self.kb_mult * sd_mult
        )
        rad = math.radians(angle_deg)

        self.vx = math.cos(rad) * total_kb * attacker_facing
        self.vy = -math.sin(rad) * total_kb

        self.on_ground = False
        self.jump_rise_timer = 0
        self.hitstun = max(6, int(total_kb * 1.45))
        self.current_move = None
        self.attack_timer = 0
        self.attack_delay = 0
        self.grab_timer = 0
        self.dodge_timer = 0
        if ignore_dodge:
            self.invuln_timer = 0
        return "hit"

    def step_physics(
        self,
        move_dir,
        press_down,
        platforms,
        allow_direction_change=True,
        wind_vx=0.0,
        afterimages=None,
        hold_shield=False,
        hold_attack=False,
        sfx=None,
        volume=0.6,
    ):
        self.prev_bottom = self.rect.bottom

        if self.drop_through_timer > 0:
            self.drop_through_timer -= 1
        if self.jump_rise_timer > 0:
            self.jump_rise_timer -= 1
        if self.dash_burst_timer > 0:
            self.dash_burst_timer -= 1
        if self.power_boost_timer > 0:
            self.power_boost_timer -= 1
        if self.dodge_timer > 0:
            self.dodge_timer -= 1
        if self.parry_window > 0:
            self.parry_window -= 1
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
        if self.invuln_timer > 0:
            self.invuln_timer -= 1
        if self.grab_timer > 0:
            self.grab_timer -= 1
        if self.grab_cooldown > 0:
            self.grab_cooldown -= 1
        if self.proj_cooldown > 0:
            self.proj_cooldown -= 1
        if self.ledge_cooldown > 0:
            self.ledge_cooldown -= 1
        if self.shield_break_stun > 0:
            self.shield_break_stun -= 1

        if self.combo_display_timer > 0:
            self.combo_display_timer -= 1
            if self.combo_display_timer == 0:
                self.combo_count = 0

        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.current_move = None

        if self.attack_delay > 0:
            self.attack_delay -= 1

        if self.charging_smash:
            if hold_attack and self.smash_charge_frames < 42:
                self.smash_charge_frames += 1
            else:
                self.release_smash_charge(sfx, volume)

        can_shield = (
            hold_shield
            and self.on_ground
            and self.hitstun == 0
            and self.shield_break_stun == 0
            and self.attack_timer == 0
            and self.grab_timer == 0
            and self.dodge_timer == 0
            and not self.charging_smash
            and self.shield_hp > 5.0
        )
        self.shielding = can_shield
        if self.shielding:
            self.shield_hp = max(0.0, self.shield_hp - 0.28)
            if self.shield_hp <= 0.0:
                self.shielding = False
                self.shield_break_stun = 135
                self.vy = -12.5
                self.on_ground = False
        else:
            self.shield_hp = min(100.0, self.shield_hp + 0.18)

        if self.ledge_grabbed:
            self.vx = 0.0
            self.vy = 0.0
            if press_down:
                self.ledge_grabbed = False
                self.ledge_cooldown = 30
            return

        dashing = (
            self.current_move is not None
            and self.attack_timer > 0
            and self.current_move.get("dash_vx", 0.0) != 0.0
        )

        if afterimages is not None and (
            self.dash_burst_timer > 0
            or self.dodge_timer > 0
            or (
                self.current_move
                and self.current_move.get("dash_vx", 0.0) >= 10.0
            )
        ):
            afterimages.append(Afterimage(self.rect, self.color, life=8))

        if self.hitstun > 0 or self.shield_break_stun > 0:
            if self.hitstun > 0:
                self.hitstun -= 1
            if move_dir != 0:
                self.vx += move_dir * 0.12
        elif (
            self.dodge_timer <= 0
            and self.grab_timer <= 0
            and not self.shielding
            and not self.charging_smash
        ):
            if (
                allow_direction_change
                and move_dir != 0
                and self.attack_timer == 0
                and self.attack_delay == 0
            ):
                self.facing = move_dir

            accel = self.move_accel if self.on_ground else self.air_accel
            boost_mult = 1.18 if self.power_boost_timer > 0 else 1.0
            top_speed = (
                self.max_run_speed * 1.55
                if self.dash_burst_timer > 0
                else self.max_run_speed * boost_mult
            )
            if move_dir != 0 and not dashing:
                self.vx += move_dir * accel * boost_mult
                if abs(self.vx) > top_speed:
                    self.vx = max(-top_speed, min(top_speed, self.vx))

            if press_down and not dashing:
                if self.on_ground:
                    self.drop_through_timer = 10
                    self.on_ground = False
                elif self.vy > 0:
                    self.vy = max(self.vy, FAST_FALL_SPEED * 0.75)

        if wind_vx != 0.0 and self.dodge_timer <= 0 and not self.shielding:
            self.vx += wind_vx

        if self.dodge_timer > 0 or self.grab_timer > 0:
            self.vx *= 0.9
        elif dashing:
            self.vx *= 0.96
        elif self.on_ground:
            self.vx *= GROUND_FRICTION
            if abs(self.vx) < 0.1:
                self.vx = 0
        else:
            self.vx *= AIR_FRICTION

        if not self.on_ground and self.dodge_timer <= 0:
            self.vy = min(self.vy + GRAVITY, MAX_FALL_SPEED)

        self.rect.x += int(round(self.vx))
        for plat in platforms:
            if not plat.one_way and self.rect.colliderect(plat.rect):
                if self.vx > 0:
                    self.rect.right = plat.rect.left
                elif self.vx < 0:
                    self.rect.left = plat.rect.right
                self.vx = 0

        self.rect.y += int(round(self.vy))
        self.on_ground = False

        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if plat.one_way:
                    if (
                        self.vy >= 0
                        and self.drop_through_timer == 0
                        and self.prev_bottom <= plat.rect.top + 8
                    ):
                        self.rect.bottom = plat.rect.top
                        self.rect.x += plat.dx
                        self.vy = 0
                        self.on_ground = True
                        self.jump_rise_timer = 0
                        self.jumps_left = self.max_jumps
                else:
                    if self.vy > 0:
                        self.rect.bottom = plat.rect.top
                        self.rect.x += plat.dx
                        self.vy = 0
                        self.on_ground = True
                        self.jump_rise_timer = 0
                        self.jumps_left = self.max_jumps
                    elif self.vy < 0:
                        self.rect.top = plat.rect.bottom
                        self.vy = 0

        if (
            not self.on_ground
            and self.vy > 0
            and self.hitstun == 0
            and self.shield_break_stun == 0
            and self.ledge_cooldown == 0
            and platforms
        ):
            main_plat = platforms[0]
            left_ledge = pygame.Rect(
                main_plat.rect.left - 24, main_plat.rect.top - 10, 28, 36
            )
            right_ledge = pygame.Rect(
                main_plat.rect.right - 4, main_plat.rect.top - 10, 28, 36
            )
            if self.rect.colliderect(left_ledge) and self.facing == 1:
                self.ledge_grabbed = True
                self.ledge_side = -1
                self.rect.right = main_plat.rect.left + 2
                self.rect.top = main_plat.rect.top + 4
                self.vx = 0.0
                self.vy = 0.0
                self.jumps_left = self.max_jumps
                self.invuln_timer = max(self.invuln_timer, 45)
            elif self.rect.colliderect(right_ledge) and self.facing == -1:
                self.ledge_grabbed = True
                self.ledge_side = 1
                self.rect.left = main_plat.rect.right - 2
                self.rect.top = main_plat.rect.top + 4
                self.vx = 0.0
                self.vy = 0.0
                self.jumps_left = self.max_jumps
                self.invuln_timer = max(self.invuln_timer, 45)

    def update(
        self,
        keys,
        platforms,
        wind_vx=0.0,
        afterimages=None,
        sfx=None,
        volume=0.6,
    ):
        move_dir = 0
        if keys[self.controls["left"]]:
            move_dir -= 1
        if keys[self.controls["right"]]:
            move_dir += 1
        press_down = bool(keys[self.controls["down"]])
        hold_shield = bool(keys[self.controls["dodge"]])
        hold_attack = bool(keys[self.controls["attack"]])
        self.step_physics(
            move_dir,
            press_down,
            platforms,
            allow_direction_change=True,
            wind_vx=wind_vx,
            afterimages=afterimages,
            hold_shield=hold_shield,
            hold_attack=hold_attack,
            sfx=sfx,
            volume=volume,
        )

    def draw(
        self,
        surface,
        offset_x=0,
        offset_y=0,
        show_training_boxes=False,
    ):
        shifted_rect = self.rect.move(offset_x, offset_y)

        if self.special_meter >= 100.0:
            aura = shifted_rect.inflate(10, 10)
            pygame.draw.rect(
                surface, METER_READY_COLOR, aura, width=2, border_radius=8
            )
        elif self.power_boost_timer > 0:
            aura = shifted_rect.inflate(8, 8)
            pygame.draw.rect(
                surface, ARCADE_NEON_YELLOW, aura, width=2, border_radius=8
            )

        if self.charging_smash:
            pulse = 4 + (self.smash_charge_frames % 6)
            pygame.draw.rect(
                surface,
                ARCADE_NEON_YELLOW,
                shifted_rect.inflate(pulse * 2, pulse * 2),
                width=2,
                border_radius=10,
            )

        if self.parry_window > 0:
            pygame.draw.circle(
                surface, PARRY_COLOR, shifted_rect.center, 42, width=3
            )

        dash_spd = getattr(
            self,
            "_net_dash_vx",
            self.current_move.get("dash_vx", 0.0) if self.current_move else 0.0,
        )

        if self.sprite:
            img = self.sprite if self.facing == 1 else self.sprite_flipped

            if self.invuln_timer > 0:
                img = img.copy()
                blink_alpha = 115 if (self.invuln_timer % 6 < 3) else 190
                img.set_alpha(blink_alpha)

            if self.hitstun > 0:
                angle = -25 * self.facing
                img = pygame.transform.rotate(img, angle)
                draw_rect = img.get_rect(center=shifted_rect.center)
                surface.blit(img, draw_rect)
            elif dash_spd >= 8.0:
                angle = 22 * self.facing
                img = pygame.transform.rotate(img, angle)
                draw_rect = img.get_rect(midbottom=shifted_rect.midbottom)
                surface.blit(img, draw_rect)
            else:
                draw_rect = img.get_rect(midbottom=shifted_rect.midbottom)
                surface.blit(img, draw_rect)
        else:
            body_color = (
                (255, 255, 255) if (self.hitstun % 4 >= 2) else self.color
            )
            pygame.draw.rect(surface, body_color, shifted_rect, border_radius=6)

            eye_x = (
                shifted_rect.right - 13
                if self.facing == 1
                else shifted_rect.left + 5
            )
            eye_rect = pygame.Rect(eye_x, shifted_rect.top + 13, 8, 8)
            pygame.draw.rect(surface, (20, 20, 25), eye_rect)

        if self.shielding and self.shield_hp > 0:
            rad = max(14, int(44 * (self.shield_hp / 100.0)))
            bubble = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                bubble, (*self.color[:3], 85), (rad, rad), rad
            )
            pygame.draw.circle(
                bubble, (*self.color[:3], 220), (rad, rad), rad, width=3
            )
            surface.blit(
                bubble, bubble.get_rect(center=shifted_rect.center).topleft
            )

        if self.shield_break_stun > 0:
            for si in range(3):
                ang = (self.shield_break_stun * 0.18) + si * (math.tau / 3)
                sx = shifted_rect.centerx + int(math.cos(ang) * 20)
                sy = shifted_rect.top - 12 + int(math.sin(ang) * 6)
                pygame.draw.circle(surface, ARCADE_NEON_YELLOW, (sx, sy), 4)

        if self.attack_timer == 0 and self.attack_delay > 0:
            pygame.draw.rect(
                surface,
                ARCADE_NEON_PINK,
                pygame.Rect(
                    shifted_rect.left,
                    shifted_rect.top - 10,
                    shifted_rect.width,
                    4,
                ),
                border_radius=2,
            )

        gb = self.get_grab_box()
        if gb:
            pygame.draw.rect(
                surface,
                ARCADE_NEON_CYAN,
                gb.move(offset_x, offset_y),
                width=2,
                border_radius=6,
            )

        hb = self.get_hitbox()
        if hb:
            pygame.draw.rect(
                surface,
                HITBOX_COLOR,
                hb.move(offset_x, offset_y),
                border_radius=4,
            )
            if show_training_boxes:
                pygame.draw.rect(
                    surface,
                    ARCADE_NEON_PINK,
                    hb.move(offset_x, offset_y),
                    width=2,
                    border_radius=4,
                )

        if show_training_boxes:
            pygame.draw.rect(
                surface, CPU_COLOR, shifted_rect, width=1, border_radius=4
            )


class CpuController:
    def __init__(self, fighter, difficulty="Média"):
        self.fighter = fighter
        self.difficulty = difficulty
        self.attack_cooldown = 0
        self.jump_cooldown = 0
        self.decision_timer = 0
        self.desired_dir = 0

    def set_difficulty(self, difficulty):
        if difficulty in CPU_DIFFICULTIES:
            self.difficulty = difficulty
            self.decision_timer = 0
            self.attack_cooldown = min(self.attack_cooldown, 12)

    def reset(self):
        self.attack_cooldown = 0
        self.jump_cooldown = 0
        self.decision_timer = 0
        self.desired_dir = 0

    def update(
        self,
        target,
        platforms,
        projectiles,
        particles,
        popups,
        sfx=None,
        volume=0.6,
        training_mode=False,
        wind_vx=0.0,
        afterimages=None,
    ):
        f = self.fighter
        if training_mode:
            if f.hitstun > 0:
                self.step_with_dir(
                    0, False, platforms, wind_vx=0.0, afterimages=afterimages
                )
            else:
                f.vx = 0.0
                if f.on_ground:
                    f.vy = 0.0
                self.step_with_dir(
                    0, False, platforms, wind_vx=0.0, afterimages=afterimages
                )
            return

        cfg = CPU_DIFFICULTIES.get(self.difficulty, CPU_DIFFICULTIES["Média"])

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1

        if f.ledge_grabbed:
            f.jump()
            self.step_with_dir(
                0, False, platforms, wind_vx=wind_vx, afterimages=afterimages
            )
            return

        if f.hitstun > 0 or f.shield_break_stun > 0:
            if (
                f.hitstun > 0
                and self.difficulty == "Difícil"
                and f.dodge_cooldown == 0
                and random.random() < 0.08
            ):
                f.dodge(sfx, volume)
            self.step_with_dir(
                0, False, platforms, wind_vx=wind_vx, afterimages=afterimages
            )
            return

        stage_left, stage_right, stage_top = 220, 980, 535
        offstage = (
            f.rect.centerx < stage_left
            or f.rect.centerx > stage_right
            or f.rect.bottom > stage_top + 25
        )

        press_down = False

        if offstage:
            center_x = (stage_left + stage_right) // 2
            move_dir = 1 if center_x > f.rect.centerx else -1
            if self.jump_cooldown == 0 and f.vy > cfg["recovery_jump_vy"]:
                f.jump()
                self.jump_cooldown = cfg["jump_cooldown"]
        else:
            if self.decision_timer > 0:
                self.decision_timer -= 1
            else:
                if random.random() < cfg["idle_chance"]:
                    self.desired_dir = 0
                else:
                    dx = target.rect.centerx - f.rect.centerx
                    deadzone = 34 if self.difficulty == "Difícil" else 52
                    if abs(dx) > deadzone:
                        self.desired_dir = 1 if dx > 0 else -1
                    else:
                        self.desired_dir = 0

                low_d, high_d = cfg["decision_range"]
                self.decision_timer = random.randint(low_d, high_d)

            move_dir = self.desired_dir
            dy = target.rect.centery - f.rect.centery

            if dy < -72 and self.jump_cooldown == 0 and f.vy >= -1.2:
                f.jump()
                self.jump_cooldown = cfg["jump_cooldown"]
            elif dy > 95 and f.on_ground and f.rect.bottom < stage_top - 10:
                press_down = True

            dx_abs = abs(target.rect.centerx - f.rect.centerx)

            if (
                f.special_meter >= 100.0
                and dx_abs < 360
                and abs(dy) < 120
                and random.random() < 0.25
            ):
                if dx_abs > 10:
                    f.facing = (
                        1 if target.rect.centerx > f.rect.centerx else -1
                    )
                if f.trigger_ultimate(
                    2, target, projectiles, particles, popups, sfx, volume
                ):
                    self.attack_cooldown = 20
                    self.step_with_dir(
                        0,
                        False,
                        platforms,
                        wind_vx=wind_vx,
                        afterimages=afterimages,
                    )
                    return

            if (
                f.attack_timer == 0
                and f.attack_delay == 0
                and self.attack_cooldown == 0
                and dx_abs < cfg["attack_reach_x"]
                and abs(dy) < cfg["attack_reach_y"]
                and random.random() < cfg["attack_chance"]
            ):
                if dx_abs > 10:
                    f.facing = (
                        1 if target.rect.centerx > f.rect.centerx else -1
                    )

                if (
                    (target.dodge_timer > 0 or target.shielding)
                    and dx_abs < 62
                    and f.grab_cooldown == 0
                ):
                    f.grab(sfx, volume)
                elif not f.on_ground and f.vy > 1.5 and dy > 10:
                    f.trigger_move("underdive", sfx, volume)
                elif not f.on_ground and f.vy < -1.5 and dy < -15:
                    f.trigger_move("uppercut", sfx, volume)
                elif (
                    f.on_ground
                    and 55 < dx_abs < 125
                    and random.random() < 0.45
                ):
                    f.trigger_move("rasteira", sfx, volume)
                elif dy < -32 or random.random() < 0.2:
                    f.trigger_move("up", sfx, volume)
                elif dx_abs > 62 or random.random() < 0.35:
                    f.trigger_move("side", sfx, volume)
                else:
                    f.trigger_move("neutral", sfx, volume)

                low_c, high_c = cfg["attack_cooldown_range"]
                self.attack_cooldown = random.randint(low_c, high_c)

        self.step_with_dir(
            move_dir,
            press_down,
            platforms,
            wind_vx=wind_vx,
            afterimages=afterimages,
        )

    def step_with_dir(
        self, move_dir, press_down, platforms, wind_vx=0.0, afterimages=None
    ):
        self.fighter.step_physics(
            move_dir,
            press_down,
            platforms,
            allow_direction_change=True,
            wind_vx=wind_vx,
            afterimages=afterimages,
        )


def spawn_hit_particles(particles, x, y, color, count=8):
    for _ in range(count):
        ang = random.uniform(0, math.tau)
        spd = random.uniform(2.0, 6.5)
        particles.append(
            Particle(
                x,
                y,
                math.cos(ang) * spd,
                math.sin(ang) * spd,
                color,
                life=random.randint(12, 20),
                radius=random.randint(3, 6),
            )
        )


def check_combat(
    attacker,
    defender,
    particles,
    popups,
    sfx=None,
    volume=0.6,
    sudden_death=False,
):
    grab_box = attacker.get_grab_box()
    if grab_box and grab_box.colliderect(defender.rect):
        attacker.grab_registered = True
        attacker.grab_timer = 0
        defender.shielding = False
        throw_dmg = 9.0
        outcome = defender.take_hit(
            damage=throw_dmg,
            base_kb=8.8,
            scaling_kb=0.16,
            angle_deg=48,
            attacker_facing=attacker.facing,
            ignore_dodge=True,
            sudden_death=sudden_death,
        )
        if outcome == "hit":
            attacker.register_combo_hit("Arremesso", throw_dmg)
            spawn_hit_particles(
                particles,
                defender.rect.centerx,
                defender.rect.centery,
                ARCADE_NEON_CYAN,
                count=12,
            )
            popups.append(
                DamagePopup(
                    defender.rect.centerx,
                    defender.rect.top - 12,
                    f"GRAB -{int(throw_dmg)}%",
                    ARCADE_NEON_CYAN,
                )
            )
            if sfx:
                sfx.play("hit", volume)
            return 5, 5

    hitbox = attacker.get_hitbox()
    move = attacker.current_move
    if (
        hitbox
        and move
        and not attacker.hit_registered
        and hitbox.colliderect(defender.rect)
    ):
        attacker.hit_registered = True

        if defender.hitstun <= 0:
            attacker.combo_count = 0

        dmg_mult = 1.2 if attacker.power_boost_timer > 0 else 1.0
        dealt = round(move["damage"] * dmg_mult, 1)

        outcome = defender.take_hit(
            damage=dealt,
            base_kb=move["base_kb"],
            scaling_kb=move["scaling_kb"],
            angle_deg=move["angle_deg"],
            attacker_facing=attacker.facing,
            sudden_death=sudden_death,
        )
        if outcome == "parry":
            attacker.attack_delay = max(attacker.attack_delay, 16)
            spawn_hit_particles(
                particles,
                defender.rect.centerx,
                defender.rect.centery,
                PARRY_COLOR,
                count=16,
            )
            popups.append(
                DamagePopup(
                    defender.rect.centerx,
                    defender.rect.top - 16,
                    "PARRY! +25%",
                    PARRY_COLOR,
                    life=36,
                )
            )
            if sfx:
                sfx.play("parry", volume)
            return 8, 5
        elif outcome == "shield":
            spawn_hit_particles(
                particles,
                defender.rect.centerx,
                defender.rect.centery,
                defender.color,
                count=8,
            )
            popups.append(
                DamagePopup(
                    defender.rect.centerx,
                    defender.rect.top - 14,
                    "SHIELD!",
                    defender.color,
                    life=24,
                )
            )
            if sfx:
                sfx.play("blip", volume)
            return 3, 2
        elif outcome == "shield_break":
            spawn_hit_particles(
                particles,
                defender.rect.centerx,
                defender.rect.centery,
                ARCADE_NEON_YELLOW,
                count=22,
            )
            popups.append(
                DamagePopup(
                    defender.rect.centerx,
                    defender.rect.top - 22,
                    "SHIELD BREAK!",
                    ARCADE_NEON_YELLOW,
                    life=48,
                )
            )
            if sfx:
                sfx.play("shield_break", volume)
            return 12, 9
        elif outcome == "hit":
            attacker.register_combo_hit(move["name"], dealt)
            hit_pos = hitbox.center
            spawn_hit_particles(
                particles, hit_pos[0], hit_pos[1], HITBOX_COLOR, count=9
            )
            popups.append(
                DamagePopup(
                    defender.rect.centerx,
                    defender.rect.top - 10,
                    f"-{int(round(dealt))}%",
                    HITBOX_COLOR,
                )
            )
            if sfx:
                sfx.play("hit", volume)
            shake = 7 if dealt >= 12.0 else 3
            return move["hitstop"], shake
    return 0, 0


def check_blast_zones(
    fighter,
    attacker,
    particles,
    ko_beams,
    sfx=None,
    volume=0.6,
    training_mode=False,
):
    margin = 200
    hit_left = fighter.rect.right < -margin
    hit_right = fighter.rect.left > WIDTH + margin
    hit_bottom = fighter.rect.top > HEIGHT + margin
    hit_top = fighter.rect.bottom < -margin * 1.5

    if hit_left or hit_right or hit_bottom or hit_top:
        bx = max(30, min(WIDTH - 30, fighter.rect.centerx))
        by = max(30, min(HEIGHT - 30, fighter.rect.centery))
        if hit_left:
            beam_ang = 0
        elif hit_right:
            beam_ang = 180
        elif hit_bottom:
            beam_ang = -90
        else:
            beam_ang = 90

        ko_beams.append(KOBlastBeam(bx, by, beam_ang, fighter.color))
        spawn_hit_particles(
            particles,
            bx,
            by,
            ARCADE_NEON_PINK,
            count=20,
        )
        if sfx:
            sfx.play("ko", volume)
        if training_mode:
            fighter.reset(respawn_invuln=45)
            return False
        fighter.stocks = max(0, fighter.stocks - 1)
        finisher = (
            attacker.last_combo_label.split(" (")[0]
            if attacker.last_combo_label
            else "Ring Out"
        )
        attacker.ko_moves_scored.append(finisher)
        if fighter.stocks > 0:
            fighter.reset(respawn_invuln=72)
        return True
    return False


def draw_offscreen_magnifier(surface, fighter, small_font):
    if (
        0 <= fighter.rect.centerx <= WIDTH
        and 0 <= fighter.rect.centery <= HEIGHT
    ):
        return
    cx = max(36, min(WIDTH - 36, fighter.rect.centerx))
    cy = max(68, min(HEIGHT - 110, fighter.rect.centery))
    pygame.draw.circle(surface, PANEL_COLOR, (cx, cy), 26)
    pygame.draw.circle(surface, fighter.color, (cx, cy), 26, width=3)
    if fighter.sprite:
        mini = pygame.transform.smoothscale(fighter.sprite, (30, 34))
        surface.blit(mini, mini.get_rect(center=(cx, cy - 3)))
    pct_s = small_font.render(f"{int(fighter.damage_pct)}%", True, TEXT_COLOR)
    surface.blit(pct_s, pct_s.get_rect(center=(cx, cy + 16)))


def draw_clock_top_right(surface, small_font):
    now_str = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    clock_surf = small_font.render(now_str, True, ARCADE_NEON_CYAN)
    box_w = clock_surf.get_width() + 18
    box_h = clock_surf.get_height() + 8
    box_rect = pygame.Rect(WIDTH - box_w - 22, 18, box_w, box_h)
    pygame.draw.rect(surface, PANEL_COLOR, box_rect, border_radius=5)
    pygame.draw.rect(surface, PANEL_BORDER, box_rect, width=1, border_radius=5)
    surface.blit(clock_surf, clock_surf.get_rect(center=box_rect.center))


def draw_arcade_backdrop(
    surface,
    tick_count,
    small_font=None,
    bg_color=BG_COLOR,
    grid_color=GRID_COLOR,
):
    surface.fill(bg_color)

    spacing = 48
    scroll_y = tick_count % spacing
    for x in range(0, WIDTH + 1, spacing):
        pygame.draw.line(surface, grid_color, (x, 0), (x, HEIGHT), 1)
    for y in range(-spacing + scroll_y, HEIGHT + 1, spacing):
        pygame.draw.line(surface, grid_color, (0, y), (WIDTH, y), 1)

    pygame.draw.rect(
        surface,
        ARCADE_NEON_CYAN,
        pygame.Rect(8, 8, WIDTH - 16, HEIGHT - 16),
        width=2,
        border_radius=12,
    )

    if small_font is not None:
        draw_clock_top_right(surface, small_font)


def draw_meter_bar(surface, x, y, w, h, meter_pct, small_font, align_right=False):
    bg_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, PANEL_COLOR, bg_rect, border_radius=4)
    fill_w = int(w * max(0.0, min(1.0, meter_pct / 100.0)))
    if fill_w > 0:
        fill_x = x + (w - fill_w) if align_right else x
        bar_col = (
            METER_READY_COLOR
            if meter_pct >= 100.0
            else (ARCADE_NEON_PINK if meter_pct >= 50.0 else ARCADE_NEON_CYAN)
        )
        pygame.draw.rect(
            surface, bar_col, pygame.Rect(fill_x, y, fill_w, h), border_radius=4
        )
    mid_x = x + w // 2
    pygame.draw.line(surface, TEXT_COLOR, (mid_x, y), (mid_x, y + h), 1)
    pygame.draw.rect(surface, PANEL_BORDER, bg_rect, width=1, border_radius=4)
    lbl_text = (
        f"FINAL SMASH! ({int(meter_pct)}%)"
        if meter_pct >= 100.0
        else (
            f"RC PRONTO ({int(meter_pct)}%)"
            if meter_pct >= 50.0
            else f"ESPECIAL {int(meter_pct)}%"
        )
    )
    lbl = small_font.render(
        lbl_text,
        True,
        METER_READY_COLOR if meter_pct >= 100.0 else MUTED_TEXT,
    )
    surface.blit(lbl, lbl.get_rect(center=bg_rect.center))


def draw_stock_icons(surface, fighter, start_x, y, small_font, training_mode):
    if training_mode:
        t = small_font.render("TREINO", True, CPU_COLOR)
        surface.blit(t, (start_x, y))
        return
    for i in range(fighter.stocks):
        ix = start_x + i * 24
        if fighter.sprite:
            icon = pygame.transform.smoothscale(fighter.sprite, (20, 22))
            surface.blit(icon, (ix, y - 2))
        else:
            pygame.draw.circle(surface, fighter.color, (ix + 9, y + 9), 8)


def draw_hud(
    surface,
    font,
    combo_font,
    small_font,
    p1,
    p2,
    cpu_enabled,
    cpu_difficulty,
    training_mode,
    sudden_death=False,
    net_role=None,
):
    top_bar = pygame.Rect(18, 16, WIDTH - 36, 38)
    pygame.draw.rect(surface, PANEL_COLOR, top_bar, border_radius=6)
    pygame.draw.rect(surface, PANEL_BORDER, top_bar, width=1, border_radius=6)

    if sudden_death:
        sd_surf = combo_font.render(
            "SUDDEN DEATH! (KNOCKBACK +25%)", True, ARCADE_NEON_PINK
        )
        surface.blit(sd_surf, sd_surf.get_rect(center=(WIDTH // 2, 74)))

    p1_pct_col = (
        ARCADE_NEON_PINK
        if p1.damage_pct >= 110
        else (ARCADE_NEON_YELLOW if p1.damage_pct >= 60 else p1.color)
    )
    p1_tag = " [HOST]" if net_role else ""
    p1_text = font.render(
        f"{p1.name}{p1_tag}: {int(p1.damage_pct)}%",
        True,
        p1_pct_col,
    )
    surface.blit(p1_text, (45, HEIGHT - 74))
    draw_stock_icons(
        surface,
        p1,
        45 + p1_text.get_width() + 14,
        HEIGHT - 72,
        small_font,
        training_mode,
    )
    draw_meter_bar(surface, 45, HEIGHT - 40, 260, 18, p1.special_meter, small_font)

    if p1.combo_display_timer > 0 and p1.last_combo_label:
        c1_surf = combo_font.render(p1.last_combo_label, True, COMBO_COLOR)
        surface.blit(c1_surf, (45, HEIGHT - 104))

    if net_role:
        p2_mode = " [ONLINE P2]"
    elif cpu_enabled:
        p2_mode = f" [CPU: {cpu_difficulty}]"
    else:
        p2_mode = " [P2]"
    p2_pct_col = (
        ARCADE_NEON_PINK
        if p2.damage_pct >= 110
        else (
            ARCADE_NEON_YELLOW
            if p2.damage_pct >= 60
            else (CPU_COLOR if cpu_enabled else p2.color)
        )
    )
    p2_text = font.render(
        f"{p2.name}{p2_mode}: {int(p2.damage_pct)}%",
        True,
        p2_pct_col,
    )
    p2_x = WIDTH - p2_text.get_width() - 125
    surface.blit(p2_text, (p2_x, HEIGHT - 74))
    draw_stock_icons(
        surface,
        p2,
        p2_x + p2_text.get_width() + 12,
        HEIGHT - 72,
        small_font,
        training_mode,
    )
    draw_meter_bar(
        surface,
        WIDTH - 305,
        HEIGHT - 40,
        260,
        18,
        p2.special_meter,
        small_font,
        align_right=True,
    )

    if p2.combo_display_timer > 0 and p2.last_combo_label:
        c2_surf = combo_font.render(p2.last_combo_label, True, COMBO_COLOR)
        surface.blit(c2_surf, (WIDTH - c2_surf.get_width() - 45, HEIGHT - 104))


def draw_button(surface, rect, text, font, hovered):
    color = BUTTON_HOVER if hovered else BUTTON_IDLE
    border = ARCADE_NEON_YELLOW if hovered else PANEL_BORDER
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, width=2, border_radius=8)
    label = font.render(text, True, TEXT_COLOR)
    surface.blit(label, label.get_rect(center=rect.center))


def get_char_card_rects(roster_len):
    cols = 4
    card_w, card_h = 250, 146
    gap_x, gap_y = 24, 18
    total_w = cols * card_w + (cols - 1) * gap_x
    start_x = (WIDTH - total_w) // 2
    start_y = 126

    rects = []
    for idx in range(roster_len):
        row = idx // cols
        col = idx % cols
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        rects.append(pygame.Rect(x, y, card_w, card_h))
    return rects


def draw_main_menu(
    surface,
    title_font,
    btn_font,
    small_font,
    selected_idx,
    mouse_pos,
    jukebox,
    records,
    tick_count,
):
    draw_arcade_backdrop(surface, tick_count, small_font)

    title = title_font.render("ARCADE SMASH", True, ARCADE_NEON_YELLOW)
    tag = small_font.render(
        "SMASH EDITION  •  SHIELD • SMASH ATTACKS • MULTIPLAYER ONLINE/LAN",
        True,
        ARCADE_NEON_PINK,
    )
    subtitle = small_font.render(
        "Use Setas/W-S e Enter ou clique nos botões",
        True,
        MUTED_TEXT,
    )
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 92)))
    surface.blit(tag, tag.get_rect(center=(WIDTH // 2, 130)))
    surface.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 154)))

    options = [
        "Versus (1P / 2P Local)",
        "Modo Arcade (Torre)",
        "Multiplayer (Criar / Entrar)",
        "Move List & Lutadores",
        "Configurações",
        "Jukebox",
    ]
    for idx, label in enumerate(options):
        rect = pygame.Rect(WIDTH // 2 - 210, 178 + idx * 58, 420, 46)
        is_active = (idx == selected_idx) or rect.collidepoint(mouse_pos)
        draw_button(surface, rect, label, btn_font, is_active)

    best_t = records.get("best_time_sec")
    rec_text = (
        f"Recorde Torre: {best_t:.1f}s ({records.get('best_time_char', '')})  •  Combo Máx: {records.get('best_combo', 0)}x"
        if best_t is not None
        else "Recorde Torre Arcade: Ainda sem conclusão registrada"
    )
    rec_surf = small_font.render(rec_text, True, ARCADE_NEON_YELLOW)
    surface.blit(rec_surf, rec_surf.get_rect(center=(WIDTH // 2, 558)))

    now_playing = (
        f"♪ {jukebox.playing_track}"
        if jukebox.playing_track and not jukebox.is_paused
        else "Jukebox: coloque .mp3, .ogg ou .wav na pasta do jogo"
    )
    np_surf = small_font.render(now_playing, True, ARCADE_NEON_CYAN)
    surface.blit(np_surf, np_surf.get_rect(center=(WIDTH // 2, 588)))


def draw_multiplayer_lobby_screen(
    surface,
    title_font,
    btn_font,
    small_font,
    net,
    join_ip_input,
    editing_ip,
    p1_char_idx,
    p2_char_idx,
    stage_idx,
    mouse_pos,
    tick_count,
):
    draw_arcade_backdrop(surface, tick_count, small_font)

    title = title_font.render(
        "MULTIPLAYER ONLINE / LAN", True, ARCADE_NEON_YELLOW
    )
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 62)))

    sub = small_font.render(
        "Crie uma sala como Host (P1) ou digite o IP da sala para entrar como P2",
        True,
        ARCADE_NEON_CYAN,
    )
    surface.blit(sub, sub.get_rect(center=(WIDTH // 2, 98)))

    # Card Host (Esquerda)
    host_box = pygame.Rect(85, 134, 495, 290)
    pygame.draw.rect(surface, PANEL_COLOR, host_box, border_radius=12)
    pygame.draw.rect(
        surface,
        ARCADE_NEON_YELLOW if net.role == "host" else PANEL_BORDER,
        host_box,
        width=2,
        border_radius=12,
    )
    h_title = btn_font.render("1. CRIAR SALA (HOST / P1)", True, P1_COLOR)
    surface.blit(h_title, h_title.get_rect(center=(host_box.centerx, 168)))

    ip_lbl = small_font.render(
        f"Seu IP Local: {net.host_ip}  |  Porta: {NET_PORT}",
        True,
        TEXT_COLOR,
    )
    surface.blit(ip_lbl, ip_lbl.get_rect(center=(host_box.centerx, 204)))

    c1_name = CHARACTER_ROSTER[p1_char_idx]["name"]
    st_name = STAGE_PRESETS[stage_idx]["name"]
    sel_info = small_font.render(
        f"Lutador Host: < {c1_name} >   •   Arena: < {st_name} >",
        True,
        ARCADE_NEON_CYAN,
    )
    surface.blit(sel_info, sel_info.get_rect(center=(host_box.centerx, 238)))

    btn_host = pygame.Rect(host_box.x + 48, 272, 400, 48)
    btn_h_char = pygame.Rect(host_box.x + 48, 332, 192, 42)
    btn_h_stage = pygame.Rect(host_box.x + 256, 332, 192, 42)

    draw_button(
        surface,
        btn_host,
        "Reiniciar Sala" if net.role == "host" else "Abrir Sala (Host)",
        btn_font,
        btn_host.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        btn_h_char,
        "Trocar Lutador",
        small_font,
        btn_h_char.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        btn_h_stage,
        "Trocar Arena",
        small_font,
        btn_h_stage.collidepoint(mouse_pos),
    )

    # Card Join (Direita)
    join_box = pygame.Rect(620, 134, 495, 290)
    pygame.draw.rect(surface, PANEL_COLOR, join_box, border_radius=12)
    pygame.draw.rect(
        surface,
        ARCADE_NEON_YELLOW if net.role == "client" else PANEL_BORDER,
        join_box,
        width=2,
        border_radius=12,
    )
    j_title = btn_font.render("2. ENTRAR EM SALA (P2)", True, P2_COLOR)
    surface.blit(j_title, j_title.get_rect(center=(join_box.centerx, 168)))

    ip_box = pygame.Rect(join_box.x + 48, 196, 400, 42)
    pygame.draw.rect(surface, BG_COLOR, ip_box, border_radius=6)
    pygame.draw.rect(
        surface,
        ARCADE_NEON_PINK if editing_ip else PANEL_BORDER,
        ip_box,
        width=2,
        border_radius=6,
    )
    cursor = "_" if (editing_ip and (tick_count // 20) % 2 == 0) else ""
    ip_txt = small_font.render(
        f"IP do Host: {join_ip_input}{cursor}", True, TEXT_COLOR
    )
    surface.blit(ip_txt, ip_txt.get_rect(center=ip_box.center))

    c2_name = CHARACTER_ROSTER[p2_char_idx]["name"]
    c2_info = small_font.render(
        f"Lutador Cliente (P2): < {c2_name} >", True, ARCADE_NEON_CYAN
    )
    surface.blit(c2_info, c2_info.get_rect(center=(join_box.centerx, 254)))

    btn_join = pygame.Rect(join_box.x + 48, 282, 400, 48)
    btn_j_char = pygame.Rect(join_box.x + 128, 340, 240, 40)

    draw_button(
        surface,
        btn_join,
        "Conectar na Sala",
        btn_font,
        btn_join.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        btn_j_char,
        "Trocar Lutador P2",
        small_font,
        btn_j_char.collidepoint(mouse_pos),
    )

    # Painel de Status & Início
    status_box = pygame.Rect(85, 444, 1030, 110)
    pygame.draw.rect(surface, PANEL_COLOR, status_box, border_radius=12)
    pygame.draw.rect(
        surface,
        CPU_COLOR if net.connected else PANEL_BORDER,
        status_box,
        width=2,
        border_radius=12,
    )
    st_col = CPU_COLOR if net.connected else ARCADE_NEON_YELLOW
    st_surf = btn_font.render(f"Status: {net.status_msg}", True, st_col)
    surface.blit(st_surf, st_surf.get_rect(center=(status_box.centerx, 478)))

    tip_net = small_font.render(
        "Dica: Para jogar online à distância sem abrir portas no roteador, use Radmin VPN, ZeroTier ou Hamachi e cole o IP virtual.",
        True,
        MUTED_TEXT,
    )
    surface.blit(tip_net, tip_net.get_rect(center=(status_box.centerx, 518)))

    back_rect = pygame.Rect(WIDTH // 2 - 260, 578, 230, 54)
    start_rect = pygame.Rect(WIDTH // 2 + 30, 578, 250, 54)
    draw_button(
        surface,
        back_rect,
        "Voltar ao Menu",
        btn_font,
        back_rect.collidepoint(mouse_pos),
    )
    if net.role == "host" and net.connected:
        draw_button(
            surface,
            start_rect,
            "INICIAR PARTIDA!",
            btn_font,
            start_rect.collidepoint(mouse_pos),
        )


def draw_character_select_screen(
    surface,
    title_font,
    btn_font,
    small_font,
    roster,
    sprites_map,
    p1_idx,
    p2_idx,
    p1_confirmed,
    cpu_enabled,
    arcade_mode,
    training_mode,
    mouse_pos,
    tick_count,
):
    draw_arcade_backdrop(surface, tick_count, small_font)

    hdr_text = (
        "MODO ARCADE - ESCOLHA SEU CAMPEÃO"
        if arcade_mode
        else "ESCOLHA SEU LUTADOR"
    )
    title = title_font.render(hdr_text, True, ARCADE_NEON_YELLOW)
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 58)))

    mode_tag = (
        "TORRE 4 LUTAS"
        if arcade_mode
        else ("TREINO [F2]" if training_mode else "VERSUS")
    )
    if arcade_mode:
        step_text = "P1: A/D escolhe • X: Aleatório • ENTER: Avançar para Cenário"
    else:
        step_text = (
            "P1: A/D escolhe • X: Aleatório • W/F/ENTER confirma"
            if not p1_confirmed
            else (
                "CPU: Setas escolhe • X: Aleatório • ENTER escolhe Cenário"
                if cpu_enabled
                else "P2: Setas escolhe • X: Aleatório • CIMA/ENTER escolhe Cenário"
            )
        )
    step_surf = small_font.render(
        f"{step_text}  •  [M] Move List  •  {mode_tag}",
        True,
        ARCADE_NEON_CYAN,
    )
    surface.blit(step_surf, step_surf.get_rect(center=(WIDTH // 2, 96)))

    card_rects = get_char_card_rects(len(roster))
    name_font = pygame.font.SysFont("consolas", 18, bold=True)

    for idx, (char, rect) in enumerate(zip(roster, card_rects)):
        is_p1 = idx == p1_idx
        is_p2 = (not arcade_mode) and (idx == p2_idx)
        hovered = rect.collidepoint(mouse_pos)

        bg = (48, 56, 86) if (is_p1 or is_p2 or hovered) else PANEL_COLOR
        pygame.draw.rect(surface, bg, rect, border_radius=10)

        border_color = PANEL_BORDER
        if is_p1 and is_p2:
            border_color = ARCADE_NEON_YELLOW
        elif is_p1:
            border_color = P1_COLOR
        elif is_p2:
            border_color = CPU_COLOR if cpu_enabled else P2_COLOR
        pygame.draw.rect(surface, border_color, rect, width=3, border_radius=10)

        spr = sprites_map.get(char["name"])
        if spr:
            mini_spr = pygame.transform.smoothscale(spr, (54, 64))
            spr_rect = mini_spr.get_rect(
                center=(rect.x + 42, rect.centery - 6)
            )
            surface.blit(mini_spr, spr_rect)
        else:
            ph = pygame.Rect(0, 0, 46, 58)
            ph.center = (rect.x + 42, rect.centery - 6)
            pygame.draw.rect(surface, char["color"], ph, border_radius=6)

        text_x = rect.x + 150
        name_surf = name_font.render(char["name"], True, TEXT_COLOR)
        surface.blit(
            name_surf, name_surf.get_rect(center=(text_x, rect.y + 52))
        )

        tag_surf = small_font.render(char["tag"], True, MUTED_TEXT)
        surface.blit(
            tag_surf, tag_surf.get_rect(center=(text_x, rect.y + 82))
        )

        if is_p1:
            b1 = small_font.render(
                "P1 OK" if p1_confirmed else "P1", True, P1_COLOR
            )
            surface.blit(b1, (rect.x + 10, rect.y + 8))
        if is_p2:
            b2_label = "CPU" if cpu_enabled else "P2"
            b2_col = CPU_COLOR if cpu_enabled else P2_COLOR
            b2 = small_font.render(b2_label, True, b2_col)
            surface.blit(b2, (rect.right - b2.get_width() - 10, rect.y + 8))

    summary = pygame.Rect(WIDTH // 2 - 460, 442, 920, 122)
    pygame.draw.rect(surface, PANEL_COLOR, summary, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, summary, width=2, border_radius=12)

    c1 = roster[p1_idx]
    c2 = roster[p2_idx]
    mirror_tag = (
        "  [MIRROR MATCH!]"
        if (not arcade_mode and p1_idx == p2_idx)
        else ""
    )
    if arcade_mode:
        vs_title = btn_font.render(
            f"{c1['name']} na Torre Arcade (4 Desafios)",
            True,
            ARCADE_NEON_YELLOW,
        )
    else:
        vs_title = btn_font.render(
            f"{c1['name']}   VS   {c2['name']}{mirror_tag}",
            True,
            ARCADE_NEON_YELLOW,
        )
    surface.blit(
        vs_title, vs_title.get_rect(center=(summary.centerx, summary.y + 28))
    )

    p1_moves = (
        f"P1 ({c1['name']}): Final Smash [{c1['ultimate_name']}] | "
        f"{c1['moveset']['side']['name']} | {c1['moveset']['uppercut']['name']}"
    )
    p2_moves = (
        "Dificuldade progressiva: Fácil → Média → Média → Difícil"
        if arcade_mode
        else (
            f"{'CPU' if cpu_enabled else 'P2'} ({c2['name']}): Final Smash [{c2['ultimate_name']}] | "
            f"{c2['moveset']['side']['name']} | {c2['moveset']['uppercut']['name']}"
        )
    )
    m1_s = small_font.render(p1_moves, True, P1_COLOR)
    m2_s = small_font.render(
        p2_moves, True, CPU_COLOR if (cpu_enabled or arcade_mode) else P2_COLOR
    )
    surface.blit(m1_s, m1_s.get_rect(center=(summary.centerx, summary.y + 68)))
    surface.blit(m2_s, m2_s.get_rect(center=(summary.centerx, summary.y + 96)))

    back_rect = pygame.Rect(WIDTH // 2 - 430, 586, 195, 52)
    rand_rect = pygame.Rect(WIDTH // 2 - 210, 586, 195, 52)
    moves_rect = pygame.Rect(WIDTH // 2 + 10, 586, 195, 52)
    next_rect = pygame.Rect(WIDTH // 2 + 230, 586, 195, 52)

    draw_button(
        surface, back_rect, "Voltar", btn_font, back_rect.collidepoint(mouse_pos)
    )
    draw_button(
        surface,
        rand_rect,
        "Aleatório [X]",
        btn_font,
        rand_rect.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        moves_rect,
        "Move List [M]",
        btn_font,
        moves_rect.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        next_rect,
        "Cenário →",
        btn_font,
        next_rect.collidepoint(mouse_pos),
    )


def get_stage_card_rects():
    rects = []
    for idx in range(len(STAGE_PRESETS)):
        col = idx % 2
        row = idx // 2
        x = 95 + col * 515
        y = 132 + row * 212
        rects.append(pygame.Rect(x, y, 495, 194))
    return rects


def draw_stage_preview_mini(surface, preview_rect, stage_data):
    pygame.draw.rect(surface, stage_data["bg_tint"], preview_rect, border_radius=8)
    pygame.draw.rect(
        surface, stage_data["grid_tint"], preview_rect, width=1, border_radius=8
    )
    scale_x = preview_rect.width / WIDTH
    scale_y = preview_rect.height / HEIGHT
    for px, py, pw, ph, one_way, amp_x, amp_y, _ in stage_data["platforms"]:
        rx = preview_rect.x + int(px * scale_x)
        ry = preview_rect.y + int(py * scale_y)
        rw = max(8, int(pw * scale_x))
        rh = max(4, int(ph * scale_y))
        col = stage_data["plat_color"] if one_way else stage_data["stage_color"]
        pygame.draw.rect(
            surface, col, pygame.Rect(rx, ry, rw, rh), border_radius=3
        )
        if amp_x != 0.0 or amp_y != 0.0:
            pygame.draw.rect(
                surface,
                ARCADE_NEON_YELLOW,
                pygame.Rect(rx, ry, rw, rh),
                width=1,
                border_radius=3,
            )


def draw_stage_select_screen(
    surface,
    title_font,
    btn_font,
    small_font,
    stage_idx,
    p1_name,
    p2_name,
    arcade_mode,
    training_mode,
    mouse_pos,
    tick_count,
):
    draw_arcade_backdrop(surface, tick_count, small_font)

    title = title_font.render(
        "ESCOLHA A ARENA DE COMBATE", True, ARCADE_NEON_YELLOW
    )
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 58)))

    matchup_label = (
        f"{p1_name} na Torre Arcade"
        if arcade_mode
        else f"{p1_name}  VS  {p2_name}"
    )
    sub = small_font.render(
        f"{matchup_label}  •  Setas/A-D para navegar • ENTER para iniciar a luta!",
        True,
        ARCADE_NEON_CYAN,
    )
    surface.blit(sub, sub.get_rect(center=(WIDTH // 2, 96)))

    card_rects = get_stage_card_rects()
    for idx, (st, rect) in enumerate(zip(STAGE_PRESETS, card_rects)):
        selected = idx == stage_idx
        hovered = rect.collidepoint(mouse_pos)
        bg = (46, 56, 88) if (selected or hovered) else PANEL_COLOR
        border = ARCADE_NEON_YELLOW if selected else PANEL_BORDER
        pygame.draw.rect(surface, bg, rect, border_radius=10)
        pygame.draw.rect(
            surface, border, rect, width=3 if selected else 2, border_radius=10
        )

        mini_rect = pygame.Rect(rect.x + 14, rect.y + 18, 210, 158)
        draw_stage_preview_mini(surface, mini_rect, st)

        tx = rect.x + 240
        st_name = btn_font.render(st["name"], True, TEXT_COLOR)
        surface.blit(st_name, (tx, rect.y + 22))

        sub_parts = st["subtitle"].split("•")
        for line_i, part in enumerate(sub_parts):
            s_surf = small_font.render(part.strip(), True, MUTED_TEXT)
            surface.blit(s_surf, (tx, rect.y + 62 + line_i * 22))

        haz_surf = small_font.render(
            f"Arena: {st['hazard_desc']}", True, ARCADE_NEON_CYAN
        )
        surface.blit(haz_surf, (tx, rect.y + 120))

        if selected:
            sel_tag = small_font.render(
                "★ ARENA SELECIONADA", True, ARCADE_NEON_YELLOW
            )
            surface.blit(sel_tag, (tx, rect.y + 152))

    back_rect = pygame.Rect(WIDTH // 2 - 360, 582, 220, 54)
    train_rect = pygame.Rect(WIDTH // 2 - 110, 582, 220, 54)
    fight_rect = pygame.Rect(WIDTH // 2 + 140, 582, 220, 54)

    draw_button(
        surface,
        back_rect,
        "← Lutadores",
        btn_font,
        back_rect.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        train_rect,
        f"Treino: {'ON' if training_mode else 'OFF'}",
        btn_font,
        train_rect.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        fight_rect,
        "LUTAR!",
        btn_font,
        fight_rect.collidepoint(mouse_pos),
    )


def draw_move_list_screen(
    surface,
    title_font,
    btn_font,
    small_font,
    roster,
    sprites_map,
    char_idx,
    p1_controls,
    mouse_pos,
    tick_count,
):
    draw_arcade_backdrop(surface, tick_count, small_font)

    title = title_font.render("MOVE LIST & LUTADORES", True, ARCADE_NEON_YELLOW)
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 52)))

    tab_w = 132
    gap = 8
    start_x = (WIDTH - (len(roster) * tab_w + (len(roster) - 1) * gap)) // 2
    for idx, ch in enumerate(roster):
        t_rect = pygame.Rect(start_x + idx * (tab_w + gap), 86, tab_w, 34)
        active = idx == char_idx or t_rect.collidepoint(mouse_pos)
        draw_button(surface, t_rect, ch["name"], small_font, active)

    char = roster[char_idx]
    stats = char["stats"]

    left_panel = pygame.Rect(40, 134, 370, 445)
    pygame.draw.rect(surface, PANEL_COLOR, left_panel, border_radius=12)
    pygame.draw.rect(surface, char["color"], left_panel, width=2, border_radius=12)

    spr = sprites_map.get(char["name"])
    if spr:
        big_spr = pygame.transform.smoothscale(spr, (84, 100))
        surface.blit(big_spr, (left_panel.x + 22, left_panel.y + 20))
    else:
        pygame.draw.rect(
            surface,
            char["color"],
            pygame.Rect(left_panel.x + 24, left_panel.y + 24, 76, 94),
            border_radius=8,
        )

    c_name = btn_font.render(char["name"], True, TEXT_COLOR)
    c_arch = small_font.render(char["archetype"], True, char["color"])
    surface.blit(c_name, (left_panel.x + 122, left_panel.y + 28))
    surface.blit(c_arch, (left_panel.x + 122, left_panel.y + 62))

    words = char["bio"].split()
    bio_lines = []
    cur = ""
    for w in words:
        if len(cur + " " + w) <= 42:
            cur = (cur + " " + w).strip()
        else:
            bio_lines.append(cur)
            cur = w
    if cur:
        bio_lines.append(cur)
    for li, line in enumerate(bio_lines[:3]):
        b_surf = small_font.render(line, True, MUTED_TEXT)
        surface.blit(b_surf, (left_panel.x + 20, left_panel.y + 132 + li * 20))

    spd_pct = min(1.0, max(0.2, (stats["max_run_speed"] - 4.0) / 2.0))
    weight_pct = min(1.0, max(0.2, (stats["kb_mult"] - 0.85) / 0.4))
    agility_pct = min(1.0, max(0.2, (1.2 - stats["lag_mult"]) / 0.35))
    stat_bars = [
        ("Velocidade", spd_pct, ARCADE_NEON_CYAN),
        ("Peso / Defesa", weight_pct, CPU_COLOR),
        ("Agilidade / Recovery", agility_pct, ARCADE_NEON_PINK),
    ]
    for si, (s_lbl, ratio, scol) in enumerate(stat_bars):
        sy = left_panel.y + 205 + si * 40
        lbl_s = small_font.render(s_lbl, True, TEXT_COLOR)
        surface.blit(lbl_s, (left_panel.x + 20, sy))
        bar_bg = pygame.Rect(left_panel.x + 20, sy + 18, 330, 10)
        pygame.draw.rect(surface, BG_COLOR, bar_bg, border_radius=4)
        pygame.draw.rect(
            surface,
            scol,
            pygame.Rect(bar_bg.x, bar_bg.y, int(330 * ratio), 10),
            border_radius=4,
        )

    ult_box = pygame.Rect(
        left_panel.x + 16, left_panel.y + 332, left_panel.width - 32, 98
    )
    pygame.draw.rect(surface, BG_COLOR, ult_box, border_radius=8)
    pygame.draw.rect(
        surface, METER_READY_COLOR, ult_box, width=1, border_radius=8
    )
    u_hdr = small_font.render(
        f"FINAL SMASH ({pygame.key.name(p1_controls['ultimate']).upper()}): {char['ultimate_name']}",
        True,
        METER_READY_COLOR,
    )
    surface.blit(u_hdr, (ult_box.x + 10, ult_box.y + 10))
    u_words = char["ultimate_desc"].split()
    u_lines = []
    cur = ""
    for w in u_words:
        if len(cur + " " + w) <= 40:
            cur = (cur + " " + w).strip()
        else:
            u_lines.append(cur)
            cur = w
    if cur:
        u_lines.append(cur)
    for ui, uline in enumerate(u_lines[:3]):
        us = small_font.render(uline, True, TEXT_COLOR)
        surface.blit(us, (ult_box.x + 10, ult_box.y + 34 + ui * 19))

    right_panel = pygame.Rect(428, 134, 732, 445)
    pygame.draw.rect(surface, PANEL_COLOR, right_panel, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, right_panel, width=2, border_radius=12)

    move_order = ["neutral", "side", "rasteira", "up", "uppercut", "underdive"]
    for mi, slot in enumerate(move_order):
        mv = char["moveset"][slot]
        row_rect = pygame.Rect(
            right_panel.x + 16, right_panel.y + 14 + mi * 54, 700, 46
        )
        pygame.draw.rect(surface, BG_COLOR, row_rect, border_radius=7)

        m_title = small_font.render(
            f"{mv['name']}  [{mv['input']}]", True, ARCADE_NEON_YELLOW
        )
        m_role = small_font.render(mv["role"], True, MUTED_TEXT)
        m_stats = small_font.render(
            f"Dano: {mv['damage']}%  |  Ativo: f{mv['active_start']}-{mv['active_end']}",
            True,
            ARCADE_NEON_CYAN,
        )
        surface.blit(m_title, (row_rect.x + 12, row_rect.y + 5))
        surface.blit(m_role, (row_rect.x + 12, row_rect.y + 24))
        surface.blit(
            m_stats, (row_rect.right - m_stats.get_width() - 12, row_rect.y + 14)
        )

    mech_rect = pygame.Rect(
        right_panel.x + 16, right_panel.y + 344, 700, 86
    )
    pygame.draw.rect(surface, (32, 38, 62), mech_rect, border_radius=8)
    k_dodge = pygame.key.name(p1_controls["dodge"]).upper()
    k_grab = pygame.key.name(p1_controls["grab"]).upper()
    k_rc = pygame.key.name(p1_controls["cancel"]).upper()
    m_line1 = small_font.render(
        f"• ESCUDO & PARRY ({k_dodge}): Toque rápido dá Parry (+25%); segurar abre Bolha de Escudo!",
        True,
        PARRY_COLOR,
    )
    m_line2 = small_font.render(
        f"• AGARRÃO ({k_grab}): Quebra escudo/esquiva!  • ROMAN CANCEL ({k_rc} com 50%): Cancela lag.",
        True,
        ARCADE_NEON_PINK,
    )
    m_line3 = small_font.render(
        "• SMASH ATTACK (Segure Direção + Ataque): Carrega até +42% dano • SMASH BALL: Dá Final Smash!",
        True,
        TEXT_COLOR,
    )
    surface.blit(m_line1, (mech_rect.x + 12, mech_rect.y + 10))
    surface.blit(m_line2, (mech_rect.x + 12, mech_rect.y + 34))
    surface.blit(m_line3, (mech_rect.x + 12, mech_rect.y + 58))

    prev_rect = pygame.Rect(WIDTH // 2 - 330, 594, 200, 50)
    next_rect = pygame.Rect(WIDTH // 2 - 100, 594, 200, 50)
    back_rect = pygame.Rect(WIDTH // 2 + 130, 594, 200, 50)

    draw_button(
        surface,
        prev_rect,
        "< Anterior",
        btn_font,
        prev_rect.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        next_rect,
        "Próximo >",
        btn_font,
        next_rect.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        back_rect,
        "Voltar",
        btn_font,
        back_rect.collidepoint(mouse_pos),
    )


def draw_settings_screen(
    surface,
    title_font,
    btn_font,
    small_font,
    selected_idx,
    mouse_pos,
    jukebox,
    cpu_enabled,
    cpu_difficulty,
    training_mode,
    tick_count,
):
    draw_arcade_backdrop(surface, tick_count, small_font)

    title = title_font.render("CONFIGURAÇÕES", True, ARCADE_NEON_CYAN)
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 88)))

    panel = pygame.Rect(WIDTH // 2 - 330, 140, 660, 465)
    pygame.draw.rect(surface, PANEL_COLOR, panel, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, panel, width=2, border_radius=12)

    vol_pct = int(jukebox.volume * 100)
    rows = [
        f"Volume Geral: {vol_pct}%   (< / >)",
        f"Modo CPU P2: {'LIGADO' if cpu_enabled else 'DESLIGADO'}",
        f"Dificuldade CPU: {cpu_difficulty}   (< / >)",
        f"Modo Treino (Hitboxes): {'LIGADO' if training_mode else 'DESLIGADO'}",
        "Remapear Controles (P1 / P2)",
        "Voltar ao Menu",
    ]

    for idx, text in enumerate(rows):
        rect = pygame.Rect(panel.x + 40, panel.y + 18 + idx * 72, 580, 52)
        hovered = (idx == selected_idx) or rect.collidepoint(mouse_pos)
        draw_button(surface, rect, text, btn_font, hovered)

    hint = small_font.render(
        "Use < / > ou clique para alterar (salva automaticamente)  •  ESC volta ao menu",
        True,
        MUTED_TEXT,
    )
    surface.blit(hint, hint.get_rect(center=(WIDTH // 2, 625)))


def get_remap_button_rects():
    rects = []
    for col_idx, player_id in enumerate((1, 2)):
        col_x = 135 + col_idx * 500
        for row_idx, (act_key, act_label) in enumerate(REMAP_ACTIONS):
            r = pygame.Rect(col_x, 182 + row_idx * 60, 430, 48)
            rects.append((r, player_id, act_key, act_label))
    back_rect = pygame.Rect(WIDTH // 2 - 140, 570, 280, 50)
    return rects, back_rect


def draw_controls_remap_screen(
    surface,
    title_font,
    btn_font,
    small_font,
    p1_controls,
    p2_controls,
    listening_target,
    mouse_pos,
    tick_count,
):
    draw_arcade_backdrop(surface, tick_count, small_font)

    title = title_font.render("REMAPEAR CONTROLES", True, ARCADE_NEON_YELLOW)
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 78)))

    sub_text = (
        "PRESSIONE A NOVA TECLA AGORA (ESC cancela)..."
        if listening_target
        else "Clique em uma ação para trocar a tecla • Salvo automaticamente"
    )
    sub = small_font.render(
        sub_text,
        True,
        ARCADE_NEON_PINK if listening_target else ARCADE_NEON_CYAN,
    )
    surface.blit(sub, sub.get_rect(center=(WIDTH // 2, 118)))

    h1 = btn_font.render("JOGADOR 1 (A/D/S Move)", True, P1_COLOR)
    h2 = btn_font.render("JOGADOR 2 (Setas Move)", True, P2_COLOR)
    surface.blit(h1, h1.get_rect(center=(350, 155)))
    surface.blit(h2, h2.get_rect(center=(850, 155)))

    rects, back_rect = get_remap_button_rects()
    for rect, pid, act_key, act_label in rects:
        ctrl_map = p1_controls if pid == 1 else p2_controls
        is_listening = listening_target == (pid, act_key)
        key_label = (
            "[AGUARDANDO TECLA...]"
            if is_listening
            else pygame.key.name(ctrl_map[act_key]).upper()
        )
        draw_button(
            surface,
            rect,
            f"{act_label}: {key_label}",
            small_font,
            is_listening or rect.collidepoint(mouse_pos),
        )

    draw_button(
        surface,
        back_rect,
        "Concluir",
        btn_font,
        back_rect.collidepoint(mouse_pos),
    )


def draw_jukebox_screen(
    surface, title_font, btn_font, small_font, jukebox, mouse_pos, tick_count
):
    draw_arcade_backdrop(surface, tick_count, small_font)

    title = title_font.render("JUKEBOX", True, ARCADE_NEON_PINK)
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 105)))

    panel = pygame.Rect(WIDTH // 2 - 360, 165, 720, 360)
    pygame.draw.rect(surface, PANEL_COLOR, panel, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, panel, width=2, border_radius=12)

    if not jukebox.tracks:
        msg1 = btn_font.render(
            "Nenhuma música encontrada na pasta do jogo.", True, TEXT_COLOR
        )
        msg2 = small_font.render(
            "Coloque arquivos .mp3, .ogg ou .wav na mesma pasta e clique em Atualizar.",
            True,
            MUTED_TEXT,
        )
        surface.blit(msg1, msg1.get_rect(center=(panel.centerx, panel.y + 115)))
        surface.blit(msg2, msg2.get_rect(center=(panel.centerx, panel.y + 160)))
    else:
        visible_tracks = jukebox.tracks[:6]
        for idx, track_name in enumerate(visible_tracks):
            rect = pygame.Rect(panel.x + 30, panel.y + 24 + idx * 50, 660, 42)
            highlighted = idx == jukebox.selected_idx or rect.collidepoint(
                mouse_pos
            )
            bg = BUTTON_HOVER if highlighted else BUTTON_IDLE
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            status = (
                " [TOCANDO]"
                if jukebox.playing_track == track_name and not jukebox.is_paused
                else ""
            )
            txt = small_font.render(f"{track_name}{status}", True, TEXT_COLOR)
            surface.blit(txt, (rect.x + 14, rect.centery - txt.get_height() // 2))

    play_rect = pygame.Rect(WIDTH // 2 - 290, 550, 180, 50)
    refresh_rect = pygame.Rect(WIDTH // 2 - 90, 550, 180, 50)
    back_rect = pygame.Rect(WIDTH // 2 + 110, 550, 180, 50)

    draw_button(
        surface,
        play_rect,
        "Tocar / Pausar",
        small_font,
        play_rect.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        refresh_rect,
        "Atualizar Lista",
        small_font,
        refresh_rect.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        back_rect,
        "Voltar",
        small_font,
        back_rect.collidepoint(mouse_pos),
    )


def get_pause_button_rects():
    panel_x, panel_y = WIDTH // 2 - 260, 125
    labels = [
        "Continuar [P]",
        "Ver Move List",
        "Modo Treino [F2]",
        "Dificuldade CPU",
        "Reiniciar [R]",
        "Trocar Lutadores / Arena",
        "Menu Principal",
    ]
    rects = []
    for idx, label in enumerate(labels):
        rect = pygame.Rect(panel_x + 40, panel_y + 66 + idx * 54, 440, 44)
        rects.append((rect, label))
    return pygame.Rect(panel_x, panel_y, 520, 465), rects


def draw_pause_overlay(
    surface,
    btn_font,
    small_font,
    cpu_enabled,
    cpu_difficulty,
    training_mode,
    mouse_pos,
):
    dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dim.fill((8, 10, 18, 165))
    surface.blit(dim, (0, 0))

    panel, buttons = get_pause_button_rects()
    pygame.draw.rect(surface, PANEL_COLOR, panel, border_radius=12)
    pygame.draw.rect(surface, ARCADE_NEON_CYAN, panel, width=2, border_radius=12)

    hdr = btn_font.render("JOGO PAUSADO", True, ARCADE_NEON_YELLOW)
    surface.blit(hdr, hdr.get_rect(center=(panel.centerx, panel.y + 34)))

    dynamic_labels = [
        "Continuar [P]",
        "Ver Move List",
        f"Modo Treino [F2]: {'ON' if training_mode else 'OFF'}",
        f"CPU ({'ON' if cpu_enabled else 'OFF'}): {cpu_difficulty}",
        "Reiniciar [R]",
        "Trocar Lutadores / Arena",
        "Menu Principal",
    ]

    for (rect, _), label in zip(buttons, dynamic_labels):
        draw_button(
            surface, rect, label, small_font, rect.collidepoint(mouse_pos)
        )


def draw_game_over_screen(
    surface,
    title_font,
    btn_font,
    small_font,
    p1,
    p2,
    cpu_enabled,
    arcade_mode,
    arcade_stage_num,
    arcade_total_stages,
    arcade_elapsed_sec,
    new_record_banner,
    mouse_pos,
    tick_count,
    net_role=None,
):
    draw_arcade_backdrop(surface, tick_count, small_font)

    p1_won = p1.stocks > 0
    if arcade_mode and p1_won and arcade_stage_num >= arcade_total_stages:
        winner_label = f"CAMPEÃO DA TORRE ARCADE: {p1.name.upper()}!"
    elif arcade_mode and p1_won:
        winner_label = (
            f"FASE {arcade_stage_num}/{arcade_total_stages} CONCLUÍDA!"
        )
    elif p1_won:
        winner_label = f"VITÓRIA DE {p1.name.upper()}!"
    else:
        winner_label = f"VITÓRIA DE {p2.name.upper()}!"

    title = title_font.render(winner_label, True, ARCADE_NEON_YELLOW)
    surface.blit(title, title.get_rect(center=(WIDTH // 2, 110)))

    panel = pygame.Rect(WIDTH // 2 - 410, 168, 820, 322)
    pygame.draw.rect(surface, PANEL_COLOR, panel, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, panel, width=2, border_radius=12)

    p1_kos = ", ".join(p1.ko_moves_scored) if p1.ko_moves_scored else "-"
    p2_kos = ", ".join(p2.ko_moves_scored) if p2.ko_moves_scored else "-"

    p1_stats = btn_font.render(
        f"P1 ({p1.name}): Dano {int(round(p1.total_damage_dealt))}%  •  Combo Máx {p1.max_combo}x",
        True,
        P1_COLOR,
    )
    p1_fin = small_font.render(f"Finalizações P1: {p1_kos}", True, MUTED_TEXT)

    p2_tag = (
        f"Online ({p2.name})"
        if net_role
        else (f"CPU ({p2.name})" if cpu_enabled else f"P2 ({p2.name})")
    )
    p2_col = CPU_COLOR if cpu_enabled else P2_COLOR
    p2_stats = btn_font.render(
        f"{p2_tag}: Dano {int(round(p2.total_damage_dealt))}%  •  Combo Máx {p2.max_combo}x",
        True,
        p2_col,
    )
    p2_fin = small_font.render(
        f"Finalizações {p2_tag}: {p2_kos}", True, MUTED_TEXT
    )

    surface.blit(p1_stats, p1_stats.get_rect(center=(panel.centerx, panel.y + 52)))
    surface.blit(p1_fin, p1_fin.get_rect(center=(panel.centerx, panel.y + 82)))
    surface.blit(p2_stats, p2_stats.get_rect(center=(panel.centerx, panel.y + 132)))
    surface.blit(p2_fin, p2_fin.get_rect(center=(panel.centerx, panel.y + 162)))

    if arcade_mode:
        arc_info = btn_font.render(
            f"Tempo da Torre: {arcade_elapsed_sec:.1f}s  •  Progresso: {arcade_stage_num}/{arcade_total_stages}",
            True,
            ARCADE_NEON_CYAN,
        )
        surface.blit(
            arc_info, arc_info.get_rect(center=(panel.centerx, panel.y + 215))
        )
        if new_record_banner:
            rec_s = small_font.render(
                new_record_banner, True, ARCADE_NEON_YELLOW
            )
            surface.blit(
                rec_s, rec_s.get_rect(center=(panel.centerx, panel.y + 248))
            )

    primary_label = (
        "Próxima Luta"
        if (arcade_mode and p1_won and arcade_stage_num < arcade_total_stages)
        else ("Voltar ao Lobby" if net_role else "Revanche")
    )
    tip = small_font.render(
        f"ENTER/R: {primary_label}  •  ESC: Menu",
        True,
        MUTED_TEXT,
    )
    surface.blit(tip, tip.get_rect(center=(panel.centerx, panel.y + 286)))

    rematch_rect = pygame.Rect(WIDTH // 2 - 345, 520, 210, 54)
    roster_rect = pygame.Rect(WIDTH // 2 - 105, 520, 210, 54)
    menu_rect = pygame.Rect(WIDTH // 2 + 135, 520, 210, 54)

    draw_button(
        surface,
        rematch_rect,
        primary_label,
        btn_font,
        rematch_rect.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        roster_rect,
        "Lobby" if net_role else "Lutadores",
        btn_font,
        roster_rect.collidepoint(mouse_pos),
    )
    draw_button(
        surface,
        menu_rect,
        "Menu",
        btn_font,
        menu_rect.collidepoint(mouse_pos),
    )


def build_stage_platforms(stage_idx):
    preset = STAGE_PRESETS[stage_idx % len(STAGE_PRESETS)]
    s_col = preset.get("stage_color", MAIN_STAGE_COLOR)
    p_col = preset.get("plat_color", PLATFORM_COLOR)
    return [
        Platform(
            x,
            y,
            w,
            h,
            one_way=ow,
            amp_x=ax,
            amp_y=ay,
            freq=fr,
            stage_color=s_col,
            plat_color=p_col,
        )
        for (x, y, w, h, ow, ax, ay, fr) in preset["platforms"]
    ]


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Arcade Smash - Multiplayer Edition")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("consolas", 42, bold=True)
    game_banner_font = pygame.font.SysFont("consolas", 76, bold=True)
    btn_font = pygame.font.SysFont("consolas", 22, bold=True)
    font = pygame.font.SysFont("consolas", 22, bold=True)
    combo_font = pygame.font.SysFont("consolas", 18, bold=True)
    small_font = pygame.font.SysFont("consolas", 14)

    saved_cfg = load_saved_config()
    records = load_arcade_records()
    stage_idx = saved_cfg["stage_idx"]
    platforms = build_stage_platforms(stage_idx)

    sprites_map = {}
    for char in CHARACTER_ROSTER:
        spr = load_fighter_sprite(char["name"], 82, 98)
        sprites_map[char["name"]] = spr
        if spr is None:
            print(
                f"Aviso: '{char['name']}.jpg/.jpeg' não encontrada. Usando placeholder."
            )

    p1_controls = dict(saved_cfg["p1_controls"])
    p2_controls = dict(saved_cfg["p2_controls"])

    p1_char_idx = 0
    p2_char_idx = 1 if len(CHARACTER_ROSTER) > 1 else 0
    p1_confirmed = False
    movelist_char_idx = 0
    movelist_return_state = "menu"

    c1 = CHARACTER_ROSTER[p1_char_idx]
    c2 = CHARACTER_ROSTER[p2_char_idx]

    p1 = Fighter(
        c1["name"],
        390,
        467,
        c1["color"],
        p1_controls,
        c1["moveset"],
        facing=1,
        sprite=sprites_map.get(c1["name"]),
        stats=c1.get("stats"),
        ultimate_type=c1.get("ultimate_type", "rush"),
        ultimate_name=c1.get("ultimate_name", "Golpe Final"),
    )
    p2 = Fighter(
        c2["name"],
        765,
        467,
        c2["color"],
        p2_controls,
        c2["moveset"],
        facing=-1,
        sprite=sprites_map.get(c2["name"]),
        stats=c2.get("stats"),
        ultimate_type=c2.get("ultimate_type", "rush"),
        ultimate_name=c2.get("ultimate_name", "Golpe Final"),
    )

    cpu_difficulty = saved_cfg["cpu_difficulty"]
    cpu_p2 = CpuController(p2, difficulty=cpu_difficulty)
    cpu_enabled = saved_cfg["cpu_enabled"]
    training_mode = saved_cfg["training_mode"]
    jukebox = Jukebox(initial_volume=saved_cfg["volume"])
    sfx = SoundFX()

    net = NetSession()
    join_ip_input = saved_cfg["last_join_ip"]
    editing_ip = False
    remote_p2_keys = RemoteKeys(p2_controls)
    remote_p2_events = []

    particles = []
    projectiles = []
    popups = []
    pickups = []
    afterimages = []
    ko_beams = []
    smash_ball = None

    state = "menu"
    paused = False
    listening_target = None
    menu_selected = 0
    settings_selected = 0
    hitstop_frames = 0
    shake_frames = 0
    ko_banner_timer = 0
    game_finish_timer = 0
    pickup_spawn_timer = 300
    smash_ball_timer = 540
    tick_count = 0

    arcade_mode = False
    arcade_queue = []
    arcade_stage_num = 1
    arcade_frames = 0
    arcade_best_combo_run = 0
    new_record_banner = ""

    def persist_prefs():
        save_config(
            jukebox.volume,
            cpu_enabled,
            cpu_difficulty,
            stage_idx,
            training_mode,
            p1_controls,
            p2_controls,
            last_join_ip=join_ip_input,
        )

    def cycle_difficulty(step=1):
        nonlocal cpu_difficulty
        idx = CPU_DIFFICULTY_ORDER.index(cpu_difficulty)
        cpu_difficulty = CPU_DIFFICULTY_ORDER[
            (idx + step) % len(CPU_DIFFICULTY_ORDER)
        ]
        cpu_p2.set_difficulty(cpu_difficulty)
        persist_prefs()

    def cycle_stage(step=1):
        nonlocal stage_idx, platforms
        stage_idx = (stage_idx + step) % len(STAGE_PRESETS)
        platforms = build_stage_platforms(stage_idx)
        persist_prefs()

    def toggle_training_mode():
        nonlocal training_mode
        training_mode = not training_mode
        if training_mode:
            p1.damage_pct = 0.0
            p2.damage_pct = 0.0
            p1.stocks = 3
            p2.stocks = 3
        persist_prefs()

    def setup_arcade_tower():
        nonlocal arcade_queue, arcade_stage_num, arcade_frames
        nonlocal cpu_enabled, arcade_best_combo_run, new_record_banner
        candidates = [
            i for i in range(len(CHARACTER_ROSTER)) if i != p1_char_idx
        ]
        random.shuffle(candidates)
        arcade_queue = candidates[: len(ARCADE_TOWER_DIFFICULTIES)]
        arcade_stage_num = 1
        arcade_frames = 0
        arcade_best_combo_run = 0
        new_record_banner = ""
        cpu_enabled = True

    def start_new_match(advance_arcade=False):
        nonlocal hitstop_frames, shake_frames, platforms, paused, p2_char_idx
        nonlocal arcade_stage_num, cpu_enabled, ko_banner_timer, pickup_spawn_timer
        nonlocal game_finish_timer, smash_ball, smash_ball_timer
        if arcade_mode:
            cpu_enabled = True
            if advance_arcade and arcade_stage_num < len(arcade_queue):
                arcade_stage_num += 1
            if arcade_queue:
                p2_char_idx = arcade_queue[arcade_stage_num - 1]
                diff_for_stage = ARCADE_TOWER_DIFFICULTIES[arcade_stage_num - 1]
                cpu_p2.set_difficulty(diff_for_stage)

        platforms = build_stage_platforms(stage_idx)
        char1 = CHARACTER_ROSTER[p1_char_idx]
        char2 = CHARACTER_ROSTER[p2_char_idx]
        p1.set_character(char1, sprites_map.get(char1["name"]))
        p2.set_character(char2, sprites_map.get(char2["name"]))
        p1.reset_match_stats()
        p2.reset_match_stats()
        cpu_p2.reset()
        particles.clear()
        projectiles.clear()
        popups.clear()
        pickups.clear()
        afterimages.clear()
        ko_beams.clear()
        smash_ball = None
        hitstop_frames = 0
        shake_frames = 0
        ko_banner_timer = 0
        game_finish_timer = 0
        pickup_spawn_timer = 260
        smash_ball_timer = 480
        paused = False

    def open_move_list(return_to, initial_idx=0):
        nonlocal state, movelist_return_state, movelist_char_idx
        movelist_return_state = return_to
        movelist_char_idx = initial_idx % len(CHARACTER_ROSTER)
        state = "move_list"

    while True:
        active_fps = 22 if (state == "game" and game_finish_timer > 0) else FPS
        clock.tick(active_fps)
        tick_count += 1
        mouse_pos = pygame.mouse.get_pos()

        # Processa mensagens de rede no lobby e durante a partida
        if net.role is not None:
            net_msg = net.pop_latest()
            if net_msg:
                mtype = net_msg.get("type")
                if net.role == "host":
                    if mtype == "client_lobby":
                        p2_char_idx = (
                            int(net_msg.get("char_idx", p2_char_idx))
                            % len(CHARACTER_ROSTER)
                        )
                    elif mtype == "client_input":
                        remote_p2_keys.apply_state(net_msg.get("held", {}))
                        evs = net_msg.get("events", [])
                        if isinstance(evs, list):
                            remote_p2_events.extend(evs)
                elif net.role == "client":
                    if mtype == "host_lobby":
                        p1_char_idx = (
                            int(net_msg.get("p1_char_idx", p1_char_idx))
                            % len(CHARACTER_ROSTER)
                        )
                        new_st = (
                            int(net_msg.get("stage_idx", stage_idx))
                            % len(STAGE_PRESETS)
                        )
                        if new_st != stage_idx:
                            stage_idx = new_st
                            platforms = build_stage_platforms(stage_idx)
                        if net_msg.get("start_match") and state == "mp_lobby":
                            arcade_mode = False
                            cpu_enabled = False
                            training_mode = False
                            start_new_match(advance_arcade=False)
                            state = "game"
                    elif mtype == "game_state":
                        if state != "game" and not net_msg.get("game_over"):
                            arcade_mode = False
                            cpu_enabled = False
                            training_mode = False
                            start_new_match(advance_arcade=False)
                            state = "game"
                        p1.apply_net_dict(net_msg.get("p1"))
                        p2.apply_net_dict(net_msg.get("p2"))
                        ko_banner_timer = int(net_msg.get("ko_banner", 0))
                        game_finish_timer = int(net_msg.get("game_finish", 0))
                        for i, pl_d in enumerate(net_msg.get("plats", [])):
                            if i < len(platforms):
                                platforms[i].rect.x = int(pl_d[0])
                                platforms[i].rect.y = int(pl_d[1])
                        projectiles = [
                            Projectile(
                                pr[0],
                                pr[1],
                                pr[2],
                                0,
                                tuple(pr[3]),
                                0,
                                0,
                                0,
                            )
                            for pr in net_msg.get("projs", [])
                        ]
                        pickups = []
                        for pk_d in net_msg.get("pickups", []):
                            pk_obj = StagePickup(
                                pk_d[0] + 13, pk_d[1] + 26, pk_d[2]
                            )
                            pickups.append(pk_obj)
                        sb_d = net_msg.get("smash_ball")
                        if sb_d:
                            if smash_ball is None:
                                smash_ball = SmashBall()
                            smash_ball.x = float(sb_d[0])
                            smash_ball.y = float(sb_d[1])
                            smash_ball.rect.center = (
                                int(smash_ball.x),
                                int(smash_ball.y),
                            )
                        else:
                            smash_ball = None
                        if net_msg.get("game_over") and state == "game":
                            state = "game_over"
                    elif mtype == "back_to_lobby" and state in (
                        "game",
                        "game_over",
                    ):
                        state = "mp_lobby"

            if state == "mp_lobby" and net.connected:
                if net.role == "host":
                    net.send(
                        {
                            "type": "host_lobby",
                            "p1_char_idx": p1_char_idx,
                            "stage_idx": stage_idx,
                            "start_match": False,
                        }
                    )
                elif net.role == "client":
                    net.send(
                        {
                            "type": "client_lobby",
                            "char_idx": p2_char_idx,
                        }
                    )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                net.close()
                persist_prefs()
                pygame.quit()
                sys.exit()

            if state == "menu":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        menu_selected = (menu_selected - 1) % 6
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        menu_selected = (menu_selected + 1) % 6
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        sfx.play("blip", jukebox.volume)
                        if menu_selected == 0:
                            net.close()
                            arcade_mode = False
                            p1_confirmed = False
                            state = "char_select"
                        elif menu_selected == 1:
                            net.close()
                            arcade_mode = True
                            training_mode = False
                            p1_confirmed = False
                            state = "char_select"
                        elif menu_selected == 2:
                            arcade_mode = False
                            training_mode = False
                            cpu_enabled = False
                            editing_ip = False
                            state = "mp_lobby"
                        elif menu_selected == 3:
                            open_move_list("menu", p1_char_idx)
                        elif menu_selected == 4:
                            settings_selected = 0
                            state = "settings"
                        elif menu_selected == 5:
                            jukebox.refresh_tracks()
                            state = "jukebox"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for idx in range(6):
                        rect = pygame.Rect(
                            WIDTH // 2 - 210, 178 + idx * 58, 420, 46
                        )
                        if rect.collidepoint(event.pos):
                            menu_selected = idx
                            sfx.play("blip", jukebox.volume)
                            if idx == 0:
                                net.close()
                                arcade_mode = False
                                p1_confirmed = False
                                state = "char_select"
                            elif idx == 1:
                                net.close()
                                arcade_mode = True
                                training_mode = False
                                p1_confirmed = False
                                state = "char_select"
                            elif idx == 2:
                                arcade_mode = False
                                training_mode = False
                                cpu_enabled = False
                                editing_ip = False
                                state = "mp_lobby"
                            elif idx == 3:
                                open_move_list("menu", p1_char_idx)
                            elif idx == 4:
                                settings_selected = 0
                                state = "settings"
                            elif idx == 5:
                                jukebox.refresh_tracks()
                                state = "jukebox"

            elif state == "mp_lobby":
                host_box = pygame.Rect(85, 134, 495, 290)
                join_box = pygame.Rect(620, 134, 495, 290)
                ip_box = pygame.Rect(join_box.x + 48, 196, 400, 42)
                btn_host = pygame.Rect(host_box.x + 48, 272, 400, 48)
                btn_h_char = pygame.Rect(host_box.x + 48, 332, 192, 42)
                btn_h_stage = pygame.Rect(host_box.x + 256, 332, 192, 42)
                btn_join = pygame.Rect(join_box.x + 48, 282, 400, 48)
                btn_j_char = pygame.Rect(join_box.x + 128, 340, 240, 40)
                back_rect = pygame.Rect(WIDTH // 2 - 260, 578, 230, 54)
                start_rect = pygame.Rect(WIDTH // 2 + 30, 578, 250, 54)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        editing_ip = False
                        net.close()
                        sfx.play("blip", jukebox.volume)
                        state = "menu"
                    elif editing_ip:
                        if event.key == pygame.K_RETURN:
                            editing_ip = False
                            persist_prefs()
                            net.connect_client(join_ip_input, NET_PORT)
                        elif event.key == pygame.K_BACKSPACE:
                            join_ip_input = join_ip_input[:-1]
                        elif (
                            event.unicode
                            and event.unicode in "0123456789.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-:"
                            and len(join_ip_input) < 35
                        ):
                            join_ip_input += event.unicode
                    elif (
                        event.key in (pygame.K_RETURN, pygame.K_SPACE)
                        and net.role == "host"
                        and net.connected
                    ):
                        sfx.play("blip", jukebox.volume)
                        net.send(
                            {
                                "type": "host_lobby",
                                "p1_char_idx": p1_char_idx,
                                "stage_idx": stage_idx,
                                "start_match": True,
                            }
                        )
                        start_new_match(advance_arcade=False)
                        state = "game"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    editing_ip = ip_box.collidepoint(event.pos)
                    if btn_host.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        net.start_host(NET_PORT)
                    elif btn_h_char.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        p1_char_idx = (p1_char_idx + 1) % len(CHARACTER_ROSTER)
                    elif btn_h_stage.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        cycle_stage(1)
                    elif btn_join.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        persist_prefs()
                        net.connect_client(join_ip_input, NET_PORT)
                    elif btn_j_char.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        p2_char_idx = (p2_char_idx + 1) % len(CHARACTER_ROSTER)
                    elif back_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        net.close()
                        state = "menu"
                    elif (
                        net.role == "host"
                        and net.connected
                        and start_rect.collidepoint(event.pos)
                    ):
                        sfx.play("blip", jukebox.volume)
                        net.send(
                            {
                                "type": "host_lobby",
                                "p1_char_idx": p1_char_idx,
                                "stage_idx": stage_idx,
                                "start_match": True,
                            }
                        )
                        start_new_match(advance_arcade=False)
                        state = "game"

            elif state == "char_select":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        sfx.play("blip", jukebox.volume)
                        if p1_confirmed and not arcade_mode:
                            p1_confirmed = False
                        else:
                            state = "menu"
                    elif event.key == pygame.K_m:
                        sfx.play("blip", jukebox.volume)
                        target_i = (
                            p1_char_idx
                            if (arcade_mode or not p1_confirmed)
                            else p2_char_idx
                        )
                        open_move_list("char_select", target_i)
                    elif event.key == pygame.K_x:
                        sfx.play("blip", jukebox.volume)
                        if arcade_mode or not p1_confirmed:
                            p1_char_idx = random.randrange(len(CHARACTER_ROSTER))
                        else:
                            p2_char_idx = random.randrange(len(CHARACTER_ROSTER))
                    elif event.key == pygame.K_F2 and not arcade_mode:
                        toggle_training_mode()
                        sfx.play("blip", jukebox.volume)
                    elif arcade_mode or not p1_confirmed:
                        if event.key in (pygame.K_a, pygame.K_LEFT):
                            p1_char_idx = (p1_char_idx - 1) % len(
                                CHARACTER_ROSTER
                            )
                            sfx.play("blip", jukebox.volume)
                        elif event.key in (pygame.K_d, pygame.K_RIGHT):
                            p1_char_idx = (p1_char_idx + 1) % len(
                                CHARACTER_ROSTER
                            )
                            sfx.play("blip", jukebox.volume)
                        elif event.key in (
                            pygame.K_w,
                            pygame.K_f,
                            pygame.K_RETURN,
                            pygame.K_SPACE,
                        ):
                            sfx.play("blip", jukebox.volume)
                            if arcade_mode:
                                state = "stage_select"
                            else:
                                p1_confirmed = True
                    else:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            p2_char_idx = (p2_char_idx - 1) % len(
                                CHARACTER_ROSTER
                            )
                            sfx.play("blip", jukebox.volume)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            p2_char_idx = (p2_char_idx + 1) % len(
                                CHARACTER_ROSTER
                            )
                            sfx.play("blip", jukebox.volume)
                        elif event.key in (
                            pygame.K_UP,
                            pygame.K_RCTRL,
                            pygame.K_RETURN,
                            pygame.K_SPACE,
                        ):
                            sfx.play("blip", jukebox.volume)
                            state = "stage_select"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    card_rects = get_char_card_rects(len(CHARACTER_ROSTER))
                    for idx, rect in enumerate(card_rects):
                        if rect.collidepoint(event.pos):
                            sfx.play("blip", jukebox.volume)
                            if arcade_mode or not p1_confirmed:
                                p1_char_idx = idx
                                if not arcade_mode:
                                    p1_confirmed = True
                            else:
                                p2_char_idx = idx

                    back_rect = pygame.Rect(WIDTH // 2 - 430, 586, 195, 52)
                    rand_rect = pygame.Rect(WIDTH // 2 - 210, 586, 195, 52)
                    moves_rect = pygame.Rect(WIDTH // 2 + 10, 586, 195, 52)
                    next_rect = pygame.Rect(WIDTH // 2 + 230, 586, 195, 52)

                    if back_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        if p1_confirmed and not arcade_mode:
                            p1_confirmed = False
                        else:
                            state = "menu"
                    elif rand_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        if arcade_mode or not p1_confirmed:
                            p1_char_idx = random.randrange(len(CHARACTER_ROSTER))
                        else:
                            p2_char_idx = random.randrange(len(CHARACTER_ROSTER))
                    elif moves_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        target_i = (
                            p1_char_idx
                            if (arcade_mode or not p1_confirmed)
                            else p2_char_idx
                        )
                        open_move_list("char_select", target_i)
                    elif next_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        state = "stage_select"

            elif state == "stage_select":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        sfx.play("blip", jukebox.volume)
                        state = "char_select"
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        cycle_stage(-1)
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        cycle_stage(1)
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        cycle_stage(-2)
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        cycle_stage(2)
                        sfx.play("blip", jukebox.volume)
                    elif event.key == pygame.K_F2 and not arcade_mode:
                        toggle_training_mode()
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        sfx.play("blip", jukebox.volume)
                        if arcade_mode:
                            setup_arcade_tower()
                        start_new_match(advance_arcade=False)
                        state = "game"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    card_rects = get_stage_card_rects()
                    for idx, rect in enumerate(card_rects):
                        if rect.collidepoint(event.pos):
                            stage_idx = idx
                            platforms = build_stage_platforms(stage_idx)
                            persist_prefs()
                            sfx.play("blip", jukebox.volume)

                    back_rect = pygame.Rect(WIDTH // 2 - 360, 582, 220, 54)
                    train_rect = pygame.Rect(WIDTH // 2 - 110, 582, 220, 54)
                    fight_rect = pygame.Rect(WIDTH // 2 + 140, 582, 220, 54)

                    if back_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        state = "char_select"
                    elif train_rect.collidepoint(event.pos) and not arcade_mode:
                        toggle_training_mode()
                        sfx.play("blip", jukebox.volume)
                    elif fight_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        if arcade_mode:
                            setup_arcade_tower()
                        start_new_match(advance_arcade=False)
                        state = "game"

            elif state == "move_list":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        sfx.play("blip", jukebox.volume)
                        state = movelist_return_state
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        movelist_char_idx = (movelist_char_idx - 1) % len(
                            CHARACTER_ROSTER
                        )
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        movelist_char_idx = (movelist_char_idx + 1) % len(
                            CHARACTER_ROSTER
                        )
                        sfx.play("blip", jukebox.volume)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    tab_w = 132
                    gap = 8
                    start_x = (
                        WIDTH
                        - (
                            len(CHARACTER_ROSTER) * tab_w
                            + (len(CHARACTER_ROSTER) - 1) * gap
                        )
                    ) // 2
                    for idx in range(len(CHARACTER_ROSTER)):
                        t_rect = pygame.Rect(
                            start_x + idx * (tab_w + gap), 86, tab_w, 34
                        )
                        if t_rect.collidepoint(event.pos):
                            movelist_char_idx = idx
                            sfx.play("blip", jukebox.volume)

                    prev_rect = pygame.Rect(WIDTH // 2 - 330, 594, 200, 50)
                    next_rect = pygame.Rect(WIDTH // 2 - 100, 594, 200, 50)
                    back_rect = pygame.Rect(WIDTH // 2 + 130, 594, 200, 50)

                    if prev_rect.collidepoint(event.pos):
                        movelist_char_idx = (movelist_char_idx - 1) % len(
                            CHARACTER_ROSTER
                        )
                        sfx.play("blip", jukebox.volume)
                    elif next_rect.collidepoint(event.pos):
                        movelist_char_idx = (movelist_char_idx + 1) % len(
                            CHARACTER_ROSTER
                        )
                        sfx.play("blip", jukebox.volume)
                    elif back_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        state = movelist_return_state

            elif state == "settings":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        persist_prefs()
                        sfx.play("blip", jukebox.volume)
                        state = "menu"
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        settings_selected = (settings_selected - 1) % 6
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        settings_selected = (settings_selected + 1) % 6
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        if settings_selected == 0:
                            jukebox.set_volume(jukebox.volume - 0.1)
                            persist_prefs()
                        elif settings_selected == 2:
                            cycle_difficulty(-1)
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        if settings_selected == 0:
                            jukebox.set_volume(jukebox.volume + 0.1)
                            persist_prefs()
                        elif settings_selected == 2:
                            cycle_difficulty(1)
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        sfx.play("blip", jukebox.volume)
                        if settings_selected == 0:
                            next_vol = (
                                0.0
                                if jukebox.volume >= 1.0
                                else jukebox.volume + 0.1
                            )
                            jukebox.set_volume(next_vol)
                            persist_prefs()
                        elif settings_selected == 1:
                            cpu_enabled = not cpu_enabled
                            cpu_p2.reset()
                            persist_prefs()
                        elif settings_selected == 2:
                            cycle_difficulty(1)
                        elif settings_selected == 3:
                            toggle_training_mode()
                        elif settings_selected == 4:
                            listening_target = None
                            state = "controls_remap"
                        elif settings_selected == 5:
                            persist_prefs()
                            state = "menu"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    panel_x, panel_y = WIDTH // 2 - 330, 140
                    for idx in range(6):
                        rect = pygame.Rect(
                            panel_x + 40, panel_y + 18 + idx * 72, 580, 52
                        )
                        if rect.collidepoint(event.pos):
                            settings_selected = idx
                            sfx.play("blip", jukebox.volume)
                            if idx == 0:
                                next_vol = (
                                    0.0
                                    if jukebox.volume >= 1.0
                                    else jukebox.volume + 0.1
                                )
                                jukebox.set_volume(next_vol)
                                persist_prefs()
                            elif idx == 1:
                                cpu_enabled = not cpu_enabled
                                cpu_p2.reset()
                                persist_prefs()
                            elif idx == 2:
                                cycle_difficulty(1)
                            elif idx == 3:
                                toggle_training_mode()
                            elif idx == 4:
                                listening_target = None
                                state = "controls_remap"
                            elif idx == 5:
                                persist_prefs()
                                state = "menu"

            elif state == "controls_remap":
                if event.type == pygame.KEYDOWN:
                    if listening_target is not None:
                        if event.key != pygame.K_ESCAPE:
                            pid, act_key = listening_target
                            target_map = p1_controls if pid == 1 else p2_controls
                            target_map[act_key] = event.key
                            if act_key == "jump":
                                target_map["up"] = event.key
                            persist_prefs()
                        listening_target = None
                        sfx.play("blip", jukebox.volume)
                    elif event.key == pygame.K_ESCAPE:
                        sfx.play("blip", jukebox.volume)
                        state = "settings"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    rects, back_rect = get_remap_button_rects()
                    clicked_btn = False
                    for rect, pid, act_key, _ in rects:
                        if rect.collidepoint(event.pos):
                            listening_target = (pid, act_key)
                            sfx.play("blip", jukebox.volume)
                            clicked_btn = True
                            break
                    if not clicked_btn and back_rect.collidepoint(event.pos):
                        listening_target = None
                        sfx.play("blip", jukebox.volume)
                        state = "settings"

            elif state == "jukebox":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        sfx.play("blip", jukebox.volume)
                        state = "menu"
                    elif jukebox.tracks and event.key in (
                        pygame.K_UP,
                        pygame.K_w,
                    ):
                        jukebox.selected_idx = (jukebox.selected_idx - 1) % len(
                            jukebox.tracks
                        )
                        sfx.play("blip", jukebox.volume)
                    elif jukebox.tracks and event.key in (
                        pygame.K_DOWN,
                        pygame.K_s,
                    ):
                        jukebox.selected_idx = (jukebox.selected_idx + 1) % len(
                            jukebox.tracks
                        )
                        sfx.play("blip", jukebox.volume)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        jukebox.toggle_pause_or_play()
                        sfx.play("blip", jukebox.volume)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    panel_x, panel_y = WIDTH // 2 - 360, 165
                    for idx in range(min(6, len(jukebox.tracks))):
                        rect = pygame.Rect(
                            panel_x + 30, panel_y + 24 + idx * 50, 660, 42
                        )
                        if rect.collidepoint(event.pos):
                            jukebox.selected_idx = idx
                            jukebox.play_selected()
                            sfx.play("blip", jukebox.volume)

                    play_rect = pygame.Rect(WIDTH // 2 - 290, 550, 180, 50)
                    refresh_rect = pygame.Rect(WIDTH // 2 - 90, 550, 180, 50)
                    back_rect = pygame.Rect(WIDTH // 2 + 110, 550, 180, 50)

                    if play_rect.collidepoint(event.pos):
                        jukebox.toggle_pause_or_play()
                        sfx.play("blip", jukebox.volume)
                    elif refresh_rect.collidepoint(event.pos):
                        jukebox.refresh_tracks()
                        sfx.play("blip", jukebox.volume)
                    elif back_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        state = "menu"

            elif state == "game":
                # Se for Cliente Online, envia os comandos locais para o Host
                if net.role == "client":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            net.close()
                            state = "menu"
                            continue
                        ev_name = None
                        for act in (
                            "left",
                            "right",
                            "jump",
                            "attack",
                            "dodge",
                            "grab",
                            "cancel",
                            "ultimate",
                        ):
                            if event.key == p1_controls[act]:
                                ev_name = f"down_{act}"
                                break
                        if ev_name:
                            net.send(
                                {
                                    "type": "client_input",
                                    "held": {
                                        k: bool(
                                            pygame.key.get_pressed()[
                                                p1_controls[k]
                                            ]
                                        )
                                        for k in remote_p2_keys.held
                                    },
                                    "events": [ev_name],
                                }
                            )
                    elif event.type == pygame.KEYUP:
                        if event.key == p1_controls["attack"]:
                            net.send(
                                {
                                    "type": "client_input",
                                    "held": {
                                        k: bool(
                                            pygame.key.get_pressed()[
                                                p1_controls[k]
                                            ]
                                        )
                                        for k in remote_p2_keys.held
                                    },
                                    "events": ["up_attack"],
                                }
                            )
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p and net.role is None:
                        paused = not paused
                        sfx.play("blip", jukebox.volume)
                        continue

                    if (
                        event.key == pygame.K_F2
                        and not arcade_mode
                        and net.role is None
                    ):
                        toggle_training_mode()
                        sfx.play("blip", jukebox.volume)
                        continue

                    if paused:
                        if event.key == pygame.K_ESCAPE:
                            paused = False
                        elif event.key == pygame.K_r:
                            start_new_match(advance_arcade=False)
                        continue

                    keys = pygame.key.get_pressed()

                    if event.key == pygame.K_ESCAPE:
                        if net.role == "host":
                            net.send({"type": "back_to_lobby"})
                            state = "mp_lobby"
                        else:
                            p1_confirmed = False
                            state = "char_select"

                    if (
                        event.key == pygame.K_SPACE
                        and not arcade_mode
                        and net.role is None
                    ):
                        cpu_enabled = not cpu_enabled
                        cpu_p2.reset()
                        persist_prefs()

                    if event.key == p1.controls["left"]:
                        p1.register_direction_tap(-1, tick_count, particles)
                    elif event.key == p1.controls["right"]:
                        p1.register_direction_tap(1, tick_count, particles)

                    if not cpu_enabled and net.role is None:
                        if event.key == p2.controls["left"]:
                            p2.register_direction_tap(-1, tick_count, particles)
                        elif event.key == p2.controls["right"]:
                            p2.register_direction_tap(1, tick_count, particles)

                    if event.key == p1.controls["jump"]:
                        p1.jump()
                    if (
                        not cpu_enabled
                        and net.role is None
                        and event.key == p2.controls["jump"]
                    ):
                        p2.jump()

                    if event.key == p1.controls["attack"]:
                        p1.begin_attack_or_charge(keys, sfx, jukebox.volume)
                    if (
                        not cpu_enabled
                        and net.role is None
                        and event.key == p2.controls["attack"]
                    ):
                        p2.begin_attack_or_charge(keys, sfx, jukebox.volume)

                    if event.key == p1.controls["dodge"]:
                        if (
                            not p1.on_ground
                            or keys[p1.controls["left"]]
                            or keys[p1.controls["right"]]
                        ):
                            p1.dodge(sfx, jukebox.volume)
                        else:
                            p1.parry_window = 5
                    if (
                        not cpu_enabled
                        and net.role is None
                        and event.key == p2.controls["dodge"]
                    ):
                        if (
                            not p2.on_ground
                            or keys[p2.controls["left"]]
                            or keys[p2.controls["right"]]
                        ):
                            p2.dodge(sfx, jukebox.volume)
                        else:
                            p2.parry_window = 5

                    if event.key == p1.controls["grab"]:
                        p1.grab(sfx, jukebox.volume)
                    if (
                        not cpu_enabled
                        and net.role is None
                        and event.key == p2.controls["grab"]
                    ):
                        p2.grab(sfx, jukebox.volume)

                    if event.key == p1.controls["cancel"]:
                        p1.roman_cancel(
                            particles, popups, sfx, jukebox.volume
                        )
                    if (
                        not cpu_enabled
                        and net.role is None
                        and event.key == p2.controls["cancel"]
                    ):
                        p2.roman_cancel(
                            particles, popups, sfx, jukebox.volume
                        )

                    if event.key == p1.controls["ultimate"]:
                        p1.trigger_ultimate(
                            1,
                            p2,
                            projectiles,
                            particles,
                            popups,
                            sfx,
                            jukebox.volume,
                        )
                    if (
                        not cpu_enabled
                        and net.role is None
                        and event.key == p2.controls["ultimate"]
                    ):
                        p2.trigger_ultimate(
                            2,
                            p1,
                            projectiles,
                            particles,
                            popups,
                            sfx,
                            jukebox.volume,
                        )

                    if event.key == pygame.K_r and net.role is None:
                        start_new_match(advance_arcade=False)

                elif event.type == pygame.KEYUP and not paused:
                    if event.key == p1.controls["attack"]:
                        p1.release_smash_charge(sfx, jukebox.volume)
                    if (
                        not cpu_enabled
                        and net.role is None
                        and event.key == p2.controls["attack"]
                    ):
                        p2.release_smash_charge(sfx, jukebox.volume)

                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and paused
                ):
                    _, pause_buttons = get_pause_button_rects()
                    for b_idx, (rect, _) in enumerate(pause_buttons):
                        if rect.collidepoint(event.pos):
                            sfx.play("blip", jukebox.volume)
                            if b_idx == 0:
                                paused = False
                            elif b_idx == 1:
                                open_move_list("game", p1_char_idx)
                            elif b_idx == 2 and not arcade_mode:
                                toggle_training_mode()
                            elif b_idx == 3 and not arcade_mode:
                                cpu_enabled = True
                                cycle_difficulty(1)
                            elif b_idx == 4:
                                start_new_match(advance_arcade=False)
                            elif b_idx == 5:
                                paused = False
                                p1_confirmed = False
                                state = "char_select"
                            elif b_idx == 6:
                                paused = False
                                state = "menu"

            elif state == "game_over":
                p1_won = p1.stocks > 0
                can_advance = (
                    arcade_mode
                    and p1_won
                    and arcade_stage_num < len(arcade_queue)
                )
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_r):
                        sfx.play("blip", jukebox.volume)
                        if net.role == "host":
                            net.send({"type": "back_to_lobby"})
                            state = "mp_lobby"
                        elif net.role is None:
                            if arcade_mode and not can_advance:
                                setup_arcade_tower()
                            start_new_match(advance_arcade=can_advance)
                            state = "game"
                    elif event.key == pygame.K_ESCAPE:
                        sfx.play("blip", jukebox.volume)
                        if net.role:
                            net.close()
                            state = "menu"
                        else:
                            p1_confirmed = False
                            state = "char_select"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    rematch_rect = pygame.Rect(WIDTH // 2 - 345, 520, 210, 54)
                    roster_rect = pygame.Rect(WIDTH // 2 - 105, 520, 210, 54)
                    menu_rect = pygame.Rect(WIDTH // 2 + 135, 520, 210, 54)

                    if rematch_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        if net.role == "host":
                            net.send({"type": "back_to_lobby"})
                            state = "mp_lobby"
                        elif net.role is None:
                            if arcade_mode and not can_advance:
                                setup_arcade_tower()
                            start_new_match(advance_arcade=can_advance)
                            state = "game"
                    elif roster_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        if net.role == "host":
                            net.send({"type": "back_to_lobby"})
                            state = "mp_lobby"
                        elif net.role == "client":
                            state = "mp_lobby"
                        else:
                            p1_confirmed = False
                            state = "char_select"
                    elif menu_rect.collidepoint(event.pos):
                        sfx.play("blip", jukebox.volume)
                        net.close()
                        state = "menu"

        if state == "menu":
            draw_main_menu(
                screen,
                title_font,
                btn_font,
                small_font,
                menu_selected,
                mouse_pos,
                jukebox,
                records,
                tick_count,
            )

        elif state == "mp_lobby":
            draw_multiplayer_lobby_screen(
                screen,
                title_font,
                btn_font,
                small_font,
                net,
                join_ip_input,
                editing_ip,
                p1_char_idx,
                p2_char_idx,
                stage_idx,
                mouse_pos,
                tick_count,
            )

        elif state == "char_select":
            draw_character_select_screen(
                screen,
                title_font,
                btn_font,
                small_font,
                CHARACTER_ROSTER,
                sprites_map,
                p1_char_idx,
                p2_char_idx,
                p1_confirmed,
                cpu_enabled,
                arcade_mode,
                training_mode,
                mouse_pos,
                tick_count,
            )

        elif state == "stage_select":
            draw_stage_select_screen(
                screen,
                title_font,
                btn_font,
                small_font,
                stage_idx,
                CHARACTER_ROSTER[p1_char_idx]["name"],
                CHARACTER_ROSTER[p2_char_idx]["name"],
                arcade_mode,
                training_mode,
                mouse_pos,
                tick_count,
            )

        elif state == "move_list":
            draw_move_list_screen(
                screen,
                title_font,
                btn_font,
                small_font,
                CHARACTER_ROSTER,
                sprites_map,
                movelist_char_idx,
                p1_controls,
                mouse_pos,
                tick_count,
            )

        elif state == "settings":
            draw_settings_screen(
                screen,
                title_font,
                btn_font,
                small_font,
                settings_selected,
                mouse_pos,
                jukebox,
                cpu_enabled,
                cpu_difficulty,
                training_mode,
                tick_count,
            )

        elif state == "controls_remap":
            draw_controls_remap_screen(
                screen,
                title_font,
                btn_font,
                small_font,
                p1_controls,
                p2_controls,
                listening_target,
                mouse_pos,
                tick_count,
            )

        elif state == "jukebox":
            draw_jukebox_screen(
                screen,
                title_font,
                btn_font,
                small_font,
                jukebox,
                mouse_pos,
                tick_count,
            )

        elif state == "game":
            stage_cfg = STAGE_PRESETS[stage_idx % len(STAGE_PRESETS)]
            sudden_death = (
                (not training_mode) and p1.stocks == 1 and p2.stocks == 1
            )

            # Cliente Online envia estado contínuo das teclas seguradas ao Host
            if net.role == "client" and net.connected:
                k_now = pygame.key.get_pressed()
                net.send(
                    {
                        "type": "client_input",
                        "held": {
                            k: bool(k_now[p1_controls[k]])
                            for k in remote_p2_keys.held
                        },
                        "events": [],
                    }
                )

            # Host (ou jogo local) executa a física autoritativa
            if net.role != "client" and not paused:
                if arcade_mode and game_finish_timer == 0:
                    arcade_frames += 1

                if shake_frames > 0:
                    shake_frames -= 1

                if ko_banner_timer > 0:
                    ko_banner_timer -= 1

                for plat in platforms:
                    plat.update(tick_count)

                pickup_spawn_timer -= 1
                if pickup_spawn_timer <= 0 and len(pickups) < 2 and platforms:
                    plat = random.choice(platforms)
                    px = random.randint(
                        plat.rect.left + 24, plat.rect.right - 24
                    )
                    pickups.append(StagePickup(px, plat.rect.top))
                    pickup_spawn_timer = random.randint(420, 620)

                if smash_ball is None and game_finish_timer == 0:
                    smash_ball_timer -= 1
                    if smash_ball_timer <= 0:
                        smash_ball = SmashBall()
                        smash_ball_timer = random.randint(750, 1050)
                elif smash_ball is not None:
                    smash_ball.update()
                    if smash_ball.life <= 0:
                        smash_ball = None

                if hitstop_frames > 0:
                    hitstop_frames -= 1
                else:
                    base_wind = stage_cfg.get("wind_force", 0.0)
                    wind_vx = (
                        base_wind
                        * (1.0 if (tick_count // 180) % 2 == 0 else -1.0)
                        if base_wind != 0.0
                        else 0.0
                    )

                    keys = pygame.key.get_pressed()
                    p1.update(
                        keys,
                        platforms,
                        wind_vx=wind_vx,
                        afterimages=afterimages,
                        sfx=sfx,
                        volume=jukebox.volume,
                    )

                    if net.role == "host":
                        while remote_p2_events:
                            ev = remote_p2_events.pop(0)
                            if ev == "down_left":
                                p2.register_direction_tap(
                                    -1, tick_count, particles
                                )
                            elif ev == "down_right":
                                p2.register_direction_tap(
                                    1, tick_count, particles
                                )
                            elif ev == "down_jump":
                                p2.jump()
                            elif ev == "down_attack":
                                p2.begin_attack_or_charge(
                                    remote_p2_keys, sfx, jukebox.volume
                                )
                            elif ev == "up_attack":
                                p2.release_smash_charge(sfx, jukebox.volume)
                            elif ev == "down_dodge":
                                if (
                                    not p2.on_ground
                                    or remote_p2_keys[p2.controls["left"]]
                                    or remote_p2_keys[p2.controls["right"]]
                                ):
                                    p2.dodge(sfx, jukebox.volume)
                                else:
                                    p2.parry_window = 5
                            elif ev == "down_grab":
                                p2.grab(sfx, jukebox.volume)
                            elif ev == "down_cancel":
                                p2.roman_cancel(
                                    particles, popups, sfx, jukebox.volume
                                )
                            elif ev == "down_ultimate":
                                p2.trigger_ultimate(
                                    2,
                                    p1,
                                    projectiles,
                                    particles,
                                    popups,
                                    sfx,
                                    jukebox.volume,
                                )
                        p2.update(
                            remote_p2_keys,
                            platforms,
                            wind_vx=wind_vx,
                            afterimages=afterimages,
                            sfx=sfx,
                            volume=jukebox.volume,
                        )
                    elif cpu_enabled:
                        cpu_p2.update(
                            p1,
                            platforms,
                            projectiles,
                            particles,
                            popups,
                            sfx,
                            jukebox.volume,
                            training_mode,
                            wind_vx=wind_vx,
                            afterimages=afterimages,
                        )
                    else:
                        p2.update(
                            keys,
                            platforms,
                            wind_vx=wind_vx,
                            afterimages=afterimages,
                            sfx=sfx,
                            volume=jukebox.volume,
                        )

                    if smash_ball is not None:
                        for idx_f, ftr in ((1, p1), (2, p2)):
                            hb = ftr.get_hitbox()
                            if (
                                hb
                                and not ftr.hit_registered
                                and hb.colliderect(smash_ball.rect)
                            ):
                                ftr.hit_registered = True
                                smash_ball.hp -= (
                                    ftr.current_move["damage"]
                                    if ftr.current_move
                                    else 8.0
                                )
                                spawn_hit_particles(
                                    particles,
                                    smash_ball.rect.centerx,
                                    smash_ball.rect.centery,
                                    ARCADE_NEON_YELLOW,
                                    count=10,
                                )
                                sfx.play("hit", jukebox.volume)
                                if smash_ball.hp <= 0:
                                    ftr.add_meter(100.0)
                                    popups.append(
                                        DamagePopup(
                                            ftr.rect.centerx,
                                            ftr.rect.top - 22,
                                            "SMASH BALL! FINAL PRONTO!",
                                            METER_READY_COLOR,
                                            life=46,
                                        )
                                    )
                                    spawn_hit_particles(
                                        particles,
                                        smash_ball.rect.centerx,
                                        smash_ball.rect.centery,
                                        METER_READY_COLOR,
                                        count=24,
                                    )
                                    sfx.play("ultimate", jukebox.volume)
                                    smash_ball = None
                                    break

                    remaining_pickups = []
                    for pk in pickups:
                        pk.update()
                        if pk.life <= 0:
                            continue
                        collector = None
                        if p1.rect.colliderect(pk.rect):
                            collector = p1
                        elif p2.rect.colliderect(pk.rect):
                            collector = p2

                        if collector is not None:
                            if pk.kind == "meter":
                                collector.add_meter(30.0)
                            elif pk.kind == "heal":
                                collector.damage_pct = max(
                                    0.0, collector.damage_pct - 15.0
                                )
                            elif pk.kind == "boost":
                                collector.power_boost_timer = 300
                            popups.append(
                                DamagePopup(
                                    collector.rect.centerx,
                                    collector.rect.top - 16,
                                    pk.label,
                                    pk.color,
                                    life=36,
                                )
                            )
                            spawn_hit_particles(
                                particles,
                                pk.rect.centerx,
                                pk.rect.centery,
                                pk.color,
                                count=10,
                            )
                            sfx.play("pickup", jukebox.volume)
                            continue
                        remaining_pickups.append(pk)
                    pickups = remaining_pickups

                    proj1 = p1.try_spawn_projectile(1)
                    if proj1:
                        projectiles.append(proj1)
                    proj2 = p2.try_spawn_projectile(2)
                    if proj2:
                        projectiles.append(proj2)

                    for pr in projectiles:
                        pr.update()

                    p1_projs = [
                        p
                        for p in projectiles
                        if p.owner_idx == 1 and p.life > 0
                    ]
                    p2_projs = [
                        p
                        for p in projectiles
                        if p.owner_idx == 2 and p.life > 0
                    ]
                    canceled_p1 = set()
                    canceled_p2 = set()
                    for i1, pr1 in enumerate(p1_projs):
                        for i2, pr2 in enumerate(p2_projs):
                            if pr1.rect.colliderect(pr2.rect):
                                canceled_p1.add(i1)
                                canceled_p2.add(i2)
                                cx = (
                                    pr1.rect.centerx + pr2.rect.centerx
                                ) // 2
                                cy = (
                                    pr1.rect.centery + pr2.rect.centery
                                ) // 2
                                spawn_hit_particles(
                                    particles,
                                    cx,
                                    cy,
                                    ARCADE_NEON_CYAN,
                                    count=10,
                                )
                                sfx.play("hit", jukebox.volume)

                    active_projs = []
                    for i1, pr in enumerate(p1_projs):
                        if (
                            i1 in canceled_p1
                            or pr.rect.right < -80
                            or pr.rect.left > WIDTH + 80
                        ):
                            continue
                        if pr.rect.colliderect(p2.rect):
                            res = p2.take_hit(
                                pr.damage,
                                pr.base_kb,
                                pr.scaling_kb,
                                25,
                                1 if pr.vx >= 0 else -1,
                                sudden_death=sudden_death,
                            )
                            if res == "parry":
                                spawn_hit_particles(
                                    particles,
                                    p2.rect.centerx,
                                    p2.rect.centery,
                                    PARRY_COLOR,
                                    count=14,
                                )
                                popups.append(
                                    DamagePopup(
                                        p2.rect.centerx,
                                        p2.rect.top - 16,
                                        "PARRY! +25%",
                                        PARRY_COLOR,
                                    )
                                )
                                sfx.play("parry", jukebox.volume)
                            elif res == "shield":
                                sfx.play("blip", jukebox.volume)
                            elif res == "hit":
                                p1.register_combo_hit("Onda", pr.damage)
                                spawn_hit_particles(
                                    particles,
                                    pr.rect.centerx,
                                    pr.rect.centery,
                                    pr.color,
                                    count=7,
                                )
                                popups.append(
                                    DamagePopup(
                                        p2.rect.centerx,
                                        p2.rect.top - 10,
                                        f"-{int(round(pr.damage))}%",
                                        pr.color,
                                    )
                                )
                                sfx.play("hit", jukebox.volume)
                            continue
                        active_projs.append(pr)

                    for i2, pr in enumerate(p2_projs):
                        if (
                            i2 in canceled_p2
                            or pr.rect.right < -80
                            or pr.rect.left > WIDTH + 80
                        ):
                            continue
                        if pr.rect.colliderect(p1.rect):
                            res = p1.take_hit(
                                pr.damage,
                                pr.base_kb,
                                pr.scaling_kb,
                                25,
                                1 if pr.vx >= 0 else -1,
                                sudden_death=sudden_death,
                            )
                            if res == "parry":
                                spawn_hit_particles(
                                    particles,
                                    p1.rect.centerx,
                                    p1.rect.centery,
                                    PARRY_COLOR,
                                    count=14,
                                )
                                popups.append(
                                    DamagePopup(
                                        p1.rect.centerx,
                                        p1.rect.top - 16,
                                        "PARRY! +25%",
                                        PARRY_COLOR,
                                    )
                                )
                                sfx.play("parry", jukebox.volume)
                            elif res == "shield":
                                sfx.play("blip", jukebox.volume)
                            elif res == "hit":
                                p2.register_combo_hit("Onda", pr.damage)
                                spawn_hit_particles(
                                    particles,
                                    pr.rect.centerx,
                                    pr.rect.centery,
                                    pr.color,
                                    count=7,
                                )
                                popups.append(
                                    DamagePopup(
                                        p1.rect.centerx,
                                        p1.rect.top - 10,
                                        f"-{int(round(pr.damage))}%",
                                        pr.color,
                                    )
                                )
                                sfx.play("hit", jukebox.volume)
                            continue
                        active_projs.append(pr)

                    projectiles = active_projs

                    hs1, sh1 = check_combat(
                        p1,
                        p2,
                        particles,
                        popups,
                        sfx,
                        jukebox.volume,
                        sudden_death=sudden_death,
                    )
                    hs2, sh2 = check_combat(
                        p2,
                        p1,
                        particles,
                        popups,
                        sfx,
                        jukebox.volume,
                        sudden_death=sudden_death,
                    )
                    hitstop_frames += hs1 + hs2
                    shake_frames = max(shake_frames, sh1, sh2)

                    ko1 = check_blast_zones(
                        p1,
                        p2,
                        particles,
                        ko_beams,
                        sfx,
                        jukebox.volume,
                        training_mode,
                    )
                    ko2 = check_blast_zones(
                        p2,
                        p1,
                        particles,
                        ko_beams,
                        sfx,
                        jukebox.volume,
                        training_mode,
                    )
                    if ko1 or ko2:
                        ko_banner_timer = 45
                        shake_frames = max(shake_frames, 12)
                        if (
                            not training_mode
                            and (p1.stocks <= 0 or p2.stocks <= 0)
                            and game_finish_timer == 0
                        ):
                            game_finish_timer = 32

                    ko_beams = [kb for kb in ko_beams if kb.life > 0]
                    for kb in ko_beams:
                        kb.update()

                    afterimages = [af for af in afterimages if af.life > 0]
                    for af in afterimages:
                        af.update()

                    particles = [pt for pt in particles if pt.life > 0]
                    for pt in particles:
                        pt.update()

                    popups = [pp for pp in popups if pp.life > 0]
                    for pp in popups:
                        pp.update()

                    if arcade_mode and p1.max_combo > arcade_best_combo_run:
                        arcade_best_combo_run = p1.max_combo

                    is_over_now = False
                    if game_finish_timer > 0:
                        game_finish_timer -= 1
                        if game_finish_timer == 0:
                            is_over_now = True
                            if (
                                arcade_mode
                                and p1.stocks > 0
                                and arcade_stage_num >= len(arcade_queue)
                            ):
                                elapsed_s = round(arcade_frames / FPS, 1)
                                records["clears"] = records.get("clears", 0) + 1
                                notes = []
                                prev_best = records.get("best_time_sec")
                                if prev_best is None or elapsed_s < prev_best:
                                    records["best_time_sec"] = elapsed_s
                                    records["best_time_char"] = p1.name
                                    notes.append("NOVO RECORDE DE TEMPO!")
                                if arcade_best_combo_run > records.get(
                                    "best_combo", 0
                                ):
                                    records["best_combo"] = (
                                        arcade_best_combo_run
                                    )
                                    records["best_combo_char"] = p1.name
                                    notes.append("NOVO RECORDE DE COMBO!")
                                save_arcade_records(records)
                                new_record_banner = "  •  ".join(notes)
                            state = "game_over"

                # Host transmite snapshot completo ao Cliente
                if net.role == "host" and net.connected:
                    net.send(
                        {
                            "type": "game_state",
                            "p1": p1.to_net_dict(),
                            "p2": p2.to_net_dict(),
                            "ko_banner": ko_banner_timer,
                            "game_finish": game_finish_timer,
                            "game_over": state == "game_over",
                            "plats": [
                                [pl.rect.x, pl.rect.y] for pl in platforms
                            ],
                            "projs": [
                                [
                                    pr.owner_idx,
                                    pr.rect.x,
                                    pr.rect.y,
                                    list(pr.color[:3]),
                                ]
                                for pr in projectiles
                            ],
                            "pickups": [
                                [
                                    pk.rect.x,
                                    pk.rect.y,
                                    next(
                                        (
                                            idx_t
                                            for idx_t, t in enumerate(
                                                StagePickup.TYPES
                                            )
                                            if t[0] == pk.kind
                                        ),
                                        0,
                                    ),
                                ]
                                for pk in pickups
                            ],
                            "smash_ball": [
                                round(smash_ball.x, 1),
                                round(smash_ball.y, 1),
                            ]
                            if smash_ball
                            else None,
                        }
                    )

            offset_x = (
                random.randint(-5, 5)
                if (not paused and shake_frames > 0)
                else 0
            )
            offset_y = (
                random.randint(-5, 5)
                if (not paused and shake_frames > 0)
                else 0
            )

            draw_arcade_backdrop(
                screen,
                tick_count,
                bg_color=stage_cfg.get("bg_tint", BG_COLOR),
                grid_color=stage_cfg.get("grid_tint", GRID_COLOR),
            )

            for kb in ko_beams:
                kb.draw(screen)

            for plat in platforms:
                plat.draw(screen)

            for pk in pickups:
                pk.draw(screen, offset_x, offset_y)

            if smash_ball is not None:
                smash_ball.draw(screen, offset_x, offset_y)

            for af in afterimages:
                af.draw(screen, offset_x, offset_y)

            for pr in projectiles:
                pr.draw(screen, offset_x, offset_y)

            p1.draw(
                screen,
                offset_x,
                offset_y,
                show_training_boxes=training_mode,
            )
            p2.draw(
                screen,
                offset_x,
                offset_y,
                show_training_boxes=training_mode,
            )

            draw_offscreen_magnifier(screen, p1, small_font)
            draw_offscreen_magnifier(screen, p2, small_font)

            for pt in particles:
                pt.draw(screen, offset_x, offset_y)

            for pp in popups:
                pp.draw(screen, combo_font, offset_x, offset_y)

            if game_finish_timer > 0:
                g_surf = game_banner_font.render(
                    "GAME!", True, ARCADE_NEON_YELLOW
                )
                screen.blit(
                    g_surf,
                    g_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)),
                )
            elif ko_banner_timer > 0:
                ko_surf = title_font.render("KO!", True, ARCADE_NEON_YELLOW)
                screen.blit(
                    ko_surf,
                    ko_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)),
                )

            draw_hud(
                screen,
                font,
                combo_font,
                small_font,
                p1,
                p2,
                cpu_enabled,
                cpu_difficulty,
                training_mode,
                sudden_death=sudden_death,
                net_role=net.role,
            )

            if net.role:
                mode_label = f"ONLINE ({'HOST P1' if net.role == 'host' else 'CLIENTE P2'})"
            elif arcade_mode:
                mode_label = f"TORRE {arcade_stage_num}/{len(arcade_queue)} ({cpu_p2.difficulty})"
            else:
                mode_label = (
                    f"CPU ({cpu_difficulty})" if cpu_enabled else "2 Jogadores"
                )
            stage_label = stage_cfg["name"]
            train_label = " | TREINO (HITBOXES)" if training_mode else ""
            controls_hint = small_font.render(
                f"{mode_label} | {stage_label}{train_label} | Segure Ataque: Smash | Segure Defesa: Escudo | Q/Alt: Final Smash",
                True,
                ARCADE_NEON_YELLOW,
            )
            screen.blit(controls_hint, (24, 26))
            draw_clock_top_right(screen, small_font)

            if paused:
                draw_pause_overlay(
                    screen,
                    btn_font,
                    small_font,
                    cpu_enabled,
                    cpu_difficulty,
                    training_mode,
                    mouse_pos,
                )

        elif state == "game_over":
            draw_game_over_screen(
                screen,
                title_font,
                btn_font,
                small_font,
                p1,
                p2,
                cpu_enabled,
                arcade_mode,
                arcade_stage_num,
                max(1, len(arcade_queue)),
                arcade_frames / FPS,
                new_record_banner,
                mouse_pos,
                tick_count,
                net_role=net.role,
            )

        pygame.display.flip()

def resource_path(relative_path):
  """Retorna o caminho real do arquivo, seja rodando em script ou dentro do .exe."""
  base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
  return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    main()
