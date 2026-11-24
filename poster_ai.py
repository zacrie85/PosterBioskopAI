# -*- coding: utf-8 -*-
"""
PosterBioskopAI — MESIN AI (Stable Diffusion Turbo, ONNX, 100% OFFLINE).

Ini adalah fitur pengganti perpustakaan 999 referensi gaya: sebuah AI generatif
sungguhan. Frame terbaik dari video dipakai sebagai gambar awal (img2img), lalu
Stable Diffusion Turbo "menggambar ulang" frame itu menjadi key art poster film
sesuai prompt yang dipilih. Judul video tetap ditulis oleh mesin tipografi
(poster_engine) di atas hasil AI — dengan margin aman kiri/kanan.

Alur teknis:
  frame -> VAE encoder -> UNet Turbo (1-4 langkah, Euler) -> VAE decoder -> key art
Model ONNX fp16 diunduh sekali (tombol di GUI) ke folder `models/sd-turbo-onnx`
di samping aplikasi; setelah itu tidak perlu internet lagi.
"""

import json
import math
import os
import random
import re
import shutil
import sys
import threading
import urllib.request

import numpy as np
from PIL import Image

RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS

# ---------------------------------------------------------------------------
# Prompt bawaan — persis seperti yang diminta, terisi otomatis di GUI.
# ---------------------------------------------------------------------------
DEFAULT_PROMPT = ("Rubahlah gambar ini menjadi poster untuk sebuah film Hollywood "
                  "dengan menggunakan judul video sebagai judul di poster, "
                  "buat poster dengan gaya modern sinematik")

# Gaya bawaan yang selalu melekat pada prompt AI (yang dipahami model gambar).
_BASE_STYLE = ("cinematic hollywood movie poster key art, modern design, "
               "dramatic lighting, bold composition, rich color grading, "
               "highly detailed, sharp focus")

# ---------------------------------------------------------------------------
# Kamus prompt Indonesia -> Inggris (dipahami model gambar).
# Kata yang tidak dikenal tetap diteruskan apa adanya.
# ---------------------------------------------------------------------------
_TRANSLATE = {
    "rubahlah": "", "rubah": "", "ubahlah": "", "ubah": "", "buatlah": "",
    "buat": "", "jadikan": "", "gambarnya": "", "gambar": "", "ini": "",
    "untuk": "", "untuklah": "", "sebuah": "", "filmnya": "", "ke": "", "di": "",
    "dengan": "", "yang": "", "itu": "", "dan": "", "atau": "", "seperti": "",
    "sebagai": "", "menjadi": "", "menggunakan": "", "judulnya": "", "videonya": "",
    "posternya": "", "kita": "", "semua": "", "kawan": "", "juga": "", "kepada": "", "poster": "movie poster", "judul": "title", "video": "video",
    "holywood": "hollywood", "hollywood": "hollywood", "bioskop": "cinema",
    "sinematik": "cinematic", "sinematiknya": "cinematic", "sinema": "cinema",
    "modern": "modern", "moderen": "modern", "kekinian": "modern",
    "gaya": "style", "bergaya": "style", "ala": "style",
    "klasik": "classic", "vintage": "vintage", "retro": "retro", "futuristik": "futuristic",
    "epik": "epic", "epis": "epic", "megah": "epic", "grand": "epic",
    "dramatis": "dramatic", "drama": "drama", "romantis": "romantic", "romance": "romantic",
    "horor": "horror", "seram": "horror", "menyeramkan": "scary", "mistis": "mystical",
    "aksi": "action", "tempur": "combat", "perang": "war", "petualangan": "adventure",
    "komedi": "comedy", "lucu": "funny", "fantasi": "fantasy", "ajaib": "magical",
    "dongeng": "fairytale", "fiksi": "science", "ilmiah": "fiction", "sci-fi": "science fiction",
    "detektif": "detective", "misteri": "mystery", "thriller": "thriller", "kriminal": "crime",
    "gelap": "dark", "terang": "bright", "malam": "night", "siang": "daylight",
    "senja": "sunset", "fajar": "dawn", "matahari": "sun", "bulan": "moon",
    "kabut": "fog", "berkabut": "foggy", "hujan": "rain", "mendung": "storm",
    "badai": "storm", "salju": "snow", "berlampu": "neon", "neon": "neon",
    "hangat": "warm", "dingin": "cold", "sejuk": "cool", "emas": "golden",
    "keemasan": "golden", "merah": "red", "biru": "blue", "hijau": "green",
    "ungu": "purple", "hitam": "black", "putih": "white", "berwarna": "colorful",
    "gelapnya": "darkness", "teal": "teal", "oranye": "orange",
    "gunung": "mountains", "pegunungan": "mountains", "laut": "ocean", "pantai": "beach",
    "kota": "city", "metropolitan": "city", "desa": "village", "hutan": "forest",
    "gurun": "desert", "langit": "sky", "jalan": "road", "tropis": "tropical",
    "indonesia": "indonesia", "jakarta": "jakarta", "bali": "bali",
    "mewah": "luxury", "elegan": "elegant", "bersih": "clean", "kuat": "powerful",
    "heroik": "heroic", "pahlawan": "hero", "jarah": "epic", "mengerikan": "terrifying",
    "berdebu": "dusty", "keren": "cool", "kerenya": "cool", "gagah": "heroic",
    "cahaya": "light", "silhouette": "silhouette", "bayangan": "shadow",
    "kartun": "cartoon", "anime": "anime", "lukisan": "painting", "cat": "painting",
    "sketsa": "sketch", "realistis": "photorealistic", "foto": "photographic",
}

# ---------------------------------------------------------------------------
# Model & distribusi
# ---------------------------------------------------------------------------
# Varian ONNX NCHW standar (optimum), berjalan di CPU biasa (fp16).
MODEL_REPO = "jdp8/sd-turbo-onnx"
MODEL_URL = "https://huggingface.co/" + MODEL_REPO + "/resolve/main/"
# (jalur dalam folder model, ukuran byte menurut HF — untuk cek kelengkapan)
MODEL_FILES = [
    ("text_encoder/model.onnx", 681_552_894),
    ("unet/model.onnx", 1_737_702_391),
    ("vae_decoder/model.onnx", 99_129_787),
    ("vae_encoder/model.onnx", 136_760_235),
    ("tokenizer/vocab.json", 1_059_962),
    ("tokenizer/merges.txt", 524_619),
    ("tokenizer/tokenizer_config.json", 973),
    ("tokenizer/special_tokens_map.json", 211),
]
MODEL_TOTAL_BYTES = sum(s for _, s in MODEL_FILES)
MODEL_DIRNAME = "sd-turbo-onnx"

VAE_SCALE = 0.18215
MAX_TOKENS = 77


def app_base_dir():
    """Folder samping EXE (saat di-build) atau samping file .py ini."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def model_dir():
    return os.path.join(app_base_dir(), "models", MODEL_DIRNAME)


def model_status():
    """Return (siap: bool, terunduh_bytes, total_bytes, folder_model)."""
    d = model_dir()
    got = 0
    for rel, size in MODEL_FILES:
        p = os.path.join(d, rel)
        got += min(size, os.path.getsize(p)) if os.path.isfile(p) else 0
    return got >= MODEL_TOTAL_BYTES, got, MODEL_TOTAL_BYTES, d


def download_model(progress=None, cancel=None):
    """Unduh semua file model (lanjut dari posisi terputus).

    progress(fase, terunduh, total) dipanggil tiap potongan; cancel() -> True
    untuk berhenti (file parsial tetap disimpan agar bisa dilanjutkan).
    """
    d = model_dir()
    os.makedirs(d, exist_ok=True)
    done = 0
    for rel, size in MODEL_FILES:
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        start = os.path.getsize(p) if os.path.isfile(p) else 0
        if start >= size:
            done += size
            continue
        req = urllib.request.Request(MODEL_URL + rel)
        if start > 0:
            req.add_header("Range", "bytes=%d-" % start)
        req.add_header("User-Agent", "PosterBioskopAI")
        with urllib.request.urlopen(req, timeout=60) as r:
            # kalau server abaikan Range (balas 200, bukan 206) -> mulai ulang
            if start > 0 and getattr(r, "status", 200) != 206:
                start = 0
            mode = "ab" if start > 0 else "wb"
            with open(p, mode) as f:
                while True:
                    if cancel and cancel():
                        return False
                    chunk = r.read(1024 * 512)
                    if not chunk:
                        break
                    f.write(chunk)
                    start += len(chunk)
                    if progress:
                        progress(os.path.basename(rel), done + start, MODEL_TOTAL_BYTES)
        done += size
    return model_status()[0]


def delete_model():
    """Hapus folder model (kalau user ingin mengunduh ulang)."""
    shutil.rmtree(model_dir(), ignore_errors=True)


# ---------------------------------------------------------------------------
# Rasio kanvas AI (9:16 / 16:9 / ikuti rasio video)
# ---------------------------------------------------------------------------
def _mult64(v, lo=256, hi=1088):
    return int(max(lo, min(hi, round(v / 64) * 64)))


def ai_canvas(rasio_key, video_ratio=None):
    """Ukuran kanvas AI (kelipatan 64). rasio_key: 'Ikuti rasio video' | '9:16' | '16:9'."""
    if rasio_key == "9:16":
        return 512, 896
    if rasio_key == "16:9":
        return 896, 512
    r = video_ratio if video_ratio and video_ratio > 0 else 16 / 9
    if r < 0.78:                       # potret
        return 512, _mult64(512 / r, hi=1088)
    if r <= 1.34:                      # persegi
        return 640, 640
    return _mult64(512 * r, hi=1088), 512


def poster_full_size(rasio_key, video_ratio=None):
    """Ukuran akhir poster resolusi tinggi."""
    if rasio_key == "9:16":
        return 1080, 1920
    if rasio_key == "16:9":
        return 1920, 1080
    w, h = ai_canvas("Ikuti rasio video", video_ratio)
    return w * 2, h * 2


RASIOS = ["Ikuti rasio video", "9:16 (Story/Reels)", "16:9 (Layar)"]


def rasio_label_to_key(label):
    if label.startswith("9:16"):
        return "9:16"
    if label.startswith("16:9"):
        return "16:9"
    return "Ikuti rasio video"


# ---------------------------------------------------------------------------
# Preset kualitas AI = jumlah langkah UNet yang benar-benar dijalankan
# ---------------------------------------------------------------------------
QUALITY_PRESETS = {
    "Cepat (1 langkah)": (1, 0.85),
    "Normal (2 langkah)": (4, 0.55),
    "Tinggi (3 langkah)": (4, 0.80),
    "Maksimal (4 langkah)": (4, 1.00),
}


# ---------------------------------------------------------------------------
# Prompt Indonesia -> Inggris
# ---------------------------------------------------------------------------
def build_style_prompt(user_prompt):
    """Terjemahkan prompt pengguna ke kata kunci gaya Inggris yang dipahami AI.
    Tulisan JUDUL di poster diurus mesin tipografi, bukan AI."""
    text = (user_prompt or "").strip() or DEFAULT_PROMPT
    text = re.sub(r"[^A-Za-z\s\-]", " ", text.lower())
    words = text.split()
    out, i = [], 0
    while i < len(words):
        two = " ".join(words[i:i + 2])
        if two in _TRANSLATE:
            out.append(_TRANSLATE[two])
            i += 2
            continue
        out.append(_TRANSLATE.get(words[i], words[i]))
        i += 1
    extra = [w for w in out if w]
    seen, uniq = set(), []
    for w in " ".join(extra).split():
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return _BASE_STYLE + ", " + ", ".join(uniq[:14])


# ---------------------------------------------------------------------------
# Tokenizer CLIP — implementasi manual persis CLIPTokenizer (tanpa torch):
# regex CLIP + BPE GPT-2 + akhiran "</w>" per kata. Ini penting: tanpa "</w>"
# id token salah dan AI tidak memahami prompt.
# ---------------------------------------------------------------------------
_CLIP_PAT = None
_BYTE_ENC = None


def _clip_pattern():
    global _CLIP_PAT
    if _CLIP_PAT is None:
        import regex as re
        _CLIP_PAT = re.compile(
            r"<\|startoftext\|>|<\|endoftext\|>|'s|'t|'re|'ve|'m|'ll|'d|"
            r"[\p{L}]+|[\p{N}]|[^\s\p{L}\p{N}]+")
    return _CLIP_PAT


def _bytes_to_unicode():
    global _BYTE_ENC
    if _BYTE_ENC is None:
        bs = (list(range(ord("!"), ord("~") + 1)) +
              list(range(ord("¡"), ord("¬") + 1)) +
              list(range(ord("®"), ord("ÿ") + 1)))
        cs = bs[:]
        n = 0
        for b in range(256):
            if b not in bs:
                bs.append(b)
                cs.append(256 + n)
                n += 1
        _BYTE_ENC = dict(zip(bs, [chr(c) for c in cs]))
    return _BYTE_ENC


class ClipTokenizer:
    """Tokenizer CLIP (OpenAI) versi murni-Python. Aman untuk offline & EXE."""

    def __init__(self, model_root):
        import json
        tok_dir = os.path.join(model_root, "tokenizer")
        with open(os.path.join(tok_dir, "vocab.json"), encoding="utf-8") as f:
            self.vocab = json.load(f)
        self.ranks = {}
        with open(os.path.join(tok_dir, "merges.txt"), encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                parts = line.split(" ")
                if len(parts) == 2:
                    self.ranks[(parts[0], parts[1])] = len(self.ranks)
        self._cache = {}
        self.byte_encoder = _bytes_to_unicode()

    @staticmethod
    def _pairs(word):
        return set(zip(word[:-1], word[1:]))

    def _bpe(self, token):
        """BPE GPT-2/CLIP: akhiran "</w>" dilekatkan ke KARAKTER TERAKHIR dulu
        (persis encoder OpenAI: tuple(token)[:-1] + (token[-1] + '</w>',))."""
        key = token
        if key in self._cache:
            return self._cache[key]
        if len(token) == 1:
            word = (token + "</w>",)
        else:
            word = tuple(token[:-1]) + (token[-1] + "</w>",)
        pairs = self._pairs(word)
        if not pairs:
            self._cache[key] = [word[0]]
            return [word[0]]
        while True:
            bigram = min(pairs, key=lambda p: self.ranks.get(p, float("inf")))
            if bigram not in self.ranks:
                break
            first, second = bigram
            new_word, i = [], 0
            while i < len(word):
                try:
                    j = word.index(first, i)
                except ValueError:
                    new_word.extend(word[i:])
                    break
                new_word.extend(word[i:j])
                i = j
                if word[i] == first and i < len(word) - 1 and word[i + 1] == second:
                    new_word.append(first + second)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            word = tuple(new_word)
            if len(word) == 1:
                break
            pairs = self._pairs(word)
        out = list(word)
        self._cache[key] = out
        return out

    def encode(self, text):
        """Return list id token (TANPA bos/eos — itu ditambahkan pipeline)."""
        text = re.sub(r"\s+", " ", (text or "").strip()).lower()
        be = self.byte_encoder
        ids = []
        for w in _clip_pattern().findall(text):
            tok = "".join(be[ord(c)] for c in w)
            for piece in self._bpe(tok):
                if piece in self.vocab:
                    ids.append(self.vocab[piece])
        return ids


def _clip_tokenizer(model_root):
    return ClipTokenizer(model_root)


# ---------------------------------------------------------------------------
# Jadwal Euler (EulerDiscrete, timestep_spacing="trailing", prediksi epsilon)
# ---------------------------------------------------------------------------
def _sigma_schedule():
    betas = np.linspace(0.00085 ** 0.5, 0.012 ** 0.5, 1000) ** 2
    ac = np.cumprod(1.0 - betas)
    return np.sqrt((1.0 - ac) / ac)          # sigma per timestep 0..999


# ---------------------------------------------------------------------------
# Mesin AI
# ---------------------------------------------------------------------------
# DLL runtime C++ yang dibutuhkan pyd onnxruntime di Windows. Urutan penting:
# runtime dulu, baru onnxruntime.dll, supaya Windows mengikat pyd ke salinan
# yang benar — msvcp140 tua dari lokasi lain adalah penyebab "access violation"
# saat memuat mesin AI di sebagian PC Windows.
_ORT_DLL_URUTAN = (
    "msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll",
    "onnxruntime.dll", "onnxruntime_providers_shared.dll",
)


def _dll_dirs_ort():
    """Folder kandidat berisi DLL mesin AI (capi paket + akar aplikasi beku)."""
    import importlib.util
    dirs = []
    spec = importlib.util.find_spec("onnxruntime")
    if spec and spec.origin:
        ort_dir = os.path.dirname(os.path.abspath(spec.origin))
        dirs.append(os.path.join(ort_dir, "capi"))
        dirs.append(ort_dir)
    if getattr(sys, "frozen", False):
        dirs.append(os.path.dirname(sys.executable))
        dirs.append(getattr(sys, "_MEIPASS", ""))
    else:
        dirs.append(os.path.dirname(os.path.abspath(__file__)))
    return [d for d in dirs if d and os.path.isdir(d)]


def muat_dll_windows():
    """Windows: muat DLL mesin AI secara eksplisit (path absolut) sebelum pyd
    onnxruntime diimpor, agar Windows tidak salah memilih versi runtime C++
    dari lokasi lain. DLL yang sudah termuat otomatis dilewati Windows.
    Return daftar nama DLL yang berhasil dimuat."""
    if sys.platform != "win32":
        return []
    import ctypes
    dirs = _dll_dirs_ort()
    for d in dirs:
        try:
            os.add_dll_directory(d)
        except (AttributeError, OSError):
            pass
    dimuat = []
    for dll in _ORT_DLL_URUTAN:
        for d in dirs:
            p = os.path.join(d, dll)
            if os.path.isfile(p):
                try:
                    ctypes.WinDLL(p)
                    dimuat.append(dll)
                except OSError:
                    pass
                break
    return dimuat


class PosterAI:
    """Pipeline SD-Turbo img2img berbasis onnxruntime, sesi dimuat malas."""

    def __init__(self, model_root=None, keep_loaded=False):
        self.root = model_root or model_dir()
        self.keep_loaded = keep_loaded
        self._sess = {}
        self._tok = None
        self.lock = threading.Lock()
        self._sigmas = _sigma_schedule()

    # ------------------------------------------------------------ internal
    def _session(self, name):
        if name in self._sess:
            return self._sess[name]
        try:
            muat_dll_windows()
            import onnxruntime as ort
        except Exception as exc:                       # noqa: BLE001
            raise RuntimeError(
                "Mesin AI (onnxruntime) tidak bisa dimuat di komputer ini: %r. "
                "Detail teknis ada di log_kesalahan.txt di samping aplikasi." % (exc,))
        so = ort.SessionOptions()
        so.intra_op_num_threads = min(16, max(1, (os.cpu_count() or 4)))
        so.inter_op_num_threads = 1
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        try:
            s = ort.InferenceSession(os.path.join(self.root, name, "model.onnx"),
                                     so, providers=["CPUExecutionProvider"])
        except Exception as exc:                       # noqa: BLE001
            raise RuntimeError(
                "Model AI gagal dimuat (bagian %s): %r. Pastikan unduhan model "
                "lengkap (tombol 🤖 Status Model AI); coba juga kualitas "
                "\"Cepat (1 langkah)\" atau PC lain." % (name, exc))
        if self.keep_loaded:
            self._sess[name] = s
        return s

    def free_all(self):
        self._sess.clear()

    def _run(self, name, feeds):
        """Jalankan sesi ONNX. Feeds dicocokkan berdasarkan nama; kalau nama
        tidak persis sama (tergantung konversi model), pakai urutan input.
        Setiap feed dikonversi ke tipe yang diDEKLARASIKAN sesi; bila kernel
        ORT di CPU tertentu tetap menuntut tipe lain (pilihan kernel bergantung
        fitur CPU — kasus nyata: timestep int64 ditolak, minta float), pesan
        galat ORT diparse, feed dikonversi, dan dicoba ulang sekali."""
        s = self._session(name)
        ins = list(s.get_inputs())
        by_name = {i.name: i for i in ins}
        want_np = {
            "tensor(float)": np.float32, "tensor(float16)": np.float16,
            "tensor(double)": np.float64,
            "tensor(int64)": np.int64, "tensor(int32)": np.int32,
            "tensor(int16)": np.int16, "tensor(int8)": np.int8,
            "tensor(bool)": np.bool_,
        }

        def cast(v, want):
            t = want_np.get(want)
            if t is not None and v.dtype != t:
                return v.astype(t)
            return v

        feed, used = {}, set()
        for k, v in feeds.items():
            if k in by_name:
                feed[k] = cast(v, by_name[k].type)
                used.add(k)
        if not used:                          # nama tidak cocok -> urutan saja
            for i, (k, v) in enumerate(feeds.items()):
                if i < len(ins):
                    feed[ins[i].name] = cast(v, ins[i].type)
        try:
            outs = s.run(None, feed)
        except Exception as exc:              # noqa: BLE001
            naik = RuntimeError(
                "Sesi %s menolak feed (%s). Detail: %s"
                % (name, ", ".join("%s:%s" % (k, v.dtype) for k, v in feed.items()),
                   exc))
            m = re.search(
                r"Actual: \(tensor\((\w+)\)\)\s*,\s*expected: \(tensor\((\w+)\)\)",
                str(exc))
            if not m:
                raise naik from exc
            np_asal = want_np.get("tensor(%s)" % m.group(1))
            np_tujuh = want_np.get("tensor(%s)" % m.group(2))
            if np_asal is None or np_tujuh is None:
                raise naik from exc
            for k, v in list(feed.items()):
                if v.dtype == np_asal:
                    feed[k] = v.astype(np_tujuh)
                    break
            else:
                raise naik from exc
            try:
                outs = s.run(None, feed)
            except Exception as exc2:         # noqa: BLE001
                raise naik from exc2
        return {o.name: v for o, v in zip(s.get_outputs(), outs)}

    def _encode_text(self, prompt):
        if self._tok is None:
            self._tok = _clip_tokenizer(self.root)
        bos, eos, pad = 49406, 49407, 49407
        enc = self._tok.encode(prompt)[:MAX_TOKENS - 2]
        ids = [bos] + enc + [eos]
        ids += [pad] * (MAX_TOKENS - len(ids))
        arr = np.asarray([ids], dtype=np.int32)
        out = self._run("text_encoder", {"input_ids": arr})
        return out["last_hidden_state"].astype(np.float32)

    def _prep_image(self, img, w, h):
        # crop cover agar pas rasio (persis strategi poster lama)
        r = w / h
        iw, ih = img.size
        if iw / ih > r:
            tw = int(ih * r)
            x0 = (iw - tw) // 2
            img = img.crop((x0, 0, x0 + tw, ih))
        else:
            th = int(iw / r)
            y0 = (ih - th) // 2
            img = img.crop((0, y0, iw, y0 + th))
        arr = np.asarray(img.resize((w, h), RESAMPLE).convert("RGB"), dtype=np.float32)
        arr = arr / 127.5 - 1.0
        return arr.transpose(2, 0, 1)[None]           # 1,3,H,W

    def _decode_latents(self, latents):
        z = (latents / VAE_SCALE).astype(np.float32)
        out = self._run("vae_decoder", {"latent_sample": z})
        img = next(iter(out.values())).astype(np.float32)[0]
        img = np.clip((img * 127.5 + 127.5).transpose(1, 2, 0), 0, 255).astype(np.uint8)
        return Image.fromarray(img)

    def _encode_image(self, img, w, h, t0_sigma, rng):
        x = self._prep_image(img, w, h)
        out = self._run("vae_encoder", {"sample": x})
        key = "latent_sample" if "latent_sample" in out else next(iter(out))
        lat = out[key].astype(np.float32) * VAE_SCALE
        # tampung noise sesuai sigma langkah awal: x = x0 + sigma * noise
        noise = rng.standard_normal(lat.shape, dtype=np.float32)
        return lat + t0_sigma * noise

    # ------------------------------------------------------------ public
    def ready(self):
        ok, _, _, _ = model_status()
        return ok

    def generate(self, init_img, prompt_text, size, quality_key="Normal (2 langkah)",
                 seed=None, progress=None):
        """Ubah init_img menjadi key art poster AI. Return PIL RGB image.
        progress(fase, info) — fase: 'encode', 'langkah', 'decode'.
        """
        assert self.ready(), "Model AI belum terunduh lengkap."
        w, h = size
        n_steps, strength = QUALITY_PRESETS.get(quality_key, QUALITY_PRESETS["Normal (2 langkah)"])

        # jadwal langkah + pemangkasan sesuai strength (ala diffusers img2img)
        timesteps = np.arange(1000, 0, -(1000 // n_steps)) - 1        # trailing
        sigmas = np.append(self._sigmas[timesteps], 0.0)
        init_ts = min(int(n_steps * strength), n_steps)
        t_start = max(n_steps - init_ts, 0)
        ts_used, sg_used = timesteps[t_start:], sigmas[t_start:]

        cond = self._encode_text(build_style_prompt(prompt_text))
        if progress:
            progress("encode", "AI menganalisis frame video…")
        if not self.keep_loaded:
            self._sess.pop("text_encoder", None)      # hemat RAM saat proses UNet

        with self.lock:
            if seed is None:
                seed = random.randrange(1 << 31)
            rng = np.random.default_rng(seed)
            lat = self._encode_image(init_img, w, h, float(sg_used[0]), rng)
            cond_h = cond.astype(np.float32)
            zero_cond = np.zeros((1, 256), dtype=np.float32)
            for i, t in enumerate(ts_used):
                # EulerDiscrete.scale_model_input: UNet menerima x / sqrt(sigma^2+1)
                sigma_i = float(sg_used[i])
                x_in = (lat / math.sqrt(sigma_i * sigma_i + 1.0)).astype(np.float32)
                out = self._run("unet", {"sample": x_in,
                                         "timestep": np.asarray([int(t)], dtype=np.int64),
                                         "encoder_hidden_states": cond_h,
                                         "timestep_cond": zero_cond})
                eps = next(iter(out.values())).astype(np.float32)
                lat = lat + (sg_used[i + 1] - sg_used[i]) * eps
                if progress:
                    progress("langkah", "AI menggambar langkah %d/%d…" % (i + 1, len(ts_used)))
            if progress:
                progress("decode", "Menyempurnakan gambar…")
            if not self.keep_loaded:
                self._sess.pop("unet", None)          # sebelum memuat VAE decoder
            art = self._decode_latents(lat)
            if not self.keep_loaded:
                self._sess.clear()
        return art
