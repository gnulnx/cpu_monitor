#!/usr/bin/env python3
import tkinter as tk
import psutil

# --- Config ----------------------------------------------------
BAR_WIDTH = 16          # width of each bar in pixels
BAR_SPACING = 4         # space between bars
BAR_HEIGHT = 120        # max bar height (like the OSX mini graph)
UPDATE_MS = 1000         # refresh interval in ms
BG_COLOR = "#111111"
BAR_BG_COLOR = "#222222"
BAR_FG_COLOR = "#804aff"
TEXT_COLOR = "#dddddd"
# ---------------------------------------------------------------


def main():
    # Number of logical CPUs (threads)
    cpu_count = psutil.cpu_count(logical=True)

    # Compute canvas size based on CPU count
    canvas_width = cpu_count * (BAR_WIDTH + BAR_SPACING) + BAR_SPACING
    canvas_height = BAR_HEIGHT + 40  # extra for labels

    root = tk.Tk()
    root.title("CPU Threads Monitor")

    # Make the window small and tight like the OSX one
    root.resizable(False, False)
    root.configure(bg=BG_COLOR)

    canvas = tk.Canvas(
        root,
        width=canvas_width,
        height=canvas_height,
        highlightthickness=0,
        bg=BG_COLOR,
    )
    canvas.pack()

    # Label at the top for overall CPU usage
    overall_label = tk.Label(
        root, text="", fg=TEXT_COLOR, bg=BG_COLOR, font=("Menlo", 10)
    )
    overall_label.place(x=8, y=2)

    # Create bar rectangles
    bars = []
    top_y = 20
    bottom_y = top_y + BAR_HEIGHT

    for i in range(cpu_count):
        x0 = BAR_SPACING + i * (BAR_WIDTH + BAR_SPACING)
        x1 = x0 + BAR_WIDTH

        # Background “slot”
        canvas.create_rectangle(
            x0,
            top_y,
            x1,
            bottom_y,
            outline="#333333",
            fill=BAR_BG_COLOR,
        )

        # Foreground actual usage bar (initially empty)
        fg = canvas.create_rectangle(
            x0 + 2,
            bottom_y - 1,
            x1 - 2,
            bottom_y - 1,
            outline="",
            fill=BAR_FG_COLOR,
        )
        bars.append(fg)

    # Prime psutil so the first read isn't bogus
    psutil.cpu_percent(interval=None, percpu=True)

    def update():
        # Per-CPU usage (logical threads)
        per_cpu = psutil.cpu_percent(interval=0.0, percpu=True)
        overall = psutil.cpu_percent(interval=0.0)

        overall_label.config(text=f"CPU: {overall:5.1f}%   Cores: {cpu_count}")

        for i, percent in enumerate(per_cpu):
            percent = max(0.0, min(100.0, percent))  # clamp
            height = (percent / 100.0) * BAR_HEIGHT
            x0 = BAR_SPACING + i * (BAR_WIDTH + BAR_SPACING) + 2
            x1 = x0 + BAR_WIDTH - 4
            y1 = bottom_y - 2
            y0 = y1 - height

            # Move the foreground bar to represent new height
            canvas.coords(bars[i], x0, y0, x1, y1)

        root.after(UPDATE_MS, update)

    update()
    root.mainloop()


if __name__ == "__main__":
    main()

