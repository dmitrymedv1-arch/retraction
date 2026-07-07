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
    page_title="Retraction Article Detector Pro*2",
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
CACHE_DB = CACHE_DIR / "openalex_cache.db"
CACHE_EXPIRY_DAYS = 30

CACHE_DIR.mkdir(exist_ok=True)

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
        CREATE TABLE IF NOT EXISTS topic_works_cache (
            topic_id TEXT,
            cursor_key TEXT,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            PRIMARY KEY (topic_id, cursor_key)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics_cache (
            topic_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_works_expires ON works_cache(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_topic_works_expires ON topic_works_cache(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_topics_expires ON topics_cache(expires_at)')
    
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

def cache_topic_works(topic_id: str, cursor_key: str, data: dict):
    conn = get_cache_connection()
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(days=7)
    cursor.execute('''
        INSERT OR REPLACE INTO topic_works_cache (topic_id, cursor_key, data, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (topic_id, cursor_key, json.dumps(data), expires_at))
    conn.commit()
    conn.close()

def get_cached_topic_works(topic_id: str, cursor_key: str) -> Optional[dict]:
    conn = get_cache_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT data FROM topic_works_cache 
        WHERE topic_id = ? AND cursor_key = ? 
        AND (expires_at IS NULL OR expires_at > ?)
    ''', (topic_id, cursor_key, datetime.now()))
    result = cursor.fetchone()
    conn.close()
    if result:
        return json.loads(result[0])
    return None

def cache_topic_stats(topic_id: str, data: dict):
    conn = get_cache_connection()
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(days=30)
    cursor.execute('''
        INSERT OR REPLACE INTO topics_cache (topic_id, data, expires_at)
        VALUES (?, ?, ?)
    ''', (topic_id, json.dumps(data), expires_at))
    conn.commit()
    conn.close()

def get_cached_topic_stats(topic_id: str) -> Optional[dict]:
    conn = get_cache_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT data FROM topics_cache 
        WHERE topic_id = ? AND (expires_at IS NULL OR expires_at > ?)
    ''', (topic_id, datetime.now()))
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
    cursor.execute('DELETE FROM topic_works_cache WHERE expires_at IS NOT NULL AND expires_at <= ?', (now,))
    cursor.execute('DELETE FROM topics_cache WHERE expires_at IS NOT NULL AND expires_at <= ?', (now,))
    changes = cursor.rowcount
    if changes > 0:
        conn.commit()
        logger.info(f"Cleared {changes} expired cache entries")
    conn.close()

# ============================================================================
# YEAR PARSING FUNCTIONS
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
# COUNTRY PARSING FUNCTIONS
# ============================================================================

def parse_country_filter(country_input: str) -> List[str]:
    """
    Parse country filter string.
    Examples:
    "RU" -> ["RU"]
    "IT+RU" -> ["IT", "RU"]
    "IT+RU+CN" -> ["IT", "RU", "CN"]
    "US" -> ["US"]
    """
    if not country_input or country_input.strip() == "":
        return []
    
    # Split by + or comma
    countries = re.split(r'[+,]', country_input)
    countries = [c.strip().upper() for c in countries if c.strip()]
    
    # Filter to valid country codes (2-letter codes)
    valid_countries = [c for c in countries if len(c) == 2 and c.isalpha()]
    
    return valid_countries

def get_country_name(country_code: str) -> str:
    """
    Get full country name from country code.
    """
    country_names = {
        'AF': 'Afghanistan', 'AL': 'Albania', 'DZ': 'Algeria', 'AD': 'Andorra',
        'AO': 'Angola', 'AG': 'Antigua and Barbuda', 'AR': 'Argentina', 'AM': 'Armenia',
        'AU': 'Australia', 'AT': 'Austria', 'AZ': 'Azerbaijan', 'BS': 'Bahamas',
        'BH': 'Bahrain', 'BD': 'Bangladesh', 'BB': 'Barbados', 'BY': 'Belarus',
        'BE': 'Belgium', 'BZ': 'Belize', 'BJ': 'Benin', 'BT': 'Bhutan',
        'BO': 'Bolivia', 'BA': 'Bosnia and Herzegovina', 'BW': 'Botswana',
        'BR': 'Brazil', 'BN': 'Brunei', 'BG': 'Bulgaria', 'BF': 'Burkina Faso',
        'BI': 'Burundi', 'KH': 'Cambodia', 'CM': 'Cameroon', 'CA': 'Canada',
        'CV': 'Cape Verde', 'CF': 'Central African Republic', 'TD': 'Chad',
        'CL': 'Chile', 'CN': 'China', 'CO': 'Colombia', 'KM': 'Comoros',
        'CG': 'Congo', 'CD': 'DR Congo', 'CR': 'Costa Rica', 'HR': 'Croatia',
        'CU': 'Cuba', 'CY': 'Cyprus', 'CZ': 'Czech Republic', 'DK': 'Denmark',
        'DJ': 'Djibouti', 'DM': 'Dominica', 'DO': 'Dominican Republic',
        'EC': 'Ecuador', 'EG': 'Egypt', 'SV': 'El Salvador', 'GQ': 'Equatorial Guinea',
        'ER': 'Eritrea', 'EE': 'Estonia', 'ET': 'Ethiopia', 'FJ': 'Fiji',
        'FI': 'Finland', 'FR': 'France', 'GA': 'Gabon', 'GM': 'Gambia',
        'GE': 'Georgia', 'DE': 'Germany', 'GH': 'Ghana', 'GR': 'Greece',
        'GD': 'Grenada', 'GT': 'Guatemala', 'GN': 'Guinea', 'GW': 'Guinea-Bissau',
        'GY': 'Guyana', 'HT': 'Haiti', 'HN': 'Honduras', 'HU': 'Hungary',
        'IS': 'Iceland', 'IN': 'India', 'ID': 'Indonesia', 'IR': 'Iran',
        'IQ': 'Iraq', 'IE': 'Ireland', 'IL': 'Israel', 'IT': 'Italy',
        'JM': 'Jamaica', 'JP': 'Japan', 'JO': 'Jordan', 'KZ': 'Kazakhstan',
        'KE': 'Kenya', 'KI': 'Kiribati', 'KP': 'North Korea', 'KR': 'South Korea',
        'KW': 'Kuwait', 'KG': 'Kyrgyzstan', 'LA': 'Laos', 'LV': 'Latvia',
        'LB': 'Lebanon', 'LS': 'Lesotho', 'LR': 'Liberia', 'LY': 'Libya',
        'LI': 'Liechtenstein', 'LT': 'Lithuania', 'LU': 'Luxembourg', 'MG': 'Madagascar',
        'MW': 'Malawi', 'MY': 'Malaysia', 'MV': 'Maldives', 'ML': 'Mali',
        'MT': 'Malta', 'MH': 'Marshall Islands', 'MR': 'Mauritania', 'MU': 'Mauritius',
        'MX': 'Mexico', 'FM': 'Micronesia', 'MD': 'Moldova', 'MC': 'Monaco',
        'MN': 'Mongolia', 'ME': 'Montenegro', 'MA': 'Morocco', 'MZ': 'Mozambique',
        'MM': 'Myanmar', 'NA': 'Namibia', 'NR': 'Nauru', 'NP': 'Nepal',
        'NL': 'Netherlands', 'NZ': 'New Zealand', 'NI': 'Nicaragua', 'NE': 'Niger',
        'NG': 'Nigeria', 'NO': 'Norway', 'OM': 'Oman', 'PK': 'Pakistan',
        'PW': 'Palau', 'PA': 'Panama', 'PG': 'Papua New Guinea', 'PY': 'Paraguay',
        'PE': 'Peru', 'PH': 'Philippines', 'PL': 'Poland', 'PT': 'Portugal',
        'QA': 'Qatar', 'RO': 'Romania', 'RU': 'Russia', 'RW': 'Rwanda',
        'KN': 'Saint Kitts and Nevis', 'LC': 'Saint Lucia', 'VC': 'Saint Vincent',
        'WS': 'Samoa', 'SM': 'San Marino', 'ST': 'Sao Tome and Principe',
        'SA': 'Saudi Arabia', 'SN': 'Senegal', 'RS': 'Serbia', 'SC': 'Seychelles',
        'SL': 'Sierra Leone', 'SG': 'Singapore', 'SK': 'Slovakia', 'SI': 'Slovenia',
        'SB': 'Solomon Islands', 'SO': 'Somalia', 'ZA': 'South Africa',
        'SS': 'South Sudan', 'ES': 'Spain', 'LK': 'Sri Lanka', 'SD': 'Sudan',
        'SR': 'Suriname', 'SZ': 'Swaziland', 'SE': 'Sweden', 'CH': 'Switzerland',
        'SY': 'Syria', 'TW': 'Taiwan', 'TJ': 'Tajikistan', 'TZ': 'Tanzania',
        'TH': 'Thailand', 'TG': 'Togo', 'TO': 'Tonga', 'TT': 'Trinidad and Tobago',
        'TN': 'Tunisia', 'TR': 'Turkey', 'TM': 'Turkmenistan', 'TV': 'Tuvalu',
        'UG': 'Uganda', 'UA': 'Ukraine', 'AE': 'United Arab Emirates',
        'GB': 'United Kingdom', 'US': 'United States', 'UY': 'Uruguay',
        'UZ': 'Uzbekistan', 'VU': 'Vanuatu', 'VA': 'Vatican City',
        'VE': 'Venezuela', 'VN': 'Vietnam', 'YE': 'Yemen', 'ZM': 'Zambia',
        'ZW': 'Zimbabwe'
    }
    
    return country_names.get(country_code.upper(), country_code)

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
    
    async def fetch_retraction_notices(self, years: List[int], 
                                       progress_callback=None) -> List[dict]:
        """
        Fetch retraction notices (erratum type with Retraction in title).
        """
        all_works = []
        cursor = "*"
        page_count = 0
        total_count = 0
        
        # Build filter string: type erratum + years
        years_str = "|".join(map(str, years))
        filter_str = f"type:erratum,publication_year:{years_str}"
        
        logger.info(f"Fetching retraction notices for years {years}")
        
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
                    logger.error(f"Error fetching retraction notices: {response.status_code}")
                    break
                
                data = response.json()
                
                if page_count == 1:
                    total_count = data.get('meta', {}).get('count', 0)
                    logger.info(f"Total retraction notices found: {total_count}")
                    
                    if total_count == 0:
                        return []
                
                works = data.get('results', [])
                if not works:
                    break
                
                # Filter for Retraction/Retracted in title or display_name
                filtered_works = []
                for work in works:
                    title = work.get('title', '')
                    display_name = work.get('display_name', '')
                    if ('Retraction' in title or 'Retracted' in title or 
                        'Retraction' in display_name or 'Retracted' in display_name):
                        filtered_works.append(work)
                
                all_works.extend(filtered_works)
                
                if progress_callback and total_count > 0:
                    progress = min(len(all_works) / total_count, 1.0)
                    progress_callback(progress, len(all_works), page_count, total_count)
                
                logger.info(f"Page {page_count}: got {len(filtered_works)} retraction notices, total: {len(all_works)}/{total_count}")
                
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)
            
            logger.info(f"Finished fetching retraction notices. Total: {len(all_works)}")
            return all_works
            
        except Exception as e:
            logger.error(f"Error in fetch_retraction_notices: {str(e)}")
            return all_works
    
    async def fetch_retracted_articles(self, years: List[int],
                                       progress_callback=None) -> List[dict]:
        """
        Fetch retracted articles (is_retracted: true).
        """
        all_works = []
        cursor = "*"
        page_count = 0
        total_count = 0
        
        # Build filter string: is_retracted true + years
        years_str = "|".join(map(str, years))
        filter_str = f"is_retracted:true,publication_year:{years_str}"
        
        logger.info(f"Fetching retracted articles for years {years}")
        
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
                    logger.error(f"Error fetching retracted articles: {response.status_code}")
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
                
                all_works.extend(works)
                
                if progress_callback and total_count > 0:
                    progress = min(len(all_works) / total_count, 1.0)
                    progress_callback(progress, len(all_works), page_count, total_count)
                
                logger.info(f"Page {page_count}: got {len(works)} retracted articles, total: {len(all_works)}/{total_count}")
                
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)
            
            logger.info(f"Finished fetching retracted articles. Total: {len(all_works)}")
            return all_works
            
        except Exception as e:
            logger.error(f"Error in fetch_retracted_articles: {str(e)}")
            return all_works
    
    async def fetch_all_works_by_topic(self, topic_id: str, years: List[int], 
                                       progress_callback=None) -> List[dict]:
        """
        Fetch ALL works for a specific topic and years without citation filtering.
        Uses cursor pagination to get all available works.
        """
        all_works = []
        cursor = "*"
        page_count = 0
        total_count = 0
        
        # Build filter string: topic + years
        years_str = "|".join(map(str, years))
        filter_str = f"topics.id:{topic_id},publication_year:{years_str}"
        
        logger.info(f"Fetching ALL works for topic {topic_id}, years {years}")
        
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
                    logger.error(f"Error fetching works: {response.status_code}")
                    break
                
                data = response.json()
                
                if page_count == 1:
                    total_count = data.get('meta', {}).get('count', 0)
                    logger.info(f"Total works found: {total_count}")
                    
                    if total_count == 0:
                        return []
                
                works = data.get('results', [])
                if not works:
                    break
                
                all_works.extend(works)
                
                if progress_callback and total_count > 0:
                    progress = min(len(all_works) / total_count, 1.0)
                    progress_callback(progress, len(all_works), page_count, total_count)
                
                logger.info(f"Page {page_count}: got {len(works)} works, total: {len(all_works)}/{total_count}")
                
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)
            
            logger.info(f"Finished fetching. Total works: {len(all_works)}")
            return all_works
            
        except Exception as e:
            logger.error(f"Error in fetch_all_works_by_topic: {str(e)}")
            return all_works
    
    async def fetch_topic_stats(self, topic_id: str) -> Optional[dict]:
        cached = get_cached_topic_stats(topic_id)
        if cached:
            return cached
        
        url = f"{OPENALEX_BASE_URL}/topics/{topic_id}"
        data = await self.make_request(url)
        
        if data:
            cache_topic_stats(topic_id, data)
        
        return data

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

def fetch_retraction_notices_sync(years: List[int]) -> List[dict]:
    """
    Fetch retraction notices for given years.
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_works = []
    
    def update_progress(progress, count, page, total):
        progress_bar.progress(progress)
        status_text.text(f"Page {page}: {count}/{total} retraction notices fetched")
    
    async def fetch():
        async with OpenAlexAsyncClient() as client:
            return await client.fetch_retraction_notices(years, update_progress)
    
    result = run_async(fetch())
    progress_bar.empty()
    status_text.empty()
    return result

def fetch_retracted_articles_sync(years: List[int]) -> List[dict]:
    """
    Fetch retracted articles for given years.
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_works = []
    
    def update_progress(progress, count, page, total):
        progress_bar.progress(progress)
        status_text.text(f"Page {page}: {count}/{total} retracted articles fetched")
    
    async def fetch():
        async with OpenAlexAsyncClient() as client:
            return await client.fetch_retracted_articles(years, update_progress)
    
    result = run_async(fetch())
    progress_bar.empty()
    status_text.empty()
    return result

def fetch_all_works_by_topic_sync(topic_id: str, years: List[int]) -> List[dict]:
    """
    Fetch ALL works for a topic with given years (no citation filtering).
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_works = []
    
    def update_progress(progress, count, page, total):
        progress_bar.progress(progress)
        status_text.text(f"Page {page}: {count}/{total} works fetched")
    
    async def fetch():
        async with OpenAlexAsyncClient() as client:
            return await client.fetch_all_works_by_topic(
                topic_id, years, update_progress
            )
    
    result = run_async(fetch())
    progress_bar.empty()
    status_text.empty()
    return result

def fetch_topic_stats_sync(topic_id: str) -> Optional[dict]:
    async def fetch():
        async with OpenAlexAsyncClient() as client:
            return await client.fetch_topic_stats(topic_id)
    
    return run_async(fetch())

# ============================================================================
# HELPER FUNCTIONS
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
# RETRACTION-SPECIFIC FUNCTIONS
# ============================================================================

def extract_clean_title_from_notice(notice_title: str) -> Optional[str]:
    """
    Extract the original article title from a retraction notice title.
    Example:
    "Retraction Notice to \"RETRACTED: The angiostatic molecule Multimerin 2 is processed by MMP-9 to allow sprouting angiogenesis\""
    -> "The angiostatic molecule Multimerin 2 is processed by MMP-9 to allow sprouting angiogenesis"
    """
    if not notice_title:
        return None
    
    # Remove common prefixes
    prefixes = [
        r'^Retraction Notice to\s*["\']?',
        r'^Retraction:\s*',
        r'^RETRACTION:\s*',
        r'^Retracted:\s*',
        r'^RETRACTED:\s*',
        r'^Notice of Retraction:\s*',
        r'^Retraction Notice:\s*',
        r'^Editorial Retraction:\s*',
        r'^Retraction of:\s*',
        r'^Retraction for:\s*',
        r'^Withdrawal Notice:\s*',
        r'^Expression of Concern:\s*',
        r'^Notice of Concern:\s*'
    ]
    
    cleaned_title = notice_title
    
    for prefix in prefixes:
        cleaned_title = re.sub(prefix, '', cleaned_title, flags=re.IGNORECASE)
    
    # Remove quotes around the title
    cleaned_title = re.sub(r'^["\']+|["\']+$', '', cleaned_title)
    
    # Remove "RETRACTED:" prefix if present
    cleaned_title = re.sub(r'^RETRACTED:\s*', '', cleaned_title, flags=re.IGNORECASE)
    
    # Remove any leading/trailing whitespace
    cleaned_title = cleaned_title.strip()
    
    # If the cleaned title is still too similar to the original with "RETRACTED" prefix, try to extract the part after the colon
    if 'RETRACTED:' in cleaned_title:
        parts = cleaned_title.split('RETRACTED:', 1)
        if len(parts) > 1:
            cleaned_title = parts[1].strip()
    
    return cleaned_title if cleaned_title else None

def find_matching_retracted_article(notice_title: str, retracted_articles: List[dict]) -> Optional[dict]:
    """
    Find the retracted article that matches a retraction notice by title similarity.
    """
    if not notice_title or not retracted_articles:
        return None
    
    # Extract clean title from notice
    clean_title = extract_clean_title_from_notice(notice_title)
    if not clean_title:
        return None
    
    # Normalize clean title for comparison
    clean_title_norm = clean_title.lower().strip()
    clean_title_norm = re.sub(r'\s+', ' ', clean_title_norm)
    
    # Try to find exact match first
    for article in retracted_articles:
        article_title = article.get('title', '')
        if not article_title:
            continue
        
        article_title_norm = article_title.lower().strip()
        article_title_norm = re.sub(r'\s+', ' ', article_title_norm)
        
        # Remove "RETRACTED:" prefix if present
        article_title_norm = re.sub(r'^retracted:\s*', '', article_title_norm)
        
        # Check if clean title is in article title or vice versa
        if clean_title_norm in article_title_norm or article_title_norm in clean_title_norm:
            return article
        
        # Check if the common part matches (after removing prefixes)
        # Remove "RETRACTED:" from article title if present
        article_title_clean = re.sub(r'^RETRACTED:\s*', '', article_title, flags=re.IGNORECASE)
        article_title_clean_norm = article_title_clean.lower().strip()
        article_title_clean_norm = re.sub(r'\s+', ' ', article_title_clean_norm)
        
        if clean_title_norm in article_title_clean_norm or article_title_clean_norm in clean_title_norm:
            return article
    
    # If no exact match, try partial match with key phrases
    # Extract key words from clean title (exclude common words)
    stop_words = {'the', 'of', 'and', 'for', 'in', 'on', 'at', 'to', 'by', 'with', 'from', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
    key_words = [word for word in clean_title_norm.split() if word not in stop_words and len(word) > 3]
    
    if len(key_words) >= 3:
        for article in retracted_articles:
            article_title = article.get('title', '')
            if not article_title:
                continue
            
            article_title_norm = article_title.lower().strip()
            article_title_norm = re.sub(r'\s+', ' ', article_title_norm)
            article_title_norm = re.sub(r'^retracted:\s*', '', article_title_norm)
            
            # Count how many key words appear in the article title
            matches = sum(1 for word in key_words if word in article_title_norm)
            if matches >= len(key_words) * 0.6:  # At least 60% of key words match
                return article
    
    return None

def combine_retracted_with_notice(retracted_article: dict, notice: dict) -> dict:
    """
    Combine a retracted article with its retraction notice into a single combined card.
    """
    combined = {}
    
    # Copy retracted article data
    combined['retracted'] = retracted_article
    combined['notice'] = notice
    
    # Extract common fields from retracted article
    combined['doi_retracted'] = retracted_article.get('doi', '').replace('https://doi.org/', '')
    combined['doi_notice'] = notice.get('doi', '').replace('https://doi.org/', '')
    
    # Use the title from the retracted article (cleaner)
    combined['title'] = retracted_article.get('title', '')
    
    # Use publication info from retracted article
    combined['publication_year'] = retracted_article.get('publication_year', '')
    combined['publication_date'] = retracted_article.get('publication_date', '')
    
    # Extract authors from retracted article (all authors)
    combined['authors'] = retracted_article.get('authorships', [])
    
    # Extract journal and publisher info from retracted article
    primary_location = retracted_article.get('primary_location', {})
    source = primary_location.get('source', {}) if primary_location else {}
    combined['journal_name'] = source.get('display_name', '')
    combined['publisher'] = source.get('host_organization_name', '')
    if not combined['publisher']:
        combined['publisher'] = source.get('publisher', '')
    
    # Extract biblio info
    biblio = retracted_article.get('biblio', {})
    combined['volume'] = biblio.get('volume', '')
    combined['issue'] = biblio.get('issue', '')
    combined['first_page'] = biblio.get('first_page', '')
    combined['last_page'] = biblio.get('last_page', '')
    
    # Format pages
    if combined['first_page'] and combined['last_page'] and combined['first_page'] != combined['last_page']:
        combined['pages'] = f"{combined['first_page']}-{combined['last_page']}"
    elif combined['first_page']:
        combined['pages'] = combined['first_page']
    elif combined['last_page']:
        combined['pages'] = combined['last_page']
    else:
        combined['pages'] = ''
    
    # Extract notice-specific info
    combined['notice_publication_year'] = notice.get('publication_year', '')
    combined['notice_publication_date'] = notice.get('publication_date', '')
    
    # Notice journal
    notice_primary_location = notice.get('primary_location', {})
    notice_source = notice_primary_location.get('source', {}) if notice_primary_location else {}
    combined['notice_journal'] = notice_source.get('display_name', '')
    combined['notice_publisher'] = notice_source.get('host_organization_name', '')
    if not combined['notice_publisher']:
        combined['notice_publisher'] = notice_source.get('publisher', '')
    
    # Notice biblio
    
    combined['notice_volume'] = notice_biblio.get('volume', '')
    combined['notice_issue'] = notice_biblio.get('issue', '')
    combined['notice_first_page'] = notice_biblio.get('first_page', '')
    combined['notice_last_page'] = notice_biblio.get('last_page', '')
    
    if combined['notice_first_page'] and combined['notice_last_page'] and combined['notice_first_page'] != combined['notice_last_page']:
        combined['notice_pages'] = f"{combined['notice_first_page']}-{combined['notice_last_page']}"
    elif combined['notice_first_page']:
        combined['notice_pages'] = combined['notice_first_page']
    elif combined['notice_last_page']:
        combined['notice_pages'] = combined['notice_last_page']
    else:
        combined['notice_pages'] = ''
    
    # Extract countries from authorships of retracted article
    countries = set()
    for authorship in retracted_article.get('authorships', []):
        for institution in authorship.get('institutions', []):
            country = institution.get('country_code', '')
            if country:
                countries.add(country)
    combined['countries'] = list(countries)
    
    # Extract all affiliations from retracted article
    affiliations = []
    for authorship in retracted_article.get('authorships', []):
        for institution in authorship.get('institutions', []):
            name = institution.get('display_name', '')
            if name:
                affiliations.append(name)
    combined['affiliations'] = list(set(affiliations))
    
    return combined

def extract_author_name(author: dict) -> str:
    """
    Extract full author name from authorship data.
    """
    display_name = author.get('display_name', '')
    if display_name:
        return display_name
    return author.get('raw_author_name', '')

def extract_author_lastname_firstinitial(author_name: str) -> str:
    """
    Extract last name and first initial from author name.
    Example: "Eva Andreuzzi" -> "Andreuzzi E."
    """
    if not author_name:
        return ''
    
    parts = author_name.split()
    if len(parts) >= 2:
        last_name = parts[-1]
        first_initial = parts[0][0] if parts[0] else ''
        return f"{last_name} {first_initial}."
    else:
        return author_name

def is_article_from_selected_countries(combined_article: dict, selected_countries: List[str]) -> bool:
    """
    Check if an article has at least one author from any of the selected countries.
    """
    if not selected_countries:
        return True
    
    article_countries = combined_article.get('countries', [])
    for country in article_countries:
        if country.upper() in selected_countries:
            return True
    return False

# ============================================================================
# ENRICHMENT FUNCTIONS
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

def enrich_work_data_full(work: dict, current_year: int = None) -> dict:
    """
    Enrich article data with complete information including all fields.
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
    if current_year is None:
        current_year = datetime.now().year
    
    age = max(1, current_year - publication_year) if publication_year > 0 else 1
    citations_per_year = citations_total / age
    
    # OA status
    oa_status = get_oa_status(work)
    
    # Publication date
    publication_date = work.get('publication_date', '')
    
    # Get publication type info
    type_label, type_color, type_icon = get_publication_type_info(work)
    
    enriched = {
        'doi': doi_clean,
        'doi_url': f"https://doi.org/{doi_clean}" if doi_clean else '',
        'title': work.get('title', 'No title'),
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
        'country': extract_country_from_work(work)
    }
    
    return enriched

def enrich_combined_article(combined: dict) -> dict:
    """
    Enrich a combined article with formatted data for display and PDF generation.
    """
    if not combined:
        return {}
    
    retracted = combined.get('retracted', {})
    notice = combined.get('notice', {})
    
    # Extract all authors from retracted article
    authors = []
    for authorship in retracted.get('authorships', []):
        author = authorship.get('author', {})
        author_name = author.get('display_name', '')
        if author_name:
            authors.append(author_name)
    authors_str = ', '.join(authors) if authors else 'Authors not specified'
    
    # Extract affiliations
    affiliations = set()
    for authorship in retracted.get('authorships', []):
        for inst in authorship.get('institutions', []):
            inst_name = inst.get('display_name', '')
            if inst_name:
                affiliations.add(inst_name)
    affiliations_str = ' / '.join(affiliations) if affiliations else 'No affiliations specified'
    
    # Extract countries
    countries = set()
    for authorship in retracted.get('authorships', []):
        for inst in authorship.get('institutions', []):
            country = inst.get('country_code', '')
            if country:
                countries.add(country)
    countries_list = list(countries)
    
    # Format pages for retracted article
    biblio = retracted.get('biblio', {})
    first_page = biblio.get('first_page', '')
    last_page = biblio.get('last_page', '')
    if first_page and last_page and first_page != last_page:
        pages = f"{first_page}-{last_page}"
    elif first_page:
        pages = first_page
    elif last_page:
        pages = last_page
    else:
        pages = ''
    
    # Notice info
    notice_biblio = notice.get('biblio', {}) if notice else {}
    notice_first_page = notice_biblio.get('first_page', '') if notice_biblio else ''
    notice_last_page = notice_biblio.get('last_page', '') if notice_biblio else ''
    if notice_first_page and notice_last_page and notice_first_page != notice_last_page:
        notice_pages = f"{notice_first_page}-{notice_last_page}"
    elif notice_first_page:
        notice_pages = notice_first_page
    elif notice_last_page:
        notice_pages = notice_last_page
    else:
        notice_pages = ''
    
    # Get journal info from retracted article    retracted_primary_location = retracted.get('primary_location', {})
    retracted_primary_location = retracted.get('primary_location', {}) if retracted else {}
    retracted_source = retracted_primary_location.get('source', {}) if retracted_primary_location else {}
    retracted_journal = retracted_source.get('display_name', '') if retracted_source else ''
    retracted_publisher = retracted_source.get('host_organization_name', '') if retracted_source else ''
    if not retracted_publisher:
        retracted_publisher = retracted_source.get('publisher', '') if retracted_source else ''
    
    # Get journal info from notice
    notice_primary_location = notice.get('primary_location', {}) if notice else {}
    notice_source = notice_primary_location.get('source', {}) if notice_primary_location else {}
    notice_journal = notice_source.get('display_name', '') if notice_source else ''
    notice_publisher = notice_source.get('host_organization_name', '') if notice_source else ''
    if not notice_publisher and notice_source:
        notice_publisher = notice_source.get('publisher', '') if notice_source else ''
    
    enriched = {
        'doi_retracted': combined.get('doi_retracted', ''),
        'doi_notice': combined.get('doi_notice', ''),
        'doi_retracted_url': f"https://doi.org/{combined.get('doi_retracted', '')}" if combined.get('doi_retracted') else '',
        'doi_notice_url': f"https://doi.org/{combined.get('doi_notice', '')}" if combined.get('doi_notice') else '',
        'title': combined.get('title', 'No title'),
        'publication_year': combined.get('publication_year', ''),
        'publication_date': combined.get('publication_date', ''),
        'authors': authors_str,
        'authors_list': authors,
        'affiliations': list(affiliations),
        'affiliations_str': affiliations_str,
        'countries': countries_list,
        'journal_name': retracted_journal,
        'publisher': retracted_publisher,
        'volume': combined.get('volume', ''),
        'issue': combined.get('issue', ''),
        'pages': pages,
        'notice_journal': notice_journal,
        'notice_publisher': notice_publisher,
        'notice_volume': combined.get('notice_volume', ''),
        'notice_issue': combined.get('notice_issue', ''),
        'notice_pages': notice_pages,
        'notice_publication_year': combined.get('notice_publication_year', ''),
        'notice_publication_date': combined.get('notice_publication_date', ''),
        'raw_retracted': retracted,
        'raw_notice': notice
    }
    
    return enriched

# ============================================================================
# HIERARCHICAL GROUPING FUNCTIONS FOR RETRACTION REPORTS
# ============================================================================

@st.cache_data(ttl=3600)
def cached_group_by_country_affiliation(combined_articles_tuple: tuple, selected_countries: tuple) -> Dict[str, Dict[str, List[dict]]]:
    """
    Group combined articles by Country -> Affiliation.
    Each article appears under each country it has authors from.
    """
    combined_articles = list(combined_articles_tuple)
    selected_countries_list = list(selected_countries) if selected_countries else []
    return group_by_country_affiliation(combined_articles, selected_countries_list)

@st.cache_data(ttl=3600)
def cached_group_by_author(combined_articles_tuple: tuple) -> Dict[str, List[dict]]:
    """
    Group combined articles by author (last name + first initial).
    Each article appears under each author.
    """
    combined_articles = list(combined_articles_tuple)
    return group_by_author(combined_articles)

@st.cache_data(ttl=3600)
def cached_group_by_publisher_journal(combined_articles_tuple: tuple) -> Dict[str, Dict[str, List[dict]]]:
    """
    Group combined articles by Publisher -> Journal.
    """
    combined_articles = list(combined_articles_tuple)
    return group_by_publisher_journal(combined_articles)

def group_by_country_affiliation(combined_articles: List[dict], selected_countries: List[str]) -> Dict[str, Dict[str, List[dict]]]:
    """
    Group articles by Country -> Affiliation.
    Only includes articles that have at least one author from selected countries.
    If selected_countries is empty, includes all articles.
    """
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    # Filter articles by selected countries
    filtered_articles = []
    for article in combined_articles:
        if not selected_countries:
            filtered_articles.append(article)
        else:
            article_countries = article.get('countries', [])
            for country in article_countries:
                if country.upper() in selected_countries:
                    filtered_articles.append(article)
                    break
    
    # Group filtered articles by country -> affiliation
    for article in filtered_articles:
        countries = article.get('countries', [])
        affiliations = article.get('affiliations', ['Unknown Affiliation'])
        
        if not affiliations:
            affiliations = ['Unknown Affiliation']
        
        for country in countries:
            if selected_countries and country.upper() not in selected_countries:
                continue
            
            country_name = get_country_name(country)
            for aff in affiliations:
                hierarchy[country_name][aff].append(article)
    
    # Sort by number of articles in each country and affiliation
    sorted_hierarchy = {}
    country_items = []
    for country in hierarchy.keys():
        total_count = sum(len(articles) for articles in hierarchy[country].values())
        country_items.append((country, total_count))
    country_items.sort(key=lambda x: x[1], reverse=True)
    
    for country, _ in country_items:
        sorted_hierarchy[country] = {}
        affiliation_items = []
        for affiliation in hierarchy[country].keys():
            affiliation_items.append((affiliation, len(hierarchy[country][affiliation])))
        affiliation_items.sort(key=lambda x: x[1], reverse=True)
        
        for affiliation, _ in affiliation_items:
            # Sort articles within each affiliation by publication year (newest first)
            sorted_articles = sorted(
                hierarchy[country][affiliation],
                key=lambda x: x.get('publication_year', 0) if x.get('publication_year') else 0,
                reverse=True
            )
            sorted_hierarchy[country][affiliation] = sorted_articles
    
    return sorted_hierarchy

def group_by_author(combined_articles: List[dict]) -> Dict[str, List[dict]]:
    """
    Group articles by author (last name + first initial).
    Each article appears under each author.
    """
    author_groups = defaultdict(list)
    
    for article in combined_articles:
        authors = article.get('authors_list', [])
        if not authors:
            continue
        
        for author in authors:
            author_key = extract_author_lastname_firstinitial(author)
            if author_key:
                author_groups[author_key].append(article)
    
    # Sort authors by number of articles (descending)
    sorted_author_groups = {}
    author_items = []
    for author, articles in author_groups.items():
        author_items.append((author, articles))
    author_items.sort(key=lambda x: len(x[1]), reverse=True)
    
    for author, articles in author_items:
        # Sort articles within each author by publication year (newest first)
        sorted_articles = sorted(
            articles,
            key=lambda x: x.get('publication_year', 0) if x.get('publication_year') else 0,
            reverse=True
        )
        sorted_author_groups[author] = sorted_articles
    
    return sorted_author_groups

def group_by_publisher_journal(combined_articles: List[dict]) -> Dict[str, Dict[str, List[dict]]]:
    """
    Group articles by Publisher -> Journal.
    Uses publisher from retracted article.
    """
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for article in combined_articles:
        publisher = article.get('publisher', 'Unknown Publisher')
        if not publisher:
            publisher = 'Unknown Publisher'
        
        journal = article.get('journal_name', 'Unknown Journal')
        if not journal:
            journal = 'Unknown Journal'
        
        hierarchy[publisher][journal].append(article)
    
    # Sort by number of articles
    sorted_hierarchy = {}
    publisher_items = []
    for publisher in hierarchy.keys():
        total_count = sum(len(articles) for articles in hierarchy[publisher].values())
        publisher_items.append((publisher, total_count))
    publisher_items.sort(key=lambda x: x[1], reverse=True)
    
    for publisher, _ in publisher_items:
        sorted_hierarchy[publisher] = {}
        journal_items = []
        for journal in hierarchy[publisher].keys():
            journal_items.append((journal, len(hierarchy[publisher][journal])))
        journal_items.sort(key=lambda x: x[1], reverse=True)
        
        for journal, _ in journal_items:
            # Sort articles within each journal by publication year (newest first)
            sorted_articles = sorted(
                hierarchy[publisher][journal],
                key=lambda x: x.get('publication_year', 0) if x.get('publication_year') else 0,
                reverse=True
            )
            sorted_hierarchy[publisher][journal] = sorted_articles
    
    return sorted_hierarchy

# ============================================================================
# PDF REPORT GENERATION FUNCTIONS FOR RETRACTION REPORTS
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

def generate_retraction_pdf_by_country_affiliation(
    hierarchy: Dict,
    years: List[int],
    selected_countries: List[str],
    logo_path: str = None,
    report_title: str = "Report by Country & Affiliation"
) -> bytes:
    """
    Generate PDF report grouping retracted articles by Country -> Affiliation.
    """
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
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    notice_style = ParagraphStyle(
        'NoticeStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#e74c3c'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    doi_style = ParagraphStyle(
        'DoiStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#2980b9'),
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
    
    total_articles = sum(len(articles) for country in hierarchy.values() 
                        for affiliation in country.values() 
                        for articles in [affiliation])
    total_countries = len(hierarchy)
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo at beginning
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph("Retracted Articles Grouped by Country & Affiliation", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    
    if selected_countries:
        country_names = [get_country_name(c) for c in selected_countries]
        story.append(Paragraph(f"Selected countries: {', '.join(country_names)}", subtitle_style))
    
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_articles} retracted articles grouped by Country and Affiliation.
    Articles are sorted by the number of retractions in each group (descending order).
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Retracted Articles", str(total_articles)],
        ["Countries", str(total_countries)],
        ["Report Type", report_title],
        ["Sorting", "By Retraction Count (Descending)"]
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
        country_articles = sum(len(articles) for articles in affiliations.values())
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(country)}</b> — {country_articles} articles</a>', toc_country_style))
        
        for affiliation, articles in affiliations.items():
            aff_articles = len(articles)
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{aff_anchor_id}">{clean_text(affiliation)}</a> — {aff_articles} articles', toc_affiliation_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # Main content
    for country, affiliations in hierarchy.items():
        country_articles = sum(len(articles) for articles in affiliations.values())
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(country)} — {country_articles} articles", country_style))
        story.append(Spacer(1, 0.3*cm))
        
        for affiliation, articles in affiliations.items():
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            aff_anchor_para = Paragraph(f'<a name="{aff_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(aff_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{clean_text(affiliation)} — {len(articles)} articles", affiliation_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, article in enumerate(articles, 1):
                title = clean_text(article.get('title', 'No title'))
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {title}", article_title_style))
                
                authors = clean_text(article.get('authors', 'Authors not specified'))
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors}", authors_style))
                
                # Affiliations
                affs = clean_text(article.get('affiliations_str', ''))
                if affs and affs != 'No affiliations specified':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style))
                
                # Retracted article info
                year = article.get('publication_year', '')
                pub_date = article.get('publication_date', '')
                volume = article.get('volume', '')
                issue = article.get('issue', '')
                pages = article.get('pages', '')
                journal = article.get('journal_name', '')
                publisher = article.get('publisher', '')
                
                meta_parts = []
                if publisher:
                    meta_parts.append(f"Publisher: {publisher}")
                if journal:
                    meta_parts.append(f"Journal: {journal}")
                if year:
                    meta_parts.append(f"Year: {year}")
                if pub_date and pub_date != '0000-00-00':
                    meta_parts.append(f"Published: {pub_date}")
                if volume:
                    meta_parts.append(f"Vol. {volume}")
                if issue:
                    meta_parts.append(f"Iss. {issue}")
                if pages:
                    meta_parts.append(f"pp. {pages}")
                
                if meta_parts:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style))
                
                # Retracted article DOI
                doi_retracted = article.get('doi_retracted', '')
                if doi_retracted:
                    doi_url = clean_doi_url(f"https://doi.org/{doi_retracted}")
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Retracted Article DOI:</b> <a href='{doi_url}'>{doi_retracted}</a>", doi_style))
                
                # Notice info
                notice_year = article.get('notice_publication_year', '')
                notice_date = article.get('notice_publication_date', '')
                notice_journal = article.get('notice_journal', '')
                notice_publisher = article.get('notice_publisher', '')
                notice_volume = article.get('notice_volume', '')
                notice_issue = article.get('notice_issue', '')
                notice_pages = article.get('notice_pages', '')
                doi_notice = article.get('doi_notice', '')
                
                if notice_year or notice_journal or doi_notice:
                    notice_parts = []
                    notice_parts.append("<b>🔴 Retraction Notice:</b>")
                    if notice_publisher:
                        notice_parts.append(f"Publisher: {notice_publisher}")
                    if notice_journal:
                        notice_parts.append(f"Journal: {notice_journal}")
                    if notice_year:
                        notice_parts.append(f"Year: {notice_year}")
                    if notice_date and notice_date != '0000-00-00':
                        notice_parts.append(f"Published: {notice_date}")
                    if notice_volume:
                        notice_parts.append(f"Vol. {notice_volume}")
                    if notice_issue:
                        notice_parts.append(f"Iss. {notice_issue}")
                    if notice_pages:
                        notice_parts.append(f"pp. {notice_pages}")
                    
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{' | '.join(notice_parts)}", notice_style))
                    
                    if doi_notice:
                        notice_doi_url = clean_doi_url(f"https://doi.org/{doi_notice}")
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Retraction Notice DOI:</b> <a href='{notice_doi_url}'>{doi_notice}</a>", doi_style))
                
                story.append(Spacer(1, 0.15*cm))
                
                if idx < len(articles):
                    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;" + "─" * 40, separator_style))
                    story.append(Spacer(1, 0.1*cm))
            
            story.append(Spacer(1, 0.3*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_articles} retracted articles grouped by {total_countries} countries and their respective affiliations.
    The articles are sorted by the number of retractions in each group (descending order).
    Within each affiliation, articles are sorted by publication year (newest first).
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Retraction Detector Pro*2 | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retraction Article Detector Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_retraction_pdf_by_author(
    author_groups: Dict[str, List[dict]],
    years: List[int],
    selected_countries: List[str],
    logo_path: str = None,
    report_title: str = "Report by Author"
) -> bytes:
    """
    Generate PDF report grouping retracted articles by author.
    """
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
        fontSize=16,
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
        leftIndent=30,
        fontName=russian_font_name
    )
    
    authors_style = ParagraphStyle(
        'AuthorsStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=3,
        leftIndent=30,
        fontName=russian_font_name
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=2,
        leftIndent=30,
        fontName=russian_font_name
    )
    
    notice_style = ParagraphStyle(
        'NoticeStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#e74c3c'),
        spaceAfter=2,
        leftIndent=30,
        fontName=russian_font_name
    )
    
    doi_style = ParagraphStyle(
        'DoiStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#2980b9'),
        spaceAfter=2,
        leftIndent=30,
        fontName=russian_font_name
    )
    
    toc_author_style = ParagraphStyle(
        'TOCAuthorStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=6,
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
    
    total_articles = sum(len(articles) for articles in author_groups.values())
    total_authors = len(author_groups)
    
    story.append(Spacer(1, 2*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph("Retracted Articles Grouped by Author", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    
    if selected_countries:
        country_names = [get_country_name(c) for c in selected_countries]
        story.append(Paragraph(f"Selected countries: {', '.join(country_names)}", subtitle_style))
    
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_articles} retracted articles grouped by author (last name + first initial).
    Authors are sorted by the number of retracted articles (descending order).
    Each article appears under each author who contributed to it.
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Retracted Articles", str(total_articles)],
        ["Unique Authors", str(total_authors)],
        ["Report Type", report_title],
        ["Sorting", "By Retraction Count (Descending)"]
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
    
    for author, articles in author_groups.items():
        anchor_id = f"author_{hashlib.md5(author.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(author)}</b> — {len(articles)} articles</a>', toc_author_style))
    
    story.append(PageBreak())
    
    # Main content
    for author, articles in author_groups.items():
        anchor_id = f"author_{hashlib.md5(author.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(author)} — {len(articles)} articles", author_style))
        story.append(Spacer(1, 0.2*cm))
        
        for idx, article in enumerate(articles, 1):
            title = clean_text(article.get('title', 'No title'))
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {title}", article_title_style))
            
            all_authors = clean_text(article.get('authors', 'Authors not specified'))
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>All Authors:</b> {all_authors}", authors_style))
            
            # Affiliations
            affs = clean_text(article.get('affiliations_str', ''))
            if affs and affs != 'No affiliations specified':
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style))
            
            # Retracted article info
            year = article.get('publication_year', '')
            pub_date = article.get('publication_date', '')
            volume = article.get('volume', '')
            issue = article.get('issue', '')
            pages = article.get('pages', '')
            journal = article.get('journal_name', '')
            publisher = article.get('publisher', '')
            
            meta_parts = []
            if publisher:
                meta_parts.append(f"Publisher: {publisher}")
            if journal:
                meta_parts.append(f"Journal: {journal}")
            if year:
                meta_parts.append(f"Year: {year}")
            if pub_date and pub_date != '0000-00-00':
                meta_parts.append(f"Published: {pub_date}")
            if volume:
                meta_parts.append(f"Vol. {volume}")
            if issue:
                meta_parts.append(f"Iss. {issue}")
            if pages:
                meta_parts.append(f"pp. {pages}")
            
            if meta_parts:
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style))
            
            # Retracted article DOI
            doi_retracted = article.get('doi_retracted', '')
            if doi_retracted:
                doi_url = clean_doi_url(f"https://doi.org/{doi_retracted}")
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Retracted Article DOI:</b> <a href='{doi_url}'>{doi_retracted}</a>", doi_style))
            
            # Notice info
            notice_year = article.get('notice_publication_year', '')
            notice_date = article.get('notice_publication_date', '')
            notice_journal = article.get('notice_journal', '')
            notice_publisher = article.get('notice_publisher', '')
            notice_volume = article.get('notice_volume', '')
            notice_issue = article.get('notice_issue', '')
            notice_pages = article.get('notice_pages', '')
            doi_notice = article.get('doi_notice', '')
            
            if notice_year or notice_journal or doi_notice:
                notice_parts = []
                notice_parts.append("<b>🔴 Retraction Notice:</b>")
                if notice_publisher:
                    notice_parts.append(f"Publisher: {notice_publisher}")
                if notice_journal:
                    notice_parts.append(f"Journal: {notice_journal}")
                if notice_year:
                    notice_parts.append(f"Year: {notice_year}")
                if notice_date and notice_date != '0000-00-00':
                    notice_parts.append(f"Published: {notice_date}")
                if notice_volume:
                    notice_parts.append(f"Vol. {notice_volume}")
                if notice_issue:
                    notice_parts.append(f"Iss. {notice_issue}")
                if notice_pages:
                    notice_parts.append(f"pp. {notice_pages}")
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{' | '.join(notice_parts)}", notice_style))
                
                if doi_notice:
                    notice_doi_url = clean_doi_url(f"https://doi.org/{doi_notice}")
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Retraction Notice DOI:</b> <a href='{notice_doi_url}'>{doi_notice}</a>", doi_style))
            
            story.append(Spacer(1, 0.15*cm))
            
            if idx < len(articles):
                story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;" + "─" * 40, separator_style))
                story.append(Spacer(1, 0.1*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_articles} retracted articles grouped by {total_authors} unique authors.
    The authors are sorted by the number of retracted articles (descending order).
    Within each author group, articles are sorted by publication year (newest first).
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Retraction Detector Pro*2 | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retraction Article Detector Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_retraction_pdf_by_publisher_journal(
    hierarchy: Dict,
    years: List[int],
    selected_countries: List[str],
    logo_path: str = None,
    report_title: str = "Report by Publisher & Journal"
) -> bytes:
    """
    Generate PDF report grouping retracted articles by Publisher -> Journal.
    """
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
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    notice_style = ParagraphStyle(
        'NoticeStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#e74c3c'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    doi_style = ParagraphStyle(
        'DoiStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#2980b9'),
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
    
    total_articles = sum(len(articles) for publisher in hierarchy.values() 
                        for journal in publisher.values() 
                        for articles in [journal])
    total_publishers = len(hierarchy)
    
    story.append(Spacer(1, 2*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph("Retracted Articles Grouped by Publisher & Journal", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    
    if selected_countries:
        country_names = [get_country_name(c) for c in selected_countries]
        story.append(Paragraph(f"Selected countries: {', '.join(country_names)}", subtitle_style))
    
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_articles} retracted articles grouped by Publisher and Journal.
    Publishers and journals are sorted by the number of retracted articles (descending order).
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Retracted Articles", str(total_articles)],
        ["Publishers", str(total_publishers)],
        ["Report Type", report_title],
        ["Sorting", "By Retraction Count (Descending)"]
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
        publisher_articles = sum(len(articles) for articles in journals.values())
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(publisher)}</b> — {publisher_articles} articles</a>', toc_publisher_style))
        
        for journal, articles in journals.items():
            journal_articles = len(articles)
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{journal_anchor_id}">{clean_text(journal)}</a> — {journal_articles} articles', toc_journal_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # Main content
    for publisher, journals in hierarchy.items():
        publisher_articles = sum(len(articles) for articles in journals.values())
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(publisher)} — {publisher_articles} articles", publisher_style))
        story.append(Spacer(1, 0.3*cm))
        
        for journal, articles in journals.items():
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            journal_anchor_para = Paragraph(f'<a name="{journal_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(journal_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{clean_text(journal)} — {len(articles)} articles", journal_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, article in enumerate(articles, 1):
                title = clean_text(article.get('title', 'No title'))
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {title}", article_title_style))
                
                authors = clean_text(article.get('authors', 'Authors not specified'))
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors}", authors_style))
                
                # Affiliations
                affs = clean_text(article.get('affiliations_str', ''))
                if affs and affs != 'No affiliations specified':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style))
                
                # Retracted article info
                year = article.get('publication_year', '')
                pub_date = article.get('publication_date', '')
                volume = article.get('volume', '')
                issue = article.get('issue', '')
                pages = article.get('pages', '')
                
                meta_parts = []
                if year:
                    meta_parts.append(f"Year: {year}")
                if pub_date and pub_date != '0000-00-00':
                    meta_parts.append(f"Published: {pub_date}")
                if volume:
                    meta_parts.append(f"Vol. {volume}")
                if issue:
                    meta_parts.append(f"Iss. {issue}")
                if pages:
                    meta_parts.append(f"pp. {pages}")
                
                if meta_parts:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style))
                
                # Retracted article DOI
                doi_retracted = article.get('doi_retracted', '')
                if doi_retracted:
                    doi_url = clean_doi_url(f"https://doi.org/{doi_retracted}")
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Retracted Article DOI:</b> <a href='{doi_url}'>{doi_retracted}</a>", doi_style))
                
                # Notice info
                notice_year = article.get('notice_publication_year', '')
                notice_date = article.get('notice_publication_date', '')
                notice_journal = article.get('notice_journal', '')
                notice_publisher = article.get('notice_publisher', '')
                notice_volume = article.get('notice_volume', '')
                notice_issue = article.get('notice_issue', '')
                notice_pages = article.get('notice_pages', '')
                doi_notice = article.get('doi_notice', '')
                
                if notice_year or notice_journal or doi_notice:
                    notice_parts = []
                    notice_parts.append("<b>🔴 Retraction Notice:</b>")
                    if notice_publisher:
                        notice_parts.append(f"Publisher: {notice_publisher}")
                    if notice_journal:
                        notice_parts.append(f"Journal: {notice_journal}")
                    if notice_year:
                        notice_parts.append(f"Year: {notice_year}")
                    if notice_date and notice_date != '0000-00-00':
                        notice_parts.append(f"Published: {notice_date}")
                    if notice_volume:
                        notice_parts.append(f"Vol. {notice_volume}")
                    if notice_issue:
                        notice_parts.append(f"Iss. {notice_issue}")
                    if notice_pages:
                        notice_parts.append(f"pp. {notice_pages}")
                    
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{' | '.join(notice_parts)}", notice_style))
                    
                    if doi_notice:
                        notice_doi_url = clean_doi_url(f"https://doi.org/{doi_notice}")
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Retraction Notice DOI:</b> <a href='{notice_doi_url}'>{doi_notice}</a>", doi_style))
                
                story.append(Spacer(1, 0.15*cm))
                
                if idx < len(articles):
                    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;" + "─" * 40, separator_style))
                    story.append(Spacer(1, 0.1*cm))
            
            story.append(Spacer(1, 0.3*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_articles} retracted articles grouped by {total_publishers} publishers and their respective journals.
    The publishers and journals are sorted by the number of retracted articles (descending order).
    Within each journal, articles are sorted by publication year (newest first).
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Retraction Detector Pro*2 | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retraction Article Detector Pro*2", footer_style))
    
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
# UI STEPS FOR RETRACTION DETECTOR
# ============================================================================

def step_data_input():
    """Step 1: Input years and countries"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📥 Step 1: Configure Analysis Parameters</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Enter publication years and select countries to analyze retracted articles.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="filter-section" style="background: rgba(255, 255, 255, 0.9); border-radius: 20px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(102, 126, 234, 0.2);">
        <div class="filter-header" style="font-size: 1.1rem; font-weight: 600; color: #495057; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #667eea;">
            📅 Publication Years
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.9rem; color: #666; margin-bottom: 10px;">
        <strong>Supported formats:</strong>
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
    
    st.markdown("</div>", unsafe_allow_html=True)
    
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
    
    st.markdown("---")
    
    st.markdown("""
    <div class="filter-section" style="background: rgba(255, 255, 255, 0.9); border-radius: 20px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(102, 126, 234, 0.2);">
        <div class="filter-header" style="font-size: 1.1rem; font-weight: 600; color: #495057; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #667eea;">
            🌍 Countries (at least one author must belong)
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.9rem; color: #666; margin-bottom: 10px;">
        <strong>Supported formats:</strong>
    </div>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px;">
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">RU</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">IT+RU</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">IT+RU+CN</span>
        <span style="background: #fff3e0; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; border: 1px dashed #ff9800;">US,GB,DE</span>
    </div>
    """, unsafe_allow_html=True)
    
    country_input = st.text_input(
        "Enter country codes",
        value=st.session_state.get('country_input', ''),
        placeholder="Example: RU or IT+RU or IT+RU+CN",
        help="Enter 2-letter country codes separated by + or comma"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if country_input:
        countries = parse_country_filter(country_input)
        if countries:
            country_names = [get_country_name(c) for c in countries]
            st.markdown(f"""
            <div style="background: #e8f5e9; border-radius: 8px; padding: 12px; border-left: 4px solid #4CAF50; margin: 10px 0;">
                <strong>✅ Selected countries:</strong> {', '.join(country_names)}
                <br><span style="font-size: 0.85rem; color: #666;">Codes: {', '.join(countries)}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #ffebee; border-radius: 8px; padding: 12px; border-left: 4px solid #f44336; margin: 10px 0;">
                <strong>❌ Invalid country codes:</strong> Please use 2-letter codes.
                <br><span style="font-size: 0.85rem; color: #666;">Example: RU, IT, US, GB</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            if not years_input:
                st.error("❌ Please enter at least one year.")
                return
            
            years = parse_year_filter(years_input)
            if not years:
                st.error("❌ Invalid year format. Please check your input.")
                return
            
            countries = parse_country_filter(country_input) if country_input else []
            
            st.session_state.years = years
            st.session_state.years_input = years_input
            st.session_state.countries = countries
            st.session_state.country_input = country_input
            st.session_state.current_step = 2
            st.rerun()

def step_analysis():
    """Step 2: Fetching retraction data"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 2: Fetching Retraction Data</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Searching for retracted articles and retraction notices in OpenAlex...</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'years' not in st.session_state:
        st.error("❌ No parameters set. Please go back to Step 1.")
        return
    
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    
    years = st.session_state.years
    countries = st.session_state.countries
    
    col1, col2, col3 = st.columns(3)
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
            <div class="metric-value">8/sec</div>
            <div class="metric-label">API Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Fetch retraction notices
    with st.spinner("Fetching retraction notices..."):
        retraction_notices = fetch_retraction_notices_sync(years)
    
    st.markdown(f"""
    <div style="background: #e3f2fd; border-radius: 8px; padding: 12px; border-left: 4px solid #2196F3; margin: 10px 0;">
        <strong>📋 Retraction notices found:</strong> {len(retraction_notices)}
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch retracted articles
    with st.spinner("Fetching retracted articles..."):
        retracted_articles = fetch_retracted_articles_sync(years)
    
    st.markdown(f"""
    <div style="background: #e3f2fd; border-radius: 8px; padding: 12px; border-left: 4px solid #2196F3; margin: 10px 0;">
        <strong>📋 Retracted articles found:</strong> {len(retracted_articles)}
    </div>
    """, unsafe_allow_html=True)
    
    # Combine retracted articles with their notices
    combined_articles = []
    matched_notices = set()
    
    with st.spinner("Matching retraction notices with retracted articles..."):
        # First, try to match each retraction notice with a retracted article
        for notice in retraction_notices:
            # Проверка, что notice не None и является словарем
            if notice is None or not isinstance(notice, dict):
                continue
            
            notice_title = notice.get('title', '') if notice.get('title') else ''
            if not notice_title:
                continue
            
            matched_article = find_matching_retracted_article(notice_title, retracted_articles)
            if matched_article:
                combined = combine_retracted_with_notice(matched_article, notice)
                enriched = enrich_combined_article(combined)
                
                # Проверка, что enriched не пустой словарь
                if enriched and is_article_from_selected_countries(enriched, countries):
                    combined_articles.append(enriched)
                    matched_notices.add(notice.get('doi', ''))
        
        # Add retracted articles that don't have a matching notice
        for article in retracted_articles:
            # Проверка, что article не None и является словарем
            if article is None or not isinstance(article, dict):
                continue
            
            article_doi = article.get('doi', '').replace('https://doi.org/', '') if article.get('doi') else ''
            
            # Check if this article already has a notice matched
            already_matched = False
            for combined in combined_articles:
                if combined.get('doi_retracted') == article_doi:
                    already_matched = True
                    break
            
            if not already_matched:
                combined = {
                    'retracted': article,
                    'notice': None,
                    'doi_retracted': article_doi,
                    'doi_notice': '',
                    'title': article.get('title', 'No title') if article.get('title') else 'No title',
                    'publication_year': article.get('publication_year', '') if article.get('publication_year') else '',
                    'publication_date': article.get('publication_date', '') if article.get('publication_date') else '',
                }
                enriched = enrich_combined_article(combined)
                
                # Проверка, что enriched не пустой словарь
                if enriched and is_article_from_selected_countries(enriched, countries):
                    combined_articles.append(enriched)
    
    st.session_state.combined_articles = combined_articles
    st.session_state.retraction_notices = retraction_notices
    st.session_state.retracted_articles = retracted_articles
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #2196F315 0%, #0D47A115 100%); border-radius: 8px; padding: 12px; border-left: 3px solid #2196F3; font-size: 0.9rem; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>✅ Analysis Complete!</strong><br>
                Found {len(combined_articles)} combined retracted articles with notices
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(retraction_notices)}</div>
            <div class="metric-label">Retraction Notices</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(retracted_articles)}</div>
            <div class="metric-label">Retracted Articles</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(combined_articles)}</div>
            <div class="metric-label">Combined Entries</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📊 Generate Reports", type="primary", use_container_width=True):
            if combined_articles:
                st.session_state.current_step = 3
                st.rerun()
            else:
                st.error("❌ No combined articles found. Please try different parameters.")

def step_results():
    """Step 3: Results with 3 PDF reports"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📊 Step 3: Retraction Analysis Results</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Download reports for retracted articles.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'combined_articles' not in st.session_state:
        st.error("❌ No data available. Please go back.")
        return
    
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    
    combined_articles = st.session_state.combined_articles
    years = st.session_state.years
    countries = st.session_state.countries
    
    if not combined_articles:
        st.warning("⚠️ No combined articles found. Please try different parameters.")
        return
    
    # Generate groupings
    with st.spinner("Generating report groupings..."):
        # Group by country -> affiliation
        country_hierarchy = cached_group_by_country_affiliation(
            tuple(combined_articles), 
            tuple(countries) if countries else ()
        )
        
        # Group by author
        author_groups = cached_group_by_author(tuple(combined_articles))
        
        # Group by publisher -> journal
        publisher_hierarchy = cached_group_by_publisher_journal(tuple(combined_articles))
    
    total_articles = len(combined_articles)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_articles:,}</div>
            <div class="metric-label">Total Retracted Articles</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(country_hierarchy)}</div>
            <div class="metric-label">Countries</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(author_groups)}</div>
            <div class="metric-label">Authors</div>
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
    
    years_hash = hashlib.md5(','.join(map(str, years)).encode()).hexdigest()[:8]
    countries_hash = hashlib.md5(','.join(countries).encode()).hexdigest()[:8] if countries else 'all'
    filter_hash = hashlib.md5(str(sorted([a.get('doi_retracted', '') for a in combined_articles])).encode()).hexdigest()[:8]
    
    cache_key_country = f"retraction_country_{years_hash}_{countries_hash}_{filter_hash}"
    cache_key_author = f"retraction_author_{years_hash}_{countries_hash}_{filter_hash}"
    cache_key_publisher = f"retraction_publisher_{years_hash}_{countries_hash}_{filter_hash}"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🌍 Report 1: Country → Affiliation**")
        st.markdown("*Sorted by retraction count*")
        
        if cache_key_country in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_country]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"retraction_country_{format_year_filter_for_filename(years)}.pdf"
            st.download_button(
                label="📄 Download Country Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_country_{cache_key_country}"
            )
        else:
            if st.button("📄 Generate Country Report", key=f"gen_country_{cache_key_country}", use_container_width=True):
                with st.spinner("Generating Country → Affiliation report..."):
                    pdf_data = generate_retraction_pdf_by_country_affiliation(
                        country_hierarchy,
                        years,
                        countries,
                        logo_path,
                        "Report by Country & Affiliation"
                    )
                    st.session_state.pdf_cache[cache_key_country] = pdf_data
                    st.rerun()
    
    with col2:
        st.markdown("**👤 Report 2: Author**")
        st.markdown("*Sorted by retraction count per author*")
        
        if cache_key_author in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_author]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"retraction_author_{format_year_filter_for_filename(years)}.pdf"
            st.download_button(
                label="📄 Download Author Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_author_{cache_key_author}"
            )
        else:
            if st.button("📄 Generate Author Report", key=f"gen_author_{cache_key_author}", use_container_width=True):
                with st.spinner("Generating Author report..."):
                    pdf_data = generate_retraction_pdf_by_author(
                        author_groups,
                        years,
                        countries,
                        logo_path,
                        "Report by Author"
                    )
                    st.session_state.pdf_cache[cache_key_author] = pdf_data
                    st.rerun()
    
    with col3:
        st.markdown("**📚 Report 3: Publisher → Journal**")
        st.markdown("*Sorted by retraction count*")
        
        if cache_key_publisher in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_publisher]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"retraction_publisher_{format_year_filter_for_filename(years)}.pdf"
            st.download_button(
                label="📄 Download Publisher Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_publisher_{cache_key_publisher}"
            )
        else:
            if st.button("📄 Generate Publisher Report", key=f"gen_publisher_{cache_key_publisher}", use_container_width=True):
                with st.spinner("Generating Publisher → Journal report..."):
                    pdf_data = generate_retraction_pdf_by_publisher_journal(
                        publisher_hierarchy,
                        years,
                        countries,
                        logo_path,
                        "Report by Publisher & Journal"
                    )
                    st.session_state.pdf_cache[cache_key_publisher] = pdf_data
                    st.rerun()
    
    st.markdown("---")
    
    if all(key in st.session_state.pdf_cache for key in [cache_key_country, cache_key_author, cache_key_publisher]):
        try:
            import zipfile
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(f"retraction_country_{format_year_filter_for_filename(years)}.pdf", 
                                 st.session_state.pdf_cache[cache_key_country])
                zip_file.writestr(f"retraction_author_{format_year_filter_for_filename(years)}.pdf", 
                                 st.session_state.pdf_cache[cache_key_author])
                zip_file.writestr(f"retraction_publisher_{format_year_filter_for_filename(years)}.pdf", 
                                 st.session_state.pdf_cache[cache_key_publisher])
            
            zip_data = zip_buffer.getvalue()
            
            col_zip1, col_zip2, col_zip3 = st.columns([1, 2, 1])
            with col_zip2:
                st.download_button(
                    label="📦 Download All Reports (ZIP archive)",
                    data=zip_data,
                    file_name=f"retraction_all_reports_{format_year_filter_for_filename(years)}.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="download_all_zip"
                )
        except Exception as e:
            st.error(f"Error creating ZIP archive: {e}")
    
    st.markdown("---")
    
    if st.button("🔄 New Analysis", use_container_width=True):
        keys_to_clear = ['current_step', 'years', 'years_input', 'countries', 'country_input',
                        'retraction_notices', 'retracted_articles', 'combined_articles',
                        'pdf_cache', 'all_reports_generated']
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
    
    # Title
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 class="main-header">Retraction Article Detector Pro*2</h1>
        <p style="color: #6c757d; font-size: 1rem; margin-top: -5px;">
            Detect and analyze retracted articles using OpenAlex data
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    steps = ["Parameters", "Analysis", "Reports"]
    current_step = st.session_state.current_step
    progress = (current_step - 1) / 2
    
    st.markdown(f"""
    <div class="progress-container" style="background: #f5f5f5; border-radius: 8px; height: 6px; margin: 20px 0; overflow: hidden;">
        <div class="progress-bar" style="height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 8px; transition: width 0.5s ease; width: {progress * 100}%;"></div>
    </div>
    <div class="step-indicator" style="display: flex; justify-content: space-between; margin: 15px 0; font-size: 0.85rem; color: #666;">
        <span class="{'active' if current_step >= 1 else ''}" style="color: {'#667eea' if current_step >= 1 else '#666'}; font-weight: {'600' if current_step >= 1 else '400'};">📥 Parameters</span>
        <span class="{'active' if current_step >= 2 else ''}" style="color: {'#667eea' if current_step >= 2 else '#666'}; font-weight: {'600' if current_step >= 2 else '400'};">🔍 Analysis</span>
        <span class="{'active' if current_step >= 3 else ''}" style="color: {'#667eea' if current_step >= 3 else '#666'}; font-weight: {'600' if current_step >= 3 else '400'};">📊 Reports</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Display current step
    if st.session_state.current_step == 1:
        step_data_input()
    elif st.session_state.current_step == 2:
        step_analysis()
    elif st.session_state.current_step == 3:
        step_results()
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>© Retraction Detector Pro*2 / developed by daM©</p>
        <p style="font-size: 0.7rem; color: #aaa;">Retraction Article Detector Pro*2 with multi-report generation</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
