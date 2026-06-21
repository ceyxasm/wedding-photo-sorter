# wedding-photo-sorter

My sister got married. We had ~1800 photos. I was in one city, she was in another.

I couldn't just open a folder, manually copy-paste into another folder, lose track of what I'd seen, close the tab, reopen it, lose track again. So I built this little app over a couple of evenings to make the whole thing not terrible.

It probably won't be useful to anyone else. The use case is pretty specific — too many photos, multiple passes to narrow them down, and someone you love on the other end of an ngrok tunnel tapping ✓ or ✕ on their phone. But I'm pushing it anyway. Maybe as a reminder. Maybe as a souvenir. I don't know.

---

## What it does

- Shows you photos one by one, fullscreen. `Enter` to keep, `Space` to skip.
- Saves your progress after every keypress so you can quit and come back.
- Multiple passes — first pass might get you to 500, second to 300, third to 200. However many it takes.
- A mobile-friendly reviewer page so someone else can weigh in on your final cut from their phone (we used ngrok to share it).
- A comparison dashboard so you can see what they accepted and rejected.
- Exports the final selection as actual files into an `accepted/` folder.

## Setup

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run.sh
```

Open [http://localhost:8080](http://localhost:8080).

Put your photos in an `images/` folder first.

## Reviewer flow

```bash
# Generate compressed thumbnails so you don't murder their mobile data
.venv/bin/python generate_thumbs.py

# Expose locally via ngrok
ngrok http 8080
```

Send them `https://<ngrok-url>/review`. Watch their progress at `http://localhost:8080/compare`.

## That's it

It's scrappy. It works. The photos are picked. The wedding was beautiful. <3
