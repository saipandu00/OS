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
