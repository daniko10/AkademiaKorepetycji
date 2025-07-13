import os
import gzip
from PIL import Image

def compress_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    if ext in ('.jpg', '.jpeg', '.png'):
        try:
            img = Image.open(filepath)
            img.save(filepath,
                     optimize=True,
                     quality=70)
        except Exception as e:
            print("Image compress error:", e)

    else:
        gz_path = filepath + '.gz'
        try:
            with open(filepath, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
                f_out.writelines(f_in)
            os.replace(gz_path, filepath)
        except Exception as e:
            print("GZIP compress error:", e)
