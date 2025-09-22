import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

# --------- Configuration ----------
WINDOW_WIDTH = 760
WINDOW_HEIGHT = 520
START_ROWS = 2
BG_COLOR = "#efe4ff"
BUTTON_COLOR = "#6f42c1"
BUTTON_FG = "#ffffff"
ENTRY_FONT = ("Segoe UI", 13)
LABEL_FONT = ("Segoe UI", 11)
CALC_FONT = ("Consolas", 13)
INVALID_BG = "#ff0000"
# ---------------------------------

class TimeRow:
	def __init__(self, parent_frame, row_idx, on_change_callback,
				 in_val="", out_val="", desc_val=""):
		self.parent_frame = parent_frame
		self.row_idx = row_idx
		self.on_change_callback = on_change_callback
		self.in_var = tk.StringVar(value=in_val)
		self.out_var = tk.StringVar(value=out_val)
		self.desc_var = tk.StringVar(value=desc_val)

		self.build_widgets()

	def build_widgets(self):
		vcmd_in = (self.parent_frame.register(self._validate_time), "%P", "%W")
		vcmd_out = (self.parent_frame.register(self._validate_time), "%P", "%W")

		self.in_entry = ttk.Entry(self.parent_frame, textvariable=self.in_var,
								  justify="center", font=ENTRY_FONT, width=8,
								  validate="key", validatecommand=vcmd_in)
		self.in_entry.grid(row=self.row_idx, column=0, padx=10, pady=8, sticky="nsew")

		self.out_entry = ttk.Entry(self.parent_frame, textvariable=self.out_var,
								   justify="center", font=ENTRY_FONT, width=8,
								   validate="key", validatecommand=vcmd_out)
		self.out_entry.grid(row=self.row_idx, column=1, padx=10, pady=8, sticky="nsew")

		self.calc_label = ttk.Label(self.parent_frame, text="--:--", font=CALC_FONT, anchor="center", width=9)
		self.calc_label.grid(row=self.row_idx, column=2, padx=10, pady=8, sticky="nsew")

		self.desc_entry = ttk.Entry(self.parent_frame, textvariable=self.desc_var,
									font=ENTRY_FONT, width=34)
		self.desc_entry.grid(row=self.row_idx, column=3, padx=10, pady=8, sticky="nsew")

		self.in_var.trace_add("write", lambda *a: self.on_change_callback())
		self.out_var.trace_add("write", lambda *a: self.on_change_callback())
		self.desc_var.trace_add("write", lambda *a: self.on_change_callback())

	def _validate_time(self, proposed, widget_name):
		digits = "".join(ch for ch in proposed if ch.isdigit())
		digits = digits[:4]

		if len(digits) <= 2:
			formatted = digits
		else:
			formatted = digits[:2] + ":" + digits[2:]

		formatted = formatted[:5]
		widget = self.parent_frame.nametowidget(widget_name)
		current = widget.get()
		if current != formatted:
			widget.delete(0, tk.END)
			widget.insert(0, formatted)
		return True

	def compute_duration(self):
		tin = self.in_var.get().strip()
		tout = self.out_var.get().strip()
		if not tin and not tout and not self.desc_var.get().strip():
			return None

		if not (tin and tout):
			raise ValueError("Missing entry/exit time.")

		if len(tin) != 5 or ":" not in tin or len(tout) != 5 or ":" not in tout:
			raise ValueError("Time must be HH:MM.")

		try:
			t_in = datetime.strptime(tin, "%H:%M")
			t_out = datetime.strptime(tout, "%H:%M")
		except ValueError:
			raise ValueError("Invalid time digits.")

		if t_out <= t_in:
			raise ValueError("Exit must be after Entry (same day).")

		return t_out - t_in

	def update_calc_label(self, td: timedelta):
		if td is None:
			self.calc_label.config(text="--:--")
			return
		h, rem = divmod(td.seconds, 3600)
		m = rem // 60
		self.calc_label.config(text=f"{h:02}:{m:02}")

	def is_used(self):
		return bool(self.in_var.get().strip() or self.out_var.get().strip() or self.desc_var.get().strip())

	def get_values(self):
		return self.in_var.get().strip(), self.out_var.get().strip(), self.desc_var.get().strip()

	def mark_invalid_visuals(self):
		for ent_var, ent_widget in ((self.in_var, self.in_entry), (self.out_var, self.out_entry)):
			txt = ent_var.get().strip()
			if len(txt) == 5 and ":" in txt:
				try:
					h, m = map(int, txt.split(":"))
					if 0 <= h <= 23 and 0 <= m <= 59:
						ent_widget.configure(background="white")
					else:
						ent_widget.configure(background=INVALID_BG)
				except:
					ent_widget.configure(background=INVALID_BG)
			else:
				ent_widget.configure(background="white")


class MiniTimeManagerApp:
	def __init__(self, root):
		self.root = root
		self.root.title("TTTT — Tiny Task Time Tracker")
		self.root.configure(bg=BG_COLOR)
		self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
		self.root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.root.resizable(True, True)
		self.center_window()

		self.root.attributes("-topmost", True)

		try:
			root.iconbitmap("icon.ico")
		except Exception:
			pass

		self.style = ttk.Style()
		try:
			self.style.theme_use("clam")
		except:
			pass
		self.style.configure("TEntry", padding=6)
		self.style.configure("Header.TLabel", font=("Segoe UI", 13, "bold"), background=BG_COLOR)
		self.style.configure("TLabel", background=BG_COLOR)

		self.rows = []
		self.saved_entries = []

		self.build_ui()

	def center_window(self):
		self.root.update_idletasks()
		ws = self.root.winfo_screenwidth()
		hs = self.root.winfo_screenheight()
		x = (ws // 2) - (WINDOW_WIDTH // 2)
		y = (hs // 2) - (WINDOW_HEIGHT // 2)
		self.root.geometry(f"+{x}+{y}")

	def build_ui(self):
		title = ttk.Label(self.root, text="TTTT — Tiny Task Time Tracker", style="Header.TLabel")
		title.pack(pady=(12, 6))

		self.main_frame = ttk.Frame(self.root)
		self.main_frame.pack(fill="x", padx=14)

		headers = ["In (HH:MM)", "Out (HH:MM)", "Total", "Description"]
		for i, h in enumerate(headers):
			lbl = ttk.Label(self.main_frame, text=h, font=LABEL_FONT)
			lbl.grid(row=0, column=i, padx=8, pady=6, sticky="w")

		self.main_frame.columnconfigure(3, weight=1)

		for _ in range(START_ROWS):
			self.add_row()

		ctrl_frame = ttk.Frame(self.root)
		ctrl_frame.pack(fill="x", padx=14, pady=(10, 6))

		self.confirm_btn = tk.Button(ctrl_frame, text="Confirm ✔", bg=BUTTON_COLOR, fg=BUTTON_FG,
									 font=("Segoe UI", 12, "bold"), command=self.on_confirm)
		self.confirm_btn.pack(side="left", padx=(0, 8))

		self.clear_btn = tk.Button(ctrl_frame, text="Clear Saved", font=("Segoe UI", 11), command=self.clear_saved)
		self.clear_btn.pack(side="left")

		summary_label = ttk.Label(self.root, text="Summary", style="Header.TLabel")
		summary_label.pack(pady=(12, 6))

		self.summary_frame = ttk.Frame(self.root)
		self.summary_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

		self.update_summary_ui()

	def add_row(self, in_val="", out_val="", desc_val=""):
		idx = len(self.rows) + 1
		row = TimeRow(self.main_frame, idx, self.on_rows_changed, in_val, out_val, desc_val)
		self.rows.append(row)

	def on_rows_changed(self):
		for r in self.rows:
			try:
				td = r.compute_duration()
				r.update_calc_label(td)
			except Exception:
				r.update_calc_label(None)
		for r in self.rows:
			r.mark_invalid_visuals()

	def on_confirm(self):
		errors = []
		saved = []
		for i, r in enumerate(self.rows, start=1):
			if not r.is_used():
				continue
			try:
				td = r.compute_duration()
				if td is None:
					raise ValueError("Incomplete row.")
				tin, tout, desc = r.get_values()
				t_in = datetime.strptime(tin, "%H:%M")
				saved.append({"in": tin, "out": tout, "dur": td, "desc": desc, "t_in": t_in})
			except Exception as ex:
				errors.append(f"Row {i}: {ex}")

		if errors:
			messagebox.showerror("Validation error", "Please fix:\n\n" + "\n".join(errors))
			return

		# Sort saved by in time
		saved.sort(key=lambda x: x["t_in"])
		self.saved_entries = saved

		# --- rebuild rows in sorted order ---
		for w in self.main_frame.winfo_children():
			if isinstance(w, ttk.Entry) or isinstance(w, ttk.Label):
				w.destroy()
		self.rows.clear()

		headers = ["In (HH:MM)", "Out (HH:MM)", "Total", "Description"]
		for i, h in enumerate(headers):
			lbl = ttk.Label(self.main_frame, text=h, font=LABEL_FONT)
			lbl.grid(row=0, column=i, padx=8, pady=6, sticky="w")

		for e in saved:
			self.add_row(e["in"], e["out"], e["desc"])

		# if last row used, add empty row
		if self.rows and self.rows[-1].is_used():
			self.add_row()

		# grow window if needed
		self.root.update_idletasks()
		req_height = self.root.winfo_reqheight() + 40
		if req_height > self.root.winfo_height():
			self.root.geometry(f"{WINDOW_WIDTH}x{req_height}")

		self.update_summary_ui()

	def update_summary_ui(self):
		for w in self.summary_frame.winfo_children():
			w.destroy()
		if not self.saved_entries:
			lbl = ttk.Label(self.summary_frame, text="No saved timestamps yet.", font=LABEL_FONT)
			lbl.pack(pady=8)
			return
		totals = {}
		for e in self.saved_entries:
			desc = e["desc"]
			totals[desc] = totals.get(desc, timedelta()) + e["dur"]

		hdr = ttk.Frame(self.summary_frame)
		hdr.pack(fill="x", pady=(0, 6))
		ttk.Label(hdr, text="Description", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=6)
		ttk.Label(hdr, text="Total", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", padx=8)
		ttk.Label(hdr, text="", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", padx=6)

		for desc, td in sorted(totals.items(), key=lambda x: (x[0] != "", x[0].lower())):
			frame = ttk.Frame(self.summary_frame)
			frame.pack(fill="x", pady=4)
			display_desc = desc if desc != "" else "(empty)"
			lbl_desc = ttk.Label(frame, text=display_desc, font=LABEL_FONT)
			lbl_desc.grid(row=0, column=0, sticky="w", padx=6)
			h, rem = divmod(td.seconds, 3600)
			m = rem // 60
			total_text = f"{h}h {m}m"
			lbl_total = ttk.Label(frame, text=total_text, font=LABEL_FONT)
			lbl_total.grid(row=0, column=1, sticky="w", padx=12)
			copy_btn = tk.Button(frame, text="Copy", bg=BUTTON_COLOR, fg=BUTTON_FG,
								 command=lambda txt=total_text: self.copy_to_clipboard(txt))
			copy_btn.grid(row=0, column=2, padx=6)

	def copy_to_clipboard(self, text):
		try:
			self.root.clipboard_clear()
			self.root.clipboard_append(text)
			self.root.update()
		except Exception as ex:
			messagebox.showerror("Clipboard error", str(ex))

	def clear_saved(self):
		if not self.saved_entries:
			if not messagebox.askyesno("Clear saved", "No saved timestamps. Clear rows anyway?"):
				return
		else:
			if not messagebox.askyesno("Clear saved", "Remove all saved timestamps?"):
				return
		self.saved_entries.clear()
		for r in self.rows:
			r.in_var.set("")
			r.out_var.set("")
			r.desc_var.set("")
			r.update_calc_label(None)
		self.update_summary_ui()


if __name__ == "__main__":
	root = tk.Tk()
	app = MiniTimeManagerApp(root)
	root.mainloop()
