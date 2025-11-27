# models.py
import json
import math

class Wire:
    def __init__(self, points, name="Wire", color="#FF0000", side="back"):
        self.points = points 
        self.name = name
        self.color = color
        self.side = side 

    @property
    def start_term(self):
        return self.points[0] if self.points else None

    @property
    def end_term(self):
        return self.points[-1] if self.points else None

    def is_point_on_wire(self, x, y, threshold=0.5):
        if len(self.points) < 2: return False
        for i in range(len(self.points) - 1):
            if self._dist_point_to_segment(x, y, self.points[i], self.points[i+1]) < threshold:
                return True
        return False

    def _dist_point_to_segment(self, px, py, p1, p2):
        x1, y1 = p1; x2, y2 = p2
        dx = x2 - x1; dy = y2 - y1
        if dx == 0 and dy == 0: return math.hypot(px - x1, py - y1)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

    def to_dict(self):
        return {"points": self.points, "name": self.name, "color": self.color, "side": self.side}
    @staticmethod
    def from_dict(data):
        return Wire(data["points"], data["name"], data["color"], data.get("side", "back"))

class ComponentDefinition:
    def __init__(self, name, width, height, pin_labels, comp_type="IC", default_color="#555", body_cells=None):
        self.name = name
        self.width = width
        self.height = height
        self.pin_labels = pin_labels 
        self.comp_type = comp_type
        self.default_color = default_color
        self.body_cells = body_cells if body_cells else set((x, y) for x in range(width) for y in range(height))

    def to_dict(self):
        pins_str = {f"{k[0]},{k[1]}": v for k, v in self.pin_labels.items()}
        return {"name": self.name, "width": self.width, "height": self.height, 
                "pin_labels": pins_str, "comp_type": self.comp_type, 
                "default_color": self.default_color, "body_cells": list(self.body_cells)}
    @staticmethod
    def from_dict(data):
        pins = {}; body = set(tuple(p) for p in data["body_cells"])
        for k, v in data["pin_labels"].items(): x, y = map(int, k.split(",")); pins[(x, y)] = v
        return ComponentDefinition(data["name"], data["width"], data["height"], pins, data["comp_type"], data["default_color"], body)

class PlacedComponent:
    def __init__(self, definition, x, y, uid, rotation=0, color=None, custom_width=None, custom_height=None, value=None):
        self.definition = definition
        self.x = x
        self.y = y
        self.uid = uid
        self.rotation = rotation 
        self.custom_color = color if color else definition.default_color
        self.custom_width = custom_width if custom_width else definition.width
        self.custom_height = custom_height if custom_height else definition.height
        self.value = value if value else definition.name

    @property
    def width(self): return self.custom_height if self.rotation in [90, 270] else self.custom_width
    @property
    def height(self): return self.custom_width if self.rotation in [90, 270] else self.custom_height

    def get_rotated_coords(self, rel_x, rel_y):
        if self.rotation == 0:   return rel_x, rel_y
        if self.rotation == 90:  return rel_y, self.custom_height - 1 - rel_x
        if self.rotation == 180: return self.custom_width - 1 - rel_x, self.custom_height - 1 - rel_y
        if self.rotation == 270: return self.custom_width - 1 - rel_y, rel_x
        return rel_x, rel_y

    def get_pin_at(self, board_x, board_y):
        orig_x, orig_y = self.get_rotated_coords(board_x - self.x, board_y - self.y)
        return self.definition.pin_labels.get((orig_x, orig_y))

    def is_body_at(self, board_x, board_y):
        rel_x, rel_y = board_x - self.x, board_y - self.y
        if not (0 <= rel_x < self.width and 0 <= rel_y < self.height): return False
        orig_x, orig_y = self.get_rotated_coords(rel_x, rel_y)
        return (orig_x, orig_y) in self.definition.body_cells

class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.components = [] 
        self.wires = []
    
    def add_component_instance(self, placed_comp):
        # 1. Strict Boundary Check (Update)
        # Check negative coordinates
        if placed_comp.x < 0 or placed_comp.y < 0:
            return False
        # Check positive overflow
        if placed_comp.x + placed_comp.width > self.width or placed_comp.y + placed_comp.height > self.height:
            return False
        
        self.components.append(placed_comp)
        return True

    def remove_component(self, uid):
        self.components = [c for c in self.components if c.uid != uid]
    
    def remove_wire(self, wire):
        if wire in self.wires: self.wires.remove(wire)

    def get_component_at(self, x, y):
        for comp in reversed(self.components):
            if comp.is_body_at(x, y): return comp
        return None
    
    def get_wire_at(self, x, y):
        for wire in reversed(self.wires):
            if wire.is_point_on_wire(x, y): return wire
        return None

    def get_pin_obj_at(self, x, y):
        for comp in reversed(self.components):
            pin_name = comp.get_pin_at(x, y)
            if pin_name: return comp, pin_name
        return None, None

    def add_wire(self, wire): self.wires.append(wire)
    def is_location_blocked(self, x, y): return self.get_component_at(x, y) is not None