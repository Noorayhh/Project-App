import tkinter as tk
from tkinter import messagebox
import json
import hashlib
import os

# ---------------- Config ----------------
DATA_FILE = "pattern_data.json"
MAX_ATTEMPTS = 5
GRID_SIZE = 3
DOT_RADIUS = 20
DOT_PADDING = 62
CANVAS_SIZE = DOT_PADDING*2 + (GRID_SIZE-1)*100 + 2*DOT_RADIUS

# ---------------- Helpers ----------------
def load_pattern_hash():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                return data.get("pattern_hash")
        except:
            return None
    return None

def save_pattern_hash(hash_str):
    with open(DATA_FILE, "w") as f:
        json.dump({"pattern_hash": hash_str}, f)

def hash_pattern(seq):
    return hashlib.sha256("-".join(map(str, seq)).encode()).hexdigest()

# ---------------- Main App ----------------
class PatternLockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Neon Pattern Lock")
        self.root.configure(bg="#111")

        # Canvas
        self.canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="#111", highlightthickness=0)
        self.canvas.pack(pady=20)

        # Dots, lines, state
        self.dots = []
        self.lines = []
        self.temp_line = None
        self.pattern = []
        self.enrolling = False
        self.attempts_left = MAX_ATTEMPTS
        self.pattern_hash = load_pattern_hash()
        self.draw_grid()

        # Bind events
        self.canvas.bind("<ButtonPress-1>", self.start_pattern)
        self.canvas.bind("<B1-Motion>", self.track_pattern)
        self.canvas.bind("<ButtonRelease-1>", self.end_pattern)

        # Buttons
        btn_frame = tk.Frame(root, bg="#111")
        btn_frame.pack(pady=10)
        self.enroll_btn = tk.Button(btn_frame, text="Enroll", command=self.enroll_pattern,
                                    bg="#FF4500", fg="white", font=("Arial",10,"bold"), width=10)
        self.enroll_btn.pack(side="left", padx=5)
        self.reset_btn = tk.Button(btn_frame, text="Reset", command=self.reset_pattern_data,
                                   bg="#FF6347", fg="white", font=("Arial",10,"bold"), width=10)
        self.reset_btn.pack(side="left", padx=5)

        # Hover effects
        for btn, color in [(self.enroll_btn, "#FF6347"), (self.reset_btn, "#FF7F50")]:
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=btn.cget("bg"): b.config(bg=c))

    # -------- Draw Grid --------
    def draw_grid(self):
        self.dots.clear()
        spacing = (CANVAS_SIZE - 2*DOT_PADDING)//(GRID_SIZE-1)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                x = DOT_PADDING + j*spacing
                y = DOT_PADDING + i*spacing
                dot = self.canvas.create_oval(x-DOT_RADIUS, y-DOT_RADIUS, x+DOT_RADIUS, y+DOT_RADIUS,
                                              fill="#222", outline="#FF4500", width=2)
                self.dots.append({"id": dot, "x": x, "y": y, "index": i*GRID_SIZE+j})

    # -------- Enrollment --------
    def enroll_pattern(self):
        self.enrolling = True
        messagebox.showinfo("Enroll Mode", "Draw your new pattern to enroll.")

    # -------- Reset --------
    def reset_pattern_data(self):
        self.pattern_hash = None
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        self.attempts_left = MAX_ATTEMPTS
        messagebox.showinfo("Reset", "Pattern data cleared. Please enroll a new pattern.")

    # -------- Start Drawing --------
    def start_pattern(self, event):
        if self.pattern_hash is None and not self.enrolling:
            messagebox.showwarning("Enroll First", "Please enroll a pattern first!")
            return

        self.pattern = []
        if self.temp_line:
            self.canvas.delete(self.temp_line)
            self.temp_line = None
        for line in self.lines:
            self.canvas.delete(line)
        self.lines.clear()
        self.reset_dot_colors()

    # -------- Track Pattern --------
    def track_pattern(self, event):
        if self.pattern_hash is None and not self.enrolling:
            return

        idx = self.check_hit(event.x, event.y)
        last_pos = (self.dots[self.pattern[-1]]["x"], self.dots[self.pattern[-1]]["y"]) if self.pattern else None

        # Draw temporary line
        if last_pos:
            if self.temp_line:
                self.canvas.delete(self.temp_line)
            self.temp_line = self.canvas.create_line(last_pos[0], last_pos[1], event.x, event.y,
                                                     fill="#FF4500", width=4, capstyle=tk.ROUND)

        # Add dot to pattern
        if idx is not None and (len(self.pattern) == 0 or self.pattern[-1] != idx):
            if self.temp_line:
                self.canvas.delete(self.temp_line)
                self.temp_line = None
            if last_pos:
                self.draw_gradient_line(last_pos, (self.dots[idx]["x"], self.dots[idx]["y"]))
            self.dot_pop(idx)
            self.pattern.append(idx)

    # -------- Draw Gradient Line --------
    def draw_gradient_line(self, start, end):
        x1, y1 = start
        x2, y2 = end
        steps = 10
        for i in range(steps):
            ratio = i / steps
            r = 255
            g = int(0 + (165-0)*ratio)
            b = 0
            color = f"#{r:02X}{g:02X}{b:02X}"
            xi = x1 + (x2-x1)*(i/steps)
            yi = y1 + (y2-y1)*(i/steps)
            xj = x1 + (x2-x1)*((i+1)/steps)
            yj = y1 + (y2-y1)*((i+1)/steps)
            line = self.canvas.create_line(xi, yi, xj, yj, width=4, fill=color, capstyle=tk.ROUND)
            self.lines.append(line)
        self.root.update()

    # -------- Dot Animation --------
    def dot_pop(self, idx):
        dot = self.dots[idx]
        self.canvas.itemconfig(dot["id"], fill="#FFA500")
        self.canvas.scale(dot["id"], dot["x"], dot["y"], 1.15, 1.15)
        self.root.update()
        self.root.after(100, lambda d=dot: self.canvas.scale(d["id"], d["x"], d["y"], 0.87, 0.87))

    # -------- End Pattern --------
    def end_pattern(self, event):
        if self.temp_line:
            self.canvas.delete(self.temp_line)
            self.temp_line = None
        if not self.pattern:
            return

        if self.enrolling:
            pattern_hash_now = hash_pattern(self.pattern)
            save_pattern_hash(pattern_hash_now)
            self.pattern_hash = pattern_hash_now
            self.enrolling = False
            messagebox.showinfo("Success", "✅ Pattern enrolled successfully!")
        else:
            if self.pattern_hash is None:
                messagebox.showwarning("Enroll First", "Please enroll a pattern first!")
            else:
                pattern_hash_now = hash_pattern(self.pattern)
                if pattern_hash_now == self.pattern_hash:
                    messagebox.showinfo("Unlocked", "✅ Access granted")
                    self.attempts_left = MAX_ATTEMPTS
                else:
                    self.attempts_left -= 1
                    messagebox.showerror("Incorrect", f"Wrong pattern! {self.attempts_left} tries left")
                    if self.attempts_left <= 0:
                        messagebox.showerror("Locked", "❌ Max attempts reached. Reset to try again")

        # Clear lines
        for line in self.lines:
            self.canvas.delete(line)
        self.lines.clear()
        self.reset_dot_colors()

    # -------- Reset Dot Colors --------
    def reset_dot_colors(self):
        for dot in self.dots:
            self.canvas.itemconfig(dot["id"], fill="#222")

    # -------- Check Hit --------
    def check_hit(self, x, y):
        for dot in self.dots:
            dx = x - dot["x"]
            dy = y - dot["y"]
            if dx*dx + dy*dy <= DOT_RADIUS*DOT_RADIUS:
                return dot["index"]
        return None

# ---------------- Run App ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = PatternLockApp(root)
    root.mainloop()
