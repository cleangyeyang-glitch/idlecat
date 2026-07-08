# -*- coding: utf-8 -*-
"""
idle_cat.py — 유휴 감지 픽셀 고양이 (Windows / macOS)  v2

일정 시간(기본 60초) 동안 키보드/마우스 입력이 없으면
클로드 오렌지색 비트맵 고양이가 화면 하단에 나타나 자유롭게 행동합니다.

동작 종류:
    걷기 · 달리기 · 앉아서 꼬리 흔들기 · 그루밍(세수) ·
    기지개(스트레칭) · 잠자기(Zzz) · 깜짝 점프 후 도망

실행:
    Windows :  pythonw idle_cat.py
    macOS   :  python3 idle_cat.py
    공통    :  python idle_cat.py 30      (유휴 기준 30초로 지정)

조작:
    고양이 좌클릭  → 깜짝 놀라 점프한 뒤 화면 밖으로 도망
    고양이 우클릭  → 프로그램 종료
"""

import sys
import re
import time
import random
import ctypes
import subprocess
import tkinter as tk

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

# ─────────────────────────────── 설정 ───────────────────────────────
IDLE_SECONDS  = 60        # 이 시간 동안 입력이 없으면 고양이 등장
SCALE         = 5         # 픽셀 확대 배율
BASE_SPEED    = 4         # 걷기 속도 (px / tick)
GROUND_MARGIN = 60        # 화면 맨 아래에서 띄울 높이
CHECK_MS      = 500       # 숨어있을 때 유휴 확인 주기 (ms)
CREDIT_TEXT   = "presented by g.ad.c 2026"
TRANSPARENT   = "#FF00FF"

if len(sys.argv) > 1:
    try:
        IDLE_SECONDS = max(3, int(sys.argv[1]))
    except ValueError:
        pass

# ─────────────────────────── 픽셀 스프라이트 ───────────────────────────
PALETTE = {
    "#": "#E8926F",  # 몸통 (클로드 오렌지)
    "d": "#8C4A32",  # 진한 무늬/꼬리 끝
    "e": "#2B1B12",  # 눈
    "c": "#FBE7D2",  # 가슴 크림색
    "p": "#F2A09A",  # 볼터치
    "n": "#C96A50",  # 코/입
    "m": "#8C4A32",  # 감은 눈
    "z": "#8A8A96",  # 잠자는 Zzz 표시
}

GRIDS = {
    "WALK1": [
        "........#....#..",
        "........##..##..",
        "........######..",
        "d.......#e##e#..",
        "dd......##n###p.",
        ".##############.",
        ".######cc######.",
        "..#####cc#####..",
        "..############..",
        "..############..",
        "..##..###..##...",
        "..##...##...##..",
    ],
    "WALK2": [
        "................",
        "........#....#..",
        "........##..##..",
        "........######..",
        ".dd.....#e##e#..",
        "..#######n###p..",
        "..#####cc#####..",
        "..#####cc#####..",
        "..############..",
        "..############..",
        "...###.###.###..",
        "...##..##...##..",
    ],
    "RUN1": [
        "................",
        "........#....#..",
        "........##..##..",
        "d.......######..",
        "dd......#e##e#..",
        ".########n###p..",
        ".######cc#####..",
        ".#####cc######..",
        ".#############..",
        "..############..",
        ".##....##....##.",
        "#......##......#",
    ],
    "RUN2": [
        "................",
        "................",
        "........#....#..",
        "........##..##..",
        ".dd.....######..",
        "..#######e##e#p.",
        "..######cc####..",
        "..####cc######..",
        "..############..",
        "...##########...",
        "....##.##.##....",
        "................",
    ],
    "SIT1": [
        "....#....#......",
        "....##..##......",
        "....######......",
        "....#e##e#..dd..",
        "....##n###p.#d..",
        "....######..#...",
        "...##cc####.#...",
        "...##cc######...",
        "...##########...",
        "...#########....",
        "...##.####.##...",
        "................",
    ],
    "SIT2": [
        "....#....#......",
        "....##..##......",
        "....######......",
        "....#e##e#......",
        "....##n###p.....",
        "....######.dd...",
        "...##cc####.#d..",
        "...##cc######...",
        "...##########...",
        "...#########....",
        "...##.####.##...",
        "................",
    ],
    "GROOM1": [
        "....#....#......",
        "....##..##......",
        "....######......",
        "....#e##e#..dd..",
        "....##n###..#d..",
        "...#######..#...",
        "...#.cc####.#...",
        "..##.cc######...",
        "..#.#########...",
        "....#########...",
        "....#.####.##...",
        "................",
    ],
    "GROOM2": [
        "................",
        "....#....#......",
        "....##..##......",
        "....######..dd..",
        "...##e##e#..#d..",
        "..#.##n###..#...",
        "..#..cc####.#...",
        "..##.cc######...",
        "...##########...",
        "....#########...",
        "....#.####.##...",
        "................",
    ],
    "SLEEP1": [
        "..........z.....",
        "................",
        "................",
        ".....#...#......",
        ".....##.##......",
        "....#######.....",
        "...#md##md#.....",
        "..#############.",
        "..####cc######d.",
        "..############d.",
        "...###########..",
        "................",
    ],
    "SLEEP2": [
        "................",
        "...........z....",
        ".........z......",
        ".....#...#......",
        ".....##.##......",
        "....#######.....",
        "...#md##md#.....",
        "..#############.",
        "..####cc######d.",
        "..############d.",
        "...###########..",
        "................",
    ],
    "STRETCH1": [
        "................",
        "..........dd....",
        "...........#d...",
        "..........##....",
        ".........###....",
        ".......#####....",
        "..#...######....",
        ".############...",
        "#e##########....",
        "#n#####..##.....",
        "###..##...##....",
        ".....##....##...",
    ],
    "STRETCH2": [
        "................",
        "..........dd....",
        "..........#d....",
        "..........##....",
        ".........###....",
        ".......#####....",
        "..#..#######....",
        ".############...",
        "#e#########.....",
        "#n####..##......",
        "###...##..##....",
        "......##...##...",
    ],
    "JUMP": [
        "........#....#..",
        "........##..##..",
        "d.......######..",
        "d.......#e##e#..",
        ".#########n##p..",
        ".######cc#####..",
        ".#####cc######..",
        ".#############..",
        "..###########...",
        "..##..####..##..",
        ".##....##....##.",
        "................",
    ],
}

# 상태별 애니메이션 정의: 프레임 / 프레임 간격 / 이동속도 배율
STATE_DEF = {
    "walk":    dict(frames=["WALK1", "WALK2"],       tick=130, speed=1.0),
    "run":     dict(frames=["RUN1", "RUN2"],         tick=85,  speed=2.6),
    "sit":     dict(frames=["SIT1", "SIT2"],         tick=430, speed=0),
    "groom":   dict(frames=["GROOM1", "GROOM2"],     tick=300, speed=0),
    "sleep":   dict(frames=["SLEEP1", "SLEEP2"],     tick=650, speed=0),
    "stretch": dict(frames=["STRETCH1", "STRETCH2"], tick=350, speed=0),
    "jump":    dict(frames=["JUMP"],                 tick=100, speed=0),
    "flee":    dict(frames=["RUN1", "RUN2"],         tick=60,  speed=4.5),
}

# 걷다가 다른 행동으로 넘어갈 확률(틱당)과 지속시간 범위(초)
IDLE_ACTIONS = [
    # (상태, 가중치, 최소지속, 최대지속)
    ("sit",     30, 3.0,  7.0),
    ("groom",   20, 3.0,  6.0),
    ("stretch", 15, 1.5,  3.0),
    ("sleep",   15, 8.0, 18.0),
    ("run",     20, 1.5,  3.5),
]
ACTION_CHANCE = 0.015   # 걷는 중 매 틱마다 행동 전환 확률


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


# ─────────────────────────────── 본체 ───────────────────────────────
class IdleCat:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        if IS_WIN:
            self.bg = TRANSPARENT
            self.root.attributes("-transparentcolor", TRANSPARENT)
        elif IS_MAC:
            self.bg = "systemTransparent"
            try:
                self.root.attributes("-transparent", True)
            except tk.TclError:
                self.bg = "#1E1E1E"
        else:
            self.bg = "#1E1E1E"
        self.root.config(bg=self.bg)

        # 모든 상태의 좌/우 스프라이트 미리 생성
        self.sprites = {}
        for name, grid in GRIDS.items():
            self.sprites[(name, +1)] = build_sprite(grid, SCALE)
            self.sprites[(name, -1)] = build_sprite(grid, SCALE, flip=True)

        any_img = self.sprites[("WALK1", 1)]
        self.w, self.h = any_img.width(), any_img.height()

        self.label = tk.Label(self.root, bg=self.bg, bd=0)
        self.label.pack()
        self.credit = tk.Label(self.root, text=CREDIT_TEXT, bg=self.bg,
                               fg="#9A9A9A", font=("Consolas", 8), bd=0)
        self.credit.pack()

        for widget in (self.label, self.credit):
            widget.bind("<Button-1>", self.startle)
            widget.bind("<Button-3>", lambda e: self.root.destroy())
            widget.bind("<Button-2>", lambda e: self.root.destroy())

        self.root.update_idletasks()
        self.total_h = self.root.winfo_reqheight()
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.ground_y = self.screen_h - self.total_h - GROUND_MARGIN

        self.visible = False
        self.x = 0.0
        self.y = self.ground_y
        self.direction = 1
        self.frame_i = 0
        self.state = "walk"
        self.state_until = 0.0     # 현재 행동이 끝나는 시각
        self.jump_step = 0

        self.root.withdraw()
        self.root.after(CHECK_MS, self.watch_idle)
        self.root.mainloop()

    # ── 등장/퇴장 ──────────────────────────────────────────
    def watch_idle(self):
        if not self.visible and idle_seconds() >= IDLE_SECONDS:
            self.appear()
        self.root.after(CHECK_MS, self.watch_idle)

    def appear(self):
        self.visible = True
        self.direction = random.choice([-1, 1])
        self.x = -self.w if self.direction == 1 else self.screen_w
        self.y = self.ground_y
        self.set_state("walk")
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.step()

    def hide(self):
        self.visible = False
        self.root.withdraw()

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

    def startle(self, _event=None):
        """좌클릭: 점프 후 가까운 화면 가장자리로 도망"""
        if self.state in ("jump", "flee"):
            return
        self.jump_step = 0
        # 가까운 쪽 가장자리 방향으로
        self.direction = -1 if self.x < self.screen_w / 2 else 1
        self.set_state("jump")

    # ── 메인 루프 ──────────────────────────────────────────
    def step(self):
        if not self.visible:
            return
        # 사용자가 돌아오면 퇴장 (도망 중이 아닐 때)
        if self.state not in ("jump", "flee") and idle_seconds() < 1.0:
            self.hide()
            return

        now = time.monotonic()
        conf = STATE_DEF[self.state]

        # 상태별 로직
        if self.state == "walk":
            if random.random() < ACTION_CHANCE:
                self.pick_random_action()
                conf = STATE_DEF[self.state]

        elif self.state == "jump":
            # 짧게 위로 튀었다가 착지 → 도망
            hop = [-18, -28, -18, 0]
            self.y = self.ground_y + hop[min(self.jump_step, 3)]
            self.jump_step += 1
            if self.jump_step > 3:
                self.y = self.ground_y
                self.set_state("flee")
                conf = STATE_DEF["flee"]

        elif self.state_until and now >= self.state_until:
            # 행동 종료: 잠에서 깨면 기지개부터
            if self.state == "sleep":
                self.set_state("stretch", 2.0)
            else:
                self.set_state("walk")
            conf = STATE_DEF[self.state]

        # 이동
        speed = BASE_SPEED * conf["speed"]
        if speed:
            self.x += speed * self.direction
            if self.state == "flee":
                # 화면 밖으로 완전히 나가면 숨김
                if self.x < -self.w or self.x > self.screen_w:
                    self.hide()
                    return
            else:
                if self.x <= 0:
                    self.x, self.direction = 0, 1
                elif self.x >= self.screen_w - self.w:
                    self.x, self.direction = self.screen_w - self.w, -1

        # 프레임 갱신
        frames = conf["frames"]
        self.frame_i = (self.frame_i + 1) % len(frames)
        img = self.sprites[(frames[self.frame_i], self.direction)]
        self.label.config(image=img)
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
        self.root.after(conf["tick"], self.step)


if __name__ == "__main__":
    if not (IS_WIN or IS_MAC):
        print("이 스크립트는 Windows 또는 macOS에서 실행해야 합니다.")
        sys.exit(1)
    IdleCat()
