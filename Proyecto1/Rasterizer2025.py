import pygame
from gl import Renderer, TRIANGLES
from objloader import OBJ
from objToModel import objToModel
from shaders import (vertexShader)  # Base shader para asignación inicial
from shaders_registry import print_shader_menu
from input_controller import InputController
from model_manager import ModelManager
from config import (
    SCREEN_DIMENSIONS,
    CAMERA_DISTANCE_START,
    CAMERA_START_POSITION,
    CAMERA_START_ROTATION,
    BACKGROUND_IMAGE,
    MODEL_SCALE,
    FOV,
    NEAR_PLANE,
    FAR_PLANE,
    MODEL_PRESETS,
)

# --- Importamos las matrices de rasterización ---
from MathLib import ProjectionMatrix, ViewportMatrix
from camera import Camera

"""Las constantes de configuración se importan ahora desde config.py"""

def inicializar_entorno():
    """Configura Pygame y el motor de renderizado."""
    pygame.init()
    canvas = pygame.display.set_mode(SCREEN_DIMENSIONS, pygame.SCALED)
    time_clock = pygame.time.Clock()
    pygame.mouse.set_visible(True)
    return canvas, time_clock

def cargar_activo(filepath, texpath):
    """Carga un modelo OBJ con su textura y lo prepara para el renderizado."""
    try:
        mesh_data = OBJ(filepath)
        model_entity = objToModel(mesh_data, texpath)
        model_entity.vertexShader = vertexShader
        
        # NUEVO: Calcular normales para iluminación
        model_entity.calculateNormals()
        print(f"Normales calculadas: {len(model_entity.normals)} normales generadas.")
        
        print(f"Éxito: Modelo '{filepath}' cargado con {len(mesh_data.vertices)} vértices y {len(mesh_data.faces)} caras.")
        return model_entity
        
    except Exception as e:
        print(f"Error fatal: Fallo al cargar el modelo o la textura: {e}")
        pygame.quit()
        exit()

## Eliminada función antigua de vectores de cámara: responsabilidad movida a InputController

if __name__ == "__main__":
    screen, clock = inicializar_entorno()
    graphics_engine = Renderer(screen)
    # Cargar fondo si se configuró
    try:
        if BACKGROUND_IMAGE:
            import os, pygame
            if os.path.isfile(BACKGROUND_IMAGE):
                graphics_engine.backgroundSurface = pygame.image.load(BACKGROUND_IMAGE)
                print(f"Imagen de fondo cargada: {BACKGROUND_IMAGE}")
            else:
                print(f"Advertencia: BACKGROUND_IMAGE no encontrada: {BACKGROUND_IMAGE}")
    except Exception as e:
        print(f"No se pudo cargar fondo: {e}")
    graphics_engine.primitiveType = TRIANGLES
    # Inicialización flexible de cámara: si CAMERA_START_POSITION está definido úsalo.
    try:
        cam_pos = CAMERA_START_POSITION if CAMERA_START_POSITION else (0,0,CAMERA_DISTANCE_START)
    except NameError:
        cam_pos = (0,0,CAMERA_DISTANCE_START)
    try:
        cam_rot = CAMERA_START_ROTATION if CAMERA_START_ROTATION else (0,0,0)
    except NameError:
        cam_rot = (0,0,0)
    camera = Camera(position=cam_pos, rotation=cam_rot)
    camera.sync_renderer(graphics_engine)
    model_manager = ModelManager(graphics_engine)

    # --- Carga multi-modelo desde MODEL_PRESETS ---
    from shaders_registry import vertex_shaders, fragment_shaders
    print("\nCargando modelos desde MODEL_PRESETS...")
    for preset in MODEL_PRESETS:
        try:
            base_tex = preset.get("texture")
            model = model_manager.load_model(
                preset["path"],
                texture_path=base_tex,
                scale=preset.get("scale", MODEL_SCALE),
                rotation=tuple(preset.get("rotation", (0,0,0))),
                translation=tuple(preset.get("translation", (0,0,0))),
                name=preset.get("name")
            )
            # Si hay textura base definida, cargarla también en el renderer para detección rápida
            if base_tex:
                try:
                    graphics_engine.loadTexture(base_tex, id(model))
                except Exception as _e:
                    print(f"No se pudo registrar textura base en renderer: {base_tex} -> {_e}")
            # Shaders
            vs_key = preset.get("vertexShader")
            if vs_key and vs_key in vertex_shaders:
                model.vertexShader = vertex_shaders[vs_key]['func']
                model.vertexShaderKey = vs_key
            fs_key = preset.get("fragmentShader")
            if fs_key and fs_key in fragment_shaders:
                model.fragmentShader = fragment_shaders[fs_key]['func']
                model.fragmentShaderKey = fs_key
            # Texturas adicionales
            for tex_def in preset.get("textures", []):
                tname = tex_def.get("name"); tpath = tex_def.get("path")
                if tname and tpath:
                    model.addTexture(tname, tpath)
            # Materiales
            for mat_def in preset.get("materials", []):
                mname = mat_def.get("name"); tex_ref = mat_def.get("texture"); color = mat_def.get("color")
                if mname:
                    model.addMaterial(mname, texture_name=tex_ref, color=color)
            # Remapeo
            remap = preset.get("material_remap", {})
            default_mat = preset.get("default_material")
            if remap or default_mat:
                alias_rules = []
                for key, target in remap.items():
                    for alias in key.split('|'):
                        alias_rules.append((alias.strip().lower(), target))
                counts = {}
                for i, original in enumerate(model.materialIndices):
                    chosen = None
                    if original and original != 'default':
                        lower = original.lower()
                        for alias, target in alias_rules:
                            if alias and alias in lower:
                                chosen = target; break
                    if not chosen:
                        chosen = default_mat if default_mat else original
                    model.materialIndices[i] = chosen
                    counts[chosen] = counts.get(chosen, 0) + 1
                print(f"Remapeo materiales ({preset['path']}): {counts}")
                # Forzar que no queden materiales sin mapear si se definió default
                if default_mat:
                    try:
                        model.ensure_complete_material_assignment(default_mat)
                    except Exception:
                        pass
                # Reporte de cobertura
                try:
                    rep = model.material_coverage_report()
                    print(f"Cobertura texturas: {rep['textured_triangles']}/{rep['total_triangles']} ({rep['percent_textured']:.1f}%)")
                except Exception:
                    pass
            if model.fragmentShader is None:
                graphics_engine.forceNoTexture = True
            shown_name = model.name if getattr(model, 'name', None) else preset['path']
            print(f"Modelo cargado: {shown_name}")
        except Exception as e:
            print(f"Error cargando preset {preset.get('path')}: {e}")
    print("-------------------------------------------\n")

    print("\n--- Controles del programa ---")
    print("W / S: Mover la cámara arriba/abajo")
    print("UP / DOWN: Mover la cámara adelante/atrás")
    print("LEFT / RIGHT: Mover la cámara izquierda/derecha")
    print("A / D: Rotar la cámara (yaw)")
    print("Q / E: Ladear la cámara (roll)")
    print("R / F: Inclinar la cámara (pitch)")
    print("Clic Izquierdo + Mover Ratón: Girar la cámara libremente")
    print("Rueda del Ratón: Acercar y alejar")
    print("1: Puntos | 2: Líneas | 3: Triángulos (colores aleatorios por triángulo sin textura)")
    print("4: Fragment Textura | 5: Fragment Rainbow | 6: Fragment Toon + Textura")
    print_shader_menu()
    print("TAB / SHIFT+TAB: Cambiar modelo activo")
    print("ENTER: Guardar captura de pantalla (BMP)")
    print("ESC: Salir del programa")
    print("Modo inicial: Triángulos; usa fragment shaders para texturas (4 Texture / 6 Toon / x Slice / 5 Rainbow / m Math). TAB cambia modelo.")
    print("------------------------------\n")

    aspect_ratio = SCREEN_DIMENSIONS[0] / SCREEN_DIMENSIONS[1]
    graphics_engine.projectionMatrix = ProjectionMatrix(FOV, aspect_ratio, NEAR_PLANE, FAR_PLANE)
    print("Matriz de Proyección calculada.")
    graphics_engine.viewportMatrix = ViewportMatrix(SCREEN_DIMENSIONS[0], SCREEN_DIMENSIONS[1])
    print("Matriz de Viewport calculada.")

    input_controller = InputController(graphics_engine, camera, model_manager)
    while input_controller.running:
        deltaTime = clock.tick(60) / 1000.0
        if not input_controller.process_events(deltaTime): break
        input_controller.update_held_keys(deltaTime)
        graphics_engine.glClear(); graphics_engine.glRender(); pygame.display.flip()
    pygame.quit()