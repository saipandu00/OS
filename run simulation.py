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
