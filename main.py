from PIL import Image
from fpdf import FPDF
import numpy as np
from math import sqrt
import json

class PDF(FPDF):
    def rounded_rect(self, x, y, w, h, r, style = ''):
        _k = self.k
        hp = self.h
        if(style=='F'):
            op='f'
        elif(style=='FD' or style=='DF'):
            op='B'
        else:
            op='S'
        MyArc = 4/3 * (sqrt(2) - 1)
        self._out('%.2F %.2F m' % ((x+r)*_k,(hp-y)*_k ))
        self._out('%.2F %.2F l' % ((x+w-r)*_k,(hp-y)*_k ))
        self._out('%.2F %.2F %.2F %.2F %.2F %.2F c' % ((x+w-r+MyArc*r)*_k,(hp-y)*_k,(x+w)*_k,(hp-y+r-MyArc*r)*_k,(x+w)*_k,(hp-y+r)*_k))
        self._out('%.2F %.2F l' % ((x+w)*_k,(hp-y+h-r)*_k))
        self._out('%.2F %.2F %.2F %.2F %.2F %.2F c' % ((x+w)*_k,(hp-y+h-r+MyArc*r)*_k,(x+w-r+MyArc*r)*_k,(hp-y+h)*_k,(x+w-r)*_k,(hp-y+h)*_k))
        self._out('%.2F %.2F l' % ((x+r)*_k,(hp-y+h)*_k))
        self._out('%.2F %.2F %.2F %.2F %.2F %.2F c' % ((x+r-MyArc*r)*_k,(hp-y+h)*_k,x*_k,(hp-y+h-r+MyArc*r)*_k,x*_k,(hp-y+h-r)*_k))
        self._out('%.2F %.2F l' % (x*_k,(hp-y+r)*_k))
        self._out('%.2F %.2F %.2F %.2F %.2F %.2F c ' % (x*_k,(hp-y+r-MyArc*r)*_k,(x+r-MyArc*r)*_k,(hp-y)*_k,(x+r)*_k,(hp-y)*_k))
        self._out(op)

def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))

def closest_color(color, palette):
    distances = [sum((col - tar) ** 2 for col, tar in zip(c, color)) for c in palette]
    return palette[min(range(len(distances)), key=distances.__getitem__)]

def split_image_into_blocks(image, blocks_per_row, blocks_per_column):
    min_side = min(image.size)
    block_width = block_height = min_side // min(blocks_per_row, blocks_per_column)
    return [image.crop((i*block_width, j*block_height, (i+1)*block_width, (j+1)*block_height))
            for j in range(blocks_per_column) for i in range(blocks_per_row)]

def split_block_into_tiles(block, tiles_per_row, tiles_per_column):
    min_side = min(block.size)
    tile_size = min_side // min(tiles_per_row, tiles_per_column)
    padding = 1
    tiles = []
    for i in range(tiles_per_column):
        for j in range(tiles_per_row):
            tile = block.crop((j*tile_size+padding, i*tile_size+padding, (j+1)*tile_size-padding, (i+1)*tile_size-padding))
            tiles.append(tile)
    return tiles

palette_hex = ['#f5e9d5', '#514c53', '#ddddda', '#c5c6be', '#000000']
palette_rgb = [hex_to_rgb(color) for color in palette_hex]

color_to_letter = {
    palette_rgb[0]: 'M',
    palette_rgb[1]: 'P',
    palette_rgb[2]: 'G',
    palette_rgb[3]: 'S',
    palette_rgb[4]: 'B',
}

def colorize_tiles(tiles, palette):
    colors = [closest_color(np.array(tile).mean(axis=(0, 1)).astype(int), palette) for tile in tiles]
    # convert colors to letters
    return [color_to_letter[color] for color in colors]

letter_to_color = {v: k for k, v in color_to_letter.items()}

def count_consecutive_same_elements(lst):
    result = []
    prev_element = None
    count = 1
    for element in lst:
        if element == prev_element:
            count += 1
        else:
            if prev_element is not None:
                result.extend([prev_element]*count)
            prev_element = element
            count = 1
    if prev_element is not None:
        result.extend([prev_element]*count)

    # Обработка случая, когда весь блок одного цвета
    if len(set(result)) == 1:
        return list(range(1, len(result) + 1))

    return result

def add_original_image_page(pdf, image_path):
    try:
        img = Image.open(image_path)
        img.verify()
    except (IOError, SyntaxError) as e:
        print(f'Invalid image file: {e}')
        return

    pdf.add_page()
    pdf.image(image_path, x=40, y=40, w=125, h=200)
    

def create_tiles_data(blocks):
    tiles_data = []
    for block in blocks:
        block_data = []
        for t, letter in enumerate(block):
            tile_data = {"color": list(letter_to_color[letter]), "number": t + 1, "letter": letter}
            block_data.append(tile_data)

        tiles_data.append(block_data)

    return tiles_data

def save_tiles_to_json(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file)


def blocks_to_pdf(blocks, filename, blocks_per_page, logo_path, logo_width, logo_height, logo_x, logo_y, image_path):
    pdf = PDF(orientation='P', unit='mm', format='A4')
    blocks_per_row = 3
    blocks_per_column = blocks_per_page // blocks_per_row
    pages = (len(blocks) - 1) // blocks_per_page + 1

    group_width = group_height = min((pdf.w - 30) / blocks_per_row, (pdf.h - 30) / blocks_per_column)
    spacing = 15

    tile_size = (group_height - 20) / max(9, 15)  # Assuming 9 tiles per row and 15 per column in a block
    tile_spacing = 0.5  # spacing between tiles

    font_size = 4  # Adjust the font size as needed

    # Define the y offset to move the entire section down
    y_offset = 20

    # Add the original image page
    add_original_image_page(pdf, image_path)

    tiles_data = create_tiles_data(blocks)
    save_tiles_to_json(tiles_data, 'tiles.json')

    for p in range(pages):
        pdf.add_page()

        # Move the entire section down
        pdf.set_y(pdf.get_y() + y_offset)

        # Add the block range in the top right corner
        block_range = f"{blocks_per_page * p + 1}-{min(blocks_per_page * (p + 1), len(blocks))}"
        pdf.set_font("Arial", style='B', size=35)
        pdf.set_text_color(0, 0, 0)  # black color
        pdf.cell(0, -30, txt=block_range, align="R", ln=True)

        # Add the logo
        pdf.image(logo_path, x=logo_x, y=logo_y, w=logo_width, h=logo_height)

        for i in range(blocks_per_page * p, min(blocks_per_page * (p + 1), len(blocks))):
            block = blocks[i]
            counted_block = count_consecutive_same_elements(block)

            group_x = (i % blocks_per_row) * group_width + spacing
            group_y = ((i % blocks_per_page) // blocks_per_row) * group_height + spacing

            # Перемещаем весь блок вниз
            group_y += y_offset

            counter = 0
            previous_tile = None
            # Рисуем цветные плитки
            for t, letter in enumerate(block):
                x = group_x + 20 + (t % 9) * (tile_size + tile_spacing)
                y = group_y + 10 + (t // 9) * (tile_size + tile_spacing)
                color = letter_to_color[letter]   # Исправление здесь, сопоставляем букву с цветом

                # Рисуем плитку
                pdf.set_fill_color(*color)
                pdf.rounded_rect(x, y, tile_size, tile_size, 0.5, 'F')  # Закругленные углы 2 мм

            # Рисуем номера на плитках
            counter = 1
            previous_tile = None
            for t, letter in enumerate(block):
                x = group_x + 19.5 + (t % 9) * (tile_size + tile_spacing)
                y = group_y + 7 + (t // 9) * (tile_size + tile_spacing)

                # Сбрасываем счетчик, когда цвет плитки меняется или когда начинается новый ряд
                if previous_tile != letter or (t % 9 == 0 and t != 0):
                    counter = 1
                previous_tile = letter

                # Рисуем номер в верхнем правом углу плитки
                pdf.set_font("Arial", style='B', size=font_size - 1)
                pdf.set_text_color(129, 129, 129)  # черный цвет
                pdf.set_xy(x + tile_size - pdf.get_string_width(str(counter)) - 1, y + 1)
                pdf.cell(0, 0, str(counter), ln=False)

                # Увеличиваем счетчик
                counter += 1


            # Рисуем буквы на плитках
            for t, letter in enumerate(block):
                x = group_x + 18.5 + (t % 9) * (tile_size + tile_spacing)
                y = group_y + 6 + (t // 9) * (tile_size + tile_spacing)

                # Рисуем букву на плитке
                pdf.set_font("Arial", style='B', size=font_size)
                pdf.set_text_color(129, 129, 129)  # серый цвет
                pdf.set_xy(x + tile_size / 2 - pdf.get_string_width(letter) / 2, y + tile_size / 2 + font_size / 2)
                pdf.cell(0, 0, letter, ln=False)

            # Рисуем номера плиток (верхняя сторона)
            pdf.set_font("Arial", style='B', size=font_size)
            pdf.set_text_color(0, 0, 0)  # черный цвет
            for t in range(9):
                x = group_x + 19 + (t * (tile_size + tile_spacing)) + (tile_size - pdf.get_string_width(str(t + 1))) / 2
                y = group_y + 10 - font_size
                pdf.set_xy(x, y)
                pdf.cell(0, 0, str(t + 1), ln=False)

            # Рисуем номера плиток (нижняя сторона)
            pdf.set_font("Arial", style='B', size=font_size)
            pdf.set_text_color(0, 0, 0)  # черный цвет
            for t in range(9):
                x = group_x + 19 + (t * (tile_size + tile_spacing)) + (tile_size - pdf.get_string_width(str(t + 1))) / 2
                y = group_y + 8 + (15 * (tile_size + tile_spacing))
                pdf.set_xy(x, y)
                pdf.cell(0, 0, str(t + 1), ln=False)

            # Рисуем номера плиток (левая сторона)
            pdf.set_font("Arial", style='B', size=font_size)
            pdf.set_text_color(0, 0, 0)  # черный цвет
            for t in range(15):
                x = group_x + 18 - pdf.get_string_width(str(t + 1))
                y = group_y + 9.5 + (t * (tile_size + tile_spacing)) + (tile_size - font_size) / 2
                pdf.set_xy(x, y)
                pdf.cell(0, 0, str(t + 1), ln=False)

            # Рисуем номера плиток (правая сторона)
            pdf.set_font("Arial", style='B', size=font_size)
            pdf.set_text_color(0, 0, 0)  # черный цвет
            for t in range(15):
                x = group_x + 19 + 9 * (tile_size + tile_spacing)
                y = group_y + 9.5 + (t * (tile_size + tile_spacing)) + (tile_size - font_size) / 2
                pdf.set_xy(x, y)
                pdf.cell(0, 0, str(t + 1), ln=False)

            # Рисуем линию
            pdf.set_draw_color(0, 0, 0)  # цвет линии
            pdf.set_line_width(0.7)  # толщина линии 2 мм
            line_length = group_height - 6
            pdf.line(group_x + 15, group_y + 8, group_x + 15, group_y + line_length)

            # Рисуем номер с ячейкой для контроля высоты
            pdf.set_font("Arial", style='B', size=16)

            number_length = len(str(i+1))
            if number_length == 1:
                pdf.set_xy(group_x + 9, group_y - 2)
            elif number_length == 2:
                pdf.set_xy(group_x + 6, group_y - 2)
            elif number_length == 3:
                pdf.set_xy(group_x + 3, group_y - 2)

            pdf.cell(0, 25, txt=str(i+1), ln=True)

    pdf.output(filename)


image_path = 'classic.png'
logo_path = 'self-pixel.png'
logo_width = 50
logo_height = 25
logo_x = 10
logo_y = 5

image = Image.open(image_path).convert('RGB')
blocks = split_image_into_blocks(image, 13, 11)
tiles = [split_block_into_tiles(block, 9, 15) for block in blocks]
colorized_blocks = [colorize_tiles(block_tiles, palette_rgb) for block_tiles in tiles]
blocks_to_pdf(colorized_blocks, 'blocks.pdf', 12, logo_path, logo_width, logo_height, logo_x, logo_y, image_path)