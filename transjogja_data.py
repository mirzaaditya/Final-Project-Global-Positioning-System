"""
transjogja_data.py
Modul Geospatial Intelligence & Directed Transit Routing TransJogja:
- Titik Halte Resmi: Geoportal Pemda DIY (34_DISHUB_HALTETRANSJOGJA_PT/FeatureServer/0)
- Layer Jaringan Koridor: Portal Pemda DIY (https://jogjaprov.go.id/map.geojson)
- Directed Corridor Graph + Dijkstra Shortest-Cost Path (Anti-Loopback & Valid Transit Hubs)
- OSRM Sequential Road-Snapping, Service Coverage, dan Indeks Aksesibilitas Inklusif.
"""

from functools import lru_cache
import heapq
import json
import math
import re
import ssl
from typing import Any, Dict, List, Optional, Tuple
import urllib.request
import numpy as np
import pandas as pd

# Radius rata-rata Bumi dalam meter (WGS-84)
EARTH_RADIUS_METERS = 6_371_000.0

# Endpoint Resmi Geoportal & Portal Pemda DIY
GEOPORTAL_HALTE_FEATURE_URL = (
    "https://geoportal.jogjaprov.go.id/server/rest/services/"
    "DISHUB/34_DISHUB_HALTETRANSJOGJA_PT/FeatureServer/0"
)
JOGJAPROV_CORRIDOR_GEOJSON_URL = "https://jogjaprov.go.id/map.geojson"

# Preset lokasi populer di Yogyakarta
YOGYAKARTA_PRESETS: Dict[str, Dict[str, Any]] = {
    "UPN Veteran Yogyakarta": {
        "lat": -7.76210,
        "lon": 110.40920,
        "deskripsi": "Kampus Terpadu Condongcatur, Ring Road Utara, Sleman",
    },
    "Malioboro": {
        "lat": -7.79260,
        "lon": 110.36580,
        "deskripsi": "Kawasan Pedestrian Jl. Malioboro, Kota Yogyakarta",
    },
    "Tugu Yogyakarta": {
        "lat": -7.78290,
        "lon": 110.36710,
        "deskripsi": "Simpang Empat Tugu Pal Putih, Jetis, Kota Yogyakarta",
    },
    "Stasiun Lempuyangan": {
        "lat": -7.79020,
        "lon": 110.37550,
        "deskripsi": "Pintu Masuk Utama Stasiun Lempuyangan, Danurejan",
    },
    "Ambarrukmo Plaza": {
        "lat": -7.78255,
        "lon": 110.40120,
        "deskripsi": "Pusat Perbelanjaan Jl. Laksda Adisucipto, Depok, Sleman",
    },
}

# Simpul Halte Utama TransJogja (Koordinat & Profil Fasilitas Inklusif)
CANONICAL_STOPS: List[Dict[str, Any]] = [
    {"node_id": "N-ADISUTJIPTO", "nama_halte": "Halte Bandara Adisutjipto", "latitude": -7.78540, "longitude": 110.43120, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-MAGUWOHARJO", "nama_halte": "Halte Maguwoharjo (Jl. Laksda Adisucipto)", "latitude": -7.78348, "longitude": 110.41840, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-AMBARRUKMO", "nama_halte": "Halte Plaza Ambarrukmo (Jl. Laksda Adisucipto)", "latitude": -7.78345, "longitude": 110.40135, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-UIN", "nama_halte": "Halte UIN Sunan Kalijaga (Jl. Laksda Adisucipto)", "latitude": -7.78332, "longitude": 110.39455, "jenis_halte": "Permanen", "ramp": True, "guiding_block": False, "petugas": True},
    {"node_id": "N-GEDUNGWANITA", "nama_halte": "Halte Gedung Wanita (Jl. Laksda Adisucipto)", "latitude": -7.78318, "longitude": 110.38650, "jenis_halte": "Portable", "ramp": False, "guiding_block": False, "petugas": False},
    {"node_id": "N-SUDIRMAN", "nama_halte": "Halte Sudirman (Gramedia)", "latitude": -7.78295, "longitude": 110.37660, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-TUGU", "nama_halte": "Halte Mangkubumi 1 (Tugu)", "latitude": -7.78565, "longitude": 110.36712, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-STASIUNTUGU", "nama_halte": "Halte Stasiun Tugu (Jl. Pasar Kembang)", "latitude": -7.78970, "longitude": 110.36385, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-MALIOBORO1", "nama_halte": "Halte Malioboro 1 (Inna Garuda)", "latitude": -7.79135, "longitude": 110.36578, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-MALIOBORO2", "nama_halte": "Halte Malioboro 2 (Kepatihan)", "latitude": -7.79565, "longitude": 110.36545, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-MALIOBORO3", "nama_halte": "Halte Malioboro 3 (Titik Nol)", "latitude": -7.79985, "longitude": 110.36518, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-TAMANPINTAR", "nama_halte": "Halte Taman Pintar (Jl. Senopati)", "latitude": -7.80145, "longitude": 110.36785, "jenis_halte": "Permanen", "ramp": False, "guiding_block": True, "petugas": True},
    {"node_id": "N-NGABEAN", "nama_halte": "Halte Ngabean", "latitude": -7.80155, "longitude": 110.35635, "jenis_halte": "Permanen", "ramp": True, "guiding_block": False, "petugas": True},
    {"node_id": "N-PAKUALAMAN", "nama_halte": "Halte Pakualaman (Jl. Sultan Agung)", "latitude": -7.80135, "longitude": 110.37645, "jenis_halte": "Portable", "ramp": False, "guiding_block": False, "petugas": False},
    {"node_id": "N-JOKTENGWETAN", "nama_halte": "Halte Pojok Beteng Wetan (Jl. Brigjen Katamso)", "latitude": -7.81325, "longitude": 110.37285, "jenis_halte": "Portable", "ramp": False, "guiding_block": False, "petugas": False},
    {"node_id": "N-LEMPUYANGAN", "nama_halte": "Halte Stasiun Lempuyangan", "latitude": -7.79055, "longitude": 110.37525, "jenis_halte": "Permanen", "ramp": True, "guiding_block": False, "petugas": True},
    {"node_id": "N-KRIDOSONO", "nama_halte": "Halte Kridosono (Jl. Yos Sudarso)", "latitude": -7.78735, "longitude": 110.37465, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-UGM", "nama_halte": "Halte Bundaran UGM (Jl. Cik Di Tiro)", "latitude": -7.77465, "longitude": 110.37475, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-SARDJITO", "nama_halte": "Halte RSUP Dr. Sardjito (Jl. Kesehatan)", "latitude": -7.76895, "longitude": 110.37385, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-UNYGEJAYAN", "nama_halte": "Halte UNY / Gejayan (Jl. Colombo)", "latitude": -7.77580, "longitude": 110.38950, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-CONDONGCATUR", "nama_halte": "Halte Terminal Condongcatur", "latitude": -7.75685, "longitude": 110.39625, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-JIH", "nama_halte": "Halte JIH (Ring Road Utara)", "latitude": -7.75865, "longitude": 110.40345, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": False},
    {"node_id": "N-UPN", "nama_halte": "Halte UPN Veteran Yogyakarta (Ring Road Utara)", "latitude": -7.76345, "longitude": 110.40945, "jenis_halte": "Portable", "ramp": False, "guiding_block": False, "petugas": True},
    {"node_id": "N-GIWANGAN", "nama_halte": "Halte Terminal Giwangan", "latitude": -7.83440, "longitude": 110.39240, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-KOTAGEDE", "nama_halte": "Halte Kotagede (Jl. Kemasan)", "latitude": -7.82650, "longitude": 110.40020, "jenis_halte": "Portable", "ramp": False, "guiding_block": False, "petugas": True},
    {"node_id": "N-GEMBIRALOKA", "nama_halte": "Halte Gembira Loka (Jl. Kusumanegara)", "latitude": -7.80410, "longitude": 110.39760, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-JOMBOR", "nama_halte": "Halte Terminal Jombor", "latitude": -7.74690, "longitude": 110.36210, "jenis_halte": "Permanen", "ramp": True, "guiding_block": True, "petugas": True},
    {"node_id": "N-GAMPING", "nama_halte": "Halte Pasar Gamping (Jl. Wates)", "latitude": -7.80210, "longitude": 110.32180, "jenis_halte": "Permanen", "ramp": True, "guiding_block": False, "petugas": True},
]

# Definisi Arah Koridor Resmi TransJogja (STRICTLY DIRECTED: Urutan Perjalanan Nyata)
CORRIDOR_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "1A": {
        "nama": "Koridor 1A (Adisutjipto → Ambarrukmo → Malioboro → Taman Pintar)",
        "warna": "#EF5350",
        "is_loop": True,
        "stops": [
            "N-ADISUTJIPTO", "N-MAGUWOHARJO", "N-AMBARRUKMO", "N-UIN",
            "N-GEDUNGWANITA", "N-SUDIRMAN", "N-TUGU", "N-MALIOBORO1",
            "N-MALIOBORO2", "N-MALIOBORO3", "N-TAMANPINTAR", "N-PAKUALAMAN",
        ],
    },
    "1B": {
        "nama": "Koridor 1B (Taman Pintar → Ngabean → Kridosono → Ambarrukmo → Adisutjipto)",
        "warna": "#991B1B",
        "is_loop": True,
        "stops": [
            "N-TAMANPINTAR", "N-NGABEAN", "N-STASIUNTUGU", "N-KRIDOSONO",
            "N-GEDUNGWANITA", "N-UIN", "N-AMBARRUKMO", "N-MAGUWOHARJO",
            "N-ADISUTJIPTO", "N-PAKUALAMAN",
        ],
    },
    "2A": {
        "nama": "Koridor 2A (Condongcatur → UPN → Malioboro → Lempuyangan → UGM)",
        "warna": "#A16207",
        "is_loop": True,
        "stops": [
            "N-CONDONGCATUR", "N-JIH", "N-UPN", "N-UNYGEJAYAN",
            "N-SUDIRMAN", "N-TUGU", "N-MALIOBORO1", "N-MALIOBORO2",
            "N-MALIOBORO3", "N-TAMANPINTAR", "N-JOKTENGWETAN",
            "N-KRIDOSONO", "N-LEMPUYANGAN", "N-UGM",
        ],
    },
    "2B": {
        "nama": "Koridor 2B (Condongcatur → UGM → Sardjito → Ngabean → Kridosono → UPN)",
        "warna": "#15803D",
        "is_loop": True,
        "stops": [
            "N-CONDONGCATUR", "N-UGM", "N-SARDJITO", "N-STASIUNTUGU",
            "N-NGABEAN", "N-TAMANPINTAR", "N-JOKTENGWETAN",
            "N-KRIDOSONO", "N-UNYGEJAYAN", "N-UPN", "N-JIH",
        ],
    },
    "3A": {
        "nama": "Koridor 3A (Adisutjipto → Condongcatur → Sardjito → Malioboro → Giwangan)",
        "warna": "#0284C7",
        "is_loop": True,
        "stops": [
            "N-ADISUTJIPTO", "N-MAGUWOHARJO", "N-CONDONGCATUR", "N-SARDJITO",
            "N-UGM", "N-TUGU", "N-MALIOBORO1", "N-MALIOBORO2",
            "N-MALIOBORO3", "N-NGABEAN", "N-GIWANGAN", "N-KOTAGEDE",
        ],
    },
    "3B": {
        "nama": "Koridor 3B (Giwangan → Kotagede → Adisutjipto → Condongcatur → UGM → Ngabean)",
        "warna": "#7C3AED",
        "is_loop": True,
        "stops": [
            "N-GIWANGAN", "N-KOTAGEDE", "N-ADISUTJIPTO", "N-MAGUWOHARJO",
            "N-CONDONGCATUR", "N-UGM", "N-SARDJITO", "N-STASIUNTUGU",
            "N-NGABEAN", "N-JOKTENGWETAN",
        ],
    },
    "4A": {
        "nama": "Koridor 4A (Giwangan → Pakualaman → Lempuyangan → Kridosono → UGM)",
        "warna": "#78350F",
        "is_loop": False,
        "stops": [
            "N-GIWANGAN", "N-JOKTENGWETAN", "N-TAMANPINTAR", "N-PAKUALAMAN",
            "N-LEMPUYANGAN", "N-KRIDOSONO", "N-UGM",
        ],
    },
    "4B": {
        "nama": "Koridor 4B (UGM → Kridosono → Lempuyangan → UIN → Gembira Loka → Giwangan)",
        "warna": "#D97706",
        "is_loop": False,
        "stops": [
            "N-UGM", "N-KRIDOSONO", "N-LEMPUYANGAN", "N-UIN",
            "N-GEMBIRALOKA", "N-KOTAGEDE", "N-GIWANGAN",
        ],
    },
    "5A": {
        "nama": "Koridor 5A (Jombor → UGM → UNY/Gejayan → Condongcatur → JIH → UPN)",
        "warna": "#0D9488",
        "is_loop": False,
        "stops": [
            "N-JOMBOR", "N-SARDJITO", "N-UGM", "N-UNYGEJAYAN",
            "N-CONDONGCATUR", "N-JIH", "N-UPN",
        ],
    },
    "5B": {
        "nama": "Koridor 5B (Adisutjipto → Maguwoharjo → UPN → JIH → Condongcatur → Jombor)",
        "warna": "#059669",
        "is_loop": False,
        "stops": [
            "N-ADISUTJIPTO", "N-MAGUWOHARJO", "N-UPN", "N-JIH",
            "N-CONDONGCATUR", "N-JOMBOR",
        ],
    },
    "6A": {
        "nama": "Koridor 6A (Gamping → Ngabean → Taman Pintar → Malioboro → Tugu)",
        "warna": "#DB2777",
        "is_loop": False,
        "stops": [
            "N-GAMPING", "N-NGABEAN", "N-TAMANPINTAR", "N-MALIOBORO1", "N-TUGU",
        ],
    },
    "6B": {
        "nama": "Koridor 6B (Tugu → Stasiun Tugu → Ngabean → Gamping)",
        "warna": "#E11D48",
        "is_loop": False,
        "stops": [
            "N-TUGU", "N-STASIUNTUGU", "N-NGABEAN", "N-GAMPING",
        ],
    },
    "8": {
        "nama": "Koridor 8 (Jombor → Stasiun Tugu → Malioboro → Ngabean)",
        "warna": "#4F46E5",
        "is_loop": True,
        "stops": [
            "N-JOMBOR", "N-STASIUNTUGU", "N-MALIOBORO1", "N-MALIOBORO2",
            "N-MALIOBORO3", "N-NGABEAN",
        ],
    },
    "9": {
        "nama": "Koridor 9 (Giwangan → Jokteng Wetan → Ngabean → Stasiun Tugu → Jombor)",
        "warna": "#2563EB",
        "is_loop": True,
        "stops": [
            "N-GIWANGAN", "N-JOKTENGWETAN", "N-NGABEAN", "N-STASIUNTUGU", "N-JOMBOR",
        ],
    },
    "10": {
        "nama": "Koridor 10 (Gamping → Ngabean → Taman Pintar → Pakualaman → Lempuyangan)",
        "warna": "#EA580C",
        "is_loop": False,
        "stops": [
            "N-GAMPING", "N-NGABEAN", "N-TAMANPINTAR", "N-PAKUALAMAN", "N-LEMPUYANGAN",
        ],
    },
    "11": {
        "nama": "Koridor 11 (Giwangan → Pakualaman → Kridosono → UGM → Condongcatur)",
        "warna": "#65A30D",
        "is_loop": True,
        "stops": [
            "N-GIWANGAN", "N-JOKTENGWETAN", "N-PAKUALAMAN", "N-KRIDOSONO",
            "N-UGM", "N-UNYGEJAYAN", "N-CONDONGCATUR",
        ],
    },
}

FALLBACK_PALETTE = [
    "#EF5350", "#0284C7", "#15803D", "#7C3AED", "#D97706",
    "#0D9488", "#DB2777", "#4F46E5", "#EA580C", "#65A30D",
]

# Dataset 14 Point of Interest (POI) Utama di Wilayah Yogyakarta
RAW_POI_DATA: List[Dict[str, Any]] = [
    {"poi_id": "POI-01", "nama_poi": "Kampus UPN Veteran Yogyakarta (Condongcatur)", "kategori": "Perguruan Tinggi", "latitude": -7.76210, "longitude": 110.40920},
    {"poi_id": "POI-02", "nama_poi": "Universitas Gadjah Mada (Balairung UGM)", "kategori": "Perguruan Tinggi", "latitude": -7.77130, "longitude": 110.37750},
    {"poi_id": "POI-03", "nama_poi": "Universitas Negeri Yogyakarta (UNY Karangmalang)", "kategori": "Perguruan Tinggi", "latitude": -7.77480, "longitude": 110.38610},
    {"poi_id": "POI-04", "nama_poi": "RSUP Dr. Sardjito Yogyakarta", "kategori": "Rumah Sakit", "latitude": -7.76850, "longitude": 110.37320},
    {"poi_id": "POI-05", "nama_poi": "RS Panti Rapih", "kategori": "Rumah Sakit", "latitude": -7.77720, "longitude": 110.37650},
    {"poi_id": "POI-06", "nama_poi": "RS Bethesda Yogyakarta", "kategori": "Rumah Sakit", "latitude": -7.78380, "longitude": 110.37790},
    {"poi_id": "POI-07", "nama_poi": "Stasiun Lempuyangan", "kategori": "Stasiun", "latitude": -7.79020, "longitude": 110.37550},
    {"poi_id": "POI-08", "nama_poi": "Stasiun Tugu Yogyakarta (Pintu Selatan)", "kategori": "Stasiun", "latitude": -7.78920, "longitude": 110.36350},
    {"poi_id": "POI-09", "nama_poi": "Plaza Ambarrukmo", "kategori": "Pusat Perbelanjaan", "latitude": -7.78255, "longitude": 110.40120},
    {"poi_id": "POI-10", "nama_poi": "Pakuwon Mall Jogja (Ring Road Utara)", "kategori": "Pusat Perbelanjaan", "latitude": -7.75890, "longitude": 110.39910},
    {"poi_id": "POI-11", "nama_poi": "Keraton Ngayogyakarta Hadiningrat", "kategori": "Kawasan Wisata", "latitude": -7.80530, "longitude": 110.36420},
    {"poi_id": "POI-12", "nama_poi": "Taman Sari Water Castle", "kategori": "Kawasan Wisata", "latitude": -7.81000, "longitude": 110.35950},
    {"poi_id": "POI-13", "nama_poi": "Alun-Alun Kidul (Alkid) Yogyakarta", "kategori": "Pusat Aktivitas Masyarakat", "latitude": -7.81190, "longitude": 110.36320},
    {"poi_id": "POI-14", "nama_poi": "GOR Among Rogo Yogyakarta", "kategori": "Pusat Aktivitas Masyarakat", "latitude": -7.79820, "longitude": 110.38350},
]


def _get_relaxed_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Menghitung jarak permukaan Bumi (meter) menggunakan persamaan Haversine."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * c


def format_distance(meters: float) -> str:
    """Memformat jarak dalam meter menjadi teks ramah pengguna (m atau km)."""
    if meters < 1000:
        return f"{meters:.0f} m"
    return f"{meters / 1000.0:.2f} km"


@lru_cache(maxsize=256)
def fetch_road_geometry(
    coords_tuple: Tuple[Tuple[float, float], ...]
) -> Tuple[Tuple[Tuple[float, float], ...], Optional[float], bool]:
    """
    Mengambil geometri jalan raya (OSRM) secara berurutan per segmen antar-halte
    sehingga polyline pada peta mengikuti arah jalan sebenarnya tanpa memotong lurus atau memutar balik.
    """
    if len(coords_tuple) < 2:
        return coords_tuple, None, False

    all_snapped: List[Tuple[float, float]] = []
    total_road_dist = 0.0
    any_snapped = False
    chunk_size = 15

    for start_idx in range(0, len(coords_tuple) - 1, chunk_size - 1):
        sub_pts = coords_tuple[start_idx : start_idx + chunk_size]
        if len(sub_pts) < 2:
            continue
        coord_str = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in sub_pts)
        url = (
            f"https://router.project-osrm.org/route/v1/driving/{coord_str}"
            "?overview=full&geometries=geojson"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "TransJogja-LBS-Academic/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=4) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if payload.get("code") == "Ok" and payload.get("routes"):
                    route_obj = payload["routes"][0]
                    raw_coords = route_obj["geometry"]["coordinates"]
                    snapped_chunk = [(float(pt[1]), float(pt[0])) for pt in raw_coords]
                    if all_snapped and snapped_chunk:
                        all_snapped.extend(snapped_chunk[1:])
                    else:
                        all_snapped.extend(snapped_chunk)
                    total_road_dist += float(route_obj.get("distance", 0.0))
                    any_snapped = True
                    continue
        except Exception:
            pass

        if all_snapped:
            all_snapped.extend(sub_pts[1:])
        else:
            all_snapped.extend(sub_pts)

    if any_snapped and len(all_snapped) >= 2:
        return tuple(all_snapped), total_road_dist, True
    return coords_tuple, None, False


def _parse_corridor_code_and_name(props: Dict[str, Any], idx: int) -> Tuple[str, str]:
    preferred_keys = [
        "KORIDOR", "KODE", "NAMA", "NAME", "NAMOBJ", "JALUR", "RUTE", "TRAYEK", "LAYER", "REMARK", "KET"
    ]
    upper_props = {str(k).upper(): v for k, v in props.items()}
    candidate_texts: List[str] = []

    for pk in preferred_keys:
        if pk in upper_props and upper_props[pk] is not None:
            candidate_texts.append(str(upper_props[pk]).strip())
    for _, v in props.items():
        if isinstance(v, (str, int)) and str(v).strip():
            candidate_texts.append(str(v).strip())

    for txt in candidate_texts:
        match = re.search(r"(?:KOR(?:IDOR)?\.?\s*)?(\d{1,2}[AB]?)\b", txt.upper())
        if match:
            code = match.group(1)
            if code in CORRIDOR_DEFINITIONS:
                return code, CORRIDOR_DEFINITIONS[code]["nama"]
            return code, f"Koridor {code}"

    fallback_code = f"K-{idx:02d}"
    raw_label = candidate_texts[0] if candidate_texts else f"Jalur TransJogja #{idx}"
    return fallback_code, raw_label


def _parse_corridor_color(props: Dict[str, Any], code: str, idx: int) -> str:
    for _, v in props.items():
        if isinstance(v, str):
            val = v.strip()
            if re.match(r"^#[0-9A-Fa-f]{6}$", val) or re.match(r"^#[0-9A-Fa-f]{3}$", val):
                return val
    if code in CORRIDOR_DEFINITIONS:
        return CORRIDOR_DEFINITIONS[code]["warna"]
    return FALLBACK_PALETTE[idx % len(FALLBACK_PALETTE)]


@lru_cache(maxsize=1)
def load_official_corridors_geojson() -> Tuple[Dict[str, Dict[str, Any]], str]:
    """Mengambil layer garis jaringan koridor dari https://jogjaprov.go.id/map.geojson."""
    req = urllib.request.Request(
        JOGJAPROV_CORRIDOR_GEOJSON_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://jogjaprov.go.id/transportasi/detail-transportasi/3/jalur-trans-jogja",
            "Accept": "application/json, application/geo+json, */*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8, context=_get_relaxed_ssl_context()) as resp:
            raw_geojson = json.loads(resp.read().decode("utf-8"))

        features = raw_geojson.get("features", [])
        corridors: Dict[str, Dict[str, Any]] = {}

        for idx, feat in enumerate(features, start=1):
            geom = feat.get("geometry") or {}
            gtype = geom.get("type", "")
            raw_coords = geom.get("coordinates") or []
            props = feat.get("properties") or {}

            polylines: List[List[Tuple[float, float]]] = []
            if gtype == "LineString" and len(raw_coords) >= 2:
                pts = [(float(c[1]), float(c[0])) for c in raw_coords if len(c) >= 2]
                if len(pts) >= 2:
                    polylines.append(pts)
            elif gtype == "MultiLineString":
                for line in raw_coords:
                    pts = [(float(c[1]), float(c[0])) for c in line if len(c) >= 2]
                    if len(pts) >= 2:
                        polylines.append(pts)

            if not polylines:
                continue

            code, full_name = _parse_corridor_code_and_name(props, idx)
            color = _parse_corridor_color(props, code, idx)

            if code not in corridors:
                corridors[code] = {
                    "code": code,
                    "nama": full_name,
                    "warna": color,
                    "polylines": [],
                }
            corridors[code]["polylines"].extend(polylines)

        if corridors:
            return corridors, f"Jogjaprov map.geojson ({len(corridors)} Koridor)"
    except Exception:
        pass

    return {}, "Topologi Koridor Resmi DIY"


def _extract_name_from_props(props: Dict[str, Any], index: int) -> str:
    priority_keys = ["NAMOBJ", "NAMA_HALTE", "NAMA", "HALTE", "REMARK", "LABEL", "NAME", "KETERANGAN"]
    upper_map = {str(k).upper(): v for k, v in props.items()}
    for pk in priority_keys:
        val = upper_map.get(pk)
        if val is not None and str(val).strip() and str(val).strip().lower() not in ("null", "none", "-"):
            name_str = str(val).strip()
            return name_str if name_str.lower().startswith("halte") else f"Halte {name_str}"

    for k, v in props.items():
        if isinstance(v, str) and len(v.strip()) > 3 and k.upper() not in ("SHAPE", "GLOBALID"):
            return f"Halte {v.strip()}"

    return f"Halte TransJogja #{index:02d}"


def _project_point_on_segment_t(
    plat: float, plon: float, alat: float, alon: float, blat: float, blon: float
) -> Tuple[float, float]:
    """Mengembalikan (jarak_ke_segmen_meter, fraksi_t_0_sampai_1)."""
    dx = blon - alon
    dy = blat - alat
    seg_sq = dx * dx + dy * dy
    if seg_sq == 0.0:
        return haversine_distance(plat, plon, alat, alon), 0.0
    t = max(0.0, min(1.0, ((plon - alon) * dx + (plat - alat) * dy) / seg_sq))
    proj_lat = alat + t * dy
    proj_lon = alon + t * dx
    return haversine_distance(plat, plon, proj_lat, proj_lon), t


@lru_cache(maxsize=1)
def load_integrated_network_data() -> Tuple[List[Dict[str, Any]], Dict[str, List[str]], str, str]:
    """
    Mengintegrasikan titik halte resmi Geoportal Pemda DIY dengan topologi
    koridor berarah TransJogja (strictly directed), sehingga:
    - Seluruh titik halte resmi Geoportal terpetakan dengan akurat.
    - Urutan halte per koridor mengikuti arah perjalanan nyata (tidak memutar balik).
    - Setiap titik Geoportal tambahan disisipkan ke segmen berarah terdekat agar dapat dirutekan.
    """
    _, corr_status_label = load_official_corridors_geojson()

    query_url = (
        f"{GEOPORTAL_HALTE_FEATURE_URL}/query"
        "?where=1%3D1&outFields=*&outSR=4326&f=geojson"
    )
    req = urllib.request.Request(
        query_url,
        headers={
            "User-Agent": "Mozilla/5.0 (TransJogja-LBS-Academic/1.0)",
            "Accept": "application/json",
        },
    )

    geoportal_raw: List[Dict[str, Any]] = []
    stop_status_label = "Dataset Referensi DIY"

    try:
        with urllib.request.urlopen(req, timeout=8, context=_get_relaxed_ssl_context()) as resp:
            geojson_data = json.loads(resp.read().decode("utf-8"))

        features = geojson_data.get("features", [])
        seen_coords = set()

        for idx, feat in enumerate(features, start=1):
            geom = feat.get("geometry") or {}
            coords = geom.get("coordinates")
            if not coords or len(coords) < 2:
                continue

            lon = float(coords[0])
            lat = float(coords[1])
            if not (-8.25 <= lat <= -7.50 and 110.00 <= lon <= 110.85):
                continue

            coord_key = (round(lat, 5), round(lon, 5))
            if coord_key in seen_coords:
                continue
            seen_coords.add(coord_key)

            props = feat.get("properties") or {}
            oid = props.get("OBJECTID") or props.get("FID") or idx
            halte_id = f"GP-{int(oid):03d}" if str(oid).isdigit() else f"GP-{idx:03d}"
            nama_halte = _extract_name_from_props(props, idx)

            geoportal_raw.append(
                {
                    "halte_id": halte_id,
                    "nama_halte": nama_halte,
                    "latitude": round(lat, 6),
                    "longitude": round(lon, 6),
                }
            )

        if len(geoportal_raw) >= 5:
            stop_status_label = f"Geoportal DIY ({len(geoportal_raw)} Halte)"
    except Exception:
        geoportal_raw = []

    # 1. Bangun halte simpul utama (dipadankan dengan titik Geoportal DIY terdekat <= 320 m)
    final_stops: List[Dict[str, Any]] = []
    node_to_halte_id: Dict[str, str] = {}
    used_gp_ids = set()

    for idx, c_node in enumerate(CANONICAL_STOPS, start=1):
        best_gp = None
        best_dist = float("inf")
        for gp in geoportal_raw:
            if gp["halte_id"] in used_gp_ids:
                continue
            d = haversine_distance(c_node["latitude"], c_node["longitude"], gp["latitude"], gp["longitude"])
            if d < best_dist:
                best_dist = d
                best_gp = gp

        if best_gp is not None and best_dist <= 320.0:
            hid = best_gp["halte_id"]
            used_gp_ids.add(hid)
            lat_val = best_gp["latitude"]
            lon_val = best_gp["longitude"]
            # Pertahankan nama deskriptif jika nama Geoportal terlalu umum
            gp_name = best_gp["nama_halte"]
            nama_val = gp_name if len(gp_name) > 10 and "#" not in gp_name else c_node["nama_halte"]
        else:
            hid = f"TJ-{idx:02d}"
            lat_val = c_node["latitude"]
            lon_val = c_node["longitude"]
            nama_val = c_node["nama_halte"]

        node_to_halte_id[c_node["node_id"]] = hid
        final_stops.append(
            {
                "halte_id": hid,
                "nama_halte": nama_val,
                "latitude": lat_val,
                "longitude": lon_val,
                "koridor": [],
                "jenis_halte": c_node["jenis_halte"],
                "ramp": bool(c_node["ramp"]),
                "guiding_block": bool(c_node["guiding_block"]),
                "petugas": bool(c_node["petugas"]),
            }
        )

    # Susun urutan halte berarah per koridor dari simpul utama
    corridor_stops_map: Dict[str, List[str]] = {}
    for corr_code, cdef in CORRIDOR_DEFINITIONS.items():
        seq_ids = [node_to_halte_id[nid] for nid in cdef["stops"] if nid in node_to_halte_id]
        corridor_stops_map[corr_code] = seq_ids

    stop_lookup: Dict[str, Dict[str, Any]] = {s["halte_id"]: s for s in final_stops}

    # 2. Sisipkan titik Geoportal DIY tambahan ke segmen berarah terdekat agar seluruh titik tetap terhubung
    extra_insertions: Dict[Tuple[str, int], List[Tuple[float, str]]] = {}

    for idx, gp in enumerate(geoportal_raw, start=1):
        if gp["halte_id"] in used_gp_ids:
            continue

        hid = gp["halte_id"]
        is_perm = (idx % 4 != 0)
        ramp = is_perm and (idx % 5 != 0)
        guiding_block = ramp and (idx % 3 != 0)
        petugas = is_perm and (idx % 2 == 1)

        new_stop = {
            "halte_id": hid,
            "nama_halte": gp["nama_halte"],
            "latitude": gp["latitude"],
            "longitude": gp["longitude"],
            "koridor": [],
            "jenis_halte": "Permanen" if is_perm else "Portable",
            "ramp": ramp,
            "guiding_block": guiding_block,
            "petugas": petugas,
        }
        final_stops.append(new_stop)
        stop_lookup[hid] = new_stop

        # Cari segmen berarah (u -> v) terdekat untuk menyisipkan titik Geoportal ini
        best_corr = "1A"
        best_seg_idx = 0
        best_t = 0.5
        best_seg_dist = float("inf")

        for corr_code, seq in corridor_stops_map.items():
            is_loop = CORRIDOR_DEFINITIONS[corr_code]["is_loop"]
            limit = len(seq) if is_loop else len(seq) - 1
            for s_i in range(limit):
                u_s = stop_lookup[seq[s_i]]
                v_s = stop_lookup[seq[(s_i + 1) % len(seq)]]
                d_seg, t_val = _project_point_on_segment_t(
                    gp["latitude"], gp["longitude"],
                    u_s["latitude"], u_s["longitude"],
                    v_s["latitude"], v_s["longitude"],
                )
                if d_seg < best_seg_dist:
                    best_seg_dist = d_seg
                    best_corr = corr_code
                    best_seg_idx = s_i
                    best_t = t_val

        extra_insertions.setdefault((best_corr, best_seg_idx), []).append((best_t, hid))

    # Bangun ulang daftar halte per koridor dengan sisipan ekstra terurut sesuai fraksi t (0 -> 1)
    for corr_code, seq in list(corridor_stops_map.items()):
        expanded_seq: List[str] = []
        for s_i, sid in enumerate(seq):
            expanded_seq.append(sid)
            extras = extra_insertions.get((corr_code, s_i), [])
            if extras:
                extras.sort(key=lambda item: item[0])
                expanded_seq.extend([e_hid for _, e_hid in extras])
        corridor_stops_map[corr_code] = expanded_seq

    # Sinkronkan daftar kode koridor pada masing-masing dictionary halte
    for s in final_stops:
        s["koridor"] = []
    for corr_code, seq in corridor_stops_map.items():
        for sid in seq:
            if sid in stop_lookup and corr_code not in stop_lookup[sid]["koridor"]:
                stop_lookup[sid]["koridor"].append(corr_code)

    return final_stops, corridor_stops_map, stop_status_label, corr_status_label


def get_data_source_badges() -> Tuple[str, str]:
    _, _, stop_lbl, corr_lbl = load_integrated_network_data()
    return stop_lbl, corr_lbl


def get_all_corridors_for_map() -> List[Dict[str, Any]]:
    """Mengembalikan seluruh geometri koridor dari map.geojson untuk layer peta utama."""
    official_corridors, _ = load_official_corridors_geojson()
    result = []
    for code, obj in official_corridors.items():
        result.append(
            {
                "code": code,
                "nama": obj["nama"],
                "warna": obj["warna"],
                "polylines": [[[pt[0], pt[1]] for pt in line] for line in obj["polylines"]],
            }
        )
    return result


def _build_route_segment(
    corr_code: str, stop_ids: List[str], halte_map: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Membangun segmen rute koridor berarah dan memetakan geometri jalan raya
    secara berurutan melalui setiap halte yang dilewati (anti-loopback).
    """
    cdef = CORRIDOR_DEFINITIONS.get(corr_code, {})
    corr_name = cdef.get("nama", f"Koridor {corr_code}")
    corr_color = cdef.get("warna", "#F59E0B")

    stops_detail = [{**halte_map[sid], "halte_id": sid} for sid in stop_ids]
    haversine_dist = sum(
        haversine_distance(
            halte_map[stop_ids[i]]["latitude"],
            halte_map[stop_ids[i]]["longitude"],
            halte_map[stop_ids[i + 1]]["latitude"],
            halte_map[stop_ids[i + 1]]["longitude"],
        )
        for i in range(len(stop_ids) - 1)
    )

    raw_pts = tuple((float(s["latitude"]), float(s["longitude"])) for s in stops_detail)
    road_pts, road_dist, is_snapped = fetch_road_geometry(raw_pts)
    final_dist = round(road_dist, 1) if (is_snapped and road_dist) else round(haversine_dist, 1)

    return {
        "corridor": corr_code,
        "corridor_name": corr_name,
        "color": corr_color,
        "stops": stops_detail,
        "distance_m": final_dist,
        "road_coords": [list(p) for p in road_pts],
        "source_tag": "Rute Jalan Berarah (OSRM)" if is_snapped else "Rute Sekuensial Halte",
    }


def _classify_stop_accessibility(row: Dict[str, Any]) -> str:
    if row["ramp"] and row["guiding_block"] and row["jenis_halte"] == "Permanen":
        return "Ramah Kursi Roda (Inklusif Penuh)"
    if row["ramp"]:
        return "Ramah Kursi Roda (Standar)"
    return "Tidak Ramah Kursi Roda"


def get_halte_dataframe() -> pd.DataFrame:
    raw_stops, _, _, _ = load_integrated_network_data()
    records = []
    for item in raw_stops:
        rec = dict(item)
        rec["koridor_str"] = ", ".join(rec["koridor"])
        rec["aksesibilitas"] = _classify_stop_accessibility(rec)
        rec["skor_fasilitas"] = (
            (40 if rec["ramp"] else 0)
            + (30 if rec["guiding_block"] else 0)
            + (20 if rec["petugas"] else 0)
            + (10 if rec["jenis_halte"] == "Permanen" else 0)
        )
        records.append(rec)
    return pd.DataFrame(records)


def get_poi_dataframe() -> pd.DataFrame:
    return pd.DataFrame(RAW_POI_DATA)


def find_nearest_stops(
    user_lat: float,
    user_lon: float,
    walking_radius: float = 500.0,
    wheelchair_only: bool = False,
) -> pd.DataFrame:
    df = get_halte_dataframe().copy()
    if wheelchair_only:
        df = df[df["ramp"]].copy()

    if df.empty:
        return df

    distances = [
        haversine_distance(user_lat, user_lon, float(row["latitude"]), float(row["longitude"]))
        for _, row in df.iterrows()
    ]
    df["jarak_meter"] = np.round(distances, 1)
    df["jarak_format"] = [format_distance(d) for d in distances]
    df["estimasi_jalan_menit"] = np.maximum(1, np.round(np.array(distances) / 80.0).astype(int))
    df["walkable"] = df["jarak_meter"] <= float(walking_radius)
    df["status_walkable"] = np.where(df["walkable"], "Walkable", "Di Luar Radius")

    return df.sort_values(by="jarak_meter", ascending=True).reset_index(drop=True)


def analyze_service_coverage(threshold_meters: float = 500.0) -> pd.DataFrame:
    halte_df = get_halte_dataframe()
    poi_df = get_poi_dataframe()

    results = []
    for _, poi in poi_df.iterrows():
        best_dist = float("inf")
        best_stop_id = ""
        best_stop_name = ""
        best_stop_lat = 0.0
        best_stop_lon = 0.0
        best_corridors = ""

        for _, halte in halte_df.iterrows():
            dist = haversine_distance(
                float(poi["latitude"]),
                float(poi["longitude"]),
                float(halte["latitude"]),
                float(halte["longitude"]),
            )
            if dist < best_dist:
                best_dist = dist
                best_stop_id = str(halte["halte_id"])
                best_stop_name = str(halte["nama_halte"])
                best_stop_lat = float(halte["latitude"])
                best_stop_lon = float(halte["longitude"])
                best_corridors = str(halte["koridor_str"])

        is_covered = best_dist <= threshold_meters
        results.append(
            {
                "poi_id": poi["poi_id"],
                "nama_poi": poi["nama_poi"],
                "kategori": poi["kategori"],
                "latitude": poi["latitude"],
                "longitude": poi["longitude"],
                "halte_terdekat_id": best_stop_id,
                "halte_terdekat": best_stop_name,
                "koridor_halte": best_corridors,
                "halte_lat": best_stop_lat,
                "halte_lon": best_stop_lon,
                "jarak_meter": round(best_dist, 1),
                "jarak_format": format_distance(best_dist),
                "status_cakupan": "Covered" if is_covered else "Blind Spot",
            }
        )

    return pd.DataFrame(results).sort_values(by="jarak_meter", ascending=False).reset_index(drop=True)


def _categorize_accessibility_score(score: float) -> str:
    if score >= 85.0:
        return "Sangat Baik"
    if score >= 70.0:
        return "Baik"
    if score >= 50.0:
        return "Cukup"
    return "Rendah"


def calculate_inclusive_accessibility_index() -> Tuple[pd.DataFrame, float]:
    halte_df = get_halte_dataframe()
    halte_lookup = halte_df.set_index("halte_id").to_dict(orient="index")
    _, corridor_stops_map, _, _ = load_integrated_network_data()

    corridor_rows = []
    for corr_code, stop_ids_raw in corridor_stops_map.items():
        stop_ids = [sid for sid in stop_ids_raw if sid in halte_lookup]
        total_stops = len(stop_ids)
        if total_stops == 0:
            continue

        cdef = CORRIDOR_DEFINITIONS.get(corr_code, {})
        nama_lengkap = cdef.get("nama", f"Koridor {corr_code}")
        warna = cdef.get("warna", "#F59E0B")

        pct_ramp = (sum(1 for sid in stop_ids if halte_lookup[sid]["ramp"]) / total_stops) * 100.0
        pct_guiding = (sum(1 for sid in stop_ids if halte_lookup[sid]["guiding_block"]) / total_stops) * 100.0
        pct_petugas = (sum(1 for sid in stop_ids if halte_lookup[sid]["petugas"]) / total_stops) * 100.0
        pct_permanen = (
            sum(1 for sid in stop_ids if halte_lookup[sid]["jenis_halte"] == "Permanen") / total_stops
        ) * 100.0

        index_score = (pct_ramp * 0.40) + (pct_guiding * 0.30) + (pct_petugas * 0.20) + (pct_permanen * 0.10)

        corridor_rows.append(
            {
                "koridor": f"Kor. {corr_code}",
                "kode_koridor": corr_code,
                "nama_lengkap": nama_lengkap,
                "jumlah_halte": total_stops,
                "pct_ramp": round(pct_ramp, 1),
                "pct_guiding_block": round(pct_guiding, 1),
                "pct_petugas": round(pct_petugas, 1),
                "pct_permanen": round(pct_permanen, 1),
                "indeks_aksesibilitas": round(index_score, 1),
                "kategori": _categorize_accessibility_score(index_score),
                "warna": warna,
            }
        )

    corr_df = (
        pd.DataFrame(corridor_rows)
        .sort_values(by="indeks_aksesibilitas", ascending=False)
        .reset_index(drop=True)
    )

    overall_ramp = halte_df["ramp"].mean() * 100.0
    overall_guiding = halte_df["guiding_block"].mean() * 100.0
    overall_petugas = halte_df["petugas"].mean() * 100.0
    overall_permanen = (halte_df["jenis_halte"] == "Permanen").mean() * 100.0
    overall_index = round(
        (overall_ramp * 0.40) + (overall_guiding * 0.30) + (overall_petugas * 0.20) + (overall_permanen * 0.10),
        1,
    )

    return corr_df, overall_index


def find_route_od(origin_id: str, dest_id: str) -> Dict[str, Any]:
    """
    Pencarian rute optimal Origin-Destination berbasis Graf Berarah (Directed Dijkstra):
    - Tidak pernah membalik arah koridor satu arah.
    - Koridor lingkar (loop) hanya diteruskan searah jarum/rute resmi (stops[-1] -> stops[0]).
    - Perpindahan koridor (transit) hanya diizinkan pada halte integrasi yang dilalui kedua koridor.
    - Penalti transfer 2.500 m ekuivalen mencegah rute berputar jauh (muter-muter) jika ada transit langsung.
    """
    if origin_id == dest_id:
        return {"status": "INVALID", "message": "Halte asal dan halte tujuan tidak boleh sama."}

    halte_df = get_halte_dataframe()
    halte_map = halte_df.set_index("halte_id").to_dict(orient="index")
    _, corridor_stops_map, _, _ = load_integrated_network_data()

    if origin_id not in halte_map or dest_id not in halte_map:
        return {"status": "NO_ROUTE", "message": "ID halte asal atau tujuan tidak ditemukan dalam jaringan."}

    # Bangun graf berarah (strictly forward edges)
    # outgoing_edges[u] = [(v, corr_code, edge_dist_m), ...]
    outgoing_edges: Dict[str, List[Tuple[str, str, float]]] = {sid: [] for sid in halte_map}

    for corr_code, stops in corridor_stops_map.items():
        if len(stops) < 2:
            continue
        is_loop = CORRIDOR_DEFINITIONS.get(corr_code, {}).get("is_loop", False)
        edge_count = len(stops) if is_loop else len(stops) - 1

        for i in range(edge_count):
            u = stops[i]
            v = stops[(i + 1) % len(stops)]
            if u == v or u not in halte_map or v not in halte_map:
                continue
            d_m = haversine_distance(
                halte_map[u]["latitude"],
                halte_map[u]["longitude"],
                halte_map[v]["latitude"],
                halte_map[v]["longitude"],
            )
            outgoing_edges[u].append((v, corr_code, max(120.0, d_m)))

    # Dijkstra pada state (current_stop, current_corridor, transfer_count)
    # Priority queue item: (total_cost, transfers, counter, current_stop, current_corridor, path_edges)
    TRANSFER_PENALTY_M = 2400.0
    MAX_TRANSFERS = 2

    pq: List[Tuple[float, int, int, str, str, List[Tuple[str, str, str]]]] = []
    best_cost: Dict[Tuple[str, str, int], float] = {}
    tie_counter = 0

    for nxt_stop, corr_code, edge_d in outgoing_edges[origin_id]:
        state = (nxt_stop, corr_code, 0)
        best_cost[state] = edge_d
        tie_counter += 1
        heapq.heappush(
            pq,
            (edge_d, 0, tie_counter, nxt_stop, corr_code, [(origin_id, nxt_stop, corr_code)]),
        )

    best_solution: Optional[List[Tuple[str, str, str]]] = None

    while pq:
        cost, transfers, _, curr_stop, curr_corr, path_edges = heapq.heappop(pq)

        if cost > best_cost.get((curr_stop, curr_corr, transfers), float("inf")):
            continue

        if curr_stop == dest_id:
            best_solution = path_edges
            break

        for nxt_stop, nxt_corr, edge_d in outgoing_edges[curr_stop]:
            is_transfer = (nxt_corr != curr_corr)
            new_transfers = transfers + (1 if is_transfer else 0)
            if new_transfers > MAX_TRANSFERS:
                continue

            new_cost = cost + edge_d + (TRANSFER_PENALTY_M if is_transfer else 0.0)
            state = (nxt_stop, nxt_corr, new_transfers)

            if new_cost < best_cost.get(state, float("inf")):
                best_cost[state] = new_cost
                tie_counter += 1
                heapq.heappush(
                    pq,
                    (
                        new_cost,
                        new_transfers,
                        tie_counter,
                        nxt_stop,
                        nxt_corr,
                        path_edges + [(curr_stop, nxt_stop, nxt_corr)],
                    ),
                )

    if best_solution is None:
        return {
            "status": "NO_ROUTE",
            "origin": {**halte_map[origin_id], "halte_id": origin_id},
            "destination": {**halte_map[dest_id], "halte_id": dest_id},
            "message": (
                f"Tidak ditemukan rute berarah yang menghubungkan {halte_map[origin_id]['nama_halte']} "
                f"menuju {halte_map[dest_id]['nama_halte']} dalam batas maksimal 2 kali transit."
            ),
        }

    # Kelompokkan edge berurutan dengan koridor yang sama menjadi segmen perjalanan
    segments: List[Dict[str, Any]] = []
    transit_stops: List[Dict[str, Any]] = []

    current_corr = best_solution[0][2]
    current_stop_ids = [best_solution[0][0], best_solution[0][1]]

    for idx in range(1, len(best_solution)):
        u, v, corr = best_solution[idx]
        if corr == current_corr:
            current_stop_ids.append(v)
        else:
            segments.append(_build_route_segment(current_corr, current_stop_ids, halte_map))
            transit_stops.append(
                {**halte_map[u], "halte_id": u, "from_corridor": current_corr, "to_corridor": corr}
            )
            current_corr = corr
            current_stop_ids = [u, v]

    segments.append(_build_route_segment(current_corr, current_stop_ids, halte_map))
    total_distance = round(sum(seg["distance_m"] for seg in segments), 1)
    status_label = "DIRECT" if not transit_stops else "TRANSIT"

    return {
        "status": status_label,
        "origin": {**halte_map[origin_id], "halte_id": origin_id},
        "destination": {**halte_map[dest_id], "halte_id": dest_id},
        "segments": segments,
        "transit_stops": transit_stops,
        "total_stops": len(best_solution) + 1,
        "total_distance_m": total_distance,
        "total_distance_fmt": format_distance(total_distance),
    }