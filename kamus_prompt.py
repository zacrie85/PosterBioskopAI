# -*- coding: utf-8 -*-
"""Kamus prompt Indonesia -> Inggris untuk mesin AI PosterBioskopAI.

SD-Turbo (CLIP) hanya memahami bahasa Inggris. Modul ini menerjemahkan
prompt pengguna (contoh: "nelayan tua di pantai saat senja") menjadi
kata kunci Inggris yang benar-benar dipahami model, dengan pemadanan
frasa terpanjang dulu (4 -> 3 -> 2 -> 1 kata). Kata yang tidak ada di
kamus diteruskan apa adanya — kalau pengguna menulis Inggris, tetap aman.
"""

import re

# ---------------------------------------------------------------- kata orang
KAMUS = {
    "polisi": "police officer", "polisi lalu lintas": "traffic police officer",
    "tentara": "soldier", "prajurit": "soldier", "petani": "farmer",
    "petani padi": "rice farmer", "nelayan": "fisherman", "dokter": "doctor",
    "perawat": "nurse", "guru": "teacher", "murid": "student",
    "pelajar": "school student", "mahasiswa": "university student",
    "penyihir": "witch", "dukun": "shaman", "peramal": "fortune teller",
    "ksatria": "knight", "pendekar": "martial arts master",
    "pesilat": "silat fighter", "samurai": "samurai warrior", "ninja": "ninja",
    "detektif": "detective", "penyidik": "investigator", "hakim": "judge",
    "jaksa": "prosecutor", "advokat": "lawyer", "ratu": "queen", "raja": "king",
    "putri": "princess", "pangeran": "prince", "monster": "monster",
    "hantu": "ghost", "vampir": "vampire", "zombie": "zombie",
    "robot": "robot", "alien": "alien", "astronot": "astronaut",
    "pilot": "pilot", "kapten": "captain", "nahkoda": "ship captain",
    "pembalap": "race car driver", "pramugari": "flight attendant",
    "pemandu": "tour guide", "pemadam kebakaran": "firefighter",
    "penyelam": "diver", "pemburu": "hunter", "pengembara": "wanderer",
    "pengelana": "traveler", "pemuda": "young man", "pemudi": "young woman",
    "gadis": "young girl", "anak laki-laki": "young boy",
    "anak kecil": "small child", "bapak": "father", "ibu": "mother",
    "kakek": "old grandfather", "nenek": "old grandmother",
    "keluarga": "family", "pasangan": "couple", "penari": "dancer",
    "penyanyi": "singer", "musisi": "musician", "gitaris": "guitarist",
    "chef": "chef", "koki": "cook", "pelayan": "waiter",
    "pedagang": "street vendor", "tukang becak": "rickshaw driver",
    "ojek": "motorcycle taxi rider", "pengemudi": "driver", "sopir": "driver",
    "tukang kebun": "gardener", "pencuri": "thief", "penjahat": "villain",
    "pahlawan": "hero", "pejuang": "freedom fighter", "pendeta": "priest",
    "ustadz": "muslim cleric", "santri": "islamic student",
    "biarawan": "monk", "pandita": "holy sage", "putri duyung": "mermaid",
    "manusia serigala": "werewolf", "pahlawan super": "superhero",
    "kuntilanak": "long haired female ghost", "pocong": "shrouded ghost",
    "tuyul": "small goblin", "babi ngepet": "werepig",
    "jurig": "female ghost", "perampok": "robber", "juru masak": "cook",
    # ---------------------------------------------------------------- hewan
    "kucing": "cat", "anjing": "dog", "ayam": "chicken", "bebek": "duck",
    "elang": "eagle", "garuda": "giant mythical eagle", "harimau": "tiger",
    "singa": "lion", "gajah": "elephant", "badak": "rhinoceros",
    "ular": "snake", "kobra": "cobra", "naga": "dragon", "burung": "bird",
    "merpati": "dove", "kuda": "horse", "kerbau": "water buffalo",
    "sapi": "cow", "kambing": "goat", "serigala": "wolf", "monyet": "monkey",
    "hiu": "shark", "ikan": "fish", "kupu-kupu": "butterfly",
    "laba-laba": "giant spider", "buaya": "crocodile", "kancil": "mouse deer",
    "ayam jago": "rooster", "kelelawar": "bats", "burung hantu": "owl",
    "penguin": "penguin", "unta": "camel", "zebra": "zebra",
    # ------------------------------------------------ kendaraan & alat
    "sepeda motor": "motorcycle", "motor": "motorcycle",
    "motor klasik": "vintage motorcycle", "mobil": "car",
    "mobil sport": "sports car", "mobil klasik": "classic car",
    "truk": "truck", "becak": "cycle rickshaw", "delman": "horse cart",
    "andong": "horse carriage", "kapal": "ship", "perahu": "boat",
    "perahu layar": "sailboat",
    "pinisi": "traditional indonesian sailing ship",
    "pesawat": "airplane", "helikopter": "helicopter", "kereta": "train",
    "kereta api": "steam train", "sepeda": "bicycle", "roket": "rocket",
    "bis": "bus", "angkot": "city minibus", "sampan": "small wooden boat",
    "gerobak": "street cart", "kereta kuda": "horse carriage",
    # ------------------------------------------------ tempat & lokasi
    "sawah": "green rice terraces", "pematang sawah": "rice field path",
    "kebun": "garden", "kebun teh": "tea plantation",
    "kebun stroberi": "strawberry farm", "hutan": "forest",
    "hutan bambu": "bamboo forest", "hutan tropis": "tropical jungle",
    "gunung": "mountain", "puncak gunung": "mountain summit",
    "kaki gunung": "mountain foothill", "gunung berapi": "volcano",
    "bukit": "hill", "bukit sawah": "hillside rice terraces",
    "pantai": "beach", "laut": "open sea", "dasar laut": "deep underwater",
    "sungai": "river", "kali": "small stream", "air terjun": "waterfall",
    "danau": "lake", "desa": "village", "perkampungan": "village hamlet",
    "kota": "city", "kota besar": "big city", "kota tua": "old town",
    "pasar": "traditional market", "pasar malam": "night market",
    "warung": "street food stall", "warung kopi": "traditional coffee shop",
    "masjid": "mosque", "gereja": "church", "pura": "balinese temple",
    "vihara": "chinese temple", "sekolah": "school", "kelas": "classroom",
    "kampus": "university campus", "kantor": "office", "pabrik": "factory",
    "gudang": "warehouse", "jalan raya": "highway", "gang sempit": "narrow alley",
    "alun-alun": "town square", "teras rumah": "house terrace",
    "dapur": "kitchen", "kamar": "bedroom", "ruang tamu": "living room",
    "stadion": "stadium", "museum": "museum", "gua": "cave", "kolam": "pond",
    "jembatan": "bridge", "pelabuhan": "harbor", "bandara": "airport",
    "stasiun": "train station", "gang": "alley", "reruntuhan": "ruins",
    "istana": "palace", "menara": "tower", "hutan pinus": "pine forest",
    "sabana": "savanna", "gurun": "desert", "padang rumput": "grass field",
    "ladang": "crop field", "perkebunan": "plantation",
    "atap gedung": "rooftop", "parkiran": "parking lot",
    "rumah panggung": "stilt house", "kampung nelayan": "fishing village",
    "candi": "ancient temple ruins", "borobudur": "borobudur temple",
    "bali": "bali island", "jakarta": "jakarta city",
    "kota metropolitan": "metropolis", "tambak ikan": "fish ponds",
    "tebing karang": "sea cliff", "jurang": "canyon",
    "lorong bawah tanah": "underground tunnel", "kolong jembatan": "under the bridge",
    "pasir putih": "white sand", "tanah perkuburan": "graveyard",
    "rumah tua": "old creepy house", "gedung tinggi": "skyscrapers",
    # ------------------------------------------------ waktu & cuaca
    "pagi": "morning", "pagi buta": "early dawn", "siang": "midday",
    "sore": "afternoon", "senja": "golden sunset", "magrib": "dusk",
    "malam": "night", "tengah malam": "midnight", "fajar": "sunrise dawn",
    "subuh": "pre dawn", "gerimis": "light rain", "hujan": "heavy rain",
    "hujan deras": "torrential rain", "badai": "storm",
    "badai petir": "thunderstorm", "kabut": "fog", "kabut tebal": "thick fog",
    "berawan": "cloudy sky", "cerah": "clear sky",
    "panas terik": "scorching heat", "dingin membeku": "freezing cold",
    "salju": "snow", "matahari terbenam": "sunset", "matahari terbit": "sunrise",
    "bulan purnama": "full moon", "gerhana": "eclipse", "pelangi": "rainbow",
    "petir": "lightning", "langit merah": "red sky", "langit malam": "night sky",
    "bintang jatuh": "falling star", "gempa": "earthquake",
    "tsunami": "giant wave", "banjir": "flood", "erupsi": "eruption",
    "angin kencang": "strong wind", "musim hujan": "rainy season",
    "musim panas": "summer", "musim gugur": "autumn", "musim semi": "spring",
    "musim dingin": "winter", "cahaya matahari": "sunlight",
    "cahaya bulan": "moonlight", "cahaya lilin": "candlelight",
    "cahaya neon": "neon light", "pantulan cahaya": "light reflections",
    "menjelang pagi": "pre dawn hours", "sore hari": "golden hour",
    "saat senja": "at golden sunset", "saat pagi": "at sunrise",
    # ------------------------------------------------ suasana & genre
    "bahagia": "joyful", "ceria": "cheerful", "sedih": "melancholic",
    "menyesakkan": "heartbreaking", "menyeramkan": "terrifying",
    "horor": "horror", "romantis": "romantic", "cinta": "love story",
    "patah hati": "heartbreak", "epik": "epic", "heroik": "heroic",
    "gelap": "dark", "tenang": "peaceful", "damai": "serene",
    "tegang": "tense thriller", "misterius": "mysterious", "magis": "magical",
    "ajaib": "magical fantasy", "nostalgia": "nostalgic",
    "penuh harapan": "hopeful", "sunyi": "silent", "riuh": "chaotic",
    "kacau": "chaotic", "lucu": "funny", "komedi": "comedy",
    "berkelas": "classy", "mewah": "luxurious", "harapan": "hope",
    "pengkhianatan": "betrayal", "balas dendam": "revenge",
    "persahabatan": "friendship", "keberanian": "bravery",
    "pengorbanan": "sacrifice", "perjalanan": "journey",
    "petualangan": "adventure", "pertarungan": "fight", "perang": "war",
    "kiamat": "apocalypse", "horor komedi": "horror comedy",
    "action": "action", "drama": "drama", "thriller": "thriller",
    "fantasi": "fantasy", "fiksi ilmiah": "science fiction",
    "sejarah": "historical", "kolonial": "colonial era",
    "kerajaan": "ancient kingdom", "jadul": "retro", "vintage": "vintage",
    "menegangkan": "edge of seat suspense", "mengharukan": "tear jerking",
    "dingin": "cold tones", "hangat": "warm tones", "kacau balau": "mayhem",
    # ------------------------------------------------ aksi & kegiatan
    "berlari": "running", "lari": "running", "berjalan": "walking",
    "menari": "dancing", "tari": "traditional dance", "memasak": "cooking",
    "berdoa": "praying", "sholat": "praying at mosque", "tertawa": "laughing",
    "menangis": "crying", "bertarung": "fighting", "mengejar": "chasing",
    "terbang": "flying", "berenang": "swimming", "menyelam": "diving",
    "memanah": "archery", "menebang": "chopping wood",
    "membajak sawah": "plowing rice field", "menyiram": "watering plants",
    "menjahit": "sewing", "membaca": "reading", "menulis": "writing",
    "menggambar": "drawing", "bernyanyi": "singing",
    "bermain gitar": "playing guitar", "berteduh": "taking shelter",
    "menyeberang": "crossing", "memanjat": "climbing", "meninju": "punching",
    "menyapu": "sweeping", "mencuci": "washing clothes",
    "menanam padi": "planting rice", "memanen": "harvesting",
    "memancing": "fishing", "berlayar": "sailing", "melompat": "jumping",
    "jatuh": "falling", "tidur": "sleeping", "mimpi": "dream",
    "berangkat sekolah": "going to school", "gotong royong": "communal cooperation",
    "kerja bakti": "community work", "kejar-kejaran": "chase scene",
    "berpelukan": "hugging", "berjabat tangan": "shaking hands",
    "mengintai": "spying", "menunggu": "waiting", "berburu": "hunting",
    "menyulam": "embroidering", "menganyam": "weaving baskets",
    # ------------------------------------------------ warna
    "merah": "red", "merah muda": "pink", "biru": "blue",
    "biru langit": "sky blue", "hijau": "green", "kuning": "yellow",
    "emas": "golden", "perak": "silver", "hitam": "black", "putih": "white",
    "abu-abu": "gray", "ungu": "purple", "jingga": "orange",
    "coklat": "brown", "toska": "teal", "marun": "maroon",
    "pirus": "turquoise", "hitam putih": "black and white",
    "warna pudar": "faded colors", "warna mencolok": "vivid colors",
    # ------------------------------------------------ komposisi & kamera
    "drone": "aerial drone view", "dari udara": "aerial view",
    "close-up": "extreme close up portrait", "wajah dekat": "close up face",
    "gerak lambat": "slow motion", "siluet": "silhouette",
    "bayangan panjang": "long shadows", "bokeh": "bokeh lights",
    "asap": "smoke", "debu": "dust particles", "percikan air": "water splash",
    "percikan api": "fire sparks", "cahaya dari belakang": "backlight",
    "remang-remang": "dim moody lighting", "kontras tinggi": "high contrast",
    "gambar lebar": "wide shot", "dari atas": "top down view",
    "dari bawah": "low angle shot", "pantulan air": "water reflection",
    "jendela": "window light", "cermin": "mirror reflection",
    "beton": "concrete wall", "dinding grafiti": "graffiti wall",
    "neon": "neon signs", "lampu jalan": "street lamps",
    "jalanan basah": "wet streets", "berbayang": "shadowy",
    "sinematik": "cinematic", "potret": "portrait", "grup": "group shot",
    "berjajar": "lined up", "sepi": "empty lonely", "rusak": "damaged",
    "futuristik": "futuristic", "kuno": "ancient", "tradisional": "traditional",
    "modern": "modern", "dinding bata": "red brick wall",
    "kaca berkabut": "frosted glass", "langit dramatis": "dramatic sky",
    "awan dramatis": "dramatic clouds", "angin": "windy",
    # ------------------------------------------------ budaya Indonesia
    "batik": "batik fabric pattern", "wayang": "wayang shadow puppet",
    "wayang kulit": "wayang kulit shadow puppet",
    "gamelan": "gamelan orchestra", "angklung": "angklung bamboo music",
    "barong": "barong lion dance", "keris": "traditional dagger",
    "kebaya": "kebaya dress", "jarik": "batik sarong",
    "ondel-ondel": "ondel ondel giant puppet", "reog": "reog dance",
    "kuda lumping": "kuda lumping trance dance", "topeng": "traditional mask",
    "sasando": "sasando bamboo instrument", "sate": "satay skewers",
    "rendang": "rendang food", "nasi goreng": "fried rice",
    "kopi tubruk": "strong brewed coffee", "es teh": "iced tea",
    "kopiah": "muslim cap", "sarung": "sarong", "peci": "muslim cap",
    "jilbab": "hijab", "upacara adat": "traditional ceremony",
    "ngaben": "balinese cremation ceremony", "idul fitri": "eid celebration",
    "lebaran": "eid homecoming", "kampong": "kampung village",
    "perayaan": "celebration", "pesta": "festival party",
    # ------------------------------------------------ frasa populer
    "pemandangan desa": "village landscape",
    "pemandangan gunung": "mountain landscape",
    "pemandangan laut": "ocean seascape", "di tepi pantai": "by the shore",
    "di tengah sawah": "in the middle of rice fields",
    "di atas atap": "on the rooftop", "di bawah jembatan": "under the bridge",
    "di tengah jalan": "in the middle of the street",
    "di ujung gang": "at the end of the alley", "di atas kapal": "on a ship deck",
    "di dalam hutan": "deep in the forest",
    "di puncak gunung": "at the mountain top",
    "di atas awan": "above the clouds", "menembus awan": "above the clouds",
    "raja hutan": "king of the jungle", "pasukan zombie": "horde of zombies",
    "gerombolan hantu": "group of ghosts", "pertarungan akhir": "final battle",
    "bintang film": "movie star", "malam penuh bintang": "starry night",
    "hujan di malam hari": "rainy night", "pulang kampung": "homecoming journey",
    "kampung halaman": "hometown", "masa kecil": "childhood memory",
    "kenangan masa kecil": "childhood memory", "perjalanan jauh": "long journey",
    "akhir dunia": "end of the world", "ladang bunga": "flower field",
    "perkebunan teh": "tea plantation hills", "anak 90an": "1990s childhood",
    "film Indonesia": "indonesian cinema", "desa terpencil": "remote village",
    "kota hancur": "ruined city", "jalan kosong": "empty road",
    "saat hujan": "in the rain", "saat malam": "at night",
    "di pagi hari": "in the morning", "di malam hari": "at night",
    "di siang hari": "in broad daylight", "dari jauh": "distant view",
    "dari dekat": "close up view", "berdua": "two people together",
    "sendirian": "alone", "berombak": "waving", "berkilau": "shimmering",
    "menembus kabut": "emerging from fog", "di tengah badai": "in the storm",
    # ------------------------------------------------ pelengkap (dari kamus v1)
    "poster": "movie poster", "judul": "title", "video": "video",
    "bioskop": "cinema", "sinema": "cinema", "gaya": "style",
    "klasik": "classic", "megah": "epic", "dongeng": "fairytale",
    "mistis": "mystical", "misteri": "mystery", "kriminal": "crime",
    "seram": "horror", "langit": "sky", "tropis": "tropical",
    "elegan": "elegant", "kuat": "powerful", "keren": "cool",
    "gagah": "heroic", "kartun": "cartoon", "anime": "anime",
    "lukisan": "painting", "sketsa": "sketch",
    "realistis": "photorealistic", "foto": "photographic",
    "mendung": "storm", "sejuk": "cool", "berdebu": "dusty",
    "berwarna": "colorful", "bayangan": "shadow", "oranye": "orange",
    "keemasan": "golden", "berlampu": "neon", "matahari": "sun",
    "bulan": "moon", "pegunungan": "mountains", "indonesia": "indonesia",
    "seperti": "in the style of", "sebagai": "as", "menjadi": "become",
    "menggunakan": "using", "juga": "also", "semua": "all",
    # kata sifat umum
    "tua": "old", "muda": "young", "besar": "big", "kecil": "small",
    "tinggi": "tall", "pendek": "short", "cantik": "beautiful",
    "tampan": "handsome", "ganteng": "handsome",
    "kaya": "rich", "sakit": "sick", "lelah": "tired",
    "cepat": "fast", "lambat": "slow",
    "menyerang": "attacking", "bermain": "playing", "menang": "winning",
    "kalah": "losing", "menolong": "helping",
    "menolong teman": "helping a friend",
    "film": "movie", "gambar": "image", "cerita": "story",
}

# Kata sambung/keterangan yang tidak menambah makna untuk AI — dibuang.
_KATA_SAMBUNG = {"di", "ke", "dari", "yang", "dan", "atau", "untuk", "pada",
                 "dalam", "oleh", "dengan", "kepada", "ini", "itu", "nya",
                 "si", "kah", "lah", "pun", "ada", "saat", "akan", "sedang",
                 "telah", "sudah", "agar", "bila", "jika", "karena", "tersebut",
                 "rubahlah", "rubah", "ubahlah", "ubah", "buatlah", "buat",
                 "jadikan", "gambarnya", "filmnya", "judulnya", "videonya",
                 "posternya", "untuklah", "kita", "kawan", "juga", "sebuah"}


def terjemah_prompt(teks):
    """Terjemahkan teks Indonesia ke daftar kata kunci Inggris untuk AI.
    Frasa terpanjang dipadankan dulu (4 -> 3 -> 2 -> 1 kata); kata yang
    tidak ada di kamus diteruskan apa adanya (mis. sudah bahasa Inggris).
    Return list istilah unik, urut sesuai teks asli."""
    t = re.sub(r"[^a-z0-9\s\-]", " ", (teks or "").lower())
    kata = t.split()
    hasil, i, n = [], 0, len(kata)
    while i < n:
        cocok = None
        for panjang in (4, 3, 2):
            if i + panjang <= n:
                frasa = " ".join(kata[i:i + panjang])
                if frasa in KAMUS:
                    cocok = KAMUS[frasa]
                    i += panjang
                    break
        if cocok is None:
            kata_asli = kata[i]
            i += 1
            if kata_asli in _KATA_SAMBUNG:
                continue
            cocok = KAMUS.get(kata_asli, kata_asli)
        for bagian in cocok.split(","):
            bagian = bagian.strip()
            if bagian and bagian not in hasil:
                hasil.append(bagian)
    return hasil


def hitung_kamus():
    """Jumlah entri kamus (untuk tampilan di aplikasi)."""
    return len(KAMUS)
