import os
from PIL import Image
from flask import abort
from app import db

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

def get_or_404(model, ident):
    obj = db.session.get(model, ident)
    if obj is None:
        abort(404)
    return obj