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
    page_title="Retracted Article Detector",
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
        border-left: 4px solid #e74c3c;
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
        CREATE TABLE IF NOT EXISTS retracted_works_cache (
            cache_key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_works_expires ON works_cache(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_retracted_works_expires ON retracted_works_cache(expires_at)')
    
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

def cache_retracted_works(cache_key: str, data: dict):
    conn = get_cache_connection()
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(days=CACHE_EXPIRY_DAYS)
    cursor.execute('''
        INSERT OR REPLACE INTO retracted_works_cache (cache_key, data, expires_at)
        VALUES (?, ?, ?)
    ''', (cache_key, json.dumps(data), expires_at))
    conn.commit()
    conn.close()

def get_cached_retracted_works(cache_key: str) -> Optional[dict]:
    conn = get_cache_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT data FROM retracted_works_cache 
        WHERE cache_key = ? AND (expires_at IS NULL OR expires_at > ?)
    ''', (cache_key, datetime.now()))
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
    cursor.execute('DELETE FROM retracted_works_cache WHERE expires_at IS NOT NULL AND expires_at <= ?', (now,))
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

def parse_countries_input(country_input: str) -> List[str]:
    """
    Parse country codes from input string.
    Case-insensitive, supports various separators.
    Examples:
    "RU" -> ['RU']
    "ru" -> ['RU']
    "IT+RU" -> ['IT', 'RU']
    "it+ru" -> ['IT', 'RU']
    "it,ru" -> ['IT', 'RU']
    "IT,RU" -> ['IT', 'RU']
    "IT, RU" -> ['IT', 'RU']
    "it, ru" -> ['IT', 'RU']
    "IT+RU+CN" -> ['IT', 'RU', 'CN']
    "it+ru+cn" -> ['IT', 'RU', 'CN']
    "it, ru, cn" -> ['IT', 'RU', 'CN']
    "IT, RU, CN" -> ['IT', 'RU', 'CN']
    "it,ru,cn" -> ['IT', 'RU', 'CN']
    "IT, RU + CN" -> ['IT', 'RU', 'CN']
    "it, ru + cn" -> ['IT', 'RU', 'CN']
    "   IT   ,   RU   +   CN   " -> ['IT', 'RU', 'CN']
    """
    if not country_input or country_input.strip() == "":
        return []
    
    # Remove all whitespace
    clean_input = country_input.replace(' ', '')
    
    # Replace common separators with '+'
    # Convert commas, semicolons, spaces to '+'
    for separator in [',', ';', '|', '/', '\\', '-', '_']:
        clean_input = clean_input.replace(separator, '+')
    
    # Remove any remaining whitespace
    clean_input = clean_input.replace(' ', '')
    
    # Split by '+'
    countries = [c.strip() for c in clean_input.split('+') if c.strip()]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_countries = []
    for country in countries:
        country_upper = country.upper()
        if country_upper not in seen:
            seen.add(country_upper)
            unique_countries.append(country_upper)
    
    # Filter out empty strings and validate (2-letter codes)
    validated_countries = []
    for country in unique_countries:
        if country and country.strip():
            # Basic validation: should be 2 letters
            if len(country) == 2 and country.isalpha():
                validated_countries.append(country)
            elif len(country) > 0:
                # If it's longer than 2 letters, try to extract 2-letter code
                # This handles cases like "Russia" -> "RU"
                country_code_map = {
                    'RUSSIA': 'RU',
                    'RUSSIAN': 'RU',
                    'RUS': 'RU',
                    'ITALY': 'IT',
                    'ITALIAN': 'IT',
                    'ITA': 'IT',
                    'CHINA': 'CN',
                    'CHINESE': 'CN',
                    'PEOPLES': 'CN',
                    'UNITED STATES': 'US',
                    'UNITED STATES OF AMERICA': 'US',
                    'USA': 'US',
                    'AMERICA': 'US',
                    'UNITED KINGDOM': 'GB',
                    'UK': 'GB',
                    'GREAT BRITAIN': 'GB',
                    'ENGLAND': 'GB',
                    'GERMANY': 'DE',
                    'GERMAN': 'DE',
                    'DEU': 'DE',
                    'FRANCE': 'FR',
                    'FRENCH': 'FR',
                    'FRA': 'FR',
                    'JAPAN': 'JP',
                    'JAPANESE': 'JP',
                    'JPN': 'JP',
                    'CANADA': 'CA',
                    'CAN': 'CA',
                    'AUSTRALIA': 'AU',
                    'AUS': 'AU',
                    'BRAZIL': 'BR',
                    'BRA': 'BR',
                    'INDIA': 'IN',
                    'IND': 'IN',
                    'SOUTH KOREA': 'KR',
                    'KOREA': 'KR',
                    'KOR': 'KR',
                    'NETHERLANDS': 'NL',
                    'NLD': 'NL',
                    'SWITZERLAND': 'CH',
                    'CHE': 'CH',
                    'SWEDEN': 'SE',
                    'SWE': 'SE',
                    'BELGIUM': 'BE',
                    'BEL': 'BE',
                    'DENMARK': 'DK',
                    'DNK': 'DK',
                    'FINLAND': 'FI',
                    'FIN': 'FI',
                    'NORWAY': 'NO',
                    'NOR': 'NO',
                    'POLAND': 'PL',
                    'POL': 'PL',
                    'UKRAINE': 'UA',
                    'UKR': 'UA',
                    'KAZAKHSTAN': 'KZ',
                    'KAZ': 'KZ',
                    'UZBEKISTAN': 'UZ',
                    'UZB': 'UZ',
                    'BELARUS': 'BY',
                    'BLR': 'BY',
                    'AZERBAIJAN': 'AZ',
                    'AZE': 'AZ',
                    'GEORGIA': 'GE',
                    'GEO': 'GE',
                    'ARMENIA': 'AM',
                    'ARM': 'AM',
                    'MOLDOVA': 'MD',
                    'MDA': 'MD',
                    'TURKEY': 'TR',
                    'TUR': 'TR',
                    'ISRAEL': 'IL',
                    'ISR': 'IL',
                    'SAUDI ARABIA': 'SA',
                    'SAU': 'SA',
                    'UNITED ARAB EMIRATES': 'AE',
                    'ARE': 'AE',
                    'QATAR': 'QA',
                    'QAT': 'QA',
                    'KUWAIT': 'KW',
                    'KWT': 'KW',
                    'OMAN': 'OM',
                    'OMN': 'OM',
                    'BAHRAIN': 'BH',
                    'BHR': 'BH',
                    'IRAN': 'IR',
                    'IRN': 'IR',
                    'IRAQ': 'IQ',
                    'IRQ': 'IRQ',
                    'SYRIA': 'SY',
                    'SYR': 'SY',
                    'JORDAN': 'JO',
                    'JOR': 'JO',
                    'LEBANON': 'LB',
                    'LBN': 'LB',
                    'EGYPT': 'EG',
                    'EGY': 'EG',
                    'SOUTH AFRICA': 'ZA',
                    'ZAF': 'ZA',
                    'NIGERIA': 'NG',
                    'NGA': 'NG',
                    'KENYA': 'KE',
                    'KEN': 'KE',
                    'GHANA': 'GH',
                    'GHA': 'GH',
                    'MEXICO': 'MX',
                    'MEX': 'MX',
                    'ARGENTINA': 'AR',
                    'ARG': 'AR',
                    'CHILE': 'CL',
                    'CHL': 'CL',
                    'COLOMBIA': 'CO',
                    'COL': 'CO',
                    'PERU': 'PE',
                    'PER': 'PE',
                    'VENEZUELA': 'VE',
                    'VEN': 'VE',
                    'MALAYSIA': 'MY',
                    'MYS': 'MY',
                    'SINGAPORE': 'SG',
                    'SGP': 'SG',
                    'INDONESIA': 'ID',
                    'IDN': 'ID',
                    'THAILAND': 'TH',
                    'THA': 'TH',
                    'VIETNAM': 'VN',
                    'VNM': 'VN',
                    'PHILIPPINES': 'PH',
                    'PHL': 'PH',
                    'PAKISTAN': 'PK',
                    'PAK': 'PK',
                    'BANGLADESH': 'BD',
                    'BGD': 'BD',
                    'NEW ZEALAND': 'NZ',
                    'NZL': 'NZ'
                }
                country_upper = country.upper()
                if country_upper in country_code_map:
                    validated_countries.append(country_code_map[country_upper])
                else:
                    # Try to find a match by checking if input contains a known country code
                    found = False
                    for key, code in country_code_map.items():
                        if key in country_upper or country_upper in key:
                            validated_countries.append(code)
                            found = True
                            break
                    if not found:
                        # If it's a valid 2-letter code but lowercase, convert to uppercase
                        if len(country) == 2 and country.isalpha():
                            validated_countries.append(country.upper())
                        else:
                            # If it's a single letter, skip
                            if len(country) >= 2:
                                # Take first two letters as fallback
                                code = country[:2].upper()
                                if code.isalpha():
                                    validated_countries.append(code)
    
    # Remove duplicates after validation
    final_seen = set()
    final_countries = []
    for country in validated_countries:
        if country not in final_seen:
            final_seen.add(country)
            final_countries.append(country)
    
    return final_countries

def format_countries_for_filename(countries: List[str]) -> str:
    """
    Format country list for filename.
    ['IT', 'RU', 'CN'] -> "IT+RU+CN"
    """
    return '+'.join(countries)

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
    
    async def fetch_retracted_works(self, years: List[int], countries: List[str] = None,
                                    progress_callback=None) -> List[dict]:
        """
        Fetch retracted works for specified years and countries.
        Uses cursor pagination to get all available works.
        """
        all_works = []
        cursor = "*"
        page_count = 0
        total_count = 0
        
        # Build filter string: is_retracted:true + years
        years_str = "|".join(map(str, years))
        filter_str = f"is_retracted:true,publication_year:{years_str}"
        
        # Add country filter if countries are specified
        if countries and len(countries) > 0:
            countries_str = "|".join(countries)
            filter_str += f",authorships.countries:{countries_str}"
        
        logger.info(f"Fetching retracted works for years {years}, countries {countries}")
        logger.info(f"Filter: {filter_str}")
        
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
                
                logger.info(f"Page {page_count}: got {len(works)} works, total: {len(all_works)}/{total_count}")
                
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)
            
            logger.info(f"Finished fetching. Total works: {len(all_works)}")
            return all_works
            
        except Exception as e:
            logger.error(f"Error in fetch_retracted_works: {str(e)}")
            return all_works
    
    async def fetch_single_work(self, doi: str) -> Optional[dict]:
        cached = get_cached_work(doi)
        if cached:
            return cached
        
        url = f"{OPENALEX_BASE_URL}/works/https://doi.org/{doi}"
        data = await self.make_request(url)
        
        if data:
            cache_work(doi, data)
        
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

def fetch_retracted_works_sync(years: List[int], countries: List[str] = None) -> List[dict]:
    """
    Fetch retracted works for given years and countries.
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_works = []
    
    def update_progress(progress, count, page, total):
        progress_bar.progress(progress)
        status_text.text(f"Page {page}: {count}/{total} retracted works fetched")
    
    # Generate cache key
    years_str = ','.join(map(str, years))
    countries_str = '+'.join(countries) if countries else 'all'
    cache_key = f"retracted_{years_str}_{countries_str}"
    
    # Check cache
    cached_data = get_cached_retracted_works(cache_key)
    if cached_data:
        logger.info(f"Using cached data for {cache_key}")
        progress_bar.empty()
        status_text.empty()
        return cached_data.get('works', [])
    
    async def fetch():
        async with OpenAlexAsyncClient() as client:
            return await client.fetch_retracted_works(
                years, countries, update_progress
            )
    
    result = run_async(fetch())
    
    # Cache results
    if result:
        cache_retracted_works(cache_key, {'works': result, 'count': len(result)})
    
    progress_bar.empty()
    status_text.empty()
    return result

# ============================================================================
# ENRICHMENT FUNCTIONS FOR RETRACTED WORKS
# ============================================================================

def extract_all_authors_and_affiliations(work: dict) -> Tuple[List[dict], List[dict], List[str], List[str]]:
    """
    Extract all authors with their affiliations and countries.
    Uses raw_author_name for Cyrillic names when available.
    Returns:
    - authors_full: List of dict with author info {name, countries}
    - affiliations_full: List of dict with affiliation info {name, country}
    - countries: List of unique country codes
    - authors_names: List of author names only
    """
    import unicodedata
    import re
    
    authors_full = []
    affiliations_full = []
    countries_set = set()
    authors_names = []
    
    authorships = work.get('authorships', [])
    
    for authorship in authorships:
        if not authorship:
            continue
            
        # Extract author - try raw_author_name first (preserves Cyrillic)
        author = authorship.get('author', {})
        author_name = ''
        
        # Priority 1: Use raw_author_name (preserves original Cyrillic)
        raw_name = authorship.get('raw_author_name', '')
        if raw_name:
            raw_name = str(raw_name).strip()
            # Normalize Unicode
            raw_name = unicodedata.normalize('NFC', raw_name)
            # Remove invalid characters but keep Cyrillic and Latin
            raw_name = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s\.\,\-\'\(\)]', '', raw_name)
            raw_name = re.sub(r'\s+', ' ', raw_name).strip()
            if raw_name:
                author_name = raw_name
        
        # Priority 2: Use display_name if raw_author_name is empty
        if not author_name and author:
            author_name = author.get('display_name', '')
            if author_name:
                author_name = str(author_name).strip()
                author_name = unicodedata.normalize('NFC', author_name)
                author_name = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s\.\,\-\'\(\)]', '', author_name)
                author_name = re.sub(r'\s+', ' ', author_name).strip()
        
        # Skip if no author name
        if not author_name:
            continue
        
        # Extract countries for this author from institutions
        author_countries = []
        for inst in authorship.get('institutions', []):
            if inst:
                country_code = inst.get('country_code', '')
                if country_code:
                    author_countries.append(country_code)
                    countries_set.add(country_code)
                
                inst_name = inst.get('display_name', '')
                if inst_name:
                    inst_name = inst_name.strip()
                    if inst_name:
                        # Normalize affiliation name
                        inst_name = unicodedata.normalize('NFC', str(inst_name))
                        inst_name = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s\.\,\-\'\(\)\d]', '', inst_name)
                        inst_name = re.sub(r'\s+', ' ', inst_name).strip()
                        if inst_name:
                            affiliations_full.append({
                                'name': inst_name,
                                'country': country_code
                            })
        
        # Add author
        authors_full.append({
            'name': author_name,
            'countries': author_countries
        })
        authors_names.append(author_name)
    
    # Remove duplicate affiliations (keep first occurrence)
    unique_affiliations = []
    seen_aff = set()
    for aff in affiliations_full:
        key = f"{aff['name']}_{aff['country']}"
        if key not in seen_aff:
            seen_aff.add(key)
            unique_affiliations.append(aff)
    
    # Remove duplicate authors (keep first occurrence)
    unique_authors = []
    seen_auth = set()
    for auth in authors_full:
        if auth['name'] not in seen_auth:
            seen_auth.add(auth['name'])
            unique_authors.append(auth)
    
    return unique_authors, unique_affiliations, list(countries_set), authors_names

def extract_author_countries(work: dict) -> List[str]:
    """
    Extract all unique countries from authorships.
    """
    countries_set = set()
    authorships = work.get('authorships', [])
    
    for authorship in authorships:
        if authorship:
            for inst in authorship.get('institutions', []):
                if inst:
                    country_code = inst.get('country_code', '')
                    if country_code:
                        countries_set.add(country_code)
    
    return list(countries_set)

def get_author_from_country(work: dict, target_countries: List[str]) -> List[dict]:
    """
    Get authors from specified countries only.
    Returns list of authors with their names and countries.
    """
    authors = []
    authorships = work.get('authorships', [])
    
    for authorship in authorships:
        if authorship:
            author = authorship.get('author', {})
            author_name = ''
            if author:
                author_name = author.get('display_name', '')
                if author_name:
                    import unicodedata
                    author_name = unicodedata.normalize('NFC', str(author_name))
                    author_name = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s\.\,\-\'\(\)]', '', author_name)
                    author_name = re.sub(r'\s+', ' ', author_name).strip()
            
            if not author_name:
                continue
            
            # Check if this author has affiliations in target countries
            author_countries = []
            for inst in authorship.get('institutions', []):
                if inst:
                    country_code = inst.get('country_code', '')
                    if country_code and country_code in target_countries:
                        author_countries.append(country_code)
            
            if author_countries:
                authors.append({
                    'name': author_name,
                    'countries': author_countries
                })
    
    return authors

def enrich_retracted_work(work: dict) -> dict:
    """
    Enrich retracted article data with complete information.
    No truncation of authors or affiliations.
    Uses raw_author_name for Cyrillic names when available.
    """
    if not work:
        return {}
    
    doi_raw = work.get('doi')
    doi_clean = ''
    if doi_raw:
        doi_clean = str(doi_raw).replace('https://doi.org/', '')
    
    # Extract ALL authors and affiliations using the updated function
    authors_full, affiliations_full, all_countries, author_names = extract_all_authors_and_affiliations(work)
    
    # Build authors string with proper names
    authors_str = ', '.join([a['name'] for a in authors_full]) if authors_full else 'Authors not specified'
    
    # Format affiliations with country codes
    affiliations_str = ' / '.join([f"{a['name']} ({a['country']})" for a in affiliations_full]) if affiliations_full else 'No affiliations specified'
    
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
    
    # Publication year and date
    publication_year = work.get('publication_year', 0)
    publication_date = work.get('publication_date', '')
    
    # Get title with RETRACTED prefix if not already present
    title = work.get('title', 'No title')
    if not title.lower().startswith('retracted'):
        title = f"RETRACTED: {title}"
    
    enriched = {
        'doi': doi_clean,
        'doi_url': f"https://doi.org/{doi_clean}" if doi_clean else '',
        'title': title,
        'publication_year': publication_year,
        'publication_date': publication_date,
        'authors_full': authors_full,
        'authors_str': authors_str,
        'author_names': author_names,
        'affiliations_full': affiliations_full,
        'affiliations_str': affiliations_str,
        'journal_name': journal_name,
        'publisher': publisher,
        'publisher_chain': publisher_chain,
        'volume': volume,
        'issue': issue,
        'pages': pages_str,
        'all_countries': all_countries,
        'is_retracted': work.get('is_retracted', False)
    }
    
    return enriched

# ============================================================================
# GROUPING FUNCTIONS
# ============================================================================

def sort_hierarchy_by_count(hierarchy: Dict) -> Dict:
    """
    Sort hierarchy levels by number of articles (descending).
    If counts are equal, sort alphabetically.
    """
    if not hierarchy:
        return hierarchy
    
    sorted_hierarchy = {}
    
    # Sort top-level keys by article count (descending), then alphabetically
    top_level_items = []
    for key, value in hierarchy.items():
        if isinstance(value, dict):
            total_count = sum(len(articles) for articles in value.values())
        elif isinstance(value, list):
            total_count = len(value)
        else:
            total_count = 0
        top_level_items.append((key, value, total_count))
    
    # Sort by count descending, then by key alphabetically
    top_level_items.sort(key=lambda x: (-x[2], x[0]))
    
    for key, value, _ in top_level_items:
        if isinstance(value, dict):
            # Sort second-level items
            second_level_items = []
            for sub_key, articles in value.items():
                if isinstance(articles, list):
                    second_level_items.append((sub_key, articles, len(articles)))
                else:
                    second_level_items.append((sub_key, articles, 0))
            
            # Sort by count descending, then by key alphabetically
            second_level_items.sort(key=lambda x: (-x[2], x[0]))
            
            sorted_hierarchy[key] = {
                sub_key: articles for sub_key, articles, _ in second_level_items
            }
        elif isinstance(value, list):
            sorted_hierarchy[key] = value
    
    return sorted_hierarchy

def group_articles_by_country_affiliation(articles: List[dict], target_countries: List[str]) -> Dict[str, Dict[str, List[dict]]]:
    """
    Group articles by Country -> Affiliation.
    Only includes countries from target_countries list.
    An article can appear under multiple countries and affiliations if it has authors from multiple countries/affiliations.
    """
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for article in articles:
        affiliations_full = article.get('affiliations_full', [])
        if not affiliations_full:
            continue
        
        # Get countries for this article
        article_countries = article.get('all_countries', [])
        
        # Check if article has at least one author from target countries
        has_target_country = False
        for country in article_countries:
            if country in target_countries:
                has_target_country = True
                break
        
        if not has_target_country:
            continue
        
        # Group by each affiliation's country
        for aff in affiliations_full:
            country = aff.get('country', '')
            if not country or country not in target_countries:
                continue
            
            aff_name = aff.get('name', 'Unknown Affiliation')
            # Add article to this country and affiliation
            # Check if article already exists in this affiliation to avoid duplicates
            existing_articles = hierarchy[country][aff_name]
            if not any(a.get('doi') == article.get('doi') for a in existing_articles):
                hierarchy[country][aff_name].append(article)
    
    # Sort articles within each affiliation by publication date (newest first)
    for country in hierarchy:
        for affiliation in hierarchy[country]:
            hierarchy[country][affiliation] = sorted(
                hierarchy[country][affiliation],
                key=lambda x: x.get('publication_date', '0000-00-00'),
                reverse=True
            )
    
    return sort_hierarchy_by_count(hierarchy)

def group_articles_by_authors(articles: List[dict], target_countries: List[str]) -> Dict[str, List[dict]]:
    """
    Group articles by unique authors.
    Only includes authors from target_countries.
    Format: "LastName I." (e.g., "Mongiat M.")
    """
    author_articles = defaultdict(list)
    
    for article in articles:
        authors_full = article.get('authors_full', [])
        if not authors_full:
            continue
        
        # Check if article has authors from target countries
        for author in authors_full:
            author_countries = author.get('countries', [])
            # Check if any of the author's countries are in target_countries
            if any(c in target_countries for c in author_countries):
                # Format author name: LastName I.
                name_parts = author['name'].split()
                if len(name_parts) >= 2:
                    last_name = name_parts[-1]
                    first_initial = name_parts[0][0] if name_parts[0] else ''
                    author_key = f"{last_name} {first_initial}."
                else:
                    author_key = author['name']
                
                # Check if article already exists for this author
                existing_articles = author_articles[author_key]
                if not any(a.get('doi') == article.get('doi') for a in existing_articles):
                    author_articles[author_key].append(article)
    
    # Sort articles within each author by publication date (newest first)
    for author in author_articles:
        author_articles[author] = sorted(
            author_articles[author],
            key=lambda x: x.get('publication_date', '0000-00-00'),
            reverse=True
        )
    
    # Sort authors by article count (descending), then alphabetically
    sorted_authors = dict(
        sorted(author_articles.items(), key=lambda x: (-len(x[1]), x[0]))
    )
    
    return sorted_authors

def group_articles_by_publisher_journal(articles: List[dict]) -> Dict[str, Dict[str, List[dict]]]:
    """
    Group articles by Publisher -> Journal.
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
        
        # Check if article already exists in this journal
        existing_articles = hierarchy[publisher][journal]
        if not any(a.get('doi') == article.get('doi') for a in existing_articles):
            hierarchy[publisher][journal].append(article)
    
    # Sort articles within each journal by publication date (newest first)
    for publisher in hierarchy:
        for journal in hierarchy[publisher]:
            hierarchy[publisher][journal] = sorted(
                hierarchy[publisher][journal],
                key=lambda x: x.get('publication_date', '0000-00-00'),
                reverse=True
            )
    
    return sort_hierarchy_by_count(hierarchy)

# ============================================================================
# PDF REPORT GENERATION FUNCTIONS
# ============================================================================

def register_russian_font():
    """
    Register a font that supports Cyrillic characters.
    Tries multiple font paths and uses fallback options.
    Returns font name and whether font was found.
    """
    import os
    import sys
    
    font_found = False
    russian_font_name = 'Helvetica'
    
    # Expanded list of font paths for different operating systems
    font_paths = [
        # Linux - DejaVu (most common for Cyrillic)
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
        
        # Linux - Liberation (Red Hat fonts)
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
        
        # Linux - FreeFont
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSerif.ttf',
        
        # Linux - Ubuntu
        '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf',
        '/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf',
        
        # Linux - Noto (Google fonts, supports many scripts)
        '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf',
        '/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf',
        
        # Linux - Arial (if installed)
        '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf',
        
        # Linux - Tahoma (Windows fonts)
        '/usr/share/fonts/truetype/msttcorefonts/Tahoma.ttf',
        
        # Linux - Times New Roman
        '/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf',
        
        # Linux - system fonts
        '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/ttf-liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf',
        
        # macOS - system fonts
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/Arial.ttf',
        '/System/Library/Fonts/HelveticaNeue.ttf',
        '/System/Library/Fonts/AppleGothic.ttf',
        '/Library/Fonts/Arial.ttf',
        '/Library/Fonts/Helvetica.ttf',
        '/Library/Fonts/Microsoft/Arial.ttf',
        '/Library/Fonts/Microsoft/Calibri.ttf',
        
        # Windows - system fonts
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
        'C:/Windows/Fonts/ariali.ttf',
        'C:/Windows/Fonts/arialbi.ttf',
        'C:/Windows/Fonts/times.ttf',
        'C:/Windows/Fonts/timesbd.ttf',
        'C:/Windows/Fonts/timesi.ttf',
        'C:/Windows/Fonts/timesbi.ttf',
        'C:/Windows/Fonts/calibri.ttf',
        'C:/Windows/Fonts/calibrib.ttf',
        'C:/Windows/Fonts/calibrii.ttf',
        'C:/Windows/Fonts/calibriz.ttf',
        'C:/Windows/Fonts/consola.ttf',
        'C:/Windows/Fonts/consolab.ttf',
        'C:/Windows/Fonts/consolai.ttf',
        'C:/Windows/Fonts/consolaz.ttf',
        'C:/Windows/Fonts/cour.ttf',
        'C:/Windows/Fonts/courbd.ttf',
        'C:/Windows/Fonts/couri.ttf',
        'C:/Windows/Fonts/courbi.ttf',
        'C:/Windows/Fonts/georgia.ttf',
        'C:/Windows/Fonts/georgiab.ttf',
        'C:/Windows/Fonts/georgiai.ttf',
        'C:/Windows/Fonts/georgiaz.ttf',
        'C:/Windows/Fonts/impact.ttf',
        'C:/Windows/Fonts/trebuc.ttf',
        'C:/Windows/Fonts/trebucbd.ttf',
        'C:/Windows/Fonts/trebucbi.ttf',
        'C:/Windows/Fonts/trebucit.ttf',
        'C:/Windows/Fonts/verdana.ttf',
        'C:/Windows/Fonts/verdanab.ttf',
        'C:/Windows/Fonts/verdanai.ttf',
        'C:/Windows/Fonts/verdanaz.ttf',
        
        # Windows - additional fonts
        'C:/Windows/Fonts/msyh.ttf',  # Microsoft YaHei (Chinese, but supports Cyrillic)
        'C:/Windows/Fonts/msyhbd.ttf',
        'C:/Windows/Fonts/msyhl.ttf',
        
        # Fallback: look in current directory for bundled fonts
        os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf'),
        os.path.join(os.path.dirname(__file__), 'fonts', 'LiberationSans-Regular.ttf'),
        os.path.join(os.getcwd(), 'fonts', 'DejaVuSans.ttf'),
        os.path.join(os.getcwd(), 'fonts', 'LiberationSans-Regular.ttf'),
        
        # Docker/container paths
        '/app/fonts/DejaVuSans.ttf',
        '/app/fonts/LiberationSans-Regular.ttf',
    ]
    
    # First, try to register a font
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('RussianFont', font_path))
                russian_font_name = 'RussianFont'
                font_found = True
                logger.info(f"Successfully registered Cyrillic font from: {font_path}")
                return russian_font_name, True
            except Exception as e:
                logger.warning(f"Failed to register font from {font_path}: {e}")
                continue
    
    # If no TTF font found, try to use system fonts with different names
    if not font_found:
        # Try to use built-in fonts that might support Cyrillic
        try:
            # On some systems, Helvetica with Cyrillic encoding might work
            pdfmetrics.registerFont(TTFont('Helvetica', 'Helvetica'))
            russian_font_name = 'Helvetica'
            font_found = True
            logger.info("Using Helvetica as fallback font")
        except:
            pass
    
    if not font_found:
        # Last resort: try to use a font that might be available
        try:
            # Some systems have these fonts available
            pdfmetrics.registerFont(TTFont('Courier', 'Courier'))
            russian_font_name = 'Courier'
            font_found = True
            logger.info("Using Courier as fallback font")
        except:
            pass
    
    if not font_found:
        logger.warning("No Cyrillic font found. Text may not display correctly.")
        logger.warning("Please install a font like DejaVu Sans or Liberation Sans.")
        logger.warning("On Ubuntu/Debian: apt-get install fonts-dejavu-core fonts-liberation")
        logger.warning("On CentOS/RHEL: yum install dejavu-sans-fonts liberation-fonts")
        russian_font_name = 'Helvetica'
    
    return russian_font_name, font_found

def ensure_cyrillic_text(text):
    """
    Ensure text contains proper Cyrillic characters.
    If text has Unicode replacement characters or invalid characters, try to fix them.
    """
    if text is None:
        return ""
    if not text:
        return ""
    
    # Convert to string if needed
    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8', 'ignore')
        except:
            try:
                text = text.decode('cp1251', 'ignore')
            except:
                text = text.decode('latin-1', 'ignore')
    
    # Normalize Unicode
    import unicodedata
    text = unicodedata.normalize('NFC', str(text))
    
    # Replace common problematic characters
    replacements = {
        '�': '',  # Unicode replacement character
        '■': '',  # Black square (used for missing characters)
        '□': '',  # White square
        '▬': '',  # Black rectangle
        '▮': '',  # Black vertical rectangle
        '▯': '',  # White vertical rectangle
        '▰': '',  # Black parallelogram
        '▱': '',  # White parallelogram
        '◼': '',  # Black medium square
        '◻': '',  # White medium square
        '◾': '',  # Black medium small square
        '◽': '',  # White medium small square
        '▪': '',  # Black small square
        '▫': '',  # White small square
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove invisible characters
    text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
    
    return text.strip()

def clean_text(text, font_available=True):
    """
    Clean text for PDF display, preserving allowed special characters including slash.
    Handles Cyrillic characters properly.
    """
    if text is None:
        return ""
    if not text:
        return ""
    
    # First ensure proper Cyrillic handling
    text = ensure_cyrillic_text(text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Escape XML/HTML special characters for ReportLab
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # If font doesn't support Cyrillic, warn but keep text
    if not font_available:
        # Check if text contains Cyrillic characters
        if any(ord(char) > 0x0400 and ord(char) < 0x0500 for char in text):
            logger.debug(f"Text contains Cyrillic characters: {text[:50]}...")
    
    # Allow: letters (Latin and Cyrillic), spaces, dots, commas, hyphens, apostrophes, parentheses, digits, and slash
    # But don't strip Cyrillic characters
    allowed_pattern = r'[^a-zA-Zа-яА-ЯёЁ\s\.\,\-\'\(\)\d\/]'
    text = re.sub(allowed_pattern, '', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

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

def generate_pdf_by_country_affiliation(journal_name: str, years: List[int], countries: List[str],
                                       hierarchy: Dict, logo_path: str = None,
                                       report_title: str = "Report by Country & Affiliation") -> bytes:
    """Generate PDF report grouping articles by Country -> Affiliation."""
    # Register font and get availability
    russian_font_name, font_available = register_russian_font()
    
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
        textColor=colors.HexColor('#e74c3c'),
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
    
    toc_country_style = ParagraphStyle(
        'TOCCountryStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#e74c3c'),
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
    
    story.append(Paragraph("Retracted Articles Report", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name, font_available)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    countries_str = format_countries_for_filename(countries)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    story.append(Paragraph(f"Countries: {countries_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_articles} retracted articles,
    grouped by Country and Affiliation.
    
    Only articles with at least one author from the selected countries are included.
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Retracted Articles", str(total_articles)],
        ["Countries", str(total_countries)],
        ["Report Type", report_title],
    ]
    
    stats_table = Table(stats_data, colWidths=[doc.width/2.5, doc.width/3])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
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
    
    story.append(Paragraph("Table of Contents", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    for country, affiliations in hierarchy.items():
        country_articles = sum(len(articles) for articles in affiliations.values())
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(country, font_available)}</b> — {country_articles} retracted articles</a>', toc_country_style))
        
        for affiliation, articles in affiliations.items():
            aff_articles = len(articles)
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{aff_anchor_id}">{clean_text(affiliation, font_available)}</a> — {aff_articles} retracted articles', toc_affiliation_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    for country, affiliations in hierarchy.items():
        country_articles = sum(len(articles) for articles in affiliations.values())
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(country, font_available)} — {country_articles} retracted articles", country_style))
        story.append(Spacer(1, 0.3*cm))
        
        for affiliation, articles in affiliations.items():
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            aff_anchor_para = Paragraph(f'<a name="{aff_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(aff_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{clean_text(affiliation, font_available)} — {len(articles)} retracted articles", affiliation_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, article in enumerate(articles, 1):
                title = clean_text(article.get('title', 'No title'), font_available)
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {title}", article_title_style))
                
                authors = clean_text(article.get('authors_str', 'Authors not specified'), font_available)
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors}", authors_style))
                
                # Journal and publisher info
                journal = clean_text(article.get('journal_name', ''), font_available)
                publisher = clean_text(article.get('publisher', ''), font_available)
                
                if journal:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Journal:</b> {journal}", meta_style))
                if publisher:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Publisher:</b> {publisher}", meta_style))
                
                # Publication details
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
                
                # DOI
                doi_url = article.get('doi_url', '')
                if doi_url:
                    doi_url_clean = clean_doi_url(doi_url)
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style))
                
                # Retraction badge
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#e74c3c'><b>⚠️ RETRACTED</b></font>", meta_style))
                
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
    This report contains {total_articles} retracted articles from {total_countries} countries,
    grouped by country and affiliation.
    
    The articles are organized by country and affiliation, sorted by the number of retracted articles.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retracted Article Detector", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_pdf_by_authors(journal_name: str, years: List[int], countries: List[str],
                           author_articles: Dict[str, List[dict]], logo_path: str = None,
                           report_title: str = "Report by Author") -> bytes:
    """Generate PDF report grouping articles by author."""
    # Register font and get availability
    russian_font_name, font_available = register_russian_font()
    
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
        textColor=colors.HexColor('#e74c3c'),
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
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=2,
        leftIndent=20,
        fontName=russian_font_name
    )
    
    toc_author_style = ParagraphStyle(
        'TOCAuthorStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#e74c3c'),
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
    
    total_articles = sum(len(articles) for articles in author_articles.values())
    total_authors = len(author_articles)
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo at beginning
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retracted Articles Report by Author", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name, font_available)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    countries_str = format_countries_for_filename(countries)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    story.append(Paragraph(f"Countries (authors only from): {countries_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_articles} retracted articles,
    grouped by author.
    
    Only authors from the selected countries are included.
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Retracted Articles", str(total_articles)],
        ["Unique Authors", str(total_authors)],
        ["Report Type", report_title],
    ]
    
    stats_table = Table(stats_data, colWidths=[doc.width/2.5, doc.width/3])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
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
    
    story.append(Paragraph("Table of Contents", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    for author, articles in author_articles.items():
        article_count = len(articles)
        anchor_id = f"author_{hashlib.md5(author.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(author, font_available)}</b> — {article_count} retracted articles</a>', toc_author_style))
    
    story.append(PageBreak())
    
    for author, articles in author_articles.items():
        anchor_id = f"author_{hashlib.md5(author.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(author, font_available)} — {len(articles)} retracted articles", author_style))
        story.append(Spacer(1, 0.3*cm))
        
        for idx, article in enumerate(articles, 1):
            title = clean_text(article.get('title', 'No title'), font_available)
            story.append(Paragraph(f"&nbsp;&nbsp;{idx}. {title}", article_title_style))
            
            authors = clean_text(article.get('authors_str', 'Authors not specified'), font_available)
            story.append(Paragraph(f"&nbsp;&nbsp;<b>Authors:</b> {authors}", authors_style))
            
            # Journal and publisher info
            journal = clean_text(article.get('journal_name', ''), font_available)
            publisher = clean_text(article.get('publisher', ''), font_available)
            
            if journal:
                story.append(Paragraph(f"&nbsp;&nbsp;<b>Journal:</b> {journal}", meta_style))
            if publisher:
                story.append(Paragraph(f"&nbsp;&nbsp;<b>Publisher:</b> {publisher}", meta_style))
            
            # Publication details
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
                story.append(Paragraph(f"&nbsp;&nbsp;{', '.join(meta_parts)}", meta_style))
            
            # DOI
            doi_url = article.get('doi_url', '')
            if doi_url:
                doi_url_clean = clean_doi_url(doi_url)
                story.append(Paragraph(f"&nbsp;&nbsp;<b>DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style))
            
            # Retraction badge
            story.append(Paragraph(f"&nbsp;&nbsp;<font color='#e74c3c'><b>⚠️ RETRACTED</b></font>", meta_style))
            
            story.append(Spacer(1, 0.15*cm))
            
            if idx < len(articles):
                story.append(Paragraph("&nbsp;&nbsp;" + "─" * 50, separator_style))
                story.append(Spacer(1, 0.1*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_articles} retracted articles from {total_authors} unique authors.
    
    The authors are sorted by the number of retracted articles.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retracted Article Detector", footer_style))
    
    doc.build(story)
    return buffer.getvalue()
                               
def generate_pdf_by_publisher_journal(journal_name: str, years: List[int], countries: List[str],
                                     hierarchy: Dict, logo_path: str = None,
                                     report_title: str = "Report by Publisher & Journal") -> bytes:
    """Generate PDF report grouping articles by Publisher -> Journal."""
    # Register font and get availability
    russian_font_name, font_available = register_russian_font()
    
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
        textColor=colors.HexColor('#e74c3c'),
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
    
    toc_publisher_style = ParagraphStyle(
        'TOCPublisherStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#e74c3c'),
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
    
    # Add logo at beginning
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retracted Articles Report by Publisher & Journal", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name, font_available)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    countries_str = format_countries_for_filename(countries)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    story.append(Paragraph(f"Countries: {countries_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_articles} retracted articles,
    grouped by Publisher and Journal.
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Retracted Articles", str(total_articles)],
        ["Publishers", str(total_publishers)],
        ["Report Type", report_title],
    ]
    
    stats_table = Table(stats_data, colWidths=[doc.width/2.5, doc.width/3])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
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
    
    story.append(Paragraph("Table of Contents", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    for publisher, journals in hierarchy.items():
        publisher_articles = sum(len(articles) for articles in journals.values())
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(publisher, font_available)}</b> — {publisher_articles} retracted articles</a>', toc_publisher_style))
        
        for journal, articles in journals.items():
            journal_articles = len(articles)
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{journal_anchor_id}">{clean_text(journal, font_available)}</a> — {journal_articles} retracted articles', toc_journal_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    for publisher, journals in hierarchy.items():
        publisher_articles = sum(len(articles) for articles in journals.values())
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(publisher, font_available)} — {publisher_articles} retracted articles", publisher_style))
        story.append(Spacer(1, 0.3*cm))
        
        for journal, articles in journals.items():
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            journal_anchor_para = Paragraph(f'<a name="{journal_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(journal_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{clean_text(journal, font_available)} — {len(articles)} retracted articles", journal_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, article in enumerate(articles, 1):
                title = clean_text(article.get('title', 'No title'), font_available)
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {title}", article_title_style))
                
                authors = clean_text(article.get('authors_str', 'Authors not specified'), font_available)
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors}", authors_style))
                
                # Publication details
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
                
                # DOI
                doi_url = article.get('doi_url', '')
                if doi_url:
                    doi_url_clean = clean_doi_url(doi_url)
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style))
                
                # Retraction badge
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#e74c3c'><b>⚠️ RETRACTED</b></font>", meta_style))
                
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
    This report contains {total_articles} retracted articles from {total_publishers} publishers.
    
    The articles are organized by publisher and journal, sorted by the number of retracted articles.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retracted Article Detector", footer_style))
    
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

def step_input_years_countries():
    """Step 1: Input years and countries"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📥 Step 1: Select Publication Years and Countries</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Enter the publication period and countries to analyze retracted articles.</p>
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
            🌍 Countries
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.9rem; color: #666; margin-bottom: 10px;">
        <strong>Supported format:</strong> Country codes separated by '+'
    </div>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px;">
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">RU</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">IT+RU</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">IT+RU+CN</span>
        <span style="background: #e3f2fd; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">US+GB+DE</span>
    </div>
    <div style="font-size: 0.85rem; color: #888; margin-bottom: 10px;">
        Note: Only articles with at least one author from the selected countries will be included.
    </div>
    """, unsafe_allow_html=True)
    
    countries_input = st.text_input(
        "Enter country codes",
        value=st.session_state.get('countries_input', ''),
        placeholder="Example: RU or IT+RU or IT+RU+CN",
        help="Enter country codes separated by '+'. Only articles with authors from these countries will be included."
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if countries_input:
        countries = parse_countries_input(countries_input)
        if countries:
            countries_str = format_countries_for_filename(countries)
            st.markdown(f"""
            <div style="background: #e8f5e9; border-radius: 8px; padding: 12px; border-left: 4px solid #4CAF50; margin: 10px 0;">
                <strong>✅ Selected countries:</strong> {', '.join(countries)}
                <br><span style="font-size: 0.85rem; color: #666;">Total: {len(countries)} countries</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #ffebee; border-radius: 8px; padding: 12px; border-left: 4px solid #f44336; margin: 10px 0;">
                <strong>❌ Invalid format:</strong> Please check your input.
                <br><span style="font-size: 0.85rem; color: #666;">Example: RU or IT+RU or IT+RU+CN</span>
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
            
            if not countries_input:
                st.error("❌ Please enter at least one country code.")
                return
            
            countries = parse_countries_input(countries_input)
            if not countries:
                st.error("❌ Invalid country format. Please check your input.")
                return
            
            # Clear previous data
            if 'retracted_works' in st.session_state:
                del st.session_state.retracted_works
            if 'pdf_cache' in st.session_state:
                del st.session_state.pdf_cache
            if 'all_reports_generated' in st.session_state:
                del st.session_state.all_reports_generated
            
            st.session_state.years_input = years_input
            st.session_state.countries_input = countries_input
            st.session_state.selected_years = years
            st.session_state.selected_countries = countries
            st.session_state.current_step = 2
            st.rerun()

def step_analysis_results():
    """Step 2: Analysis and Results"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 2: Analysis in Progress</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Fetching retracted articles from OpenAlex...</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'selected_years' not in st.session_state or 'selected_countries' not in st.session_state:
        st.error("❌ No data available. Please go back to Step 1.")
        return
    
    # Back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 1
            # Clear analysis data
            if 'retracted_works' in st.session_state:
                del st.session_state.retracted_works
            if 'pdf_cache' in st.session_state:
                del st.session_state.pdf_cache
            if 'all_reports_generated' in st.session_state:
                del st.session_state.all_reports_generated
            st.rerun()
    
    years = st.session_state.selected_years
    countries = st.session_state.selected_countries
    
    # Fetch retracted works if not already fetched
    if 'retracted_works' not in st.session_state:
        with st.spinner(f"Fetching retracted articles for {len(years)} years and {len(countries)} countries..."):
            retracted_works = fetch_retracted_works_sync(years, countries)
            
            if not retracted_works:
                st.error("❌ No retracted works found for the specified years and countries.")
                return
            
            enriched_works = []
            for work in retracted_works:
                enriched = enrich_retracted_work(work)
                if enriched.get('title') and enriched.get('title') != 'No title':
                    enriched_works.append(enriched)
            
            st.session_state.retracted_works = enriched_works
    
    enriched_works = st.session_state.retracted_works
    
    if not enriched_works:
        st.warning("⚠️ No valid retracted works found after enrichment.")
        return
    
    # Statistics
    total_articles = len(enriched_works)
    
    # Count countries
    all_countries = set()
    for work in enriched_works:
        for country in work.get('all_countries', []):
            all_countries.add(country)
    
    # Count authors
    all_authors = set()
    for work in enriched_works:
        for author in work.get('authors_full', []):
            all_authors.add(author['name'])
    
    # Count publishers
    all_publishers = set()
    for work in enriched_works:
        publisher = work.get('publisher', '')
        if publisher:
            all_publishers.add(publisher)
    
    # Display metrics
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
            <div class="metric-value">{len(all_countries)}</div>
            <div class="metric-label">Countries</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(all_authors):,}</div>
            <div class="metric-label">Unique Authors</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(all_publishers)}</div>
            <div class="metric-label">Publishers</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📥 Download Reports")
    
    journal_name = f"Retracted Articles ({format_year_filter_for_filename(years)})"
    journal_abbr = generate_journal_abbreviation(journal_name)
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
    
    # Generate unique cache keys
    years_hash = hashlib.md5(','.join(map(str, years)).encode()).hexdigest()[:8]
    countries_hash = hashlib.md5('+'.join(countries).encode()).hexdigest()[:8]
    
    cache_key_country = f"country_{years_hash}_{countries_hash}"
    cache_key_author = f"author_{years_hash}_{countries_hash}"
    cache_key_publisher = f"publisher_{years_hash}_{countries_hash}"
    
    # Generate groupings
    with st.spinner("Generating report groupings..."):
        # Group by Country -> Affiliation
        country_hierarchy = group_articles_by_country_affiliation(enriched_works, countries)
        
        # Group by Author
        author_articles = group_articles_by_authors(enriched_works, countries)
        
        # Group by Publisher -> Journal
        publisher_hierarchy = group_articles_by_publisher_journal(enriched_works)
    
    col_gen1, col_gen2, col_gen3 = st.columns([1, 2, 1])
    with col_gen2:
        if not st.session_state.all_reports_generated:
            if st.button("⚡ Generate All Reports", type="primary", use_container_width=True):
                with st.spinner("Generating all reports..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("Generating Country → Affiliation report...")
                    if cache_key_country not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_country] = generate_pdf_by_country_affiliation(
                            journal_name, years, countries,
                            country_hierarchy, logo_path,
                            "Report by Country & Affiliation"
                        )
                    progress_bar.progress(0.33)
                    
                    status_text.text("Generating Author report...")
                    if cache_key_author not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_author] = generate_pdf_by_authors(
                            journal_name, years, countries,
                            author_articles, logo_path,
                            "Report by Author"
                        )
                    progress_bar.progress(0.66)
                    
                    status_text.text("Generating Publisher → Journal report...")
                    if cache_key_publisher not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_publisher] = generate_pdf_by_publisher_journal(
                            journal_name, years, countries,
                            publisher_hierarchy, logo_path,
                            "Report by Publisher & Journal"
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
        st.markdown(f"*{len(country_hierarchy)} countries*")
        
        if cache_key_country in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_country]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"{journal_abbr}_{format_year_filter_for_filename(years)}_{format_countries_for_filename(countries)}_country_affiliation.pdf"
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
                    pdf_data = generate_pdf_by_country_affiliation(
                        journal_name, years, countries,
                        country_hierarchy, logo_path,
                        "Report by Country & Affiliation"
                    )
                    st.session_state.pdf_cache[cache_key_country] = pdf_data
                    st.rerun()
    
    with col2:
        st.markdown("**👤 Report 2: By Author**")
        st.markdown(f"*{len(author_articles)} authors*")
        
        if cache_key_author in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_author]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"{journal_abbr}_{format_year_filter_for_filename(years)}_{format_countries_for_filename(countries)}_authors.pdf"
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
                    pdf_data = generate_pdf_by_authors(
                        journal_name, years, countries,
                        author_articles, logo_path,
                        "Report by Author"
                    )
                    st.session_state.pdf_cache[cache_key_author] = pdf_data
                    st.rerun()
    
    with col3:
        st.markdown("**📚 Report 3: Publisher → Journal**")
        st.markdown(f"*{len(publisher_hierarchy)} publishers*")
        
        if cache_key_publisher in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_publisher]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"{journal_abbr}_{format_year_filter_for_filename(years)}_{format_countries_for_filename(countries)}_publisher_journal.pdf"
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
                    pdf_data = generate_pdf_by_publisher_journal(
                        journal_name, years, countries,
                        publisher_hierarchy, logo_path,
                        "Report by Publisher & Journal"
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
                    zip_file.writestr(f"{journal_abbr}_{format_year_filter_for_filename(years)}_{format_countries_for_filename(countries)}_country_affiliation.pdf", 
                                     st.session_state.pdf_cache[cache_key_country])
                    zip_file.writestr(f"{journal_abbr}_{format_year_filter_for_filename(years)}_{format_countries_for_filename(countries)}_authors.pdf", 
                                     st.session_state.pdf_cache[cache_key_author])
                    zip_file.writestr(f"{journal_abbr}_{format_year_filter_for_filename(years)}_{format_countries_for_filename(countries)}_publisher_journal.pdf", 
                                     st.session_state.pdf_cache[cache_key_publisher])
                
                zip_data = zip_buffer.getvalue()
                
                col_zip1, col_zip2, col_zip3 = st.columns([1, 2, 1])
                with col_zip2:
                    st.download_button(
                        label="📦 Download All Reports (ZIP archive)",
                        data=zip_data,
                        file_name=f"{journal_abbr}_{format_year_filter_for_filename(years)}_{format_countries_for_filename(countries)}_all_reports.zip",
                        mime="application/zip",
                        use_container_width=True,
                        key="download_all_zip"
                    )
            except Exception as e:
                st.error(f"Error creating ZIP archive: {e}")
    
    st.markdown("---")
    
    if st.button("🔄 New Analysis", use_container_width=True):
        keys_to_clear = ['current_step', 'years_input', 'countries_input', 'selected_years',
                        'selected_countries', 'retracted_works', 'pdf_cache', 'all_reports_generated']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.current_step = 1
        st.rerun()

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
    steps = ["Input", "Analysis"]
    current_step = st.session_state.current_step
    progress = (current_step - 1) / 1
    
    st.markdown(f"""
    <div class="progress-container" style="background: #f5f5f5; border-radius: 8px; height: 6px; margin: 20px 0; overflow: hidden;">
        <div class="progress-bar" style="height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 8px; transition: width 0.5s ease; width: {progress * 100}%;"></div>
    </div>
    <div class="step-indicator" style="display: flex; justify-content: space-around; margin: 15px 0; font-size: 0.85rem; color: #666;">
        <span class="{'active' if current_step >= 1 else ''}" style="color: {'#667eea' if current_step >= 1 else '#666'}; font-weight: {'600' if current_step >= 1 else '400'};">📥 Input</span>
        <span class="{'active' if current_step >= 2 else ''}" style="color: {'#667eea' if current_step >= 2 else '#666'}; font-weight: {'600' if current_step >= 2 else '400'};">🔍 Analysis</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Display current step
    if st.session_state.current_step == 1:
        step_input_years_countries()
    elif st.session_state.current_step == 2:
        step_analysis_results()
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>© CTA, https://chimicatechnoacta.ru / developed by daM©</p>
        <p style="font-size: 0.7rem; color: #aaa;">Retracted Article Detector with multi-report generation</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
