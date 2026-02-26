from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .logic_export import create_logic_project_bundle
from .pipeline import analyze_melody_data, load_input_file


class LogicBuilderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Melody Logic Builder")
        self.root.geometry("760x460")

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.cwd() / "logic_export"))
        self.project_var = tk.StringVar(value="Melody Logic Project")
        self.style_var = tk.StringVar(value="pop")
        self.bars_var = tk.StringVar(value="")
        self.tempo_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Input Melody File").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.input_var, width=70).grid(row=1, column=0, sticky=tk.W)
        ttk.Button(frame, text="Browse", command=self._pick_input).grid(row=1, column=1, padx=8, sticky=tk.W)

        ttk.Label(frame, text="Output Directory").grid(row=2, column=0, sticky=tk.W, pady=(12, 0))
        ttk.Entry(frame, textvariable=self.output_var, width=70).grid(row=3, column=0, sticky=tk.W)
        ttk.Button(frame, text="Browse", command=self._pick_output).grid(row=3, column=1, padx=8, sticky=tk.W)

        ttk.Label(frame, text="Project Name").grid(row=4, column=0, sticky=tk.W, pady=(12, 0))
        ttk.Entry(frame, textvariable=self.project_var, width=40).grid(row=5, column=0, sticky=tk.W)

        options = ttk.Frame(frame)
        options.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(16, 0))
        ttk.Label(options, text="Style").grid(row=0, column=0, sticky=tk.W)
        ttk.Combobox(options, textvariable=self.style_var, values=["pop", "modal", "jazz"], width=12).grid(
            row=0, column=1, padx=(8, 20)
        )
        ttk.Label(options, text="Bars (optional)").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(options, textvariable=self.bars_var, width=8).grid(row=0, column=3, padx=(8, 20))
        ttk.Label(options, text="Tempo (optional)").grid(row=0, column=4, sticky=tk.W)
        ttk.Entry(options, textvariable=self.tempo_var, width=8).grid(row=0, column=5, padx=8)

        ttk.Button(frame, text="Generate Logic Kit", command=self._run).grid(row=7, column=0, sticky=tk.W, pady=(22, 0))
        ttk.Label(frame, textvariable=self.status_var).grid(row=8, column=0, sticky=tk.W, pady=(16, 0))

        tips = (
            "Supported input: WAV, AIFF, MIDI, MusicXML, CSV.\n"
            "Output contains logic_arrangement.mid + macOS launcher script."
        )
        ttk.Label(frame, text=tips, foreground="#444").grid(row=9, column=0, sticky=tk.W, pady=(16, 0))

    def _pick_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Select melody file",
            filetypes=[
                ("Melody files", "*.wav *.aif *.aiff *.mid *.midi *.xml *.musicxml *.csv"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.input_var.set(path)

    def _pick_output(self) -> None:
        path = filedialog.askdirectory(title="Select output directory")
        if path:
            self.output_var.set(path)

    def _run(self) -> None:
        input_path = self.input_var.get().strip()
        output_dir = self.output_var.get().strip()
        project_name = self.project_var.get().strip() or "Melody Logic Project"
        style = self.style_var.get().strip() or "pop"

        if not input_path:
            messagebox.showerror("Missing input", "Please choose an input melody file.")
            return
        if not Path(input_path).exists():
            messagebox.showerror("File not found", f"Input file does not exist:\n{input_path}")
            return

        bars = None
        tempo = None
        if self.bars_var.get().strip():
            try:
                bars = int(self.bars_var.get().strip())
            except ValueError:
                messagebox.showerror("Invalid bars", "Bars must be an integer.")
                return
        if self.tempo_var.get().strip():
            try:
                tempo = float(self.tempo_var.get().strip())
            except ValueError:
                messagebox.showerror("Invalid tempo", "Tempo must be a number.")
                return

        try:
            self.status_var.set("Analyzing melody...")
            self.root.update_idletasks()
            data = load_input_file(input_path, tempo_override=tempo, beats_per_bar=4)
            report = analyze_melody_data(data=data, style=style, bars=bars, top_k=3)
            bundle = create_logic_project_bundle(
                data=data,
                report=report,
                output_dir=output_dir,
                project_name=project_name,
                quantize_subdivisions=4,
            )
        except Exception as exc:  # noqa: BLE001
            self.status_var.set("Failed")
            messagebox.showerror("Generation failed", str(exc))
            return

        self.status_var.set(f"Done: {bundle['bundle_dir']}")
        messagebox.showinfo(
            "Logic kit generated",
            "Created successfully:\n\n"
            f"- Bundle: {bundle['bundle_dir']}\n"
            f"- MIDI: {bundle['midi']}\n"
            f"- Launcher: {bundle['logic_launcher']}",
        )


def main() -> int:
    root = tk.Tk()
    app = LogicBuilderApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
