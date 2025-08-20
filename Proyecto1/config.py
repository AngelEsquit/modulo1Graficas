# Configuración centralizada del rasterizador
# Puedes modificar estos valores sin tocar el loop principal.

# Dimensiones de pantalla
DIMENSION = 1024
SCREEN_DIMENSIONS = (DIMENSION, DIMENSION)

# Cámara inicial
CAMERA_DISTANCE_START = 10
CAMERA_START_ROTATION = [-15, 15, 0]  # pitch, yaw, roll
# Nueva forma opcional: posición inicial explícita (x, y, z). Si la modificas,
# Rasterizer2025 usará esta en vez de (0,0,CAMERA_DISTANCE_START).
CAMERA_START_POSITION = (1.5, 5, 6.5)
    
# Imagen de fondo opcional (ruta relativa). Si es None o cadena vacía, se usa color sólido.
BACKGROUND_IMAGE = "./background/Escenario2.jpg"

# Escala por defecto de modelos
MODEL_SCALE = 0.05

# Parámetros de proyección
FOV = 60
NEAR_PLANE = 0.1
FAR_PLANE = 100

# Velocidades y sensibilidad
MOVE_SPEED = 1            # unidades / segundo
ROTATION_SPEED = 15       # grados / segundo
MOUSE_SENSITIVITY = 0.1     # factor multiplicador para yaw/pitch
ZOOM_SPEED_FACTOR = 0.3     # factor relativo a MOVE_SPEED


MODEL_PRESETS = [
    # {
    #     "path": "models/yoshi.obj",
    #     "name": "Yoshi",
    #     "texture": "textures/Yoshi/yoshi.png",
    #     "scale": 3.25,
    #     "rotation": [0, 180, 0],
    #     "translation": [4, -0.7, 2.5],
    #     "vertexShader": "normal",
    #     "fragmentShader": None,
    #     "textures": [
    #         {"name": "yoshi_green",  "path": "textures/Yoshi/yoshi.png"}
    #     ],
    #     "materials": [
    #         {"name": "mat_body",  "texture": "yoshi_green"}
    #     ],
    #     "material_remap": {
    #         "yoshi_green": "mat_body"
    #     },
    #     "default_material": "mat_body"
    # },
    {
        "path": "models/crashbandicoot.obj",
        "name": "Crash",
        "texture": "textures/Crash/color_pallete.png",
        "scale": 0.015,
        "rotation": [0, -25, 0],
        "translation": [1.5, 0.35, 0],
        "vertexShader": "normal",
        "fragmentShader": "origami",
        "textures": [
            {"name": "primary", "path": "textures/Crash/color_pallete.png"},
            {"name": "shoes",   "path": "textures/Crash/shoes.png"},
            {"name": "back",    "path": "textures/Crash/back.png"}
        ],
        "materials": [
            {"name": "mat_primary", "texture": "primary"},
            {"name": "mat_shoes",   "texture": "shoes"},
            {"name": "mat_back",    "texture": "back"}
        ],
        "material_remap": {
            "shoe|zapato|feet": "mat_shoes",
            "back|shell": "mat_back"
        },
        "default_material": "mat_primary"
    },
    
    {
        "path": "models/Grass/10438_Circular_Grass_Patch_v1_iterations-2.obj",
        "name": "Grass",
        "texture": "models/Grass/grass.jpg",
        "scale": 0.05,
        "rotation": [-90, 0, 0],
        "translation": [0.35, 0, 0],
        "vertexShader": "normal",
        "fragmentShader": "nmap",
        "textures": [
            {"name": "diffuse", "path": "models/Grass/grass.jpg"}
        ],
        "materials": [
            {"name": "mat_grass", "texture": "diffuse"}
        ],
        "material_remap": {},
        "default_material": "mat_grass"
    },
    {
        "path": "models/Scorbunny/Scorbunny.obj",
        "name": "Scorbunny",
        "texture": "",  # dejamos vacío para que el loader MTL maneje materiales
        "scale": 0.2,
        "rotation": [0, -90, 0],
        "translation": [0, 0.5, -0.05],
        "vertexShader": "normal",
        "fragmentShader": "math",
        "textures": [],  # no forzamos texturas externas
        "materials": [],
        "material_remap": {},
        "default_material": ""  # no se fuerza remap; se usan nombres MTL
    },
    {
        "path": "models/Tree/Tree.obj",
        "name": "Tree",
        # Usamos una textura base para permitir shader toon (genera UVs procedurales si el OBJ no trae vt)
        "texture": "textures/Tree/texture_tree.png",
        "scale": 0.3,
        "rotation": [0, 0, 0],
        "translation": [-0.35, 0.45, -1.05],
        "vertexShader": "normal",
        "fragmentShader": "toon",  # Toon aprovecha material_color; textura sirve de soporte UV
        "textures": [
            {"name": "tree_base", "path": "textures/Tree/texture_tree.png"}
        ],
        # Colores desde el MTL (Kd). Ajustables si quieres tonos más naturales.
        "materials": [
            {"name": "mat_leavesA", "texture": "tree_base", "color": [0.328938, 0.800000, 0.156409]},
            {"name": "mat_leavesB", "texture": "tree_base", "color": [0.266614, 0.644471, 0.127680]},
            {"name": "mat_leavesC", "texture": "tree_base", "color": [0.204762, 0.580520, 0.089339]},
            {"name": "mat_trunk",   "texture": "tree_base", "color": [0.800000, 0.145528, 0.060455]}
        ],
        # Remapeo: coincidencia por substring (case-insensitive)
        "material_remap": {
            "branch_color.003": "mat_leavesC",
            "branch_color.001": "mat_leavesB",
            "branch_color": "mat_leavesA",
            "trunk_color": "mat_trunk"
        },
        "default_material": "mat_leavesA"
    },
    {
        "path": "models/Pikachu/Pikachu.obj",
        "name": "Pikachu",
        # No hay MTL presente aunque el OBJ lo referencia, así que definimos manualmente
        # las texturas y mapeos de materiales basados en los nombres de 'usemtl'.
        "texture": "textures/Pikachu/PikachuDh.png",  # textura principal (cuerpo)
        "scale": 0.3,  # ajusta si queda muy grande / pequeño
        "rotation": [0, 60, 0],
        "translation": [-1, 0.55, 0.95],  # separado un poco de Scorbunny
        "vertexShader": "normal",
        "fragmentShader": "slice",  # cada material tiene su propia textura
        "textures": [
            {"name": "pikachu_body",  "path": "textures/Pikachu/PikachuDh.png"},
            {"name": "pikachu_eye",   "path": "textures/Pikachu/PikachuEyeDh.png"},
            {"name": "pikachu_cheek", "path": "textures/Pikachu/PikachuHohoDh.png"},
            {"name": "pikachu_mouth", "path": "textures/Pikachu/PikachuMouthDh.png"}
        ],
        "materials": [
            {"name": "mat_body",  "texture": "pikachu_body"},
            {"name": "mat_eye",   "texture": "pikachu_eye"},
            {"name": "mat_cheek", "texture": "pikachu_cheek"},
            {"name": "mat_mouth", "texture": "pikachu_mouth"}
        ],
        # Los nombres en el OBJ son como: PikachuDh_PikachuDh.png, PikachuEyeDh_PikachuEyeDh.png, etc.
        # Usamos patrones para redirigirlos.
        "material_remap": {
            "Eye|EyeDh": "mat_eye",
            "Hoho|Cheek|HohoDh": "mat_cheek",
            "Mouth|MouthDh": "mat_mouth",
            "PikachuDh": "mat_body"  # fallback principal
        },
        "default_material": "mat_body"
    }, 
    {
        "path": "models/piedra.obj",
        "name": "Piedra",
        "texture": "textures/Piedra/diffuse map.png",  # difuso principal
        "scale": 0.65,
        "rotation": [0, 35, 0],
        "translation": [0.05, 0.5, 1.2],
        "vertexShader": "normal",
        "fragmentShader": "nmap",  # usa normal mapping
        "textures": [
            {"name": "stone_diffuse",   "path": "textures/Piedra/diffuse map.png"},
            {"name": "stone_normal",    "path": "textures/Piedra/normal map.png"},
            {"name": "stone_ao",        "path": "textures/Piedra/cavity-ao map.png"},
            {"name": "stone_roughness", "path": "textures/Piedra/roughness map.png"}
        ],
        "materials": [
            {"name": "mat_stone", "texture": "stone_diffuse", "normal_map": "stone_normal", "ao_map": "stone_ao", "roughness_map": "stone_roughness"}
        ],
        "material_remap": {},
        "default_material": "mat_stone"
    },

]

# Flags globales de render/debug (extensibles)
RANDOM_TRIANGLE_COLORS = True   # Colores RGB persistentes por triángulo cuando no hay fragment shader