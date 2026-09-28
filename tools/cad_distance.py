"""Read-only sampled surface comparison, independent of the product mesher."""
import math


def sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def read_mesh(text):
    points, triangles = [], []
    for line in text.splitlines():
        fields = line.split()
        if fields[:1] == ["v"]:
            points.append(tuple(map(float, fields[1:4])))
        elif fields[:1] == ["f"]:
            face = [int(f.split("/")[0]) - 1 for f in fields[1:]]
            triangles.extend((face[0], face[i], face[i+1]) for i in range(1, len(face)-1))
    return points, [tuple(points[i] for i in tri) for tri in triangles]


def segment_distance(p, a, b):
    ab, ap = sub(b, a), sub(p, a)
    t = max(0.0, min(1.0, dot(ap, ab) / dot(ab, ab)))
    delta = tuple(ap[i] - t*ab[i] for i in range(3))
    return dot(delta, delta)


def triangle_distance(p, tri):
    a, b, c = tri
    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    aa, bb, cc = dot(ab, ab), dot(ab, ac), dot(ac, ac)
    u, v = dot(ap, ab), dot(ap, ac)
    det = aa*cc-bb*bb
    if det > 1e-24:
        s, t = (cc*u-bb*v)/det, (aa*v-bb*u)/det
        if s >= 0 and t >= 0 and s+t <= 1:
            delta = tuple(ap[i]-s*ab[i]-t*ac[i] for i in range(3))
            return dot(delta, delta)
    return min(segment_distance(p, a, b), segment_distance(p, b, c), segment_distance(p, c, a))


def sampled_distance(source, target, count=128):
    vertices, triangles = read_mesh(source)
    _, targets = read_mesh(target)
    # Both vertices and face interiors: vertex-only tests can miss filled holes.
    centers = [tuple(sum(p[j] for p in tri)/3 for j in range(3)) for tri in triangles]
    samples = [items[i*len(items)//min(count, len(items))]
               for items in (vertices, centers) for i in range(min(count, len(items)))]
    boxes = [(tuple(min(p[j] for p in tri) for j in range(3)),
              tuple(max(p[j] for p in tri) for j in range(3))) for tri in targets]
    values = []
    for p in samples:
        best = math.inf
        for tri, (lo, hi) in zip(targets, boxes):
            bound = sum(max(lo[j]-p[j], 0, p[j]-hi[j])**2 for j in range(3))
            if bound < best:
                best = min(best, triangle_distance(p, tri))
        values.append(best)
    return dict(samples=len(values), maximum=math.sqrt(max(values)),
                rms=math.sqrt(sum(values)/len(values)))
