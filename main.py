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
	def __init__(self, parent_frame, row_idx, on_change_callback):
		self.parent_frame = parent_frame
		self.row_idx = row_idx
		self.on_change_callback = on_change_callback
		self.in_var = tk.StringVar()
		self.out_var = tk.StringVar()
		self.desc_var = tk.StringVar()
		self._formatting = False
		self.build_widgets()
		self.in_var.trace_add("write", lambda *a: self._on_time_changed(self.in_var, self.in_entry))
		self.out_var.trace_add("write", lambda *a: self._on_time_changed(self.out_var, self.out_entry))
		self.desc_var.trace_add("write", lambda *a: self.on_change_callback())

	def build_widgets(self):
		self.in_entry = ttk.Entry(self.parent_frame, textvariable=self.in_var,
								  justify="center", font=ENTRY_FONT, width=8)
		self.in_entry.grid(row=self.row_idx, column=0, padx=10, pady=8, sticky="nsew")

		self.out_entry = ttk.Entry(self.parent_frame, textvariable=self.out_var,
								   justify="center", font=ENTRY_FONT, width=8)
		self.out_entry.grid(row=self.row_idx, column=1, padx=10, pady=8, sticky="nsew")

		self.calc_label = ttk.Label(self.parent_frame, text="--:--", font=CALC_FONT, anchor="center", width=9)
		self.calc_label.grid(row=self.row_idx, column=2, padx=10, pady=8, sticky="nsew")

		self.desc_entry = ttk.Entry(self.parent_frame, textvariable=self.desc_var,
									font=ENTRY_FONT, width=34)
		self.desc_entry.grid(row=self.row_idx, column=3, padx=10, pady=8, sticky="nsew")

	def _on_time_changed(self, var, widget):
		"""Auto-format digits into HH:MM """
		if self._formatting:
			return

		self._formatting = True
		val = var.get()
		digits = "".join(ch for ch in val if ch.isdigit())
		digits = digits[:4]

		if len(digits) <= 2:
			formatted = digits
		else:
			formatted = digits[:2] + ":" + digits[2:]

		var.set(formatted)

		if len(formatted) == 5 and ":" in formatted:
			try:
				h, m = map(int, formatted.split(":"))
				if 0 <= h <= 23 and 0 <= m <= 59:
					widget.configure(background="white")
				else:
					widget.configure(background=INVALID_BG)
			except:
				widget.configure(background=INVALID_BG)
		else:
			widget.configure(background="white")

		self.on_change_callback()
		self._formatting = False

	def compute_duration(self): # obrigado gepeto
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
		
		h_in, m_in = map(int, tin.split(":"))
		h_out, m_out = map(int, tout.split(":"))
		
		if not (0 <= h_in <= 23 and 0 <= m_in <= 59 and 0 <= h_out <= 23 and 0 <= m_out <= 59):
			raise ValueError("Time outside 00:00-23:59.")
		
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
		self.root.resizable(False, False)
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

		# column proportions
		self.main_frame.columnconfigure(0, weight=0)
		self.main_frame.columnconfigure(1, weight=0)
		self.main_frame.columnconfigure(2, weight=0)
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

		# Summary
		summary_label = ttk.Label(self.root, text="Summary", style="Header.TLabel")
		summary_label.pack(pady=(12, 6))

		self.summary_frame = ttk.Frame(self.root)
		self.summary_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

		self.update_summary_ui()

	def add_row(self):
		idx = len(self.rows) + 1
		row = TimeRow(self.main_frame, idx, self.on_rows_changed)
		self.rows.append(row)

	def on_rows_changed(self):

		for r in self.rows:
			try:
				td = r.compute_duration()
				if td is None:
					r.update_calc_label(None)
				else:
					r.update_calc_label(td)
			except Exception:
				r.update_calc_label(None)

		for r in self.rows:
			r.mark_invalid_visuals()

	def on_confirm(self):
		"""
		Validate timestamps
		"""
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
				saved.append({"in": tin, "out": tout, "dur": td, "desc": desc})
			except Exception as ex:
				errors.append(f"Row {i}: {ex}")

		if errors:
			messagebox.showerror("Validation error", "Please fix the following:\n\n" + "\n".join(errors))
			return

		self.saved_entries = saved

		# if last row used, add an empty new row
		if self.rows and self.rows[-1].is_used():
			self.add_row()

		self.update_summary_ui()

	def update_summary_ui(self):
		# clear existing
		for w in self.summary_frame.winfo_children():
			w.destroy()

		if not self.saved_entries:
			lbl = ttk.Label(self.summary_frame, text="No saved timestamps yet.", font=LABEL_FONT)
			lbl.pack(pady=8)
			return

		# group by description (empty desc => "")
		totals = {}
		for e in self.saved_entries:
			desc = e["desc"]
			totals[desc] = totals.get(desc, timedelta()) + e["dur"]

		hdr = ttk.Frame(self.summary_frame)
		hdr.pack(fill="x", pady=(0, 6))
		ttk.Label(hdr, text="Description", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=6)
		ttk.Label(hdr, text="Total", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", padx=8)
		ttk.Label(hdr, text="", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", padx=6)

		# rows
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
			if not messagebox.askyesno("Clear saved", "Remove all saved timestamps from memory?"):
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
