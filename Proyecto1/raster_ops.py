import random

# Operaciones de rasterización de bajo nivel separadas del Renderer

def put_pixel(renderer, x, y, z, color):
    x_i, y_i = round(x), round(y)
    if 0 <= x_i < renderer.width and 0 <= y_i < renderer.height:
        if z < renderer.zBuffer[x_i][y_i]:
            renderer.zBuffer[x_i][y_i] = z
            draw_color = [int(c * 255) for c in color]
            renderer.screen.set_at((x_i, renderer.height - 1 - y_i), draw_color)
            renderer.frameBuffer[x_i][y_i] = draw_color

def draw_point(renderer, point, color):
    put_pixel(renderer, point[0], point[1], point[2], color)

def draw_line(renderer, p0, p1, color):
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    steep = dy > dx
    if steep:
        x0, y0, z0, x1, y1, z1 = y0, x0, z0, y1, x1, z1
    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0
        z0, z1 = z1, z0
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    offset = 0
    limit = 0.5
    m = dy / dx if dx != 0 else 0
    y = y0
    for x in range(int(round(x0)), int(round(x1)) + 1):
        t = (x - x0) / (x1 - x0) if (x1 - x0) != 0 else 0
        z = z0 + (z1 - z0) * t
        if steep:
            put_pixel(renderer, y, x, z, color)
        else:
            put_pixel(renderer, x, y, z, color)
        offset += m
        if offset >= limit:
            y += 1 if y0 < y1 else -1
            limit += 1

def raster_triangle(renderer, A, B, C, uv_coords=None, vertex_colors=None, normals=None, triangle_index=None, tangents=None, bitangents=None):
    # Bounds
    for p in (A, B, C):
        if len(p) < 3:
            return
    minX = max(0, int(min(A[0], B[0], C[0])))
    maxX = min(renderer.width - 1, int(max(A[0], B[0], C[0])))
    minY = max(0, int(min(A[1], B[1], C[1])))
    maxY = min(renderer.height - 1, int(max(A[1], B[1], C[1])))
    if (maxX - minX) * (maxY - minY) > 100000:
        return
    def edge(p1, p2, p):
        return (p[0] - p1[0]) * (p2[1] - p1[1]) - (p[1] - p1[1]) * (p2[0] - p1[0])
    area = edge(A, B, C)
    if abs(area) < 0.01:
        return
    for x in range(minX, maxX + 1):
        for y in range(minY, maxY + 1):
            P = (x + 0.5, y + 0.5)
            w0 = edge(B, C, P) / area
            w1 = edge(C, A, P) / area
            w2 = edge(A, B, P) / area
            if w0 >= 0 and w1 >= 0 and w2 >= 0:
                z = w0 * A[2] + w1 * B[2] + w2 * C[2]
                # Base color
                if renderer.activeFragmentShader is None:
                    base_col = renderer.triColorCurrent if renderer.triColorCurrent is not None else renderer.currColor
                    color = base_col[:]
                else:
                    color = renderer.currColor[:]
                current_texture = renderer.activeTexture
                if renderer.activeFragmentShader or getattr(renderer.activeModel, 'fragmentShaderChain', []):
                    try:
                        fragment_data = {
                            'position': [x, y, z],
                            'barycentric': [w0, w1, w2],
                            'vertex_colors': vertex_colors,
                            'uv_coords': uv_coords,
                            'texture': current_texture,
                            'normals': normals,
                            'triangle_index': triangle_index,
                            'extra_maps': getattr(renderer, '_current_extra_maps', {}),
                            'tangents': tangents,
                            'bitangents': bitangents
                        }
                        color = renderer.apply_fragment_chain(fragment_data)
                    except Exception:
                        color = [1,0,0]
                elif vertex_colors and len(vertex_colors) >= 3:
                    color = [
                        w0 * vertex_colors[0][0] + w1 * vertex_colors[1][0] + w2 * vertex_colors[2][0],
                        w0 * vertex_colors[0][1] + w1 * vertex_colors[1][1] + w2 * vertex_colors[2][1],
                        w0 * vertex_colors[0][2] + w1 * vertex_colors[1][2] + w2 * vertex_colors[2][2]
                    ]
                elif uv_coords and current_texture:
                    u = w0 * uv_coords[0][0] + w1 * uv_coords[1][0] + w2 * uv_coords[2][0]
                    v = w0 * uv_coords[0][1] + w1 * uv_coords[1][1] + w2 * uv_coords[2][1]
                    u = max(0, min(1, u))
                    v = max(0, min(1, v))
                    tex_width = current_texture.get_width()
                    tex_height = current_texture.get_height()
                    tex_x = int(u * (tex_width - 1))
                    tex_y = int((1 - v) * (tex_height - 1))
                    tex_x = max(0, min(tex_width - 1, tex_x))
                    tex_y = max(0, min(tex_height - 1, tex_y))
                    pixel_color = current_texture.get_at((tex_x, tex_y))
                    color = [pixel_color.r/255, pixel_color.g/255, pixel_color.b/255]
                put_pixel(renderer, x, y, z, color)
