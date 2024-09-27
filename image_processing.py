from PIL import Image, ImageDraw
import numpy as np

def create_circular_image(image, size):
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)

    output = image.copy()
    output = output.resize((size, size), Image.LANCZOS)
    output.putalpha(mask)

    background = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    background.paste(output, (0, 0), output)
    return background

def rotate_image(image, angle):
    return image.rotate(angle, resample=Image.BICUBIC, expand=False)