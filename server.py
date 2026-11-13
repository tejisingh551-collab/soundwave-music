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
os.chdir(DIRECTORY)

DES_KEY = b"38346591"
CIPHER = des(DES_KEY, ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)

# High-accuracy queries matching JioSaavn indexing
TRENDING_PRESETS = {
    "home": "Top Hindi Songs",
    "new": "Latest New Releases 2026",
    "hindi": "Top Hindi Songs",
    "punjabi": "Top Punjabi Hits",
    "english": "English Hits",
    "romantic": "Romantic Hindi",
    "lofi": "Hindi Lofi",
    "party": "Party Hindi",
    "haryanvi": "Top Haryanvi",
    "gurbani": "Shabad Gurbani Kirtan",
    "dhadrianwale": "Bhai Ranjit Singh Ji Dhadrianwale",
    "sleeping": "Deep Sleep Relaxing Music Lo-Fi Chill",
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

def search_jiosaavn(query, count=45):
    if not query:
        query = "Trending Hindi"
    
    q_lower = query.lower().strip()
    if q_lower in TRENDING_PRESETS:
        query = TRENDING_PRESETS[q_lower]
        
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&n={count}&p=1&_marker=0&ctx=android&q={encoded_query}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    songs = []
    seen_titles = set()
    seen_images = set()
    
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
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
                
                # Duration filter: Allow full-length diwans (up to 3 hrs), sleep music (up to 1 hr), gurbani (up to 40 mins)
                duration = int(r.get('duration', 0)) if r.get('duration') else 0
                if any(k in q_lower for k in ['dhadrianwale', 'dhadrianwala', 'diwan', 'katha']):
                    max_dur = 10800
                elif any(k in q_lower for k in ['gurbani', 'shabad', 'kirtan', 'simran', 'nitnem', 'waheguru']):
                    max_dur = 2400
                elif any(k in q_lower for k in ['sleep', 'sleeping', 'ambient', 'meditation', 'relaxing']):
                    max_dur = 3600
                else:
                    max_dur = 600

                if duration < 45 or duration > max_dur:
                    continue
                
                # Clean display title (strip "Trending Version" marketing tags)
                clean_display_title = re.sub(r'\s*[\(\[-]?\s*trending version\s*[\)\]-]?', '', raw_title, flags=re.IGNORECASE).strip()
                if not clean_display_title:
                    clean_display_title = raw_title

                # Deduplication by normalized base title
                base_title = re.sub(r'\(.*?\)|\[.*?\]', '', raw_title).lower()
                base_title = re.sub(r'\b(trending version|trending|ringtune|ringtone|remix|lofi|slowed|reverb|version|full song|audio|official|video|song)\b', '', base_title)
                base_title = re.sub(r'[^a-z0-9]', '', base_title).strip()

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
                
                songs.append({
                    'id': r.get('id', ''),
                    'name': clean_display_title,
                    'artist': artist,
                    'album': album,
                    'image': img,
                    'audioUrl': audio_url,
                    'duration': duration,
                    'year': year
                })
    except Exception as e:
        print("Search error:", e)
    return songs

class MusicAppHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/search':
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get('q', [''])[0]
            songs = search_jiosaavn(q)
            
            body = json.dumps({'success': True, 'results': songs}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

if __name__ == '__main__':
    server = ThreadingHTTPServer(('0.0.0.0', PORT), MusicAppHandler)
    server.daemon_threads = True
    print(f"SoundWave Server ready on http://localhost:{PORT}")
    server.serve_forever()
