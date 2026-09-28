"""Original tiny binary FBX fixtures; no external parser or SDK required."""
import struct
import zlib


def write_fixtures(directory):
    def array(kind, values, code, compressed):
        raw = struct.pack("<" + code * len(values), *values)
        payload = zlib.compress(raw) if compressed else raw
        return kind + struct.pack("<III", len(values), int(compressed), len(payload)) + payload

    for version in (7400, 7500):
        for compressed in (False, True):
            wide = version >= 7500
            width = 25 if wide else 13
            null = bytes(width)

            def node(name, props, children, start):
                encoded = name.encode("ascii")
                header = width + len(encoded)
                body = props
                for child in children:
                    body += node(*child, start + header + len(body))
                if children:
                    body += null
                end = start + header + len(body)
                counts = struct.pack("<QQQ" if wide else "<III", end, int(bool(props)), len(props))
                return counts + bytes([len(encoded)]) + encoded + body

            vertices = array(b"d", [0, 0, 0, 1, 0, 0, 0, 1, 0], "d", compressed)
            indices = array(b"i", [0, 1, -3], "i", compressed)
            geometry = ("Geometry", b"", [("Vertices", vertices, []), ("PolygonVertexIndex", indices, [])])
            header = b"Kaydara FBX Binary  \x00\x1a\x00" + struct.pack("<I", version)
            payload = header + node("Objects", b"", [geometry], len(header)) + null
            (directory / f"generated_{version}_{int(compressed)}.fbx").write_bytes(payload)
            if version == 7400 and not compressed:
                corrupted = bytearray(payload)
                struct.pack_into("<I", corrupted, 27, 0x7fffffff)
                (directory / "generated_bad_offset.fbx").write_bytes(corrupted)
                (directory / "generated_truncated.fbx").write_bytes(payload[:40])
