from PIL import Image
from fpdf import FPDF
import numpy as np
from math import sqrt

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

def colorize_tiles(tiles, palette):
    return [closest_color(np.array(tile).mean(axis=(0, 1)).astype(int), palette) for tile in tiles]

def blocks_to_pdf(blocks, filename, blocks_per_page, logo_path, logo_width, logo_height, logo_x, logo_y):
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

            group_x = (i % blocks_per_row) * group_width + spacing
            group_y = ((i % blocks_per_page) // blocks_per_row) * group_height + spacing

            # Move the entire block down
            group_y += y_offset

            # Draw colored tiles
            for t, color in enumerate(block):
                x = group_x + 20 + (t % 9) * (tile_size + tile_spacing)
                y = group_y + 10 + (t // 9) * (tile_size + tile_spacing)
                pdf.set_fill_color(*color)
                pdf.rounded_rect(x, y, tile_size, tile_size, 0.5, 'F')  # 2mm rounded corners

            # Draw tile numbers (top side)
            pdf.set_font("Arial", style='B', size=font_size)
            pdf.set_text_color(0, 0, 0)  # black color
            for t in range(9):
                x = group_x + 19 + (t * (tile_size + tile_spacing)) + (tile_size - pdf.get_string_width(str(t + 1))) / 2
                y = group_y + 10 - font_size
                pdf.set_xy(x, y)
                pdf.cell(0, 0, str(t + 1), ln=False)

            # Draw tile numbers (bottom side)
            pdf.set_font("Arial", style='B', size=font_size)
            pdf.set_text_color(0, 0, 0)  # black color
            for t in range(9):
                x = group_x + 19 + (t * (tile_size + tile_spacing)) + (tile_size - pdf.get_string_width(str(t + 1))) / 2
                y = group_y + 8 + (15 * (tile_size + tile_spacing))
                pdf.set_xy(x, y)
                pdf.cell(0, 0, str(t + 1), ln=False)

            # Draw tile numbers (left side)
            pdf.set_font("Arial", style='B', size=font_size)
            pdf.set_text_color(0, 0, 0)  # black color
            for t in range(15):
                x = group_x + 18 - pdf.get_string_width(str(t + 1))
                y = group_y + 9.5 + (t * (tile_size + tile_spacing)) + (tile_size - font_size) / 2
                pdf.set_xy(x, y)
                pdf.cell(0, 0, str(t + 1), ln=False)

            # Draw tile numbers (right side)
            pdf.set_font("Arial", style='B', size=font_size)
            pdf.set_text_color(0, 0, 0)  # black color
            for t in range(15):
                x = group_x + 19 + 9 * (tile_size + tile_spacing)
                y = group_y + 9.5 + (t * (tile_size + tile_spacing)) + (tile_size - font_size) / 2
                pdf.set_xy(x, y)
                pdf.cell(0, 0, str(t + 1), ln=False)

            # Draw line
            pdf.set_draw_color(0, 0, 0)  # color for the line
            pdf.set_line_width(0.7)  # set line thickness to 2mm
            line_length = group_height - 6
            pdf.line(group_x + 15, group_y + 8, group_x + 15, group_y + line_length)

            # Draw number with a cell to control the height
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


image_path = 'men.png'
logo_path = 'self-pixel.png'
logo_width = 50
logo_height = 20
logo_x = 10
logo_y = 5
palette_hex = ['#f5e9d5', '#ddddda', '#c5c6be', '#514c53', '#3a3837', '#000000']
palette_rgb = [hex_to_rgb(color) for color in palette_hex]
image = Image.open(image_path).convert('RGB')
blocks = split_image_into_blocks(image, 13, 11)
tiles = [split_block_into_tiles(block, 9, 15) for block in blocks]
colorized_blocks = [colorize_tiles(block_tiles, palette_rgb) for block_tiles in tiles]
blocks_to_pdf(colorized_blocks, 'blocks.pdf', 12, logo_path, logo_width, logo_height, logo_x, logo_y)
