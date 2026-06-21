# wedding-photo-sorter

A local web app for culling large sets of wedding photos down to a final selection across multiple passes. Built for speed — keyboard-driven, state-persisted, mobile-friendly reviewer flow.

## How it works

1. Extract all your photos into an `images/` folder
2. Run the app — go through photos one by one, `Enter` to keep, `Space` to skip
3. After each pass, start the next pass from only the selected photos
4. Repeat until you're happy with the count
5. Share a reviewer link with someone else (via ngrok) so they can vote on your final selection from their phone
6. Export the final accepted photos to an `accepted/` folder

## Setup

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage

```bash
./run.sh
```

Open [http://localhost:8080](http://localhost:8080) in your browser.

### Keyboard shortcuts (culling UI)

| Key | Action |
|-----|--------|
| `Enter` | Select image |
| `Space` | Skip image |
| `←` | Go back |

### Multi-pass flow

- Each pass shows only the images you selected in the previous pass
- Counter always shows how many selected so far
- Progress is saved after every keypress — safe to quit and resume anytime
- When a pass is complete, click **Start Next Pass**

### Adding missed photos mid-way

If you forgot a batch of photos after completing a pass, extract them into `images/` and click **+ Add More Images** on the completion screen. It creates a supplemental pass for just the new photos, then merges both selections when you start the next pass.

## Reviewer flow (mobile)

Once you have a final selection, share it with someone for a second opinion:

1. Generate compressed thumbnails (one-time, ~200KB per image instead of 10MB):
   ```bash
   .venv/bin/python generate_thumbs.py
   ```

2. Expose the app via [ngrok](https://ngrok.com):
   ```bash
   ngrok http 8080
   ```

3. Share `https://<your-ngrok-url>/review` with the reviewer

The reviewer sees each photo with **✕** / **✓** buttons and ← → to navigate. Their decisions are saved to `review_state.json` — completely separate from your culling state.

4. Watch their progress live at [http://localhost:8080/compare](http://localhost:8080/compare)

### Export final photos

Once the reviewer is done, copy all accepted photos to an `accepted/` folder:

```bash
.venv/bin/python3 -c "
import json, os, shutil
with open('review_state.json') as f:
    r = json.load(f)
accepted = [img for img in r['pool'] if r['decisions'].get(img) == 'accept']
os.makedirs('accepted', exist_ok=True)
for img in accepted:
    shutil.copy2(os.path.join('images', img), os.path.join('accepted', os.path.basename(img)))
print(f'{len(accepted)} photos copied to accepted/')
"
```

## File structure

```
.
├── app.py                 # Flask backend
├── generate_thumbs.py     # One-time thumbnail generator
├── run.sh                 # Start the app
├── requirements.txt
├── templates/
│   ├── index.html         # Culling UI
│   ├── review.html        # Mobile reviewer UI
│   └── compare.html       # Review results dashboard
├── images/                # Your photos go here (gitignored)
├── thumbs/                # Auto-generated thumbnails (gitignored)
├── accepted/              # Final export (gitignored)
├── state.json             # Culling progress (gitignored)
└── review_state.json      # Reviewer progress (gitignored)
```
