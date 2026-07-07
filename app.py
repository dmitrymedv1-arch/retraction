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
    page_title="CTA Retraction Article Detector Pro*2",
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
POLITE_POOL_HEADER = {'User-Agent': f'CTA-App (mailto:{MAILTO})'}

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
    "RU+IT" -> ["RU", "IT"]
    "RU+IT+CN" -> ["RU", "IT", "CN"]
    "ru+it" -> ["RU", "IT"]
    """
    if not country_input or country_input.strip() == "":
        return []
    
    # Remove spaces and split by '+'
    country_input = country_input.strip().upper()
    countries = [c.strip() for c in country_input.split('+') if c.strip()]
    
    # Validate country codes (2-letter ISO codes)
    valid_countries = []
    for country in countries:
        if len(country) == 2 and country.isalpha():
            valid_countries.append(country)
        else:
            logger.warning(f"Invalid country code: {country}")
    
    return valid_countries

def get_full_country_name(country_code: str) -> str:
    """
    Get full country name from country code.
    """
    country_map = {
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
        'CG': 'Congo', 'CD': 'Congo (DRC)', 'CR': 'Costa Rica', 'HR': 'Croatia',
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
        'LI': 'Liechtenstein', 'LT': 'Lithuania', 'LU': 'Luxembourg',
        'MK': 'North Macedonia', 'MG': 'Madagascar', 'MW': 'Malawi',
        'MY': 'Malaysia', 'MV': 'Maldives', 'ML': 'Mali', 'MT': 'Malta',
        'MH': 'Marshall Islands', 'MR': 'Mauritania', 'MU': 'Mauritius',
        'MX': 'Mexico', 'FM': 'Micronesia', 'MD': 'Moldova', 'MC': 'Monaco',
        'MN': 'Mongolia', 'ME': 'Montenegro', 'MA': 'Morocco', 'MZ': 'Mozambique',
        'MM': 'Myanmar', 'NA': 'Namibia', 'NR': 'Nauru', 'NP': 'Nepal',
        'NL': 'Netherlands', 'NZ': 'New Zealand', 'NI': 'Nicaragua',
        'NE': 'Niger', 'NG': 'Nigeria', 'NO': 'Norway', 'OM': 'Oman',
        'PK': 'Pakistan', 'PW': 'Palau', 'PA': 'Panama', 'PG': 'Papua New Guinea',
        'PY': 'Paraguay', 'PE': 'Peru', 'PH': 'Philippines', 'PL': 'Poland',
        'PT': 'Portugal', 'QA': 'Qatar', 'RO': 'Romania', 'RU': 'Russia',
        'RW': 'Rwanda', 'KN': 'Saint Kitts and Nevis', 'LC': 'Saint Lucia',
        'VC': 'Saint Vincent and the Grenadines', 'WS': 'Samoa', 'SM': 'San Marino',
        'ST': 'Sao Tome and Principe', 'SA': 'Saudi Arabia', 'SN': 'Senegal',
        'RS': 'Serbia', 'SC': 'Seychelles', 'SL': 'Sierra Leone', 'SG': 'Singapore',
        'SK': 'Slovakia', 'SI': 'Slovenia', 'SB': 'Solomon Islands',
        'SO': 'Somalia', 'ZA': 'South Africa', 'SS': 'South Sudan',
        'ES': 'Spain', 'LK': 'Sri Lanka', 'SD': 'Sudan', 'SR': 'Suriname',
        'SZ': 'Eswatini', 'SE': 'Sweden', 'CH': 'Switzerland', 'SY': 'Syria',
        'TW': 'Taiwan', 'TJ': 'Tajikistan', 'TZ': 'Tanzania', 'TH': 'Thailand',
        'TL': 'Timor-Leste', 'TG': 'Togo', 'TO': 'Tonga', 'TT': 'Trinidad and Tobago',
        'TN': 'Tunisia', 'TR': 'Turkey', 'TM': 'Turkmenistan', 'TV': 'Tuvalu',
        'UG': 'Uganda', 'UA': 'Ukraine', 'AE': 'United Arab Emirates',
        'GB': 'United Kingdom', 'US': 'United States', 'UY': 'Uruguay',
        'UZ': 'Uzbekistan', 'VU': 'Vanuatu', 'VA': 'Vatican City',
        'VE': 'Venezuela', 'VN': 'Vietnam', 'YE': 'Yemen', 'ZM': 'Zambia',
        'ZW': 'Zimbabwe'
    }
    return country_map.get(country_code.upper(), country_code)

# ============================================================================
# RETRACTION DETECTION FUNCTIONS
# ============================================================================

def is_retraction_notice(work: dict) -> bool:
    """
    Check if a work is a retraction notice.
    Checks for:
    - type == "erratum"
    - "Retraction" or "Retracted" in display_name or title
    """
    if not work:
        return False
    
    # Check type
    work_type = work.get('type', '').lower()
    if work_type != 'erratum':
        return False
    
    # Check display_name and title for retraction keywords
    display_name = work.get('display_name', '')
    title = work.get('title', '')
    
    retraction_keywords = ['retraction', 'retracted']
    combined_text = (display_name + ' ' + title).lower()
    
    for keyword in retraction_keywords:
        if keyword in combined_text:
            return True
    
    return False

def extract_clean_title_from_retraction_notice(work: dict) -> str:
    """
    Extract the clean title of the retracted article from a retraction notice.
    Example:
    "Retraction Notice to "RETRACTED: The angiostatic molecule Multimerin 2 is processed by MMP-9 to allow sprouting angiogenesis""
    -> "The angiostatic molecule Multimerin 2 is processed by MMP-9 to allow sprouting angiogenesis"
    """
    if not work:
        return ""
    
    display_name = work.get('display_name', '')
    title = work.get('title', '')
    
    combined = display_name if display_name else title
    
    # Remove "Retraction Notice to" and similar prefixes
    patterns = [
        r'(?i)^retraction\s+notice\s+to\s+["\']?(retracted:\s*)?',
        r'(?i)^retraction\s+notice\s+["\']?(retracted:\s*)?',
        r'(?i)^retracted\s+["\']?',
        r'(?i)^notice\s+of\s+retraction\s+["\']?(retracted:\s*)?',
        r'(?i)^retraction\s+["\']?(retracted:\s*)?',
    ]
    
    clean_title = combined
    for pattern in patterns:
        clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)
    
    # Remove quotes
    clean_title = re.sub(r'^["\']+|["\']+$', '', clean_title)
    clean_title = clean_title.strip()
    
    # If still has "RETRACTED:" prefix, remove it
    clean_title = re.sub(r'^RETRACTED:\s*', '', clean_title, flags=re.IGNORECASE)
    clean_title = clean_title.strip()
    
    return clean_title

def extract_clean_title_from_retracted_article(work: dict) -> str:
    """
    Extract the clean title from a retracted article.
    Removes "RETRACTED:" prefix if present.
    """
    if not work:
        return ""
    
    title = work.get('title', '')
    display_name = work.get('display_name', '')
    
    combined = display_name if display_name else title
    
    # Remove "RETRACTED:" prefix
    clean_title = re.sub(r'^RETRACTED:\s*', '', combined, flags=re.IGNORECASE)
    clean_title = clean_title.strip()
    
    return clean_title

def find_retracted_article_for_notice(notice_work: dict, retracted_articles: List[dict]) -> Optional[dict]:
    """
    Find the retracted article that corresponds to a retraction notice.
    Uses title matching: extracts clean title from notice and searches for similar title in retracted articles.
    """
    if not notice_work or not retracted_articles:
        return None
    
    clean_notice_title = extract_clean_title_from_retraction_notice(notice_work)
    if not clean_notice_title:
        return None
    
    # Normalize for comparison
    clean_notice_title_norm = clean_notice_title.lower().strip()
    
    best_match = None
    best_score = 0
    
    for article in retracted_articles:
        clean_article_title = extract_clean_title_from_retracted_article(article)
        if not clean_article_title:
            continue
        
        clean_article_title_norm = clean_article_title.lower().strip()
        
        # Check if titles match exactly or if one contains the other
        if clean_notice_title_norm == clean_article_title_norm:
            return article
        elif clean_article_title_norm in clean_notice_title_norm:
            # Notice title contains article title (or vice versa)
            score = len(clean_article_title_norm) / len(clean_notice_title_norm)
            if score > best_score:
                best_score = score
                best_match = article
        elif clean_notice_title_norm in clean_article_title_norm:
            score = len(clean_notice_title_norm) / len(clean_article_title_norm)
            if score > best_score:
                best_score = score
                best_match = article
    
    # Only return if match is reasonably good (> 0.5 similarity)
    if best_score > 0.5:
        return best_match
    
    return None

def find_retraction_notices_for_article(article_work: dict, retraction_notices: List[dict]) -> List[dict]:
    """
    Find all retraction notices that correspond to a retracted article.
    """
    if not article_work or not retraction_notices:
        return []
    
    clean_article_title = extract_clean_title_from_retracted_article(article_work)
    if not clean_article_title:
        return []
    
    clean_article_title_norm = clean_article_title.lower().strip()
    
    matching_notices = []
    
    for notice in retraction_notices:
        clean_notice_title = extract_clean_title_from_retraction_notice(notice)
        if not clean_notice_title:
            continue
        
        clean_notice_title_norm = clean_notice_title.lower().strip()
        
        # Check if titles match
        if (clean_article_title_norm == clean_notice_title_norm or
            clean_article_title_norm in clean_notice_title_norm or
            clean_notice_title_norm in clean_article_title_norm):
            matching_notices.append(notice)
    
    return matching_notices

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
    
    async def fetch_retracted_works_by_years(self, years: List[int], 
                                             progress_callback=None) -> List[dict]:
        """
        Fetch all retracted works (is_retracted: true) for given years.
        """
        all_works = []
        cursor = "*"
        page_count = 0
        total_count = 0
        
        years_str = "|".join(map(str, years))
        filter_str = f"is_retracted:true,publication_year:{years_str}"
        
        logger.info(f"Fetching retracted works for years {years}")
        
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
                    logger.error(f"Error fetching retracted works: {response.status_code}")
                    break
                
                data = response.json()
                
                if page_count == 1:
                    total_count = data.get('meta', {}).get('count', 0)
                    logger.info(f"Total retracted works found: {total_count}")
                    
                    if total_count == 0:
                        return []
                
                works = data.get('results', [])
                if not works:
                    break
                
                all_works.extend(works)
                
                if progress_callback and total_count > 0:
                    progress = min(len(all_works) / total_count, 1.0)
                    progress_callback(progress, len(all_works), page_count, total_count)
                
                logger.info(f"Page {page_count}: got {len(works)} retracted works, total: {len(all_works)}/{total_count}")
                
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)
            
            logger.info(f"Finished fetching retracted works. Total: {len(all_works)}")
            return all_works
            
        except Exception as e:
            logger.error(f"Error in fetch_retracted_works_by_years: {str(e)}")
            return all_works
    
    async def fetch_retraction_notices_by_years(self, years: List[int],
                                                progress_callback=None) -> List[dict]:
        """
        Fetch all retraction notices (type: erratum with retraction keywords) for given years.
        """
        all_works = []
        cursor = "*"
        page_count = 0
        total_count = 0
        
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
                    logger.info(f"Total erratum works found: {total_count}")
                    
                    if total_count == 0:
                        return []
                
                works = data.get('results', [])
                if not works:
                    break
                
                # Filter for retraction notices
                for work in works:
                    if is_retraction_notice(work):
                        all_works.append(work)
                
                if progress_callback and total_count > 0:
                    progress = min(len(all_works) / total_count, 1.0)
                    progress_callback(progress, len(all_works), page_count, total_count)
                
                logger.info(f"Page {page_count}: got {len(works)} works, retraction notices: {len(all_works)}")
                
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)
            
            logger.info(f"Finished fetching retraction notices. Total: {len(all_works)}")
            return all_works
            
        except Exception as e:
            logger.error(f"Error in fetch_retraction_notices_by_years: {str(e)}")
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

def fetch_retracted_works_by_years_sync(years: List[int]) -> List[dict]:
    """
    Fetch all retracted works for given years.
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_works = []
    
    def update_progress(progress, count, page, total):
        progress_bar.progress(progress)
        status_text.text(f"Page {page}: {count}/{total} retracted works fetched")
    
    async def fetch():
        async with OpenAlexAsyncClient() as client:
            return await client.fetch_retracted_works_by_years(years, update_progress)
    
    result = run_async(fetch())
    progress_bar.empty()
    status_text.empty()
    return result

def fetch_retraction_notices_by_years_sync(years: List[int]) -> List[dict]:
    """
    Fetch all retraction notices for given years.
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_works = []
    
    def update_progress(progress, count, page, total):
        progress_bar.progress(progress)
        status_text.text(f"Page {page}: {count}/{total} works scanned")
    
    async def fetch():
        async with OpenAlexAsyncClient() as client:
            return await client.fetch_retraction_notices_by_years(years, update_progress)
    
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
# ENRICHMENT FUNCTIONS FOR RETRACTION DATA
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

def extract_authors_with_countries(work: dict) -> List[Tuple[str, List[str]]]:
    """
    Extract all authors with their countries.
    Returns list of (author_name, [country_codes]) tuples.
    """
    authors_with_countries = []
    
    authorships = work.get('authorships', [])
    
    for authorship in authorships:
        if authorship:
            author = authorship.get('author', {})
            if author:
                author_name = author.get('display_name', '')
                if author_name:
                    import unicodedata
                    author_name = unicodedata.normalize('NFC', str(author_name))
                    author_name = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s\.\,\-\'\(\)]', '', author_name)
                    author_name = re.sub(r'\s+', ' ', author_name).strip()
                    
                    if author_name:
                        countries = []
                        for inst in authorship.get('institutions', []):
                            if inst:
                                country_code = inst.get('country_code', '')
                                if country_code:
                                    countries.append(country_code.upper())
                        if countries:
                            authors_with_countries.append((author_name, list(set(countries))))
    
    return authors_with_countries

def extract_author_name_parts(author_name: str) -> Tuple[str, str]:
    """
    Extract last name and first initial from author name.
    Example: "Eva Andreuzzi" -> ("Andreuzzi", "E.")
    """
    if not author_name:
        return "", ""
    
    parts = author_name.strip().split()
    if not parts:
        return "", ""
    
    last_name = parts[-1]
    
    # Get first initial from first part
    first_part = parts[0]
    first_initial = first_part[0].upper() if first_part else ""
    
    return last_name, first_initial

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
    if is_retraction_notice(work):
        return ('Retraction Notice', '#e74c3c', '⚠️')
    
    # Check if retracted
    if work.get('is_retracted', False):
        return ('Retracted Article', '#c0392b', '🚫')
    
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

def enrich_retraction_card(article_work: dict, notice_works: List[dict] = None) -> dict:
    """
    Enrich a retraction card combining retracted article and its retraction notices.
    """
    if not article_work:
        return {}
    
    notice_works = notice_works or []
    
    # Extract basic info from article
    doi_raw = article_work.get('doi')
    doi_clean = ''
    if doi_raw:
        doi_clean = str(doi_raw).replace('https://doi.org/', '')
    
    # Extract ALL authors and affiliations (no truncation)
    authors, affiliations = extract_all_authors_and_affiliations(article_work)
    authors_str = ', '.join(authors) if authors else 'Authors not specified'
    
    # Join all affiliations with slash separator
    if affiliations:
        affiliations_str = ' / '.join(affiliations)
    else:
        affiliations_str = 'No affiliations specified'
    
    # Extract authors with countries
    authors_with_countries = extract_authors_with_countries(article_work)
    
    # Extract publication info
    biblio = article_work.get('biblio', {})
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
    primary_location = article_work.get('primary_location')
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
    primary_topic = article_work.get('primary_topic', {})
    topic_name = primary_topic.get('display_name', '') if primary_topic else ''
    topic_id = ''
    if primary_topic:
        topic_id_raw = primary_topic.get('id', '')
        if topic_id_raw:
            topic_id = topic_id_raw.split('/')[-1]
    
    # Citation metrics
    citations_total = article_work.get('cited_by_count', 0)
    referenced_works = article_work.get('referenced_works_count', 0)
    
    publication_year = article_work.get('publication_year', 0)
    current_year = datetime.now().year
    age = max(1, current_year - publication_year) if publication_year > 0 else 1
    citations_per_year = citations_total / age
    
    # OA status
    oa_status = get_oa_status(article_work)
    
    # Publication date
    publication_date = article_work.get('publication_date', '')
    
    # Get publication type info
    type_label, type_color, type_icon = get_publication_type_info(article_work)
    
    # Process notice works
    notice_data = []
    for notice in notice_works:
        notice_doi = notice.get('doi', '').replace('https://doi.org/', '')
        notice_year = notice.get('publication_year', 0)
        notice_date = notice.get('publication_date', '')
        notice_title = notice.get('title', '')
        notice_display_name = notice.get('display_name', '')
        
        notice_data.append({
            'doi': notice_doi,
            'doi_url': f"https://doi.org/{notice_doi}" if notice_doi else '',
            'year': notice_year,
            'date': notice_date,
            'title': notice_title,
            'display_name': notice_display_name
        })
    
    # Determine card type
    has_notice = len(notice_data) > 0
    is_retracted = article_work.get('is_retracted', False)
    
    if has_notice and is_retracted:
        card_type = 'retracted_with_notice'
        card_type_label = 'Retracted Article + Retraction Notice'
        card_type_icon = '⚠️🚫'
    elif is_retracted:
        card_type = 'retracted_only'
        card_type_label = 'Retracted Article (No Notice)'
        card_type_icon = '🚫'
    elif has_notice:
        card_type = 'notice_only'
        card_type_label = 'Retraction Notice (No Article)'
        card_type_icon = '⚠️'
    else:
        card_type = 'unknown'
        card_type_label = 'Unknown'
        card_type_icon = '❓'
    
    enriched = {
        'doi': doi_clean,
        'doi_url': f"https://doi.org/{doi_clean}" if doi_clean else '',
        'title': article_work.get('title', 'No title'),
        'display_name': article_work.get('display_name', ''),
        'publication_year': publication_year,
        'publication_date': publication_date,
        'cited_by_count': citations_total,
        'citations_per_year': round(citations_per_year, 1),
        'referenced_works_count': referenced_works,
        'authors': authors_str,
        'authors_list': authors,
        'affiliations': affiliations,
        'affiliations_str': affiliations_str,
        'authors_with_countries': authors_with_countries,
        'journal_name': journal_name,
        'publisher': publisher,
        'publisher_chain': publisher_chain,
        'volume': volume,
        'issue': issue,
        'pages': pages_str,
        'primary_topic': topic_name,
        'topic_id': topic_id,
        'oa_status': oa_status,
        'type': article_work.get('type', ''),
        'type_label': type_label,
        'type_color': type_color,
        'type_icon': type_icon,
        'country': extract_country_from_work(article_work),
        'is_retracted': is_retracted,
        'notice_data': notice_data,
        'card_type': card_type,
        'card_type_label': card_type_label,
        'card_type_icon': card_type_icon,
        'has_notice': has_notice,
        'notice_count': len(notice_data)
    }
    
    return enriched

def enrich_retraction_notice_only(notice_work: dict) -> dict:
    """
    Enrich a retraction notice that doesn't have a corresponding retracted article.
    """
    if not notice_work:
        return {}
    
    # Extract basic info from notice
    doi_raw = notice_work.get('doi')
    doi_clean = ''
    if doi_raw:
        doi_clean = str(doi_raw).replace('https://doi.org/', '')
    
    # Extract ALL authors and affiliations (no truncation)
    authors, affiliations = extract_all_authors_and_affiliations(notice_work)
    authors_str = ', '.join(authors) if authors else 'Authors not specified'
    
    # Join all affiliations with slash separator
    if affiliations:
        affiliations_str = ' / '.join(affiliations)
    else:
        affiliations_str = 'No affiliations specified'
    
    # Extract authors with countries
    authors_with_countries = extract_authors_with_countries(notice_work)
    
    # Extract publication info
    biblio = notice_work.get('biblio', {})
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
    primary_location = notice_work.get('primary_location')
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
    primary_topic = notice_work.get('primary_topic', {})
    topic_name = primary_topic.get('display_name', '') if primary_topic else ''
    topic_id = ''
    if primary_topic:
        topic_id_raw = primary_topic.get('id', '')
        if topic_id_raw:
            topic_id = topic_id_raw.split('/')[-1]
    
    # Citation metrics
    citations_total = notice_work.get('cited_by_count', 0)
    referenced_works = notice_work.get('referenced_works_count', 0)
    
    publication_year = notice_work.get('publication_year', 0)
    current_year = datetime.now().year
    age = max(1, current_year - publication_year) if publication_year > 0 else 1
    citations_per_year = citations_total / age
    
    # OA status
    oa_status = get_oa_status(notice_work)
    
    # Publication date
    publication_date = notice_work.get('publication_date', '')
    
    # Get publication type info
    type_label, type_color, type_icon = get_publication_type_info(notice_work)
    
    enriched = {
        'doi': doi_clean,
        'doi_url': f"https://doi.org/{doi_clean}" if doi_clean else '',
        'title': notice_work.get('title', 'No title'),
        'display_name': notice_work.get('display_name', ''),
        'publication_year': publication_year,
        'publication_date': publication_date,
        'cited_by_count': citations_total,
        'citations_per_year': round(citations_per_year, 1),
        'referenced_works_count': referenced_works,
        'authors': authors_str,
        'authors_list': authors,
        'affiliations': affiliations,
        'affiliations_str': affiliations_str,
        'authors_with_countries': authors_with_countries,
        'journal_name': journal_name,
        'publisher': publisher,
        'publisher_chain': publisher_chain,
        'volume': volume,
        'issue': issue,
        'pages': pages_str,
        'primary_topic': topic_name,
        'topic_id': topic_id,
        'oa_status': oa_status,
        'type': notice_work.get('type', ''),
        'type_label': type_label,
        'type_color': type_color,
        'type_icon': type_icon,
        'country': extract_country_from_work(notice_work),
        'is_retracted': False,
        'notice_data': [{
            'doi': doi_clean,
            'doi_url': f"https://doi.org/{doi_clean}" if doi_clean else '',
            'year': publication_year,
            'date': publication_date,
            'title': notice_work.get('title', ''),
            'display_name': notice_work.get('display_name', '')
        }],
        'card_type': 'notice_only',
        'card_type_label': 'Retraction Notice (No Article)',
        'card_type_icon': '⚠️',
        'has_notice': True,
        'notice_count': 1
    }
    
    return enriched

# ============================================================================
# RETRACTION CARD GROUPING AND SORTING FUNCTIONS
# ============================================================================

def filter_cards_by_countries(cards: List[dict], selected_countries: List[str]) -> List[dict]:
    """
    Filter retraction cards by selected countries.
    A card is included if at least one author belongs to a selected country.
    """
    if not selected_countries:
        return cards
    
    filtered_cards = []
    selected_countries_upper = [c.upper() for c in selected_countries]
    
    for card in cards:
        authors_with_countries = card.get('authors_with_countries', [])
        card_countries = set()
        
        for author_name, countries in authors_with_countries:
            for country in countries:
                if country.upper():
                    card_countries.add(country.upper())
        
        # Check if any card country is in selected countries
        if any(country in selected_countries_upper for country in card_countries):
            filtered_cards.append(card)
    
    return filtered_cards

def get_author_last_initial(author_name: str) -> str:
    """
    Get author's last name and first initial.
    Example: "Eva Andreuzzi" -> "Andreuzzi E."
    """
    if not author_name:
        return ""
    
    parts = author_name.strip().split()
    if not parts:
        return ""
    
    last_name = parts[-1]
    first_initial = parts[0][0].upper() if parts[0] else ""
    
    return f"{last_name} {first_initial}."

def group_cards_by_country_affiliation(cards: List[dict], selected_countries: List[str]) -> Dict[str, Dict[str, List[dict]]]:
    """
    Group retraction cards by Country -> Affiliation.
    Only includes countries from selected_countries.
    Sorted by number of cards (descending).
    """
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    selected_countries_upper = [c.upper() for c in selected_countries] if selected_countries else []
    
    for card in cards:
        authors_with_countries = card.get('authors_with_countries', [])
        affiliations = card.get('affiliations', ['Unknown Affiliation'])
        if not affiliations:
            affiliations = ['Unknown Affiliation']
        
        card_countries = set()
        for author_name, countries in authors_with_countries:
            for country in countries:
                if country.upper():
                    card_countries.add(country.upper())
        
        # Only include selected countries
        if selected_countries_upper:
            card_countries = card_countries.intersection(set(selected_countries_upper))
        
        for country in card_countries:
            country_name = get_full_country_name(country)
            for aff in affiliations:
                if aff:
                    hierarchy[country][aff].append(card)
    
    # Sort by card count (descending)
    sorted_hierarchy = {}
    
    # Sort countries by total card count
    country_items = []
    for country in hierarchy.keys():
        total_count = sum(len(cards) for cards in hierarchy[country].values())
        country_items.append((country, total_count))
    country_items.sort(key=lambda x: x[1], reverse=True)
    
    for country, _ in country_items:
        # Sort affiliations by card count
        aff_items = []
        for aff in hierarchy[country].keys():
            aff_items.append((aff, len(hierarchy[country][aff])))
        aff_items.sort(key=lambda x: x[1], reverse=True)
        
        sorted_hierarchy[country] = {}
        for aff, _ in aff_items:
            sorted_hierarchy[country][aff] = hierarchy[country][aff]
    
    return sorted_hierarchy

def group_cards_by_author(cards: List[dict], selected_countries: List[str]) -> Dict[str, List[dict]]:
    """
    Group retraction cards by author (last name + first initial).
    Only includes authors from selected countries.
    Sorted by number of cards (descending).
    """
    author_cards = defaultdict(list)
    
    selected_countries_upper = [c.upper() for c in selected_countries] if selected_countries else []
    
    for card in cards:
        authors_with_countries = card.get('authors_with_countries', [])
        
        for author_name, countries in authors_with_countries:
            # Check if author belongs to selected countries
            author_countries = [c.upper() for c in countries if c]
            
            if selected_countries_upper:
                if not any(country in selected_countries_upper for country in author_countries):
                    continue
            
            author_key = get_author_last_initial(author_name)
            if author_key:
                author_cards[author_key].append(card)
    
    # Sort authors by card count (descending)
    sorted_authors = {}
    for author in sorted(author_cards.keys(), key=lambda x: len(author_cards[x]), reverse=True):
        sorted_authors[author] = author_cards[author]
    
    return sorted_authors

def group_cards_by_publisher_journal(cards: List[dict]) -> Dict[str, Dict[str, List[dict]]]:
    """
    Group retraction cards by Publisher -> Journal.
    Sorted by number of cards (descending).
    """
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for card in cards:
        publisher = card.get('publisher', 'Unknown Publisher')
        if publisher is None:
            publisher = 'Unknown Publisher'
        if isinstance(publisher, str):
            if publisher.startswith('P') and publisher[1:].isdigit() or 'openalex.org/P' in publisher:
                publisher_chain = card.get('publisher_chain', [])
                if publisher_chain and len(publisher_chain) > 0:
                    publisher = publisher_chain[0]
                else:
                    publisher = 'Unknown Publisher'
        
        journal = card.get('journal_name', 'Unknown Journal')
        if journal is None:
            journal = 'Unknown Journal'
        
        hierarchy[publisher][journal].append(card)
    
    # Sort by card count (descending)
    sorted_hierarchy = {}
    
    # Sort publishers by total card count
    publisher_items = []
    for publisher in hierarchy.keys():
        total_count = sum(len(cards) for cards in hierarchy[publisher].values())
        publisher_items.append((publisher, total_count))
    publisher_items.sort(key=lambda x: x[1], reverse=True)
    
    for publisher, _ in publisher_items:
        # Sort journals by card count
        journal_items = []
        for journal in hierarchy[publisher].keys():
            journal_items.append((journal, len(hierarchy[publisher][journal])))
        journal_items.sort(key=lambda x: x[1], reverse=True)
        
        sorted_hierarchy[publisher] = {}
        for journal, _ in journal_items:
            sorted_hierarchy[publisher][journal] = hierarchy[publisher][journal]
    
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

def generate_pdf_retraction_report_country_affiliation(
    journal_name: str, 
    years: List[int],
    countries: List[str],
    hierarchy: Dict[str, Dict[str, List[dict]]],
    logo_path: str = None,
    report_title: str = "Retraction Report by Country & Affiliation"
) -> bytes:
    """Generate PDF report grouping retraction cards by Country -> Affiliation."""
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
    
    card_title_style = ParagraphStyle(
        'CardTitle',
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
    
    meta_style_retracted = ParagraphStyle(
        'MetaRetracted',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#c0392b'),
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
    
    total_cards = sum(len(cards) for country in hierarchy.values() 
                      for affiliation in country.values() 
                      for cards in [affiliation])
    total_countries = len(hierarchy)
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo at beginning
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    countries_str = ', '.join([get_full_country_name(c) for c in countries]) if countries else 'All countries'
    story.append(Paragraph(f"Selected countries: {countries_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_cards} retraction cards grouped by Country and Affiliation.
    
    Cards are sorted by the number of retractions (descending).
    Each card represents either a retracted article, a retraction notice, or a combination of both.
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Cards", str(total_cards)],
        ["Countries", str(total_countries)],
        ["Report Type", report_title],
        ["Period", years_str],
        ["Countries", countries_str]
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
        country_articles = sum(len(cards) for cards in affiliations.values())
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(country)}</b> — {country_articles} cards</a>', toc_country_style))
        
        for affiliation, cards in affiliations.items():
            aff_count = len(cards)
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{aff_anchor_id}">{clean_text(affiliation)}</a> — {aff_count} cards', toc_affiliation_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # Main content
    for country, affiliations in hierarchy.items():
        country_articles = sum(len(cards) for cards in affiliations.values())
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(country)} — {country_articles} cards", country_style))
        story.append(Spacer(1, 0.3*cm))
        
        for affiliation, cards in affiliations.items():
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            aff_anchor_para = Paragraph(f'<a name="{aff_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(aff_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{clean_text(affiliation)} — {len(cards)} cards", affiliation_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, card in enumerate(cards, 1):
                title = clean_text(card.get('title', 'No title'))
                card_type_icon = card.get('card_type_icon', '📄')
                card_type_label = card.get('card_type_label', 'Unknown')
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {card_type_icon} {title}", card_title_style))
                
                # Card type badge
                if card_type_label == 'Retracted Article + Retraction Notice':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#c0392b'><b>⚠️🚫 {card_type_label}</b></font>", meta_style_retracted))
                elif card_type_label == 'Retracted Article (No Notice)':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#c0392b'><b>🚫 {card_type_label}</b></font>", meta_style_retracted))
                elif card_type_label == 'Retraction Notice (No Article)':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#e74c3c'><b>⚠️ {card_type_label}</b></font>", meta_style_notice))
                
                authors = clean_text(card.get('authors', 'Authors not specified'))
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors}", authors_style))
                
                # Affiliations
                affs = clean_text(card.get('affiliations_str', ''))
                if affs and affs != 'No affiliations specified':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style))
                
                # Journal and publisher
                journal_name_article = clean_text(card.get('journal_name', ''))
                if journal_name_article:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Journal:</b> {journal_name_article}", meta_style))
                
                publisher = clean_text(card.get('publisher', ''))
                if publisher:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Publisher:</b> {publisher}", meta_style))
                
                year = card.get('publication_year', '')
                pub_date = card.get('publication_date', '')
                volume = card.get('volume', '')
                issue = card.get('issue', '')
                pages = card.get('pages', '')
                
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
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style))
                
                # DOI for article
                doi_url = card.get('doi_url', '')
                if doi_url:
                    doi_url_clean = clean_doi_url(doi_url)
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Article DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style))
                
                # Notice DOIs
                notice_data = card.get('notice_data', [])
                if notice_data:
                    for notice_idx, notice in enumerate(notice_data, 1):
                        notice_doi_url = notice.get('doi_url', '')
                        if notice_doi_url:
                            notice_doi_clean = clean_doi_url(notice_doi_url)
                            notice_year = notice.get('year', '')
                            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Notice {notice_idx} DOI:</b> <a href='{notice_doi_clean}'>{notice_doi_clean}</a> (Year: {notice_year})", meta_style_notice))
                
                # Citations
                citations = card.get('cited_by_count', 0)
                citations_per_year = card.get('citations_per_year', 0)
                references = card.get('referenced_works_count', 0)
                oa_status = card.get('oa_status', 'Closed Access')
                
                citation_text = f"<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f} | <b>References:</b> {references} | <b>OA:</b> {oa_status}"
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{citation_text}", meta_style))
                
                story.append(Spacer(1, 0.15*cm))
                
                if idx < len(cards):
                    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;" + "─" * 40, separator_style))
                    story.append(Spacer(1, 0.1*cm))
            
            story.append(Spacer(1, 0.3*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    # Conclusion
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_cards} retraction cards grouped by {total_countries} countries and their respective affiliations.
    
    The cards are organized by the number of retractions (descending) within each level.
    Each card represents a retracted article, a retraction notice, or a combination of both when available.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using CTA Retraction Article Detector Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_pdf_retraction_report_author(
    journal_name: str,
    years: List[int],
    countries: List[str],
    author_cards: Dict[str, List[dict]],
    logo_path: str = None,
    report_title: str = "Retraction Report by Author"
) -> bytes:
    """Generate PDF report grouping retraction cards by author."""
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
    
    card_title_style = ParagraphStyle(
        'CardTitle',
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
    
    meta_style_retracted = ParagraphStyle(
        'MetaRetracted',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#c0392b'),
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
    
    total_cards = sum(len(cards) for cards in author_cards.values())
    total_authors = len(author_cards)
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo at beginning
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    countries_str = ', '.join([get_full_country_name(c) for c in countries]) if countries else 'All countries'
    story.append(Paragraph(f"Selected countries: {countries_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_cards} retraction cards grouped by Author.
    
    Cards are sorted by the number of retractions per author (descending).
    Each card represents either a retracted article, a retraction notice, or a combination of both.
    Only authors from selected countries are included.
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Cards", str(total_cards)],
        ["Authors", str(total_authors)],
        ["Report Type", report_title],
        ["Period", years_str],
        ["Countries", countries_str]
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
    
    for author, cards in author_cards.items():
        anchor_id = f"author_{hashlib.md5(author.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(author)}</b> — {len(cards)} cards</a>', toc_author_style))
    
    story.append(PageBreak())
    
    # Main content
    for author, cards in author_cards.items():
        anchor_id = f"author_{hashlib.md5(author.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(author)} — {len(cards)} cards", author_style))
        story.append(Spacer(1, 0.3*cm))
        
        for idx, card in enumerate(cards, 1):
            title = clean_text(card.get('title', 'No title'))
            card_type_icon = card.get('card_type_icon', '📄')
            card_type_label = card.get('card_type_label', 'Unknown')
            
            story.append(Paragraph(f"&nbsp;&nbsp;{idx}. {card_type_icon} {title}", card_title_style))
            
            # Card type badge
            if card_type_label == 'Retracted Article + Retraction Notice':
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#c0392b'><b>⚠️🚫 {card_type_label}</b></font>", meta_style_retracted))
            elif card_type_label == 'Retracted Article (No Notice)':
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#c0392b'><b>🚫 {card_type_label}</b></font>", meta_style_retracted))
            elif card_type_label == 'Retraction Notice (No Article)':
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#e74c3c'><b>⚠️ {card_type_label}</b></font>", meta_style_notice))
            
            authors = clean_text(card.get('authors', 'Authors not specified'))
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>All Authors:</b> {authors}", authors_style))
            
            # Affiliations
            affs = clean_text(card.get('affiliations_str', ''))
            if affs and affs != 'No affiliations specified':
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style))
            
            # Journal and publisher
            journal_name_article = clean_text(card.get('journal_name', ''))
            if journal_name_article:
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Journal:</b> {journal_name_article}", meta_style))
            
            publisher = clean_text(card.get('publisher', ''))
            if publisher:
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Publisher:</b> {publisher}", meta_style))
            
            year = card.get('publication_year', '')
            pub_date = card.get('publication_date', '')
            volume = card.get('volume', '')
            issue = card.get('issue', '')
            pages = card.get('pages', '')
            
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
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style))
            
            # DOI for article
            doi_url = card.get('doi_url', '')
            if doi_url:
                doi_url_clean = clean_doi_url(doi_url)
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Article DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style))
            
            # Notice DOIs
            notice_data = card.get('notice_data', [])
            if notice_data:
                for notice_idx, notice in enumerate(notice_data, 1):
                    notice_doi_url = notice.get('doi_url', '')
                    if notice_doi_url:
                        notice_doi_clean = clean_doi_url(notice_doi_url)
                        notice_year = notice.get('year', '')
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Notice {notice_idx} DOI:</b> <a href='{notice_doi_clean}'>{notice_doi_clean}</a> (Year: {notice_year})", meta_style_notice))
            
            # Citations
            citations = card.get('cited_by_count', 0)
            citations_per_year = card.get('citations_per_year', 0)
            references = card.get('referenced_works_count', 0)
            oa_status = card.get('oa_status', 'Closed Access')
            
            citation_text = f"<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f} | <b>References:</b> {references} | <b>OA:</b> {oa_status}"
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{citation_text}", meta_style))
            
            story.append(Spacer(1, 0.15*cm))
            
            if idx < len(cards):
                story.append(Paragraph("&nbsp;&nbsp;" + "─" * 40, separator_style))
                story.append(Spacer(1, 0.1*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    # Conclusion
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_cards} retraction cards grouped by {total_authors} authors.
    
    The cards are organized by the number of retractions per author (descending).
    Each card represents a retracted article, a retraction notice, or a combination of both when available.
    Only authors from selected countries are included.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using CTA Retraction Article Detector Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_pdf_retraction_report_publisher_journal(
    journal_name: str,
    years: List[int],
    countries: List[str],
    hierarchy: Dict[str, Dict[str, List[dict]]],
    logo_path: str = None,
    report_title: str = "Retraction Report by Publisher & Journal"
) -> bytes:
    """Generate PDF report grouping retraction cards by Publisher -> Journal."""
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
    
    card_title_style = ParagraphStyle(
        'CardTitle',
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
    
    meta_style_retracted = ParagraphStyle(
        'MetaRetracted',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#c0392b'),
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
    
    total_cards = sum(len(cards) for publisher in hierarchy.values() 
                      for journal in publisher.values() 
                      for cards in [journal])
    total_publishers = len(hierarchy)
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo at beginning
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    countries_str = ', '.join([get_full_country_name(c) for c in countries]) if countries else 'All countries'
    story.append(Paragraph(f"Selected countries: {countries_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_cards} retraction cards grouped by Publisher and Journal.
    
    Cards are sorted by the number of retractions (descending).
    Each card represents either a retracted article, a retraction notice, or a combination of both.
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Cards", str(total_cards)],
        ["Publishers", str(total_publishers)],
        ["Report Type", report_title],
        ["Period", years_str],
        ["Countries", countries_str]
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
        publisher_articles = sum(len(cards) for cards in journals.values())
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(publisher)}</b> — {publisher_articles} cards</a>', toc_publisher_style))
        
        for journal, cards in journals.items():
            journal_count = len(cards)
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{journal_anchor_id}">{clean_text(journal)}</a> — {journal_count} cards', toc_journal_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # Main content
    for publisher, journals in hierarchy.items():
        publisher_articles = sum(len(cards) for cards in journals.values())
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(publisher)} — {publisher_articles} cards", publisher_style))
        story.append(Spacer(1, 0.3*cm))
        
        for journal, cards in journals.items():
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            journal_anchor_para = Paragraph(f'<a name="{journal_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(journal_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{clean_text(journal)} — {len(cards)} cards", journal_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, card in enumerate(cards, 1):
                title = clean_text(card.get('title', 'No title'))
                card_type_icon = card.get('card_type_icon', '📄')
                card_type_label = card.get('card_type_label', 'Unknown')
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {card_type_icon} {title}", card_title_style))
                
                # Card type badge
                if card_type_label == 'Retracted Article + Retraction Notice':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#c0392b'><b>⚠️🚫 {card_type_label}</b></font>", meta_style_retracted))
                elif card_type_label == 'Retracted Article (No Notice)':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#c0392b'><b>🚫 {card_type_label}</b></font>", meta_style_retracted))
                elif card_type_label == 'Retraction Notice (No Article)':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#e74c3c'><b>⚠️ {card_type_label}</b></font>", meta_style_notice))
                
                authors = clean_text(card.get('authors', 'Authors not specified'))
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors}", authors_style))
                
                # Affiliations
                affs = clean_text(card.get('affiliations_str', ''))
                if affs and affs != 'No affiliations specified':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style))
                
                # Journal and publisher
                journal_name_article = clean_text(card.get('journal_name', ''))
                if journal_name_article:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Journal:</b> {journal_name_article}", meta_style))
                
                publisher_name = clean_text(card.get('publisher', ''))
                if publisher_name:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Publisher:</b> {publisher_name}", meta_style))
                
                year = card.get('publication_year', '')
                pub_date = card.get('publication_date', '')
                volume = card.get('volume', '')
                issue = card.get('issue', '')
                pages = card.get('pages', '')
                
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
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style))
                
                # DOI for article
                doi_url = card.get('doi_url', '')
                if doi_url:
                    doi_url_clean = clean_doi_url(doi_url)
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Article DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style))
                
                # Notice DOIs
                notice_data = card.get('notice_data', [])
                if notice_data:
                    for notice_idx, notice in enumerate(notice_data, 1):
                        notice_doi_url = notice.get('doi_url', '')
                        if notice_doi_url:
                            notice_doi_clean = clean_doi_url(notice_doi_url)
                            notice_year = notice.get('year', '')
                            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Notice {notice_idx} DOI:</b> <a href='{notice_doi_clean}'>{notice_doi_clean}</a> (Year: {notice_year})", meta_style_notice))
                
                # Citations
                citations = card.get('cited_by_count', 0)
                citations_per_year = card.get('citations_per_year', 0)
                references = card.get('referenced_works_count', 0)
                oa_status = card.get('oa_status', 'Closed Access')
                
                citation_text = f"<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f} | <b>References:</b> {references} | <b>OA:</b> {oa_status}"
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{citation_text}", meta_style))
                
                story.append(Spacer(1, 0.15*cm))
                
                if idx < len(cards):
                    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;" + "─" * 40, separator_style))
                    story.append(Spacer(1, 0.1*cm))
            
            story.append(Spacer(1, 0.3*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    # Conclusion
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_cards} retraction cards grouped by {total_publishers} publishers and their respective journals.
    
    The cards are organized by the number of retractions (descending) within each level.
    Each card represents a retracted article, a retraction notice, or a combination of both when available.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using CTA Retraction Article Detector Pro*2", footer_style))
    
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
# UI STEPS
# ============================================================================

def step_retraction_parameters():
    """Step 1: Input retraction search parameters"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📥 Step 1: Search Parameters</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Enter publication years and countries to search for retracted articles.</p>
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
    <div class="filter-section" style="background: rgba(255, 255, 255, 0.9); border-radius: 20px; padding: 20px; margin-top: 20px; border: 1px solid rgba(102, 126, 234, 0.2);">
        <div class="filter-header" style="font-size: 1.1rem; font-weight: 600; color: #495057; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #667eea;">
            🌍 Countries
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.9rem; color: #666; margin-bottom: 10px;">
        <strong>Supported formats:</strong>
    </div>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px;">
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">RU</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">IT</span>
        <span style="background: #fff3e0; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; border: 1px dashed #ff9800;">RU+IT</span>
        <span style="background: #fff3e0; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; border: 1px dashed #ff9800;">IT+RU+CN</span>
    </div>
    <div style="font-size: 0.85rem; color: #888; margin-bottom: 10px;">
        Use '+' to combine multiple countries (e.g., RU+IT+CN)
    </div>
    """, unsafe_allow_html=True)
    
    countries_input = st.text_input(
        "Enter country codes (2-letter ISO codes)",
        value=st.session_state.get('countries_input', ''),
        placeholder="Example: RU or IT+RU or RU+IT+CN",
        help="Use '+' to combine multiple countries"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if countries_input:
        countries = parse_country_filter(countries_input)
        if countries:
            country_names = [get_full_country_name(c) for c in countries]
            st.markdown(f"""
            <div style="background: #e8f5e9; border-radius: 8px; padding: 12px; border-left: 4px solid #4CAF50; margin: 10px 0;">
                <strong>✅ Selected countries:</strong> {', '.join(country_names)} ({', '.join(countries)})
                <br><span style="font-size: 0.85rem; color: #666;">Total: {len(countries)} countries</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #ffebee; border-radius: 8px; padding: 12px; border-left: 4px solid #f44336; margin: 10px 0;">
                <strong>❌ Invalid country codes:</strong> Please use 2-letter ISO codes separated by '+'.
                <br><span style="font-size: 0.85rem; color: #666;">Example: RU, IT, RU+IT, RU+IT+CN</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 Search Retracted Articles", type="primary", use_container_width=True):
            if not years_input:
                st.error("❌ Please enter at least one year.")
                return
            
            years = parse_year_filter(years_input)
            if not years:
                st.error("❌ Invalid year format. Please check your input.")
                return
            
            countries = parse_country_filter(countries_input) if countries_input else []
            
            st.session_state.years_input = years_input
            st.session_state.selected_years = years
            st.session_state.countries_input = countries_input
            st.session_state.selected_countries = countries
            
            # Clear previous results
            if 'retracted_articles' in st.session_state:
                del st.session_state.retracted_articles
            if 'retraction_notices' in st.session_state:
                del st.session_state.retraction_notices
            if 'retraction_cards' in st.session_state:
                del st.session_state.retraction_cards
            if 'filtered_cards' in st.session_state:
                del st.session_state.filtered_cards
            if 'pdf_cache' in st.session_state:
                del st.session_state.pdf_cache
            if 'all_reports_generated' in st.session_state:
                del st.session_state.all_reports_generated
            
            st.session_state.current_step = 2
            st.rerun()

def step_retraction_search():
    """Step 2: Search for retracted articles and notices"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 2: Searching Retracted Articles</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Fetching retracted articles and retraction notices from OpenAlex...</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'selected_years' not in st.session_state:
        st.error("❌ No search parameters. Please go back to Step 1.")
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
            <div class="metric-label">Articles</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">...</div>
            <div class="metric-label">Notices</div>
        </div>
        """, unsafe_allow_html=True)
    
    with st.spinner("Fetching retracted articles..."):
        retracted_articles = fetch_retracted_works_by_years_sync(years)
        st.session_state.retracted_articles = retracted_articles
    
    with st.spinner("Fetching retraction notices..."):
        retraction_notices = fetch_retraction_notices_by_years_sync(years)
        st.session_state.retraction_notices = retraction_notices
    
    # Build retraction cards
    with st.spinner("Building retraction cards..."):
        cards = []
        
        # Track which articles have been matched with notices
        matched_article_dois = set()
        
        # First, match retracted articles with their notices
        for article in retracted_articles:
            article_doi = article.get('doi', '').replace('https://doi.org/', '')
            matching_notices = find_retraction_notices_for_article(article, retraction_notices)
            
            if matching_notices:
                # Article with notices
                card = enrich_retraction_card(article, matching_notices)
                cards.append(card)
                matched_article_dois.add(article_doi)
                
                # Mark notices as matched
                for notice in matching_notices:
                    notice_doi = notice.get('doi', '').replace('https://doi.org/', '')
                    if notice_doi:
                        matched_article_dois.add(notice_doi)
            else:
                # Article without notice
                card = enrich_retraction_card(article, [])
                cards.append(card)
                matched_article_dois.add(article_doi)
        
        # Add notices that don't have matching articles
        for notice in retraction_notices:
            notice_doi = notice.get('doi', '').replace('https://doi.org/', '')
            if notice_doi not in matched_article_dois:
                # Check if this notice might have been matched already
                is_matched = False
                clean_notice_title = extract_clean_title_from_retraction_notice(notice)
                for article in retracted_articles:
                    clean_article_title = extract_clean_title_from_retracted_article(article)
                    if clean_notice_title and clean_article_title:
                        if (clean_notice_title.lower().strip() == clean_article_title.lower().strip() or
                            clean_article_title.lower().strip() in clean_notice_title.lower().strip() or
                            clean_notice_title.lower().strip() in clean_article_title.lower().strip()):
                            is_matched = True
                            break
                
                if not is_matched:
                    card = enrich_retraction_notice_only(notice)
                    cards.append(card)
        
        st.session_state.retraction_cards = cards
        
        # Filter cards by selected countries
        if countries:
            filtered_cards = filter_cards_by_countries(cards, countries)
            st.session_state.filtered_cards = filtered_cards
        else:
            st.session_state.filtered_cards = cards
    
    total_articles = len(retracted_articles)
    total_notices = len(retraction_notices)
    total_cards = len(st.session_state.retraction_cards)
    filtered_count = len(st.session_state.filtered_cards)
    
    st.markdown(f"""
    <div style="background: #e8f5e9; border-radius: 8px; padding: 12px; border-left: 4px solid #4CAF50; margin: 10px 0;">
        <strong>✅ Search Complete!</strong><br>
        Found {total_articles} retracted articles, {total_notices} retraction notices, 
        built {total_cards} cards ({filtered_count} after country filter)
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_articles:,}</div>
            <div class="metric-label">Retracted Articles</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_notices:,}</div>
            <div class="metric-label">Retraction Notices</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_cards:,}</div>
            <div class="metric-label">Total Cards</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{filtered_count:,}</div>
            <div class="metric-label">Filtered Cards</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card type breakdown
    card_types = Counter([card.get('card_type', 'unknown') for card in st.session_state.filtered_cards])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size: 1.3rem;">{card_types.get('retracted_with_notice', 0)}</div>
            <div class="metric-label">⚠️🚫 Article + Notice</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size: 1.3rem;">{card_types.get('retracted_only', 0)}</div>
            <div class="metric-label">🚫 Article Only</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size: 1.3rem;">{card_types.get('notice_only', 0)}</div>
            <div class="metric-label">⚠️ Notice Only</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📊 Generate Reports", type="primary", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()

def step_retraction_results():
    """Step 3: Retraction Results with 3 PDF reports"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📊 Step 3: Retraction Reports</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Download retraction analysis reports.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'filtered_cards' not in st.session_state:
        st.error("❌ No data available. Please go back.")
        return
    
    # Back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    
    cards = st.session_state.filtered_cards
    years = st.session_state.selected_years
    countries = st.session_state.get('selected_countries', [])
    
    if not cards:
        st.warning("⚠️ No cards found after filtering. Try adjusting your search parameters.")
        return
    
    # Generate groupings
    with st.spinner("Generating report groupings..."):
        country_hierarchy = group_cards_by_country_affiliation(cards, countries)
        author_cards = group_cards_by_author(cards, countries)
        publisher_hierarchy = group_cards_by_publisher_journal(cards)
    
    total_cards = len(cards)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_cards:,}</div>
            <div class="metric-label">Total Cards</div>
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
            <div class="metric-value">{len(author_cards)}</div>
            <div class="metric-label">Authors</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📥 Download Reports")
    
    journal_name = "Retraction Analysis"
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
    
    # Create unique cache keys
    filter_hash = hashlib.md5(str(sorted([card.get('doi', '') for card in cards])).encode()).hexdigest()[:8]
    years_hash = hashlib.md5(','.join(map(str, years)).encode()).hexdigest()[:8]
    countries_hash = hashlib.md5(','.join(sorted(countries)).encode()).hexdigest()[:8] if countries else 'all'
    
    cache_key_country = f"retract_country_{years_hash}_{countries_hash}_{filter_hash}"
    cache_key_author = f"retract_author_{years_hash}_{countries_hash}_{filter_hash}"
    cache_key_publisher = f"retract_publisher_{years_hash}_{countries_hash}_{filter_hash}"
    
    st.markdown("---")
    
    col_gen1, col_gen2, col_gen3 = st.columns([1, 1, 1])
    with col_gen2:
        if not st.session_state.all_reports_generated:
            if st.button("⚡ Generate All Reports", type="primary", use_container_width=True):
                with st.spinner("Generating all reports..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("Generating Country → Affiliation report...")
                    if cache_key_country not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_country] = generate_pdf_retraction_report_country_affiliation(
                            journal_name, years, countries,
                            country_hierarchy, logo_path,
                            "Retraction Report by Country & Affiliation"
                        )
                    progress_bar.progress(0.33)
                    
                    status_text.text("Generating Author report...")
                    if cache_key_author not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_author] = generate_pdf_retraction_report_author(
                            journal_name, years, countries,
                            author_cards, logo_path,
                            "Retraction Report by Author"
                        )
                    progress_bar.progress(0.66)
                    
                    status_text.text("Generating Publisher → Journal report...")
                    if cache_key_publisher not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_publisher] = generate_pdf_retraction_report_publisher_journal(
                            journal_name, years, countries,
                            publisher_hierarchy, logo_path,
                            "Retraction Report by Publisher & Journal"
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
        st.markdown("*Sorted by card count*")
        
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
                    pdf_data = generate_pdf_retraction_report_country_affiliation(
                        journal_name, years, countries,
                        country_hierarchy, logo_path,
                        "Retraction Report by Country & Affiliation"
                    )
                    st.session_state.pdf_cache[cache_key_country] = pdf_data
                    st.rerun()
    
    with col2:
        st.markdown("**👤 Report 2: By Author**")
        st.markdown("*Sorted by card count*")
        
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
                    pdf_data = generate_pdf_retraction_report_author(
                        journal_name, years, countries,
                        author_cards, logo_path,
                        "Retraction Report by Author"
                    )
                    st.session_state.pdf_cache[cache_key_author] = pdf_data
                    st.rerun()
    
    with col3:
        st.markdown("**📚 Report 3: Publisher → Journal**")
        st.markdown("*Sorted by card count*")
        
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
                    pdf_data = generate_pdf_retraction_report_publisher_journal(
                        journal_name, years, countries,
                        publisher_hierarchy, logo_path,
                        "Retraction Report by Publisher & Journal"
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
                        'selected_countries', 'retracted_articles', 'retraction_notices',
                        'retraction_cards', 'filtered_cards', 'pdf_cache', 'all_reports_generated']
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
        step_retraction_parameters()
    elif st.session_state.current_step == 2:
        step_retraction_search()
    elif st.session_state.current_step == 3:
        step_retraction_results()
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>© CTA, https://chimicatechnoacta.ru / developed by daM©</p>
        <p style="font-size: 0.7rem; color: #aaa;">CTA Retraction Article Detector Pro*2 with multi-report generation</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
