from PIL import Image
import glob, os

for image_filename in glob.glob("sprites/*.png"):
    print(f'Creating sprite from {image_filename}')

    file_name = os.path.splitext(os.path.basename(image_filename))[0]
    img = Image.open('sprites/' + file_name + '.png')
    pix = img.load()

    width, height = img.size

    for y in range(height):
        pixel_row = ''
        for x in range(width):
            if (pix[x, y] == (255, 255, 255, 255) or pix[x, y] == (255, 255, 255)):
                pixel_row += '0'
            else:
                pixel_row += '1'
                    
        print(f"sprite_data[{width*(y+1)-1: <3}: {width*y: <3}] <= {width}'b{pixel_row[::-1]};")
