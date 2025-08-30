import tkinter as tk
from tkinter import ttk, messagebox
import random

# ------------- Utility: color helpers -------------
def color_array(n, highlights=None, default="gray"):
    """
    Build a color list for n bars.
    highlights: dict {index: "color"} to color specific bars.
    """
    colors = [default] * n
    if highlights:
        for idx, col in highlights.items():
            if 0 <= idx < n:
                colors[idx] = col
    return colors

# ------------- Sorting Algorithms as Generators -------------

def bubble_sort_gen(arr, draw, delay_ms, get_delay):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            # highlight the two being compared
            draw(arr, color_array(n, {j: "orange", j+1: "orange"}))
            yield
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                # highlight a swap
                draw(arr, color_array(n, {j: "red", j+1: "red"}))
                yield
        # mark last sorted element
        draw(arr, color_array(n, {n-1-i: "green"}))
        yield

def merge_sort_gen(arr, draw, delay_ms, get_delay):
    # Recursive merge sort with yields at each write
    n = len(arr)

    def merge(l, m, r):
        left = arr[l:m+1]
        right = arr[m+1:r+1]
        i = j = 0
        k = l
        # visualize the working range
        while i < len(left) and j < len(right):
            # highlight current write position k, and working range l..r
            highlights = {k: "red"}
            for idx in range(l, r+1):
                highlights.setdefault(idx, "lightblue")
            draw(arr, color_array(n, highlights))
            yield

            if left[i] <= right[j]:
                arr[k] = left[i]
                i += 1
            else:
                arr[k] = right[j]
                j += 1
            k += 1

        while i < len(left):
            highlights = {k: "red"}
            for idx in range(l, r+1):
                highlights.setdefault(idx, "lightblue")
            draw(arr, color_array(n, highlights))
            yield
            arr[k] = left[i]
            i += 1
            k += 1

        while j < len(right):
            highlights = {k: "red"}
            for idx in range(l, r+1):
                highlights.setdefault(idx, "lightblue")
            draw(arr, color_array(n, highlights))
            yield
            arr[k] = right[j]
            j += 1
            k += 1

        # mark merged section as "sorted-ish"
        block = {idx: "green" for idx in range(l, r+1)}
        draw(arr, color_array(n, block))
        yield

    def sort(l, r):
        if l >= r:
            return
        m = (l + r) // 2
        yield from sort(l, m)
        yield from sort(m + 1, r)
        yield from merge(l, m, r)

    yield from sort(0, n - 1)

def quick_sort_gen(arr, draw, delay_ms, get_delay):
    # Iterative quicksort with Lomuto partition, visualized
    n = len(arr)
    stack = [(0, n - 1)]

    while stack:
        low, high = stack.pop()
        if low >= high:
            continue

        pivot = arr[high]
        i = low
        # show pivot
        draw(arr, color_array(n, {high: "purple"}))
        yield

        for j in range(low, high):
            # highlight j and i and pivot
            draw(arr, color_array(n, {j: "orange", i: "blue", high: "purple"}))
            yield
            if arr[j] <= pivot:
                arr[i], arr[j] = arr[j], arr[i]
                # highlight swap
                draw(arr, color_array(n, {i: "red", j: "red", high: "purple"}))
                yield
                i += 1

        # place pivot
        arr[i], arr[high] = arr[high], arr[i]
        draw(arr, color_array(n, {i: "green"}))
        yield

        # Push subarrays (larger first/second doesn't matter for visualization)
        left = (low, i - 1)
        right = (i + 1, high)
        # push the larger one second (slightly balances stack)
        if (left[1] - left[0]) > (right[1] - right[0]):
            stack.append(left)
            stack.append(right)
        else:
            stack.append(right)
            stack.append(left)

# ------------- GUI Application -------------

class VisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Algorithms Visualizer")
        self.root.geometry("920x600")
        self.root.resizable(False, False)

        # state
        self.arr = []
        self.generator = None
        self.sorting = False

        # top frame: controls
        ctrl = ttk.Frame(root, padding=10)
        ctrl.pack(fill="x")

        ttk.Label(ctrl, text="Algorithm:").grid(row=0, column=0, padx=5)
        self.algo = ttk.Combobox(ctrl, values=["Bubble Sort", "Merge Sort", "Quick Sort"], state="readonly", width=16)
        self.algo.current(0)
        self.algo.grid(row=0, column=1, padx=5)

        ttk.Label(ctrl, text="Size:").grid(row=0, column=2, padx=5)
        self.size_var = tk.IntVar(value=50)
        self.size = ttk.Scale(ctrl, from_=5, to=150, orient="horizontal", command=lambda v: None)
        self.size.set(self.size_var.get())
        self.size.grid(row=0, column=3, padx=5, sticky="ew")

        ttk.Label(ctrl, text="Speed:").grid(row=0, column=4, padx=5)
        self.speed = ttk.Scale(ctrl, from_=1, to=100, orient="horizontal")
        self.speed.set(60)  # higher = faster
        self.speed.grid(row=0, column=5, padx=5, sticky="ew")

        self.generate_btn = ttk.Button(ctrl, text="Generate", command=self.generate_array)
        self.generate_btn.grid(row=0, column=6, padx=6)

        self.start_btn = ttk.Button(ctrl, text="Start", command=self.start_sort)
        self.start_btn.grid(row=0, column=7, padx=6)

        self.reset_btn = ttk.Button(ctrl, text="Reset", command=self.reset_array, state="disabled")
        self.reset_btn.grid(row=0, column=8, padx=6)

        # second row: custom array
        ttk.Label(ctrl, text="Custom (comma-separated):").grid(row=1, column=0, padx=5, pady=8, sticky="e", columnspan=2)
        self.custom_entry = ttk.Entry(ctrl, width=40)
        self.custom_entry.grid(row=1, column=2, columnspan=3, padx=5, sticky="we")
        self.use_custom_btn = ttk.Button(ctrl, text="Use Custom", command=self.use_custom)
        self.use_custom_btn.grid(row=1, column=5, padx=5, sticky="w")

        # allow some columns to stretch
        ctrl.grid_columnconfigure(3, weight=1)
        ctrl.grid_columnconfigure(5, weight=1)
        ctrl.grid_columnconfigure(2, weight=0)

        # canvas
        self.canvas_w = 900
        self.canvas_h = 430
        self.canvas = tk.Canvas(root, width=self.canvas_w, height=self.canvas_h, bg="white")
        self.canvas.pack(padx=10, pady=10)

        # first data
        self.generate_array()

    # -------- controls/helpers --------
    def get_delay_ms(self):
        # map speed slider (1..100) to a delay (ms). Higher speed -> smaller delay
        s = self.speed.get()
        # keep min delay reasonable; tweak curve for better control:
        return int(max(1, 200 - (s * 1.8)))

    def generate_array(self):
        if self.sorting:
            return
        size = int(self.size.get())
        # values in 10..400, random
        self.arr = [random.randint(10, 400) for _ in range(size)]
        self.draw(self.arr, color_array(len(self.arr)))
        self.reset_btn.config(state="disabled")

    def use_custom(self):
        if self.sorting:
            return
        text = self.custom_entry.get().strip()
        if not text:
            messagebox.showinfo("Info", "Please enter numbers separated by commas.")
            return
        try:
            nums = [int(x.strip()) for x in text.split(",")]
            if not nums:
                raise ValueError
            # normalize very small/large values to keep bars visible
            # but we’ll just clamp drawing; values themselves can be anything
            self.arr = nums
            self.draw(self.arr, color_array(len(self.arr)))
            self.reset_btn.config(state="disabled")
        except Exception:
            messagebox.showerror("Error", "Invalid input. Example: 10, 3, 25, 7, 18")

    def reset_array(self):
        if self.sorting:
            return
        # just redraw to clear highlights
        self.draw(self.arr, color_array(len(self.arr)))
        self.reset_btn.config(state="disabled")

    def start_sort(self):
        if self.sorting:
            return
        if not self.arr:
            messagebox.showinfo("Info", "Generate or enter an array first.")
            return
        algo = self.algo.get()
        # pick generator
        if algo == "Bubble Sort":
            self.generator = bubble_sort_gen(self.arr, self.draw, self.get_delay_ms(), self.get_delay_ms)
        elif algo == "Merge Sort":
            self.generator = merge_sort_gen(self.arr, self.draw, self.get_delay_ms(), self.get_delay_ms)
        else:
            self.generator = quick_sort_gen(self.arr, self.draw, self.get_delay_ms(), self.get_delay_ms)

        self.sorting = True
        self.set_controls_state(tk.DISABLED)
        self.run_step()

    def run_step(self):
        try:
            # advance one animation step
            next(self.generator)
            # schedule next step
            self.root.after(self.get_delay_ms(), self.run_step)
        except StopIteration:
            # finished
            self.sorting = False
            # final draw all green
            self.draw(self.arr, ["green"] * len(self.arr))
            self.set_controls_state(tk.NORMAL)
            self.reset_btn.config(state="normal")

    def set_controls_state(self, state):
        for w in (self.algo, self.size, self.speed, self.generate_btn, self.use_custom_btn, self.custom_entry):
            try:
                w.config(state=state)
            except Exception:
                # some widgets use 'readonly'
                if w is self.algo and state == tk.NORMAL:
                    self.algo.config(state="readonly")
        # start button only when idle
        if state == tk.NORMAL:
            self.start_btn.config(state=tk.NORMAL)
            self.algo.config(state="readonly")
        else:
            self.start_btn.config(state=tk.DISABLED)

    # -------- drawing --------
    def draw(self, arr, colors):
        self.canvas.delete("all")
        n = len(arr)
        if n == 0:
            return
        # scale heights to canvas
        max_val = max(arr) if max(arr) > 0 else 1
        bar_w = self.canvas_w / n
        pad = 2  # small gap between bars

        for i, val in enumerate(arr):
            # normalize height to canvas_h
            h = (val / max_val) * (self.canvas_h - 10)
            x0 = i * bar_w + pad
            y0 = self.canvas_h - h
            x1 = (i + 1) * bar_w
            y1 = self.canvas_h
            col = colors[i] if i < len(colors) else "gray"
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=col, outline="")
        self.root.update_idletasks()

# ------------- main -------------
if __name__ == "__main__":
    root = tk.Tk()
    app = VisualizerApp(root)
    root.mainloop()
