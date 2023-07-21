from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math

# Ваши функции для создания мозаики

def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))  # skipping '#' character in hex color

def closest_color(color, palette):
    distances = [sum((col - tar) ** 2 for col, tar in zip(c, color)) for c in palette]
    return palette[min(range(len(distances)), key=distances.__getitem__)]

def create_selfpixel_tile(color, size):
    base = Image.new('RGB', (size, size), color)
    draw = ImageDraw.Draw(base)

    shadow_color = (35, 35, 35)
    draw.ellipse([(size // 4 + 1, size // 4 + 1), (3 * size // 4 + 1, 3 * size // 4 + 1)], fill=shadow_color)
    base = base.filter(ImageFilter.GaussianBlur(radius=2))
    draw = ImageDraw.Draw(base)
    draw.ellipse([(size // 4, size // 4), (3 * size // 4, 3 * size // 4)], fill=color)

    return base

def determine_tile_size(image, num_tiles):
    width, height = image.size
    total_pixels = width * height
    tile_size = math.isqrt(total_pixels // num_tiles)
    return tile_size

def selfpixel_mosaic(image_path, num_tiles, palette_hex, mosaic_size):
    palette_rgb = [hex_to_rgb(color) for color in palette_hex]

    image = Image.open(image_path).convert('RGB')
    image = image.resize(mosaic_size)
    tile_size = determine_tile_size(image, num_tiles)
    new_image = Image.new('RGB', (image.width // tile_size * tile_size, image.height // tile_size * tile_size))

    for i in range(0, new_image.width, tile_size):
        for j in range(0, new_image.height, tile_size):
            tile = image.crop((i, j, i + tile_size, j + tile_size))
            avg_color = tuple(np.array(tile).mean(axis=(0, 1)).astype(int))
            closest_color_in_palette = closest_color(avg_color, palette_rgb)
            selfpixel_tile = create_selfpixel_tile(closest_color_in_palette, tile_size)
            new_image.paste(selfpixel_tile, (i, j))

    return new_image

# Создание мозаики и сохранение её в изображение
mosaic_size = (1287, 2145)
palette_hex_original = ['#f5e9d5', '#514c53', '#ddddda', '#c5c6be', '#000000']

mosaic_image = selfpixel_mosaic('img.png', 19305, palette_hex_original, mosaic_size)
mosaic_image.save('classic.png')
