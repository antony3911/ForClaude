"""Walk a Monster Hunter Wilds .efx (version 5571972) down to its attributes.

Follows the layout of kagenocookie's REE-EFX-Unified 010 template (RE_Engine_EFX_UNIFIED.bt):
header, string block, expression parameters (with default values), bones, actions and
entries, each made of attributes. In Wilds every attribute starts with
(itemType, itemSize, ...), so attributes can be stepped over without knowing their fields.

Used by recolor_efx.py. Run directly to list a file:
    python efx_walk.py <file.efx.5571972> [wilds_types.json]
(wilds_types.json maps type ids to names; made from the template's getStructNameMHWilds.)
"""
import json
import struct
import sys


class Attr:
    def __init__(self, owner, index, offset, item_type, size):
        self.owner, self.index, self.offset, self.type, self.size = owner, index, offset, item_type, size

    @property
    def data_start(self):
        return self.offset + 8           # after itemType and itemSize

    @property
    def end(self):
        return self.offset + 8 + self.size


class Efx:
    def __init__(self, data):
        self.data = data
        u = lambda o: struct.unpack_from("<I", data, o)[0]
        if data[:4] != b"efxr":
            raise ValueError("not an efx file")
        (self.unkn0, self.entry_count, self.entry_length, self.action_count, self.field_count,
         self.expr_count, self.group_count, self.group_length, self.bone_count,
         self.bone_attr_count, self.unkn_flag) = struct.unpack_from("<11I", data, 4)
        pos = 48
        self.strings = self._strings(pos)
        pos += self.entry_length
        # Expression parameters: 2 hashes, type, 12 bytes of value (type 1 = RGBA colour).
        self.expressions = []
        for i in range(self.expr_count):
            h16, h8, typ = struct.unpack_from("<3I", data, pos)
            self.expressions.append({"offset": pos, "type": typ, "value_offset": pos + 12,
                                     "name": self.strings["expressions"][i] if i < len(self.strings["expressions"]) else "?"})
            pos += 24
        pos += self.bone_count * 8
        pos += self.bone_attr_count * 2
        self.attrs = []
        for a in range(self.action_count):
            _, _, count = struct.unpack_from("<3I", data, pos)
            pos = self._attrs(pos + 12, count, f"action {a}")
        for _ in range(self.field_count):
            pos = self._field(pos)
        for e in range(self.entry_count):
            _, _, _, count = struct.unpack_from("<3Ii", data, pos)
            name = self.strings["entries"][e] if e < len(self.strings["entries"]) else f"entry {e}"
            pos = self._attrs(pos + 16, count, name)
        self.end = pos

    def _strings(self, pos):
        """Expression names are UTF-8 + UTF-16, bone names likewise, the rest UTF-8."""
        d = self.data

        def cstr(p):
            e = d.index(b"\0", p)
            return d[p:e].decode("utf-8", "replace"), e + 1

        def wstr(p):
            e = p
            while d[e:e + 2] != b"\0\0":
                e += 2
            return d[p:e].decode("utf-16le", "replace"), e + 2

        out = {"expressions": [], "bones": [], "actions": [], "fields": [], "entries": []}
        for _ in range(self.expr_count):
            s, pos = cstr(pos)
            w, pos = wstr(pos)
            out["expressions"].append(w or s)
        for _ in range(self.bone_count):
            s, pos = cstr(pos)
            w, pos = wstr(pos)
            out["bones"].append(w or s)
        for key, n in (("actions", self.action_count), ("fields", self.field_count),
                       ("entries", self.entry_count)):
            for _ in range(n):
                s, pos = cstr(pos)
                out[key].append(s)
        return out

    def _attrs(self, pos, count, owner):
        for i in range(count):
            item_type, size = struct.unpack_from("<Ii", self.data, pos)
            attr = Attr(owner, i, pos, item_type, size)
            self.attrs.append(attr)
            pos = attr.end
        return pos

    def _field(self, pos):
        d = self.data
        typ = struct.unpack_from("<I", d, pos + 12)[0]
        if typ == 196:
            n = struct.unpack_from("<I", d, pos + 20)[0]
            return pos + 24 + n * 2
        pos += 20 + 4 + 8 + 12 + 4          # unkn5, unkn6, unkn7, 3 floats, wilds_unkn0
        if typ in (110, 144, 183, 184, 194, 196, 202, 215, 217):
            n = struct.unpack_from("<I", d, pos)[0]
            pos += 4 + n * 2
        return pos


def main():
    data = open(sys.argv[1], "rb").read()
    names = {}
    if len(sys.argv) > 2:
        names = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
    efx = Efx(data)
    print(f"entries {efx.entry_count}, actions {efx.action_count}, fields {efx.field_count}, "
          f"expressions {efx.expressions and [(e['name'], e['type']) for e in efx.expressions]}")
    print(f"parsed to {efx.end} of {len(data)} bytes")
    for a in efx.attrs:
        print(f"  {a.owner:18s} #{a.index:2d} @{a.offset:6d} type {a.type:3d} "
              f"{names.get(a.type, '?'):36s} size {a.size}")


if __name__ == "__main__":
    main()
