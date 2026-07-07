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
    page_title="Retraction Article Analyzer Pro*2",
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
# YEAR PARSING FUNCTIONS (ADDED)
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
    """
    if not country_input or not country_input.strip():
        return []
    
    # Split by '+' and clean
    countries = [c.strip().upper() for c in country_input.split('+') if c.strip()]
    return countries

def get_country_name(country_code: str) -> str:
    """
    Get full country name from country code.
    """
    country_names = {
        'RU': 'Russia',
        'IT': 'Italy',
        'CN': 'China',
        'US': 'United States',
        'GB': 'United Kingdom',
        'DE': 'Germany',
        'FR': 'France',
        'JP': 'Japan',
        'CA': 'Canada',
        'AU': 'Australia',
        'BR': 'Brazil',
        'IN': 'India',
        'KR': 'South Korea',
        'NL': 'Netherlands',
        'CH': 'Switzerland',
        'SE': 'Sweden',
        'ES': 'Spain',
        'IT': 'Italy',
        'UA': 'Ukraine',
        'PL': 'Poland',
        'CZ': 'Czech Republic',
        'AT': 'Austria',
        'BE': 'Belgium',
        'DK': 'Denmark',
        'FI': 'Finland',
        'NO': 'Norway',
        'PT': 'Portugal',
        'GR': 'Greece',
        'HU': 'Hungary',
        'RO': 'Romania',
        'BG': 'Bulgaria',
        'HR': 'Croatia',
        'SI': 'Slovenia',
        'SK': 'Slovakia',
        'LT': 'Lithuania',
        'LV': 'Latvia',
        'EE': 'Estonia',
        'IS': 'Iceland',
        'IE': 'Ireland',
        'NZ': 'New Zealand',
        'ZA': 'South Africa',
        'IL': 'Israel',
        'SG': 'Singapore',
        'MY': 'Malaysia',
        'PH': 'Philippines',
        'ID': 'Indonesia',
        'TH': 'Thailand',
        'VN': 'Vietnam',
        'MX': 'Mexico',
        'AR': 'Argentina',
        'CL': 'Chile',
        'CO': 'Colombia',
        'PE': 'Peru'
    }
    return country_names.get(country_code.upper(), country_code)

# ============================================================================
# RETRACTION DETECTION FUNCTIONS
# ============================================================================

def is_retraction_notice(work: dict) -> bool:
    """
    Check if a work is a retraction notice.
    Checks type and display_name/title for retraction keywords.
    """
    if not work:
        return False
    
    # Check type - could be erratum, retraction, or other
    work_type = work.get('type', '').lower()
    
    # Check if type is erratum or retraction
    if work_type in ['erratum', 'retraction', 'retraction-notice']:
        pass
    elif 'retract' in work_type:
        pass
    else:
        # If type doesn't match, check if it's a retraction notice by other means
        pass
    
    # Check display_name and title for retraction keywords
    display_name = work.get('display_name', '').lower()
    title = work.get('title', '').lower()
    
    retraction_keywords = ['retraction', 'retracted', 'retract', 'withdrawal', 'withdrawn']
    
    for keyword in retraction_keywords:
        if keyword in display_name or keyword in title:
            return True
    
    # Also check if the work has a relationship to a retracted work
    # This could be through referenced_works or other fields
    
    return False

def is_retracted_article(work: dict) -> bool:
    """
    Check if a work is a retracted article.
    """
    if not work:
        return False
    
    return work.get('is_retracted', False)

def extract_core_title(title: str) -> str:
    """
    Extract core title from retraction notice or retracted article.
    Removes prefixes like "Retraction Notice to", "RETRACTED:", etc.
    """
    if not title:
        return ""
    
    # Remove common prefixes
    prefixes = [
        r'^Retraction Notice to\s+["“]?',
        r'^RETRACTED:\s*',
        r'^Retraction:\s*',
        r'^Notice of Retraction:\s*',
        r'^Retraction notice for\s+["“]?',
        r'^Withdrawal Notice to\s+["“]?',
        r'^Notice of Withdrawal:\s*',
        r'^Withdrawn:\s*',
        r'^Retraction of\s+["“]?',
        r'^Retracted:\s*',
        r'^RETRACTED:\s*["“]?',
        r'^Notice to\s+["“]?',
        r'^Retraction Notice\s+["“]?',
        r'^Retraction notice\s+["“]?',
        r'^RETRACTION\s+["“]?',
        r'^RETRACTION NOTICE\s+["“]?',
        r'^Notice of Retraction\s+["“]?',
        r'^Notice of withdrawal\s+["“]?',
    ]
    
    clean_title = title
    for prefix in prefixes:
        clean_title = re.sub(prefix, '', clean_title, flags=re.IGNORECASE)
    
    # Remove quotes
    clean_title = clean_title.strip('"“”\'')
    
    return clean_title.strip()

def find_core_title_match(retraction_notice_title: str, article_title: str) -> bool:
    """
    Check if retraction notice and article share the same core title.
    """
    if not retraction_notice_title or not article_title:
        return False
    
    core_notice = extract_core_title(retraction_notice_title)
    core_article = extract_core_title(article_title)
    
    # If either core title is empty, try more lenient matching
    if not core_notice or not core_article:
        # Try to find common substring (at least 15 characters)
        notice_lower = retraction_notice_title.lower()
        article_lower = article_title.lower()
        
        # Check if article title is contained in notice title (or vice versa)
        if len(article_lower) > 20 and article_lower in notice_lower:
            return True
        if len(notice_lower) > 20 and notice_lower in article_lower:
            return True
        
        # Check for common significant words
        notice_words = set(re.findall(r'\b[a-z]{4,}\b', notice_lower))
        article_words = set(re.findall(r'\b[a-z]{4,}\b', article_lower))
        common_words = notice_words.intersection(article_words)
        
        # If more than 40% of words match (or at least 3 words), consider it a match
        if len(common_words) >= 3 and len(common_words) / max(len(notice_words), 1) > 0.3:
            return True
        
        return False
    
    # Compare core titles
    core_notice = core_notice.lower()
    core_article = core_article.lower()
    
    # Exact match
    if core_notice == core_article:
        return True
    
    # One contains the other (if at least 10 characters)
    if len(core_notice) > 10 and core_notice in core_article:
        return True
    if len(core_article) > 10 and core_article in core_notice:
        return True
    
    # Check significant words
    notice_words = set(re.findall(r'\b[a-z]{4,}\b', core_notice))
    article_words = set(re.findall(r'\b[a-z]{4,}\b', core_article))
    common_words = notice_words.intersection(article_words)
    
    if len(common_words) >= 3 and len(common_words) / max(len(notice_words), 1) > 0.3:
        return True
    
    return False

def find_related_retracted_article(notice_work: dict, all_works: List[dict]) -> Optional[dict]:
    """
    Find the retracted article related to a retraction notice.
    """
    if not notice_work or not all_works:
        return None
    
    notice_title = notice_work.get('title', '')
    if not notice_title:
        return None
    
    # First try to find by referenced_works
    referenced_works = notice_work.get('referenced_works', [])
    if referenced_works:
        for ref in referenced_works:
            for work in all_works:
                work_id = work.get('id', '')
                if ref == work_id and work.get('is_retracted', False):
                    return work
    
    # Then try by title matching
    best_match = None
    best_score = 0
    
    for work in all_works:
        if work.get('id') == notice_work.get('id'):
            continue
        
        if not work.get('is_retracted', False):
            continue
        
        work_title = work.get('title', '')
        if not work_title:
            continue
        
        # Check if titles match
        if find_core_title_match(notice_title, work_title):
            # Calculate a score based on how good the match is
            core_notice = extract_core_title(notice_title)
            core_work = extract_core_title(work_title)
            
            if core_notice and core_work:
                if core_notice.lower() == core_work.lower():
                    return work
                
                # Check word overlap
                notice_words = set(re.findall(r'\b[a-z]{4,}\b', core_notice.lower()))
                work_words = set(re.findall(r'\b[a-z]{4,}\b', core_work.lower()))
                common = notice_words.intersection(work_words)
                score = len(common) / max(len(notice_words), 1)
                
                if score > best_score:
                    best_score = score
                    best_match = work
    
    return best_match

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
    
    async def fetch_retraction_works_by_years(self, years: List[int]) -> List[dict]:
        """
        Fetch retraction notices and retracted articles for given years.
        """
        all_works = []
        years_str = "|".join(map(str, years))
        
        # Fetch retraction notices
        logger.info(f"Fetching retraction notices for years {years}")
        
        # Query for retraction notices (type: erratum + retraction keywords)
        notice_keywords = "retraction%20OR%20retracted%20OR%20withdrawal%20OR%20withdrawn"
        
        # First try to get works with type erratum and retraction keywords
        filter_str = f"type:erratum,publication_year:{years_str}"
        url = f"{OPENALEX_BASE_URL}/works?filter={filter_str}&per-page=200&mailto={MAILTO}"
        
        try:
            response = requests.get(url, headers=POLITE_POOL_HEADER, timeout=60)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                for work in results:
                    if is_retraction_notice(work):
                        all_works.append(work)
                logger.info(f"Found {len(results)} erratum works, {len([w for w in results if is_retraction_notice(w)])} retraction notices")
        except Exception as e:
            logger.error(f"Error fetching retraction notices: {str(e)}")
        
        # Also try to get retracted articles directly
        filter_str = f"is_retracted:true,publication_year:{years_str}"
        url = f"{OPENALEX_BASE_URL}/works?filter={filter_str}&per-page=200&mailto={MAILTO}"
        
        try:
            response = requests.get(url, headers=POLITE_POOL_HEADER, timeout=60)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                for work in results:
                    # Check if already added
                    already_added = False
                    for existing in all_works:
                        if existing.get('id') == work.get('id'):
                            already_added = True
                            break
                    if not already_added:
                        all_works.append(work)
                logger.info(f"Found {len(results)} retracted articles")
        except Exception as e:
            logger.error(f"Error fetching retracted articles: {str(e)}")
        
        # Also try to get retraction notices with other types
        filter_str = f"publication_year:{years_str}"
        url = f"{OPENALEX_BASE_URL}/works?filter={filter_str}&per-page=200&mailto={MAILTO}"
        url += "&search=retraction%20notice%20OR%20retracted%20OR%20withdrawal"
        
        try:
            response = requests.get(url, headers=POLITE_POOL_HEADER, timeout=60)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                for work in results:
                    if is_retraction_notice(work) or work.get('is_retracted', False):
                        already_added = False
                        for existing in all_works:
                            if existing.get('id') == work.get('id'):
                                already_added = True
                                break
                        if not already_added:
                            all_works.append(work)
                logger.info(f"Found {len(results)} additional works from search")
        except Exception as e:
            logger.error(f"Error fetching from search: {str(e)}")
        
        return all_works

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

def fetch_retraction_works_sync(years: List[int]) -> List[dict]:
    """
    Fetch retraction notices and retracted articles synchronously.
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    async def fetch():
        async with OpenAlexAsyncClient() as client:
            return await client.fetch_retraction_works_by_years(years)
    
    result = run_async(fetch())
    progress_bar.empty()
    status_text.empty()
    return result

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

def get_all_countries_from_work(work: dict) -> List[str]:
    """
    Get all countries from all authorships.
    """
    countries = set()
    authorships = work.get('authorships', [])
    
    for authorship in authorships:
        if authorship:
            institutions = authorship.get('institutions', [])
            for inst in institutions:
                if inst:
                    country = inst.get('country_code', '')
                    if country:
                        countries.add(country.upper())
                    else:
                        country_name = inst.get('country', '')
                        if country_name:
                            countries.add(country_name)
    
    return list(countries)

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
    
    # Check for retracted article
    if work.get('is_retracted', False):
        return ('Retracted Article', '#c0392b', '🔴')
    
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
    
    # Get all countries
    countries = get_all_countries_from_work(work)
    
    # Check if retracted
    is_retracted = work.get('is_retracted', False)
    is_retraction_notice_flag = is_retraction_notice(work)
    
    enriched = {
        'doi': doi_clean,
        'doi_url': f"https://doi.org/{doi_clean}" if doi_clean else '',
        'title': work.get('title', 'No title'),
        'display_name': work.get('display_name', ''),
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
        'countries': countries,
        'is_retracted': is_retracted,
        'is_retraction_notice': is_retraction_notice_flag,
        'id': work.get('id', ''),
        'referenced_works': work.get('referenced_works', [])
    }
    
    return enriched

# ============================================================================
# RETRACTION DATA PROCESSING FUNCTIONS
# ============================================================================

def process_retraction_data(works: List[dict], selected_countries: List[str]) -> Dict[str, Any]:
    """
    Process works to identify retractions and pair notices with articles.
    Returns structured data for report generation.
    """
    if not works:
        return {
            'retraction_notices': [],
            'retracted_articles': [],
            'paired_retractions': [],
            'unpaired_notices': [],
            'unpaired_retracted': [],
            'all_works': []
        }
    
    # Enrich all works
    enriched_works = []
    for work in works:
        enriched = enrich_work_data_full(work)
        if enriched:
            enriched_works.append(enriched)
    
    # Separate retraction notices and retracted articles
    retraction_notices = [w for w in enriched_works if w.get('is_retraction_notice', False)]
    retracted_articles = [w for w in enriched_works if w.get('is_retracted', False)]
    
    # Filter by selected countries if specified
    if selected_countries:
        filtered_notices = []
        for notice in retraction_notices:
            notice_countries = notice.get('countries', [])
            if any(c in selected_countries for c in notice_countries):
                filtered_notices.append(notice)
        retraction_notices = filtered_notices
        
        filtered_articles = []
        for article in retracted_articles:
            article_countries = article.get('countries', [])
            if any(c in selected_countries for c in article_countries):
                filtered_articles.append(article)
        retracted_articles = filtered_articles
    
    # Pair retraction notices with retracted articles
    paired_retractions = []
    unpaired_notices = []
    unpaired_retracted = []
    
    # Try to pair each notice with an article
    for notice in retraction_notices:
        notice_title = notice.get('title', '')
        notice_doi = notice.get('doi', '')
        
        # Find matching retracted article
        matched_article = None
        for article in retracted_articles:
            article_title = article.get('title', '')
            if find_core_title_match(notice_title, article_title):
                matched_article = article
                break
        
        if matched_article:
            paired_retractions.append({
                'notice': notice,
                'article': matched_article,
                'paired': True
            })
        else:
            unpaired_notices.append(notice)
    
    # Find unpaired retracted articles
    paired_article_dois = set()
    for pair in paired_retractions:
        article_doi = pair['article'].get('doi', '')
        if article_doi:
            paired_article_dois.add(article_doi)
    
    for article in retracted_articles:
        article_doi = article.get('doi', '')
        if article_doi not in paired_article_dois:
            # Check if this article is referenced by any notice
            is_referenced = False
            for notice in retraction_notices:
                referenced = notice.get('referenced_works', [])
                article_id = article.get('id', '')
                if article_id in referenced:
                    is_referenced = True
                    break
            
            if not is_referenced:
                unpaired_retracted.append(article)
    
    return {
        'retraction_notices': retraction_notices,
        'retracted_articles': retracted_articles,
        'paired_retractions': paired_retractions,
        'unpaired_notices': unpaired_notices,
        'unpaired_retracted': unpaired_retracted,
        'all_works': enriched_works
    }

def group_retractions_by_country_affiliation(paired_retractions: List[dict], sort_option: str = 'by_count') -> Dict[str, Dict[str, List[dict]]]:
    """
    Group retractions by Country -> Affiliation.
    Sorted according to sort_option: 'alphabetical' or 'by_count'.
    An article can appear under multiple countries if it has authors from different countries.
    """
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for pair in paired_retractions:
        article = pair.get('article', {})
        countries = article.get('countries', ['Unknown'])
        if not countries:
            countries = ['Unknown']
        
        affiliations = article.get('affiliations', ['Unknown Affiliation'])
        if not affiliations:
            affiliations = ['Unknown Affiliation']
        else:
            affiliations = [aff for aff in affiliations if aff is not None]
            if not affiliations:
                affiliations = ['Unknown Affiliation']
        
        for country in countries:
            for aff in affiliations:
                hierarchy[country][aff].append(pair)
    
    # Sort top-level countries
    if sort_option == 'by_count':
        country_items = []
        for country in hierarchy.keys():
            if country is not None:
                total_count = sum(len(pairs) for pairs in hierarchy[country].values())
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
            sorted_pairs = sorted(
                hierarchy[country][affiliation],
                key=lambda x: x['article'].get('cited_by_count', 0) if x['article'].get('cited_by_count') is not None else 0,
                reverse=True
            )
            sorted_hierarchy[country][affiliation] = sorted_pairs
    
    return sorted_hierarchy

def group_retractions_by_author(paired_retractions: List[dict]) -> Dict[str, List[dict]]:
    """
    Group retractions by unique author (last name + first initial).
    Each article appears under every author.
    """
    author_groups = defaultdict(list)
    
    for pair in paired_retractions:
        article = pair.get('article', {})
        authors = article.get('authors_list', [])
        
        for author in authors:
            if not author:
                continue
            
            # Extract last name and first initial
            author_parts = author.split()
            if not author_parts:
                continue
            
            last_name = author_parts[-1]
            first_initial = author_parts[0][0] if author_parts[0] else ''
            author_key = f"{last_name} {first_initial}."
            
            author_groups[author_key].append(pair)
    
    # Sort by number of retractions (descending)
    sorted_authors = sorted(
        author_groups.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    return dict(sorted_authors)

def group_retractions_by_publisher_journal(paired_retractions: List[dict], sort_option: str = 'by_count') -> Dict[str, Dict[str, List[dict]]]:
    """
    Group retractions by Publisher -> Journal.
    Sorted according to sort_option: 'alphabetical' or 'by_count'.
    """
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for pair in paired_retractions:
        article = pair.get('article', {})
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
        hierarchy[publisher][journal].append(pair)
    
    # Sort top-level publishers
    if sort_option == 'by_count':
        publisher_items = []
        for publisher in hierarchy.keys():
            if publisher is not None:
                total_count = sum(len(pairs) for pairs in hierarchy[publisher].values())
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
            sorted_pairs = sorted(
                hierarchy[publisher][journal],
                key=lambda x: x['article'].get('cited_by_count', 0) if x['article'].get('cited_by_count') is not None else 0,
                reverse=True
            )
            sorted_hierarchy[publisher][journal] = sorted_pairs
    
    return sorted_hierarchy

# ============================================================================
# PDF REPORT GENERATION FUNCTIONS FOR RETRACTION
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

def generate_pdf_retractions_by_country_affiliation(report_name: str, years: List[int],
                                                    hierarchy: Dict, selected_countries: List[str],
                                                    logo_path: str = None, sort_option: str = 'by_count') -> bytes:
    """Generate PDF report grouping retractions by Country -> Affiliation."""
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
    
    meta_style_retracted = ParagraphStyle(
        'MetaRetracted',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#c0392b'),
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
    
    total_pairs = sum(len(pairs) for country in hierarchy.values() 
                      for affiliation in country.values() 
                      for pairs in [affiliation])
    total_countries = len(hierarchy)
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo at beginning with preserved aspect ratio
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"«{clean_text(report_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Analysis period: {years_str}", subtitle_style))
    
    if selected_countries:
        country_names = [get_country_name(c) for c in selected_countries]
        story.append(Paragraph(f"Selected countries: {', '.join(country_names)}", subtitle_style))
    
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_pairs} retracted articles (with retraction notices)
    grouped by Country and Affiliation.
    
    <b>Sorting:</b> By number of retractions (descending)
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Retractions", str(total_pairs)],
        ["Countries", str(total_countries)],
        ["Report Type", "Country → Affiliation"],
        ["Sorting", "By Number of Retractions"]
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
        country_articles = sum(len(pairs) for pairs in affiliations.values())
        country_name = get_country_name(country)
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(country_name)}</b> — {country_articles} retractions</a>', toc_country_style))
        
        for affiliation, pairs in affiliations.items():
            aff_count = len(pairs)
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{aff_anchor_id}">{clean_text(affiliation)}</a> — {aff_count} retractions', toc_affiliation_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # Main content
    for country, affiliations in hierarchy.items():
        country_articles = sum(len(pairs) for pairs in affiliations.values())
        country_name = get_country_name(country)
        anchor_id = f"country_{hashlib.md5(country.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(country_name)} — {country_articles} retractions", country_style))
        story.append(Spacer(1, 0.3*cm))
        
        for affiliation, pairs in affiliations.items():
            aff_anchor_id = f"affiliation_{hashlib.md5(f"{country}_{affiliation}".encode('utf-8')).hexdigest()[:8]}"
            aff_anchor_para = Paragraph(f'<a name="{aff_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(aff_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{clean_text(affiliation)} — {len(pairs)} retractions", affiliation_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, pair in enumerate(pairs, 1):
                article = pair.get('article', {})
                notice = pair.get('notice', {})
                
                # Article title
                title = clean_text(article.get('title', 'No title'))
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {title}", article_title_style))
                
                # Authors (full list)
                authors = clean_text(article.get('authors', 'Authors not specified'))
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors}", authors_style))
                
                # Affiliations
                affs = clean_text(article.get('affiliations_str', ''))
                if affs and affs != 'No affiliations specified':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style_default))
                
                # Publication info
                journal_name_article = clean_text(article.get('journal_name', ''))
                publisher = clean_text(article.get('publisher', ''))
                
                if journal_name_article:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Journal:</b> {journal_name_article}", meta_style_default))
                if publisher:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Publisher:</b> {publisher}", meta_style_default))
                
                year = article.get('publication_year', '')
                pub_date = article.get('publication_date', '')
                volume = article.get('volume', '')
                issue = article.get('issue', '')
                pages = article.get('pages', '')
                
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
                
                # Article DOI
                doi_url = article.get('doi_url', '')
                if doi_url:
                    doi_url_clean = clean_doi_url(doi_url)
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>DOI (Article):</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style_default))
                
                # Notice DOI
                notice_doi = notice.get('doi_url', '')
                notice_year = notice.get('publication_year', '')
                notice_date = notice.get('publication_date', '')
                if notice_doi:
                    notice_doi_clean = clean_doi_url(notice_doi)
                    notice_info = f"<b>Retraction Notice:</b> <a href='{notice_doi_clean}'>{notice_doi_clean}</a>"
                    if notice_year:
                        notice_info += f" ({notice_year}"
                        if notice_date and notice_date != '0000-00-00':
                            notice_info += f"-{notice_date}"
                        notice_info += ")"
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{notice_info}", meta_style_notice))
                
                # Citation info
                citations = article.get('cited_by_count', 0)
                citations_per_year = article.get('citations_per_year', 0)
                references = article.get('referenced_works_count', 0)
                oa_status = article.get('oa_status', 'Closed Access')
                
                citation_text = f"<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f} | <b>References:</b> {references} | <b>OA:</b> {oa_status}"
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{citation_text}", citation_style))
                
                # Retraction status
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#c0392b'><b>⚠️ RETRACTED</b></font>", meta_style_retracted))
                
                story.append(Spacer(1, 0.15*cm))
                
                if idx < len(pairs):
                    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;" + "─" * 40, separator_style))
                    story.append(Spacer(1, 0.1*cm))
            
            story.append(Spacer(1, 0.3*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    # Conclusion
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_pairs} retracted articles from the selected countries,
    grouped by {total_countries} countries and their respective affiliations.
    
    The articles are organized by number of retractions in descending order.
    Each entry includes the full list of authors and complete publication information.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end with preserved aspect ratio (smaller)
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retraction Article Analyzer Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_pdf_retractions_by_author(report_name: str, years: List[int],
                                       author_groups: Dict[str, List[dict]],
                                       selected_countries: List[str],
                                       logo_path: str = None) -> bytes:
    """Generate PDF report grouping retractions by author."""
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
        spaceBefore=15,
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
    
    meta_style_default = ParagraphStyle(
        'MetaDefault',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=2,
        leftIndent=30,
        fontName=russian_font_name
    )
    
    meta_style_notice = ParagraphStyle(
        'MetaNotice',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#e74c3c'),
        spaceAfter=2,
        leftIndent=30,
        fontName=russian_font_name
    )
    
    meta_style_retracted = ParagraphStyle(
        'MetaRetracted',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#c0392b'),
        spaceAfter=2,
        leftIndent=30,
        fontName=russian_font_name
    )
    
    citation_style = ParagraphStyle(
        'CitationStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#27AE60'),
        spaceAfter=2,
        leftIndent=30,
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
    
    total_authors = len(author_groups)
    total_retractions = sum(len(pairs) for pairs in author_groups.values())
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo at beginning with preserved aspect ratio
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"«{clean_text(report_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Analysis period: {years_str}", subtitle_style))
    
    if selected_countries:
        country_names = [get_country_name(c) for c in selected_countries]
        story.append(Paragraph(f"Selected countries: {', '.join(country_names)}", subtitle_style))
    
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_retractions} retracted articles grouped by author.
    A total of {total_authors} unique authors are listed.
    
    Each author's articles are shown below, with all co-authors listed.
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Retractions", str(total_retractions)],
        ["Unique Authors", str(total_authors)],
        ["Report Type", "By Author"],
        ["Sorting", "By Number of Retractions"]
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
    
    for author, pairs in author_groups.items():
        anchor_id = f"author_{hashlib.md5(author.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}">{clean_text(author)}</a> — {len(pairs)} retractions', toc_author_style))
    
    story.append(PageBreak())
    
    # Main content
    for author, pairs in author_groups.items():
        anchor_id = f"author_{hashlib.md5(author.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(author)} — {len(pairs)} retractions", author_style))
        story.append(Spacer(1, 0.2*cm))
        
        for idx, pair in enumerate(pairs, 1):
            article = pair.get('article', {})
            notice = pair.get('notice', {})
            
            # Article title
            title = clean_text(article.get('title', 'No title'))
            story.append(Paragraph(f"&nbsp;&nbsp;{idx}. {title}", article_title_style))
            
            # Authors (full list)
            authors_full = clean_text(article.get('authors', 'Authors not specified'))
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors_full}", authors_style))
            
            # Affiliations
            affs = clean_text(article.get('affiliations_str', ''))
            if affs and affs != 'No affiliations specified':
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style_default))
            
            # Publication info
            journal_name_article = clean_text(article.get('journal_name', ''))
            publisher = clean_text(article.get('publisher', ''))
            
            if journal_name_article:
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Journal:</b> {journal_name_article}", meta_style_default))
            if publisher:
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Publisher:</b> {publisher}", meta_style_default))
            
            year = article.get('publication_year', '')
            pub_date = article.get('publication_date', '')
            volume = article.get('volume', '')
            issue = article.get('issue', '')
            pages = article.get('pages', '')
            
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
            
            # Article DOI
            doi_url = article.get('doi_url', '')
            if doi_url:
                doi_url_clean = clean_doi_url(doi_url)
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>DOI (Article):</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style_default))
            
            # Notice DOI
            notice_doi = notice.get('doi_url', '')
            notice_year = notice.get('publication_year', '')
            notice_date = notice.get('publication_date', '')
            if notice_doi:
                notice_doi_clean = clean_doi_url(notice_doi)
                notice_info = f"<b>Retraction Notice:</b> <a href='{notice_doi_clean}'>{notice_doi_clean}</a>"
                if notice_year:
                    notice_info += f" ({notice_year}"
                    if notice_date and notice_date != '0000-00-00':
                        notice_info += f"-{notice_date}"
                    notice_info += ")"
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{notice_info}", meta_style_notice))
            
            # Citation info
            citations = article.get('cited_by_count', 0)
            citations_per_year = article.get('citations_per_year', 0)
            references = article.get('referenced_works_count', 0)
            oa_status = article.get('oa_status', 'Closed Access')
            
            citation_text = f"<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f} | <b>References:</b> {references} | <b>OA:</b> {oa_status}"
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{citation_text}", citation_style))
            
            # Retraction status
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#c0392b'><b>⚠️ RETRACTED</b></font>", meta_style_retracted))
            
            story.append(Spacer(1, 0.15*cm))
            
            if idx < len(pairs):
                story.append(Paragraph("&nbsp;&nbsp;" + "─" * 50, separator_style))
                story.append(Spacer(1, 0.1*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    # Conclusion
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_retractions} retracted articles grouped by {total_authors} authors.
    
    Each author's retracted articles are listed with complete bibliographic information
    and links to the corresponding retraction notices.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end with preserved aspect ratio (smaller)
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retraction Article Analyzer Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_pdf_retractions_by_publisher_journal(report_name: str, years: List[int],
                                                  hierarchy: Dict, selected_countries: List[str],
                                                  logo_path: str = None, sort_option: str = 'by_count') -> bytes:
    """Generate PDF report grouping retractions by Publisher -> Journal."""
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
    
    meta_style_retracted = ParagraphStyle(
        'MetaRetracted',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#c0392b'),
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
    
    total_pairs = sum(len(pairs) for publisher in hierarchy.values() 
                      for journal in publisher.values() 
                      for pairs in [journal])
    total_publishers = len(hierarchy)
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo at beginning with preserved aspect ratio
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Retraction Analysis Report", title_style))
    story.append(Paragraph(f"«{clean_text(report_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Analysis period: {years_str}", subtitle_style))
    
    if selected_countries:
        country_names = [get_country_name(c) for c in selected_countries]
        story.append(Paragraph(f"Selected countries: {', '.join(country_names)}", subtitle_style))
    
    story.append(Spacer(1, 1.5*cm))
    
    intro_text = f"""
    This report contains {total_pairs} retracted articles grouped by Publisher and Journal.
    
    <b>Sorting:</b> By number of retractions (descending)
    """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Retractions", str(total_pairs)],
        ["Publishers", str(total_publishers)],
        ["Report Type", "Publisher → Journal"],
        ["Sorting", "By Number of Retractions"]
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
        publisher_articles = sum(len(pairs) for pairs in journals.values())
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}"><b>{clean_text(publisher)}</b> — {publisher_articles} retractions</a>', toc_publisher_style))
        
        for journal, pairs in journals.items():
            journal_articles = len(pairs)
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{journal_anchor_id}">{clean_text(journal)}</a> — {journal_articles} retractions', toc_journal_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # Main content
    for publisher, journals in hierarchy.items():
        publisher_articles = sum(len(pairs) for pairs in journals.values())
        anchor_id = f"publisher_{hashlib.md5(publisher.encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        story.append(Paragraph(f"{clean_text(publisher)} — {publisher_articles} retractions", publisher_style))
        story.append(Spacer(1, 0.3*cm))
        
        for journal, pairs in journals.items():
            journal_anchor_id = f"journal_{hashlib.md5(f"{publisher}_{journal}".encode('utf-8')).hexdigest()[:8]}"
            journal_anchor_para = Paragraph(f'<a name="{journal_anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
            story.append(journal_anchor_para)
            
            story.append(Paragraph(f"&nbsp;&nbsp;{clean_text(journal)} — {len(pairs)} retractions", journal_style))
            story.append(Spacer(1, 0.2*cm))
            
            for idx, pair in enumerate(pairs, 1):
                article = pair.get('article', {})
                notice = pair.get('notice', {})
                
                # Article title
                title = clean_text(article.get('title', 'No title'))
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{idx}. {title}", article_title_style))
                
                # Authors (full list)
                authors = clean_text(article.get('authors', 'Authors not specified'))
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Authors:</b> {authors}", authors_style))
                
                # Affiliations
                affs = clean_text(article.get('affiliations_str', ''))
                if affs and affs != 'No affiliations specified':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style_default))
                
                # Publication info
                journal_name_article = clean_text(article.get('journal_name', ''))
                
                if journal_name_article:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Journal:</b> {journal_name_article}", meta_style_default))
                
                year = article.get('publication_year', '')
                pub_date = article.get('publication_date', '')
                volume = article.get('volume', '')
                issue = article.get('issue', '')
                pages = article.get('pages', '')
                
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
                
                # Article DOI
                doi_url = article.get('doi_url', '')
                if doi_url:
                    doi_url_clean = clean_doi_url(doi_url)
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>DOI (Article):</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style_default))
                
                # Notice DOI
                notice_doi = notice.get('doi_url', '')
                notice_year = notice.get('publication_year', '')
                notice_date = notice.get('publication_date', '')
                if notice_doi:
                    notice_doi_clean = clean_doi_url(notice_doi)
                    notice_info = f"<b>Retraction Notice:</b> <a href='{notice_doi_clean}'>{notice_doi_clean}</a>"
                    if notice_year:
                        notice_info += f" ({notice_year}"
                        if notice_date and notice_date != '0000-00-00':
                            notice_info += f"-{notice_date}"
                        notice_info += ")"
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{notice_info}", meta_style_notice))
                
                # Citation info
                citations = article.get('cited_by_count', 0)
                citations_per_year = article.get('citations_per_year', 0)
                references = article.get('referenced_works_count', 0)
                oa_status = article.get('oa_status', 'Closed Access')
                
                citation_text = f"<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f} | <b>References:</b> {references} | <b>OA:</b> {oa_status}"
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{citation_text}", citation_style))
                
                # Retraction status
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='#c0392b'><b>⚠️ RETRACTED</b></font>", meta_style_retracted))
                
                story.append(Spacer(1, 0.15*cm))
                
                if idx < len(pairs):
                    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;" + "─" * 40, separator_style))
                    story.append(Spacer(1, 0.1*cm))
            
            story.append(Spacer(1, 0.3*cm))
        
        story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())
    
    # Conclusion
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_pairs} retracted articles from {total_publishers} publishers
    and their respective journals.
    
    The articles are organized by number of retractions in descending order.
    Each entry includes the full list of authors and complete publication information.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end with preserved aspect ratio (smaller)
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using Retraction Article Analyzer Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

# ============================================================================
# UI STEPS - RETRACTION ANALYZER
# ============================================================================

def step_retraction_input():
    """Step 1: Input analysis parameters"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📥 Step 1: Set Analysis Parameters</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Configure the period and countries for retraction analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="filter-section" style="background: rgba(255, 255, 255, 0.9); border-radius: 20px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(102, 126, 234, 0.2);">
        <div class="filter-header" style="font-size: 1.1rem; font-weight: 600; color: #495057; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #667eea;">
            ⚙️ Analysis Configuration
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.9rem; color: #666; margin-bottom: 10px;">
        <strong>Publication year formats:</strong>
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
    
    <div style="font-size: 0.9rem; color: #666; margin-bottom: 10px;">
        <strong>Country format:</strong> Use '+' to combine multiple countries
    </div>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px;">
        <span style="background: #e8f5e9; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; border: 1px solid #4CAF50;">RU</span>
        <span style="background: #e8f5e9; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; border: 1px solid #4CAF50;">IT+RU</span>
        <span style="background: #e8f5e9; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; border: 1px solid #4CAF50;">IT+RU+CN</span>
    </div>
    """, unsafe_allow_html=True)
    
    years_input = st.text_input(
        "📅 Publication years",
        placeholder="Example: 2000 or 2010-2020 or 2015,2018-2020,2022",
        help="Enter years in any format: single year, range, or combination"
    )
    
    country_input = st.text_input(
        "🌍 Countries (ISO codes, use '+' for multiple)",
        placeholder="Example: RU or IT+RU or IT+RU+CN",
        help="Enter country codes separated by '+'"
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
                <strong>❌ Invalid year format:</strong> Please check your input.
            </div>
            """, unsafe_allow_html=True)
    
    if country_input:
        countries = parse_country_filter(country_input)
        if countries:
            country_names = [get_country_name(c) for c in countries]
            st.markdown(f"""
            <div style="background: #e3f2fd; border-radius: 8px; padding: 12px; border-left: 4px solid #2196F3; margin: 10px 0;">
                <strong>✅ Selected countries:</strong> {', '.join(country_names)}
                <br><span style="font-size: 0.85rem; color: #666;">Codes: {', '.join(countries)}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #ffebee; border-radius: 8px; padding: 12px; border-left: 4px solid #f44336; margin: 10px 0;">
                <strong>❌ Invalid country format:</strong> Please use '+' to combine codes.
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
            
            countries = parse_country_filter(country_input) if country_input else []
            
            st.session_state.retraction_years = years
            st.session_state.retraction_countries = countries
            st.session_state.retraction_years_input = years_input
            st.session_state.retraction_country_input = country_input
            st.session_state.current_step = 2
            st.rerun()

def step_retraction_analysis():
    """Step 2: Retraction analysis in progress"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 2: Retraction Analysis in Progress</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Fetching retraction data from OpenAlex...</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'retraction_years' not in st.session_state:
        st.error("❌ No analysis parameters. Please go back to Step 1.")
        return
    
    # Back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    
    years = st.session_state.retraction_years
    countries = st.session_state.retraction_countries
    
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
            <div class="metric-value">~{len(years)*5}s</div>
            <div class="metric-label">Est. Time</div>
        </div>
        """, unsafe_allow_html=True)
    
    with st.spinner("Fetching retraction data from OpenAlex..."):
        works = fetch_retraction_works_sync(years)
        
        if not works:
            st.error("❌ No retraction data found for the selected period.")
            return
        
        processed = process_retraction_data(works, countries)
        
        st.session_state.retraction_works = works
        st.session_state.retraction_processed = processed
    
    # Display statistics
    retraction_notices = processed.get('retraction_notices', [])
    retracted_articles = processed.get('retracted_articles', [])
    paired_retractions = processed.get('paired_retractions', [])
    unpaired_notices = processed.get('unpaired_notices', [])
    unpaired_retracted = processed.get('unpaired_retracted', [])
    
    st.markdown(f"""
    <div class="info-message" style="background: linear-gradient(135deg, #4CAF5015 0%, #2E7D3215 100%); border-radius: 8px; padding: 12px; border-left: 3px solid #4CAF50; font-size: 0.9rem; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>✅ Analysis Complete!</strong><br>
                Found {len(retraction_notices)} retraction notices and {len(retracted_articles)} retracted articles
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
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
            <div class="metric-value">{len(paired_retractions)}</div>
            <div class="metric-label">Paired (Notice + Article)</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(unpaired_notices) + len(unpaired_retracted)}</div>
            <div class="metric-label">Unpaired</div>
        </div>
        """, unsafe_allow_html=True)
    
    if unpaired_notices:
        with st.expander(f"⚠️ Unpaired Retraction Notices ({len(unpaired_notices)})", expanded=False):
            for notice in unpaired_notices[:20]:
                st.markdown(f"- {notice.get('title', 'No title')} (DOI: {notice.get('doi', 'N/A')})")
            if len(unpaired_notices) > 20:
                st.info(f"... and {len(unpaired_notices) - 20} more")
    
    if unpaired_retracted:
        with st.expander(f"⚠️ Unpaired Retracted Articles ({len(unpaired_retracted)})", expanded=False):
            for article in unpaired_retracted[:20]:
                st.markdown(f"- {article.get('title', 'No title')} (DOI: {article.get('doi', 'N/A')})")
            if len(unpaired_retracted) > 20:
                st.info(f"... and {len(unpaired_retracted) - 20} more")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if paired_retractions:
            if st.button("📊 Generate Reports", type="primary", use_container_width=True):
                st.session_state.current_step = 3
                st.rerun()
        else:
            st.warning("⚠️ No paired retractions found. Cannot generate reports.")

def step_retraction_results():
    """Step 3: Retraction results with reports"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📊 Step 3: Retraction Analysis Results</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Download reports for retraction analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'retraction_processed' not in st.session_state:
        st.error("❌ No data available. Please go back.")
        return
    
    # Back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    
    processed = st.session_state.retraction_processed
    paired_retractions = processed.get('paired_retractions', [])
    
    if not paired_retractions:
        st.warning("⚠️ No paired retractions found.")
        return
    
    years = st.session_state.retraction_years
    countries = st.session_state.retraction_countries
    report_name = f"Retraction Analysis {format_year_filter_for_filename(years)}"
    
    # Report sorting options
    st.markdown("### ⚙️ Report Sorting Options")
    
    col_sort1, col_sort2, col_sort3 = st.columns(3)
    
    with col_sort1:
        sort_country = st.radio(
            "Country → Affiliation sorting:",
            options=["By Article Count", "Alphabetical"],
            index=0,
            key="sort_retraction_country"
        )
    
    with col_sort2:
        sort_publisher = st.radio(
            "Publisher → Journal sorting:",
            options=["By Article Count", "Alphabetical"],
            index=0,
            key="sort_retraction_publisher"
        )
    
    with col_sort3:
        st.markdown("**Author Report**")
        st.markdown("*Sorted by number of retractions*")
    
    # Convert UI options to function parameters
    sort_country_param = 'by_count' if sort_country == "By Article Count" else 'alphabetical'
    sort_publisher_param = 'by_count' if sort_publisher == "By Article Count" else 'alphabetical'
    
    # Generate groupings
    with st.spinner("Generating report groupings..."):
        country_hierarchy = group_retractions_by_country_affiliation(
            paired_retractions, sort_country_param
        )
        
        author_groups = group_retractions_by_author(paired_retractions)
        
        publisher_hierarchy = group_retractions_by_publisher_journal(
            paired_retractions, sort_publisher_param
        )
    
    # Statistics
    total_pairs = len(paired_retractions)
    total_countries = len(country_hierarchy)
    total_authors = len(author_groups)
    total_publishers = len(publisher_hierarchy)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_pairs}</div>
            <div class="metric-label">Paired Retractions</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_countries}</div>
            <div class="metric-label">Countries</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_authors}</div>
            <div class="metric-label">Unique Authors</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_publishers}</div>
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
    
    if 'retraction_pdf_cache' not in st.session_state:
        st.session_state.retraction_pdf_cache = {}
    if 'retraction_all_generated' not in st.session_state:
        st.session_state.retraction_all_generated = False
    
    # Create unique cache keys
    cache_key_country = f"retraction_country_{hashlib.md5(str(paired_retractions).encode()).hexdigest()[:8]}_{sort_country_param}"
    cache_key_author = f"retraction_author_{hashlib.md5(str(paired_retractions).encode()).hexdigest()[:8]}"
    cache_key_publisher = f"retraction_publisher_{hashlib.md5(str(paired_retractions).encode()).hexdigest()[:8]}_{sort_publisher_param}"
    
    col_gen1, col_gen2, col_gen3 = st.columns([1, 2, 1])
    with col_gen2:
        if not st.session_state.retraction_all_generated:
            if st.button("⚡ Generate All Reports", type="primary", use_container_width=True):
                with st.spinner("Generating all reports..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("Generating Country → Affiliation report...")
                    if cache_key_country not in st.session_state.retraction_pdf_cache:
                        st.session_state.retraction_pdf_cache[cache_key_country] = generate_pdf_retractions_by_country_affiliation(
                            report_name, years, country_hierarchy, countries,
                            logo_path, sort_country_param
                        )
                    progress_bar.progress(0.33)
                    
                    status_text.text("Generating Author report...")
                    if cache_key_author not in st.session_state.retraction_pdf_cache:
                        st.session_state.retraction_pdf_cache[cache_key_author] = generate_pdf_retractions_by_author(
                            report_name, years, author_groups, countries,
                            logo_path
                        )
                    progress_bar.progress(0.66)
                    
                    status_text.text("Generating Publisher → Journal report...")
                    if cache_key_publisher not in st.session_state.retraction_pdf_cache:
                        st.session_state.retraction_pdf_cache[cache_key_publisher] = generate_pdf_retractions_by_publisher_journal(
                            report_name, years, publisher_hierarchy, countries,
                            logo_path, sort_publisher_param
                        )
                    progress_bar.progress(1.0)
                    
                    status_text.text("✅ All reports generated!")
                    st.session_state.retraction_all_generated = True
                    time.sleep(0.5)
                    st.rerun()
        else:
            st.success("✅ All reports already generated! Use the buttons below to download.")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🌍 Report 1: Country → Affiliation**")
        st.markdown(f"*{sort_country} sorting*")
        
        if cache_key_country in st.session_state.retraction_pdf_cache:
            pdf_data = st.session_state.retraction_pdf_cache[cache_key_country]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"Retractions_{format_year_filter_for_filename(years)}_country_affiliation.pdf"
            st.download_button(
                label="📄 Download Country Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"retraction_pdf_country_download_{cache_key_country}"
            )
        else:
            if st.button("📄 Generate Country Report", key=f"retraction_gen_country_{cache_key_country}", use_container_width=True):
                with st.spinner("Generating Country Report..."):
                    pdf_data = generate_pdf_retractions_by_country_affiliation(
                        report_name, years, country_hierarchy, countries,
                        logo_path, sort_country_param
                    )
                    st.session_state.retraction_pdf_cache[cache_key_country] = pdf_data
                    st.rerun()
    
    with col2:
        st.markdown("**👨‍🔬 Report 2: By Author**")
        st.markdown("*Sorted by number of retractions*")
        
        if cache_key_author in st.session_state.retraction_pdf_cache:
            pdf_data = st.session_state.retraction_pdf_cache[cache_key_author]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"Retractions_{format_year_filter_for_filename(years)}_by_author.pdf"
            st.download_button(
                label="📄 Download Author Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"retraction_pdf_author_download_{cache_key_author}"
            )
        else:
            if st.button("📄 Generate Author Report", key=f"retraction_gen_author_{cache_key_author}", use_container_width=True):
                with st.spinner("Generating Author Report..."):
                    pdf_data = generate_pdf_retractions_by_author(
                        report_name, years, author_groups, countries,
                        logo_path
                    )
                    st.session_state.retraction_pdf_cache[cache_key_author] = pdf_data
                    st.rerun()
    
    with col3:
        st.markdown("**📚 Report 3: Publisher → Journal**")
        st.markdown(f"*{sort_publisher} sorting*")
        
        if cache_key_publisher in st.session_state.retraction_pdf_cache:
            pdf_data = st.session_state.retraction_pdf_cache[cache_key_publisher]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"Retractions_{format_year_filter_for_filename(years)}_publisher_journal.pdf"
            st.download_button(
                label="📄 Download Publisher Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"retraction_pdf_publisher_download_{cache_key_publisher}"
            )
        else:
            if st.button("📄 Generate Publisher Report", key=f"retraction_gen_publisher_{cache_key_publisher}", use_container_width=True):
                with st.spinner("Generating Publisher Report..."):
                    pdf_data = generate_pdf_retractions_by_publisher_journal(
                        report_name, years, publisher_hierarchy, countries,
                        logo_path, sort_publisher_param
                    )
                    st.session_state.retraction_pdf_cache[cache_key_publisher] = pdf_data
                    st.rerun()
    
    st.markdown("---")
    
    if st.session_state.retraction_all_generated:
        if all(key in st.session_state.retraction_pdf_cache for key in [cache_key_country, cache_key_author, cache_key_publisher]):
            try:
                import zipfile
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.writestr(f"Retractions_{format_year_filter_for_filename(years)}_country_affiliation.pdf", 
                                     st.session_state.retraction_pdf_cache[cache_key_country])
                    zip_file.writestr(f"Retractions_{format_year_filter_for_filename(years)}_by_author.pdf", 
                                     st.session_state.retraction_pdf_cache[cache_key_author])
                    zip_file.writestr(f"Retractions_{format_year_filter_for_filename(years)}_publisher_journal.pdf", 
                                     st.session_state.retraction_pdf_cache[cache_key_publisher])
                
                zip_data = zip_buffer.getvalue()
                
                col_zip1, col_zip2, col_zip3 = st.columns([1, 2, 1])
                with col_zip2:
                    st.download_button(
                        label="📦 Download All Reports (ZIP archive)",
                        data=zip_data,
                        file_name=f"Retractions_{format_year_filter_for_filename(years)}_all_reports.zip",
                        mime="application/zip",
                        use_container_width=True,
                        key="retraction_download_all_zip"
                    )
            except Exception as e:
                st.error(f"Error creating ZIP archive: {e}")
    
    st.markdown("---")
    
    if st.button("🔄 New Retraction Analysis", use_container_width=True):
        keys_to_clear = ['current_step', 'retraction_years', 'retraction_countries', 
                        'retraction_years_input', 'retraction_country_input',
                        'retraction_works', 'retraction_processed', 'retraction_pdf_cache',
                        'retraction_all_generated']
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
        <div class="progress-bar" style="height: 100%; background: linear-gradient(90deg, #e74c3c, #c0392b); border-radius: 8px; transition: width 0.5s ease; width: {progress * 100}%;"></div>
    </div>
    <div class="step-indicator" style="display: flex; justify-content: space-between; margin: 15px 0; font-size: 0.85rem; color: #666;">
        <span class="{'active' if current_step >= 1 else ''}" style="color: {'#e74c3c' if current_step >= 1 else '#666'}; font-weight: {'600' if current_step >= 1 else '400'};">📥 Parameters</span>
        <span class="{'active' if current_step >= 2 else ''}" style="color: {'#e74c3c' if current_step >= 2 else '#666'}; font-weight: {'600' if current_step >= 2 else '400'};">🔍 Analysis</span>
        <span class="{'active' if current_step >= 3 else ''}" style="color: {'#e74c3c' if current_step >= 3 else '#666'}; font-weight: {'600' if current_step >= 3 else '400'};">📊 Reports</span>
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
        <p style="font-size: 0.7rem; color: #aaa;">Retraction Article Analyzer Pro*2</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
