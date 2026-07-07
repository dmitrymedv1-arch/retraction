import streamlit as st
import requests
import pandas as pd
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import json
import asyncio
import aiohttp
import time
import sqlite3
import os
from pathlib import Path
import hashlib
import joblib
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ratelimit import limits, sleep_and_retry
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from typing import List, Dict, Tuple, Optional, Set, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import io
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Image
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Image
from reportlab.platypus import KeepTogether
import xlsxwriter
from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import zipfile

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App settings
st.set_page_config(
    page_title="Retraction Article Detector Pro",
    page_icon="logo.jpg",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CUSTOM CSS DESIGN
# ============================================================================

st.markdown("""
<style>
    /* Main styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Gradient background for main */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Main header with animation */
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        animation: fadeInDown 0.8s ease-out;
        letter-spacing: -0.02em;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Step cards with glass effect */
    .step-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(0, 0, 0, 0.04);
        margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeInUp 0.6s ease-out;
    }
    
    .step-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 24px 48px rgba(0, 0, 0, 0.12);
    }
    
    /* Metric cards with gradient */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(102, 126, 234, 0.15);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 16px 32px rgba(102, 126, 234, 0.15);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #6c757d;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Result card */
    .result-card {
        background: white;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 12px;
        border-left: 4px solid #667eea;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    
    .result-card:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        transform: translateX(4px);
    }
    
    /* Filter section */
    .filter-section {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(8px);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    }
    
    /* Custom buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    /* Custom expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        font-weight: 600;
        color: #2c3e50;
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
    }
    
    /* Inputs with focus */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Selectors */
    .stSelectbox > div > div {
        border-radius: 12px;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
    }
    
    /* Info box */
    .stAlert {
        border-radius: 16px;
        border-left: 4px solid #667eea;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    .loading-spinner {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* Citation badge */
    .citation-badge {
        display: inline-block;
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #d63031;
    }
    
    /* Gradient divider */
    .gradient-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, #764ba2, #f093fb, transparent);
        margin: 20px 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        color: #6c757d;
        font-size: 0.8rem;
        border-top: 1px solid rgba(102, 126, 234, 0.2);
        margin-top: 40px;
    }
    
    /* Custom tab */
    .custom-tab {
        background: white;
        border-radius: 12px;
        padding: 8px 16px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    /* Message editor style */
    .message-editor {
        background: white;
        border-radius: 16px;
        padding: 16px;
        border: 1px solid #e0e0e0;
        margin-bottom: 16px;
    }
    
    /* Animated gradient */
    @keyframes gradientShift {
        0% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
        100% {
            background-position: 0% 50%;
        }
    }
    
    /* Navigation buttons container */
    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 20px;
        margin-top: 20px;
        padding-top: 20px;
        border-top: 1px solid rgba(102, 126, 234, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# OPENALEX API CONFIGURATION
# ============================================================================

OPENALEX_BASE_URL = "https://api.openalex.org"
MAILTO = "your-email@example.com"
POLITE_POOL_HEADER = {'User-Agent': f'Retraction-App (mailto:{MAILTO})'}

RATE_LIMIT_PER_SECOND = 8
BATCH_SIZE = 50
CURSOR_PAGE_SIZE = 200
MAX_WORKERS_ASYNC = 3
MAX_RETRIES = 3
INITIAL_DELAY = 1
MAX_DELAY = 60

CACHE_DIR = Path("./cache")
CACHE_DB = CACHE_DIR / "retraction_cache.db"
CACHE_EXPIRY_DAYS = 30

CACHE_DIR.mkdir(exist_ok=True)

# ============================================================================
# COUNTRY CODE MAPPING
# ============================================================================

COUNTRY_CODE_MAP = {
    'AF': 'Afghanistan', 'AL': 'Albania', 'DZ': 'Algeria', 'AD': 'Andorra', 'AO': 'Angola',
    'AG': 'Antigua and Barbuda', 'AR': 'Argentina', 'AM': 'Armenia', 'AU': 'Australia',
    'AT': 'Austria', 'AZ': 'Azerbaijan', 'BS': 'Bahamas', 'BH': 'Bahrain', 'BD': 'Bangladesh',
    'BB': 'Barbados', 'BY': 'Belarus', 'BE': 'Belgium', 'BZ': 'Belize', 'BJ': 'Benin',
    'BT': 'Bhutan', 'BO': 'Bolivia', 'BA': 'Bosnia and Herzegovina', 'BW': 'Botswana',
    'BR': 'Brazil', 'BN': 'Brunei', 'BG': 'Bulgaria', 'BF': 'Burkina Faso', 'BI': 'Burundi',
    'CV': 'Cabo Verde', 'KH': 'Cambodia', 'CM': 'Cameroon', 'CA': 'Canada', 'CF': 'Central African Republic',
    'TD': 'Chad', 'CL': 'Chile', 'CN': 'China', 'CO': 'Colombia', 'KM': 'Comoros',
    'CG': 'Congo', 'CR': 'Costa Rica', 'HR': 'Croatia', 'CU': 'Cuba', 'CY': 'Cyprus',
    'CZ': 'Czech Republic', 'DK': 'Denmark', 'DJ': 'Djibouti', 'DM': 'Dominica', 'DO': 'Dominican Republic',
    'EC': 'Ecuador', 'EG': 'Egypt', 'SV': 'El Salvador', 'GQ': 'Equatorial Guinea', 'ER': 'Eritrea',
    'EE': 'Estonia', 'SZ': 'Eswatini', 'ET': 'Ethiopia', 'FJ': 'Fiji', 'FI': 'Finland',
    'FR': 'France', 'GA': 'Gabon', 'GM': 'Gambia', 'GE': 'Georgia', 'DE': 'Germany',
    'GH': 'Ghana', 'GR': 'Greece', 'GD': 'Grenada', 'GT': 'Guatemala', 'GN': 'Guinea',
    'GW': 'Guinea-Bissau', 'GY': 'Guyana', 'HT': 'Haiti', 'HN': 'Honduras', 'HU': 'Hungary',
    'IS': 'Iceland', 'IN': 'India', 'ID': 'Indonesia', 'IR': 'Iran', 'IQ': 'Iraq',
    'IE': 'Ireland', 'IL': 'Israel', 'IT': 'Italy', 'JM': 'Jamaica', 'JP': 'Japan',
    'JO': 'Jordan', 'KZ': 'Kazakhstan', 'KE': 'Kenya', 'KI': 'Kiribati', 'KP': 'North Korea',
    'KR': 'South Korea', 'KW': 'Kuwait', 'KG': 'Kyrgyzstan', 'LA': 'Laos', 'LV': 'Latvia',
    'LB': 'Lebanon', 'LS': 'Lesotho', 'LR': 'Liberia', 'LY': 'Libya', 'LI': 'Liechtenstein',
    'LT': 'Lithuania', 'LU': 'Luxembourg', 'MG': 'Madagascar', 'MW': 'Malawi', 'MY': 'Malaysia',
    'MV': 'Maldives', 'ML': 'Mali', 'MT': 'Malta', 'MH': 'Marshall Islands', 'MR': 'Mauritania',
    'MU': 'Mauritius', 'MX': 'Mexico', 'FM': 'Micronesia', 'MD': 'Moldova', 'MC': 'Monaco',
    'MN': 'Mongolia', 'ME': 'Montenegro', 'MA': 'Morocco', 'MZ': 'Mozambique', 'MM': 'Myanmar',
    'NA': 'Namibia', 'NR': 'Nauru', 'NP': 'Nepal', 'NL': 'Netherlands', 'NZ': 'New Zealand',
    'NI': 'Nicaragua', 'NE': 'Niger', 'NG': 'Nigeria', 'MK': 'North Macedonia', 'NO': 'Norway',
    'OM': 'Oman', 'PK': 'Pakistan', 'PW': 'Palau', 'PA': 'Panama', 'PG': 'Papua New Guinea',
    'PY': 'Paraguay', 'PE': 'Peru', 'PH': 'Philippines', 'PL': 'Poland', 'PT': 'Portugal',
    'QA': 'Qatar', 'RO': 'Romania', 'RU': 'Russia', 'RW': 'Rwanda', 'KN': 'Saint Kitts and Nevis',
    'LC': 'Saint Lucia', 'VC': 'Saint Vincent and the Grenadines', 'WS': 'Samoa', 'SM': 'San Marino',
    'ST': 'Sao Tome and Principe', 'SA': 'Saudi Arabia', 'SN': 'Senegal', 'RS': 'Serbia',
    'SC': 'Seychelles', 'SL': 'Sierra Leone', 'SG': 'Singapore', 'SK': 'Slovakia', 'SI': 'Slovenia',
    'SB': 'Solomon Islands', 'SO': 'Somalia', 'ZA': 'South Africa', 'SS': 'South Sudan',
    'ES': 'Spain', 'LK': 'Sri Lanka', 'SD': 'Sudan', 'SR': 'Suriname', 'SE': 'Sweden',
    'CH': 'Switzerland', 'SY': 'Syria', 'TW': 'Taiwan', 'TJ': 'Tajikistan', 'TZ': 'Tanzania',
    'TH': 'Thailand', 'TL': 'Timor-Leste', 'TG': 'Togo', 'TO': 'Tonga', 'TT': 'Trinidad and Tobago',
    'TN': 'Tunisia', 'TR': 'Turkey', 'TM': 'Turkmenistan', 'TV': 'Tuvalu', 'UG': 'Uganda',
    'UA': 'Ukraine', 'AE': 'United Arab Emirates', 'GB': 'United Kingdom', 'US': 'United States',
    'UY': 'Uruguay', 'UZ': 'Uzbekistan', 'VU': 'Vanuatu', 'VA': 'Vatican City', 'VE': 'Venezuela',
    'VN': 'Vietnam', 'YE': 'Yemen', 'ZM': 'Zambia', 'ZW': 'Zimbabwe'
}

# ============================================================================
# SQLITE CACHING
# ============================================================================

def init_cache_db():
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS works_cache (
            doi TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS retraction_notices_cache (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS retracted_articles_cache (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_cache (
            search_key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_works_expires ON works_cache(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notices_expires ON retraction_notices_cache(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_expires ON retracted_articles_cache(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_expires ON search_cache(expires_at)')
    
    conn.commit()
    conn.close()

def get_cache_connection():
    init_cache_db()
    return sqlite3.connect(CACHE_DB, check_same_thread=False)

def cache_work(doi: str, data: dict):
    conn = get_cache_connection()
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(days=CACHE_EXPIRY_DAYS)
    cursor.execute('''
        INSERT OR REPLACE INTO works_cache (doi, data, expires_at)
        VALUES (?, ?, ?)
    ''', (doi, json.dumps(data), expires_at))
    conn.commit()
    conn.close()

def get_cached_work(doi: str) -> Optional[dict]:
    conn = get_cache_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT data FROM works_cache 
        WHERE doi = ? AND (expires_at IS NULL OR expires_at > ?)
    ''', (doi, datetime.now()))
    result = cursor.fetchone()
    conn.close()
    if result:
        return json.loads(result[0])
    return None

def cache_retraction_notice(notice_id: str, data: dict):
    conn = get_cache_connection()
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(days=CACHE_EXPIRY_DAYS)
    cursor.execute('''
        INSERT OR REPLACE INTO retraction_notices_cache (id, data, expires_at)
        VALUES (?, ?, ?)
    ''', (notice_id, json.dumps(data), expires_at))
    conn.commit()
    conn.close()

def get_cached_retraction_notice(notice_id: str) -> Optional[dict]:
    conn = get_cache_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT data FROM retraction_notices_cache 
        WHERE id = ? AND (expires_at IS NULL OR expires_at > ?)
    ''', (notice_id, datetime.now()))
    result = cursor.fetchone()
    conn.close()
    if result:
        return json.loads(result[0])
    return None

def cache_retracted_article(article_id: str, data: dict):
    conn = get_cache_connection()
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(days=CACHE_EXPIRY_DAYS)
    cursor.execute('''
        INSERT OR REPLACE INTO retracted_articles_cache (id, data, expires_at)
        VALUES (?, ?, ?)
    ''', (article_id, json.dumps(data), expires_at))
    conn.commit()
    conn.close()

def get_cached_retracted_article(article_id: str) -> Optional[dict]:
    conn = get_cache_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT data FROM retracted_articles_cache 
        WHERE id = ? AND (expires_at IS NULL OR expires_at > ?)
    ''', (article_id, datetime.now()))
    result = cursor.fetchone()
    conn.close()
    if result:
        return json.loads(result[0])
    return None

def cache_search_result(search_key: str, data: dict):
    conn = get_cache_connection()
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(days=7)
    cursor.execute('''
        INSERT OR REPLACE INTO search_cache (search_key, data, expires_at)
        VALUES (?, ?, ?)
    ''', (search_key, json.dumps(data), expires_at))
    conn.commit()
    conn.close()

def get_cached_search_result(search_key: str) -> Optional[dict]:
    conn = get_cache_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT data FROM search_cache 
        WHERE search_key = ? AND (expires_at IS NULL OR expires_at > ?)
    ''', (search_key, datetime.now()))
    result = cursor.fetchone()
    conn.close()
    if result:
        return json.loads(result[0])
    return None

def clear_old_cache():
    conn = get_cache_connection()
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute('DELETE FROM works_cache WHERE expires_at IS NOT NULL AND expires_at <= ?', (now,))
    cursor.execute('DELETE FROM retraction_notices_cache WHERE expires_at IS NOT NULL AND expires_at <= ?', (now,))
    cursor.execute('DELETE FROM retracted_articles_cache WHERE expires_at IS NOT NULL AND expires_at <= ?', (now,))
    cursor.execute('DELETE FROM search_cache WHERE expires_at IS NOT NULL AND expires_at <= ?', (now,))
    changes = cursor.rowcount
    if changes > 0:
        conn.commit()
        logger.info(f"Cleared {changes} expired cache entries")
    conn.close()

# ============================================================================
# YEAR PARSING FUNCTIONS (UNCHANGED)
# ============================================================================

def parse_year_filter(year_input: str) -> List[int]:
    """
    Parse year filter string.
    Examples:
    "2000" -> [2000]
    "2010" -> [2010]
    "2010-2020" -> [2010, 2011, 2012, ..., 2020]
    "2020" -> [2020]
    "2023-2026" -> [2023, 2024, 2025, 2026]
    "2005,2010-2015,2020" -> [2005, 2010, 2011, 2012, 2013, 2014, 2015, 2020]
    "2015,2018-2020,2022-2024" -> [2015, 2018, 2019, 2020, 2022, 2023, 2024]
    """
    years = set()
    
    if not year_input or year_input.strip() == "":
        current_year = datetime.now().year
        return [current_year - 2, current_year - 1, current_year]
    
    parts = year_input.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = part.split('-')
                start_year = int(start.strip())
                end_year = int(end.strip())
                for year in range(start_year, end_year + 1):
                    if 1900 <= year <= 2100:
                        years.add(year)
            except ValueError:
                logger.warning(f"Could not parse range: {part}")
        else:
            try:
                year = int(part)
                if 1900 <= year <= 2100:
                    years.add(year)
            except ValueError:
                logger.warning(f"Could not parse year: {part}")
    
    return sorted(list(years))

def format_year_filter_for_filename(years: List[int]) -> str:
    """
    Format year list for filename.
    [2021, 2023, 2024, 2025] -> "2021,2023-2025"
    """
    if not years:
        return ""
    
    years_sorted = sorted(years)
    ranges = []
    start = years_sorted[0]
    end = years_sorted[0]
    
    for i in range(1, len(years_sorted)):
        if years_sorted[i] == end + 1:
            end = years_sorted[i]
        else:
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            start = years_sorted[i]
            end = years_sorted[i]
    
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")
    
    return ",".join(ranges)

def calculate_toc_indices(total_count: int) -> List[int]:
    """
    Calculate which article indices to display in Table of Contents.
    Uses multiples of 5, 10, or 50 depending on total count.
    Always includes first and last articles.
    
    Args:
        total_count: Total number of articles
        
    Returns:
        List of 1-based indices to display in TOC
    """
    if total_count <= 0:
        return []
    
    # If 25 or fewer articles, show all
    if total_count <= 25:
        return list(range(1, total_count + 1))
    
    # Always include first and last
    indices = [1, total_count]
    
    # Determine step based on total count
    if total_count <= 100:
        step = 5
    elif total_count <= 500:
        step = 10
    else:
        step = 50
    
    # Add intermediate indices with the calculated step
    for i in range(step, total_count, step):
        if i not in indices:
            indices.append(i)
    
    return sorted(indices)

# ============================================================================
# ASYNCIO + AIOHTTP CLIENT
# ============================================================================

class OpenAlexAsyncClient:
    def __init__(self):
        self.session = None
        self.semaphore = asyncio.Semaphore(MAX_WORKERS_ASYNC)
        self.request_count = 0
        self.start_time = time.time()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=POLITE_POOL_HEADER,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=INITIAL_DELAY, max=MAX_DELAY),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def make_request(self, url: str) -> Optional[dict]:
        async with self.semaphore:
            elapsed = time.time() - self.start_time
            expected_time = self.request_count / RATE_LIMIT_PER_SECOND
            
            if elapsed < expected_time:
                wait_time = expected_time - elapsed
                await asyncio.sleep(wait_time)
            
            try:
                async with self.session.get(url) as response:
                    self.request_count += 1
                    
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 5))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=429
                        )
                    
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.warning(f"Resource not found: {url}")
                        return None
                    else:
                        logger.error(f"HTTP {response.status}: {url}")
                        return None
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout: {url}")
                raise
            except Exception as e:
                logger.error(f"Error: {url} - {str(e)}")
                raise
    
    async def fetch_works_by_dois_batch(self, dois: List[str]) -> List[Optional[dict]]:
        if not dois:
            return []
        
        cached_results = []
        uncached_dois = []
        
        for doi in dois:
            cached = get_cached_work(doi)
            if cached:
                cached_results.append(cached)
            else:
                uncached_dois.append(doi)
        
        if not uncached_dois:
            return cached_results
        
        logger.info(f"Fetching {len(uncached_dois)} works via batch API")
        
        doi_filter = "|".join(uncached_dois)
        url = f"{OPENALEX_BASE_URL}/works?filter=doi:{doi_filter}&per-page=200"
        
        try:
            data = await self.make_request(url)
            if data and 'results' in data:
                results = data['results']
                
                for work in results:
                    doi = work.get('doi', '').replace('https://doi.org/', '')
                    if doi:
                        cache_work(doi, work)
                
                doi_to_work = {w.get('doi', '').replace('https://doi.org/', ''): w for w in results}
                batch_results = []
                
                for doi in uncached_dois:
                    if doi in doi_to_work:
                        batch_results.append(doi_to_work[doi])
                    else:
                        try:
                            work_data = await self.fetch_single_work(doi)
                            batch_results.append(work_data)
                        except:
                            batch_results.append(None)
                
                return cached_results + batch_results
            else:
                return cached_results + [None] * len(uncached_dois)
                
        except Exception as e:
            logger.error(f"Batch fetch error: {str(e)}")
            return cached_results + [None] * len(uncached_dois)
    
    async def fetch_single_work(self, doi: str) -> Optional[dict]:
        cached = get_cached_work(doi)
        if cached:
            return cached
        
        url = f"{OPENALEX_BASE_URL}/works/https://doi.org/{doi}"
        data = await self.make_request(url)
        
        if data:
            cache_work(doi, data)
        
        return data
    
    async def search_retraction_notices(self, years: List[int], countries: List[str], 
                                        progress_callback=None) -> List[dict]:
        """
        Search for retraction notices by years and countries.
        Looks for type: erratum|retraction|withdrawal AND keywords in display_name.
        """
        all_notices = []
        cursor = "*"
        page_count = 0
        total_count = 0
        
        # Build filter string: years
        years_str = "|".join(map(str, years))
        
        # Build type filter - multiple types
        type_filters = ["erratum", "retraction", "withdrawal", "retraction-notice"]
        type_str = "|".join(type_filters)
        
        filter_str = f"publication_year:{years_str},type:{type_str}"
        
        logger.info(f"Searching for retraction notices, years {years}, countries {countries}")
        
        try:
            while True:
                page_count += 1
                
                params = {
                    "filter": filter_str,
                    "per-page": CURSOR_PAGE_SIZE,
                    "cursor": cursor,
                    "mailto": MAILTO
                }
                
                url = f"{OPENALEX_BASE_URL}/works"
                response = requests.get(url, params=params, headers=POLITE_POOL_HEADER, timeout=60)
                
                if response.status_code != 200:
                    logger.error(f"Error fetching notices: {response.status_code}")
                    break
                
                data = response.json()
                
                if page_count == 1:
                    total_count = data.get('meta', {}).get('count', 0)
                    logger.info(f"Total notices found: {total_count}")
                    
                    if total_count == 0:
                        return []
                
                works = data.get('results', [])
                if not works:
                    break
                
                # Filter by retraction keywords in display_name or title                for work in works:
                    display_name = work.get('display_name', '')
                    title = work.get('title', '')
                    
                    # Check for retraction keywords
                    if re.search(r'(?i)retraction|retracted', display_name) or re.search(r'(?i)retraction|retracted', title):
                        # Check if notice has authors from selected countries
                        if countries:
                            has_country = self._work_has_country(work, countries)
                            if has_country:
                                all_notices.append(work)
                                cache_retraction_notice(work.get('id', ''), work)
                        else:
                            all_notices.append(work)
                            cache_retraction_notice(work.get('id', ''), work)
                
                if progress_callback and total_count > 0:
                    progress = min(len(all_notices) / total_count, 1.0)
                    progress_callback(progress, len(all_notices), page_count, total_count)
                
                logger.info(f"Page {page_count}: found {len(works)} works, filtered: {len(all_notices)} notices")
                
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)
            
            logger.info(f"Finished searching notices. Total: {len(all_notices)}")
            return all_notices
            
        except Exception as e:
            logger.error(f"Error in search_retraction_notices: {str(e)}")
            return all_notices
    
    async def search_retracted_articles(self, years: List[int], countries: List[str],
                                        progress_callback=None) -> List[dict]:
        """
        Search for retracted articles by years and countries.
        Looks for is_retracted: true.
        """
        all_articles = []
        cursor = "*"
        page_count = 0
        total_count = 0
        
        # Build filter string: years + is_retracted
        years_str = "|".join(map(str, years))
        filter_str = f"publication_year:{years_str},is_retracted:true"
        
        logger.info(f"Searching for retracted articles, years {years}, countries {countries}")
        
        try:
            while True:
                page_count += 1
                
                params = {
                    "filter": filter_str,
                    "per-page": CURSOR_PAGE_SIZE,
                    "cursor": cursor,
                    "mailto": MAILTO
                }
                
                url = f"{OPENALEX_BASE_URL}/works"
                response = requests.get(url, params=params, headers=POLITE_POOL_HEADER, timeout=60)
                
                if response.status_code != 200:
                    logger.error(f"Error fetching articles: {response.status_code}")
                    break
                
                data = response.json()
                
                if page_count == 1:
                    total_count = data.get('meta', {}).get('count', 0)
                    logger.info(f"Total retracted articles found: {total_count}")
                    
                    if total_count == 0:
                        return []
                
                works = data.get('results', [])
                if not works:
                    break
                
                # Filter by countries
                for work in works:
                    if countries:
                        has_country = self._work_has_country(work, countries)
                        if has_country:
                            all_articles.append(work)
                            cache_retracted_article(work.get('id', ''), work)
                    else:
                        all_articles.append(work)
                        cache_retracted_article(work.get('id', ''), work)
                
                if progress_callback and total_count > 0:
                    progress = min(len(all_articles) / total_count, 1.0)
                    progress_callback(progress, len(all_articles), page_count, total_count)
                
                logger.info(f"Page {page_count}: found {len(works)} works, filtered: {len(all_articles)} articles")
                
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)
            
            logger.info(f"Finished searching articles. Total: {len(all_articles)}")
            return all_articles
            
        except Exception as e:
            logger.error(f"Error in search_retracted_articles: {str(e)}")
            return all_articles
    
    def _work_has_country(self, work: dict, countries: List[str]) -> bool:
        """
        Check if work has at least one author from selected countries.
        """
        if not countries:
            return True
        
        authorships = work.get('authorships', [])
        for authorship in authorships:
            institutions = authorship.get('institutions', [])
            for inst in institutions:
                country_code = inst.get('country_code', '')
                if country_code and country_code.upper() in countries:
                    return True
                # Also check country field
                country = inst.get('country', '')
                if country:
                    # Try to find matching country code
                    for code, name in COUNTRY_CODE_MAP.items():
                        if name.upper() == country.upper() and code in countries:
                            return True
        
        return False

# ============================================================================
# SYNCHRONOUS WRAPPERS
# ============================================================================

def run_async(coro):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def fetch_works_by_dois_sync(dois: List[str]) -> Tuple[List[dict], int, int]:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    batches = [dois[i:i + BATCH_SIZE] for i in range(0, len(dois), BATCH_SIZE)]
    all_results = []
    successful = 0
    failed = 0
    
    async def process_batches():
        nonlocal all_results, successful, failed
        async with OpenAlexAsyncClient() as client:
            for i, batch in enumerate(batches):
                progress = (i + 1) / len(batches)
                progress_bar.progress(progress)
                status_text.text(f"Batch {i+1}/{len(batches)}: {len(batch)} DOI")
                
                results = await client.fetch_works_by_dois_batch(batch)
                
                for result in results:
                    if result:
                        successful += 1
                        all_results.append({
                            'data': result,
                            'success': True
                        })
                    else:
                        failed += 1
                        all_results.append({
                            'data': None,
                            'success': False
                        })
                
                if i < len(batches) - 1:
                    await asyncio.sleep(1)
    
    run_async(process_batches())
    
    progress_bar.empty()
    status_text.empty()
    
    return all_results, successful, failed

def search_retraction_notices_sync(years: List[int], countries: List[str]) -> List[dict]:
    """
    Search for retraction notices by years and countries.
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_notices = []
    
    def update_progress(progress, count, page, total):
        progress_bar.progress(progress)
        status_text.text(f"Page {page}: {count}/{total} notices found")
    
    async def search():
        async with OpenAlexAsyncClient() as client:
            return await client.search_retraction_notices(
                years, countries, update_progress
            )
    
    result = run_async(search())
    progress_bar.empty()
    status_text.empty()
    return result

def search_retracted_articles_sync(years: List[int], countries: List[str]) -> List[dict]:
    """
    Search for retracted articles by years and countries.
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_articles = []
    
    def update_progress(progress, count, page, total):
        progress_bar.progress(progress)
        status_text.text(f"Page {page}: {count}/{total} articles found")
    
    async def search():
        async with OpenAlexAsyncClient() as client:
            return await client.search_retracted_articles(
                years, countries, update_progress
            )
    
    result = run_async(search())
    progress_bar.empty()
    status_text.empty()
    return result

# ============================================================================
# HELPER FUNCTIONS (UNCHANGED)
# ============================================================================

def normalize_word(word: str) -> str:
    word_lower = word.lower()
    
    if len(word_lower) < 4:
        return ''
    
    plural_exceptions = {
        'analyses': 'analysis', 'bases': 'base', 'criteria': 'criterion',
        'hypotheses': 'hypothesis', 'phenomena': 'phenomenon',
        'properties': 'property', 'activities': 'activity',
        'efficiencies': 'efficiency', 'performances': 'performance'
    }
    
    if word_lower in plural_exceptions:
        return plural_exceptions[word_lower]
    
    if word_lower.endswith('ies'):
        base = word_lower[:-3] + 'y'
        if len(base) >= 4:
            return base
    elif word_lower.endswith('es'):
        if word_lower.endswith(('ches', 'shes', 'xes', 'zes', 'sses')):
            base = word_lower[:-2]
            if len(base) >= 4:
                return base
    elif word_lower.endswith('s') and not word_lower.endswith(('ss', 'us', 'is', 'ys', 'as')):
        base = word_lower[:-1]
        if len(base) >= 4:
            return base
    
    return word_lower

def extract_keywords_from_title(title: str) -> List[str]:
    if not title:
        return []
    
    words = re.findall(r'\b[a-zA-Z]{4,}\b', title)
    filtered_words = []
    
    for word in words:
        word_lower = word.lower()
        
        if word_lower in ALL_STOPWORDS:
            continue
        
        if re.search(r'\d', word_lower):
            continue
        
        normalized = normalize_word(word_lower)
        if normalized:
            filtered_words.append(normalized)
    
    return filtered_words

def parse_doi_input(text: str) -> List[str]:
    """
    Extract DOI identifiers from text handling various formats.
    """
    if not text or not text.strip():
        return []
    
    doi_patterns = [
        r'(?i)https?://(?:dx\.)?doi\.org/(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)',
        r'(?i)(?:doi|DOI)[:\s]+(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)',
        r'\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b'
    ]
    
    all_dois = []
    
    for pattern in doi_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                doi = match[0] if match else ''
            else:
                doi = match
            
            if doi:
                doi = doi.strip()
                doi = re.sub(r'[.,;:]+$', '', doi)
                doi = doi.strip('<>()[]{}')
                all_dois.append(doi)
    
    seen = set()
    unique_dois = []
    for doi in all_dois:
        doi_lower = doi.lower()
        if doi_lower not in seen:
            seen.add(doi_lower)
            unique_dois.append(doi)
    
    return unique_dois[:300]

def analyze_keywords_parallel(titles: List[str]) -> Counter:
    all_keywords = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(extract_keywords_from_title, title) for title in titles]
        for future in as_completed(futures):
            all_keywords.extend(future.result())
    
    return Counter(all_keywords)

def extract_numeric_from_doi(doi: str) -> int:
    if not doi:
        return 0
    
    parts = doi.replace('.', '/').replace('-', '/').split('/')
    
    for part in reversed(parts):
        if part.isdigit():
            return int(part)
    
    numbers = re.findall(r'\d+', doi)
    if numbers:
        return int(numbers[-1])
    
    return 0

# ============================================================================
# ENRICHMENT FUNCTIONS FOR RETRACTION
# ============================================================================

def extract_all_authors_and_affiliations(work: dict) -> Tuple[List[str], List[str]]:
    """
    Extract all authors and unique affiliations from authorships.
    No truncation - returns full lists.
    """
    authors = []
    affiliations = set()
    
    authorships = work.get('authorships', [])
    
    for authorship in authorships:
        if authorship:
            # Extract author
            author = authorship.get('author', {})
            if author:
                author_name = author.get('display_name', '')
                if author_name:
                    import unicodedata
                    author_name = unicodedata.normalize('NFC', str(author_name))
                    author_name = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s\.\,\-\'\(\)]', '', author_name)
                    author_name = re.sub(r'\s+', ' ', author_name).strip()
                    if author_name:
                        authors.append(author_name)
            
            # Extract institutions (affiliations)
            for inst in authorship.get('institutions', []):
                if inst:
                    inst_name = inst.get('display_name', '')
                    if inst_name:
                        inst_name = inst_name.strip()
                        if inst_name:
                            affiliations.add(inst_name)
    
    return authors, list(affiliations)

def extract_country_from_work(work: dict) -> str:
    """
    Extract country from first institution in first authorship.
    """
    authorships = work.get('authorships', [])
    if authorships:
        first_authorship = authorships[0]
        if first_authorship:
            institutions = first_authorship.get('institutions', [])
            if institutions:
                first_inst = institutions[0]
                if first_inst:
                    country = first_inst.get('country_code', '')
                    if country:
                        return country.upper()
                    country_name = first_inst.get('country', '')
                    if country_name:
                        return country_name
    return 'Unknown'

def get_oa_status(work: dict) -> str:
    """
    Get Open Access status.
    """
    open_access = work.get('open_access', {})
    if open_access:
        is_oa = open_access.get('is_oa', False)
        if is_oa:
            oa_status = open_access.get('oa_status', '')
            if oa_status:
                return oa_status.capitalize()
            return 'Open Access'
    return 'Closed Access'

def get_publication_type_info(work: dict) -> Tuple[str, str, str]:
    """
    Determine publication type, color, and icon for styling.
    Returns: (type_label, color_hex, icon_emoji)
    """
    pub_type = work.get('type', '').lower()
    primary_location = work.get('primary_location', {})
    source = primary_location.get('source', {}) if primary_location else {}
    source_type = source.get('type', '').lower() if source else ''
    raw_type = primary_location.get('raw_type', '').lower() if primary_location and isinstance(primary_location, dict) and primary_location.get('raw_type') else ''
    
    # Check for retraction notice
    if pub_type in ['erratum', 'retraction', 'withdrawal', 'retraction-notice']:
        return ('Retraction Notice', '#e74c3c', '🔴')
    
    # Check for preprint / repository
    if pub_type == 'preprint' or source_type == 'repository' or 'preprint' in pub_type:
        return ('Preprint', '#9b59b6', '📋')
    
    # Check for book / book chapter
    if pub_type in ['book-chapter', 'book', 'edited-book'] or source_type == 'book series' or 'book' in pub_type:
        return ('Book/Chapter', '#e67e22', '📚')
    
    # Check for conference proceedings
    if pub_type == 'proceedings-article' or 'proceedings' in pub_type or 'proceedings' in raw_type:
        return ('Conference', '#2980b9', '🎤')
    
    # Check for journal article
    if pub_type == 'journal-article' or source_type == 'journal':
        return ('Article', '#27ae60', '📄')
    
    # Default
    if pub_type:
        return (pub_type.capitalize(), '#7f8c8d', '📎')
    return ('Other', '#95a5a6', '📎')

def enrich_retraction_data(work: dict, is_notice: bool = False) -> dict:
    """
    Enrich retraction work data with complete information including all fields.
    No truncation of authors or affiliations.
    """
    if not work:
        return {}
    
    doi_raw = work.get('doi')
    doi_clean = ''
    if doi_raw:
        doi_clean = str(doi_raw).replace('https://doi.org/', '')
    
    # Extract ALL authors and affiliations (no truncation)
    authors, affiliations = extract_all_authors_and_affiliations(work)
    authors_str = ', '.join(authors) if authors else 'Authors not specified'
    
    # Join all affiliations with slash separator
    if affiliations:
        affiliations_str = ' / '.join(affiliations)
    else:
        affiliations_str = 'No affiliations specified'
    
    # Extract publication info
    biblio = work.get('biblio', {})
    volume = biblio.get('volume', '')
    issue = biblio.get('issue', '')
    first_page = biblio.get('first_page', '')
    last_page = biblio.get('last_page', '')
    
    # Format pages
    pages_str = ''
    if first_page and last_page and first_page != last_page:
        pages_str = f"{first_page}-{last_page}"
    elif first_page:
        pages_str = first_page
    elif last_page:
        pages_str = last_page
    
    # Get journal and publisher info
    journal_name = ''
    publisher = ''
    publisher_chain = []
    primary_location = work.get('primary_location')
    if primary_location:
        source = primary_location.get('source', {})
        if source:
            journal_name = source.get('display_name', '') or ''
            publisher = source.get('host_organization_name', '') or ''
            if not publisher:
                publisher = source.get('publisher', '') or ''
            if not publisher:
                publisher = source.get('host_organization', '') or ''
            publisher_chain = source.get('host_organization_lineage_names', [])
    
    # Extract topic info
    primary_topic = work.get('primary_topic', {})
    topic_name = primary_topic.get('display_name', '') if primary_topic else ''
    topic_id = ''
    if primary_topic:
        topic_id_raw = primary_topic.get('id', '')
        if topic_id_raw:
            topic_id = topic_id_raw.split('/')[-1]
    
    # Citation metrics
    citations_total = work.get('cited_by_count', 0)
    referenced_works = work.get('referenced_works_count', 0)
    
    publication_year = work.get('publication_year', 0)
    current_year = datetime.now().year
    
    age = max(1, current_year - publication_year) if publication_year > 0 else 1
    citations_per_year = citations_total / age
    
    # OA status
    oa_status = get_oa_status(work)
    
    # Publication date
    publication_date = work.get('publication_date', '')
    
    # Get publication type info
    type_label, type_color, type_icon = get_publication_type_info(work)
    
    # Extract all countries from authorships
    countries = set()
    authorships = work.get('authorships', [])
    for authorship in authorships:
        institutions = authorship.get('institutions', [])
        for inst in institutions:
            country_code = inst.get('country_code', '')
            if country_code:
                countries.add(country_code.upper())
            country = inst.get('country', '')
            if country:
                for code, name in COUNTRY_CODE_MAP.items():
                    if name.upper() == country.upper():
                        countries.add(code)
                        break
    
    enriched = {
        'doi': doi_clean,
        'doi_url': f"https://doi.org/{doi_clean}" if doi_clean else '',
        'title': work.get('title', 'No title'),
        'display_name': work.get('display_name', 'No title'),
        'publication_year': publication_year,
        'publication_date': publication_date,
        'cited_by_count': citations_total,
        'citations_per_year': round(citations_per_year, 1),
        'referenced_works_count': referenced_works,
        'authors': authors_str,
        'authors_list': authors,
        'affiliations': affiliations,
        'affiliations_str': affiliations_str,
        'journal_name': journal_name,
        'publisher': publisher,
        'publisher_chain': publisher_chain,
        'volume': volume,
        'issue': issue,
        'pages': pages_str,
        'primary_topic': topic_name,
        'topic_id': topic_id,
        'oa_status': oa_status,
        'type': work.get('type', ''),
        'type_label': type_label,
        'type_color': type_color,
        'type_icon': type_icon,
        'country': extract_country_from_work(work),
        'countries': list(countries),
        'is_retracted': work.get('is_retracted', False),
        'is_notice': is_notice,
        'openalex_id': work.get('id', ''),
        'referenced_works': work.get('referenced_works', [])
    }
    
    return enriched

# ============================================================================
# MERGING RETRACTION PAIRS
# ============================================================================

def extract_clean_title(title: str) -> str:
    """
    Extract clean title from retraction notice.
    Remove prefixes like "Retraction Notice to", "RETRACTED:", etc.
    """
    if not title:
        return ""
    
    # Remove common prefixes
    patterns = [
        r'(?i)^Retraction Notice to\s*["\u201c]*',
        r'(?i)^Retraction Notice:\s*["\u201c]*',
        r'(?i)^Notice to\s*["\u201c]*',
        r'(?i)^Notice:\s*["\u201c]*',
        r'(?i)^RETRACTED:\s*["\u201c]*',
        r'(?i)^Retracted:\s*["\u201c]*',
        r'(?i)^Statement of Retraction:\s*["\u201c]*',
    ]
    
    clean_title = title
    for pattern in patterns:
        clean_title = re.sub(pattern, '', clean_title)
    
    # Remove trailing quotes and spaces
    clean_title = clean_title.strip()
    clean_title = re.sub(r'^["\u201c\u201d]+|["\u201c\u201d]+$', '', clean_title)
    clean_title = clean_title.strip()
    
    return clean_title

def find_matching_article(clean_title: str, articles: List[dict]) -> Optional[dict]:
    """
    Find matching retracted article by clean title.
    Exact match after cleaning both titles.
    """
    if not clean_title or not articles:
        return None
    
    clean_title_lower = clean_title.lower().strip()
    
    for article in articles:
        article_title = article.get('display_name', '') or article.get('title', '')
        if not article_title:
            continue
        
        # Try exact match after cleaning
        article_clean = extract_clean_title(article_title).lower().strip()
        if article_clean == clean_title_lower:
            return article
        
        # Also try matching the clean_title against the full title
        if clean_title_lower in article_title.lower():
            return article
        
        # Try matching the article title against the clean_title
        if article_clean and article_clean in clean_title_lower:
            return article
    
    return None

def merge_retraction_pairs(notices: List[dict], articles: List[dict]) -> List[dict]:
    """
    Merge retraction notices with their corresponding retracted articles.
    Returns list of merged cards.
    """
    merged_cards = []
    used_notices = set()
    used_articles = set()
    
    # First pass: try to match notices with articles
    for notice in notices:
        notice_title = notice.get('display_name', '') or notice.get('title', '')
        clean_title = extract_clean_title(notice_title)
        
        if clean_title:
            matched_article = find_matching_article(clean_title, articles)
            if matched_article:
                article_id = matched_article.get('id', '')
                notice_id = notice.get('id', '')
                
                # Check if this article already has a notice
                # If multiple notices for same article, we'll handle later
                if article_id not in used_articles:
                    # Create merged card
                    merged_card = {
                        'article_data': matched_article,
                        'notice_data': [notice],
                        'is_merged': True,
                        'article_enriched': enrich_retraction_data(matched_article, is_notice=False),
                        'notice_enriched': [enrich_retraction_data(notice, is_notice=True)]
                    }
                    merged_cards.append(merged_card)
                    used_articles.add(article_id)
                    used_notices.add(notice_id)
                else:
                    # Multiple notices for same article - add to existing
                    for card in merged_cards:
                        if card.get('article_data', {}).get('id', '') == article_id:
                            if isinstance(card['notice_data'], list):
                                card['notice_data'].append(notice)
                                card['notice_enriched'].append(enrich_retraction_data(notice, is_notice=True))
                            used_notices.add(notice_id)
                            break
    
    # Second pass: notices without matching articles
    for notice in notices:
        notice_id = notice.get('id', '')
        if notice_id not in used_notices:
            merged_card = {
                'article_data': None,
                'notice_data': [notice],
                'is_merged': False,
                'article_enriched': None,
                'notice_enriched': [enrich_retraction_data(notice, is_notice=True)]
            }
            merged_cards.append(merged_card)
            used_notices.add(notice_id)
    
    # Third pass: articles without matching notices
    for article in articles:
        article_id = article.get('id', '')
        if article_id not in used_articles:
            merged_card = {
                'article_data': article,
                'notice_data': [],
                'is_merged': False,
                'article_enriched': enrich_retraction_data(article, is_notice=False),
                'notice_enriched': []
            }
            merged_cards.append(merged_card)
            used_articles.add(article_id)
    
    return merged_cards

# ============================================================================
# GROUPING FUNCTIONS FOR RETRACTION REPORTS
# ============================================================================

def group_cards_by_country_affiliation(cards: List[dict]) -> Dict[str, Dict[str, List[dict]]]:
    """
    Group merged cards by Country -> Affiliation.
    Cards with multiple countries appear in multiple groups.
    """
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for card in cards:
        # Determine which countries this card belongs to
        countries = set()
        
        # Get countries from article if available
        if card.get('article_enriched'):
            article_countries = card['article_enriched'].get('countries', [])
            countries.update(article_countries)
        else:
            # Get from notice
            for notice_enriched in card.get('notice_enriched', []):
                notice_countries = notice_enriched.get('countries', [])
                countries.update(notice_countries)
        
        # If no countries found, use 'Unknown'
        if not countries:
            countries.add('Unknown')
        
        # Get affiliations from article if available
        affiliations = []
        if card.get('article_enriched'):
            affiliations = card['article_enriched'].get('affiliations', [])
        if not affiliations:
            for notice_enriched in card.get('notice_enriched', []):
                affs = notice_enriched.get('affiliations', [])
                affiliations.extend(affs)
        
        if not affiliations:
            affiliations = ['Unknown Affiliation']
        
        # Add card to each country and each affiliation
        for country in countries:
            country_full = COUNTRY_CODE_MAP.get(country, country)
            for aff in affiliations:
                hierarchy[country_full][aff].append(card)
    
    return hierarchy

def group_cards_by_author(cards: List[dict]) -> Dict[str, List[dict]]:
    """
    Group merged cards by author (last name + first initial).
    Cards with multiple authors appear in multiple author groups.
    """
    author_cards = defaultdict(list)
    
    for card in cards:
        # Get authors from article if available
        authors = []
        if card.get('article_enriched'):
            authors = card['article_enriched'].get('authors_list', [])
        if not authors:
            for notice_enriched in card.get('notice_enriched', []):
                auths = notice_enriched.get('authors_list', [])
                authors.extend(auths)
        
        if not authors:
            authors = ['Unknown Author']
        
        # For each author, extract last name + first initial
        for author in authors:
            if author and author != 'Authors not specified':
                # Parse author name: "Last, First" or "First Last"
                parts = author.split()
                if len(parts) >= 2:
                    # Try to get last name and first initial
                    last_name = parts[-1]
                    first_initial = parts[0][0] if parts[0] else ''
                    author_key = f"{last_name}, {first_initial}."
                else:
                    author_key = author
                
                author_cards[author_key].append(card)
    
    return dict(author_cards)

def group_cards_by_publisher_journal(cards: List[dict]) -> Dict[str, Dict[str, List[dict]]]:
    """
    Group merged cards by Publisher -> Journal.
    """
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for card in cards:
        # Get publisher and journal from article if available
        publisher = 'Unknown Publisher'
        journal = 'Unknown Journal'
        
        if card.get('article_enriched'):
            publisher = card['article_enriched'].get('publisher', 'Unknown Publisher')
            journal = card['article_enriched'].get('journal_name', 'Unknown Journal')
        
        if publisher in ['', None, 'null', 'Unknown Publisher']:
            # Try to get from notice
            for notice_enriched in card.get('notice_enriched', []):
                pub = notice_enriched.get('publisher', '')
                if pub and pub not in ['', 'null', 'Unknown Publisher']:
                    publisher = pub
                    break
        
        if journal in ['', None, 'null', 'Unknown Journal']:
            for notice_enriched in card.get('notice_enriched', []):
                jour = notice_enriched.get('journal_name', '')
                if jour and jour not in ['', 'null', 'Unknown Journal']:
                    journal = jour
                    break
        
        hierarchy[publisher][journal].append(card)
    
    return hierarchy

def sort_hierarchy_by_notice_count(hierarchy: Dict) -> Dict:
    """
    Sort hierarchy levels by number of retraction notices (descending).
    """
    if not hierarchy:
        return hierarchy
    
    sorted_hierarchy = {}
    
    # Sort top-level keys by notice count
    top_level_items = []
    for key, value in hierarchy.items():
        if isinstance(value, dict):
            # Count notices in this group
            notice_count = 0
            for sub_key, cards in value.items():
                for card in cards:
                    if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                        notice_count += len(card.get('notice_data', []))
            top_level_items.append((key, value, notice_count))
        else:
            top_level_items.append((key, value, 0))
    
    top_level_items.sort(key=lambda x: x[2], reverse=True)
    
    for key, value, _ in top_level_items:
        if isinstance(value, dict):
            # Sort second-level items by notice count
            second_level_items = []
            for sub_key, cards in value.items():
                notice_count = 0
                for card in cards:
                    if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                        notice_count += len(card.get('notice_data', []))
                second_level_items.append((sub_key, cards, notice_count))
            second_level_items.sort(key=lambda x: x[2], reverse=True)
            
            sorted_hierarchy[key] = {
                sub_key: cards for sub_key, cards, _ in second_level_items
            }
        else:
            sorted_hierarchy[key] = value
    
    return sorted_hierarchy

def sort_author_groups_by_notice_count(author_groups: Dict[str, List[dict]]) -> Dict[str, List[dict]]:
    """
    Sort author groups by number of retraction notices (descending).
    """
    if not author_groups:
        return author_groups
    
    items = []
    for author_key, cards in author_groups.items():
        notice_count = 0
        for card in cards:
            if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                notice_count += len(card.get('notice_data', []))
        items.append((author_key, cards, notice_count))
    
    items.sort(key=lambda x: x[2], reverse=True)
    
    sorted_groups = {
        item[0]: item[1] for item in items
    }
    
    return sorted_groups

# ============================================================================
# PDF REPORT GENERATION FOR RETRACTION
# ============================================================================

def register_russian_font():
    """Register a font that supports Cyrillic characters."""
    import os
    
    font_found = False
    russian_font_name = 'Helvetica'
    
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
        '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf',
        '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/Arial.ttf',
        '/Library/Fonts/Arial.ttf',
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/times.ttf',
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('RussianFont', font_path))
                russian_font_name = 'RussianFont'
                font_found = True
                logger.info(f"Registered font from: {font_path}")
                break
            except Exception as e:
                logger.warning(f"Failed to register {font_path}: {e}")
                continue
    
    if not font_found:
        logger.warning("No Cyrillic font found, text may not display correctly")
        russian_font_name = 'Helvetica'
    
    return russian_font_name

def clean_text(text):
    """
    Clean text for PDF display, preserving allowed special characters including slash.
    """
    if text is None:
        return ""
    if not text:
        return ""
    if isinstance(text, bytes):
        text = text.decode('utf-8', 'ignore')
    import unicodedata
    text = unicodedata.normalize('NFC', str(text))
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Allow: letters (Latin and Cyrillic), spaces, dots, commas, hyphens, apostrophes, parentheses, digits, and slash
    allowed_pattern = r'[^a-zA-Zа-яА-ЯёЁ\s\.\,\-\'\(\)\d\/]'
    text = re.sub(allowed_pattern, '', text)
    return text

def clean_doi_url(url):
    if not url:
        return ""
    url = url.replace('&', '&amp;')
    url = url.replace('"', '&quot;')
    url = url.replace("'", '&apos;')
    url = url.replace('<', '&lt;')
    url = url.replace('>', '&gt;')
    return url

def add_logo_to_pdf(story, logo_path, max_width=150, max_height=150, add_spacer=True):
    """
    Add logo to PDF with preserved aspect ratio.
    Returns True if logo was successfully added, False otherwise.
    """
    if not logo_path or not os.path.exists(logo_path):
        return False
    
    try:
        from PIL import Image as PILImage
        pil_img = PILImage.open(logo_path)
        original_width, original_height = pil_img.size
        pil_img.close()
        
        # Calculate scale preserving aspect ratio
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        scale_ratio = min(width_ratio, height_ratio)
        
        new_width = original_width * scale_ratio
        new_height = original_height * scale_ratio
        
        logo = Image(logo_path, width=new_width, height=new_height)
        logo.hAlign = 'CENTER'
        story.append(logo)
        
        if add_spacer:
            story.append(Spacer(1, 0.5*cm))
        return True
    except Exception as e:
        logger.warning(f"Could not load logo: {e}")
        return False

def generate_retraction_pdf_by_country(journal_name: str, years: List[int],
                                       hierarchy: Dict, logo_path: str = None,
                                       report_title: str = "Retracted Articles by Country & Affiliation") -> bytes:
    """Generate PDF report grouping retracted articles by Country -> Affiliation."""
    russian_font_name = register_russian_font()
    
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontSize=22,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    country_style = ParagraphStyle(
        'CountryStyle',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=10,
        spaceBefore=20,
        fontName=russian_font_name
    )
    
    affiliation_style = ParagraphStyle(
        'AffiliationStyle',
        parent=styles['Normal'],
        fontSize=15,
        textColor=colors.HexColor('#764ba2'),
        spaceAfter=8,
        spaceBefore=12,
        leftIndent=20,
        fontName=russian_font_name
    )
    
    article_title_style = ParagraphStyle(
        'ArticleTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=5,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    authors_style = ParagraphStyle(
        'AuthorsStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=3,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    meta_style_default = ParagraphStyle(
        'MetaDefault',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    meta_style_notice = ParagraphStyle(
        'MetaNotice',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#e74c3c'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    citation_style = ParagraphStyle(
        'CitationStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#27AE60'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    toc_country_style = ParagraphStyle(
        'TOCCountryStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=6,
        fontName=russian_font_name
    )
    
    toc_affiliation_style = ParagraphStyle(
        'TOCAffiliationStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#764ba2'),
        spaceAfter=4,
        leftIndent=15,
        fontName=russian_font_name
    )
    
    intro_style = ParagraphStyle(
        'IntroStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=20,
        alignment=TA_JUSTIFY,
        fontName=russian_font_name
    )
    
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#95A5A6'),
        spaceBefore=15,
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    separator_style = ParagraphStyle(
        'Separator',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#BDC3C7'),
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    conclusion_style = ParagraphStyle(
        'ConclusionStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=20,
        alignment=TA_JUSTIFY,
        fontName=russian_font_name
    )
    
    story = []
    
    # Count total cards and notices
    total_cards = 0
    total_notices = 0
    for country, affiliations in hierarchy.items():
        for affiliation, cards in affiliations.items():
            total_cards += len(cards)
            for card in cards:
                if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                    total_notices += len(card.get('notice_data', []))
    
    story.append(Spacer(1, 2*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_cards} retracted articles/notices,
    grouped by Country and Affiliation.
    
    Total retraction notices found: {total_notices}
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Articles/Notices", str(total_cards)],
        ["Retraction Notices", str(total_notices)],
        ["Countries", str(len(hierarchy))],
        ["Report Type", report_title]
    ]
    
    stats_table = Table(stats_data, colWidths=[doc.width/2.5, doc.width/3])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), russian_font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5DBDB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F4F4')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(stats_table)
    story.append(PageBreak())
    
    # Table of Contents
    story.append(Paragraph("Table of Contents", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    for country, affiliations in hierarchy.items():
        country_notices = 0
        for affiliation, cards in affiliations.items():
            for card in cards:
                if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                    country_notices += len(card.get('notice_data', []))
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(country)}</b> — {country_notices} retraction notices</a>', toc_country_style))
        
        for affiliation, cards in affiliations.items():
            aff_notices = 0
            for card in cards:
                if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                    aff_notices += len(card.get('notice_data', []))
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{aff_anchor_id}">{clean_text(affiliation)}</a> — {aff_notices} retraction notices', toc_affiliation_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # Main content
    for country, affiliations in hierarchy.items():
        country_notices = 0
        for affiliation, cards in affiliations.items():
            for card in cards:
                if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                    country_notices += len(card.get('notice_data', []))
        
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(country)} — {country_notices} retraction notices", country_style))
        story.append(Spacer(1, 0.3*cm))
        
        for affiliation, cards in affiliations.items():
            aff_notices = 0
            for card in cards:
                if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                    aff_notices += len(card.get('notice_data', []))
            
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            aff_anchor_para = Paragraph(f'<a name="{aff_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(aff_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{clean_text(affiliation)} — {aff_notices} retraction notices", affiliation_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, card in enumerate(cards, 1):
                # Get enriched data
                article_enriched = card.get('article_enriched')
                notice_enriched_list = card.get('notice_enriched', [])
                
                # Title - from article if available, else from notice
                if article_enriched:
                    title = clean_text(article_enriched.get('title', 'No title'))
                else:
                    title = clean_text(notice_enriched_list[0].get('title', 'No title')) if notice_enriched_list else 'No title'
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {title}", article_title_style))
                
                # Authors - from article if available
                if article_enriched:
                    authors = clean_text(article_enriched.get('authors', 'Authors not specified'))
                else:
                    authors = clean_text(notice_enriched_list[0].get('authors', 'Authors not specified')) if notice_enriched_list else 'Authors not specified'
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors}", authors_style))
                
                # Affiliations
                if article_enriched:
                    affs = clean_text(article_enriched.get('affiliations_str', ''))
                else:
                    affs = clean_text(notice_enriched_list[0].get('affiliations_str', '')) if notice_enriched_list else ''
                
                if affs and affs != 'No affiliations specified':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style_default))
                
                # Publication info
                if article_enriched:
                    journal_name_article = clean_text(article_enriched.get('journal_name', ''))
                    year = article_enriched.get('publication_year', '')
                    pub_date = article_enriched.get('publication_date', '')
                    volume = article_enriched.get('volume', '')
                    issue = article_enriched.get('issue', '')
                    pages = article_enriched.get('pages', '')
                    publisher = clean_text(article_enriched.get('publisher', ''))
                else:
                    journal_name_article = clean_text(notice_enriched_list[0].get('journal_name', '')) if notice_enriched_list else ''
                    year = notice_enriched_list[0].get('publication_year', '') if notice_enriched_list else ''
                    pub_date = notice_enriched_list[0].get('publication_date', '') if notice_enriched_list else ''
                    volume = notice_enriched_list[0].get('volume', '') if notice_enriched_list else ''
                    issue = notice_enriched_list[0].get('issue', '') if notice_enriched_list else ''
                    pages = notice_enriched_list[0].get('pages', '') if notice_enriched_list else ''
                    publisher = clean_text(notice_enriched_list[0].get('publisher', '')) if notice_enriched_list else ''
                
                if journal_name_article:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Journal:</b> {journal_name_article}", meta_style_default))
                
                if publisher:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Publisher:</b> {publisher}", meta_style_default))
                
                meta_parts = []
                if year:
                    meta_parts.append(str(year))
                if pub_date and pub_date != '0000-00-00':
                    meta_parts.append(f"({pub_date})")
                if volume:
                    meta_parts.append(f"Vol. {volume}")
                if issue:
                    meta_parts.append(f"Iss. {issue}")
                if pages:
                    meta_parts.append(f"pp. {pages}")
                
                if meta_parts:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style_default))
                
                # DOI - from article if available
                if article_enriched:
                    doi_url = article_enriched.get('doi_url', '')
                    if doi_url:
                        doi_url_clean = clean_doi_url(doi_url)
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Retracted Article DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style_default))
                
                # Retraction notice DOIs
                for notice_enriched in notice_enriched_list:
                    notice_doi_url = notice_enriched.get('doi_url', '')
                    if notice_doi_url:
                        notice_doi_clean = clean_doi_url(notice_doi_url)
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>🔴 Retraction Notice DOI:</b> <a href='{notice_doi_clean}'>{notice_doi_clean}</a>", meta_style_notice))
                
                # Citations
                if article_enriched:
                    citations = article_enriched.get('cited_by_count', 0)
                    citations_per_year = article_enriched.get('citations_per_year', 0)
                else:
                    citations = notice_enriched_list[0].get('cited_by_count', 0) if notice_enriched_list else 0
                    citations_per_year = notice_enriched_list[0].get('citations_per_year', 0) if notice_enriched_list else 0
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f}", citation_style))
                
                # Type badge
                if article_enriched:
                    type_label = article_enriched.get('type_label', '')
                    type_icon = article_enriched.get('type_icon', '')
                    type_color = article_enriched.get('type_color', '')
                else:
                    type_label = notice_enriched_list[0].get('type_label', '') if notice_enriched_list else ''
                    type_icon = notice_enriched_list[0].get('type_icon', '') if notice_enriched_list else ''
                    type_color = notice_enriched_list[0].get('type_color', '') if notice_enriched_list else ''
                
                if type_label:
                    story.append(Paragraph(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='{type_color}'><b>{type_icon} {type_label}</b></font>",
                        meta_style_default
                    ))
                
                story.append(Spacer(1, 0.15*cm))
                
                if idx < len(cards):
                    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;" + "─" * 40, separator_style))
                    story.append(Spacer(1, 0.1*cm))
            
            story.append(Spacer(1, 0.3*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_cards} retracted articles/notices,
    grouped by {len(hierarchy)} countries and their respective affiliations.
    
    Total retraction notices found: {total_notices}
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Retraction Detector Pro | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retraction Article Detector Pro", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_retraction_pdf_by_author(journal_name: str, years: List[int],
                                     author_groups: Dict[str, List[dict]], 
                                     logo_path: str = None,
                                     report_title: str = "Retracted Articles by Author") -> bytes:
    """Generate PDF report grouping retracted articles by author."""
    russian_font_name = register_russian_font()
    
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontSize=22,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    author_style = ParagraphStyle(
        'AuthorStyle',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=10,
        spaceBefore=20,
        fontName=russian_font_name
    )
    
    article_title_style = ParagraphStyle(
        'ArticleTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=5,
        leftIndent=20,
        fontName=russian_font_name
    )
    
    authors_style = ParagraphStyle(
        'AuthorsStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=3,
        leftIndent=20,
        fontName=russian_font_name
    )
    
    meta_style_default = ParagraphStyle(
        'MetaDefault',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=2,
        leftIndent=20,
        fontName=russian_font_name
    )
    
    meta_style_notice = ParagraphStyle(
        'MetaNotice',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#e74c3c'),
        spaceAfter=2,
        leftIndent=20,
        fontName=russian_font_name
    )
    
    citation_style = ParagraphStyle(
        'CitationStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#27AE60'),
        spaceAfter=2,
        leftIndent=20,
        fontName=russian_font_name
    )
    
    intro_style = ParagraphStyle(
        'IntroStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=20,
        alignment=TA_JUSTIFY,
        fontName=russian_font_name
    )
    
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#95A5A6'),
        spaceBefore=15,
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    separator_style = ParagraphStyle(
        'Separator',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#BDC3C7'),
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    conclusion_style = ParagraphStyle(
        'ConclusionStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=20,
        alignment=TA_JUSTIFY,
        fontName=russian_font_name
    )
    
    story = []
    
    total_cards = 0
    total_notices = 0
    for author_key, cards in author_groups.items():
        total_cards += len(cards)
        for card in cards:
            if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                total_notices += len(card.get('notice_data', []))
    
    story.append(Spacer(1, 2*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_cards} retracted articles/notices,
    grouped by author (last name, first initial).
    
    Total retraction notices found: {total_notices}
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Articles/Notices", str(total_cards)],
        ["Retraction Notices", str(total_notices)],
        ["Unique Authors", str(len(author_groups))],
        ["Report Type", report_title]
    ]
    
    stats_table = Table(stats_data, colWidths=[doc.width/2.5, doc.width/3])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), russian_font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5DBDB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F4F4')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(stats_table)
    story.append(PageBreak())
    
    # Main content
    for author_key, cards in author_groups.items():
        author_notices = 0
        for card in cards:
            if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                author_notices += len(card.get('notice_data', []))
        
        story.append(Paragraph(f"{clean_text(author_key)} — {author_notices} retraction notices", author_style))
        story.append(Spacer(1, 0.3*cm))
        
        for idx, card in enumerate(cards, 1):
            article_enriched = card.get('article_enriched')
            notice_enriched_list = card.get('notice_enriched', [])
            
            if article_enriched:
                title = clean_text(article_enriched.get('title', 'No title'))
            else:
                title = clean_text(notice_enriched_list[0].get('title', 'No title')) if notice_enriched_list else 'No title'
            
            story.append(Paragraph(f"{idx}. {title}", article_title_style))
            
            if article_enriched:
                authors = clean_text(article_enriched.get('authors', 'Authors not specified'))
            else:
                authors = clean_text(notice_enriched_list[0].get('authors', 'Authors not specified')) if notice_enriched_list else 'Authors not specified'
            
            story.append(Paragraph(f"<b>Authors:</b> {authors}", authors_style))
            
            if article_enriched:
                journal_name_article = clean_text(article_enriched.get('journal_name', ''))
                year = article_enriched.get('publication_year', '')
                pub_date = article_enriched.get('publication_date', '')
                volume = article_enriched.get('volume', '')
                issue = article_enriched.get('issue', '')
                pages = article_enriched.get('pages', '')
            else:
                journal_name_article = clean_text(notice_enriched_list[0].get('journal_name', '')) if notice_enriched_list else ''
                year = notice_enriched_list[0].get('publication_year', '') if notice_enriched_list else ''
                pub_date = notice_enriched_list[0].get('publication_date', '') if notice_enriched_list else ''
                volume = notice_enriched_list[0].get('volume', '') if notice_enriched_list else ''
                issue = notice_enriched_list[0].get('issue', '') if notice_enriched_list else ''
                pages = notice_enriched_list[0].get('pages', '') if notice_enriched_list else ''
            
            if journal_name_article:
                story.append(Paragraph(f"<b>Journal:</b> {journal_name_article}", meta_style_default))
            
            meta_parts = []
            if year:
                meta_parts.append(str(year))
            if pub_date and pub_date != '0000-00-00':
                meta_parts.append(f"({pub_date})")
            if volume:
                meta_parts.append(f"Vol. {volume}")
            if issue:
                meta_parts.append(f"Iss. {issue}")
            if pages:
                meta_parts.append(f"pp. {pages}")
            
            if meta_parts:
                story.append(Paragraph(f"{', '.join(meta_parts)}", meta_style_default))
            
            if article_enriched:
                doi_url = article_enriched.get('doi_url', '')
                if doi_url:
                    doi_url_clean = clean_doi_url(doi_url)
                    story.append(Paragraph(f"<b>Retracted Article DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style_default))
            
            for notice_enriched in notice_enriched_list:
                notice_doi_url = notice_enriched.get('doi_url', '')
                if notice_doi_url:
                    notice_doi_clean = clean_doi_url(notice_doi_url)
                    story.append(Paragraph(f"<b>🔴 Retraction Notice DOI:</b> <a href='{notice_doi_clean}'>{notice_doi_clean}</a>", meta_style_notice))
            
            if article_enriched:
                citations = article_enriched.get('cited_by_count', 0)
                citations_per_year = article_enriched.get('citations_per_year', 0)
            else:
                citations = notice_enriched_list[0].get('cited_by_count', 0) if notice_enriched_list else 0
                citations_per_year = notice_enriched_list[0].get('citations_per_year', 0) if notice_enriched_list else 0
            
            story.append(Paragraph(f"<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f}", citation_style))
            
            story.append(Spacer(1, 0.15*cm))
            
            if idx < len(cards):
                story.append(Paragraph("─" * 60, separator_style))
                story.append(Spacer(1, 0.1*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_cards} retracted articles/notices,
    grouped by {len(author_groups)} unique authors.
    
    Total retraction notices found: {total_notices}
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Retraction Detector Pro | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retraction Article Detector Pro", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_retraction_pdf_by_publisher(journal_name: str, years: List[int],
                                        hierarchy: Dict, logo_path: str = None,
                                        report_title: str = "Retracted Articles by Publisher & Journal") -> bytes:
    """Generate PDF report grouping retracted articles by Publisher -> Journal."""
    russian_font_name = register_russian_font()
    
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontSize=22,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    publisher_style = ParagraphStyle(
        'PublisherStyle',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=10,
        spaceBefore=20,
        fontName=russian_font_name
    )
    
    journal_style = ParagraphStyle(
        'JournalStyle',
        parent=styles['Normal'],
        fontSize=15,
        textColor=colors.HexColor('#764ba2'),
        spaceAfter=8,
        spaceBefore=12,
        leftIndent=20,
        fontName=russian_font_name
    )
    
    article_title_style = ParagraphStyle(
        'ArticleTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=5,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    authors_style = ParagraphStyle(
        'AuthorsStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=3,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    meta_style_default = ParagraphStyle(
        'MetaDefault',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    meta_style_notice = ParagraphStyle(
        'MetaNotice',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#e74c3c'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    citation_style = ParagraphStyle(
        'CitationStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#27AE60'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    toc_publisher_style = ParagraphStyle(
        'TOCPublisherStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=6,
        fontName=russian_font_name
    )
    
    toc_journal_style = ParagraphStyle(
        'TOCJournalStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#764ba2'),
        spaceAfter=4,
        leftIndent=15,
        fontName=russian_font_name
    )
    
    intro_style = ParagraphStyle(
        'IntroStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=20,
        alignment=TA_JUSTIFY,
        fontName=russian_font_name
    )
    
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#95A5A6'),
        spaceBefore=15,
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    separator_style = ParagraphStyle(
        'Separator',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#BDC3C7'),
        alignment=TA_CENTER,
        fontName=russian_font_name
    )
    
    conclusion_style = ParagraphStyle(
        'ConclusionStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=20,
        alignment=TA_JUSTIFY,
        fontName=russian_font_name
    )
    
    story = []
    
    total_cards = 0
    total_notices = 0
    for publisher, journals in hierarchy.items():
        for journal, cards in journals.items():
            total_cards += len(cards)
            for card in cards:
                if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                    total_notices += len(card.get('notice_data', []))
    
    story.append(Spacer(1, 2*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_cards} retracted articles/notices,
    grouped by Publisher and Journal.
    
    Total retraction notices found: {total_notices}
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Articles/Notices", str(total_cards)],
        ["Retraction Notices", str(total_notices)],
        ["Publishers", str(len(hierarchy))],
        ["Report Type", report_title]
    ]
    
    stats_table = Table(stats_data, colWidths=[doc.width/2.5, doc.width/3])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), russian_font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5DBDB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F4F4')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(stats_table)
    story.append(PageBreak())
    
    # Table of Contents
    story.append(Paragraph("Table of Contents", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    for publisher, journals in hierarchy.items():
        publisher_notices = 0
        for journal, cards in journals.items():
            for card in cards:
                if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                    publisher_notices += len(card.get('notice_data', []))
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(publisher)}</b> — {publisher_notices} retraction notices</a>', toc_publisher_style))
        
        for journal, cards in journals.items():
            journal_notices = 0
            for card in cards:
                if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                    journal_notices += len(card.get('notice_data', []))
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{journal_anchor_id}">{clean_text(journal)}</a> — {journal_notices} retraction notices', toc_journal_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # Main content
    for publisher, journals in hierarchy.items():
        publisher_notices = 0
        for journal, cards in journals.items():
            for card in cards:
                if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                    publisher_notices += len(card.get('notice_data', []))
        
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(publisher)} — {publisher_notices} retraction notices", publisher_style))
        story.append(Spacer(1, 0.3*cm))
        
        for journal, cards in journals.items():
            journal_notices = 0
            for card in cards:
                if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
                    journal_notices += len(card.get('notice_data', []))
            
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            journal_anchor_para = Paragraph(f'<a name="{journal_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(journal_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{clean_text(journal)} — {journal_notices} retraction notices", journal_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, card in enumerate(cards, 1):
                article_enriched = card.get('article_enriched')
                notice_enriched_list = card.get('notice_enriched', [])
                
                if article_enriched:
                    title = clean_text(article_enriched.get('title', 'No title'))
                else:
                    title = clean_text(notice_enriched_list[0].get('title', 'No title')) if notice_enriched_list else 'No title'
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {title}", article_title_style))
                
                if article_enriched:
                    authors = clean_text(article_enriched.get('authors', 'Authors not specified'))
                else:
                    authors = clean_text(notice_enriched_list[0].get('authors', 'Authors not specified')) if notice_enriched_list else 'Authors not specified'
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors}", authors_style))
                
                if article_enriched:
                    journal_name_article = clean_text(article_enriched.get('journal_name', ''))
                    year = article_enriched.get('publication_year', '')
                    pub_date = article_enriched.get('publication_date', '')
                    volume = article_enriched.get('volume', '')
                    issue = article_enriched.get('issue', '')
                    pages = article_enriched.get('pages', '')
                else:
                    journal_name_article = clean_text(notice_enriched_list[0].get('journal_name', '')) if notice_enriched_list else ''
                    year = notice_enriched_list[0].get('publication_year', '') if notice_enriched_list else ''
                    pub_date = notice_enriched_list[0].get('publication_date', '') if notice_enriched_list else ''
                    volume = notice_enriched_list[0].get('volume', '') if notice_enriched_list else ''
                    issue = notice_enriched_list[0].get('issue', '') if notice_enriched_list else ''
                    pages = notice_enriched_list[0].get('pages', '') if notice_enriched_list else ''
                
                meta_parts = []
                if year:
                    meta_parts.append(str(year))
                if pub_date and pub_date != '0000-00-00':
                    meta_parts.append(f"({pub_date})")
                if volume:
                    meta_parts.append(f"Vol. {volume}")
                if issue:
                    meta_parts.append(f"Iss. {issue}")
                if pages:
                    meta_parts.append(f"pp. {pages}")
                
                if meta_parts:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style_default))
                
                if article_enriched:
                    doi_url = article_enriched.get('doi_url', '')
                    if doi_url:
                        doi_url_clean = clean_doi_url(doi_url)
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Retracted Article DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style_default))
                
                for notice_enriched in notice_enriched_list:
                    notice_doi_url = notice_enriched.get('doi_url', '')
                    if notice_doi_url:
                        notice_doi_clean = clean_doi_url(notice_doi_url)
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>🔴 Retraction Notice DOI:</b> <a href='{notice_doi_clean}'>{notice_doi_clean}</a>", meta_style_notice))
                
                if article_enriched:
                    citations = article_enriched.get('cited_by_count', 0)
                    citations_per_year = article_enriched.get('citations_per_year', 0)
                else:
                    citations = notice_enriched_list[0].get('cited_by_count', 0) if notice_enriched_list else 0
                    citations_per_year = notice_enriched_list[0].get('citations_per_year', 0) if notice_enriched_list else 0
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f}", citation_style))
                
                story.append(Spacer(1, 0.15*cm))
                
                if idx < len(cards):
                    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;" + "─" * 40, separator_style))
                    story.append(Spacer(1, 0.1*cm))
            
            story.append(Spacer(1, 0.3*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_cards} retracted articles/notices,
    grouped by {len(hierarchy)} publishers and their respective journals.
    
    Total retraction notices found: {total_notices}
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Retraction Detector Pro | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retraction Article Detector Pro", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_journal_abbreviation(journal_name: str) -> str:
    if not journal_name:
        return "JOURNAL"
    
    stop_words = {'of', 'the', 'and', 'for', 'in', 'on', 'at', 'to', 'by', 'with', 'from'}
    words = re.findall(r'[A-Za-z]+', journal_name)
    
    abbreviation_parts = []
    for word in words:
        word_lower = word.lower()
        if word_lower not in stop_words and len(word) > 2:
            abbreviation_parts.append(word[0].upper())
        elif len(abbreviation_parts) == 0 and len(words) <= 3:
            abbreviation_parts.append(word[0].upper())
    
    if len(abbreviation_parts) < 3 and len(words) > 0:
        for word in words:
            if word.lower() not in stop_words:
                abbreviation_parts = [word[:4].upper()]
                break
    
    abbreviation = ''.join(abbreviation_parts)
    
    if not abbreviation and words:
        abbreviation = words[0][:4].upper()
    
    return abbreviation if abbreviation else "JOURNAL"

# ============================================================================
# UI STEPS FOR RETRACTION DETECTION
# ============================================================================

def step_parameters():
    """Step 1: Enter parameters (years and countries)"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📥 Step 1: Set Analysis Parameters</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Enter publication years and countries to analyze retracted articles.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="filter-section" style="background: rgba(255, 255, 255, 0.9); border-radius: 20px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(102, 126, 234, 0.2);">
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.9rem; color: #666; margin-bottom: 10px;">
        <strong>Supported year formats:</strong>
    </div>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px;">
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">2000</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">2010</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">2010-2020</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">2020</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">2023-2026</span>
        <span style="background: #fff3e0; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; border: 1px dashed #ff9800;">2005,2010-2015,2020</span>
        <span style="background: #fff3e0; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; border: 1px dashed #ff9800;">2015,2018-2020,2022-2024</span>
    </div>
    """, unsafe_allow_html=True)
    
    years_input = st.text_input(
        "Enter publication years",
        value=st.session_state.get('years_input', ''),
        placeholder="Example: 2000 or 2010 or 2010-2020 or 2020 or 2023-2026 or 2015,2018-2020,2022",
        help="Enter years in any format: single year (2020), range (2010-2020), or combination (2015,2018-2020,2022)"
    )
    
    if years_input:
        years = parse_year_filter(years_input)
        if years:
            years_str = format_year_filter_for_filename(years)
            st.markdown(f"""
            <div style="background: #e8f5e9; border-radius: 8px; padding: 12px; border-left: 4px solid #4CAF50; margin: 10px 0;">
                <strong>✅ Selected years:</strong> {', '.join(map(str, years))}
                <br><span style="font-size: 0.85rem; color: #666;">Total: {len(years)} years</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #ffebee; border-radius: 8px; padding: 12px; border-left: 4px solid #f44336; margin: 10px 0;">
                <strong>❌ Invalid format:</strong> Please check your input.
                <br><span style="font-size: 0.85rem; color: #666;">Example: 2000, 2010-2020, 2015,2018-2020,2022</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.9rem; color: #666; margin: 15px 0 10px 0;">
        <strong>Country codes (separate with +):</strong>
    </div>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px;">
        <span style="background: #e8f5e9; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">RU</span>
        <span style="background: #e8f5e9; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">US</span>
        <span style="background: #e8f5e9; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">IT</span>
        <span style="background: #e8f5e9; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">CN</span>
        <span style="background: #e8f5e9; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">GB</span>
        <span style="background: #e8f5e9; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">DE</span>
        <span style="background: #fff3e0; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; border: 1px dashed #ff9800;">IT+RU+CN</span>
    </div>
    """, unsafe_allow_html=True)
    
    countries_input = st.text_input(
        "Enter countries (ISO codes, separate with +)",
        value=st.session_state.get('countries_input', ''),
        placeholder="Example: RU or IT+RU or IT+RU+CN",
        help="Enter country codes separated by '+'. Example: IT+RU+CN"
    )
    
    if countries_input:
        countries = [c.strip().upper() for c in countries_input.split('+') if c.strip()]
        if countries:
            country_names = []
            for code in countries:
                full_name = COUNTRY_CODE_MAP.get(code, code)
                country_names.append(f"{code} ({full_name})")
            st.markdown(f"""
            <div style="background: #e8f5e9; border-radius: 8px; padding: 12px; border-left: 4px solid #4CAF50; margin: 10px 0;">
                <strong>✅ Selected countries:</strong> {', '.join(country_names)}
                <br><span style="font-size: 0.85rem; color: #666;">Total: {len(countries)} countries</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 Find Retracted Articles", type="primary", use_container_width=True):
            if not years_input:
                st.error("❌ Please enter at least one year.")
                return
            
            years = parse_year_filter(years_input)
            if not years:
                st.error("❌ Invalid year format. Please check your input.")
                return
            
            # Parse countries
            countries = []
            if countries_input:
                countries = [c.strip().upper() for c in countries_input.split('+') if c.strip()]
            
            # Store in session state
            st.session_state.years_input = years_input
            st.session_state.selected_years = years
            st.session_state.countries_input = countries_input
            st.session_state.selected_countries = countries
            st.session_state.current_step = 2
            st.rerun()

def step_search():
    """Step 2: Search for retracted articles and notices"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 2: Searching for Retracted Articles</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Fetching data from OpenAlex...</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'selected_years' not in st.session_state:
        st.error("❌ No parameters set. Please go back to Step 1.")
        return
    
    # Back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    
    years = st.session_state.selected_years
    countries = st.session_state.get('selected_countries', [])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(years)}</div>
            <div class="metric-label">Years</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(countries) if countries else 'All'}</div>
            <div class="metric-label">Countries</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">...</div>
            <div class="metric-label">Notices</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">...</div>
            <div class="metric-label">Articles</div>
        </div>
        """, unsafe_allow_html=True)
    
    with st.spinner("Searching for retraction notices..."):
        notices = search_retraction_notices_sync(years, countries)
    
    with st.spinner("Searching for retracted articles..."):
        articles = search_retracted_articles_sync(years, countries)
    
    st.markdown(f"""
    <div class="info-message" style="background: linear-gradient(135deg, #2196F315 0%, #0D47A115 100%); border-radius: 8px; padding: 12px; border-left: 3px solid #2196F3; font-size: 0.9rem; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>✅ Search Complete!</strong><br>
                Found {len(notices)} retraction notices and {len(articles)} retracted articles
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state.retraction_notices = notices
    st.session_state.retracted_articles = articles
    
    # Merge into cards
    with st.spinner("Merging retraction pairs..."):
        merged_cards = merge_retraction_pairs(notices, articles)
    
    st.session_state.merged_cards = merged_cards
    
    # Statistics after merging
    merged_count = sum(1 for card in merged_cards if card.get('is_merged', False))
    notice_only = sum(1 for card in merged_cards if card.get('article_data') is None)
    article_only = sum(1 for card in merged_cards if card.get('notice_data') == [] or len(card.get('notice_data', [])) == 0)
    
    total_notices = 0
    for card in merged_cards:
        if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
            total_notices += len(card.get('notice_data', []))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(merged_cards)}</div>
            <div class="metric-label">Total Cards</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{merged_count}</div>
            <div class="metric-label">Merged Pairs</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{notice_only}</div>
            <div class="metric-label">Notice Only</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{article_only}</div>
            <div class="metric-label">Article Only</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📊 Generate Reports", type="primary", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()

def step_reports():
    """Step 3: Generate and download reports"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📊 Step 3: Retraction Reports</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Download reports for retracted articles.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'merged_cards' not in st.session_state:
        st.error("❌ No data available. Please go back to Step 2.")
        return
    
    # Back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    
    cards = st.session_state.merged_cards
    years = st.session_state.selected_years
    journal_name = "Retracted Articles Analysis"
    journal_abbr = "RETRACT"
    logo_path = None
    
    possible_paths = [
        "logo.png",
        "./logo.png",
        "app/logo.png",
        os.path.join(os.path.dirname(__file__), "logo.png"),
        os.path.join(os.getcwd(), "logo.png")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            logo_path = path
            break
    
    if 'pdf_cache' not in st.session_state:
        st.session_state.pdf_cache = {}
    if 'all_reports_generated' not in st.session_state:
        st.session_state.all_reports_generated = False
    
    # Generate groupings
    with st.spinner("Generating report groupings..."):
        country_hierarchy = group_cards_by_country_affiliation(cards)
        country_hierarchy = sort_hierarchy_by_notice_count(country_hierarchy)
        
        author_groups = group_cards_by_author(cards)
        author_groups = sort_author_groups_by_notice_count(author_groups)
        
        publisher_hierarchy = group_cards_by_publisher_journal(cards)
        publisher_hierarchy = sort_hierarchy_by_notice_count(publisher_hierarchy)
    
    # Statistics
    total_cards = len(cards)
    total_notices = 0
    for card in cards:
        if card.get('notice_data') and len(card.get('notice_data', [])) > 0:
            total_notices += len(card.get('notice_data', []))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_cards}</div>
            <div class="metric-label">Total Cards</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_notices}</div>
            <div class="metric-label">Retraction Notices</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(country_hierarchy)}</div>
            <div class="metric-label">Countries</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(publisher_hierarchy)}</div>
            <div class="metric-label">Publishers</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📥 Download Reports")
    
    # Create unique cache keys
    cards_hash = hashlib.md5(str([str(id(card)) for card in cards]).encode()).hexdigest()[:8]
    years_hash = hashlib.md5(','.join(map(str, years)).encode()).hexdigest()[:8]
    
    cache_key_country = f"country_{years_hash}_{cards_hash}"
    cache_key_author = f"author_{years_hash}_{cards_hash}"
    cache_key_publisher = f"publisher_{years_hash}_{cards_hash}"
    
    col_gen1, col_gen2, col_gen3 = st.columns([1, 1, 1])
    with col_gen2:
        if not st.session_state.all_reports_generated:
            if st.button("⚡ Generate All Reports", type="primary", use_container_width=True):
                with st.spinner("Generating all reports..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("Generating Country → Affiliation report...")
                    if cache_key_country not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_country] = generate_retraction_pdf_by_country(
                            journal_name, years,
                            country_hierarchy, logo_path,
                            "Retracted Articles by Country & Affiliation"
                        )
                    progress_bar.progress(0.33)
                    
                    status_text.text("Generating Author report...")
                    if cache_key_author not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_author] = generate_retraction_pdf_by_author(
                            journal_name, years,
                            author_groups, logo_path,
                            "Retracted Articles by Author"
                        )
                    progress_bar.progress(0.66)
                    
                    status_text.text("Generating Publisher → Journal report...")
                    if cache_key_publisher not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_publisher] = generate_retraction_pdf_by_publisher(
                            journal_name, years,
                            publisher_hierarchy, logo_path,
                            "Retracted Articles by Publisher & Journal"
                        )
                    progress_bar.progress(1.0)
                    
                    status_text.text("✅ All reports generated!")
                    st.session_state.all_reports_generated = True
                    time.sleep(0.5)
                    st.rerun()
        else:
            st.success("✅ All reports already generated! Use the buttons below to download.")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🌍 Report 1: Country → Affiliation**")
        st.markdown("*Sorted by retraction notice count*")
        
        if cache_key_country in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_country]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"{journal_abbr}_{format_year_filter_for_filename(years)}_country_affiliation.pdf"
            st.download_button(
                label="📄 Download Country Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_country_download_{cache_key_country}"
            )
        else:
            if st.button("📄 Generate Country Report", key=f"gen_country_{cache_key_country}", use_container_width=True):
                with st.spinner("Generating Country Report..."):
                    pdf_data = generate_retraction_pdf_by_country(
                        journal_name, years,
                        country_hierarchy, logo_path,
                        "Retracted Articles by Country & Affiliation"
                    )
                    st.session_state.pdf_cache[cache_key_country] = pdf_data
                    st.rerun()
    
    with col2:
        st.markdown("**👤 Report 2: Author**")
        st.markdown("*Sorted by retraction notice count*")
        
        if cache_key_author in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_author]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"{journal_abbr}_{format_year_filter_for_filename(years)}_author.pdf"
            st.download_button(
                label="📄 Download Author Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_author_download_{cache_key_author}"
            )
        else:
            if st.button("📄 Generate Author Report", key=f"gen_author_{cache_key_author}", use_container_width=True):
                with st.spinner("Generating Author Report..."):
                    pdf_data = generate_retraction_pdf_by_author(
                        journal_name, years,
                        author_groups, logo_path,
                        "Retracted Articles by Author"
                    )
                    st.session_state.pdf_cache[cache_key_author] = pdf_data
                    st.rerun()
    
    with col3:
        st.markdown("**📚 Report 3: Publisher → Journal**")
        st.markdown("*Sorted by retraction notice count*")
        
        if cache_key_publisher in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_publisher]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"{journal_abbr}_{format_year_filter_for_filename(years)}_publisher_journal.pdf"
            st.download_button(
                label="📄 Download Publisher Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_publisher_download_{cache_key_publisher}"
            )
        else:
            if st.button("📄 Generate Publisher Report", key=f"gen_publisher_{cache_key_publisher}", use_container_width=True):
                with st.spinner("Generating Publisher Report..."):
                    pdf_data = generate_retraction_pdf_by_publisher(
                        journal_name, years,
                        publisher_hierarchy, logo_path,
                        "Retracted Articles by Publisher & Journal"
                    )
                    st.session_state.pdf_cache[cache_key_publisher] = pdf_data
                    st.rerun()
    
    st.markdown("---")
    
    if st.session_state.all_reports_generated:
        if all(key in st.session_state.pdf_cache for key in [cache_key_country, cache_key_author, cache_key_publisher]):
            try:
                import zipfile
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.writestr(f"{journal_abbr}_{format_year_filter_for_filename(years)}_country_affiliation.pdf", 
                                     st.session_state.pdf_cache[cache_key_country])
                    zip_file.writestr(f"{journal_abbr}_{format_year_filter_for_filename(years)}_author.pdf", 
                                     st.session_state.pdf_cache[cache_key_author])
                    zip_file.writestr(f"{journal_abbr}_{format_year_filter_for_filename(years)}_publisher_journal.pdf", 
                                     st.session_state.pdf_cache[cache_key_publisher])
                
                zip_data = zip_buffer.getvalue()
                
                col_zip1, col_zip2, col_zip3 = st.columns([1, 2, 1])
                with col_zip2:
                    st.download_button(
                        label="📦 Download All Reports (ZIP archive)",
                        data=zip_data,
                        file_name=f"{journal_abbr}_{format_year_filter_for_filename(years)}_all_reports.zip",
                        mime="application/zip",
                        use_container_width=True,
                        key="download_all_zip"
                    )
            except Exception as e:
                st.error(f"Error creating ZIP archive: {e}")
    
    st.markdown("---")
    
    if st.button("🔄 New Analysis", use_container_width=True):
        keys_to_clear = ['current_step', 'years_input', 'selected_years', 'countries_input',
                        'selected_countries', 'retraction_notices', 'retracted_articles',
                        'merged_cards', 'pdf_cache', 'all_reports_generated']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.current_step = 1
        st.rerun()

# ============================================================================
# STOPWORDS
# ============================================================================

import nltk
nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords

COMMON_WORDS = {
    'study', 'studies', 'research', 'paper', 'article', 'review', 'analysis', 'analyses',
    'investigation', 'investigations', 'effect', 'effects', 'property', 'properties',
    'performance', 'behavior', 'behaviour', 'characterization', 'characterisation',
    'synthesis', 'development', 'preparation', 'fabrication', 'application', 'applications',
    'method', 'methods', 'approach', 'approaches', 'result', 'results', 'discussion',
    'conclusion', 'conclusions', 'introduction', 'experimental', 'experiment', 'experiments',
    'measurement', 'measurements', 'observation', 'observations', 'technique', 'techniques',
    'technology', 'technologies', 'material', 'materials', 'system', 'systems',
    'process', 'processes', 'structure', 'structures', 'model', 'models',
    'based', 'using', 'used', 'use', 'high', 'low', 'temperature', 'temperatures',
    'pressure', 'different', 'various', 'several', 'important', 'significant',
    'novel', 'new', 'recent', 'current', 'potential', 'possible', 'first',
    'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth',
    'tenth', 'good', 'better', 'best', 'poor', 'higher', 'lower', 'strong',
    'weak', 'large', 'small', 'great', 'major', 'minor', 'main', 'primary',
    'secondary', 'critical', 'essential', 'general', 'specific', 'special',
    'particular', 'similar', 'different', 'various', 'several', 'multiple',
    'numerous', 'common', 'unusual', 'typical', 'atypical', 'standard',
    'advanced', 'basic', 'fundamental', 'theoretical', 'practical', 'experimental',
    'computational', 'numerical', 'analytical', 'theoretical', 'practical'
}

ALL_STOPWORDS = set(stopwords.words('english')).union(COMMON_WORDS)

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main application function"""
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    # Header
    import base64
    
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        
        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; padding: 20px 0; margin-bottom: 10px;">
            <img src="data:image/png;base64,{img_data}" 
                 style="width: 33%; max-width: 400px; height: auto; object-fit: contain;">
        </div>
        """, unsafe_allow_html=True)
    
    # Progress bar
    steps = ["Parameters", "Search", "Reports"]
    current_step = st.session_state.current_step
    progress = (current_step - 1) / 2
    
    st.markdown(f"""
    <div class="progress-container" style="background: #f5f5f5; border-radius: 8px; height: 6px; margin: 20px 0; overflow: hidden;">
        <div class="progress-bar" style="height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 8px; transition: width 0.5s ease; width: {progress * 100}%;"></div>
    </div>
    <div class="step-indicator" style="display: flex; justify-content: space-between; margin: 15px 0; font-size: 0.85rem; color: #666;">
        <span class="{'active' if current_step >= 1 else ''}" style="color: {'#667eea' if current_step >= 1 else '#666'}; font-weight: {'600' if current_step >= 1 else '400'};">📥 Parameters</span>
        <span class="{'active' if current_step >= 2 else ''}" style="color: {'#667eea' if current_step >= 2 else '#666'}; font-weight: {'600' if current_step >= 2 else '400'};">🔍 Search</span>
        <span class="{'active' if current_step >= 3 else ''}" style="color: {'#667eea' if current_step >= 3 else '#666'}; font-weight: {'600' if current_step >= 3 else '400'};">📊 Reports</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Display current step
    if st.session_state.current_step == 1:
        step_parameters()
    elif st.session_state.current_step == 2:
        step_search()
    elif st.session_state.current_step == 3:
        step_reports()
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>© Retraction Detector Pro | https://chimicatechnoacta.ru</p>
        <p style="font-size: 0.7rem; color: #aaa;">Retraction Article Detector Pro with multi-report generation</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
