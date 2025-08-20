import pygame
from shaders import (
    vertexShader, waveVertexShader, pulseVertexShader, mathPathVertexShader,
    rainbowFragmentShader, textureFragmentShader, toonFragmentShader,
    mathPathFragmentShader, sliceFragmentShader, normalMapFragmentShader, origamiFragmentShader, dotFragmentShader
)

# Registro de shaders Vertex
vertex_shaders = {
    'normal':  { 'func': vertexShader,        'label': 'Normal',     'desc': 'Geometría sin deformar', 'hotkey': '7' },
    'wave':    { 'func': waveVertexShader,    'label': 'Wave',       'desc': 'Ondas senoidales',       'hotkey': '8' },
    'pulse':   { 'func': pulseVertexShader,   'label': 'Pulse',      'desc': 'Escala pulsante',        'hotkey': '9' },
    'math':    { 'func': mathPathVertexShader,'label': 'MathPath',   'desc': 'Trayectorias matem.',    'hotkey': '0' },
}

# Registro de shaders Fragment
fragment_shaders = {
    'texture': { 'func': textureFragmentShader,  'label': 'Texture', 'desc': 'Muestra textura',       'hotkey': '4', 'requires_texture': True },
    'rainbow': { 'func': rainbowFragmentShader,  'label': 'Rainbow', 'desc': 'Gradiente arcoíris',    'hotkey': '5', 'requires_texture': False },
    'toon':    { 'func': toonFragmentShader,     'label': 'Toon',    'desc': 'Sombreado cartoon',     'hotkey': '6', 'requires_texture': True },
    'math':    { 'func': mathPathFragmentShader, 'label': 'Math',    'desc': 'Bandas matemáticas',    'hotkey': 'm', 'requires_texture': False },
    'slice':   { 'func': sliceFragmentShader,    'label': 'Slice',   'desc': 'Cortes en X',           'hotkey': 'x', 'requires_texture': True },
    'nmap':    { 'func': normalMapFragmentShader,'label': 'NMap',    'desc': 'Normal mapping básico', 'hotkey': 'n', 'requires_texture': True },
    'origami': { 'func': origamiFragmentShader,  'label': 'Origami', 'desc': 'Caras blancas, bordes', 'hotkey': 'o', 'requires_texture': False },
    'dot':     { 'func': dotFragmentShader,      'label': 'Dot',     'desc': 'Halftone puntos',       'hotkey': 'p', 'requires_texture': False },
}

def build_keymap():
    """Construye un diccionario keycode -> (tipo, shader_key)."""
    keymap = {}
    for key, data in vertex_shaders.items():
        hot = data.get('hotkey')
        if hot:
            keymap[ord(hot)] = ('vertex', key)
    for key, data in fragment_shaders.items():
        hot = data.get('hotkey')
        if hot:
            # Letras en minúscula
            if len(hot) == 1:
                keymap[ord(hot)] = ('fragment', key)
    return keymap

def build_menu_lines():
    lines = ["--- Shaders Vertex (dinámico) ---"]
    for k, d in sorted(vertex_shaders.items(), key=lambda x: x[1]['hotkey']):
        lines.append(f"{d['hotkey']}: V-{d['label']} | {d['desc']}")
    lines.append("--- Shaders Fragment (dinámico) ---")
    for k, d in sorted(fragment_shaders.items(), key=lambda x: x[1]['hotkey']):
        tex = ' (tex)' if d.get('requires_texture') else ''
        lines.append(f"{d['hotkey']}: F-{d['label']}{tex} | {d['desc']}")
    return lines

def print_shader_menu():
    for line in build_menu_lines():
        print(line)

def handle_shader_key(keycode, model, renderer):
    """Toggle de vertex shaders y cadena de fragment shaders.

    Vertex: pulsar activa/desactiva.
    Fragment: agrega o quita de la cadena (orden = orden de activación).
    """
    if model is None:
        return False
    km = build_keymap()
    entry = km.get(keycode)
    if not entry:
        return False
    kind, shader_key = entry
    if kind == 'vertex':
        # Toggle: si ya está activo -> apagar
        current_key = getattr(model, 'vertexShaderKey', None)
        if current_key == shader_key:
            model.vertexShader = None
            model.vertexShaderKey = None
            print(f"Vertex shader '{shader_key}' desactivado (modo identidad).")
        else:
            data = vertex_shaders[shader_key]
            model.vertexShader = data['func']
            model.vertexShaderKey = shader_key
            print(f"Vertex shader activo: {data['label']}")
        return True
    # Fragment shaders (cadena)
    data = fragment_shaders[shader_key]
    func = data['func']
    if data.get('requires_texture'):
        tex = renderer.textures.get(id(model))
        if tex is None:
            print(f"Advertencia: '{data['label']}' requiere textura y el modelo no tiene una activa.")
        renderer.activeTexture = tex
        renderer.forceNoTexture = False
    else:
        renderer.forceNoTexture = False
    activated = model.toggle_fragment_shader(shader_key, func)
    chain_labels = [fragment_shaders[k]['label'] for k,_ in model.fragmentShaderChain]
    print(f"Fragment '{data['label']}' {'ON' if activated else 'OFF'} | Cadena: {chain_labels if chain_labels else 'vacía'}")
    return True
