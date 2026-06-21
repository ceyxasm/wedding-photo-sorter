import os, json
from PIL import Image, ImageOps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, 'images')
THUMB_DIR = os.path.join(BASE_DIR, 'thumbs')
REVIEW_FILE = os.path.join(BASE_DIR, 'review_state.json')

os.makedirs(THUMB_DIR, exist_ok=True)

if not os.path.exists(REVIEW_FILE):
    print('review_state.json not found — start the app first so it creates the review pool.')
    exit(1)

with open(REVIEW_FILE) as f:
    review = json.load(f)

pool = review['pool']
total = len(pool)
print(f'Generating thumbnails for {total} images...\n')

skipped = 0
done = 0
failed = 0

for i, filename in enumerate(pool, 1):
    src = os.path.join(IMAGE_DIR, filename)
    thumb_path = os.path.join(THUMB_DIR, filename)
    os.makedirs(os.path.dirname(thumb_path), exist_ok=True)

    if os.path.exists(thumb_path):
        skipped += 1
        print(f'  [{i}/{total}] skip  {filename}')
        continue

    try:
        with Image.open(src) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((1200, 1200), Image.LANCZOS)
            img.save(thumb_path, 'JPEG', quality=75, optimize=True)
        done += 1
        print(f'  [{i}/{total}] ok    {filename}')
    except Exception as e:
        failed += 1
        print(f'  [{i}/{total}] FAIL  {filename}  ({e})')

print(f'\nDone. generated={done}  skipped={skipped}  failed={failed}')
