# -*- coding: utf-8 -*-
"""
idle_cat.py — 유휴 감지 픽셀 고양이 + 타이머 알람  (Windows / macOS)  v4

기본 기능:
    일정 시간 입력이 없으면 픽셀 고양이가 화면 하단을 산책 (걷기·달리기·
    앉기·그루밍·기지개·잠자기, 클릭 시 점프 후 도망)

타이머 기능:
    작은 설정 창에서 분 단위 타이머를 입력하고 "시작"을 누르면 카운트다운.

    ⏳ 마감 20초 전부터: 고양이들이 하나둘 화면 가운데로 모여들어
       원형 대형을 짜고 앉아서 기다립니다.
    ⏰ 시간이 다 되면: 화면이 붉게 번쩍거리고, 원형으로 모인 고양이들이
       점점 커지기 시작합니다.
    ✅ "정지/완료" 버튼을 누르면 즉시 원상 복귀.

실행:
    Windows :  pythonw idle_cat.py
    macOS   :  python3 idle_cat.py
    공통    :  python idle_cat.py 30      (유휴 감지 기준을 30초로 지정)

조작:
    고양이 좌클릭  → 깜짝 놀라 점프한 뒤 화면 밖으로 도망 (평상시 고양이만 해당)
    설정 창의 "정지/완료" → 알람/집결 중단 및 초기화
"""

import sys
import re
import math
import time
import random
import ctypes
import subprocess
import tkinter as tk

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

# ─────────────────────────────── 설정 ───────────────────────────────
IDLE_SECONDS   = 60        # 이 시간 동안 입력이 없으면 평상시 고양이 등장
SCALE          = 5         # 기본 픽셀 확대 배율
BASE_SPEED     = 4         # 걷기 속도 (px / tick)
GROUND_MARGIN  = 60        # 화면 맨 아래에서 띄울 높이
CHECK_MS       = 500       # 유휴 확인 주기 (ms)
CREDIT_TEXT    = "presented by g.ad.c 2026"
TRANSPARENT    = "#FF00FF"

# 알람(타이머 초과) 관련 설정
ALARM_FLASH_MS       = 250    # 화면 번쩍임 간격 (ms)
ALARM_FLASH_ALPHA    = 0.35   # 번쩍임 최대 투명도(0~1)
ALARM_GROWTH_STEP    = 1      # 성장 시 늘어나는 배율 단위
ALARM_GROWTH_MS      = 4000   # 이 간격마다 고양이가 커짐
ALARM_SCALE_MAX      = 16     # 최대 확대 배율
ALARM_CAT_COUNT_MAX  = 5      # 원형 대형에 모이는 최대 고양이 수(메인 포함)

# 집결(마감 전 모임) 관련 설정
GATHER_LEAD_SECONDS = 20      # 마감 이 시간 전부터 집결 시작
GATHER_RADIUS_X     = 110     # 원형 대형 가로 반지름(px)
GATHER_RADIUS_Y     = 50      # 원형 대형 세로 반지름(px)
GATHER_MOVE_SPEED   = 7.0     # 집결 중 이동 속도 (px / tick)

if len(sys.argv) > 1:
    try:
        IDLE_SECONDS = max(3, int(sys.argv[1]))
    except ValueError:
        pass

# ─────────────────────────── 픽셀 스프라이트 ───────────────────────────
PALETTE = {
    "#": "#E8926F", "d": "#8C4A32", "e": "#2B1B12", "c": "#FBE7D2",
    "p": "#F2A09A", "n": "#C96A50", "m": "#8C4A32", "z": "#8A8A96",
}

GRIDS = {
    "WALK1": [
        "........#....#..", "........##..##..", "........######..",
        "d.......#e##e#..", "dd......##n###p.", ".##############.",
        ".######cc######.", "..#####cc#####..", "..############..",
        "..############..", "..##..###..##...", "..##...##...##..",
    ],
    "WALK2": [
        "................", "........#....#..", "........##..##..",
        "........######..", ".dd.....#e##e#..", "..#######n###p..",
        "..#####cc#####..", "..#####cc#####..", "..############..",
        "..############..", "...###.###.###..", "...##..##...##..",
    ],
    "RUN1": [
        "................", "........#....#..", "........##..##..",
        "d.......######..", "dd......#e##e#..", ".########n###p..",
        ".######cc#####..", ".#####cc######..", ".#############..",
        "..############..", ".##....##....##.", "#......##......#",
    ],
    "RUN2": [
        "................", "................", "........#....#..",
        "........##..##..", ".dd.....######..", "..#######e##e#p.",
        "..######cc####..", "..####cc######..", "..############..",
        "...##########...", "....##.##.##....", "................",
    ],
    "SIT1": [
        "....#....#......", "....##..##......", "....######......",
        "....#e##e#..dd..", "....##n###p.#d..", "....######..#...",
        "...##cc####.#...", "...##cc######...", "...##########...",
        "...#########....", "...##.####.##...", "................",
    ],
    "SIT2": [
        "....#....#......", "....##..##......", "....######......",
        "....#e##e#......", "....##n###p.....", "....######.dd...",
        "...##cc####.#d..", "...##cc######...", "...##########...",
        "...#########....", "...##.####.##...", "................",
    ],
    "GROOM1": [
        "....#....#......", "....##..##......", "....######......",
        "....#e##e#..dd..", "....##n###..#d..", "...#######..#...",
        "...#.cc####.#...", "..##.cc######...", "..#.#########...",
        "....#########...", "....#.####.##...", "................",
    ],
    "GROOM2": [
        "................", "....#....#......", "....##..##......",
        "....######..dd..", "...##e##e#..#d..", "..#.##n###..#...",
        "..#..cc####.#...", "..##.cc######...", "...##########...",
        "....#########...", "....#.####.##...", "................",
    ],
    "SLEEP1": [
        "..........z.....", "................", "................",
        ".....#...#......", ".....##.##......", "....#######.....",
        "...#md##md#.....", "..#############.", "..####cc######d.",
        "..############d.", "...###########..", "................",
    ],
    "SLEEP2": [
        "................", "...........z....", ".........z......",
        ".....#...#......", ".....##.##......", "....#######.....",
        "...#md##md#.....", "..#############.", "..####cc######d.",
        "..############d.", "...###########..", "................",
    ],
    "STRETCH1": [
        "................", "..........dd....", "...........#d...",
        "..........##....", ".........###....", ".......#####....",
        "..#...######....", ".############...", "#e##########....",
        "#n#####..##.....", "###..##...##....", ".....##....##...",
    ],
    "STRETCH2": [
        "................", "..........dd....", "..........#d....",
        "..........##....", ".........###....", ".......#####....",
        "..#..#######....", ".############...", "#e#########.....",
        "#n####..##......", "###...##..##....", "......##...##...",
    ],
    "JUMP": [
        "........#....#..", "........##..##..", "d.......######..",
        "d.......#e##e#..", ".#########n##p..", ".######cc#####..",
        ".#####cc######..", ".#############..", "..###########...",
        "..##..####..##..", ".##....##....##.", "................",
    ],
}

STATE_DEF = {
    "walk":       dict(frames=["WALK1", "WALK2"],       tick=130, speed=1.0),
    "run":        dict(frames=["RUN1", "RUN2"],         tick=85,  speed=2.6),
    "sit":        dict(frames=["SIT1", "SIT2"],         tick=430, speed=0),
    "groom":      dict(frames=["GROOM1", "GROOM2"],     tick=300, speed=0),
    "sleep":      dict(frames=["SLEEP1", "SLEEP2"],     tick=650, speed=0),
    "stretch":    dict(frames=["STRETCH1", "STRETCH2"], tick=350, speed=0),
    "jump":       dict(frames=["JUMP"],                 tick=100, speed=0),
    "flee":       dict(frames=["RUN1", "RUN2"],         tick=60,  speed=4.5),
    "gather":     dict(frames=["WALK1", "WALK2"],       tick=110, speed=0),
    "circle_sit": dict(frames=["SIT1", "SIT2"],         tick=430, speed=0),
}

IDLE_ACTIONS = [
    ("sit",     30, 3.0,  7.0),
    ("groom",   20, 3.0,  6.0),
    ("stretch", 15, 1.5,  3.0),
    ("sleep",   15, 8.0, 18.0),
    ("run",     20, 1.5,  3.5),
]
ACTION_CHANCE = 0.015


def build_sprite(grid, scale, flip=False):
    h, w = len(grid), max(len(r) for r in grid)
    img = tk.PhotoImage(width=w * scale, height=h * scale)
    for y, row in enumerate(grid):
        row = row.ljust(w, ".")
        if flip:
            row = row[::-1]
        for x, ch in enumerate(row):
            color = PALETTE.get(ch)
            if color:
                img.put(color, to=(x * scale, y * scale,
                                   (x + 1) * scale, (y + 1) * scale))
    return img


# ─────────────────────────── 유휴 시간 감지 ───────────────────────────
if IS_WIN:
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

    def idle_seconds():
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        return (ctypes.windll.kernel32.GetTickCount() - lii.dwTime) / 1000.0

elif IS_MAC:
    _HID_RE = re.compile(r'"HIDIdleTime"\s*=\s*(\d+)')

    def idle_seconds():
        try:
            out = subprocess.run(
                ["ioreg", "-c", "IOHIDSystem", "-d", "4"],
                capture_output=True, text=True, timeout=3,
            ).stdout
            m = _HID_RE.search(out)
            return int(m.group(1)) / 1e9 if m else 0.0
        except Exception:
            return 0.0
else:
    def idle_seconds():
        return 0.0


def screen_bg_attr(win):
    """OS별 투명 배경 속성 적용, 사용한 배경색 문자열 반환"""
    if IS_WIN:
        win.attributes("-transparentcolor", TRANSPARENT)
        return TRANSPARENT
    elif IS_MAC:
        try:
            win.attributes("-transparent", True)
            return "systemTransparent"
        except tk.TclError:
            return "#1E1E1E"
    return "#1E1E1E"


# ─────────────────────────────── 고양이 창 ───────────────────────────────
class Cat:
    """화면 위를 돌아다니는 고양이 한 마리 (Toplevel 창 하나)"""

    def __init__(self, app, show_credit=False):
        self.app = app
        self.win = tk.Toplevel(app.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.bg = screen_bg_attr(self.win)
        self.win.config(bg=self.bg)

        self.label = tk.Label(self.win, bg=self.bg, bd=0)
        self.label.pack()
        if show_credit:
            self.credit = tk.Label(self.win, text=CREDIT_TEXT, bg=self.bg,
                                    fg="#9A9A9A", font=("Consolas", 8), bd=0)
            self.credit.pack()

        self.label.bind("<Button-1>", self.on_click)
        self.label.bind("<Button-3>", lambda e: app.root.destroy())

        self.scale = SCALE
        self.sprites = {}
        self._build_sprites()

        self.visible = False
        self.forced = False          # True면 유휴와 무관하게 항상 표시
        self.x = 0.0
        self.y = float(app.ground_y)
        self.direction = 1
        self.frame_i = 0
        self.state = "walk"
        self.state_until = 0.0
        self.jump_step = 0
        self.target_x = 0.0
        self.target_y = 0.0

    def _build_sprites(self):
        self.sprites = {}
        for name, grid in GRIDS.items():
            self.sprites[(name, +1)] = build_sprite(grid, self.scale)
            self.sprites[(name, -1)] = build_sprite(grid, self.scale, flip=True)
        self.w = self.sprites[("WALK1", 1)].width()
        self.h = self.sprites[("WALK1", 1)].height()

    def grow(self, amount=ALARM_GROWTH_STEP):
        if self.scale >= ALARM_SCALE_MAX:
            return
        old_h = self.h
        self.scale = min(self.scale + amount, ALARM_SCALE_MAX)
        self._build_sprites()
        self.y -= (self.h - old_h)   # 커진 만큼 위로 보정(발 위치 유지)

    def reset_scale(self):
        self.scale = SCALE
        self._build_sprites()

    # ── 등장/퇴장 ──────────────────────────────────────────
    def appear(self, from_edge=True):
        self.visible = True
        self.direction = random.choice([-1, 1])
        base_h = build_sprite(GRIDS["WALK1"], SCALE).height()
        if from_edge:
            self.x = -self.w if self.direction == 1 else self.app.screen_w
        else:
            self.x = random.uniform(0, max(0, self.app.screen_w - self.w))
        self.y = self.app.ground_y - (self.h - base_h)
        self.set_state("walk")
        self.win.deiconify()
        self.win.attributes("-topmost", True)
        self.step()

    def hide(self):
        self.visible = False
        self.win.withdraw()

    def destroy(self):
        try:
            self.win.destroy()
        except tk.TclError:
            pass

    # ── 상태 전환 ──────────────────────────────────────────
    def set_state(self, state, duration=None):
        self.state = state
        self.frame_i = 0
        self.state_until = time.monotonic() + duration if duration else 0.0

    def pick_random_action(self):
        total = sum(w for _, w, _, _ in IDLE_ACTIONS)
        r = random.uniform(0, total)
        acc = 0
        for name, w, dmin, dmax in IDLE_ACTIONS:
            acc += w
            if r <= acc:
                self.set_state(name, random.uniform(dmin, dmax))
                return

    def on_click(self, _event=None):
        if self.forced or self.state in ("jump", "flee", "gather", "circle_sit"):
            return
        self.jump_step = 0
        self.direction = -1 if self.x < self.app.screen_w / 2 else 1
        self.set_state("jump")

    # ── 메인 루프 ──────────────────────────────────────────
    def step(self):
        if not self.visible:
            return

        if self.state == "gather":
            self._step_gather()
            return
        if self.state == "circle_sit":
            self._step_circle_sit()
            return

        if not self.forced and self.state not in ("jump", "flee") and idle_seconds() < 1.0:
            self.hide()
            return

        now = time.monotonic()
        conf = STATE_DEF[self.state]

        if self.state == "walk":
            if not self.forced and random.random() < ACTION_CHANCE:
                self.pick_random_action()
                conf = STATE_DEF[self.state]

        elif self.state == "jump":
            hop = [-18, -28, -18, 0]
            base_h = build_sprite(GRIDS["WALK1"], SCALE).height()
            base_y = self.app.ground_y - (self.h - base_h)
            self.y = base_y + hop[min(self.jump_step, 3)]
            self.jump_step += 1
            if self.jump_step > 3:
                self.y = base_y
                self.set_state("flee")
                conf = STATE_DEF["flee"]

        elif self.state_until and now >= self.state_until:
            if self.state == "sleep":
                self.set_state("stretch", 2.0)
            else:
                self.set_state("walk")
            conf = STATE_DEF[self.state]

        speed = BASE_SPEED * conf["speed"]
        if speed:
            self.x += speed * self.direction
            if self.state == "flee":
                if self.x < -self.w or self.x > self.app.screen_w:
                    self.hide()
                    return
            else:
                if self.x <= 0:
                    self.x, self.direction = 0, 1
                elif self.x >= self.app.screen_w - self.w:
                    self.x, self.direction = self.app.screen_w - self.w, -1

        frames = conf["frames"]
        self.frame_i = (self.frame_i + 1) % len(frames)
        img = self.sprites[(frames[self.frame_i], self.direction)]
        self.label.config(image=img)
        self.win.geometry(f"+{int(self.x)}+{int(self.y)}")
        self.win.after(conf["tick"], self.step)

    # ── 집결(원형 대형으로 이동) ──────────────────────────
    def _step_gather(self):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)

        if dist < 5:
            self.x, self.y = self.target_x, self.target_y
            self.direction = 1 if self.app.gather_center_x >= self.x else -1
            self.set_state("circle_sit")
        else:
            spd = min(GATHER_MOVE_SPEED, dist)
            self.x += spd * dx / dist
            self.y += spd * dy / dist
            self.direction = 1 if dx >= 0 else -1

        conf = STATE_DEF["gather"]
        frames = conf["frames"]
        self.frame_i = (self.frame_i + 1) % len(frames)
        img = self.sprites[(frames[self.frame_i], self.direction)]
        self.label.config(image=img)
        self.win.geometry(f"+{int(self.x)}+{int(self.y)}")
        self.win.after(conf["tick"], self.step)

    def _step_circle_sit(self):
        conf = STATE_DEF["circle_sit"]
        frames = conf["frames"]
        self.frame_i = (self.frame_i + 1) % len(frames)
        img = self.sprites[(frames[self.frame_i], self.direction)]
        self.label.config(image=img)
        self.win.geometry(f"+{int(self.x)}+{int(self.y)}")
        self.win.after(conf["tick"], self.step)


# ─────────────────────────────── 앱(설정 창 + 타이머) ───────────────────────────────
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("IdleCat")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.geometry("+40+40")

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.ground_y = self.screen_h - GROUND_MARGIN - 60

        self._build_ui()

        self.idle_cat = Cat(self, show_credit=True)
        self.extra_cats = []          # 집결/알람용 추가 고양이
        self.gather_active = False
        self.alarm_active = False
        self.flash_win = None
        self.flash_on = False
        self.timer_remaining = 0
        self.timer_running = False
        self._gather_positions = []
        self._gather_spawn_index = 0

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(CHECK_MS, self.watch_idle)
        self.root.mainloop()

    # ── UI ──────────────────────────────────────────
    def _build_ui(self):
        frm = tk.Frame(self.root, padx=12, pady=10)
        frm.pack(fill="both", expand=True)

        tk.Label(frm, text="🐱 IdleCat 타이머", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

        tk.Label(frm, text="시간(분):").grid(row=1, column=0, sticky="w")
        self.minutes_var = tk.StringVar(value="25")
        tk.Entry(frm, textvariable=self.minutes_var, width=6).grid(row=1, column=1, sticky="w")

        tk.Button(frm, text="시작", width=6, command=self.start_timer).grid(
            row=2, column=0, pady=6, sticky="w")
        tk.Button(frm, text="정지/완료", width=8, command=self.stop_timer).grid(
            row=2, column=1, columnspan=2, pady=6, sticky="w")

        self.timer_label = tk.Label(frm, text="타이머 꺼짐", fg="#555555")
        self.timer_label.grid(row=3, column=0, columnspan=3, sticky="w")

        tk.Label(frm, text=CREDIT_TEXT, fg="#aaaaaa", font=("Consolas", 8)).grid(
            row=4, column=0, columnspan=3, sticky="e", pady=(10, 0))

    # ── 타이머 ──────────────────────────────────────────
    def start_timer(self):
        try:
            minutes = float(self.minutes_var.get())
        except ValueError:
            self.timer_label.config(text="숫자를 입력하세요", fg="#CC3333")
            return
        if minutes <= 0:
            self.timer_label.config(text="0보다 큰 값을 입력하세요", fg="#CC3333")
            return

        self.stop_alarm()
        self.timer_remaining = int(minutes * 60)
        self.timer_running = True
        self.timer_label.config(fg="#555555")

        if self.timer_remaining <= GATHER_LEAD_SECONDS:
            self.start_gather()

        self._tick_timer()

    def _tick_timer(self):
        if not self.timer_running:
            return
        if self.timer_remaining <= 0:
            self.timer_label.config(text="⏰ 시간 종료!", fg="#CC3333")
            self.trigger_alarm()
            return
        if self.timer_remaining == GATHER_LEAD_SECONDS and not self.gather_active:
            self.start_gather()

        mm, ss = divmod(self.timer_remaining, 60)
        self.timer_label.config(text=f"남은 시간 {mm:02d}:{ss:02d}")
        self.timer_remaining -= 1
        self.root.after(1000, self._tick_timer)

    def stop_timer(self):
        self.timer_running = False
        if self.alarm_active:
            self.timer_label.config(text="완료! 타이머 꺼짐", fg="#2E8B57")
        else:
            self.timer_label.config(text="타이머 꺼짐", fg="#555555")
        self.stop_alarm()

    # ── 집결 (마감 20초 전) ──────────────────────────────
    def _circle_positions(self, count):
        pts = []
        for i in range(count):
            angle = 2 * math.pi * i / count - math.pi / 2
            tx = self.gather_center_x + GATHER_RADIUS_X * math.cos(angle)
            ty = self.gather_center_y + GATHER_RADIUS_Y * math.sin(angle)
            pts.append((tx, ty))
        return pts

    def start_gather(self):
        if self.gather_active:
            return
        self.gather_active = True
        self.gather_center_x = self.screen_w / 2
        self.gather_center_y = self.ground_y - 40

        positions = self._circle_positions(ALARM_CAT_COUNT_MAX)
        self._gather_positions = positions

        if not self.idle_cat.visible:
            self.idle_cat.appear(from_edge=True)
        self.idle_cat.forced = True
        self.idle_cat.target_x, self.idle_cat.target_y = positions[0]
        self.idle_cat.set_state("gather")

        self._gather_spawn_index = 1
        self._gather_spawn_next()

    def _gather_spawn_next(self):
        if not self.gather_active:
            return
        if self._gather_spawn_index >= len(self._gather_positions):
            return
        c = Cat(self, show_credit=False)
        c.forced = True
        c.appear(from_edge=True)
        tx, ty = self._gather_positions[self._gather_spawn_index]
        c.target_x, c.target_y = tx, ty
        c.set_state("gather")
        self.extra_cats.append(c)
        self._gather_spawn_index += 1

        remaining_slots = len(self._gather_positions) - self._gather_spawn_index
        if remaining_slots > 0:
            interval_ms = max(800, int(GATHER_LEAD_SECONDS * 1000 / len(self._gather_positions)))
            self.root.after(interval_ms, self._gather_spawn_next)

    # ── 알람 (시간 초과) ──────────────────────────────────
    def trigger_alarm(self):
        self.timer_running = False
        self.alarm_active = True

        if not self.gather_active:
            # 20초 미만으로 설정해 집결이 생략된 경우 대비
            self.start_gather()

        self._flash_step()
        self._alarm_grow_step()

    def stop_alarm(self):
        self.gather_active = False
        self.alarm_active = False
        self._gather_positions = []
        self._gather_spawn_index = 0

        if self.flash_win is not None:
            try:
                self.flash_win.destroy()
            except tk.TclError:
                pass
            self.flash_win = None

        for c in self.extra_cats:
            c.destroy()
        self.extra_cats = []

        self.idle_cat.forced = False
        self.idle_cat.reset_scale()
        if self.idle_cat.visible:
            self.idle_cat.hide()

    def _flash_step(self):
        if not self.alarm_active:
            return
        if self.flash_win is None:
            self.flash_win = tk.Toplevel(self.root)
            self.flash_win.overrideredirect(True)
            self.flash_win.geometry(f"{self.screen_w}x{self.screen_h}+0+0")
            self.flash_win.attributes("-topmost", True)
            self.flash_win.config(bg="#FF3B30")
            try:
                self.flash_win.attributes("-alpha", 0.0)
            except tk.TclError:
                pass

        self.flash_on = not self.flash_on
        try:
            self.flash_win.attributes("-alpha", ALARM_FLASH_ALPHA if self.flash_on else 0.0)
        except tk.TclError:
            pass

        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(ALARM_FLASH_MS, self._flash_step)

    def _alarm_grow_step(self):
        if not self.alarm_active:
            return
        self.idle_cat.grow()
        for c in self.extra_cats:
            c.grow()
        self.root.after(ALARM_GROWTH_MS, self._alarm_grow_step)

    # ── 평상시 유휴 감지 ──────────────────────────────────
    def watch_idle(self):
        if (not self.idle_cat.visible and not self.idle_cat.forced
                and idle_seconds() >= IDLE_SECONDS):
            self.idle_cat.appear()
        self.root.after(CHECK_MS, self.watch_idle)

    def on_close(self):
        self.stop_alarm()
        self.root.destroy()


if __name__ == "__main__":
    if not (IS_WIN or IS_MAC):
        print("이 스크립트는 Windows 또는 macOS에서 실행해야 합니다.")
        sys.exit(1)
    App()
