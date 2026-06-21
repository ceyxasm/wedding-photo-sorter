from flask import Flask, jsonify, request, send_file, render_template
import os, json, threading

_review_lock = threading.Lock()

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, 'images')
THUMB_DIR = os.path.join(BASE_DIR, 'thumbs')
STATE_FILE = os.path.join(BASE_DIR, 'state.json')
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)
SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic'}
SKIP_DIRS = {'templates', '__pycache__', '.git', 'node_modules'}


def scan_images():
    images = []
    for root, dirs, files in os.walk(IMAGE_DIR):
        dirs.sort()
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext in SUPPORTED_EXTS:
                relpath = os.path.relpath(os.path.join(root, f), IMAGE_DIR)
                images.append(relpath)
    return images


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    images = scan_images()
    state = {
        'passes': [{
            'number': 1,
            'pool': images,
            'decisions': {},
            'selected': [],
            'current_index': 0,
            'completed': False
        }],
        'current_pass': 0
    }
    save_state(state)
    return state


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/state')
def api_state():
    return jsonify(load_state())


@app.route('/api/action', methods=['POST'])
def api_action():
    data = request.json
    action = data['action']  # 'select', 'skip', 'back'

    state = load_state()
    cp = state['current_pass']
    p = state['passes'][cp]
    decisions = p.get('decisions', {})
    pool = p['pool']

    if action == 'back':
        if p['current_index'] > 0:
            p['current_index'] -= 1
            p['completed'] = False
    else:
        idx = p['current_index']
        if idx < len(pool):
            image = pool[idx]
            decisions[image] = action
            p['decisions'] = decisions
            p['current_index'] = idx + 1
            if p['current_index'] >= len(pool):
                p['completed'] = True

    p['selected'] = [img for img in pool if decisions.get(img) == 'select']
    save_state(state)
    return jsonify(state)


@app.route('/api/next-pass', methods=['POST'])
def next_pass():
    state = load_state()
    cp = state['current_pass']
    p = state['passes'][cp]

    if not p['completed']:
        return jsonify({'error': 'Current pass not completed yet'}), 400

    # If this was a supplemental pass, merge its selections with the previous pass's selections
    if p.get('supplemental') and cp > 0:
        prev_selected = state['passes'][cp - 1]['selected']
        pool = list(dict.fromkeys(prev_selected + p['selected']))  # merge, dedupe, preserve order
    else:
        pool = p['selected']

    if not pool:
        return jsonify({'error': 'No images selected'}), 400

    new_pass = {
        'number': p['number'] + 1,
        'pool': pool,
        'decisions': {},
        'selected': [],
        'current_index': 0,
        'completed': False
    }
    state['passes'].append(new_pass)
    state['current_pass'] = cp + 1
    save_state(state)
    return jsonify(state)


@app.route('/api/add-images', methods=['POST'])
def add_images():
    state = load_state()
    cp = state['current_pass']
    p = state['passes'][cp]

    if not p['completed']:
        return jsonify({'error': 'Finish the current pass first'}), 400

    # Find images not already tracked in any pass
    known = set()
    for pass_ in state['passes']:
        known.update(pass_['pool'])

    all_images = scan_images()
    new_images = [img for img in all_images if img not in known]

    if not new_images:
        return jsonify({'error': 'No new images found — make sure they are extracted into the images/ folder'}), 400

    new_pass = {
        'number': p['number'] + 1,
        'pool': new_images,
        'decisions': {},
        'selected': [],
        'current_index': 0,
        'completed': False,
        'supplemental': True  # signals next-pass to merge with previous selections
    }
    state['passes'].append(new_pass)
    state['current_pass'] = cp + 1
    save_state(state)
    return jsonify(state)


@app.route('/api/export')
def export_list():
    state = load_state()
    p = state['passes'][state['current_pass']]
    text = '\n'.join(p['selected'])
    return text, 200, {'Content-Type': 'text/plain; charset=utf-8'}


# ── Review (sister's pass) ────────────────────────────────────────────────────

REVIEW_FILE = os.path.join(BASE_DIR, 'review_state.json')


def load_review_state():
    if os.path.exists(REVIEW_FILE):
        with open(REVIEW_FILE) as f:
            return json.load(f)
    # Seed from the current pass's selected images
    state = load_state()
    p = state['passes'][state['current_pass']]
    review = {'pool': p['selected'], 'decisions': {}, 'last_index': 0}
    save_review_state(review)
    return review


def save_review_state(review):
    tmp = REVIEW_FILE + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(review, f, indent=2)
    os.replace(tmp, REVIEW_FILE)  # atomic on POSIX — no partial writes


@app.route('/review')
def review_page():
    return render_template('review.html')


@app.route('/compare')
def compare_page():
    return render_template('compare.html')


@app.route('/api/review/state')
def api_review_state():
    return jsonify(load_review_state())


@app.route('/api/review/action', methods=['POST'])
def api_review_action():
    data = request.json
    filename = data['filename']
    decision = data.get('decision')   # 'accept', 'reject', or null to clear

    with _review_lock:
        review = load_review_state()
        if filename not in review['pool']:
            return jsonify({'error': 'Image not in review pool'}), 400
        if decision is None:
            review['decisions'].pop(filename, None)
        else:
            review['decisions'][filename] = decision
        save_review_state(review)

    return jsonify(review)


@app.route('/api/review/position', methods=['POST'])
def api_review_position():
    data = request.json
    with _review_lock:
        review = load_review_state()
        review['last_index'] = data['last_index']
        save_review_state(review)
    return '', 204


@app.route('/api/review/export')
def api_review_export():
    review = load_review_state()
    accepted = [img for img in review['pool'] if review['decisions'].get(img) == 'accept']
    text = '\n'.join(accepted)
    return text, 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/api/rescan', methods=['POST'])
def rescan():
    """Reset state and rescan images — use when downloads finish."""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    return jsonify(load_state())


@app.route('/img/<path:filename>')
def serve_image(filename):
    filepath = os.path.abspath(os.path.join(IMAGE_DIR, filename))
    if not filepath.startswith(IMAGE_DIR + os.sep) and filepath != IMAGE_DIR:
        return 'Forbidden', 403
    return send_file(filepath)


@app.route('/thumb/<path:filename>')
def serve_thumb(filename):
    thumb_path = os.path.abspath(os.path.join(THUMB_DIR, filename))
    if not thumb_path.startswith(THUMB_DIR + os.sep):
        return 'Forbidden', 403
    if os.path.exists(thumb_path):
        return send_file(thumb_path)
    # fallback to original if thumb not generated yet
    return serve_image(filename)


if __name__ == '__main__':
    print('\n  Gallery Selector running at http://localhost:8080\n')
    app.run(port=8080, debug=False)
