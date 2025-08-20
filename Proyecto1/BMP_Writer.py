import struct


def GenerateBMP(filename: str, width: int, height: int, byteDepth: int, colorBuffer: list[list[tuple[int, int, int]]]) -> None:
    """
    Genera un archivo BMP a partir de un buffer de color.
    
    Parámetros:
        filename (str): Nombre del archivo BMP a crear.
        width (int): Ancho de la imagen en píxeles.
        height (int): Alto de la imagen en píxeles.
        byteDepth (int): Profundidad de color en bytes por píxel (por ejemplo, 3 para RGB).
        colorBuffer (list): Buffer de color, lista bidimensional con tuplas (R, G, B).
    """

    def char(c: str) -> bytes:
        # Devuelve el carácter como un byte (1 byte)
        return struct.pack("<c", c.encode("ascii"))

    def word(w: int) -> bytes:
        # Devuelve el entero como palabra (2 bytes, little endian)
        return struct.pack("<H", w)

    def dword(d: int) -> bytes:
        # Devuelve el entero como doble palabra (4 bytes, little endian)
        return struct.pack("<L", d)

    # Abrimos el archivo en modo binario para escritura
    with open(filename, "wb") as file:
        # --- Encabezado BMP (Bitmap File Header) ---
        file.write(char("B"))  # Identificador BMP, primer carácter
        file.write(char("M"))  # Identificador BMP, segundo carácter
        # Tamaño total del archivo en bytes: header + info header + datos de imagen
        file.write(dword(14 + 40 + (width * height * byteDepth)))
        file.write(dword(0))  # Reservado, siempre 0
        file.write(dword(14 + 40))  # Offset donde empiezan los datos de la imagen

        # --- Encabezado de información (DIB Header) ---
        file.write(dword(40))  # Tamaño del encabezado de información (40 bytes)
        file.write(dword(width))  # Ancho de la imagen
        file.write(dword(height))  # Alto de la imagen
        file.write(word(1))  # Número de planos de color, siempre 1
        file.write(word(byteDepth * 8))  # Bits por píxel (profundidad de color)
        file.write(dword(0))  # Compresión (0 = sin compresión)
        file.write(dword(width * height * byteDepth))  # Tamaño de los datos de la imagen
        file.write(dword(0))  # Resolución horizontal (pixeles por metro, opcional)
        file.write(dword(0))  # Resolución vertical (pixeles por metro, opcional)
        file.write(dword(0))  # Número de colores en la paleta (0 = 2^n)
        file.write(dword(0))  # Colores importantes (0 = todos)

        # --- Datos de la imagen (Color table) ---
        # Se recorren los píxeles de la imagen y se escriben en formato BMP (B, G, R)
        # Cada fila en BMP debe estar alineada a múltiplos de 4 bytes (padding)
        row_stride = width * byteDepth
        padding = (4 - (row_stride % 4)) % 4
        pad_bytes = b"\x00" * padding

        for y in range(height):
            for x in range(width):
                color = colorBuffer[x][y]
                # Aceptar color como lista/tuple de enteros o numpy.uint8
                # Orden de salida BMP: B,G,R
                bgr = []
                for comp in reversed(color):
                    # Convertir a int por si es numpy.uint8
                    val = int(comp)
                    if val < 0: val = 0
                    if val > 255: val = 255
                    bgr.append(val)
                file.write(bytes(bgr))
            if padding:
                file.write(pad_bytes)
