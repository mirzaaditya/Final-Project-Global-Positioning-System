import heapq
import json
import math
import os
import re
from datetime import datetime
import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st
from pyproj import Transformer
from shapely.geometry import LineString, MultiLineString, Point
from streamlit_folium import st_folium

try:
    from streamlit_js_eval import get_geolocation
    HAS_JS_EVAL = True
except ImportError:
    HAS_JS_EVAL = False

# ==============================================================================
# 1. KONFIGURASI HALAMAN & CUSTOM DARK THEME CSS
# ==============================================================================
st.set_page_config(
    page_title="TransJogja Accessibility Intelligence",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }
        header[data-testid="stHeader"] {
            background: transparent !important;
        }
        .stApp {
            background-color: #0B1120;
            color: #F8FAFC;
        }
        .block-container {
            padding-top: 1.1rem !important;
            padding-bottom: 2rem !important;
            max-width: 1480px;
        }

        /* Top Banner Header */
        .tj-header {
            background: linear-gradient(90deg, #0F172A 0%, #131C31 65%, #172554 100%);
            border: 1px solid #1E293B;
            border-radius: 14px;
            padding: 1.05rem 1.4rem;
            margin-bottom: 0.9rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.8rem;
        }
        .tj-title {
            font-size: 1.38rem;
            font-weight: 800;
            color: #F8FAFC;
            margin: 0;
            letter-spacing: -0.01em;
        }
        .tj-title span {
            color: #F59E0B;
        }
        .tj-subtitle {
            font-size: 0.82rem;
            color: #94A3B8;
            margin: 0.2rem 0 0 0;
        }
        .status-group {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            flex-wrap: wrap;
        }
        .badge-online {
            background: rgba(16, 185, 129, 0.14);
            border: 1px solid rgba(16, 185, 129, 0.45);
            color: #34D399;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.28rem 0.65rem;
            border-radius: 6px;
            letter-spacing: 0.04em;
        }
        .badge-mode {
            background: rgba(245, 158, 11, 0.14);
            border: 1px solid rgba(245, 158, 11, 0.45);
            color: #FBBF24;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.28rem 0.65rem;
            border-radius: 6px;
            letter-spacing: 0.04em;
        }
        .badge-coord {
            background: #0F172A;
            border: 1px solid #334155;
            color: #CBD5E1;
            font-size: 0.74rem;
            font-family: monospace;
            padding: 0.28rem 0.7rem;
            border-radius: 6px;
        }

        /* Tombol GPS Hijau Utama */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            height: 2.65rem !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25) !important;
        }
        div.stButton > button[kind="secondary"] {
            background-color: #131C31 !important;
            color: #FBBF24 !important;
            border: 1px solid #F59E0B !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
        }

        label, .stSelectbox label, .stSlider label, .stToggle label, .stTextInput label, .stTextArea label {
            color: #CBD5E1 !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
        }
        div[data-baseweb="select"] > div {
            background-color: #131C31 !important;
            border-color: #26334D !important;
            color: #F8FAFC !important;
            border-radius: 10px !important;
        }

        /* 4 KPI Cards */
        .kpi-box {
            background-color: #131C31;
            border: 1px solid #1E293B;
            border-radius: 12px;
            padding: 0.95rem 1.15rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }
        .kpi-title {
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #94A3B8;
            margin-bottom: 0.2rem;
        }
        .kpi-num {
            font-size: 1.55rem;
            font-weight: 800;
            color: #F8FAFC;
            line-height: 1.15;
        }
        .kpi-desc {
            font-size: 0.74rem;
            color: #64748B;
            margin-top: 0.2rem;
        }
        .kpi-icon {
            width: 38px;
            height: 38px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.15rem;
        }

        /* Navigation Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1.4rem;
            border-bottom: 1px solid #1E293B;
            padding-bottom: 0.1rem;
            margin-bottom: 0.85rem;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent !important;
            color: #94A3B8 !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            padding: 0.45rem 0.2rem !important;
        }
        .stTabs [aria-selected="true"] {
            color: #F59E0B !important;
            border-bottom: 2px solid #F59E0B !important;
        }

        /* Halte Cards */
        .halte-card {
            background-color: #131C31;
            border: 1px solid #1E293B;
            border-radius: 11px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.55rem;
            transition: border-color 0.2s ease;
        }
        .halte-card:hover {
            border-color: #334155;
        }
        .halte-card-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 0.5rem;
            margin-bottom: 0.45rem;
        }
        .halte-name {
            font-size: 0.9rem;
            font-weight: 700;
            color: #F8FAFC;
        }
        .halte-corridors {
            font-size: 0.74rem;
            font-weight: 700;
            color: #F59E0B;
            white-space: nowrap;
        }
        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            align-items: center;
        }
        .pill-dist {
            background: rgba(16, 185, 129, 0.14);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #34D399;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.15rem 0.5rem;
            border-radius: 6px;
        }
        .pill-dist-far {
            background: rgba(148, 163, 184, 0.12);
            border: 1px solid rgba(148, 163, 184, 0.28);
            color: #CBD5E1;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.15rem 0.5rem;
            border-radius: 6px;
        }
        .pill-ramp-ok {
            background: rgba(59, 130, 246, 0.14);
            border: 1px solid rgba(59, 130, 246, 0.35);
            color: #60A5FA;
            font-size: 0.71rem;
            font-weight: 600;
            padding: 0.15rem 0.48rem;
            border-radius: 6px;
        }
        .pill-ramp-no {
            background: rgba(239, 68, 68, 0.14);
            border: 1px solid rgba(239, 68, 68, 0.35);
            color: #F87171;
            font-size: 0.71rem;
            font-weight: 600;
            padding: 0.15rem 0.48rem;
            border-radius: 6px;
        }
        .pill-guiding {
            background: rgba(245, 158, 11, 0.14);
            border: 1px solid rgba(245, 158, 11, 0.35);
            color: #FBBF24;
            font-size: 0.71rem;
            font-weight: 600;
            padding: 0.15rem 0.48rem;
            border-radius: 6px;
        }
        .pill-staff {
            background: rgba(148, 163, 184, 0.12);
            border: 1px solid rgba(148, 163, 184, 0.25);
            color: #94A3B8;
            font-size: 0.71rem;
            font-weight: 600;
            padding: 0.15rem 0.48rem;
            border-radius: 6px;
        }

        /* Floating Map Legend Overlay */
        .floating-legend {
            background: rgba(15, 23, 42, 0.94);
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 0.55rem 0.8rem;
            color: #E2E8F0;
            font-size: 0.72rem;
            margin-top: 0.45rem;
            width: fit-content;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45);
        }
        .legend-title {
            font-size: 0.65rem;
            font-weight: 800;
            color: #F59E0B;
            letter-spacing: 0.06em;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
        }
        .legend-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 0.3rem 1.1rem;
        }
        .dot {
            height: 9px;
            width: 9px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
        }

        /* Route & Summary Cards */
        .dark-panel {
            background-color: #131C31;
            border: 1px solid #1E293B;
            border-radius: 12px;
            padding: 1rem 1.15rem;
            margin-bottom: 0.75rem;
        }
        .trip-summary-bar {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.5rem;
            background: #0B1120;
            border: 1px solid #26334D;
            border-radius: 10px;
            padding: 0.65rem 0.75rem;
            margin: 0.55rem 0 0.75rem 0;
            text-align: center;
        }
        .trip-sum-label {
            font-size: 0.65rem;
            text-transform: uppercase;
            color: #94A3B8;
            font-weight: 700;
            letter-spacing: 0.04em;
        }
        .trip-sum-val {
            font-size: 0.96rem;
            font-weight: 800;
            color: #F8FAFC;
            margin-top: 0.1rem;
        }
        .route-step-dark {
            border-left: 3px solid #10B981;
            padding-left: 0.85rem;
            margin: 0.6rem 0;
        }
        .route-step-transit {
            border-left: 3px solid #F59E0B;
            padding-left: 0.85rem;
            margin: 0.6rem 0;
        }
        .route-step-end {
            border-left: 3px solid #EF4444;
            padding-left: 0.85rem;
            margin: 0.6rem 0;
        }
        .leg-meta {
            font-size: 0.75rem;
            color: #94A3B8;
            margin-top: 0.15rem;
        }
        .corridor-chip {
            display: inline-block;
            padding: 0.18rem 0.55rem;
            border-radius: 6px;
            color: #FFFFFF;
            font-weight: 700;
            font-size: 0.76rem;
            margin-right: 0.3rem;
            margin-top: 0.22rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

LAPORAN_FILE = "laporan_kondisi.json"
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32749", always_xy=True)
TO_4326 = Transformer.from_crs("EPSG:32749", "EPSG:4326", always_xy=True)


# ==============================================================================
# 2. DATA TITIK LOKASI PRESET & POI BLIND SPOT YOGYAKARTA
# ==============================================================================
PRESET_LOCATIONS = {
    "UPN Veteran Yogyakarta": (-7.7621, 110.4092),
    "Kawasan Malioboro (Kepatihan)": (-7.7952, 110.3656),
    "Tugu Pal Putih Yogyakarta": (-7.7829, 110.3671),
    "Kampus UGM (Bundaran)": (-7.7713, 110.3775),
    "Stasiun Tugu Yogyakarta": (-7.7892, 110.3635),
    "Stasiun Lempuyangan": (-7.7904, 110.3755),
    "Terminal Giwangan": (-7.8342, 110.3918),
    "Plaza Ambarrukmo": (-7.7828, 110.4012),
    "Area Blind Spot (Seturan / Babarsari Dalam)": (-7.7725, 110.4115),
}

YOGYA_POIS = [
    ("UPN Veteran Yogyakarta", -7.7621, 110.4092),
    ("Malioboro Mall / Kepatihan", -7.7952, 110.3656),
    ("Tugu Pal Putih", -7.7829, 110.3671),
    ("Stasiun Tugu Yogyakarta", -7.7892, 110.3635),
    ("Stasiun Lempuyangan", -7.7904, 110.3755),
    ("RSUP Dr. Sardjito", -7.7686, 110.3735),
    ("Plaza Ambarrukmo", -7.7828, 110.4012),
    ("Pakuwon Mall Jogja", -7.7589, 110.3991),
    ("Jogja Expo Center (JEC)", -7.7997, 110.4038),
    ("Gembira Loka Zoo", -7.8038, 110.3968),
    ("XT Square Yogyakarta", -7.8162, 110.3860),
    ("Terminal Giwangan", -7.8342, 110.3918),
    ("Terminal Jombor", -7.7474, 110.3612),
    ("Bandara Adisutjipto", -7.7845, 110.4357),
    ("Universitas Muhammadiyah Yogyakarta (UMY)", -7.8105, 110.3218),
]


# ==============================================================================
# 3. PENYIMPANAN LAPORAN KONDISI HALTE
# ==============================================================================
def load_laporan():
    if os.path.exists(LAPORAN_FILE):
        try:
            with open(LAPORAN_FILE, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
            normalized = []
            for it in raw_items:
                kat = it.get("kategori") or it.get("status") or "🟢 Kondisi Normal & Lancar"
                normalized.append(
                    {
                        "halte": it.get("halte", "Halte TransJogja"),
                        "kategori": kat,
                        "catatan": it.get("catatan", "Laporan kondisi lapangan."),
                        "waktu": it.get("waktu", "-"),
                    }
                )
            return normalized
        except Exception:
            pass

    default_data = [
        {
            "halte": "Halte UPN Veteran",
            "kategori": "🟢 Kondisi Normal & Lancar",
            "catatan": "Bus Kor. 3A baru tiba, akses masuk halte bersih dan petugas siaga.",
            "waktu": "13:05 WIB",
        },
        {
            "halte": "Halte Malioboro 1 (Inna Garuda)",
            "kategori": "🟡 Ramai Penumpang",
            "catatan": "Antrean penumpang cukup padat, ramp kursi roda berfungsi baik.",
            "waktu": "12:40 WIB",
        },
        {
            "halte": "Halte Janti Bawah Flyover",
            "kategori": "🔴 Kendala Fasilitas / Akses",
            "catatan": "Area trotoar menuju ramp agak terhalang parkir liar motor.",
            "waktu": "11:55 WIB",
        },
    ]
    save_laporan(default_data)
    return default_data


def save_laporan(items):
    with open(LAPORAN_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


# ==============================================================================
# 4. PARSER GEOJSON RUTE & 63 HALTE TRANSJOGJA (DENGAN KOORDINAT UTM PRE-CACHED)
# ==============================================================================
@st.cache_data
def load_rute_geojson(filepath="rute_transjogja.geojson"):
    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    features_2d = []
    records = []
    color_map = {}

    for feat in raw.get("features", []):
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})

        koridor = (props.get("name") or props.get("trips_rout") or "Tanpa Nama").strip()
        kode = re.sub(r"^Kor\.?\s*", "", koridor, flags=re.IGNORECASE).strip()
        tujuan = (props.get("trips_trip") or "-").strip()
        warna = (props.get("stroke") or "#3B82F6").strip()

        color_map[kode] = warna
        color_map[koridor] = warna

        lines = []
        if geom.get("type") == "GeometryCollection":
            for g in geom.get("geometries", []):
                if g.get("type") == "LineString":
                    pts = [(c[0], c[1]) for c in g.get("coordinates", []) if len(c) >= 2]
                    if len(pts) >= 2:
                        lines.append(pts)
        elif geom.get("type") == "LineString":
            pts = [(c[0], c[1]) for c in geom.get("coordinates", []) if len(c) >= 2]
            if len(pts) >= 2:
                lines.append(pts)

        if not lines:
            continue

        records.append(
            {
                "kode": kode,
                "koridor": koridor,
                "tujuan": tujuan,
                "warna": warna,
                "geometry": MultiLineString([LineString(l) for l in lines]),
            }
        )
        features_2d.append(
            {
                "type": "Feature",
                "properties": {"kode": kode, "koridor": koridor, "tujuan": tujuan, "warna": warna},
                "geometry": {"type": "MultiLineString", "coordinates": lines},
            }
        )

    return gpd.GeoDataFrame(records, crs="EPSG:4326"), features_2d, color_map


@st.cache_data
def load_halte_geojson(filepath="halte_transjogja.geojson"):
    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    non_ramp_keywords = [
        "upn veteran",
        "janti bawah",
        "gejayan",
        "de brito",
        "gedung wanita",
        "urip sumoharjo",
        "sudirman (santika)",
        "tentara pelajar",
        "sma n 1",
        "sma n 7",
        "nitikan",
        "tegal gendu",
    ]

    records = []
    for feat in raw.get("features", []):
        props = feat.get("properties", {})
        coords = feat.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue

        lon, lat = float(coords[0]), float(coords[1])
        x_utm, y_utm = TO_UTM.transform(lon, lat)
        nama = (props.get("nama") or props.get("namobj") or "Halte TransJogja").strip()
        ket = (props.get("keterangan") or "").strip()
        kode_list = list(dict.fromkeys(re.findall(r"\(([0-9]+[A-Z]?)\)", ket)))

        nama_lower = nama.lower()
        has_ramp = not any(kw in nama_lower for kw in non_ramp_keywords)

        koridor_label = (
            "Kor. " + ", ".join(kode_list[:3]) + ("..." if len(kode_list) > 3 else "")
            if kode_list
            else "Kor. Utama"
        )

        records.append(
            {
                "objectid": props.get("objectid"),
                "nama": nama,
                "lat": lat,
                "lon": lon,
                "x_utm": float(x_utm),
                "y_utm": float(y_utm),
                "kode_koridor": kode_list,
                "koridor_short": koridor_label,
                "koridor_full": ", ".join([f"Kor. {k}" for k in kode_list]),
                "jumlah_koridor": len(kode_list),
                "has_ramp": has_ramp,
                "has_guiding": True,
                "has_petugas": True,
                "keterangan": ket,
                "geometry": Point(lon, lat),
            }
        )

    return gpd.GeoDataFrame(records, crs="EPSG:4326")


# ==============================================================================
# 5. GRAF JARINGAN JALAN KORIDOR + JARINGAN JALAN TERPADU (SUPER CEPAT)
# ==============================================================================
def format_jarak(meter: float) -> str:
    if meter < 1000:
        return f"{int(round(meter))} m"
    return f"{meter / 1000.0:.2f} km"


def jarak_antar_titik_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    x1, y1 = TO_UTM.transform(lon1, lat1)
    x2, y2 = TO_UTM.transform(lon2, lat2)
    return float(math.hypot(x2 - x1, y2 - y1))


def estimasi_menit_bus_jalan(road_dist_m: float) -> int:
    return max(2, int(np.ceil(road_dist_m / 367.0)))


def estimasi_menit_jalan(jarak_m: float) -> int:
    return max(1, int(np.ceil(jarak_m / 80.0)))


def _dijkstra_path(coords_arr: np.ndarray, adj: list, p1_xy: np.ndarray, p2_xy: np.ndarray, snap_margin: float = 30.0):
    n_nodes = len(coords_arr)
    if n_nodes < 2:
        return None, float("inf")

    d_start = np.hypot(coords_arr[:, 0] - p1_xy[0], coords_arr[:, 1] - p1_xy[1])
    d_end = np.hypot(coords_arr[:, 0] - p2_xy[0], coords_arr[:, 1] - p2_xy[1])

    min_s = float(np.min(d_start))
    min_e = float(np.min(d_end))

    start_nodes = np.where(d_start <= min_s + snap_margin)[0]
    end_set = set(np.where(d_end <= min_e + snap_margin)[0].tolist())

    dist = [float("inf")] * n_nodes
    parent = [-1] * n_nodes
    pq = []

    for s_idx in start_nodes:
        s_i = int(s_idx)
        init_cost = float(d_start[s_i])
        dist[s_i] = init_cost
        heapq.heappush(pq, (init_cost, s_i))

    best_end = -1
    best_total = float("inf")

    while pq:
        d_curr, u = heapq.heappop(pq)
        if d_curr > dist[u]:
            continue
        if u in end_set:
            total_with_snap = d_curr + float(d_end[u])
            if total_with_snap < best_total:
                best_total = total_with_snap
                best_end = u
            continue
        for v, w in adj[u]:
            nd = d_curr + w
            if nd < dist[v]:
                dist[v] = nd
                parent[v] = u
                heapq.heappush(pq, (nd, v))

    if best_end == -1:
        return None, float("inf")

    path_indices = []
    curr = best_end
    while curr != -1:
        path_indices.append(curr)
        curr = parent[curr]
    path_indices.reverse()

    return coords_arr[path_indices], float(best_total)


@st.cache_data
def build_road_networks(_gdf_rute: gpd.GeoDataFrame):
    gdf_utm = _gdf_rute.to_crs("EPSG:32749")
    corridor_graphs = {}

    u_nodes = []
    u_index = {}
    u_adj = []

    def get_u_node(x: float, y: float) -> int:
        key = (round(x, 1), round(y, 1))
        if key in u_index:
            return u_index[key]
        idx = len(u_nodes)
        u_nodes.append((x, y))
        u_index[key] = idx
        u_adj.append([])
        return idx

    for _, row in gdf_utm.iterrows():
        kode = row["kode"]
        geom = row.geometry
        lines = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]

        nodes = []
        node_index = {}
        adj = []
        comp_ids = []
        endpoint_flags = []

        def get_c_node(x: float, y: float, comp_id: int, is_end: bool) -> int:
            key = (round(x, 1), round(y, 1))
            if key in node_index:
                idx = node_index[key]
                if is_end:
                    endpoint_flags[idx] = True
                return idx
            idx = len(nodes)
            nodes.append((x, y))
            node_index[key] = idx
            adj.append([])
            comp_ids.append(comp_id)
            endpoint_flags.append(is_end)
            return idx

        for c_idx, ln in enumerate(lines):
            coords = list(ln.coords)
            if len(coords) < 2:
                continue
            prev_c = None
            prev_u = None
            total_segs = len(coords) - 1
            for i in range(total_segs):
                x1, y1 = coords[i][0], coords[i][1]
                x2, y2 = coords[i + 1][0], coords[i + 1][1]
                seg_len = math.hypot(x2 - x1, y2 - y1)
                steps = max(1, int(math.ceil(seg_len / 55.0)))
                for s in range(steps + 1):
                    t = s / steps
                    px = x1 + (x2 - x1) * t
                    py = y1 + (y2 - y1) * t
                    is_end = (i == 0 and s == 0) or (i == total_segs - 1 and s == steps)

                    curr_c = get_c_node(px, py, c_idx, is_end)
                    if prev_c is not None and prev_c != curr_c:
                        d = math.hypot(nodes[curr_c][0] - nodes[prev_c][0], nodes[curr_c][1] - nodes[prev_c][1])
                        adj[prev_c].append((curr_c, d))
                        adj[curr_c].append((prev_c, d * 8.0))
                    prev_c = curr_c

                    curr_u = get_u_node(px, py)
                    if prev_u is not None and prev_u != curr_u:
                        du = math.hypot(u_nodes[curr_u][0] - u_nodes[prev_u][0], u_nodes[curr_u][1] - u_nodes[prev_u][1])
                        u_adj[prev_u].append((curr_u, du))
                        u_adj[curr_u].append((prev_u, du))
                    prev_u = curr_u

        n_nodes = len(nodes)
        if n_nodes >= 2:
            coords_arr = np.array(nodes)
            comp_arr = np.array(comp_ids)
            end_arr = np.array(endpoint_flags)
            unique_comps = sorted(set(comp_ids))

            if len(unique_comps) > 1:
                for i in range(len(unique_comps)):
                    for j in range(i + 1, len(unique_comps)):
                        idx_a = np.where(comp_arr == unique_comps[i])[0]
                        idx_b = np.where(comp_arr == unique_comps[j])[0]
                        if len(idx_a) == 0 or len(idx_b) == 0:
                            continue

                        pts_a = coords_arr[idx_a]
                        pts_b = coords_arr[idx_b]
                        diff = pts_a[:, None, :] - pts_b[None, :, :]
                        dists = np.hypot(diff[:, :, 0], diff[:, :, 1])

                        touch_r, touch_c = np.where(dists <= 25.0)
                        for r_i, c_i in zip(touch_r, touch_c):
                            u = int(idx_a[r_i])
                            v = int(idx_b[c_i])
                            w = float(dists[r_i, c_i])
                            adj[u].append((v, w))
                            adj[v].append((u, w))

                        if len(touch_r) == 0:
                            end_a_mask = end_arr[idx_a]
                            end_b_mask = end_arr[idx_b]
                            cand_edges = []
                            if np.any(end_a_mask):
                                sub_d = dists[end_a_mask, :]
                                pos = np.unravel_index(np.argmin(sub_d), sub_d.shape)
                                cand_edges.append((float(sub_d[pos]), int(idx_a[end_a_mask][pos[0]]), int(idx_b[pos[1]])))
                            if np.any(end_b_mask):
                                sub_d = dists[:, end_b_mask]
                                pos = np.unravel_index(np.argmin(sub_d), sub_d.shape)
                                cand_edges.append((float(sub_d[pos]), int(idx_a[pos[0]]), int(idx_b[end_b_mask][pos[1]])))

                            for min_d, u, v in cand_edges:
                                if min_d <= 110.0:
                                    adj[u].append((v, min_d * 1.4))
                                    adj[v].append((u, min_d * 1.4))

            corridor_graphs[kode] = (coords_arr, adj)

    u_coords_arr = np.array(u_nodes) if u_nodes else np.zeros((0, 2))
    if len(u_coords_arr) >= 2:
        grid = {}
        cell_size = 25.0
        for idx, (ux, uy) in enumerate(u_nodes):
            gx, gy = int(ux // cell_size), int(uy // cell_size)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for other_idx in grid.get((gx + dx, gy + dy), []):
                        ox, oy = u_nodes[other_idx]
                        dd = math.hypot(ux - ox, uy - oy)
                        if 0.5 < dd <= 22.0:
                            u_adj[idx].append((other_idx, dd))
                            u_adj[other_idx].append((idx, dd))
            grid.setdefault((gx, gy), []).append(idx)

    return corridor_graphs, (u_coords_arr, u_adj)


@st.cache_data
def precompute_valid_corridors(_gdf_halte: gpd.GeoDataFrame, _gdf_rute: gpd.GeoDataFrame):
    """Pre-compute koridor yang melintas <= 220m dari setiap halte dalam hitungan milidetik."""
    corridor_graphs, _ = build_road_networks(_gdf_rute)
    valid_map = {}
    for _, row in _gdf_halte.iterrows():
        nama = row["nama"]
        hx, hy = row["x_utm"], row["y_utm"]
        valid_k = []
        for k in row["kode_koridor"]:
            if k in corridor_graphs:
                c_arr, _ = corridor_graphs[k]
                if float(np.min(np.hypot(c_arr[:, 0] - hx, c_arr[:, 1] - hy))) <= 220.0:
                    valid_k.append(k)
        valid_map[nama] = valid_k if valid_k else list(row["kode_koridor"])
    return valid_map


def _xy_list_to_latlon(xy_pts, lat1: float, lon1: float, lat2: float, lon2: float):
    arr = np.array(xy_pts)
    lons, lats = TO_4326.transform(arr[:, 0], arr[:, 1])
    coords = [[float(lat1), float(lon1)]]
    coords.extend([[float(lt), float(ln)] for lt, ln in zip(lats, lons)])
    coords.append([float(lat2), float(lon2)])
    return coords


def extract_road_segment(
    kode_koridor: str,
    lat1: float,
    lon1: float,
    x1: float,
    y1: float,
    lat2: float,
    lon2: float,
    x2: float,
    y2: float,
    corridor_graphs: dict,
    unified_graph: tuple,
):
    fallback_coords = [[lat1, lon1], [lat2, lon2]]
    fallback_dist = math.hypot(x2 - x1, y2 - y1) * 1.35

    if kode_koridor not in corridor_graphs:
        return fallback_coords, fallback_dist

    c_coords, c_adj = corridor_graphs[kode_koridor]
    u_coords_arr, u_adj = unified_graph
    p1_xy = np.array([x1, y1])
    p2_xy = np.array([x2, y2])

    d_c1 = np.hypot(c_coords[:, 0] - x1, c_coords[:, 1] - y1)
    d_c2 = np.hypot(c_coords[:, 0] - x2, c_coords[:, 1] - y2)

    min_d1 = float(np.min(d_c1))
    min_d2 = float(np.min(d_c2))
    snap1_xy = c_coords[int(np.argmin(d_c1))]
    snap2_xy = c_coords[int(np.argmin(d_c2))]

    main_xy, main_cost = _dijkstra_path(c_coords, c_adj, snap1_xy, snap2_xy, snap_margin=30.0)
    if main_xy is None or len(main_xy) < 2:
        if len(u_coords_arr) >= 2:
            u_xy, u_cost = _dijkstra_path(u_coords_arr, u_adj, p1_xy, p2_xy, snap_margin=35.0)
            if u_xy is not None and len(u_xy) >= 2:
                return _xy_list_to_latlon(u_xy, lat1, lon1, lat2, lon2), float(u_cost)
        return fallback_coords, fallback_dist

    full_xy_list = []
    extra_cost = 0.0

    if min_d1 > 110.0 and len(u_coords_arr) >= 2:
        conn1_xy, conn1_cost = _dijkstra_path(u_coords_arr, u_adj, p1_xy, snap1_xy, snap_margin=35.0)
        if conn1_xy is not None and len(conn1_xy) >= 2:
            full_xy_list.extend(conn1_xy.tolist())
            extra_cost += conn1_cost
        else:
            extra_cost += min_d1
    else:
        extra_cost += min_d1

    full_xy_list.extend(main_xy.tolist())

    if min_d2 > 110.0 and len(u_coords_arr) >= 2:
        conn2_xy, conn2_cost = _dijkstra_path(u_coords_arr, u_adj, snap2_xy, p2_xy, snap_margin=35.0)
        if conn2_xy is not None and len(conn2_xy) >= 2:
            full_xy_list.extend(conn2_xy.tolist())
            extra_cost += conn2_cost
        else:
            extra_cost += min_d2
    else:
        extra_cost += min_d2

    cleaned_pts = []
    for xy in full_xy_list:
        if not cleaned_pts or math.hypot(xy[0] - cleaned_pts[-1][0], xy[1] - cleaned_pts[-1][1]) > 1.0:
            cleaned_pts.append(xy)

    if len(cleaned_pts) < 2:
        return fallback_coords, fallback_dist

    return _xy_list_to_latlon(cleaned_pts, lat1, lon1, lat2, lon2), float(main_cost + extra_cost)


def create_pin_icon(label: str, sub_icon: str, bg_color: str, text_color: str = "#FFFFFF"):
    html = f"""
    <div style="
        width:116px;
        height:42px;
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:flex-end;
        pointer-events:auto;">
        <div style="
            background:{bg_color};
            color:{text_color};
            font-family:sans-serif;
            font-weight:800;
            font-size:10.5px;
            letter-spacing:0.04em;
            padding:4px 9px;
            border-radius:8px;
            border:2px solid #FFFFFF;
            box-shadow:0 3px 10px rgba(0,0,0,0.45);
            display:flex;
            align-items:center;
            gap:4px;
            white-space:nowrap;">
            <span>{sub_icon}</span><span>{label}</span>
        </div>
        <div style="
            width:0;
            height:0;
            border-left:7px solid transparent;
            border-right:7px solid transparent;
            border-top:9px solid {bg_color};
            margin-top:-1px;
            filter:drop-shadow(0 2px 2px rgba(0,0,0,0.35));">
        </div>
    </div>
    """
    return folium.DivIcon(html=html, icon_size=(116, 42), icon_anchor=(58, 42))


def run_spatial_engine(user_lat, user_lon, radius_m, wheelchair_only, gdf_halte):
    df_h = gdf_halte.copy()
    if wheelchair_only:
        df_h = df_h[df_h["has_ramp"]].copy()

    if df_h.empty:
        df_h = gdf_halte.copy()

    ux, uy = TO_UTM.transform(user_lon, user_lat)
    df_h["jarak_m"] = np.hypot(df_h["x_utm"].values - ux, df_h["y_utm"].values - uy)
    df_h["menit_jalan"] = np.maximum(1, np.ceil(df_h["jarak_m"] / 80.0)).astype(int)
    df_h["walkable"] = df_h["jarak_m"] <= radius_m
    halte_sorted = df_h.sort_values("jarak_m").reset_index(drop=True)

    hx_arr = df_h["x_utm"].values
    hy_arr = df_h["y_utm"].values
    h_names = df_h["nama"].tolist()

    poi_records = []
    for poi_name, p_lat, p_lon in YOGYA_POIS:
        px, py = TO_UTM.transform(p_lon, p_lat)
        dists = np.hypot(hx_arr - px, hy_arr - py)
        min_idx = int(np.argmin(dists))
        min_d = float(dists[min_idx])
        poi_records.append(
            {
                "Lokasi Strategis (POI)": poi_name,
                "Halte Terdekat": h_names[min_idx],
                "Jarak (m)": int(round(min_d)),
                "Status": "Blind Spot (>Radius)" if min_d > radius_m else "Terlayani",
            }
        )
    df_poi = pd.DataFrame(poi_records)
    blind_spot_count = int((df_poi["Jarak (m)"] > radius_m).sum())

    nearest_dist = float(halte_sorted.iloc[0]["jarak_m"])
    walkable_count = int(halte_sorted["walkable"].sum())
    ramp_ratio = float(gdf_halte["has_ramp"].mean()) * 100.0
    poi_coverage_ratio = ((len(df_poi) - blind_spot_count) / len(df_poi)) * 100.0
    prox_score = float(np.clip((1200.0 - nearest_dist) / 1100.0 * 100.0, 0.0, 100.0))

    indeks_aksesibilitas = round(
        0.35 * prox_score
        + 0.30 * poi_coverage_ratio
        + 0.20 * ramp_ratio
        + 0.15 * min(walkable_count / 3.0 * 100.0, 100.0),
        1,
    )

    return {
        "halte_df": halte_sorted,
        "walkable_count": walkable_count,
        "blind_spot_count": blind_spot_count,
        "total_poi": len(df_poi),
        "df_poi": df_poi,
        "indeks_aksesibilitas": indeks_aksesibilitas,
    }


@st.cache_data
def compute_fastest_route_cached(asal_nama: str, tujuan_nama: str, _gdf_halte: gpd.GeoDataFrame, _gdf_rute: gpd.GeoDataFrame):
    """Menghitung dan meng-cache rute tercepat antar dua halte dalam milidetik."""
    if asal_nama == tujuan_nama:
        return {"status": "sama", "best": None}

    corridor_graphs, unified_graph = build_road_networks(_gdf_rute)
    valid_map = precompute_valid_corridors(_gdf_halte, _gdf_rute)

    asal_row = _gdf_halte[_gdf_halte["nama"] == asal_nama].iloc[0]
    tujuan_row = _gdf_halte[_gdf_halte["nama"] == tujuan_nama].iloc[0]

    set_a = set(valid_map.get(asal_nama, []))
    set_b = set(valid_map.get(tujuan_nama, []))
    kandidat_semua = []

    # 1. Rute langsung
    for k in sorted(list(set_a & set_b)):
        coords_road, dist_road = extract_road_segment(
            k,
            asal_row["lat"],
            asal_row["lon"],
            asal_row["x_utm"],
            asal_row["y_utm"],
            tujuan_row["lat"],
            tujuan_row["lon"],
            tujuan_row["x_utm"],
            tujuan_row["y_utm"],
            corridor_graphs,
            unified_graph,
        )
        bus_min = estimasi_menit_bus_jalan(dist_road)
        kandidat_semua.append(
            {
                "jenis": "langsung",
                "k1": k,
                "k2": None,
                "hub_nama": None,
                "hub_lat": None,
                "hub_lon": None,
                "coords1": coords_road,
                "coords2": None,
                "leg1_m": dist_road,
                "leg1_min": bus_min,
                "leg2_m": 0.0,
                "leg2_min": 0,
                "transfer_min": 0,
                "bus_m": dist_road,
                "bus_min": bus_min,
            }
        )

    # 2. Rute 1x transit pada hub yang dilintasi kedua koridor
    hub_candidates = []
    for _, mid in _gdf_halte.iterrows():
        mid_nama = mid["nama"]
        if mid_nama in (asal_nama, tujuan_nama):
            continue
        set_m = set(valid_map.get(mid_nama, []))
        leg1_list = sorted(list(set_a & set_m))
        leg2_list = sorted(list(set_m & set_b))
        if leg1_list and leg2_list:
            d_straight = math.hypot(mid["x_utm"] - asal_row["x_utm"], mid["y_utm"] - asal_row["y_utm"]) + math.hypot(
                tujuan_row["x_utm"] - mid["x_utm"], tujuan_row["y_utm"] - mid["y_utm"]
            )
            hub_candidates.append((d_straight, mid, leg1_list, leg2_list))

    hub_candidates.sort(key=lambda x: x[0])

    for _, hub, leg1_list, leg2_list in hub_candidates[:10]:
        best_leg1 = None
        for k1 in leg1_list:
            c1, d1 = extract_road_segment(
                k1,
                asal_row["lat"],
                asal_row["lon"],
                asal_row["x_utm"],
                asal_row["y_utm"],
                hub["lat"],
                hub["lon"],
                hub["x_utm"],
                hub["y_utm"],
                corridor_graphs,
                unified_graph,
            )
            if best_leg1 is None or d1 < best_leg1[2]:
                best_leg1 = (k1, c1, d1)

        best_leg2 = None
        for k2 in leg2_list:
            c2, d2 = extract_road_segment(
                k2,
                hub["lat"],
                hub["lon"],
                hub["x_utm"],
                hub["y_utm"],
                tujuan_row["lat"],
                tujuan_row["lon"],
                tujuan_row["x_utm"],
                tujuan_row["y_utm"],
                corridor_graphs,
                unified_graph,
            )
            if best_leg2 is None or d2 < best_leg2[2]:
                best_leg2 = (k2, c2, d2)

        if best_leg1 is None or best_leg2 is None:
            continue

        k1_win, coords1, dist1 = best_leg1
        k2_win, coords2, dist2 = best_leg2
        if k1_win == k2_win:
            continue

        min1 = estimasi_menit_bus_jalan(dist1)
        min2 = estimasi_menit_bus_jalan(dist2)
        transfer_min = 4
        total_bus_m = dist1 + dist2
        total_bus_min = min1 + transfer_min + min2

        kandidat_semua.append(
            {
                "jenis": "transit",
                "k1": k1_win,
                "k2": k2_win,
                "hub_nama": hub["nama"],
                "hub_lat": float(hub["lat"]),
                "hub_lon": float(hub["lon"]),
                "coords1": coords1,
                "coords2": coords2,
                "leg1_m": dist1,
                "leg1_min": min1,
                "leg2_m": dist2,
                "leg2_min": min2,
                "transfer_min": transfer_min,
                "bus_m": total_bus_m,
                "bus_min": total_bus_min,
            }
        )

    kandidat_semua.sort(key=lambda x: (x["bus_min"], x["bus_m"]))
    return {
        "status": "ok" if kandidat_semua else "none",
        "best": kandidat_semua[0] if kandidat_semua else None,
    }


def get_single_fastest_route(user_lat, user_lon, asal_row, tujuan_nama, gdf_halte, gdf_rute):
    tujuan_df = gdf_halte[gdf_halte["nama"] == tujuan_nama]
    if tujuan_df.empty:
        return None
    tujuan_row = tujuan_df.iloc[0]

    walk_m = jarak_antar_titik_m(user_lat, user_lon, asal_row["lat"], asal_row["lon"])
    walk_min = estimasi_menit_jalan(walk_m)

    cached_res = compute_fastest_route_cached(asal_row["nama"], tujuan_nama, gdf_halte, gdf_rute)
    return {
        "status": cached_res["status"],
        "asal": asal_row,
        "tujuan": tujuan_row,
        "walk_m": walk_m,
        "walk_min": walk_min,
        "best": cached_res["best"],
    }


# ==============================================================================
# 6. INISIALISASI STATE, CALLBACK LOKASI & MUAT DATASET
# ==============================================================================
if "user_lat" not in st.session_state:
    st.session_state.user_lat, st.session_state.user_lon = PRESET_LOCATIONS["UPN Veteran Yogyakarta"]
if "loc_label" not in st.session_state:
    st.session_state.loc_label = "UPN Veteran Yogyakarta"
if "gps_mode" not in st.session_state:
    st.session_state.gps_mode = False


def set_preset_location(preset_name: str):
    st.session_state.gps_mode = False
    st.session_state.loc_label = preset_name
    st.session_state.user_lat, st.session_state.user_lon = PRESET_LOCATIONS[preset_name]


def on_preset_selectbox_change():
    picked = st.session_state.preset_selectbox_key
    if picked in PRESET_LOCATIONS:
        set_preset_location(picked)


try:
    gdf_rute, rute_features, color_map = load_rute_geojson("rute_transjogja.geojson")
    gdf_halte = load_halte_geojson("halte_transjogja.geojson")
except FileNotFoundError as e:
    st.error(f"File `{e.filename}` tidak ditemukan di folder proyek.")
    st.stop()

laporan_items = load_laporan()
reported_halves = {
    item["halte"]: item
    for item in laporan_items
    if "Kendala" in item.get("kategori", "") or "🔴" in item.get("kategori", "")
}


# ==============================================================================
# 7. TOP HEADER BANNER
# ==============================================================================
mode_badge_text = "MODE GPS LIVE" if st.session_state.gps_mode else "MODE PRESET"

st.markdown(
    f"""
    <div class="tj-header">
        <div>
            <p class="tj-title">🚌 TransJogja <span>Accessibility Intelligence</span></p>
            <p class="tj-subtitle">Lacak halte terdekat, audit aksesibilitas kursi roda &amp; rencanakan rute perjalanan Yogyakarta</p>
        </div>
        <div class="status-group">
            <span class="badge-online">● SYSTEM ONLINE</span>
            <span class="badge-mode">{mode_badge_text}</span>
            <span class="badge-coord">{st.session_state.loc_label} &bull; {st.session_state.user_lat:.4f}, {st.session_state.user_lon:.4f}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# 8. BARIS KONTROL 4 KOLOM (GPS, PRESET, RADIUS SLIDER, TOGGLE KURSI RODA)
# ==============================================================================
c_gps, c_preset, c_rad, c_wc = st.columns([1.05, 1.45, 1.35, 1.15], gap="medium")

with c_gps:
    st.markdown("<div style='height:1.42rem;'></div>", unsafe_allow_html=True)
    if st.button("📍 Deteksi GPS Saya", type="primary", use_container_width=True):
        st.session_state.gps_mode = True
        st.session_state.loc_label = "GPS Live Browser"
        st.rerun()

with c_preset:
    preset_keys = list(PRESET_LOCATIONS.keys())
    if st.session_state.loc_label in preset_keys:
        dropdown_options = preset_keys
        current_idx = preset_keys.index(st.session_state.loc_label)
    else:
        dropdown_options = [st.session_state.loc_label] + preset_keys
        current_idx = 0

    st.selectbox(
        "📍 Titik Lokasi (Preset Yogyakarta)",
        options=dropdown_options,
        index=current_idx,
        key="preset_selectbox_key",
        on_change=on_preset_selectbox_change,
    )

with c_rad:
    radius_m = st.slider(
        "⭕ Radius Jalan Kaki (meter)",
        min_value=200,
        max_value=1000,
        value=500,
        step=50,
    )

with c_wc:
    st.markdown("<div style='height:1.55rem;'></div>", unsafe_allow_html=True)
    wheelchair_only = st.toggle("♿ Hanya Ramah Kursi Roda", value=False)

if st.session_state.gps_mode:
    if HAS_JS_EVAL:
        @st.fragment(run_every=5)
        def gps_live_listener():
            loc = get_geolocation()
            if loc and "coords" in loc:
                lat_g = float(loc["coords"]["latitude"])
                lon_g = float(loc["coords"]["longitude"])
                if abs(lat_g - st.session_state.user_lat) > 0.00002 or abs(lon_g - st.session_state.user_lon) > 0.00002:
                    st.session_state.user_lat = lat_g
                    st.session_state.user_lon = lon_g
                    st.session_state.loc_label = "GPS Live Browser"
                    st.rerun()
        gps_live_listener()
    else:
        st.warning("Library `streamlit-js-eval` belum terpasang.")
        st.session_state.gps_mode = False

jarak_dari_diy_m = jarak_antar_titik_m(st.session_state.user_lat, st.session_state.user_lon, -7.7829, 110.3671)
if jarak_dari_diy_m > 25000:
    b_warn, b_reset = st.columns([3.2, 1.3], gap="small")
    with b_warn:
        st.warning(
            f"📍 Lokasi GPS Anda terdeteksi **{format_jarak(jarak_dari_diy_m)}** di luar area layanan TransJogja (Yogyakarta)."
        )
    with b_reset:
        st.markdown("<div style='height:0.25rem;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Pindah ke UPN Veteran Yogyakarta", use_container_width=True):
            set_preset_location("UPN Veteran Yogyakarta")
            st.rerun()


# ==============================================================================
# 9. JALANKAN ANALISIS SPASIAL & TAMPILKAN 4 KARTU KPI
# ==============================================================================
engine = run_spatial_engine(
    st.session_state.user_lat,
    st.session_state.user_lon,
    radius_m,
    wheelchair_only,
    gdf_halte,
)

k1, k2, k3, k4 = st.columns(4, gap="medium")

with k1:
    st.markdown(
        f"""
        <div class="kpi-box">
            <div>
                <div class="kpi-title">TOTAL HALTE</div>
                <div class="kpi-num">{len(gdf_halte)} Halte</div>
                <div class="kpi-desc">{len(gdf_rute)} Koridor Aktif DIY</div>
            </div>
            <div class="kpi-icon" style="background:rgba(59,130,246,0.15);color:#3B82F6;">🚌</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k2:
    st.markdown(
        f"""
        <div class="kpi-box">
            <div>
                <div class="kpi-title">WALKABLE (&lt;{radius_m}M)</div>
                <div class="kpi-num">{engine['walkable_count']} Halte</div>
                <div class="kpi-desc">Dalam radius jalan kaki</div>
            </div>
            <div class="kpi-icon" style="background:rgba(16,185,129,0.15);color:#10B981;">🚶</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k3:
    st.markdown(
        f"""
        <div class="kpi-box">
            <div>
                <div class="kpi-title">POI BLIND SPOT</div>
                <div class="kpi-num">{engine['blind_spot_count']} / {engine['total_poi']}</div>
                <div class="kpi-desc">Jarak halte &gt; {radius_m} m</div>
            </div>
            <div class="kpi-icon" style="background:rgba(239,68,68,0.15);color:#EF4444;">🎯</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k4:
    st.markdown(
        f"""
        <div class="kpi-box">
            <div>
                <div class="kpi-title">INDEKS AKSESIBILITAS</div>
                <div class="kpi-num">{engine['indeks_aksesibilitas']}%</div>
                <div class="kpi-desc">Skor inklusif jaringan</div>
            </div>
            <div class="kpi-icon" style="background:rgba(37,99,235,0.18);color:#60A5FA;">♿</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# 10. 4 TAB NAVIGASI UTAMA
# ==============================================================================
tab_jelajah, tab_rute, tab_analisis, tab_lapor = st.tabs(
    [
        "🗺️ Jelajah Halte",
        "🧭 Rute Perjalanan",
        "📐 Analisis Spasial",
        "📢 Lapor Kondisi",
    ]
)

# ------------------------------------------------------------------------------
# TAB 1: JELAJAH HALTE
# ------------------------------------------------------------------------------
with tab_jelajah:
    col_map, col_list = st.columns([1.55, 1.0], gap="medium")

    with col_map:
        m = folium.Map(
            location=[st.session_state.user_lat, st.session_state.user_lon],
            zoom_start=14,
            tiles="OpenStreetMap",
            control_scale=True,
        )

        folium.GeoJson(
            data={"type": "FeatureCollection", "features": rute_features},
            name="Rute Koridor TransJogja",
            style_function=lambda feat: {
                "color": feat["properties"]["warna"],
                "weight": 3,
                "opacity": 0.55,
            },
            tooltip=folium.GeoJsonTooltip(fields=["koridor", "tujuan"], aliases=["Koridor:", "Arah:"]),
        ).add_to(m)

        folium.Circle(
            location=[st.session_state.user_lat, st.session_state.user_lon],
            radius=radius_m,
            color="#10B981",
            weight=2,
            fill=True,
            fill_color="#10B981",
            fill_opacity=0.18,
            tooltip=f"Radius Jalan Kaki {radius_m} m",
        ).add_to(m)

        for _, row in engine["halte_df"].iterrows():
            nama_h = row["nama"]
            is_walk = bool(row["walkable"])
            has_alert = nama_h in reported_halves

            if has_alert:
                bg_pin, icon_glyph = "#DC2626", "⚠️"
            elif is_walk:
                bg_pin, icon_glyph = "#10B981", "🚌"
            else:
                bg_pin, icon_glyph = "#1D4ED8", "🚌"

            ramp_txt = "♿ Ramp Tersedia" if row["has_ramp"] else "⚠️ Tanpa Ramp"
            popup_html = f"""
            <div style="font-family:sans-serif;min-width:210px;">
                <b style="font-size:13px;">{nama_h}</b><br>
                <span style="color:#059669;font-weight:700;font-size:12px;">
                    {row['jarak_m']:.0f} m (~{row['menit_jalan']} mnt jalan kaki)
                </span><br>
                <div style="margin:5px 0;font-size:11px;"><b>Koridor:</b> {row['koridor_full']}</div>
                <div style="font-size:11px;color:#334155;">{ramp_txt} &bull; 🟨 Guiding &bull; 👮 Petugas</div>
            </div>
            """

            folium.Marker(
                location=[row["lat"], row["lon"]],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        background:{bg_pin};
                        color:white;
                        width:26px;height:26px;
                        border-radius:50%;
                        border:2.5px solid white;
                        box-shadow:0 2px 6px rgba(0,0,0,0.45);
                        display:flex;align-items:center;justify-content:center;
                        font-size:12px;">{icon_glyph}</div>
                    """,
                    icon_size=(26, 26),
                    icon_anchor=(13, 13),
                ),
                popup=folium.Popup(popup_html, max_width=270),
                tooltip=f"{nama_h} ({row['jarak_m']:.0f} m)",
            ).add_to(m)

        folium.Marker(
            location=[st.session_state.user_lat, st.session_state.user_lon],
            icon=folium.Icon(color="red", icon="map-marker", prefix="fa"),
            tooltip=f"Posisi Anda ({st.session_state.loc_label})",
        ).add_to(m)

        map_out = st_folium(
            m,
            height=520,
            use_container_width=True,
            returned_objects=["last_clicked"],
            key="jelajah_map",
        )

        st.markdown(
            f"""
            <div class="floating-legend">
                <div class="legend-title">LEGENDA PETA</div>
                <div class="legend-grid">
                    <div><span class="dot" style="background:#EF4444;"></span>Posisi Anda</div>
                    <div><span class="dot" style="background:#10B981;"></span>Walkable (&lt;{radius_m}m)</div>
                    <div><span class="dot" style="background:#1D4ED8;"></span>Halte Lainnya</div>
                    <div><span class="dot" style="background:#DC2626;"></span>Laporan Kondisi</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if map_out and map_out.get("last_clicked"):
            c_lat = float(map_out["last_clicked"]["lat"])
            c_lon = float(map_out["last_clicked"]["lng"])
            if abs(c_lat - st.session_state.user_lat) > 0.00001 or abs(c_lon - st.session_state.user_lon) > 0.00001:
                st.session_state.gps_mode = False
                st.session_state.user_lat = c_lat
                st.session_state.user_lon = c_lon
                st.session_state.loc_label = "Klik Peta"
                st.rerun()

    with col_list:
        st.markdown(
            f"""
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.65rem;">
                <span style="font-size:1.05rem;font-weight:800;color:#F8FAFC;">🚏 5 Halte Terdekat</span>
                <span class="badge-online">{engine['walkable_count']} Walkable</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        top5 = engine["halte_df"].head(5)
        for idx, row in top5.iterrows():
            jarak_val = row["jarak_m"]
            jarak_str = format_jarak(jarak_val)
            dist_class = "pill-dist" if row["walkable"] else "pill-dist-far"
            ramp_badge = (
                "<span class='pill-ramp-ok'>♿ Ramp</span>"
                if row["has_ramp"]
                else "<span class='pill-ramp-no'>⚠️ Tanpa Ramp</span>"
            )

            st.markdown(
                f"""
                <div class="halte-card">
                    <div class="halte-card-top">
                        <div class="halte-name">{idx + 1}. {row['nama']}</div>
                        <div class="halte-corridors">{row['koridor_short']}</div>
                    </div>
                    <div class="pill-row">
                        <span class="{dist_class}">📏 {jarak_str} (~{row['menit_jalan']} mnt)</span>
                        {ramp_badge}
                        <span class="pill-guiding">🟨 Guiding</span>
                        <span class="pill-staff">👮 Petugas</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("🔍 Cek Detail & Audit Fasilitas Halte Lainnya"):
            audit_df = engine["halte_df"][["nama", "jarak_m", "koridor_full", "has_ramp"]].copy()
            audit_df["Jarak (m)"] = audit_df["jarak_m"].round(0).astype(int)
            audit_df["Akses Kursi Roda"] = audit_df["has_ramp"].map({True: "✅ Ramp", False: "⚠️ Tangga"})
            st.dataframe(
                audit_df[["nama", "Jarak (m)", "Akses Kursi Roda", "koridor_full"]].rename(
                    columns={"nama": "Nama Halte", "koridor_full": "Koridor"}
                ),
                use_container_width=True,
                hide_index=True,
                height=240,
            )


# ------------------------------------------------------------------------------
# TAB 2: RUTE PERJALANAN (FAST CACHED ROUTING + STATIC MAP KEY)
# ------------------------------------------------------------------------------
with tab_rute:
    r_left, r_right = st.columns([1.05, 1.45], gap="medium")
    daftar_halte = sorted(gdf_halte["nama"].tolist())
    nearest_asal = engine["halte_df"].iloc[0]

    with r_left:
        st.markdown("#### 🧭 Perencana Perjalanan TransJogja")
        asal_pilihan = st.selectbox(
            "Titik Naik / Halte Keberangkatan:",
            options=daftar_halte,
            index=daftar_halte.index(nearest_asal["nama"]),
        )
        default_dest_idx = (
            daftar_halte.index("Halte Malioboro 1 (Inna Garuda)")
            if "Halte Malioboro 1 (Inna Garuda)" in daftar_halte
            else 0
        )
        tujuan_pilihan = st.selectbox(
            "Titik Turun / Halte Tujuan:",
            options=daftar_halte,
            index=default_dest_idx,
        )

        asal_row = gdf_halte[gdf_halte["nama"] == asal_pilihan].iloc[0]
        hasil_rute = get_single_fastest_route(
            st.session_state.user_lat,
            st.session_state.user_lon,
            asal_row,
            tujuan_pilihan,
            gdf_halte,
            gdf_rute,
        )

        chosen_route = hasil_rute["best"] if hasil_rute["status"] == "ok" else None
        is_walkable_origin = hasil_rute["walk_m"] <= 1500.0

        if hasil_rute["status"] == "sama":
            total_trip_m = 0.0
            total_trip_min = 0
            jenis_txt = "Halte Sama"
        elif chosen_route is not None:
            bus_m_val = chosen_route["bus_m"]
            bus_min_val = chosen_route["bus_min"]
            total_trip_m = bus_m_val + (hasil_rute["walk_m"] if is_walkable_origin else 0.0)
            total_trip_min = bus_min_val + (hasil_rute["walk_min"] if is_walkable_origin else 0)
            jenis_txt = "Langsung" if chosen_route["jenis"] == "langsung" else "1x Transit"
        else:
            total_trip_m = 0.0
            total_trip_min = 0
            jenis_txt = "-"

        st.markdown(
            f"""
            <div class="trip-summary-bar">
                <div>
                    <div class="trip-sum-label">Jarak Rute</div>
                    <div class="trip-sum-val">📏 {format_jarak(total_trip_m)}</div>
                </div>
                <div>
                    <div class="trip-sum-label">Perkiraan Waktu</div>
                    <div class="trip-sum-val">⏱️ ~{total_trip_min} mnt</div>
                </div>
                <div>
                    <div class="trip-sum-label">Tipe Rute</div>
                    <div class="trip-sum-val">🚌 {jenis_txt}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if hasil_rute["status"] == "sama":
            st.error(
                f"⚠️ **Titik Naik dan Titik Turun tidak boleh sama!** Anda memilih **{asal_pilihan}** untuk keberangkatan sekaligus tujuan. Silakan pilih halte tujuan yang berbeda."
            )
        elif chosen_route is not None and chosen_route["jenis"] == "langsung":
            k1 = chosen_route["k1"]
            w1 = color_map.get(k1, "#2563EB")
            chip1 = f"<span class='corridor-chip' style='background:{w1};'>Kor. {k1}</span>"
            walk_info = (
                f"Jalan kaki dari lokasi Anda: {format_jarak(hasil_rute['walk_m'])} (~{hasil_rute['walk_min']} mnt) &bull; "
                if is_walkable_origin
                else ""
            )
            st.markdown(
                f"""
                <div class="dark-panel">
                    <span class="badge-online">⚡ RUTE TERCEPAT • LANGSUNG TANPA TRANSIT</span>
                    <div class="route-step-dark">
                        <b>📍 Titik Naik: {asal_row['nama']}</b>
                        <div class="leg-meta">{walk_info}{'♿ Ramp' if asal_row['has_ramp'] else '⚠️ Tanpa Ramp'}</div>
                    </div>
                    <div class="route-step-dark">
                        <b>🚌 Naik Koridor:</b><br>{chip1}
                        <div class="leg-meta">Jarak jalan raya: {format_jarak(chosen_route['bus_m'])} (~{chosen_route['bus_min']} mnt)</div>
                    </div>
                    <div class="route-step-end">
                        <b>🏁 Titik Turun: {hasil_rute['tujuan']['nama']}</b>
                        <div class="leg-meta">{'♿ Ramp Tersedia' if hasil_rute['tujuan']['has_ramp'] else '⚠️ Tanpa Ramp'}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif chosen_route is not None and chosen_route["jenis"] == "transit":
            k1, k2 = chosen_route["k1"], chosen_route["k2"]
            w1 = color_map.get(k1, "#2563EB")
            w2 = color_map.get(k2, "#7C3AED")
            chip1 = f"<span class='corridor-chip' style='background:{w1};'>Kor. {k1}</span>"
            chip2 = f"<span class='corridor-chip' style='background:{w2};'>Kor. {k2}</span>"
            walk_info = (
                f"Jalan kaki awal: {format_jarak(hasil_rute['walk_m'])} (~{hasil_rute['walk_min']} mnt) &bull; "
                if is_walkable_origin
                else ""
            )
            st.markdown(
                f"""
                <div class="dark-panel">
                    <span class="badge-online">⚡ RUTE TERCEPAT • 1X TITIK TRANSIT</span>
                    <div class="route-step-dark">
                        <b>📍 Titik Naik: {asal_row['nama']}</b>
                        <div class="leg-meta">{walk_info}Naik {chip1} ({format_jarak(chosen_route['leg1_m'])}, ~{chosen_route['leg1_min']} mnt)</div>
                    </div>
                    <div class="route-step-transit">
                        <b>🔄 Titik Transit: {chosen_route['hub_nama']}</b>
                        <div class="leg-meta">Pindah armada (~{chosen_route['transfer_min']} mnt) &rarr; Ganti ke {chip2} ({format_jarak(chosen_route['leg2_m'])}, ~{chosen_route['leg2_min']} mnt)</div>
                    </div>
                    <div class="route-step-end">
                        <b>🏁 Titik Turun: {hasil_rute['tujuan']['nama']}</b>
                        <div class="leg-meta">{'♿ Ramp Tersedia' if hasil_rute['tujuan']['has_ramp'] else '⚠️ Tanpa Ramp'}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.warning("Belum ditemukan koneksi langsung atau 1x transit antar kedua halte tersebut.")

    with r_right:
        bounds_pts = [
            [asal_row["lat"], asal_row["lon"]],
            [hasil_rute["tujuan"]["lat"], hasil_rute["tujuan"]["lon"]],
        ]
        if is_walkable_origin:
            bounds_pts.append([st.session_state.user_lat, st.session_state.user_lon])

        m_route = folium.Map(
            location=[float(np.mean([p[0] for p in bounds_pts])), float(np.mean([p[1] for p in bounds_pts]))],
            zoom_start=14,
            tiles="OpenStreetMap",
            control_scale=True,
        )

        if is_walkable_origin:
            folium.PolyLine(
                locations=[[st.session_state.user_lat, st.session_state.user_lon], [asal_row["lat"], asal_row["lon"]]],
                color="#10B981",
                weight=4,
                dash_array="6, 7",
                tooltip=f"Jalan kaki ke Halte: {format_jarak(hasil_rute['walk_m'])} (~{hasil_rute['walk_min']} mnt)",
            ).add_to(m_route)
            folium.CircleMarker(
                location=[st.session_state.user_lat, st.session_state.user_lon],
                radius=7.5,
                color="#FFFFFF",
                weight=2,
                fill=True,
                fill_color="#2563EB",
                fill_opacity=1.0,
                tooltip=f"Posisi Anda ({st.session_state.loc_label})",
            ).add_to(m_route)

        if hasil_rute["status"] == "sama":
            folium.Marker(
                location=[asal_row["lat"], asal_row["lon"]],
                icon=create_pin_icon("HALTE SAMA", "⚠️", "#F59E0B", "#0F172A"),
                popup=folium.Popup(
                    f"<b>{asal_row['nama']}</b><br>Titik naik & turun sama. Pilih halte tujuan berbeda.",
                    max_width=250,
                ),
                tooltip=f"{asal_row['nama']} (Titik Naik & Turun Sama)",
            ).add_to(m_route)
        else:
            if chosen_route is not None and chosen_route["jenis"] == "langsung":
                road_coords = chosen_route["coords1"]
                k_code = chosen_route["k1"]
                k_color = color_map.get(k_code, "#2563EB")
                bounds_pts.extend(road_coords)

                folium.PolyLine(locations=road_coords, color="#FFFFFF", weight=8.5, opacity=0.88).add_to(m_route)
                folium.PolyLine(
                    locations=road_coords,
                    color=k_color,
                    weight=5.5,
                    opacity=0.96,
                    tooltip=f"Kor. {k_code}: {format_jarak(chosen_route['bus_m'])} (~{chosen_route['bus_min']} mnt)",
                ).add_to(m_route)

            elif chosen_route is not None and chosen_route["jenis"] == "transit":
                bounds_pts.append([chosen_route["hub_lat"], chosen_route["hub_lon"]])
                bounds_pts.extend(chosen_route["coords1"])
                bounds_pts.extend(chosen_route["coords2"])

                c1_color = color_map.get(chosen_route["k1"], "#2563EB")
                c2_color = color_map.get(chosen_route["k2"], "#7C3AED")

                folium.PolyLine(locations=chosen_route["coords1"], color="#FFFFFF", weight=8.5, opacity=0.88).add_to(m_route)
                folium.PolyLine(
                    locations=chosen_route["coords1"],
                    color=c1_color,
                    weight=5.5,
                    opacity=0.96,
                    tooltip=f"Etape 1 (Kor. {chosen_route['k1']}): {format_jarak(chosen_route['leg1_m'])} (~{chosen_route['leg1_min']} mnt)",
                ).add_to(m_route)

                folium.PolyLine(locations=chosen_route["coords2"], color="#FFFFFF", weight=8.5, opacity=0.88).add_to(m_route)
                folium.PolyLine(
                    locations=chosen_route["coords2"],
                    color=c2_color,
                    weight=5.5,
                    opacity=0.96,
                    tooltip=f"Etape 2 (Kor. {chosen_route['k2']}): {format_jarak(chosen_route['leg2_m'])} (~{chosen_route['leg2_min']} mnt)",
                ).add_to(m_route)

            folium.Marker(
                location=[asal_row["lat"], asal_row["lon"]],
                icon=create_pin_icon("NAIK", "🚌", "#059669", "#FFFFFF"),
                popup=folium.Popup(
                    f"<b>Titik Naik: {asal_row['nama']}</b><br>Koridor: {asal_row['koridor_full']}",
                    max_width=250,
                ),
                tooltip=f"Titik Naik: {asal_row['nama']}",
            ).add_to(m_route)

            if chosen_route is not None and chosen_route["jenis"] == "transit":
                folium.Marker(
                    location=[chosen_route["hub_lat"], chosen_route["hub_lon"]],
                    icon=create_pin_icon("TRANSIT", "🔄", "#F59E0B", "#0F172A"),
                    popup=folium.Popup(
                        f"<b>Titik Transit: {chosen_route['hub_nama']}</b><br>"
                        f"Kor. {chosen_route['k1']} &rarr; Ganti Kor. {chosen_route['k2']}",
                        max_width=250,
                    ),
                    tooltip=f"Titik Transit: {chosen_route['hub_nama']}",
                ).add_to(m_route)

            folium.Marker(
                location=[hasil_rute["tujuan"]["lat"], hasil_rute["tujuan"]["lon"]],
                icon=create_pin_icon("TURUN", "🏁", "#DC2626", "#FFFFFF"),
                popup=folium.Popup(
                    f"<b>Titik Turun: {hasil_rute['tujuan']['nama']}</b><br>Koridor: {hasil_rute['tujuan']['koridor_full']}",
                    max_width=250,
                ),
                tooltip=f"Titik Turun: {hasil_rute['tujuan']['nama']}",
            ).add_to(m_route)

            lats = [p[0] for p in bounds_pts]
            lons = [p[1] for p in bounds_pts]
            m_route.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(55, 55))

        st_folium(m_route, height=505, use_container_width=True, returned_objects=[], key="route_preview_map")


# ------------------------------------------------------------------------------
# TAB 3: ANALISIS SPASIAL
# ------------------------------------------------------------------------------
with tab_analisis:
    a_left, a_right = st.columns([1.15, 1.35], gap="medium")
    with a_left:
        st.markdown(f"#### 📐 Evaluasi Blind Spot Titik Strategis (Radius {radius_m} m)")
        st.dataframe(engine["df_poi"], use_container_width=True, hide_index=True, height=440)

    with a_right:
        st.markdown("#### 🗺️ Peta Sebaran Blind Spot POI vs Jangkauan 63 Halte")
        m_bs = folium.Map(location=[-7.785, 110.382], zoom_start=12, tiles="OpenStreetMap")

        for _, h in gdf_halte.iterrows():
            folium.Circle(
                [h["lat"], h["lon"]],
                radius=radius_m,
                color="#10B981",
                weight=1,
                fill=True,
                fill_color="#10B981",
                fill_opacity=0.14,
            ).add_to(m_bs)

        for poi_name, p_lat, p_lon in YOGYA_POIS:
            row_p = engine["df_poi"][engine["df_poi"]["Lokasi Strategis (POI)"] == poi_name].iloc[0]
            is_bs = row_p["Jarak (m)"] > radius_m
            folium.CircleMarker(
                [p_lat, p_lon],
                radius=7,
                color="#FFFFFF",
                weight=1.5,
                fill=True,
                fill_color="#EF4444" if is_bs else "#10B981",
                fill_opacity=0.95,
                tooltip=f"{poi_name}: {row_p['Jarak (m)']} m ({row_p['Status']})",
            ).add_to(m_bs)

        st_folium(m_bs, height=440, use_container_width=True, returned_objects=[], key="blindspot_map")


# ------------------------------------------------------------------------------
# TAB 4: LAPOR KONDISI
# ------------------------------------------------------------------------------
with tab_lapor:
    l_form, l_feed = st.columns([1.0, 1.4], gap="medium")
    daftar_halte = sorted(gdf_halte["nama"].tolist())

    with l_form:
        st.markdown("#### 📢 Kirim Laporan Kondisi / Akses Halte")
        with st.form("form_lapor_dark", clear_on_submit=True):
            h_target = st.selectbox("Pilih Halte:", daftar_halte)
            kat_lapor = st.selectbox(
                "Status / Kategori Laporan:",
                [
                    "🟢 Kondisi Normal & Lancar",
                    "🟡 Ramai Penumpang",
                    "🔵 Armada Bus Baru Tiba",
                    "🔴 Kendala Fasilitas / Akses Ramp",
                ],
            )
            catatan_lapor = st.text_area(
                "Detail Kondisi Lapangan:",
                placeholder="Contoh: Jalur ramp landai aman, bus Koridor 1A baru melintas...",
                height=100,
            )
            if st.form_submit_button("Kirim Laporan Sekarang", type="primary", use_container_width=True):
                laporan_items.insert(
                    0,
                    {
                        "halte": h_target,
                        "kategori": kat_lapor,
                        "catatan": catatan_lapor.strip() or "Laporan kondisi lapangan.",
                        "waktu": datetime.now().strftime("%H:%M WIB"),
                    },
                )
                save_laporan(laporan_items)
                st.success(f"Laporan untuk **{h_target}** tersimpan dan otomatis memperbarui peta!")
                st.rerun()

    with l_feed:
        st.markdown("#### 🕒 Feed Laporan Terkini dari Pengguna")
        for rep in laporan_items[:8]:
            kat_text = rep.get("kategori") or rep.get("status") or "🟢 Kondisi Normal"
            is_alert = "🔴" in kat_text or "Kendala" in kat_text
            border_c = "#EF4444" if is_alert else "#1E293B"
            st.markdown(
                f"""
                <div class="halte-card" style="border-left:4px solid {border_c};">
                    <div class="halte-card-top">
                        <span class="halte-name">🚏 {rep['halte']}</span>
                        <span style="font-size:0.74rem;color:#64748B;">{rep['waktu']}</span>
                    </div>
                    <div style="margin-bottom:0.35rem;">
                        <span class="{'pill-ramp-no' if is_alert else 'pill-dist'}">{kat_text}</span>
                    </div>
                    <div style="font-size:0.83rem;color:#CBD5E1;">{rep['catatan']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )