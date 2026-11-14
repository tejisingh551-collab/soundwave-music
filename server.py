import os
import re
import json
import base64
import urllib.request
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pyDes import des, ECB, PAD_PKCS5

PORT = int(os.environ.get('PORT', 8080))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
try:
    os.chdir(DIRECTORY)
except Exception:
    pass

DES_KEY = b"38346591"
CIPHER = des(DES_KEY, ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)

# High-accuracy queries matching JioSaavn indexing
TRENDING_PRESETS = {
    "home": "Latest Hindi Songs 2026 Hits",
    "new": "Latest New Releases 2026",
    "hindi": "Top Hindi Songs Bollywood Chartbusters",
    "hindi_mix": "Bollywood Evergreen Hits",
    "hindi_2026": "Best Hindi Songs",
    "hindi_2010s": "2010s Bollywood Hits Arijit Singh",
    "hindi_2000s": "2000s Hindi Hits",
    "hindi_90s": "90s Hindi Hits",
    "hindi_80s": "80s Hindi Hits",
    "hindi_70s": "70s Hindi Hits",
    "hindi_classic": "Classic Old Hindi Songs",
    "punjabi": "Top Punjabi Hits 2026",
    "punjabi_dj": "Punjabi DJ Remix",
    "punjabi_bass": "Punjabi Bass Boosted",
    "punjabi_dhol": "Punjabi Dhol Mix",
    "punjabi_mashup": "Punjabi Mashup",
    "punjabi_club": "Punjabi Club Mix",
    "english": "Billboard Hot 100 English Hits",
    "romantic": "Romantic Hindi Love Songs",
    "lofi": "Bollywood Lofi",
    "lofi_midnight": "Lofi Midnight",
    "lofi_bollywood": "Bollywood Lofi",
    "lofi_punjabi": "Punjabi Lofi",
    "lofi_chillhop": "Chillhop",
    "lofi_rain": "Lofi Sleep Rain",
    "party": "Party Hindi Dance Bangers",
    "haryanvi": "Top Haryanvi Songs",
    "bhojpuri": "Top Bhojpuri Songs",
    "gurbani": "Shabad Gurbani Kirtan",
    "sehaj_path": "Sehaj Paath Ang",
    "nitnem": "Nitnem Sahib Full Path",
    "sukhmani": "Sukhmani Sahib Full Path",
    "dhadrianwale": "Bhai Ranjit Singh Ji Dhadrianwale",
    "japji_sartaj": "Satinder Sartaaj Japji Sahib",
    "funk": "Top Funk Hits",
    "bhangra": "Top Punjabi Bhangra Hits",
    "bhangra_2025": "Latest Punjabi Bhangra Songs 2025",
    "bhangra_2024": "Punjabi Bhangra Songs 2024",
    "bhangra_2023": "Punjabi Bhangra Songs 2023",
    "bhangra_2022": "Punjabi Bhangra Songs 2022",
    "bhangra_2021": "Punjabi Bhangra Songs 2021",
    "bhangra_2020": "Punjabi Bhangra Songs 2020",
    "bhangra_2015": "Punjabi Bhangra Hits 2015",
    "bhangra_2010": "Punjabi Bhangra Hits 2010",
    "bhangra_2000": "Punjabi Bhangra 2000",
    "bhangra_1990": "Punjabi Bhangra 1990"
}

def decrypt_url(enc_url):
    try:
        dec = CIPHER.decrypt(base64.b64decode(enc_url.strip())).decode('utf-8')
        return dec.replace('_96.mp4', '_320.mp4').replace('_160.mp4', '_320.mp4')
    except Exception as e:
        return ""

def clean_string(s):
    if not s:
        return ""
    return s.replace('&quot;', '"').replace('&amp;', '&').replace('&#039;', "'").strip()

def search_jiosaavn(query, page=1, fetch_depth=2):
    if not query:
        query = "Trending Hindi"
    
    q_lower = query.lower().strip()
    if ('japji' in q_lower and ('sartaj' in q_lower or 'sartaaj' in q_lower)) or q_lower == 'japji_sartaj':
        query = "Satinder Sartaaj Japji Sahib"
        q_lower = "japji_sartaj"
    elif 'sehaj' in q_lower or q_lower == 'sehaj_path':
        query = "Sehaj Paath Ang"
        q_lower = "sehaj_path"
    elif 'sukhmani' in q_lower or q_lower == 'sukhmani':
        query = "Sukhmani Sahib Full Path"
        q_lower = "sukhmani"
    elif 'nitnem' in q_lower or q_lower == 'nitnem':
        query = "Nitnem Sahib Full Path"
        q_lower = "nitnem"
    elif 'bhojpuri' in q_lower:
        query = "Top Bhojpuri Songs"
        q_lower = "bhojpuri"
    elif q_lower in ['lofi', 'lo-fi', 'lofi midnight', 'lofi_midnight']:
        query = "Bollywood Lofi"
        q_lower = "lofi"
    elif q_lower in ['punjabi_dj', 'punjabi dj', 'punjabi dj remix', 'punjabi remix', 'dj punjabi', 'dj punjabi remix']:
        query = "Punjabi DJ Remix"
        q_lower = "punjabi_dj"
    elif q_lower in TRENDING_PRESETS:
        query = TRENDING_PRESETS[q_lower]
        
    encoded_query = urllib.parse.quote(query)
    
    songs = []
    seen_titles = set()
    seen_images = set()
    
    # Massive Library Expansion: fetch multiple pages/sources to get 80-100+ raw tracks
    if q_lower == 'lofi' and page == 1:
        query_urls = [
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=40&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Bollywood Lofi')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Lofi Midnight')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=25&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Punjabi Lofi')}",
        ]
    elif q_lower == 'punjabi_dj' and page == 1:
        query_urls = [
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Punjabi DJ Remix')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=30&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Punjabi Bass Boosted')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=25&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Punjabi Dhol Mix')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=25&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Punjabi Mashup')}",
        ]
    elif q_lower in ['hindi', 'hindi_mix'] and page == 1:
        query_urls = [
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Bollywood Evergreen Hits')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Best Hindi Songs')}",
        ]
    elif q_lower == 'hindi_90s' and page == 1:
        query_urls = [
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('90s Hindi Hits')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Kumar Sanu Romantic Hits')}",
        ]
    elif q_lower == 'hindi_80s' and page == 1:
        query_urls = [
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('80s Hindi Hits')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('80s Bollywood Songs')}",
        ]
    elif q_lower == 'hindi_70s' and page == 1:
        query_urls = [
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('70s Hindi Hits')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Kishore Kumar Hits')}",
        ]
    elif q_lower == 'hindi_classic' and page == 1:
        query_urls = [
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=30&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Classic Old Hindi Songs')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=30&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Mukesh Golden Hits')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=25&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Lata Mangeshkar Evergreen Hits')}",
        ]
    elif q_lower == 'funk' and page == 1:
        query_urls = [
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Top Funk Hits')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=35&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Brazilian Phonk Funk')}",
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=30&p=1&_marker=0&ctx=android&q={urllib.parse.quote('Funk Groove Disco')}",
        ]
    else:
        pages_to_fetch = [page]
        if fetch_depth > 1:
            pages_to_fetch.append(page + 1)
            if q_lower in ['home', 'punjabi', 'hindi', 'bhangra', 'funk', 'hindi_mix', 'hindi_90s', 'hindi_80s', 'hindi_70s', 'hindi_2000s', 'hindi_2010s', 'hindi_2026', 'hindi_classic']:
                pages_to_fetch.append(page + 2)
        query_urls = [
            f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n=50&p={p_num}&_marker=0&ctx=android&q={encoded_query}"
            for p_num in pages_to_fetch
        ]
            
    for url in query_urls:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        try:
            with urllib.request.urlopen(req, timeout=9) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
                data = json.loads(content)
                results = data.get('results', [])
                
                for r in results:
                    raw_title = clean_string(r.get('song', '') or r.get('title', ''))
                    if not raw_title:
                        continue
                    
                    # Filter out Ringtones, Ringtunes, Teasers, Promos, Dialogue tracks
                    title_lower = raw_title.lower()
                    bad_keywords = [
                        'ringtone', 'ringtune', 'ring tone', 'ring tune', 'caller tune', 'callertune',
                        'dialogue', 'teaser', 'trailer', 'promo', 'bgm', 'theme music', 'hook step',
                        'status sound', 'compilation', 'jukebox'
                    ]
                    if any(bad in title_lower for bad in bad_keywords):
                        continue
                    
                    # Duration filter: Allow complete 5-hour Sehaj Path episodes, 90-min Sukhmani Sahib, 2-hr Nitnem, 3-hr Diwans
                    duration = int(r.get('duration', 0)) if r.get('duration') else 0
                    if any(k in q_lower for k in [
                        'sehaj', 'paath', 'path', 'sukhmani', 'nitnem', 'gurbani', 'shabad', 'kirtan', 
                        'simran', 'waheguru', 'japji', 'jaap', 'chaupai', 'rehras', 'sohila', 
                        'dukh bhanjani', 'asa di war', 'asa di vaar', 'dhadrianwale', 'dhadrianwala', 'diwan', 'katha'
                    ]):
                        max_dur = 18000 # 5 Hours (Never cut off full Gurbani Baanis or Sehaj Path!)
                    elif any(k in q_lower for k in ['sleep', 'sleeping', 'ambient', 'meditation', 'relaxing', 'lofi', 'lo-fi', 'chillhop', 'dj', 'remix', 'mashup', 'bass']):
                        max_dur = 3600
                    else:
                        max_dur = 900 # 15 minutes for general songs
    
                    if duration < 45 or duration > max_dur:
                        continue
                    
                    # Clean display title (strip "Trending Version" marketing tags)
                    clean_display_title = re.sub(r'\s*[\(\[-]?\s*trending version\s*[\)\]-]?', '', raw_title, flags=re.IGNORECASE).strip()
                    if not clean_display_title:
                        clean_display_title = raw_title
    
                    # Deduplication by normalized base title
                    base_title = re.sub(r'\(.*?\)|\[.*?\]', '', raw_title).lower()
                    is_special = any(k in q_lower for k in ['lofi', 'chill', 'dj', 'remix', 'mashup', 'bass'])
                    if not is_special:
                        base_title = re.sub(r'\b(trending version|trending|ringtune|ringtone|remix|lofi|slowed|reverb|version|full song|audio|official|video|song)\b', '', base_title)
                    else:
                        base_title = re.sub(r'\b(trending version|trending|ringtune|ringtone|version|full song|audio|official|video|song)\b', '', base_title)
                    base_title = re.sub(r'[^a-z0-9]', '', base_title).strip()
                    if not base_title:
                        base_title = re.sub(r'[^a-z0-9]', '', raw_title.lower()).strip()
    
                    if not base_title or base_title in seen_titles:
                        continue
                    seen_titles.add(base_title)
    
                    # Decrypt audio stream
                    enc_url = r.get('encrypted_media_url')
                    if not enc_url:
                        continue
                    audio_url = decrypt_url(enc_url)
                    if not audio_url:
                        continue
                    
                    # Distinct image deduplication: prevent repeating identical compilation album covers
                    img = r.get('image', '').replace('150x150', '500x500')
                    if not img or 'default' in img.lower() or img in seen_images:
                        img = ""
                    else:
                        seen_images.add(img)
                    
                    artist = clean_string(r.get('primary_artists', '') or r.get('singers', ''))
                    album = clean_string(r.get('album', ''))
                    year = clean_string(str(r.get('year', '') or ''))
                    
                    ang_match = re.search(r'Ang\s*\(?([0-9\s\-to]+)\)?', clean_display_title, re.IGNORECASE)
                    ang_badge = ('Ang ' + ang_match.group(1).strip()) if ang_match else ''
                    
                    songs.append({
                        'id': r.get('id', ''),
                        'name': clean_display_title,
                        'artist': artist,
                        'album': album,
                        'image': img,
                        'audioUrl': audio_url,
                        'duration': duration,
                        'year': year,
                        'ang': ang_badge
                    })
        except Exception as e:
            print(f"Search error on page {p_num}:", e)

    # For Sehaj Path, sort in exact sequential order from Ang 1 to Ang 1430
    if q_lower == 'sehaj_path' or 'sehaj' in q_lower:
        def get_ang_val(s):
            name = s.get('name', '')
            m = re.search(r'Ang\s*\(?(\d+)', name, re.IGNORECASE)
            if m:
                return int(m.group(1))
            m = re.search(r'Part\s*(\d+)', name, re.IGNORECASE)
            if m:
                return int(m.group(1)) * 18
            return 9999
        songs.sort(key=get_ang_val)

    return songs

class MusicAppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/search':
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get('q', [''])[0]
            try:
                p = int(query_params.get('p', ['1'])[0])
            except Exception:
                p = 1
            songs = search_jiosaavn(q, page=p, fetch_depth=2 if p == 1 else 1)
            
            body = json.dumps({'success': True, 'page': p, 'results': songs}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == '/sw.js':
            try:
                file_path = os.path.join(DIRECTORY, 'sw.js')
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript')
                self.send_header('Service-Worker-Allowed', '/')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(404, "File not found")
        elif parsed.path in ['/TejiMusic.apk', '/download/apk']:
            try:
                file_path = os.path.join(DIRECTORY, 'TejiMusic.apk')
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.android.package-archive')
                self.send_header('Content-Disposition', 'attachment; filename="TejiMusic.apk"')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(404, "File not found")
        elif parsed.path == '/api/user/load':
            query_params = urllib.parse.parse_qs(parsed.query)
            uname = query_params.get('username', [''])[0].strip().lower()
            users_file = os.path.join(DIRECTORY, 'users_db.json')
            user_data = {}
            if os.path.exists(users_file):
                try:
                    with open(users_file, 'r', encoding='utf-8') as f:
                        all_users = json.load(f)
                        user_data = all_users.get(uname, {})
                except Exception:
                    pass
            body = json.dumps({'success': True, 'user': user_data}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == '/manifest.json':
            try:
                file_path = os.path.join(DIRECTORY, 'manifest.json')
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/manifest+json')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(404, "File not found")
        else:
            super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/user/sync':
            try:
                length = int(self.headers.get('Content-Length', 0))
                req_data = json.loads(self.rfile.read(length).decode('utf-8'))
                uname = (req_data.get('username') or req_data.get('name', '')).strip().lower()
                if not uname:
                    uname = "default_user"
                users_file = os.path.join(DIRECTORY, 'users_db.json')
                all_users = {}
                if os.path.exists(users_file):
                    try:
                        with open(users_file, 'r', encoding='utf-8') as f:
                            all_users = json.load(f)
                    except Exception:
                        pass
                all_users[uname] = req_data
                with open(users_file, 'w', encoding='utf-8') as f:
                    json.dump(all_users, f, indent=2, ensure_ascii=False)
                
                body = json.dumps({'success': True, 'message': 'User profile synced successfully'}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                err_body = json.dumps({'success': False, 'error': str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)
        else:
            self.send_error(404, "Not found")

if __name__ == '__main__':
    try:
        server = ThreadingHTTPServer(('0.0.0.0', PORT), MusicAppHandler)
        server.daemon_threads = True
        print(f"TejiMusic Server ready on http://localhost:{PORT}", flush=True)
        server.serve_forever()
    except Exception as e:
        import traceback
        traceback.print_exc()
