import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random

class MemoryManager:
    def __init__(self, page_size, total_memory, segment_sizes):
        self.page_size = page_size
        self.total_memory = total_memory
        self.page_table = {}
        self.physical_memory = [None] * (total_memory // page_size)
        self.page_faults = 0
        self.page_replacements = 0
        self.segments = segment_sizes if segment_sizes else [total_memory]
        self.segment_table = {}
        self.fragmentation = {'internal': 0, 'external': 0}
        self.free_frames = set(range(total_memory // page_size))
        self.initialize_segments()

    def initialize_segments(self):
        base_address = 0
        for i, size in enumerate(self.segments):
            pages_needed = (size + self.page_size - 1) // self.page_size
            self.segment_table[i] = {'base': base_address, 'limit': size, 'pages': pages_needed}
            base_address += pages_needed * self.page_size
            self.fragmentation['internal'] += (pages_needed * self.page_size) - size
        self.fragmentation['external'] = self.total_memory - base_address

    def lru_page_replacement(self, page_number, segment_id):
        if segment_id not in self.segment_table:
            return False

        if page_number in self.page_table:
            self.page_table[page_number]['last_used'] = self.page_table[page_number].get('last_used', 0) + 1
            return True

        self.page_faults += 1
        if not self.free_frames:
            lru_page = min(self.page_table.items(), key=lambda x: x[1]['last_used'])[0]
            frame = self.page_table[lru_page]['physical_frame']
            self.physical_memory[frame] = None
            self.free_frames.add(frame)
            del self.page_table[lru_page]
            self.page_replacements += 1

        frame = self.free_frames.pop()
        self.physical_memory[frame] = page_number
        self.page_table[page_number] = {'last_used': 0, 'physical_frame': frame, 'segment_id': segment_id}
        return False

    def optimal_page_replacement(self, page_number, segment_id, future_sequence):
        if segment_id not in self.segment_table:
            return False

        if page_number in self.page_table:
            return True

        self.page_faults += 1
        if not self.free_frames:
            page_to_replace = None
            max_future_index = -1
            for page in self.page_table:
                try:
                    future_index = future_sequence.index(page)
                except ValueError:
                    future_index = float('inf')
                if future_index > max_future_index:
                    max_future_index = future_index
                    page_to_replace = page
            if page_to_replace is None:
                page_to_replace = list(self.page_table.keys())[0]
            frame = self.page_table[page_to_replace]['physical_frame']
            self.physical_memory[frame] = None
            self.free_frames.add(frame)
            del self.page_table[page_to_replace]
            self.page_replacements += 1

        frame = self.free_frames.pop()
        self.physical_memory[frame] = page_number
        self.page_table[page_number] = {'last_used': 0, 'physical_frame': frame, 'segment_id': segment_id}
        return False

    def demand_page(self, page_number, segment_id):
        if page_number not in self.page_table:
            self.lru_page_replacement(page_number, segment_id)

class MemorySimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Memory Management Simulator")
        self.root.geometry("900x700")

        input_frame = ttk.LabelFrame(root, text="Configuration", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="Page Size (bytes):").grid(row=0, column=0, padx=5, pady=5)
        self.page_size_entry = ttk.Entry(input_frame)
        self.page_size_entry.insert(0, "4096")
        self.page_size_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Total Memory (bytes):").grid(row=1, column=0, padx=5, pady=5)
        self.total_memory_entry = ttk.Entry(input_frame)
        self.total_memory_entry.insert(0, "16384")
        self.total_memory_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Segment Sizes (comma-separated):").grid(row=2, column=0, padx=5, pady=5)
        self.segment_sizes_entry = ttk.Entry(input_frame)
        self.segment_sizes_entry.insert(0, "8192,4096,4096")
        self.segment_sizes_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Algorithm:").grid(row=3, column=0, padx=5, pady=5)
        self.algorithm_combo = ttk.Combobox(input_frame, values=["LRU", "Optimal"], state="readonly")
        self.algorithm_combo.set("LRU")
        self.algorithm_combo.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Page Sequence (comma-separated):").grid(row=4, column=0, padx=5, pady=5)
        self.page_sequence_entry = ttk.Entry(input_frame)
        self.page_sequence_entry.insert(0, "1,2,3,4,1,2,5,1,2,3,4,5")
        self.page_sequence_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Segment IDs (comma-separated):").grid(row=5, column=0, padx=5, pady=5)
        self.segment_ids_entry = ttk.Entry(input_frame)
        self.segment_ids_entry.insert(0, "0,0,0,1,0,0,2,0,0,1,1,2")
        self.segment_ids_entry.grid(row=5, column=1, padx=5, pady=5)

        ttk.Button(input_frame, text="Run Simulation", command=self.run_simulation).grid(row=6, column=0, padx=5, pady=5)
        ttk.Button(input_frame, text="Demand Paging", command=self.demand_paging).grid(row=6, column=1, padx=5, pady=5)

        self.results_frame = ttk.LabelFrame(root, text="Results", padding=10)
        self.results_frame.pack(fill="x", padx=10, pady=5)

        self.results_text = tk.Text(self.results_frame, height=10, width=50)
        self.results_text.pack(pady=5)

        self.memory_frame = ttk.LabelFrame(root, text="Memory Layout", padding=10)
        self.memory_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.memory_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def run_simulation(self):
        try:
            page_size = int(self.page_size_entry.get())
            total_memory = int(self.total_memory_entry.get())  # Fixed: Correct comma and variable name
            segment_sizes = [int(x) for x in self.segment_sizes_entry.get().split(',')]
            page_sequence = [int(x) for x in self.page_sequence_entry.get().split(',')]
            segment_ids = [int(x) for x in self.segment_ids_entry.get().split(',')]

            if len(page_sequence) != len(segment_ids):
                messagebox.showerror("Error", "Page sequence and segment IDs must have the same length")
                return

            memory = MemoryManager(page_size, total_memory, segment_sizes)
            algorithm = self.algorithm_combo.get().lower()

            for i, (page, seg_id) in enumerate(zip(page_sequence, segment_ids)):
                future_sequence = page_sequence[i + 1:]
                if algorithm == 'lru':
                    memory.lru_page_replacement(page, seg_id)
                else:
                    memory.optimal_page_replacement(page, seg_id, future_sequence)

            self.display_results(memory)
            self.visualize_memory(memory)
        except ValueError as e:
            messagebox.showerror("Error", "Invalid input: " + str(e))

    def demand_paging(self):
        try:
            page_size = int(self.page_size_entry.get())
            total_memory = int(self.total_memory_entry.get())  # Fixed: Correct comma and variable name
            segment_sizes = [int(x) for x in self.segment_sizes_entry.get().split(',')]
            page_sequence = [int(x) for x in self.page_sequence_entry.get().split(',')]
            segment_ids = [int(x) for x in self.segment_ids_entry.get().split(',')]

            if len(page_sequence) != len(segment_ids):
                messagebox.showerror("Error", "Page sequence and segment IDs must have the same length")
                return

            memory = MemoryManager(page_size, total_memory, segment_sizes)
            for page, seg_id in zip(page_sequence, segment_ids):
                memory.demand_page(page, seg_id)

            self.display_results(memory)
            self.visualize_memory(memory)
        except ValueError as e:
            messagebox.showerror("Error", "Invalid input: " + str(e))

    def display_results(self, memory):
        self.results_text.delete(1.0, tk.END)
        results = (
            f"Page Faults: {memory.page_faults}\n"
            f"Page Replacements: {memory.page_replacements}\n"
            f"Internal Fragmentation: {memory.fragmentation['internal']} bytes\n"
            f"External Fragmentation: {memory.fragmentation['external']} bytes\n\n"
            "Segment Table:\n"
        )
        for seg_id, info in memory.segment_table.items():
            results += f"Segment {seg_id}: Base {info['base']}, Limit {info['limit']}, Pages {info['pages']}\n"
        self.results_text.insert(tk.END, results)

    def visualize_memory(self, memory):
        self.ax.clear()
        frame_count = len(memory.physical_memory)
        colors = ['gray' if frame is None else f'C{memory.page_table[frame]["segment_id"] % 10}' for frame in memory.physical_memory]
        labels = [f'P{frame}' if frame is not None else '' for frame in memory.physical_memory]

        self.ax.bar(range(frame_count), [1] * frame_count, color=colors, edgecolor='black')
        for i, label in enumerate(labels):
            if label:
                self.ax.text(i, 0.5, label, ha='center', va='center', color='white', fontsize=8)

        self.ax.set_title("Physical Memory Layout")
        self.ax.set_xlabel("Frame Number")
        self.ax.set_yticks([])
        self.fig.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = MemorySimulatorApp(root)
    root.mainloop()
