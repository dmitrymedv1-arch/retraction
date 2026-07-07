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
    page_title="CTA Retraction Detector Pro*2",
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
    
    /* Retraction badge */
    .retraction-badge {
        display: inline-block;
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        color: white;
    }
    
    .notice-badge {
        display: inline-block;
        background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        color: white;
    }
    
    .combined-badge {
        display: inline-block;
        background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        color: white;
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
    """
    if not country_input or country_input.strip() == "":
        return []
    
    countries = []
    parts = country_input.split('+')
    
    for part in parts:
        part = part.strip().upper()
        if part and len(part) >= 2:
            countries.append(part)
    
    return countries

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
        'CG': 'Congo', 'CD': 'Democratic Republic of the Congo', 'CR': 'Costa Rica',
        'HR': 'Croatia', 'CU': 'Cuba', 'CY': 'Cyprus', 'CZ': 'Czech Republic',
        'DK': 'Denmark', 'DJ': 'Djibouti', 'DM': 'Dominica', 'DO': 'Dominican Republic',
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
        'LI': 'Liechtenstein', 'LT': 'Lithuania', 'LU': 'Luxembourg', 'MK': 'North Macedonia',
        'MG': 'Madagascar', 'MW': 'Malawi', 'MY': 'Malaysia', 'MV': 'Maldives',
        'ML': 'Mali', 'MT': 'Malta', 'MH': 'Marshall Islands', 'MR': 'Mauritania',
        'MU': 'Mauritius', 'MX': 'Mexico', 'FM': 'Micronesia', 'MD': 'Moldova',
        'MC': 'Monaco', 'MN': 'Mongolia', 'ME': 'Montenegro', 'MA': 'Morocco',
        'MZ': 'Mozambique', 'MM': 'Myanmar', 'NA': 'Namibia', 'NR': 'Nauru',
        'NP': 'Nepal', 'NL': 'Netherlands', 'NZ': 'New Zealand', 'NI': 'Nicaragua',
        'NE': 'Niger', 'NG': 'Nigeria', 'NO': 'Norway', 'OM': 'Oman',
        'PK': 'Pakistan', 'PW': 'Palau', 'PA': 'Panama', 'PG': 'Papua New Guinea',
        'PY': 'Paraguay', 'PE': 'Peru', 'PH': 'Philippines', 'PL': 'Poland',
        'PT': 'Portugal', 'QA': 'Qatar', 'RO': 'Romania', 'RU': 'Russia',
        'RW': 'Rwanda', 'KN': 'Saint Kitts and Nevis', 'LC': 'Saint Lucia',
        'VC': 'Saint Vincent and the Grenadines', 'WS': 'Samoa', 'SM': 'San Marino',
        'ST': 'Sao Tome and Principe', 'SA': 'Saudi Arabia', 'SN': 'Senegal',
        'RS': 'Serbia', 'SC': 'Seychelles', 'SL': 'Sierra Leone', 'SG': 'Singapore',
        'SK': 'Slovakia', 'SI': 'Slovenia', 'SB': 'Solomon Islands', 'SO': 'Somalia',
        'ZA': 'South Africa', 'SS': 'South Sudan', 'ES': 'Spain', 'LK': 'Sri Lanka',
        'SD': 'Sudan', 'SR': 'Suriname', 'SZ': 'Eswatini', 'SE': 'Sweden',
        'CH': 'Switzerland', 'SY': 'Syria', 'TW': 'Taiwan', 'TJ': 'Tajikistan',
        'TZ': 'Tanzania', 'TH': 'Thailand', 'TL': 'Timor-Leste', 'TG': 'Togo',
        'TO': 'Tonga', 'TT': 'Trinidad and Tobago', 'TN': 'Tunisia', 'TR': 'Turkey',
        'TM': 'Turkmenistan', 'TV': 'Tuvalu', 'UG': 'Uganda', 'UA': 'Ukraine',
        'AE': 'United Arab Emirates', 'GB': 'United Kingdom', 'US': 'United States',
        'UY': 'Uruguay', 'UZ': 'Uzbekistan', 'VU': 'Vanuatu', 'VA': 'Vatican City',
        'VE': 'Venezuela', 'VN': 'Vietnam', 'YE': 'Yemen', 'ZM': 'Zambia',
        'ZW': 'Zimbabwe'
    }
    
    return country_names.get(country_code.upper(), country_code.upper())

# ============================================================================
# RETRACTION DETECTION FUNCTIONS
# ============================================================================

def is_retraction_notice(work: dict) -> bool:
    """
    Check if a work is a retraction notice.
    Looks for type "erratum" and retraction-related keywords in display_name.
    """
    if not work:
        return False
    
    work_type = work.get('type', '').lower()
    
    # Check if type is erratum or retraction
    if work_type not in ['erratum', 'retraction']:
        return False
    
    # Check display_name for retraction keywords
    display_name = work.get('display_name', '')
    if not display_name:
        return False
    
    retraction_keywords = ['retraction', 'retracted', 'withdrawal']
    display_lower = display_name.lower()
    
    for keyword in retraction_keywords:
        if keyword in display_lower:
            return True
    
    return False

def is_retracted_article(work: dict) -> bool:
    """
    Check if a work is a retracted article.
    """
    if not work:
        return False
    
    return work.get('is_retracted', False)

def extract_clean_title(title: str) -> str:
    """
    Extract clean title from retraction notice or retracted article.
    Removes prefixes like "RETRACTED:", "Retraction Notice to", etc.
    """
    if not title:
        return ""
    
    clean_title = title
    
    # Remove common prefixes
    prefixes_to_remove = [
        r'^Retraction Notice to\s*["\']?',
        r'^RETRACTED:\s*["\']?',
        r'^Retraction:\s*["\']?',
        r'^Withdrawal:\s*["\']?',
        r'^Notice of Retraction:\s*["\']?',
        r'^Retracted:\s*["\']?',
    ]
    
    for prefix in prefixes_to_remove:
        clean_title = re.sub(prefix, '', clean_title, flags=re.IGNORECASE)
    
    # Remove surrounding quotes
    clean_title = clean_title.strip()
    if clean_title.startswith('"') and clean_title.endswith('"'):
        clean_title = clean_title[1:-1]
    if clean_title.startswith('“') and clean_title.endswith('”'):
        clean_title = clean_title[1:-1]
    if clean_title.startswith('"') and clean_title.endswith('"'):
        clean_title = clean_title[1:-1]
    
    return clean_title.strip()

def find_matching_retracted_article(notice: dict, retracted_articles: List[dict]) -> Optional[dict]:
    """
    Find retracted article that matches a retraction notice by title similarity.
    """
    if not notice or not retracted_articles:
        return None
    
    notice_title = notice.get('display_name', '')
    if not notice_title:
        return None
    
    clean_notice_title = extract_clean_title(notice_title)
    if not clean_notice_title:
        return None
    
    # Try to find exact match first
    for article in retracted_articles:
        article_title = article.get('display_name', '')
        if not article_title:
            continue
        
        clean_article_title = extract_clean_title(article_title)
        if not clean_article_title:
            continue
        
        # Check if clean titles match
        if clean_notice_title.lower() == clean_article_title.lower():
            return article
        
        # Check if notice title contains article title (or vice versa)
        if len(clean_notice_title) > 20 and len(clean_article_title) > 20:
            if clean_article_title.lower() in clean_notice_title.lower():
                return article
            if clean_notice_title.lower() in clean_article_title.lower():
                return article
    
    # Try fuzzy matching if no exact match found
    for article in retracted_articles:
        article_title = article.get('display_name', '')
        if not article_title:
            continue
        
        clean_article_title = extract_clean_title(article_title)
        if not clean_article_title:
            continue
        
        # Check for significant overlap (more than 50% of words match)
        notice_words = set(clean_notice_title.lower().split())
        article_words = set(clean_article_title.lower().split())
        
        if not notice_words or not article_words:
            continue
        
        common_words = notice_words.intersection(article_words)
        min_len = min(len(notice_words), len(article_words))
        
        # If more than 50% of words match and at least 3 common words
        if len(common_words) >= min_len * 0.5 and len(common_words) >= 3:
            return article
    
    return None

def group_retraction_cards(retracted_articles: List[dict], retraction_notices: List[dict], 
                          selected_countries: List[str]) -> List[dict]:
    """
    Group retracted articles and retraction notices into cards.
    Each card can contain:
    - One retracted article (with optional notices)
    - One retraction notice (without matching article)
    """
    cards = []
    
    # Process notices first - try to match with articles
    matched_article_ids = set()
    matched_notice_ids = set()
    
    for notice in retraction_notices:
        matching_article = find_matching_retracted_article(notice, retracted_articles)
        
        if matching_article:
            article_id = matching_article.get('id', '')
            notice_id = notice.get('id', '')
            
            # Check if article is in selected countries
            if selected_countries:
                article_countries = extract_all_countries_from_work(matching_article)
                if not any(c in article_countries for c in selected_countries):
                    # If article doesn't have selected countries, skip notice
                    continue
            
            # Check if already matched
            existing_card = None
            for card in cards:
                if card.get('article_id') == article_id:
                    existing_card = card
                    break
            
            if existing_card:
                # Add notice to existing card
                if 'notices' not in existing_card:
                    existing_card['notices'] = []
                if notice_id not in [n.get('id', '') for n in existing_card['notices']]:
                    existing_card['notices'].append(notice)
            else:
                # Create new card with article and notice
                cards.append({
                    'article': matching_article,
                    'article_id': article_id,
                    'notices': [notice],
                    'type': 'combined'
                })
            
            matched_article_ids.add(article_id)
            matched_notice_ids.add(notice_id)
        else:
            # Notice without matching article
            notice_id = notice.get('id', '')
            
            # Check if notice has selected countries
            if selected_countries:
                notice_countries = extract_all_countries_from_work(notice)
                if not any(c in notice_countries for c in selected_countries):
                    continue
            
            cards.append({
                'article': None,
                'article_id': None,
                'notices': [notice],
                'type': 'notice_only'
            })
            matched_notice_ids.add(notice_id)
    
    # Process remaining articles (without notices)
    for article in retracted_articles:
        article_id = article.get('id', '')
        
        if article_id in matched_article_ids:
            continue
        
        # Check if article has selected countries
        if selected_countries:
            article_countries = extract_all_countries_from_work(article)
            if not any(c in article_countries for c in selected_countries):
                continue
        
        cards.append({
            'article': article,
            'article_id': article_id,
            'notices': [],
            'type': 'article_only'
        })
    
    return cards

def extract_all_countries_from_work(work: dict) -> List[str]:
    """
    Extract all country codes from a work's authorships.
    """
    if not work:
        return []
    
    countries = set()
    authorships = work.get('authorships', [])
    
    for authorship in authorships:
        if authorship:
            # Get countries from institutions
            for inst in authorship.get('institutions', []):
                if inst:
                    country = inst.get('country_code')
                    if country:
                        countries.add(country.upper())
            
            # Also check countries field
            for country in authorship.get('countries', []):
                if country:
                    countries.add(country.upper())
    
    return list(countries)

def extract_all_authors_with_countries(work: dict, selected_countries: List[str] = None) -> List[Dict]:
    """
    Extract all authors with their country affiliations.
    If selected_countries provided, only return authors from those countries.
    """
    if not work:
        return []
    
    authors = []
    authorships = work.get('authorships', [])
    
    for authorship in authorships:
        if not authorship:
            continue
        
        author = authorship.get('author', {})
        if not author:
            continue
        
        author_name = author.get('display_name', '')
        if not author_name:
            continue
        
        # Get countries for this author
        author_countries = set()
        for inst in authorship.get('institutions', []):
            if inst:
                country = inst.get('country_code')
                if country:
                    author_countries.add(country.upper())
        
        for country in authorship.get('countries', []):
            if country:
                author_countries.add(country.upper())
        
        # Filter by selected countries if provided
        if selected_countries:
            if not any(c in selected_countries for c in author_countries):
                continue
        
        authors.append({
            'name': author_name,
            'countries': list(author_countries),
            'orcid': author.get('orcid', '')
        })
    
    return authors

def extract_authors_by_country(work: dict, selected_countries: List[str]) -> List[str]:
    """
    Extract author names from a work that belong to selected countries.
    """
    if not work or not selected_countries:
        return []
    
    authors = []
    authorships = work.get('authorships', [])
    
    for authorship in authorships:
        if not authorship:
            continue
        
        author = authorship.get('author', {})
        if not author:
            continue
        
        author_name = author.get('display_name', '')
        if not author_name:
            continue
        
        # Check if author has selected country
        has_selected_country = False
        for inst in authorship.get('institutions', []):
            if inst:
                country = inst.get('country_code')
                if country and country.upper() in [c.upper() for c in selected_countries]:
                    has_selected_country = True
                    break
        
        if has_selected_country:
            authors.append(author_name)
    
    return authors

def get_author_lastname_initial(author_name: str) -> str:
    """
    Extract last name and first initial from author name.
    Example: "Eva Andreuzzi" -> "Andreuzzi E."
    """
    if not author_name:
        return ""
    
    parts = author_name.strip().split()
    if not parts:
        return ""
    
    # Get last part as last name
    last_name = parts[-1]
    
    # Get first initial
    first_initial = ""
    if len(parts) >= 2:
        first_name = parts[0]
        if first_name:
            first_initial = first_name[0].upper()
    
    return f"{last_name} {first_initial}."

def extract_publisher_info(work: dict) -> str:
    """
    Extract publisher name from work.
    """
    if not work:
        return "Unknown Publisher"
    
    primary_location = work.get('primary_location', {})
    if primary_location:
        source = primary_location.get('source', {})
        if source:
            publisher = source.get('host_organization_name', '')
            if publisher:
                return publisher
    
    # Try from publisher field
    publisher = work.get('publisher', '')
    if publisher:
        return publisher
    
    return "Unknown Publisher"

def extract_journal_info(work: dict) -> str:
    """
    Extract journal name from work.
    """
    if not work:
        return "Unknown Journal"
    
    primary_location = work.get('primary_location', {})
    if primary_location:
        source = primary_location.get('source', {})
        if source:
            journal = source.get('display_name', '')
            if journal:
                return journal
    
    # Try from journal field
    journal = work.get('journal', '')
    if journal:
        if isinstance(journal, dict):
            return journal.get('display_name', 'Unknown Journal')
        return str(journal)
    
    return "Unknown Journal"

def extract_biblio_info(work: dict) -> Dict:
    """
    Extract bibliographic information from work.
    """
    biblio = work.get('biblio', {})
    return {
        'volume': biblio.get('volume', ''),
        'issue': biblio.get('issue', ''),
        'first_page': biblio.get('first_page', ''),
        'last_page': biblio.get('last_page', '')
    }

def format_card_doi_info(card: dict) -> Dict:
    """
    Format DOI information for a card.
    Returns dict with article_doi and notice_dois.
    """
    result = {
        'article_doi': '',
        'article_doi_url': '',
        'notice_dois': [],
        'notice_doi_urls': []
    }
    
    if card.get('article'):
        doi = card['article'].get('doi', '')
        if doi:
            result['article_doi'] = doi.replace('https://doi.org/', '')
            result['article_doi_url'] = doi
    
    for notice in card.get('notices', []):
        doi = notice.get('doi', '')
        if doi:
            result['notice_dois'].append(doi.replace('https://doi.org/', ''))
            result['notice_doi_urls'].append(doi)
    
    return result

# ============================================================================
# RETRACTION REPORT GENERATION FUNCTIONS
# ============================================================================

def generate_retraction_pdf_by_country(cards: List[dict], selected_countries: List[str],
                                       years: List[int], logo_path: str = None,
                                       report_title: str = "Retraction Report by Country & Affiliation",
                                       sort_option: str = 'by_count') -> bytes:
    """
    Generate PDF report grouping retraction cards by Country -> Affiliation.
    Only shows countries from selected_countries.
    """
    russian_font_name = get_pdf_font_name()
    
    # Build hierarchy: country -> affiliation -> cards
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for card in cards:
        # Get countries from card (article or notices)
        card_countries = set()
        
        # Get from article
        if card.get('article'):
            article_countries = extract_all_countries_from_work(card['article'])
            card_countries.update(article_countries)
        
        # Get from notices
        for notice in card.get('notices', []):
            notice_countries = extract_all_countries_from_work(notice)
            card_countries.update(notice_countries)
        
        # Filter by selected countries
        filtered_countries = [c for c in card_countries if c.upper() in [sc.upper() for sc in selected_countries]]
        
        if not filtered_countries:
            continue
        
        # For each country, extract affiliations
        for country in filtered_countries:
            # Get affiliations for this country
            affiliations = set()
            
            # From article
            if card.get('article'):
                authorships = card['article'].get('authorships', [])
                for authorship in authorships:
                    for inst in authorship.get('institutions', []):
                        country_code = inst.get('country_code')
                        if inst and country_code and country_code.upper() == country.upper():
                            aff_name = inst.get('display_name', 'Unknown Affiliation')
                            if aff_name:
                                affiliations.add(aff_name)
            
            # From notices
            for notice in card.get('notices', []):
                authorships = notice.get('authorships', [])
                for authorship in authorships:
                    for inst in authorship.get('institutions', []):
                        country_code = inst.get('country_code')
                        if inst and country_code and country_code.upper() == country.upper():
                            aff_name = inst.get('display_name', 'Unknown Affiliation')
                            if aff_name:
                                affiliations.add(aff_name)
            
            if not affiliations:
                affiliations.add('Unknown Affiliation')
            
            for affiliation in affiliations:
                hierarchy[country][affiliation].append(card)
    
    # Sort hierarchy by count (descending)
    sorted_hierarchy = {}
    country_items = []
    for country in hierarchy.keys():
        total_count = sum(len(cards) for cards in hierarchy[country].values())
        country_items.append((country, total_count))
    country_items.sort(key=lambda x: x[1], reverse=True)
    
    for country, _ in country_items:
        sorted_hierarchy[country] = {}
        aff_items = []
        for affiliation in hierarchy[country].keys():
            aff_items.append((affiliation, len(hierarchy[country][affiliation])))
        aff_items.sort(key=lambda x: x[1], reverse=True)
        for affiliation, _ in aff_items:
            sorted_hierarchy[country][affiliation] = hierarchy[country][affiliation]
    
    # Generate PDF
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
    
    badge_style = ParagraphStyle(
        'BadgeStyle',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=3,
        leftIndent=40,
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
    
    story = []
    
    total_cards = len(cards)
    total_countries = len(sorted_hierarchy)
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"Report by Country & Affiliation", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    countries_str = '+'.join(selected_countries)
    story.append(Paragraph(f"Period: {years_str} | Countries: {countries_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_cards} retraction-related cards,
    grouped by Country and Affiliation.
    
    Only countries from the selection ({countries_str}) are shown.
    Each card may contain:
    - A retracted article (with optional retraction notices)
    - A retraction notice (without matching article)
    
    <b>Sorting:</b> By number of cards (descending)
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Cards", str(total_cards)],
        ["Countries", str(total_countries)],
        ["Report Type", report_title],
        ["Sorting", "By Count (Descending)"]
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
    
    for country, affiliations in sorted_hierarchy.items():
        country_articles = sum(len(cards) for cards in affiliations.values())
        country_name = get_country_name(country)
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{country_name}</b> — {country_articles} cards</a>', toc_country_style))
        
        for affiliation, cards in affiliations.items():
            aff_cards = len(cards)
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{aff_anchor_id}">{affiliation}</a> — {aff_cards} cards', toc_affiliation_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # Main content
    for country, affiliations in sorted_hierarchy.items():
        country_articles = sum(len(cards) for cards in affiliations.values())
        country_name = get_country_name(country)
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{country_name} — {country_articles} cards", country_style))
        story.append(Spacer(1, 0.3*cm))
        
        for affiliation, cards in affiliations.items():
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            aff_anchor_para = Paragraph(f'<a name="{aff_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(aff_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{affiliation} — {len(cards)} cards", affiliation_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, card in enumerate(cards, 1):
                # Card type badge
                if card['type'] == 'combined':
                    badge_text = "🔴 RETRACTED ARTICLE + NOTICE"
                    badge_color = "#e17055"
                elif card['type'] == 'article_only':
                    badge_text = "🔴 RETRACTED ARTICLE (without notice)"
                    badge_color = "#ff6b6b"
                else:
                    badge_text = "🟡 RETRACTION NOTICE (without article)"
                    badge_color = "#fdcb6e"
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. <font color='{badge_color}'><b>{badge_text}</b></font>", badge_style))
                
                # Title
                if card.get('article'):
                    title = clean_text(card['article'].get('display_name', card['article'].get('title', 'No title')))
                else:
                    title = clean_text(card['notices'][0].get('display_name', card['notices'][0].get('title', 'No title')))
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{title}", card_title_style))
                
                # Authors
                all_authors = []
                if card.get('article'):
                    authors = extract_all_authors_with_countries(card['article'], selected_countries)
                    all_authors.extend([a['name'] for a in authors])
                
                for notice in card.get('notices', []):
                    authors = extract_all_authors_with_countries(notice, selected_countries)
                    all_authors.extend([a['name'] for a in authors])
                
                # Remove duplicates while preserving order
                seen_authors = set()
                unique_authors = []
                for author in all_authors:
                    if author not in seen_authors:
                        seen_authors.add(author)
                        unique_authors.append(author)
                
                if unique_authors:
                    authors_str = ', '.join(unique_authors)
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors_str}", authors_style))
                
                # Journal and publisher
                if card.get('article'):
                    journal = extract_journal_info(card['article'])
                    publisher = extract_publisher_info(card['article'])
                else:
                    journal = extract_journal_info(card['notices'][0])
                    publisher = extract_publisher_info(card['notices'][0])
                
                if journal:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Journal:</b> {journal}", meta_style))
                if publisher:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Publisher:</b> {publisher}", meta_style))
                
                # Bibliographic info
                if card.get('article'):
                    biblio = extract_biblio_info(card['article'])
                else:
                    biblio = extract_biblio_info(card['notices'][0])
                
                meta_parts = []
                
                # Publication year and date
                if card.get('article'):
                    year = card['article'].get('publication_year', '')
                    pub_date = card['article'].get('publication_date', '')
                else:
                    year = card['notices'][0].get('publication_year', '')
                    pub_date = card['notices'][0].get('publication_date', '')
                
                if year:
                    meta_parts.append(str(year))
                if pub_date and pub_date != '0000-00-00':
                    meta_parts.append(f"({pub_date})")
                if biblio.get('volume'):
                    meta_parts.append(f"Vol. {biblio['volume']}")
                if biblio.get('issue'):
                    meta_parts.append(f"Iss. {biblio['issue']}")
                if biblio.get('first_page') and biblio.get('last_page'):
                    meta_parts.append(f"pp. {biblio['first_page']}-{biblio['last_page']}")
                elif biblio.get('first_page'):
                    meta_parts.append(f"p. {biblio['first_page']}")
                
                if meta_parts:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style))
                
                # DOI information
                doi_info = format_card_doi_info(card)
                
                if doi_info['article_doi_url']:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Retracted Article DOI:</b> <a href='{clean_doi_url(doi_info['article_doi_url'])}'>{doi_info['article_doi']}</a>", meta_style))
                
                if doi_info['notice_doi_urls']:
                    for notice_doi_url in doi_info['notice_doi_urls']:
                        notice_doi = notice_doi_url.replace('https://doi.org/', '')
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Retraction Notice DOI:</b> <a href='{clean_doi_url(notice_doi_url)}'>{notice_doi}</a>", meta_style))
                
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
    This report contains {total_cards} retraction-related cards,
    grouped by {total_countries} countries and their respective affiliations.
    
    The report shows only countries from the selection ({countries_str}).
    Each card represents either a retracted article, a retraction notice,
    or a combination of both when available.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using CTA Retraction Detector Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_retraction_pdf_by_author(cards: List[dict], selected_countries: List[str],
                                      years: List[int], logo_path: str = None,
                                      report_title: str = "Retraction Report by Author",
                                      sort_option: str = 'by_count') -> bytes:
    """
    Generate PDF report grouping retraction cards by Author.
    Only shows authors from selected countries.
    """
    russian_font_name = get_pdf_font_name()
    
    # Build hierarchy: author -> cards
    hierarchy = defaultdict(list)
    
    for card in cards:
        # Get authors from card (article or notices) that belong to selected countries
        card_authors = []
        
        if card.get('article'):
            authors = extract_all_authors_with_countries(card['article'], selected_countries)
            for author in authors:
                author_key = get_author_lastname_initial(author['name'])
                if author_key:
                    card_authors.append(author_key)
        
        for notice in card.get('notices', []):
            authors = extract_all_authors_with_countries(notice, selected_countries)
            for author in authors:
                author_key = get_author_lastname_initial(author['name'])
                if author_key:
                    card_authors.append(author_key)
        
        # Remove duplicates for this card
        for author_key in set(card_authors):
            hierarchy[author_key].append(card)
    
    # Sort by count (descending)
    sorted_authors = sorted(hierarchy.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Generate PDF
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
    
    card_title_style = ParagraphStyle(
        'CardTitle',
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
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=2,
        leftIndent=20,
        fontName=russian_font_name
    )
    
    badge_style = ParagraphStyle(
        'BadgeStyle',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=3,
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
    
    toc_author_style = ParagraphStyle(
        'TOCAuthorStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=5,
        fontName=russian_font_name
    )
    
    story = []
    
    total_cards = len(cards)
    total_authors = len(sorted_authors)
    
    story.append(Spacer(1, 2*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"Report by Author", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    countries_str = '+'.join(selected_countries)
    story.append(Paragraph(f"Period: {years_str} | Countries: {countries_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_cards} retraction-related cards,
    grouped by Author.
    
    Only authors from the selected countries ({countries_str}) are shown.
    Each card may contain:
    - A retracted article (with optional retraction notices)
    - A retraction notice (without matching article)
    
    <b>Sorting:</b> By number of cards (descending)
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Cards", str(total_cards)],
        ["Authors", str(total_authors)],
        ["Report Type", report_title],
        ["Sorting", "By Count (Descending)"]
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
    
    for author, cards in sorted_authors:
        author_cards = len(cards)
        anchor_id = f"author_{hashlib.md5(author.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{author}</b> — {author_cards} cards</a>', toc_author_style))
    
    story.append(PageBreak())
    
    # Main content
    for author, cards in sorted_authors:
        author_cards = len(cards)
        anchor_id = f"author_{hashlib.md5(author.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{author} — {author_cards} cards", author_style))
        story.append(Spacer(1, 0.3*cm))
        
        for idx, card in enumerate(cards, 1):
            # Card type badge
            if card['type'] == 'combined':
                badge_text = "🔴 RETRACTED ARTICLE + NOTICE"
                badge_color = "#e17055"
            elif card['type'] == 'article_only':
                badge_text = "🔴 RETRACTED ARTICLE (without notice)"
                badge_color = "#ff6b6b"
            else:
                badge_text = "🟡 RETRACTION NOTICE (without article)"
                badge_color = "#fdcb6e"
            
            story.append(Paragraph(f"&nbsp;&nbsp;{idx}. <font color='{badge_color}'><b>{badge_text}</b></font>", badge_style))
            
            # Title
            if card.get('article'):
                title = clean_text(card['article'].get('display_name', card['article'].get('title', 'No title')))
            else:
                title = clean_text(card['notices'][0].get('display_name', card['notices'][0].get('title', 'No title')))
            
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{title}", card_title_style))
            
            # Authors (only those from selected countries)
            all_authors = []
            if card.get('article'):
                authors = extract_all_authors_with_countries(card['article'], selected_countries)
                all_authors.extend([a['name'] for a in authors])
            
            for notice in card.get('notices', []):
                authors = extract_all_authors_with_countries(notice, selected_countries)
                all_authors.extend([a['name'] for a in authors])
            
            seen_authors = set()
            unique_authors = []
            for author_name in all_authors:
                if author_name not in seen_authors:
                    seen_authors.add(author_name)
                    unique_authors.append(author_name)
            
            if unique_authors:
                authors_str = ', '.join(unique_authors)
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors_str}", authors_style))
            
            # Journal and publisher
            if card.get('article'):
                journal = extract_journal_info(card['article'])
                publisher = extract_publisher_info(card['article'])
            else:
                journal = extract_journal_info(card['notices'][0])
                publisher = extract_publisher_info(card['notices'][0])
            
            if journal:
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Journal:</b> {journal}", meta_style))
            if publisher:
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Publisher:</b> {publisher}", meta_style))
            
            # Bibliographic info
            if card.get('article'):
                biblio = extract_biblio_info(card['article'])
            else:
                biblio = extract_biblio_info(card['notices'][0])
            
            meta_parts = []
            
            if card.get('article'):
                year = card['article'].get('publication_year', '')
                pub_date = card['article'].get('publication_date', '')
            else:
                year = card['notices'][0].get('publication_year', '')
                pub_date = card['notices'][0].get('publication_date', '')
            
            if year:
                meta_parts.append(str(year))
            if pub_date and pub_date != '0000-00-00':
                meta_parts.append(f"({pub_date})")
            if biblio.get('volume'):
                meta_parts.append(f"Vol. {biblio['volume']}")
            if biblio.get('issue'):
                meta_parts.append(f"Iss. {biblio['issue']}")
            if biblio.get('first_page') and biblio.get('last_page'):
                meta_parts.append(f"pp. {biblio['first_page']}-{biblio['last_page']}")
            elif biblio.get('first_page'):
                meta_parts.append(f"p. {biblio['first_page']}")
            
            if meta_parts:
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style))
            
            # DOI information
            doi_info = format_card_doi_info(card)
            
            if doi_info['article_doi_url']:
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Retracted Article DOI:</b> <a href='{clean_doi_url(doi_info['article_doi_url'])}'>{doi_info['article_doi']}</a>", meta_style))
            
            if doi_info['notice_doi_urls']:
                for notice_doi_url in doi_info['notice_doi_urls']:
                    notice_doi = notice_doi_url.replace('https://doi.org/', '')
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Retraction Notice DOI:</b> <a href='{clean_doi_url(notice_doi_url)}'>{notice_doi}</a>", meta_style))
            
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
    This report contains {total_cards} retraction-related cards,
    grouped by {total_authors} authors.
    
    The report shows only authors from the selected countries ({countries_str}).
    Each card represents either a retracted article, a retraction notice,
    or a combination of both when available.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using CTA Retraction Detector Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_retraction_pdf_by_publisher_journal(cards: List[dict], selected_countries: List[str],
                                                 years: List[int], logo_path: str = None,
                                                 report_title: str = "Retraction Report by Publisher & Journal",
                                                 sort_option: str = 'by_count') -> bytes:
    """
    Generate PDF report grouping retraction cards by Publisher -> Journal.
    """
    russian_font_name = get_pdf_font_name()
    
    # Build hierarchy: publisher -> journal -> cards
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for card in cards:
        # Get publisher and journal from card (article or notices)
        if card.get('article'):
            publisher = extract_publisher_info(card['article'])
            journal = extract_journal_info(card['article'])
        else:
            publisher = extract_publisher_info(card['notices'][0])
            journal = extract_journal_info(card['notices'][0])
        
        hierarchy[publisher][journal].append(card)
    
    # Sort by count (descending)
    sorted_hierarchy = {}
    publisher_items = []
    for publisher in hierarchy.keys():
        total_count = sum(len(cards) for cards in hierarchy[publisher].values())
        publisher_items.append((publisher, total_count))
    publisher_items.sort(key=lambda x: x[1], reverse=True)
    
    for publisher, _ in publisher_items:
        sorted_hierarchy[publisher] = {}
        journal_items = []
        for journal in hierarchy[publisher].keys():
            journal_items.append((journal, len(hierarchy[publisher][journal])))
        journal_items.sort(key=lambda x: x[1], reverse=True)
        for journal, _ in journal_items:
            sorted_hierarchy[publisher][journal] = hierarchy[publisher][journal]
    
    # Generate PDF
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
    
    badge_style = ParagraphStyle(
        'BadgeStyle',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=3,
        leftIndent=40,
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
    
    story = []
    
    total_cards = len(cards)
    total_publishers = len(sorted_hierarchy)
    
    story.append(Spacer(1, 2*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"Report by Publisher & Journal", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    countries_str = '+'.join(selected_countries)
    story.append(Paragraph(f"Period: {years_str} | Countries: {countries_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_cards} retraction-related cards,
    grouped by Publisher and Journal.
    
    Each card may contain:
    - A retracted article (with optional retraction notices)
    - A retraction notice (without matching article)
    
    <b>Sorting:</b> By number of cards (descending)
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Cards", str(total_cards)],
        ["Publishers", str(total_publishers)],
        ["Report Type", report_title],
        ["Sorting", "By Count (Descending)"]
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
    
    for publisher, journals in sorted_hierarchy.items():
        publisher_cards = sum(len(cards) for cards in journals.values())
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{publisher}</b> — {publisher_cards} cards</a>', toc_publisher_style))
        
        for journal, cards in journals.items():
            journal_cards = len(cards)
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{journal_anchor_id}">{journal}</a> — {journal_cards} cards', toc_journal_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # Main content
    for publisher, journals in sorted_hierarchy.items():
        publisher_cards = sum(len(cards) for cards in journals.values())
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{publisher} — {publisher_cards} cards", publisher_style))
        story.append(Spacer(1, 0.3*cm))
        
        for journal, cards in journals.items():
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            journal_anchor_para = Paragraph(f'<a name="{journal_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(journal_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{journal} — {len(cards)} cards", journal_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, card in enumerate(cards, 1):
                # Card type badge
                if card['type'] == 'combined':
                    badge_text = "🔴 RETRACTED ARTICLE + NOTICE"
                    badge_color = "#e17055"
                elif card['type'] == 'article_only':
                    badge_text = "🔴 RETRACTED ARTICLE (without notice)"
                    badge_color = "#ff6b6b"
                else:
                    badge_text = "🟡 RETRACTION NOTICE (without article)"
                    badge_color = "#fdcb6e"
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. <font color='{badge_color}'><b>{badge_text}</b></font>", badge_style))
                
                # Title
                if card.get('article'):
                    title = clean_text(card['article'].get('display_name', card['article'].get('title', 'No title')))
                else:
                    title = clean_text(card['notices'][0].get('display_name', card['notices'][0].get('title', 'No title')))
                
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{title}", card_title_style))
                
                # Authors (only those from selected countries)
                all_authors = []
                if card.get('article'):
                    authors = extract_all_authors_with_countries(card['article'], selected_countries)
                    all_authors.extend([a['name'] for a in authors])
                
                for notice in card.get('notices', []):
                    authors = extract_all_authors_with_countries(notice, selected_countries)
                    all_authors.extend([a['name'] for a in authors])
                
                seen_authors = set()
                unique_authors = []
                for author_name in all_authors:
                    if author_name not in seen_authors:
                        seen_authors.add(author_name)
                        unique_authors.append(author_name)
                
                if unique_authors:
                    authors_str = ', '.join(unique_authors)
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors_str}", authors_style))
                
                # Bibliographic info
                if card.get('article'):
                    biblio = extract_biblio_info(card['article'])
                else:
                    biblio = extract_biblio_info(card['notices'][0])
                
                meta_parts = []
                
                if card.get('article'):
                    year = card['article'].get('publication_year', '')
                    pub_date = card['article'].get('publication_date', '')
                else:
                    year = card['notices'][0].get('publication_year', '')
                    pub_date = card['notices'][0].get('publication_date', '')
                
                if year:
                    meta_parts.append(str(year))
                if pub_date and pub_date != '0000-00-00':
                    meta_parts.append(f"({pub_date})")
                if biblio.get('volume'):
                    meta_parts.append(f"Vol. {biblio['volume']}")
                if biblio.get('issue'):
                    meta_parts.append(f"Iss. {biblio['issue']}")
                if biblio.get('first_page') and biblio.get('last_page'):
                    meta_parts.append(f"pp. {biblio['first_page']}-{biblio['last_page']}")
                elif biblio.get('first_page'):
                    meta_parts.append(f"p. {biblio['first_page']}")
                
                if meta_parts:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style))
                
                # DOI information
                doi_info = format_card_doi_info(card)
                
                if doi_info['article_doi_url']:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Retracted Article DOI:</b> <a href='{clean_doi_url(doi_info['article_doi_url'])}'>{doi_info['article_doi']}</a>", meta_style))
                
                if doi_info['notice_doi_urls']:
                    for notice_doi_url in doi_info['notice_doi_urls']:
                        notice_doi = notice_doi_url.replace('https://doi.org/', '')
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Retraction Notice DOI:</b> <a href='{clean_doi_url(notice_doi_url)}'>{notice_doi}</a>", meta_style))
                
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
    This report contains {total_cards} retraction-related cards,
    grouped by {total_publishers} publishers and their journals.
    
    Each card represents either a retracted article, a retraction notice,
    or a combination of both when available.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using CTA Retraction Detector Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

# ============================================================================
# HELPER FUNCTIONS FOR PDF
# ============================================================================

def register_russian_font():
    """
    Register a font that supports Cyrillic characters.
    Returns font name.
    """
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
        'C:/Windows/Fonts/calibri.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
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

def get_pdf_font_name() -> str:
    """
    Get a font name that supports both Latin and Cyrillic characters.
    Returns font name that can be used in ParagraphStyle.
    """
    # Try to register a Unicode font first
    import os
    
    # List of possible Unicode fonts on different systems
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
        'C:/Windows/Fonts/calibri.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    ]
    
    # Try to register a font that supports Unicode
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('UnicodeFont', font_path))
                logger.info(f"Registered Unicode font from: {font_path}")
                return 'UnicodeFont'
            except Exception as e:
                logger.warning(f"Failed to register {font_path}: {e}")
                continue
    
    # Try to use the Russian font if available
    russian_font = register_russian_font()
    if russian_font != 'Helvetica':
        return russian_font
    
    # Fallback: try to use a built-in font that might work
    try:
        # Try to register a font from the system
        import platform
        system = platform.system()
        
        if system == 'Windows':
            fallback_paths = ['C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/times.ttf']
        elif system == 'Darwin':  # macOS
            fallback_paths = ['/System/Library/Fonts/Arial.ttf', '/System/Library/Fonts/Helvetica.ttc']
        else:  # Linux
            fallback_paths = ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf']
        
        for font_path in fallback_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('FallbackFont', font_path))
                return 'FallbackFont'
    except Exception as e:
        logger.warning(f"Failed to register fallback font: {e}")
    
    # Final fallback - Helvetica (will not show Cyrillic properly)
    logger.warning("No Unicode font found, using Helvetica (Cyrillic may not display correctly)")
    return 'Helvetica'

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
    
    async def fetch_retraction_works(self, years: List[int], 
                                     progress_callback=None) -> Tuple[List[dict], List[dict]]:
        """
        Fetch retracted articles and retraction notices for given years.
        Returns: (retracted_articles, retraction_notices)
        """
        retracted_articles = []
        retraction_notices = []
        
        years_str = "|".join(map(str, years))
        
        # Fetch retracted articles
        logger.info(f"Fetching retracted articles for years {years}")
        
        cursor = "*"
        page_count = 0
        total_count = 0
        
        try:
            while True:
                page_count += 1
                
                filter_str = f"is_retracted:true,publication_year:{years_str}"
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
                
                works = data.get('results', [])
                if not works:
                    break
                
                for work in works:
                    # Cache each work
                    doi = work.get('doi', '').replace('https://doi.org/', '')
                    if doi:
                        cache_work(doi, work)
                    retracted_articles.append(work)
                
                if progress_callback and total_count > 0:
                    progress = min(len(retracted_articles) / total_count, 1.0)
                    progress_callback(progress, len(retracted_articles), page_count, total_count, "retracted_articles")
                
                logger.info(f"Page {page_count}: got {len(works)} retracted articles, total: {len(retracted_articles)}/{total_count}")
                
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)
            
            logger.info(f"Finished fetching retracted articles. Total: {len(retracted_articles)}")
            
        except Exception as e:
            logger.error(f"Error fetching retracted articles: {str(e)}")
        
        # Fetch retraction notices
        logger.info(f"Fetching retraction notices for years {years}")
        
        cursor = "*"
        page_count = 0
        total_count = 0
        
        try:
            while True:
                page_count += 1
                
                # Filter for erratum type with retraction keywords
                filter_str = f"type:erratum|retraction,publication_year:{years_str}"
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
                    logger.info(f"Total potential retraction notices found: {total_count}")
                
                works = data.get('results', [])
                if not works:
                    break
                
                for work in works:
                    # Check if it's actually a retraction notice
                    if is_retraction_notice(work):
                        # Cache each work
                        doi = work.get('doi', '').replace('https://doi.org/', '')
                        if doi:
                            cache_work(doi, work)
                        retraction_notices.append(work)
                
                if progress_callback and total_count > 0:
                    progress = min(len(retraction_notices) / total_count if total_count > 0 else 0, 1.0)
                    progress_callback(progress, len(retraction_notices), page_count, total_count, "retraction_notices")
                
                logger.info(f"Page {page_count}: got {len(works)} potential notices, confirmed: {len(retraction_notices)}")
                
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)
            
            logger.info(f"Finished fetching retraction notices. Total: {len(retraction_notices)}")
            
        except Exception as e:
            logger.error(f"Error fetching retraction notices: {str(e)}")
        
        return retracted_articles, retraction_notices

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

def fetch_retraction_works_sync(years: List[int]) -> Tuple[List[dict], List[dict]]:
    """
    Fetch retracted articles and retraction notices for given years.
    Returns: (retracted_articles, retraction_notices)
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    retracted_articles = []
    retraction_notices = []
    
    def update_progress(progress, count, page, total, type_name):
        progress_bar.progress(progress)
        status_text.text(f"{type_name}: Page {page}: {count}/{total} works fetched")
    
    async def fetch():
        async with OpenAlexAsyncClient() as client:
            return await client.fetch_retraction_works(years, update_progress)
    
    retracted_articles, retraction_notices = run_async(fetch())
    
    progress_bar.empty()
    status_text.empty()
    
    return retracted_articles, retraction_notices

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
    
    # Check if retracted
    is_retracted = work.get('is_retracted', False)
    is_retraction_notice = is_retraction_notice(work)
    
    enriched = {
        'doi': doi_clean,
        'doi_url': f"https://doi.org/{doi_clean}" if doi_clean else '',
        'title': work.get('title', 'No title'),
        'display_name': work.get('display_name', work.get('title', 'No title')),
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
        'is_retracted': is_retracted,
        'is_retraction_notice': is_retraction_notice,
        'raw_data': work
    }
    
    return enriched

# ============================================================================
# HIERARCHICAL GROUPING FUNCTIONS WITH CACHING
# ============================================================================

@st.cache_data(ttl=3600)
def cached_group_articles_by_publisher_journal(articles_tuple: tuple, sort_option: str = 'alphabetical') -> Dict[str, Dict[str, List[dict]]]:
    """
    Cached version of group_articles_by_publisher_journal with sort option.
    """
    articles = list(articles_tuple)
    return group_articles_by_publisher_journal(articles, sort_option)

@st.cache_data(ttl=3600)
def cached_group_articles_by_country_affiliation(articles_tuple: tuple, sort_option: str = 'alphabetical') -> Dict[str, Dict[str, List[dict]]]:
    """
    Cached version of group_articles_by_country_affiliation with sort option.
    """
    articles = list(articles_tuple)
    return group_articles_by_country_affiliation(articles, sort_option)

@st.cache_data(ttl=3600)
def cached_sort_articles_by_citations(articles_tuple: tuple, sort_by: str = 'citations_per_year') -> List[dict]:
    """
    Cached version of sort_articles_by_citations with sort option.
    """
    articles = list(articles_tuple)
    return sort_articles_by_citations(articles, sort_by)

def group_articles_by_publisher_journal(articles: List[dict], sort_option: str = 'alphabetical') -> Dict[str, Dict[str, List[dict]]]:
    """
    Group articles by Publisher -> Journal.
    Sorted according to sort_option: 'alphabetical' or 'by_count'.
    """
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for article in articles:
        publisher = article.get('publisher', 'Unknown Publisher')
        if publisher is None:
            publisher = 'Unknown Publisher'
        if isinstance(publisher, str):
            if publisher.startswith('P') and publisher[1:].isdigit() or 'openalex.org/P' in publisher:
                publisher_chain = article.get('publisher_chain', [])
                if publisher_chain and len(publisher_chain) > 0:
                    publisher = publisher_chain[0]
                else:
                    publisher = 'Unknown Publisher'
        
        journal = article.get('journal_name', 'Unknown Journal')
        if journal is None:
            journal = 'Unknown Journal'
        hierarchy[publisher][journal].append(article)
    
    # Sort top-level publishers
    if sort_option == 'by_count':
        publisher_items = []
        for publisher in hierarchy.keys():
            if publisher is not None:
                total_count = sum(len(articles) for articles in hierarchy[publisher].values())
                publisher_items.append((publisher, total_count))
        publisher_items.sort(key=lambda x: x[1], reverse=True)
        sorted_publishers = [item[0] for item in publisher_items]
    else:  # alphabetical
        sorted_publishers = sorted([p for p in hierarchy.keys() if p is not None])
    
    sorted_hierarchy = {}
    for publisher in sorted_publishers:
        # Sort journals within each publisher
        if sort_option == 'by_count':
            journal_items = []
            for journal in hierarchy[publisher].keys():
                if journal is not None:
                    journal_items.append((journal, len(hierarchy[publisher][journal])))
            journal_items.sort(key=lambda x: x[1], reverse=True)
            sorted_journals = [item[0] for item in journal_items]
        else:  # alphabetical
            sorted_journals = sorted([j for j in hierarchy[publisher].keys() if j is not None])
        
        sorted_hierarchy[publisher] = {}
        for journal in sorted_journals:
            sorted_articles = sorted(
                hierarchy[publisher][journal],
                key=lambda x: x.get('citations_per_year', 0) if x.get('citations_per_year') is not None else 0,
                reverse=True
            )
            sorted_hierarchy[publisher][journal] = sorted_articles
    
    return sorted_hierarchy

def group_articles_by_country_affiliation(articles: List[dict], sort_option: str = 'alphabetical') -> Dict[str, Dict[str, List[dict]]]:
    """
    Group articles by Country -> Affiliation.
    An article can appear under multiple countries if it has authors from different countries.
    Sorted according to sort_option: 'alphabetical' or 'by_count'.
    """
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for article in articles:
        country = article.get('country', 'Unknown')
        if country is None:
            country = 'Unknown'
        affiliations = article.get('affiliations', ['Unknown Affiliation'])
        if not affiliations:
            affiliations = ['Unknown Affiliation']
        else:
            affiliations = [aff for aff in affiliations if aff is not None]
            if not affiliations:
                affiliations = ['Unknown Affiliation']
        
        for aff in affiliations:
            hierarchy[country][aff].append(article)
    
    # Sort top-level countries
    if sort_option == 'by_count':
        country_items = []
        for country in hierarchy.keys():
            if country is not None:
                total_count = sum(len(articles) for articles in hierarchy[country].values())
                country_items.append((country, total_count))
        country_items.sort(key=lambda x: x[1], reverse=True)
        sorted_countries = [item[0] for item in country_items]
    else:  # alphabetical
        sorted_countries = sorted([c for c in hierarchy.keys() if c is not None])
    
    sorted_hierarchy = {}
    for country in sorted_countries:
        # Sort affiliations within each country
        if sort_option == 'by_count':
            affiliation_items = []
            for affiliation in hierarchy[country].keys():
                if affiliation is not None:
                    affiliation_items.append((affiliation, len(hierarchy[country][affiliation])))
            affiliation_items.sort(key=lambda x: x[1], reverse=True)
            sorted_affiliations = [item[0] for item in affiliation_items]
        else:  # alphabetical
            sorted_affiliations = sorted([a for a in hierarchy[country].keys() if a is not None])
        
        sorted_hierarchy[country] = {}
        for affiliation in sorted_affiliations:
            sorted_articles = sorted(
                hierarchy[country][affiliation],
                key=lambda x: x.get('citations_per_year', 0) if x.get('citations_per_year') is not None else 0,
                reverse=True
            )
            sorted_hierarchy[country][affiliation] = sorted_articles
    
    return sorted_hierarchy

def sort_articles_by_citations(articles: List[dict], sort_by: str = 'citations_per_year') -> List[dict]:
    """
    Sort all articles by citations per year, total citations, or publication date.
    """
    if sort_by == 'total_citations':
        return sorted(
            articles,
            key=lambda x: x.get('cited_by_count', 0) if x.get('cited_by_count') is not None else 0,
            reverse=True
        )
    elif sort_by == 'publication_date':
        return sorted(
            articles,
            key=lambda x: x.get('publication_date', '0000-00-00') if x.get('publication_date') else '0000-00-00',
            reverse=True
        )
    else:  # default: citations_per_year
        return sorted(
            articles,
            key=lambda x: x.get('citations_per_year', 0) if x.get('citations_per_year') is not None else 0,
            reverse=True
        )

def sort_hierarchy_by_article_count(hierarchy: Dict) -> Dict:
    """
    Sort hierarchy levels by number of articles (descending).
    """
    if not hierarchy:
        return hierarchy
    
    sorted_hierarchy = {}
    
    # Sort top-level keys by total article count
    top_level_items = []
    for key, value in hierarchy.items():
        if isinstance(value, dict):
            total_count = sum(len(articles) for articles in value.values())
        else:
            total_count = len(value)
        top_level_items.append((key, value, total_count))
    
    top_level_items.sort(key=lambda x: x[2], reverse=True)
    
    for key, value, _ in top_level_items:
        if isinstance(value, dict):
            # Sort second-level items
            second_level_items = []
            for sub_key, articles in value.items():
                second_level_items.append((sub_key, articles, len(articles)))
            second_level_items.sort(key=lambda x: x[2], reverse=True)
            
            sorted_hierarchy[key] = {
                sub_key: articles for sub_key, articles, _ in second_level_items
            }
        else:
            sorted_hierarchy[key] = value
    
    return sorted_hierarchy

# ============================================================================
# SEARCH FUNCTIONS FOR STEP 6
# ============================================================================

def normalize_for_search(text: str) -> str:
    """
    Normalize text for search: lowercase, remove extra spaces.
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def check_phrase_match(title: str, phrase: str) -> bool:
    """
    Check if exact phrase exists in title (case-insensitive).
    """
    if not title or not phrase:
        return False
    title_norm = normalize_for_search(title)
    phrase_norm = normalize_for_search(phrase)
    return phrase_norm in title_norm

def check_and_match(title: str, terms: List[str]) -> bool:
    """
    Check if ALL terms exist in title (AND logic).
    """
    if not title or not terms:
        return False
    title_norm = normalize_for_search(title)
    for term in terms:
        term_norm = normalize_for_search(term)
        if term_norm not in title_norm:
            return False
    return True

def expand_wildcard(term: str) -> str:
    """
    Expand wildcard terms by removing trailing * for matching.
    Example: "catal*" -> "catal"
    """
    if not term:
        return term
    # Remove trailing * and any following characters
    term = re.sub(r'\*+$', '', term)
    return term

def expand_plural(term: str) -> List[str]:
    """
    Generate possible plural/singular forms of a term.
    """
    if not term:
        return [term]
    
    term_lower = term.lower()
    variants = [term_lower]
    
    # Common pluralization rules
    if term_lower.endswith('s') and not term_lower.endswith(('ss', 'us', 'is')):
        singular = term_lower[:-1]
        if len(singular) >= 3:
            variants.append(singular)
    else:
        # Add plural forms
        if term_lower.endswith('y'):
            variants.append(term_lower[:-1] + 'ies')
        elif term_lower.endswith(('ch', 'sh', 'x', 'z')):
            variants.append(term_lower + 'es')
        elif not term_lower.endswith('s'):
            variants.append(term_lower + 's')
    
    return list(set(variants))

def check_term_match(title: str, term: str) -> bool:
    """
    Check if a single term matches the title with wildcard and plural support.
    """
    if not title or not term:
        return False
    
    title_norm = normalize_for_search(title)
    
    # Check for wildcard (catal*)
    if '*' in term:
        base = expand_wildcard(term)
        if base and base in title_norm:
            return True
        # Also try to match word prefixes
        words = title_norm.split()
        for word in words:
            if word.startswith(base):
                return True
        return False
    
    # Check with plural forms
    variants = expand_plural(term)
    for variant in variants:
        if variant in title_norm:
            return True
        # Also check as separate word
        words = title_norm.split()
        for word in words:
            if variant == word:
                return True
            if word.startswith(variant) and len(word) >= len(variant):
                # For partial matches like "catalytic" matching "catal"
                pass
    
    return False

def parse_search_query(query: str) -> Dict[str, Any]:
    """
    Parse search query and return structured search parameters.
    Now supports OR operator.
    Returns: {
        'phrase': str or None,  # exact phrase in quotes
        'and_terms': List[str],  # terms with AND logic
        'or_groups': List[List[str]],  # groups of terms with OR logic
        'has_wildcard': bool
    }
    """
    if not query or not query.strip():
        return {'phrase': None, 'and_terms': [], 'or_groups': [], 'has_wildcard': False}
    
    query = query.strip()
    
    # Check for quoted phrases
    phrase_match = re.search(r'"([^"]+)"', query)
    phrase = phrase_match.group(1) if phrase_match else None
    
    # Remove quoted parts
    remaining = re.sub(r'"[^"]*"', '', query).strip()
    
    # Split by OR to get groups
    or_groups = []
    and_terms = []
    has_wildcard = False
    
    if ' OR ' in remaining or ' or ' in remaining:
        # Split by OR (case insensitive)
        groups = re.split(r'\s+OR\s+', remaining, flags=re.IGNORECASE)
        for group in groups:
            group = group.strip()
            if group:
                # Each group can have multiple AND terms
                group_terms = group.split()
                # Check for wildcards in group terms
                for term in group_terms:
                    if '*' in term:
                        has_wildcard = True
                or_groups.append(group_terms)
    else:
        # No OR - treat as AND terms
        terms = remaining.split() if remaining else []
        for term in terms:
            if '*' in term:
                has_wildcard = True
            and_terms.append(term)
    
    return {
        'phrase': phrase,
        'and_terms': and_terms,
        'or_groups': or_groups,
        'has_wildcard': has_wildcard
    }

def filter_articles_by_query(articles: List[dict], query: str) -> List[dict]:
    """
    Filter articles by search query.
    Supports:
    - Quoted phrases: "high temperature"
    - AND logic: high temperature (both words must appear)
    - OR logic: high OR low (at least one word must appear)
    - Wildcards: catal* (matches catalysis, catalyst, etc.)
    - Plural forms: fuel cell = fuel cells
    - Combined: "high temperature" OR "low temperature"
    """
    if not query or not query.strip() or not articles:
        return articles
    
    parsed = parse_search_query(query)
    filtered = []
    
    for article in articles:
        title = article.get('title', '')
        if not title:
            continue
        
        match = True
        
        # Check phrase match
        if parsed['phrase']:
            if not check_phrase_match(title, parsed['phrase']):
                match = False
        
        # Check OR groups (if present)
        if match and parsed['or_groups']:
            or_match = False
            for group_terms in parsed['or_groups']:
                # For each OR group, check if ALL terms in the group match (AND within OR group)
                group_match = True
                for term in group_terms:
                    if not check_term_match(title, term):
                        group_match = False
                        break
                if group_match:
                    or_match = True
                    break
            
            if not or_match:
                match = False
        
        # Check AND terms (if no OR groups)
        if match and parsed['and_terms']:
            for term in parsed['and_terms']:
                if not check_term_match(title, term):
                    match = False
                    break
        
        if match:
            filtered.append(article)
    
    return filtered

def parse_complex_search_query(query: str) -> Dict[str, Any]:
    """
    Enhanced parser that can handle mixed AND/OR logic.
    Example: "catal*" AND ("high temperature" OR "low temperature")
    """
    # This is a more advanced parser if you need nested logic
    pass

# ============================================================================
# UI STEPS - RETRACTION DETECTOR
# ============================================================================

def step_retraction_input():
    """Step 1: Input parameters for retraction analysis"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📥 Step 1: Set Analysis Parameters</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Define the period and countries for retraction analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="filter-section" style="background: rgba(255, 255, 255, 0.9); border-radius: 20px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(102, 126, 234, 0.2);">
        <div class="filter-header" style="font-size: 1.1rem; font-weight: 600; color: #495057; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #667eea;">
            📅 Publication Period
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
    
    st.markdown("""
    <div class="filter-section" style="background: rgba(255, 255, 255, 0.9); border-radius: 20px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(102, 126, 234, 0.2);">
        <div class="filter-header" style="font-size: 1.1rem; font-weight: 600; color: #495057; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #667eea;">
            🌍 Countries
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.9rem; color: #666; margin-bottom: 10px;">
        <strong>Supported format:</strong>
    </div>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px;">
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">RU</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">IT+RU</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">IT+RU+CN</span>
    </div>
    """, unsafe_allow_html=True)
    
    countries_input = st.text_input(
        "Enter country codes (separated by '+')",
        value=st.session_state.get('countries_input', ''),
        placeholder="Example: RU or IT+RU or IT+RU+CN",
        help="Enter country codes in ISO format (2 letters) separated by '+'"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if countries_input:
        countries = parse_country_filter(countries_input)
        if countries:
            countries_names = [get_country_name(c) for c in countries]
            st.markdown(f"""
            <div style="background: #e8f5e9; border-radius: 8px; padding: 12px; border-left: 4px solid #4CAF50; margin: 10px 0;">
                <strong>✅ Selected countries:</strong> {', '.join(countries_names)}
                <br><span style="font-size: 0.85rem; color: #666;">Codes: {', '.join(countries)}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #ffebee; border-radius: 8px; padding: 12px; border-left: 4px solid #f44336; margin: 10px 0;">
                <strong>❌ Invalid format:</strong> Please check your input.
                <br><span style="font-size: 0.85rem; color: #666;">Example: RU, IT+RU, IT+RU+CN</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 Start Retraction Analysis", type="primary", use_container_width=True):
            if not years_input:
                st.error("❌ Please enter at least one year.")
                return
            
            years = parse_year_filter(years_input)
            if not years:
                st.error("❌ Invalid year format. Please check your input.")
                return
            
            if not countries_input:
                st.error("❌ Please enter at least one country.")
                return
            
            countries = parse_country_filter(countries_input)
            if not countries:
                st.error("❌ Invalid country format. Please check your input.")
                return
            
            st.session_state.years_input = years_input
            st.session_state.selected_years = years
            st.session_state.countries_input = countries_input
            st.session_state.selected_countries = countries
            st.session_state.current_step = 2
            st.rerun()

def step_retraction_analysis():
    """Step 2: Retraction analysis in progress"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 2: Retraction Analysis in Progress</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Fetching retracted articles and retraction notices from OpenAlex...</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'selected_years' not in st.session_state or 'selected_countries' not in st.session_state:
        st.error("❌ No parameters set. Please go back to Step 1.")
        return
    
    years = st.session_state.selected_years
    countries = st.session_state.selected_countries
    
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    
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
            <div class="metric-value">{len(countries)}</div>
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
    
    with st.spinner("Fetching retracted articles and retraction notices..."):
        retracted_articles, retraction_notices = fetch_retraction_works_sync(years)
    
    st.session_state.retracted_articles = retracted_articles
    st.session_state.retraction_notices = retraction_notices
    
    st.markdown(f"""
    <div class="info-message" style="background: linear-gradient(135deg, #2196F315 0%, #0D47A115 100%); border-radius: 8px; padding: 12px; border-left: 3px solid #2196F3; font-size: 0.9rem; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>✅ Analysis Complete!</strong><br>
                Found {len(retracted_articles)} retracted articles and {len(retraction_notices)} retraction notices
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(retracted_articles)}</div>
            <div class="metric-label">Retracted Articles</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(retraction_notices)}</div>
            <div class="metric-label">Retraction Notices</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        total_cards = len(retracted_articles) + len(retraction_notices)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_cards}</div>
            <div class="metric-label">Total Records</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📊 Generate Retraction Reports", type="primary", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()

def step_retraction_results():
    """Step 3: Retraction results with 3 PDF reports"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📊 Step 3: Retraction Analysis Results</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Download reports for retracted articles and retraction notices.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'retracted_articles' not in st.session_state or 'retraction_notices' not in st.session_state:
        st.error("❌ No data available. Please go back to Step 1.")
        return
    
    retracted_articles = st.session_state.retracted_articles
    retraction_notices = st.session_state.retraction_notices
    years = st.session_state.selected_years
    countries = st.session_state.selected_countries
    
    # Group into cards
    cards = group_retraction_cards(retracted_articles, retraction_notices, countries)
    st.session_state.retraction_cards = cards
    
    # Statistics
    total_cards = len(cards)
    combined_cards = sum(1 for c in cards if c['type'] == 'combined')
    article_only = sum(1 for c in cards if c['type'] == 'article_only')
    notice_only = sum(1 for c in cards if c['type'] == 'notice_only')
    
    st.markdown(f"""
    <div style="background: white; border-radius: 8px; padding: 12px; border: 1px solid #ced4da; margin-bottom: 15px;">
        <strong>Analysis Summary:</strong>
        <br>Total cards: {total_cards} | Combined (article + notice): {combined_cards} | Article only: {article_only} | Notice only: {notice_only}
    </div>
    """, unsafe_allow_html=True)
    
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
            <div class="metric-value">{combined_cards}</div>
            <div class="metric-label">Combined</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{article_only}</div>
            <div class="metric-label">Article Only</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{notice_only}</div>
            <div class="metric-label">Notice Only</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📥 Download Retraction Reports")
    
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
    cards_hash = hashlib.md5(str(sorted([str(c) for c in cards])).encode()).hexdigest()[:8]
    years_hash = hashlib.md5(','.join(map(str, years)).encode()).hexdigest()[:8]
    countries_hash = hashlib.md5(','.join(countries).encode()).hexdigest()[:8]
    
    cache_key_country = f"retraction_country_{years_hash}_{countries_hash}_{cards_hash}"
    cache_key_author = f"retraction_author_{years_hash}_{countries_hash}_{cards_hash}"
    cache_key_publisher = f"retraction_publisher_{years_hash}_{countries_hash}_{cards_hash}"
    
    st.markdown("---")
    
    col_gen1, col_gen2, col_gen3 = st.columns([1, 1, 1])
    with col_gen2:
        if not st.session_state.all_reports_generated:
            if st.button("⚡ Generate All Retraction Reports", type="primary", use_container_width=True):
                with st.spinner("Generating all retraction reports..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("Generating Country → Affiliation report...")
                    if cache_key_country not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_country] = generate_retraction_pdf_by_country(
                            cards, countries, years, logo_path,
                            "Retraction Report by Country & Affiliation",
                            'by_count'
                        )
                    progress_bar.progress(0.33)
                    
                    status_text.text("Generating Author report...")
                    if cache_key_author not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_author] = generate_retraction_pdf_by_author(
                            cards, countries, years, logo_path,
                            "Retraction Report by Author",
                            'by_count'
                        )
                    progress_bar.progress(0.66)
                    
                    status_text.text("Generating Publisher → Journal report...")
                    if cache_key_publisher not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_publisher] = generate_retraction_pdf_by_publisher_journal(
                            cards, countries, years, logo_path,
                            "Retraction Report by Publisher & Journal",
                            'by_count'
                        )
                    progress_bar.progress(1.0)
                    
                    status_text.text("✅ All retraction reports generated!")
                    st.session_state.all_reports_generated = True
                    time.sleep(0.5)
                    st.rerun()
        else:
            st.success("✅ All retraction reports already generated! Use the buttons below to download.")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🌍 Report 1: Country → Affiliation**")
        st.markdown("*By number of cards*")
        
        if cache_key_country in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_country]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            countries_str = '+'.join(countries)
            filename = f"retraction_{format_year_filter_for_filename(years)}_{countries_str}_country.pdf"
            st.download_button(
                label="📄 Download Country Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_retraction_country_download_{cache_key_country}"
            )
        else:
            if st.button("📄 Generate Country Report", key=f"gen_retraction_country_{cache_key_country}", use_container_width=True):
                with st.spinner("Generating Country Report..."):
                    pdf_data = generate_retraction_pdf_by_country(
                        cards, countries, years, logo_path,
                        "Retraction Report by Country & Affiliation",
                        'by_count'
                    )
                    st.session_state.pdf_cache[cache_key_country] = pdf_data
                    st.rerun()
    
    with col2:
        st.markdown("**👤 Report 2: By Author**")
        st.markdown("*By number of cards*")
        
        if cache_key_author in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_author]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            countries_str = '+'.join(countries)
            filename = f"retraction_{format_year_filter_for_filename(years)}_{countries_str}_author.pdf"
            st.download_button(
                label="📄 Download Author Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_retraction_author_download_{cache_key_author}"
            )
        else:
            if st.button("📄 Generate Author Report", key=f"gen_retraction_author_{cache_key_author}", use_container_width=True):
                with st.spinner("Generating Author Report..."):
                    pdf_data = generate_retraction_pdf_by_author(
                        cards, countries, years, logo_path,
                        "Retraction Report by Author",
                        'by_count'
                    )
                    st.session_state.pdf_cache[cache_key_author] = pdf_data
                    st.rerun()
    
    with col3:
        st.markdown("**📚 Report 3: Publisher → Journal**")
        st.markdown("*By number of cards*")
        
        if cache_key_publisher in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_publisher]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            countries_str = '+'.join(countries)
            filename = f"retraction_{format_year_filter_for_filename(years)}_{countries_str}_publisher.pdf"
            st.download_button(
                label="📄 Download Publisher Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_retraction_publisher_download_{cache_key_publisher}"
            )
        else:
            if st.button("📄 Generate Publisher Report", key=f"gen_retraction_publisher_{cache_key_publisher}", use_container_width=True):
                with st.spinner("Generating Publisher Report..."):
                    pdf_data = generate_retraction_pdf_by_publisher_journal(
                        cards, countries, years, logo_path,
                        "Retraction Report by Publisher & Journal",
                        'by_count'
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
                    countries_str = '+'.join(countries)
                    zip_file.writestr(f"retraction_{format_year_filter_for_filename(years)}_{countries_str}_country.pdf", 
                                     st.session_state.pdf_cache[cache_key_country])
                    zip_file.writestr(f"retraction_{format_year_filter_for_filename(years)}_{countries_str}_author.pdf", 
                                     st.session_state.pdf_cache[cache_key_author])
                    zip_file.writestr(f"retraction_{format_year_filter_for_filename(years)}_{countries_str}_publisher.pdf", 
                                     st.session_state.pdf_cache[cache_key_publisher])
                
                zip_data = zip_buffer.getvalue()
                
                col_zip1, col_zip2, col_zip3 = st.columns([1, 2, 1])
                with col_zip2:
                    st.download_button(
                        label="📦 Download All Retraction Reports (ZIP archive)",
                        data=zip_data,
                        file_name=f"retraction_{format_year_filter_for_filename(years)}_{countries_str}_all_reports.zip",
                        mime="application/zip",
                        use_container_width=True,
                        key="download_retraction_all_zip"
                    )
            except Exception as e:
                st.error(f"Error creating ZIP archive: {e}")
    
    st.markdown("---")
    
    if st.button("🔄 New Retraction Analysis", use_container_width=True):
        keys_to_clear = ['current_step', 'years_input', 'selected_years', 'countries_input', 
                        'selected_countries', 'retracted_articles', 'retraction_notices',
                        'retraction_cards', 'pdf_cache', 'all_reports_generated']
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
        step_retraction_input()
    elif st.session_state.current_step == 2:
        step_retraction_analysis()
    elif st.session_state.current_step == 3:
        step_retraction_results()
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>© CTA, https://chimicatechnoacta.ru / developed by daM©</p>
        <p style="font-size: 0.7rem; color: #aaa;">CTA Retraction Detector Pro*2 — Detection and analysis of retracted articles and retraction notices</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
