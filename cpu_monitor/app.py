#!/usr/bin/env python3
import argparse
import math
import tkinter as tk

import psutil

# ----------------------------- CONFIG ---------------------------------
UPDATE_MS = 500   # refresh interval

BG_COLOR = "#111111"
TEXT_COLOR = "#DDDDDD"

# Bar mode
BAR_WIDTH = 16
BAR_SPACING = 4
BAR_HEIGHT = 120
BAR_BG_COLOR = "#222222"
BAR_FG_COLOR = "#4A6BFF"  # your purple/blue

# Heatmap mode
CELL_SIZE = 40
CELL_SPACING = 4

BUTTON_BG = "#222222"
BUTTON_BG_ACTIVE = "#4A6BFF"
BUTTON_FG = "#EEEEEE"
BUTTON_FONT = ("Menlo", 9)
# ----------------------------------------------------------------------


def cpu_color_black_red(percent: float) -> str:
    """
    Smooth Black → Red gradient.
    0%   -> #000000
    100% -> #FF0000
    """
    percent = max(0.0, min(100.0, percent))
    r = int((percent / 100.0) * 255)
    g = 0
    b = 0
    return f"#{r:02x}{g:02x}{b:02x}"


class CpuMonitorApp:
    def __init__(self, start_mode: str = "bars"):
        # Mode: 'bars' or 'heatmap'
        self.mode = start_mode  # initial mode
        # Heatmap view: 'threads' or 'cores'
        self.view = "threads"

        self.logical = psutil.cpu_count(logical=True)
        self.physical = psutil.cpu_count(logical=False) or self.logical

        # Tk root
        self.root = tk.Tk()
        self.root.title("CPU Monitor")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        # --- UI layout -------------------------------------------------
        self._build_controls()
        self._build_status_label()
        self.canvas = None  # will be built per mode
        self.bars = []
        self.heat_rects = []
        self.heat_count = 0
        self.heat_grid = 0

        # prime psutil so first call isn't bogus
        psutil.cpu_percent(interval=None, percpu=True)

        # build initial canvas
        self._build_canvas()

    # ------------------------- UI BUILDING -----------------------------

    def _build_controls(self):
        self.controls_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.controls_frame.pack(side="top", fill="x", padx=4, pady=4)

        # Mode row: Heatmap / Bars
        mode_label = tk.Label(
            self.controls_frame,
            text="Mode:",
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            font=("Menlo", 9),
        )
        mode_label.grid(row=0, column=0, sticky="w", padx=(2, 4))

        self.btn_mode_heatmap = tk.Button(
            self.controls_frame,
            text="Heatmap",
            command=self._on_mode_heatmap,
            font=BUTTON_FONT,
            fg=BUTTON_FG,
            bg=BUTTON_BG,
            activebackground=BUTTON_BG_ACTIVE,
            activeforeground=BUTTON_FG,
            relief="flat",
            bd=1,
            highlightthickness=0,
            padx=6,
            pady=2,
        )
        self.btn_mode_heatmap.grid(row=0, column=1, padx=2)

        self.btn_mode_bars = tk.Button(
            self.controls_frame,
            text="Bars",
            command=self._on_mode_bars,
            font=BUTTON_FONT,
            fg=BUTTON_FG,
            bg=BUTTON_BG,
            activebackground=BUTTON_BG_ACTIVE,
            activeforeground=BUTTON_FG,
            relief="flat",
            bd=1,
            highlightthickness=0,
            padx=6,
            pady=2,
        )
        self.btn_mode_bars.grid(row=0, column=2, padx=2)

        # View row: Threads / Cores
        view_label = tk.Label(
            self.controls_frame,
            text="View:",
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            font=("Menlo", 9),
        )
        view_label.grid(row=1, column=0, sticky="w", padx=(2, 4), pady=(4, 0))

        self.btn_view_threads = tk.Button(
            self.controls_frame,
            text="Threads",
            command=self._on_view_threads,
            font=BUTTON_FONT,
            fg=BUTTON_FG,
            bg=BUTTON_BG,
            activebackground=BUTTON_BG_ACTIVE,
            activeforeground=BUTTON_FG,
            relief="flat",
            bd=1,
            highlightthickness=0,
            padx=6,
            pady=2,
        )
        self.btn_view_threads.grid(row=1, column=1, padx=2, pady=(4, 0))

        self.btn_view_cores = tk.Button(
            self.controls_frame,
            text="Cores",
            command=self._on_view_cores,
            font=BUTTON_FONT,
            fg=BUTTON_FG,
            bg=BUTTON_BG,
            activebackground=BUTTON_BG_ACTIVE,
            activeforeground=BUTTON_FG,
            relief="flat",
            bd=1,
            highlightthickness=0,
            padx=6,
            pady=2,
        )
        self.btn_view_cores.grid(row=1, column=2, padx=2, pady=(4, 0))

        self._update_button_styles()

    def _build_status_label(self):
        self.status_label = tk.Label(
            self.root,
            text="",
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            font=("Menlo", 9),
        )
        self.status_label.pack(anchor="w", padx=8)

    def _build_canvas(self):
        # Destroy old canvas
        if self.canvas is not None:
            self.canvas.destroy()
            self.canvas = None
        self.bars = []
        self.heat_rects = []

        if self.mode == "bars":
            self._build_canvas_bars()
        else:
            self._build_canvas_heatmap()

    def _build_canvas_bars(self):
        # choose how many bars based on view
        cpu_count = self.logical if self.view == "threads" else self.physical

        canvas_width = cpu_count * (BAR_WIDTH + BAR_SPACING) + BAR_SPACING
        canvas_height = BAR_HEIGHT + 30

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            highlightthickness=0,
            bg=BG_COLOR,
        )
        self.canvas.pack(padx=4, pady=(2, 6))

        top_y = 10
        bottom_y = top_y + BAR_HEIGHT

        self.bars = []

        for i in range(cpu_count):
            x0 = BAR_SPACING + i * (BAR_WIDTH + BAR_SPACING)
            x1 = x0 + BAR_WIDTH

            # background slot
            self.canvas.create_rectangle(
                x0,
                top_y,
                x1,
                bottom_y,
                outline="#333333",
                fill=BAR_BG_COLOR,
            )

            fg = self.canvas.create_rectangle(
                x0 + 2,
                bottom_y - 1,
                x1 - 2,
                bottom_y - 1,
                outline="",
                fill=BAR_FG_COLOR,
            )

            self.bars.append((fg, top_y, bottom_y))


    def _build_canvas_heatmap(self):
        # Determine number of tiles based on view
        if self.view == "threads":
            count = self.logical
        else:
            count = self.physical

        grid = math.ceil(math.sqrt(count))
        total_cells = grid * grid

        width = grid * (CELL_SIZE + CELL_SPACING) + CELL_SPACING
        height = grid * (CELL_SIZE + CELL_SPACING) + CELL_SPACING + 10

        self.canvas = tk.Canvas(
            self.root,
            width=width,
            height=height,
            highlightthickness=0,
            bg=BG_COLOR,
        )
        self.canvas.pack(padx=4, pady=(2, 6))

        self.heat_count = count
        self.heat_grid = grid

        for i in range(total_cells):
            row = i // grid
            col = i % grid

            x0 = CELL_SPACING + col * (CELL_SIZE + CELL_SPACING)
            y0 = CELL_SPACING + row * (CELL_SIZE + CELL_SPACING)
            x1 = x0 + CELL_SIZE
            y1 = y0 + CELL_SIZE

            if i < count:
                fill = "#000000"
            else:
                fill = "#111111"

            rect = self.canvas.create_rectangle(
                x0, y0, x1, y1, outline="#222222", fill=fill
            )
            self.heat_rects.append(rect)

    # ------------------------- BUTTON HANDLERS -------------------------

    def _on_mode_heatmap(self):
        if self.mode != "heatmap":
            self.mode = "heatmap"
            self._update_button_styles()
            self._build_canvas()

    def _on_mode_bars(self):
        if self.mode != "bars":
            self.mode = "bars"
            self._update_button_styles()
            self._build_canvas()

    def _on_view_threads(self):
        if self.view != "threads":
            self.view = "threads"
            self._update_button_styles()
            self._build_canvas()   # always rebuild canvas

    def _on_view_cores(self):
        if self.view != "cores":
            self.view = "cores"
            self._update_button_styles()
            self._build_canvas()   # always rebuild canvas


    def _update_button_styles(self):
        # Mode buttons
        if self.mode == "heatmap":
            self.btn_mode_heatmap.configure(bg=BUTTON_BG_ACTIVE)
            self.btn_mode_bars.configure(bg=BUTTON_BG)
        else:
            self.btn_mode_heatmap.configure(bg=BUTTON_BG)
            self.btn_mode_bars.configure(bg=BUTTON_BG_ACTIVE)

        # View buttons (only meaningful in heatmap mode)
        if self.view == "threads":
            self.btn_view_threads.configure(bg=BUTTON_BG_ACTIVE)
            self.btn_view_cores.configure(bg=BUTTON_BG)
        else:
            self.btn_view_threads.configure(bg=BUTTON_BG)
            self.btn_view_cores.configure(bg=BUTTON_BG_ACTIVE)

    # --------------------------- CORE LOGIC ----------------------------

    def _compute_core_usages(self, per_cpu):
        """
        Aggregate thread usage into per-core usage using MAX(thread_i...).
        """
        logical = self.logical
        physical = self.physical or logical

        if logical >= physical and logical % physical == 0:
            threads_per_core = logical // physical
            core_vals = []
            for core in range(physical):
                vals = []
                for k in range(threads_per_core):
                    idx = core + k * physical
                    if idx < len(per_cpu):
                        vals.append(per_cpu[idx])
                if vals:
                    core_vals.append(max(vals))  # Option B: max intensity
            return core_vals
        else:
            # Fallback: first N threads
            return per_cpu[:physical]

    def _update_status(self, overall):
        self.status_label.config(
            text=(
                f"CPU: {overall:5.1f}%   "
                f"Cores: {self.physical}   Threads: {self.logical}"
            )
        )

    def update_loop(self):
        per_cpu = psutil.cpu_percent(interval=0.0, percpu=True)
        overall = psutil.cpu_percent(interval=0.0)

        self._update_status(overall)

        if self.mode == "bars":
            self._update_bars(per_cpu)
        else:
            self._update_heatmap(per_cpu)

        self.root.after(UPDATE_MS, self.update_loop)

    def _update_bars(self, per_cpu):
        for i, (rect, top_y, bottom_y) in enumerate(self.bars):
            if i >= len(per_cpu):
                continue
            if self.view == "threads":
                pct = per_cpu[i]
            else:
                core_vals = self._compute_core_usages(per_cpu)
                if i < len(core_vals):
                    pct = core_vals[i]
                else:
                    pct = 0
            height = (pct / 100.0) * BAR_HEIGHT

            x0, _, x1, _ = self.canvas.coords(rect)
            y1 = bottom_y - 2
            y0 = y1 - height
            self.canvas.coords(rect, x0, y0, x1, y1)

    def _update_heatmap(self, per_cpu):
        # Decide whether we show threads or cores
        if self.view == "threads":
            values = per_cpu[: self.logical]
        else:
            values = self._compute_core_usages(per_cpu)

        count = min(self.heat_count, len(values))

        for i in range(count):
            pct = values[i]
            color = cpu_color_black_red(pct)
            self.canvas.itemconfig(self.heat_rects[i], fill=color)

    # ----------------------------- RUN --------------------------------

    def run(self):
        self.root.after(UPDATE_MS, self.update_loop)
        self.root.mainloop()


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--heatmap",
        action="store_true",
        help="Start in heatmap mode instead of bar mode.",
    )
    args = parser.parse_args()

    start_mode = "heatmap" if args.heatmap else "bars"
    app = CpuMonitorApp(start_mode=start_mode)
    app.run()


if __name__ == "__main__":
    main()
