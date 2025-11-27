import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, simpledialog
import json
import os
import math
from models import Board, ComponentDefinition, PlacedComponent, Wire

# --- Config ---
COLOR_APP_BG = "#2E2E2E"
COLOR_PCB_BOARD = "#2E7D32"
COLOR_PCB_TEXT = "#A5D6A7"
COLOR_GRID_LINE = "#388E3C"
COLOR_PAD = "#1B5E20"
COLOR_PAD_HOLE = "#000000"
COLOR_WIRE_PREVIEW = "#FFEB3B"
COLOR_SNAP = "#FF5252"
COLOR_SELECT_HIGHLIGHT = "#00E5FF"
COLOR_ERROR_GHOST = "#FF0000"

LIBRARY_FILE = "user_library.json"

# --- Dialogs ---

class EditWireDialog(tk.Toplevel):
    """線條編輯視窗"""
    def __init__(self, parent, wire, callback):
        super().__init__(parent)
        self.title("Edit Wire")
        self.geometry("300x250")
        self.wire = wire
        self.callback = callback
        
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Name:").grid(row=0, column=0, pady=5)
        self.entry_name = ttk.Entry(frame)
        self.entry_name.insert(0, wire.name)
        self.entry_name.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Layer:").grid(row=1, column=0, pady=5)
        self.combo_side = ttk.Combobox(frame, values=["front", "back"], state="readonly")
        self.combo_side.set(wire.side)
        self.combo_side.grid(row=1, column=1, pady=5)

        ttk.Button(frame, text="Change Color", command=self.pick_color).grid(row=2, column=0, columnspan=2, pady=10)
        self.btn_color_preview = tk.Label(frame, text="     ", bg=wire.color, relief="sunken")
        self.btn_color_preview.grid(row=2, column=2, padx=5)

        ttk.Button(frame, text="Save", command=self.save).grid(row=3, column=0, columnspan=3, pady=20)

    def pick_color(self):
        # 修正縮排錯誤：變數 c 必須在函式內定義
        c = colorchooser.askcolor(color=self.wire.color)[1]
        if c: 
            self.wire.color = c
            self.btn_color_preview.config(bg=c)

    def save(self):
        self.wire.name = self.entry_name.get()
        self.wire.side = self.combo_side.get()
        self.callback()
        self.destroy()

class EditComponentDialog(tk.Toplevel):
    def __init__(self, parent, component, callback):
        super().__init__(parent)
        self.title("Edit Component")
        self.geometry("300x450")
        self.component = component
        self.callback = callback
        
        # Color
        frame_col = ttk.LabelFrame(self, text="Color")
        frame_col.pack(fill="x", padx=10, pady=5)
        self.btn_color = tk.Button(frame_col, text="Color", bg=component.custom_color, command=self.pick_color)
        self.btn_color.pack(fill="x", padx=5, pady=5)

        # Value
        frame_val = ttk.LabelFrame(self, text="Value / Label")
        frame_val.pack(fill="x", padx=10, pady=5)
        self.entry_val = ttk.Entry(frame_val)
        self.entry_val.insert(0, component.value)
        self.entry_val.pack(fill="x", padx=5, pady=5)

        # Size
        frame_size = ttk.LabelFrame(self, text="Dimensions (Grid)")
        frame_size.pack(fill="x", padx=10, pady=5)
        self.var_w = tk.IntVar(value=component.custom_width)
        self.var_h = tk.IntVar(value=component.custom_height)
        ttk.Entry(frame_size, textvariable=self.var_w, width=5).pack(side="left", padx=5)
        ttk.Entry(frame_size, textvariable=self.var_h, width=5).pack(side="left", padx=5)

        ttk.Button(self, text="Apply", command=self.save).pack(pady=10)

    def pick_color(self):
        c = colorchooser.askcolor(color=self.component.custom_color)[1]
        if c: 
            self.component.custom_color = c
            self.btn_color.config(bg=c)

    def save(self):
        self.component.value = self.entry_val.get()
        self.component.custom_width = self.var_w.get()
        self.component.custom_height = self.var_h.get()
        self.callback()
        self.destroy()

class StandardComponentWizard(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Wizard")
        self.geometry("350x300")
        
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Name").grid(row=0, column=0, pady=5)
        self.entry_name = ttk.Entry(frame)
        self.entry_name.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Type").grid(row=1, column=0, pady=5)
        self.combo_type = ttk.Combobox(frame, values=["IC", "Header"], state="readonly")
        self.combo_type.current(0)
        self.combo_type.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="W:").grid(row=2, column=0, pady=5)
        self.entry_w = ttk.Entry(frame)
        self.entry_w.insert(0, "4")
        self.entry_w.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="H:").grid(row=3, column=0, pady=5)
        self.entry_h = ttk.Entry(frame)
        self.entry_h.insert(0, "2")
        self.entry_h.grid(row=3, column=1, pady=5)

        ttk.Button(frame, text="Create", command=self.create).grid(row=4, column=0, columnspan=2, pady=20)

    def create(self):
        name = self.entry_name.get()
        if not name: return
        try: 
            w, h = int(self.entry_w.get()), int(self.entry_h.get())
        except: return
        
        pins = {}
        for y in range(h):
            for x in range(w):
                if self.combo_type.get() == "IC" and h > 2 and 0 < x < w-1: 
                    continue
                pins[(x, y)] = f"{len(pins)+1}"
        
        self.callback(ComponentDefinition(name, w, h, pins, "IC", "#333"))
        self.destroy()

class CustomShapeDrawer(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Drawer")
        self.geometry("600x700")
        self.grid_cells = {}
        
        # Settings
        ft = ttk.LabelFrame(self, text="Settings")
        ft.pack(fill="x", padx=10, pady=5)
        
        self.entry_name = ttk.Entry(ft)
        self.entry_name.pack(side="left", padx=2)
        self.entry_name.insert(0, "MyPart")
        
        self.combo_type = ttk.Combobox(ft, values=["IC", "R", "C", "D"], width=5)
        self.combo_type.current(0)
        self.combo_type.pack(side="left", padx=2)
        
        self.entry_w = ttk.Entry(ft, width=5)
        self.entry_w.pack(side="left", padx=2)
        self.entry_w.insert(0, "4")
        
        self.entry_h = ttk.Entry(ft, width=5)
        self.entry_h.pack(side="left", padx=2)
        self.entry_h.insert(0, "4")
        
        ttk.Button(ft, text="Set Grid", command=self.reset_grid).pack(side="left", padx=5)

        # Grid
        self.frame_grid = tk.Frame(self)
        self.frame_grid.pack(pady=10)
        
        ttk.Button(self, text="Save", command=self.save).pack(pady=10)
        self.reset_grid()

    def reset_grid(self):
        for w in self.frame_grid.winfo_children(): w.destroy()
        self.grid_cells = {}
        try: 
            w, h = int(self.entry_w.get()), int(self.entry_h.get())
        except: return

        for y in range(h):
            for x in range(w):
                btn = tk.Button(self.frame_grid, width=4, height=2, bg="white", 
                                command=lambda px=x, py=y: self.on_left(px, py))
                btn.grid(row=y, column=x, padx=1, pady=1)
                btn.bind("<Button-3>", lambda e, px=x, py=y: self.on_right(px, py))
                self.grid_cells[(x, y)] = {'btn': btn, 'state': 'empty', 'pin': None}

    def on_left(self, x, y):
        c = self.grid_cells[(x, y)]
        if c['state'] == 'empty':
            c['state'] = 'body'
            c['btn'].config(bg="#888", text="")
        else:
            c['state'] = 'empty'
            c['btn'].config(bg="white", text="")
            c['pin'] = None

    def on_right(self, x, y):
        c = self.grid_cells[(x, y)]
        if c['state'] != 'pin':
            name = simpledialog.askstring("Pin", "Name")
            if name:
                c['state'] = 'pin'
                c['pin'] = name
                c['btn'].config(bg="#F55", text=name)
        else:
            c['state'] = 'body'
            c['pin'] = None
            c['btn'].config(bg="#888", text="")

    def save(self):
        try: w, h = int(self.entry_w.get()), int(self.entry_h.get())
        except: return
        
        pins = {}
        body = set()
        for (x, y), c in self.grid_cells.items():
            if c['state'] in ['pin', 'body']:
                body.add((x, y))
            if c['state'] == 'pin':
                pins[(x, y)] = c['pin']
        
        if not body: return
        
        col_map = {"R": "#D4AC0D", "C": "#2980B9", "D": "#C0392B"}
        color = col_map.get(self.combo_type.get(), "#555")
        
        comp = ComponentDefinition(self.entry_name.get(), w, h, pins, self.combo_type.get(), color, body)
        self.callback(comp)
        self.destroy()


class PCBStudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PCB Studio Pro - Ultimate")
        self.root.geometry("1400x900")
        
        self.board = Board(30, 20)
        self.cell_size = 30
        self.scale = 1.0
        self.offset_x = 80
        self.offset_y = 80
        
        self.mode = "SELECT"
        self.is_back_view = False
        self.place_rotation = 0
        self.current_wire_points = []
        
        self.selected_comp_uid = None
        self.selected_wire = None
        
        self.hover_cell = (0,0)
        self.snap_cell = None 
        self.is_panning = False
        
        self.library = self._init_default_library()
        self.load_user_library()
        self.current_place_def = list(self.library.values())[0]

        self._setup_ui()
        self._bind_events()
        self.set_mode("SELECT")

    def _init_default_library(self):
        dip8_pins = {**{(0,y):str(y+1) for y in range(4)}, **{(2,3-y):str(y+5) for y in range(4)}}
        dip8_body = set([(0,y) for y in range(4)] + [(2,y) for y in range(4)])
        return {
            "DIP8 (IC)": ComponentDefinition("DIP8", 3, 4, dip8_pins, "IC", "#333", dip8_body),
            "Resistor": ComponentDefinition("Resistor", 3, 1, {(0,0):"1", (2,0):"2"}, "R", "#D4AC0D"),
            "Capacitor": ComponentDefinition("Cap", 2, 1, {(0,0):"+", (1,0):"-"}, "C", "#2980B9"),
            "LED": ComponentDefinition("LED", 1, 1, {(0,0):"A"}, "D", "#C0392B"),
        }

    def load_user_library(self):
        if os.path.exists(LIBRARY_FILE):
            try:
                with open(LIBRARY_FILE, "r") as f:
                    data = json.load(f)
                    for d in data: self.library[d["name"]] = ComponentDefinition.from_dict(d)
            except Exception as e: print(f"Error: {e}")

    def save_user_library(self):
        data = [c.to_dict() for c in self.library.values()]
        with open(LIBRARY_FILE, "w") as f: json.dump(data, f, indent=2)

    def _setup_ui(self):
        toolbar = ttk.Frame(self.root, relief="raised", padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Tools Left
        ttk.Button(toolbar, text="Select (Esc)", command=lambda: self.set_mode("SELECT")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Place (A)", command=lambda: self.set_mode("PLACE")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Wire (W)", command=lambda: self.set_mode("WIRE")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Eraser (X)", command=lambda: self.set_mode("DELETE")).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        # Mode Indicator
        self.lbl_status = tk.Label(toolbar, text="MODE: SELECT", font=("Arial", 10, "bold"), fg="#007ACC", width=20)
        self.lbl_status.pack(side=tk.LEFT, padx=20)

        # Tools Right
        ttk.Button(toolbar, text="Help (H)", command=self.show_help).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="Save Lib", command=self.save_user_library).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="Flip View (V)", command=self.toggle_view).pack(side=tk.RIGHT, padx=5)

        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        frame_left = ttk.Frame(paned, width=250, padding=5)
        paned.add(frame_left, weight=0)
        
        fr_cr = ttk.LabelFrame(frame_left, text="Create", padding=5)
        fr_cr.pack(fill="x")
        ttk.Button(fr_cr, text="Wizard", command=self.open_wizard).pack(fill="x")
        ttk.Button(fr_cr, text="Drawer", command=self.open_drawer).pack(fill="x")

        fr_lib = ttk.LabelFrame(frame_left, text="Library", padding=5)
        fr_lib.pack(fill="both", expand=True, pady=5)
        self.listbox = tk.Listbox(fr_lib, bg="#444", fg="white", selectbackground="#007ACC")
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_lib_select)
        ttk.Button(fr_lib, text="Delete", command=self.delete_comp).pack(fill="x")
        self.refresh_listbox()
        
        self.canvas = tk.Canvas(paned, bg=COLOR_APP_BG)
        paned.add(self.canvas, weight=1)

    # ... Helpers ...
    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for k in sorted(self.library.keys()): self.listbox.insert(tk.END, k)

    def delete_comp(self): 
        idx = self.listbox.curselection()
        if idx and messagebox.askyesno("Confirm", "Delete?"): 
            del self.library[self.listbox.get(idx)]
            self.refresh_listbox()
            self.save_user_library()

    def open_wizard(self): StandardComponentWizard(self.root, self.add_lib)
    def open_drawer(self): CustomShapeDrawer(self.root, self.add_lib)
    def add_lib(self, c): 
        self.library[c.name] = c
        self.refresh_listbox()
        self.save_user_library()

    def on_lib_select(self, e):
        idx = self.listbox.curselection()
        if idx: self.current_place_def = self.library[self.listbox.get(idx)]; self.set_mode("PLACE")

    # --- Mode & Help ---
    def set_mode(self, m): 
        self.mode = m
        self.current_wire_points = []
        self.lbl_status.config(text=f"MODE: {m}")
        
        cursor = "arrow"
        if m == "PLACE": cursor = "tcross"
        elif m == "WIRE": cursor = "plus"
        elif m == "DELETE": cursor = "X_cursor"
        
        self.canvas.config(cursor=cursor)
        self.redraw_all()

    def show_help(self):
        msg = """
        [PCB Studio Pro Help]
        
        Modes:
        - Select (Esc): Click to select components/wires. Double-click to edit. Drag to move.
        - Place (A): Place components from library. 'R' to Rotate.
        - Wire (W): Draw connections. Click pin/grid to start. Esc to finish wire.
        - Eraser (X): Click component or wire to delete.

        Shortcuts:
        - V: Flip View (Front/Back)
        - R: Rotate Component (90deg)
        - Delete: Remove selected item
        - Scroll: Zoom In/Out
        - Right Click Drag: Pan View
        """
        messagebox.showinfo("Help", msg)

    # --- Interaction ---
    def handle_esc(self, event):
        if self.mode == "WIRE" and len(self.current_wire_points) >= 2: 
            self.finish_wire()
        else: 
            self.set_mode("SELECT")

    def on_move(self, event):
        lx, ly = self.screen_to_logic(event.x, event.y)
        self.hover_cell = (lx, ly)
        self.snap_cell = None
        if self.mode == "WIRE":
            comp, pin = self.board.get_pin_obj_at(lx, ly)
            if pin: self.snap_cell = (lx, ly)
            else: self.snap_cell = (lx, ly) # Grid Center Snap
        
        if self.mode in ["PLACE", "WIRE"]: self.redraw_all()

    def on_click(self, event):
        lx, ly = self.screen_to_logic(event.x, event.y)
        
        if self.mode == "WIRE":
            target = self.snap_cell if self.snap_cell else (lx, ly)
            if not self.is_back_view:
                comp_at, pin_at = self.board.get_pin_obj_at(*target)
                is_blocked = self.board.is_location_blocked(*target)
                if is_blocked and not pin_at: 
                    messagebox.showwarning("Blocked", "Body!")
                    return
            
            self.current_wire_points.append(target)
            if len(self.current_wire_points) > 1 and self.current_wire_points[-1] == self.current_wire_points[-2]: 
                self.finish_wire()
            else: 
                self.redraw_all()

        elif self.mode == "PLACE":
            # Ghost Check (Strict)
            valid = True
            test = PlacedComponent(self.current_place_def, lx, ly, "t", self.place_rotation)
            if test.x < 0 or test.y < 0: valid = False
            elif test.x + test.width > self.board.width or test.y + test.height > self.board.height: valid = False
            
            if valid:
                self.board.add_component_instance(PlacedComponent(self.current_place_def, lx, ly, f"u{len(self.board.components)}", self.place_rotation))
                self.redraw_all()
        
        elif self.mode == "DELETE":
            c = self.board.get_component_at(lx, ly)
            if c: self.board.remove_component(c.uid)
            else:
                w = self.board.get_wire_at(lx, ly)
                if w: self.board.remove_wire(w)
            self.redraw_all()
            
        elif self.mode == "SELECT":
            c = self.board.get_component_at(lx, ly)
            if c: 
                self.selected_comp_uid = c.uid; self.selected_wire = None
            else:
                w = self.board.get_wire_at(lx, ly)
                if w: self.selected_wire = w; self.selected_comp_uid = None
                else: self.selected_wire = None; self.selected_comp_uid = None
            self.redraw_all()

    def on_double_click(self, event):
        if self.mode == "WIRE": 
            self.finish_wire()
        elif self.mode == "SELECT":
            if self.selected_comp_uid:
                comp = next((c for c in self.board.components if c.uid == self.selected_comp_uid), None)
                if comp: EditComponentDialog(self.root, comp, self.redraw_all)
            elif self.selected_wire:
                EditWireDialog(self.root, self.selected_wire, self.redraw_all)

    def on_key_delete(self, event):
        if self.selected_comp_uid: 
            self.board.remove_component(self.selected_comp_uid)
            self.selected_comp_uid = None
        elif self.selected_wire: 
            self.board.remove_wire(self.selected_wire)
            self.selected_wire = None
        self.redraw_all()

    def finish_wire(self):
        if len(self.current_wire_points) > 1 and self.current_wire_points[-1] == self.current_wire_points[-2]:
            self.current_wire_points.pop()
        
        if len(self.current_wire_points) >= 2:
            name = f"N{len(self.board.wires)}"
            side = "back" if self.is_back_view else "front"
            def_col = "#2980B9" if side == "back" else "#C0392B"
            self.board.add_wire(Wire(self.current_wire_points, name, def_col, side))
        
        self.current_wire_points = []
        self.set_mode("SELECT" if self.mode != "WIRE" else "WIRE")

    def redraw_all(self):
        self.canvas.delete("all")
        sz = self.cell_size * self.scale
        cols, rows = self.board.width, self.board.height
        bx1 = self.offset_x; by1 = self.offset_y
        bx2 = self.offset_x + cols * sz; by2 = self.offset_y + rows * sz
        margin = sz * 1.0
        
        # PCB
        self.canvas.create_rectangle(bx1-margin, by1-margin, bx2+margin, by2+margin, fill=COLOR_PCB_BOARD, outline="black", width=3)
        
        # Labels
        for c in range(cols):
            cx, cy = self.logic_to_screen(c, 0); cx += sz/2
            idx = (cols - 1 - c) if self.is_back_view else c
            char = chr(ord('A') + (idx % 26))
            self.canvas.create_text(cx, by1 - margin/2, text=char, fill=COLOR_PCB_TEXT, font=("Arial", 10, "bold"))
            self.canvas.create_text(cx, by2 + margin/2, text=char, fill=COLOR_PCB_TEXT, font=("Arial", 10, "bold"))
        for r in range(rows):
            cy = self.offset_y + r * sz + sz/2
            self.canvas.create_text(bx1 - margin/2, cy, text=str(r+1), fill=COLOR_PCB_TEXT, font=("Arial", 10, "bold"))
            self.canvas.create_text(bx2 + margin/2, cy, text=str(r+1), fill=COLOR_PCB_TEXT, font=("Arial", 10, "bold"))

        # Holes
        for r in range(rows):
            for c in range(cols):
                x, y = self.logic_to_screen(c, r)
                self.canvas.create_oval(x+2, y+2, x+sz-2, y+sz-2, fill=COLOR_PAD, outline="")
                self.canvas.create_oval(x+sz/2-2, y+sz/2-2, x+sz/2+2, y+sz/2+2, fill=COLOR_PAD_HOLE)

        # Wires
        for wire in self.board.wires:
            pts = [self.logic_to_screen(p[0], p[1]) for p in wire.points]
            flat = []
            for px, py in pts: flat.extend([px+sz/2, py+sz/2])
            
            if len(flat) >= 4:
                active = (self.is_back_view and wire.side == "back") or (not self.is_back_view and wire.side == "front")
                w_thick = 5 if active else 2 
                lc = COLOR_SELECT_HIGHLIGHT if wire == self.selected_wire else wire.color
                if wire == self.selected_wire: w_thick += 2
                
                self.canvas.create_line(flat, fill=lc, width=w_thick, capstyle="round", joinstyle="round")
                
                # Terminals
                r_term = w_thick * 0.8
                self.canvas.create_oval(flat[0]-r_term, flat[1]-r_term, flat[0]+r_term, flat[1]+r_term, fill=lc, outline="black")
                self.canvas.create_oval(flat[-2]-r_term, flat[-1]-r_term, flat[-2]+r_term, flat[-1]+r_term, fill=lc, outline="black")

        # Wire Preview
        if self.mode == "WIRE" and self.current_wire_points:
            pts = [self.logic_to_screen(p[0], p[1]) for p in self.current_wire_points]
            flat = []
            for px, py in pts: flat.extend([px+sz/2, py+sz/2])
            target = self.snap_cell if self.snap_cell else self.hover_cell
            cx, cy = self.logic_to_screen(*target)
            flat.extend([cx+sz/2, cy+sz/2])
            if len(flat) >= 4: self.canvas.create_line(flat, fill=COLOR_WIRE_PREVIEW, width=3, dash=(4,2))

        # Snap
        if self.mode == "WIRE" and self.snap_cell:
            sx, sy = self.logic_to_screen(*self.snap_cell)
            self.canvas.create_rectangle(sx-2, sy-2, sx+sz+2, sy+sz+2, outline=COLOR_SNAP, width=3)

        # Components
        for comp in self.board.components: self._draw_component(comp, sz)
        
        # Ghost
        if self.mode == "PLACE":
            test = PlacedComponent(self.current_place_def, self.hover_cell[0], self.hover_cell[1], "t", self.place_rotation)
            valid = True
            if test.x < 0 or test.y < 0: valid = False
            elif test.x + test.width > self.board.width or test.y + test.height > self.board.height: valid = False
            
            ghost_color = None if valid else COLOR_ERROR_GHOST
            self._draw_component(test, sz, is_ghost=True, ghost_override_color=ghost_color)

        txt = "BACK (SOLDER)" if self.is_back_view else "FRONT (COMPONENT)"
        self.canvas.create_text(20, 20, text=txt, fill="white", anchor="w", font=("Arial", 14, "bold"))

    def _draw_component(self, comp, sz, is_ghost=False, ghost_override_color=None):
        tags = ("comp", comp.uid)
        color = comp.custom_color
        is_transparent = comp.definition.comp_type in ["R", "C", "D"]
        draw_fill = (not self.is_back_view) and (not is_transparent) and (not is_ghost)
        draw_outline = self.is_back_view or is_ghost
        min_x, min_y, max_x, max_y = 9999, 9999, -9999, -9999
        
        for bx, by in comp.definition.body_cells:
            w, h = comp.definition.width, comp.definition.height
            rx, ry = bx, by
            if comp.rotation == 90: rx, ry = h-1-ry, rx
            elif comp.rotation == 180: rx, ry = w-1-rx, h-1-ry
            elif comp.rotation == 270: rx, ry = ry, w-1-rx
            abs_x, abs_y = comp.x + rx, comp.y + ry
            sx, sy = self.logic_to_screen(abs_x, abs_y)
            min_x = min(min_x, sx); min_y = min(min_y, sy)
            max_x = max(max_x, sx+sz); max_y = max(max_y, sy+sz)

            if draw_fill: self.canvas.create_rectangle(sx, sy, sx+sz, sy+sz, fill=color, outline="", tags=tags)
            elif draw_outline: 
                oc = ghost_override_color if ghost_override_color else "white"
                self.canvas.create_rectangle(sx+2, sy+2, sx+sz-2, sy+sz-2, outline=oc, dash=(2,2), tags=tags)
            
            if self.selected_comp_uid == comp.uid: self.canvas.create_rectangle(sx-1, sy-1, sx+sz+1, sy+sz+1, outline=COLOR_SELECT_HIGHLIGHT, width=2)
            
            if not (is_ghost and ghost_override_color):
                pin = comp.get_pin_at(abs_x, abs_y)
                if pin:
                    pc = "#FFC107" if self.is_back_view else "#B0BEC5"
                    pm = sz*0.3
                    self.canvas.create_oval(sx+pm, sy+pm, sx+sz-pm, sy+sz-pm, fill=pc, outline="black")
                    if self.is_back_view: self.canvas.create_text(sx+sz/2, sy+sz/2, text=pin, font=("Arial", 8))

        if not is_ghost and not self.is_back_view:
            cx, cy = (min_x+max_x)/2, (min_y+max_y)/2
            w_px = max_x - min_x; h_px = max_y - min_y
            c_type = comp.definition.comp_type
            if c_type == "R":
                line_w = max(3, sz * 0.15); margin = sz * 0.2
                if w_px > h_px:
                    l = w_px - 2*margin; step = l/6; pts = [(min_x+margin, cy)]
                    for i in range(1, 6): pts.append((min_x+margin + i*step, cy + ((sz*0.4) if i%2!=0 else -(sz*0.4))))
                    pts.append((max_x-margin, cy)); self.canvas.create_line(pts, fill="black", width=line_w, capstyle="round", tags=tags)
                else:
                    l = h_px - 2*margin; step = l/6; pts = [(cx, min_y+margin)]
                    for i in range(1, 6): pts.append((cx + ((sz*0.4) if i%2!=0 else -(sz*0.4)), min_y+margin + i*step))
                    pts.append((cx, max_y-margin)); self.canvas.create_line(pts, fill="black", width=line_w, capstyle="round", tags=tags)
            elif c_type == "C":
                line_w = max(2, sz * 0.1); gap = sz * 0.3; plate_len = sz * 0.8
                if w_px > h_px:
                    self.canvas.create_line(min_x, cy, cx-gap, cy, width=line_w, tags=tags)
                    self.canvas.create_line(max_x, cy, cx+gap, cy, width=line_w, tags=tags)
                    self.canvas.create_line(cx-gap, cy-plate_len/2, cx-gap, cy+plate_len/2, width=line_w*2, tags=tags)
                    self.canvas.create_line(cx+gap, cy-plate_len/2, cx+gap, cy+plate_len/2, width=line_w*2, tags=tags)
                else:
                    self.canvas.create_line(cx, min_y, cx, cy-gap, width=line_w, tags=tags)
                    self.canvas.create_line(cx, max_y, cx, cy+gap, width=line_w, tags=tags)
                    self.canvas.create_line(cx-plate_len/2, cy-gap, cx+plate_len/2, cy-gap, width=line_w*2, tags=tags)
                    self.canvas.create_line(cx-plate_len/2, cy+gap, cx+plate_len/2, cy+gap, width=line_w*2, tags=tags)
            font_size = max(8, int(9*self.scale))
            text_str = comp.value
            text_y = cy - sz * 0.6 if is_transparent and w_px > h_px else cy
            text_x = cx if w_px > h_px else cx + sz * 0.6
            self.canvas.create_text(text_x, text_y, text=text_str, fill="white", font=("Arial", font_size, "bold"), tags=tags)

    def logic_to_screen(self, lx, ly):
        sz = self.cell_size * self.scale
        draw_lx = (self.board.width - 1 - lx) if self.is_back_view else lx
        return self.offset_x + draw_lx * sz, self.offset_y + ly * sz
    def screen_to_logic(self, sx, sy):
        sz = self.cell_size * self.scale
        lx = round((sx - self.offset_x) / sz); ly = round((sy - self.offset_y) / sz)
        if self.is_back_view: lx = self.board.width - 1 - lx
        return int(lx), int(ly)
    def on_lib_select(self, e):
        idx = self.listbox.curselection()
        if idx: self.current_place_def = self.library[self.listbox.get(idx)]; self.set_mode("PLACE")
    def toggle_view(self): self.is_back_view = not self.is_back_view; self.redraw_all()
    def _bind_events(self):
        self.canvas.bind("<Button-1>", self.on_click); self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Motion>", self.on_move); self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.do_pan); self.canvas.bind("<ButtonRelease-3>", self.end_pan)
        self.canvas.bind("<MouseWheel>", self.on_zoom); self.root.bind("<Escape>", self.handle_esc)
        self.root.bind("<a>", lambda e: self.set_mode("PLACE")); self.root.bind("<w>", lambda e: self.set_mode("WIRE"))
        self.root.bind("<x>", lambda e: self.set_mode("DELETE")); self.root.bind("<v>", lambda e: self.toggle_view())
        self.root.bind("<r>", lambda e: self.rotate_key()); self.root.bind("<Delete>", self.on_key_delete)
    def start_pan(self, e): self.is_panning=True; self.last_mouse_x=e.x; self.last_mouse_y=e.y
    def do_pan(self, e): 
        if self.is_panning: self.offset_x += e.x - self.last_mouse_x; self.offset_y += e.y - self.last_mouse_y; self.last_mouse_x, self.last_mouse_y = e.x, e.y; self.redraw_all()
    def end_pan(self, e): self.is_panning=False
    def on_zoom(self, e): f = 0.9 if e.delta<0 else 1.1; self.offset_x = e.x - (e.x - self.offset_x)*f; self.offset_y = e.y - (e.y - self.offset_y)*f; self.scale *= f; self.redraw_all()
    def rotate_key(self): self.place_rotation = (self.place_rotation+90)%360; self.redraw_all()

if __name__ == "__main__":
    root = tk.Tk()
    app = PCBStudioApp(root)
    root.mainloop()