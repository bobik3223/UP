"""
Desktop Tamagotchi
Requirements: pip install pystray pillow plyer
Usage:        python tamagotchi.py
"""

import tkinter as tk
import threading
import time
import random
import sys

try:
    from PIL import Image, ImageDraw
    import pystray
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

try:
    from plyer import notification
    HAS_NOTIFY = True
except ImportError:
    HAS_NOTIFY = False


# ═══════════════════════════════════════
# PET MODEL
# Holds all state for the virtual pet and exposes
# mutation methods used by the UI and game loop.
# ═══════════════════════════════════════

class Pet:
    def __init__(self):
        self.name     = "Buddy"
        self.hunger   = 80   # 0–100; lower = hungrier
        self.happy    = 80   # 0–100; lower = sadder
        self.energy   = 80   # 0–100; lower = more tired
        self.age      = 0    # incremented every game tick while awake
        self.alive    = True
        self.sleeping = False
        self.last_notified: dict[str, float] = {}

    @property
    def status(self) -> str:
        """Returns the highest-priority status string for the current state."""
        if not self.alive:   return "dead"
        if self.sleeping:    return "sleep"
        if self.hunger < 20: return "hungry"
        if self.happy  < 20: return "sad"
        if self.energy < 20: return "tired"
        if self.hunger > 70 and self.happy > 70 and self.energy > 70:
            return "happy"
        return "normal"

    def tick(self) -> None:
        """
        Advances the simulation by one step.
        Called every 30 seconds by the game loop.
        Sleeping pets recover energy but still lose hunger slowly.
        """
        if not self.alive:
            return
        if self.sleeping:
            self.energy = min(100, self.energy + 10)
            self.hunger = max(0,   self.hunger  -  3)
            return
        self.hunger = max(0, self.hunger - 4)
        self.happy  = max(0, self.happy  - 2)
        self.energy = max(0, self.energy - 3)
        self.age   += 1
        # Pet dies if both hunger and energy are fully depleted
        if self.hunger == 0 and self.energy == 0:
            self.alive = False

    def feed(self) -> None:
        """Restores hunger and slightly boosts happiness."""
        self.hunger = min(100, self.hunger + 30)
        self.happy  = min(100, self.happy  +  5)

    def play(self) -> bool:
        """
        Boosts happiness at the cost of energy and hunger.
        Returns False if the pet is too tired to play.
        """
        if self.energy < 10:
            return False
        self.happy  = min(100, self.happy  + 25)
        self.energy = max(0,   self.energy - 15)
        self.hunger = max(0,   self.hunger - 10)
        return True

    def sleep(self) -> bool:
        """Toggles sleep mode. Returns the new sleeping state."""
        self.sleeping = not self.sleeping
        return self.sleeping

    def should_notify(self, kind: str, interval: int = 90) -> bool:
        """
        Rate-limits notifications of a given kind.
        Returns True at most once per `interval` seconds.
        """
        now = time.time()
        if now - self.last_notified.get(kind, 0) > interval:
            self.last_notified[kind] = now
            return True
        return False


# ═══════════════════════════════════════
# ANIMATION FRAMES
# Four-frame ASCII sprite cycle per status.
# ═══════════════════════════════════════
FRAMES: dict[str, list[str]] = {
    "happy":  ["(^-^) *", "(^-^)~ ", "(^-^) *", "~(^-^) "],
    "normal": ["(o_o)  ", "(o_o)~ ", "(o_o)  ", "(o_o). "],
    "hungry": ["(>_<)  ", "(>_<)~ ", "(>_<)  ", "~(>_<) "],
    "sad":    ["(T_T)  ", "(T-T) ",  "(T_T)  ", ".(T_T) "],
    "tired":  ["(-_-). ", "(-_-)  ", "(-_-)z ", "(-_-)  "],
    "sleep":  ["(-.-)z ", "(-.-)Z ", "(-.-)z ", "(-.-). "],
    "dead":   ["(x_x)  ", "(x_x). ", "(x_x)  ", "(x_x). "],
}

# ── Status accent colours (used for bar fills and tray icon) ──
COLORS: dict[str, str] = {
    "happy":  "#ffe066",
    "normal": "#b5ead7",
    "hungry": "#ffb347",
    "sad":    "#aecde8",
    "tired":  "#d5b4f0",
    "sleep":  "#c8e6f7",
    "dead":   "#cccccc",
}

# ── Background tints for the pet display area ──
BG_COLORS: dict[str, str] = {
    "happy":  "#fff9d6",
    "normal": "#f0fff8",
    "hungry": "#fff3e0",
    "sad":    "#eaf4fb",
    "tired":  "#f3ecfb",
    "sleep":  "#e8f4fd",
    "dead":   "#f5f5f5",
}

# ── Human-readable status labels ──
STATUS_TEXT: dict[str, str] = {
    "happy":  "Happy!",
    "normal": "All good~",
    "hungry": "Hungry...",
    "sad":    "Feeling sad...",
    "tired":  "Tired...",
    "sleep":  "Zzz... sleeping...",
    "dead":   "Pet has passed away.",
}


# ═══════════════════════════════════════
# APPLICATION
# ═══════════════════════════════════════

class TamagotchiApp:
    def __init__(self):
        self.pet       = Pet()
        self.frame_idx = 0
        self.tray_icon = None

        self.root = tk.Tk()
        self.root.title("Tamagotchi")
        self.root.resizable(False, False)
        self.root.geometry("220x420+60+60")
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self._build_ui()
        self._start_tray()
        self._animation_loop()
        self._game_loop()

    # ─── UI Construction ──────────────────────────────────────────────────
    def _build_ui(self) -> None:
        self.root.configure(bg="#fef6ff")

        # Header bar
        header = tk.Frame(self.root, bg="#e8d5f5", pady=4)
        header.pack(fill="x")
        tk.Label(
            header,
            text=self.pet.name,
            bg="#e8d5f5", fg="#7a4fa3",
            font=("Segoe UI", 11, "bold"),
        ).pack()

        # Pet sprite display area
        self.pet_frame = tk.Frame(self.root, bg="#f0fff8", width=200, height=110)
        self.pet_frame.pack(pady=6, padx=10, fill="x")
        self.pet_frame.pack_propagate(False)

        self.sprite_label = tk.Label(
            self.pet_frame,
            text="",
            bg="#f0fff8",
            fg="#4a4a4a",
            font=("Courier New", 20, "bold"),
            justify="center",
        )
        self.sprite_label.place(relx=0.5, rely=0.5, anchor="center")

        self.status_label = tk.Label(
            self.root, text="",
            font=("Segoe UI", 9), bg="#fef6ff", fg="#888",
        )
        self.status_label.pack()

        # Stat bars (hunger, happiness, energy)
        bars_frame = tk.Frame(self.root, bg="#fef6ff", padx=12)
        bars_frame.pack(fill="x", pady=4)
        self.bars: dict[str, tuple[tk.Canvas, str]] = {}

        for attr, label, color in [
            ("hunger", "Hunger", "#ff8c69"),
            ("happy",  "Happy",  "#ffd166"),
            ("energy", "Energy", "#06d6a0"),
        ]:
            row = tk.Frame(bars_frame, bg="#fef6ff")
            row.pack(fill="x", pady=2)
            tk.Label(
                row, text=label, bg="#fef6ff",
                font=("Segoe UI", 8), width=6, anchor="w",
            ).pack(side="left")
            canvas = tk.Canvas(
                row, width=140, height=12,
                bg="#ece8f0", bd=0, highlightthickness=0,
            )
            canvas.pack(side="left", padx=(4, 0))
            self.bars[attr] = (canvas, color)

        # Action buttons
        btn_frame = tk.Frame(self.root, bg="#fef6ff", pady=6)
        btn_frame.pack()
        btn_style = dict(
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2",
            padx=8, pady=5, bd=0,
        )

        self.feed_btn = tk.Button(
            btn_frame, text="Feed",
            bg="#ffb347", fg="white",
            command=self.action_feed,
            activebackground="#ff9020",
            **btn_style,
        )
        self.feed_btn.grid(row=0, column=0, padx=4, pady=3)

        self.play_btn = tk.Button(
            btn_frame, text="Play",
            bg="#70d0b0", fg="white",
            command=self.action_play,
            activebackground="#40b890",
            **btn_style,
        )
        self.play_btn.grid(row=0, column=1, padx=4, pady=3)

        self.sleep_btn = tk.Button(
            btn_frame, text="Sleep",
            bg="#9b8ec4", fg="white",
            command=self.action_sleep,
            activebackground="#7a6ea4",
            **btn_style,
        )
        self.sleep_btn.grid(row=1, column=0, padx=4, pady=3)

        self.hide_btn = tk.Button(
            btn_frame, text="Hide to Tray",
            bg="#b0b0b0", fg="white",
            command=self.hide_to_tray,
            activebackground="#909090",
            **btn_style,
        )
        self.hide_btn.grid(row=1, column=1, padx=4, pady=3)

        self.age_label = tk.Label(
            self.root, text="",
            font=("Segoe UI", 8), bg="#fef6ff", fg="#aaa",
        )
        self.age_label.pack(pady=(0, 4))

    # ─── UI Update ────────────────────────────────────────────────────────
    def _update_ui(self) -> None:
        """Redraws all dynamic UI elements from the current pet state."""
        if not self.root.winfo_exists():
            return

        status = self.pet.status
        self.frame_idx = (self.frame_idx + 1) % 4
        sprite = FRAMES[status][self.frame_idx]
        bg     = BG_COLORS[status]

        self.pet_frame.configure(bg=bg)
        self.sprite_label.configure(text=sprite, bg=bg)
        self.status_label.configure(text=STATUS_TEXT[status])

        # Redraw stat bars
        for attr, (canvas, color) in self.bars.items():
            canvas.delete("all")
            fill_width = int(140 * getattr(self.pet, attr) / 100)
            if fill_width > 0:
                canvas.create_rectangle(0, 0, fill_width, 12,
                                        fill=color, outline="")

        self.age_label.configure(text=f"Age: {self.pet.age} h.")
        self.sleep_btn.configure(
            text="Wake up" if self.pet.sleeping else "Sleep"
        )

        # Disable action buttons when the pet is dead
        state = "disabled" if not self.pet.alive else "normal"
        for btn in (self.feed_btn, self.play_btn, self.sleep_btn):
            btn.configure(state=state)

    # ─── Button Actions ───────────────────────────────────────────────────
    def action_feed(self) -> None:
        self.pet.feed()
        self._update_ui()

    def action_play(self) -> None:
        if not self.pet.play():
            self.status_label.configure(text="Too tired to play!")
        self._update_ui()

    def action_sleep(self) -> None:
        self.pet.sleep()
        self._update_ui()

    # ─── System Tray ──────────────────────────────────────────────────────
    def _make_tray_image(self, color: str = "#b5ead7") -> "Image.Image":
        """Generates a simple smiley-face icon for the system tray."""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d   = ImageDraw.Draw(img)
        d.ellipse([4, 4, 60, 60],   fill=color)
        d.ellipse([18, 22, 28, 32], fill="#333")   # left eye
        d.ellipse([36, 22, 46, 32], fill="#333")   # right eye
        d.arc([18, 34, 46, 50], start=0, end=180, fill="#333", width=3)  # mouth
        return img

    def _start_tray(self) -> None:
        """Initialises the pystray icon and starts it in a daemon thread."""
        if not HAS_TRAY:
            return
        try:
            menu = pystray.Menu(
                pystray.MenuItem("Open",  self._show_window, default=True),
                pystray.MenuItem("Feed",  lambda i, it: self._tray_action("feed")),
                pystray.MenuItem("Play",  lambda i, it: self._tray_action("play")),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit",  self._quit),
            )
            self.tray_icon = pystray.Icon(
                "tamagotchi",
                self._make_tray_image(),
                "Tamagotchi",
                menu,
            )
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"Tray unavailable: {e}")

    def _tray_action(self, action: str) -> None:
        """Executes a pet action triggered from the tray context menu."""
        if action == "feed":
            self.pet.feed()
        elif action == "play":
            self.pet.play()
        self.root.after(0, self._update_ui)
        self.root.after(0, self._show_window)

    def hide_to_tray(self) -> None:
        """Hides the main window without closing the application."""
        self.root.withdraw()

    def _show_window(self, *_) -> None:
        """Restores the main window from tray."""
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def _quit(self, *_) -> None:
        """Stops the tray icon and destroys the Tk window."""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    # ─── Loops ────────────────────────────────────────────────────────────
    def _animation_loop(self) -> None:
        """Redraws the sprite every 600 ms to animate the pet."""
        if self.root.winfo_exists():
            self._update_ui()
            self.root.after(600, self._animation_loop)

    def _game_loop(self) -> None:
        """Advances the game simulation every 30 seconds."""
        if self.root.winfo_exists():
            self.pet.tick()
            self._check_notifications()
            self.root.after(30_000, self._game_loop)

    # ─── Notifications ────────────────────────────────────────────────────
    def _check_notifications(self) -> None:
        """
        Evaluates the pet's current state and triggers OS notifications
        or fallback popups when critical thresholds are crossed.
        """
        p = self.pet
        if not p.alive:
            self._notify("Pet has died", f"{p.name} is gone...", "dead")
            return
        if p.hunger < 20 and p.should_notify("hungry"):
            self._notify("Hungry!", f"{p.name} is very hungry!", "hungry")
        elif p.happy < 20 and p.should_notify("sad"):
            self._notify("Bored", f"Play with {p.name}!", "sad")
        elif p.energy < 15 and not p.sleeping and p.should_notify("tired"):
            self._notify("Tired", f"{p.name} needs to sleep!", "tired")

    def _notify(self, title: str, msg: str, kind: str) -> None:
        """
        Sends a notification through the best available channel:
        1. OS notification via plyer
        2. Fallback Tk popup
        Updates the tray icon colour to reflect the alert.
        """
        if HAS_TRAY and self.tray_icon:
            try:
                self.tray_icon.icon = self._make_tray_image(COLORS.get(kind, "#b5ead7"))
            except Exception:
                pass

        if HAS_NOTIFY:
            try:
                notification.notify(
                    title=title, message=msg,
                    app_name="Tamagotchi", timeout=5,
                )
                return
            except Exception:
                pass

        # Fallback: small always-on-top Tk popup
        self.root.after(0, lambda: self._popup(title, msg))

    def _popup(self, title: str, msg: str) -> None:
        """Creates a small auto-dismissing notification popup."""
        if not self.root.winfo_exists():
            return
        win = tk.Toplevel(self.root)
        win.title("")
        win.attributes("-topmost", True)
        win.resizable(False, False)
        win.geometry("240x90+80+400")
        win.configure(bg="#fff3e0")
        tk.Label(
            win, text=title,
            font=("Segoe UI", 10, "bold"),
            bg="#fff3e0", fg="#cc6600",
        ).pack(pady=(10, 2))
        tk.Label(
            win, text=msg,
            font=("Segoe UI", 9),
            bg="#fff3e0", fg="#555",
            wraplength=220,
        ).pack()
        win.after(4000, win.destroy)

    # ─── Entry Point ──────────────────────────────────────────────────────
    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    TamagotchiApp().run()