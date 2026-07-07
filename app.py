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
    page_title="CTA Article Recommender Pro*2",
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
# PDF REPORT GENERATION FUNCTIONS
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

def generate_pdf_by_publisher_journal(journal_name: str, journal_abbr: str, years: List[int],
                                      hierarchy: Dict, logo_path: str = None,
                                      report_title: str = "Report by Publisher & Journal",
                                      sort_option: str = 'alphabetical') -> bytes:
    """Generate PDF report grouping articles by Publisher -> Journal."""
    russian_font_name = register_russian_font()
    
    # Get filter info from session_state
    search_query = st.session_state.get('search_query', '')
    has_filter = 'filtered_articles' in st.session_state and st.session_state.filtered_articles
    
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
    
    meta_style_preprint = ParagraphStyle(
        'MetaPreprint',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9b59b6'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    meta_style_book = ParagraphStyle(
        'MetaBook',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#e67e22'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    meta_style_conference = ParagraphStyle(
        'MetaConference',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#2980b9'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    meta_style_other = ParagraphStyle(
        'MetaOther',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
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
    
    total_articles = sum(len(articles) for publisher in hierarchy.values() 
                        for journal in publisher.values() 
                        for articles in [journal])
    total_publishers = len(hierarchy)
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo at beginning with preserved aspect ratio
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Analytical Report", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    # Format intro text with filter info
    if search_query and has_filter:
        intro_text = f"""
        This report contains {total_articles} articles from «{clean_text(journal_name)}»,
        grouped by Publisher and Journal.
        
        <b>Applied filter:</b> «{clean_text(search_query)}»
        <b>Sorting:</b> {sort_option.replace('_', ' ').title()}
        """
    else:
        intro_text = f"""
        This report contains {total_articles} articles from «{clean_text(journal_name)}»,
        grouped by Publisher and Journal.
        
        <b>Sorting:</b> {sort_option.replace('_', ' ').title()}
        """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Articles", str(total_articles)],
        ["Publishers", str(total_publishers)],
        ["Report Type", report_title],
        ["Sorting", sort_option.replace('_', ' ').title()]
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
                
                # Single output of affiliations with proper separator
                affs = clean_text(article.get('affiliations_str', ''))
                if affs and affs != 'No affiliations specified':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style_default))
                
                # Publication type badge
                type_label = article.get('type_label', 'Other')
                type_icon = article.get('type_icon', '📎')
                type_color = article.get('type_color', '#7f8c8d')
                
                # Select appropriate style based on type
                if type_label == 'Preprint':
                    meta_style = meta_style_preprint
                elif type_label == 'Book/Chapter':
                    meta_style = meta_style_book
                elif type_label == 'Conference':
                    meta_style = meta_style_conference
                elif type_label == 'Article':
                    meta_style = meta_style_default
                else:
                    meta_style = meta_style_other
                
                story.append(Paragraph(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='{type_color}'><b>{type_icon} {type_label}</b></font>",
                    meta_style
                ))
                
                # Journal name
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
                
                citations = article.get('cited_by_count', 0)
                citations_per_year = article.get('citations_per_year', 0)
                references = article.get('referenced_works_count', 0)
                oa_status = article.get('oa_status', 'Closed Access')
                
                citation_text = f"<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f} | <b>References:</b> {references} | <b>OA:</b> {oa_status}"
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{citation_text}", citation_style))
                
                doi_url = article.get('doi_url', '')
                if doi_url:
                    doi_url_clean = clean_doi_url(doi_url)
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style_default))
                
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
    This report contains {total_articles} articles from «{clean_text(journal_name)}»,
    grouped by {total_publishers} publishers and their respective journals.
    
    The articles are organized alphabetically by publisher and journal name.
    Within each journal, articles are sorted by citations per year (descending).
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end with preserved aspect ratio (smaller)
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using CTA Article Recommender Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_pdf_by_citations(journal_name: str, journal_abbr: str, years: List[int],
                              articles: List[dict], logo_path: str = None,
                              report_title: str = "Report by Citations per Year",
                              sort_option: str = 'citations_per_year') -> bytes:
    """Generate PDF report with articles sorted by citations per year."""
    russian_font_name = register_russian_font()
    
    # Get filter info from session_state
    search_query = st.session_state.get('search_query', '')
    has_filter = 'filtered_articles' in st.session_state and st.session_state.filtered_articles
    
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
    
    article_title_style = ParagraphStyle(
        'ArticleTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=5,
        leftIndent=0,
        fontName=russian_font_name
    )
    
    authors_style = ParagraphStyle(
        'AuthorsStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=3,
        leftIndent=0,
        fontName=russian_font_name
    )
    
    meta_style_default = ParagraphStyle(
        'MetaDefault',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=2,
        leftIndent=0,
        fontName=russian_font_name
    )
    
    meta_style_preprint = ParagraphStyle(
        'MetaPreprint',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9b59b6'),
        spaceAfter=2,
        leftIndent=0,
        fontName=russian_font_name
    )
    
    meta_style_book = ParagraphStyle(
        'MetaBook',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#e67e22'),
        spaceAfter=2,
        leftIndent=0,
        fontName=russian_font_name
    )
    
    meta_style_conference = ParagraphStyle(
        'MetaConference',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#2980b9'),
        spaceAfter=2,
        leftIndent=0,
        fontName=russian_font_name
    )
    
    meta_style_other = ParagraphStyle(
        'MetaOther',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=2,
        leftIndent=0,
        fontName=russian_font_name
    )
    
    citation_style = ParagraphStyle(
        'CitationStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#27AE60'),
        spaceAfter=2,
        leftIndent=0,
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
    
    toc_article_style = ParagraphStyle(
        'TOCArticleStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=3,
        fontName=russian_font_name
    )
    
    toc_more_style = ParagraphStyle(
        'TOCMoreStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7F8C8D'),
        spaceAfter=3,
        fontName=russian_font_name
    )
    
    story = []
    
    total_articles = len(articles)
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo at beginning with preserved aspect ratio
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Analytical Report", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    avg_citations = sum(a.get('citations_per_year', 0) for a in articles) / total_articles if total_articles > 0 else 0
    
    # Format intro text with filter info
    sort_display = sort_option.replace('_', ' ').title()
    if sort_option == 'publication_date':
        sort_display = 'Publication Date (Newest First)'
    
    if search_query and has_filter:
        intro_text = f"""
        This report contains {total_articles} articles from «{clean_text(journal_name)}»,
        sorted by {sort_display}.
        
        Average citations per year: {avg_citations:.1f}
        
        <b>Applied filter:</b> «{clean_text(search_query)}»
        """
    else:
        intro_text = f"""
        This report contains {total_articles} articles from «{clean_text(journal_name)}»,
        sorted by {sort_display}.
        
        Average citations per year: {avg_citations:.1f}
        """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Articles", str(total_articles)],
        ["Avg Citations/Year", f"{avg_citations:.1f}"],
        ["Report Type", report_title],
        ["Sorting", sort_display]
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
    
    # ===== TABLE OF CONTENTS WITH INTELLIGENT INDEX SELECTION =====
    story.append(Paragraph("Table of Contents", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Calculate which article indices to show in TOC
    toc_indices = calculate_toc_indices(total_articles)
    
    # Display selected articles in TOC
    for idx in toc_indices:
        article = articles[idx - 1]  # Convert 1-based index to 0-based
        title = clean_text(article.get('title', 'No title')[:60])
        
        # Format the display text based on sort option
        if sort_option == 'citations_per_year':
            citations = article.get('citations_per_year', 0)
            display_text = f"{idx}. {title}... — {citations:.1f} citations/year"
        elif sort_option == 'total_citations':
            citations = article.get('cited_by_count', 0)
            display_text = f"{idx}. {title}... — {citations} total citations"
        else:  # publication_date
            pub_date = article.get('publication_date', '')
            display_text = f"{idx}. {title}... — {pub_date}"
        
        # Create anchor for this article
        anchor_id = f"article_{hashlib.md5(str(idx).encode('utf-8')).hexdigest()[:8]}"
        story.append(Paragraph(f'<a href="#{anchor_id}">{display_text}</a>', toc_article_style))
    
    # Show message about omitted articles if any
    if len(toc_indices) < total_articles:
        omitted_count = total_articles - len(toc_indices)
        story.append(Paragraph(f"... and {omitted_count} more articles not shown in TOC", toc_more_style))
    
    story.append(PageBreak())
    
    # ===== MAIN CONTENT =====
    sort_display_title = sort_display
    story.append(Paragraph(f"Articles by {sort_display_title}", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    for idx, article in enumerate(articles, 1):
        anchor_id = f"article_{hashlib.md5(str(idx).encode('utf-8')).hexdigest()[:8]}"
        anchor_para = Paragraph(f'<a name="{anchor_id}"/>', ParagraphStyle('AnchorStyle', parent=styles['Normal'], fontSize=1, textColor=colors.white, fontName=russian_font_name))
        story.append(anchor_para)
        
        title = clean_text(article.get('title', 'No title'))
        story.append(Paragraph(f"{idx}. {title}", article_title_style))
        
        authors = clean_text(article.get('authors', 'Authors not specified'))
        story.append(Paragraph(f"<b>Authors:</b> {authors}", authors_style))
        
        # Single output of affiliations with proper separator
        affs = clean_text(article.get('affiliations_str', ''))
        if affs and affs != 'No affiliations specified':
            story.append(Paragraph(f"<b>Affiliations:</b> {affs}", meta_style_default))
        
        # Publication type badge
        type_label = article.get('type_label', 'Other')
        type_icon = article.get('type_icon', '📎')
        type_color = article.get('type_color', '#7f8c8d')
        
        # Select appropriate style based on type
        if type_label == 'Preprint':
            meta_style = meta_style_preprint
        elif type_label == 'Book/Chapter':
            meta_style = meta_style_book
        elif type_label == 'Conference':
            meta_style = meta_style_conference
        elif type_label == 'Article':
            meta_style = meta_style_default
        else:
            meta_style = meta_style_other
        
        story.append(Paragraph(
            f"<font color='{type_color}'><b>{type_icon} {type_label}</b></font>",
            meta_style
        ))
        
        # Journal name
        journal_name_article = clean_text(article.get('journal_name', ''))
        if journal_name_article:
            story.append(Paragraph(f"<b>Journal:</b> {journal_name_article}", meta_style_default))
        
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
            story.append(Paragraph(f"{', '.join(meta_parts)}", meta_style_default))
        
        citations = article.get('cited_by_count', 0)
        citations_per_year = article.get('citations_per_year', 0)
        references = article.get('referenced_works_count', 0)
        oa_status = article.get('oa_status', 'Closed Access')
        
        citation_text = f"<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f} | <b>References:</b> {references} | <b>OA:</b> {oa_status}"
        story.append(Paragraph(citation_text, citation_style))
        
        doi_url = article.get('doi_url', '')
        if doi_url:
            doi_url_clean = clean_doi_url(doi_url)
            story.append(Paragraph(f"<b>DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style_default))
        
        story.append(Spacer(1, 0.15*cm))
        
        if idx < len(articles):
            story.append(Paragraph("─" * 60, separator_style))
            story.append(Spacer(1, 0.1*cm))
    
    story.append(Spacer(1, 0.3*cm))
    story.append(PageBreak())
    
    story.append(Paragraph("Conclusion", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    conclusion_text = f"""
    This report contains {total_articles} articles from «{clean_text(journal_name)}»,
    sorted by {sort_display} in descending order.
    
    The articles with the highest {sort_display.lower()} are listed first,
    representing the most impactful recent publications.
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end with preserved aspect ratio (smaller)
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using CTA Article Recommender Pro*2", footer_style))
    
    doc.build(story)
    return buffer.getvalue()

def generate_pdf_by_country_affiliation(journal_name: str, journal_abbr: str, years: List[int],
                                       hierarchy: Dict, logo_path: str = None,
                                       report_title: str = "Report by Country & Affiliation",
                                       sort_option: str = 'alphabetical') -> bytes:
    """Generate PDF report grouping articles by Country -> Affiliation."""
    russian_font_name = register_russian_font()
    
    # Get filter info from session_state
    search_query = st.session_state.get('search_query', '')
    has_filter = 'filtered_articles' in st.session_state and st.session_state.filtered_articles
    
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
    
    meta_style_preprint = ParagraphStyle(
        'MetaPreprint',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9b59b6'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    meta_style_book = ParagraphStyle(
        'MetaBook',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#e67e22'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    meta_style_conference = ParagraphStyle(
        'MetaConference',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#2980b9'),
        spaceAfter=2,
        leftIndent=40,
        fontName=russian_font_name
    )
    
    meta_style_other = ParagraphStyle(
        'MetaOther',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
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
    
    total_articles = sum(len(articles) for country in hierarchy.values() 
                        for affiliation in country.values() 
                        for articles in [affiliation])
    total_countries = len(hierarchy)
    
    story.append(Spacer(1, 2*cm))
    
    # Add logo at beginning with preserved aspect ratio
    add_logo_to_pdf(story, logo_path, max_width=200, max_height=200, add_spacer=True)
    
    story.append(Paragraph("Analytical Report", title_style))
    story.append(Paragraph(f"«{clean_text(journal_name)}»", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    years_str = format_year_filter_for_filename(years)
    story.append(Paragraph(f"Publication period: {years_str}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    # Format intro text with filter info
    if search_query and has_filter:
        intro_text = f"""
        This report contains {total_articles} articles from «{clean_text(journal_name)}»,
        grouped by Country and Affiliation.
        
        <b>Applied filter:</b> «{clean_text(search_query)}»
        <b>Sorting:</b> {sort_option.replace('_', ' ').title()}
        """
    else:
        intro_text = f"""
        This report contains {total_articles} articles from «{clean_text(journal_name)}»,
        grouped by Country and Affiliation.
        
        <b>Sorting:</b> {sort_option.replace('_', ' ').title()}
        """
    
    story.append(Paragraph(intro_text, intro_style))
    story.append(Spacer(1, 1*cm))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Articles", str(total_articles)],
        ["Countries", str(total_countries)],
        ["Report Type", report_title],
        ["Sorting", sort_option.replace('_', ' ').title()]
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
                
                # Single output of affiliations with proper separator
                affs = clean_text(article.get('affiliations_str', ''))
                if affs and affs != 'No affiliations specified':
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Affiliations:</b> {affs}", meta_style_default))
                
                # Publication type badge
                type_label = article.get('type_label', 'Other')
                type_icon = article.get('type_icon', '📎')
                type_color = article.get('type_color', '#7f8c8d')
                
                # Select appropriate style based on type
                if type_label == 'Preprint':
                    meta_style = meta_style_preprint
                elif type_label == 'Book/Chapter':
                    meta_style = meta_style_book
                elif type_label == 'Conference':
                    meta_style = meta_style_conference
                elif type_label == 'Article':
                    meta_style = meta_style_default
                else:
                    meta_style = meta_style_other
                
                story.append(Paragraph(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;<font color='{type_color}'><b>{type_icon} {type_label}</b></font>",
                    meta_style
                ))
                
                # Journal name
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
                
                citations = article.get('cited_by_count', 0)
                citations_per_year = article.get('citations_per_year', 0)
                references = article.get('referenced_works_count', 0)
                oa_status = article.get('oa_status', 'Closed Access')
                
                citation_text = f"<b>Citations:</b> {citations} | <b>per year:</b> {citations_per_year:.1f} | <b>References:</b> {references} | <b>OA:</b> {oa_status}"
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{citation_text}", citation_style))
                
                doi_url = article.get('doi_url', '')
                if doi_url:
                    doi_url_clean = clean_doi_url(doi_url)
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>DOI:</b> <a href='{doi_url_clean}'>{doi_url_clean}</a>", meta_style_default))
                
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
    This report contains {total_articles} articles from «{clean_text(journal_name)}»,
    grouped by {total_countries} countries and their respective affiliations.
    
    The articles are organized alphabetically by country and affiliation name.
    Within each affiliation, articles are sorted by citations per year (descending).
    """
    
    story.append(Paragraph(conclusion_text, conclusion_style))
    story.append(Spacer(1, 1*cm))
    
    # Add logo at end with preserved aspect ratio (smaller)
    add_logo_to_pdf(story, logo_path, max_width=120, max_height=120, add_spacer=True)
    
    story.append(Paragraph(f"© Chimica Techno Acta | {datetime.now().strftime('%Y-%m-%d')}", footer_style))
    story.append(Paragraph("Report generated using CTA Article Recommender Pro*2", footer_style))
    
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

def step_data_input():
    """Step 1: Input DOIs"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📥 Step 1: Input Research DOIs</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Enter DOI identifiers to analyze topics and keywords.</p>
    </div>
    """, unsafe_allow_html=True)
    
    doi_input = st.text_area(
        "**DOI Input** (one per line or comma-separated):",
        height=150,
        placeholder="Examples:\n10.1038/nmat1849\nhttps://doi.org/10.1038/nmat1849",
        help="Enter up to 300 DOI identifiers"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            if doi_input:
                dois = parse_doi_input(doi_input)
                if dois:
                    st.session_state.dois = dois
                    st.session_state.current_step = 2
                    if 'pdf_cache' in st.session_state:
                        del st.session_state.pdf_cache
                    if 'all_reports_generated' in st.session_state:
                        del st.session_state.all_reports_generated
                    if 'filtered_articles' in st.session_state:
                        del st.session_state.filtered_articles
                    if 'search_query' in st.session_state:
                        del st.session_state.search_query
                    st.rerun()
                else:
                    st.error("❌ No valid DOI identifiers found.")
            else:
                st.error("❌ Please enter at least one DOI")

def step_analysis():
    """Step 2: Analysis"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 2: Analysis in Progress</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Fetching data from OpenAlex...</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'dois' not in st.session_state:
        st.error("❌ No data to analyze. Please go back to Step 1.")
        return
    
    # Back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    
    dois = st.session_state.dois
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(dois)}</div>
            <div class="metric-label">DOIs</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(dois)//10}s</div>
            <div class="metric-label">Est. Time</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">8/sec</div>
            <div class="metric-label">API Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with st.spinner("Fetching data..."):
        results, successful, failed = fetch_works_by_dois_sync(dois)
    
    works_data = []
    topic_counter = Counter()
    titles = []
    
    for result in results:
        if result.get('success') and result.get('data'):
            work = result['data']
            enriched = enrich_work_data_full(work)
            
            if enriched.get('primary_topic'):
                topic_counter[enriched['primary_topic']] += 1
            
            works_data.append(enriched)
            titles.append(enriched.get('title', ''))
    
    keyword_counter = analyze_keywords_parallel(titles)
    
    st.session_state.works_data = works_data
    st.session_state.topic_counter = topic_counter
    st.session_state.keyword_counter = keyword_counter
    st.session_state.successful = successful
    st.session_state.failed = failed
    
    st.markdown(f"""
    <div class="info-message" style="background: linear-gradient(135deg, #2196F315 0%, #0D47A115 100%); border-radius: 8px; padding: 12px; border-left: 3px solid #2196F3; font-size: 0.9rem; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>✅ Analysis Complete!</strong><br>
                Successfully processed {successful} papers
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{successful}</div>
            <div class="metric-label">Successful</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{failed}</div>
            <div class="metric-label">Failed</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(topic_counter)}</div>
            <div class="metric-label">Topics</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Continue to Topic Selection", type="primary", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()

def step_topic_selection():
    """Step 3: Topic Selection"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🎯 Step 3: Select Research Topic</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Choose a topic for deep analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.works_data:
        st.error("❌ No data available. Please start from Step 1.")
        return
    
    # Back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 2
            # Clear any existing topic selection when going back
            if 'selected_topic' in st.session_state:
                del st.session_state.selected_topic
            if 'selected_topic_id' in st.session_state:
                del st.session_state.selected_topic_id
            if 'selected_years' in st.session_state:
                del st.session_state.selected_years
            if 'all_works' in st.session_state:
                del st.session_state.all_works
            if 'enriched_count' in st.session_state:
                del st.session_state.enriched_count
            if 'pdf_cache' in st.session_state:
                del st.session_state.pdf_cache
            if 'all_reports_generated' in st.session_state:
                del st.session_state.all_reports_generated
            if 'filtered_articles' in st.session_state:
                del st.session_state.filtered_articles
            if 'search_query' in st.session_state:
                del st.session_state.search_query
            if 'search_results_count' in st.session_state:
                del st.session_state.search_results_count
            if 'years_input' in st.session_state:
                del st.session_state.years_input
            st.rerun()
    
    topics = st.session_state.topic_counter.most_common()
    
    cols = st.columns(2)
    for idx, (topic, count) in enumerate(topics[:10]):
        with cols[idx % 2]:
            is_selected = st.session_state.get('selected_topic') == topic
            st.markdown(f"""
            <div class="topic-card" style="background: white; border-radius: 8px; padding: 12px; margin-bottom: 8px; border: 1px solid {'#667eea' if is_selected else '#e0e0e0'}; cursor: pointer; transition: all 0.2s ease;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 600; font-size: 0.9rem;">{topic[:70]}{'...' if len(topic) > 70 else ''}</div>
                    <span style="background: #667eea; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">
                        {count} papers
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Select", key=f"select_{idx}", 
                        use_container_width=True,
                        type="primary" if is_selected else "secondary"):
                # Clear previous topic data when selecting new topic
                if 'selected_topic' in st.session_state and st.session_state.selected_topic != topic:
                    if 'selected_topic_id' in st.session_state:
                        del st.session_state.selected_topic_id
                    if 'selected_years' in st.session_state:
                        del st.session_state.selected_years
                    if 'all_works' in st.session_state:
                        del st.session_state.all_works
                    if 'enriched_count' in st.session_state:
                        del st.session_state.enriched_count
                    if 'pdf_cache' in st.session_state:
                        del st.session_state.pdf_cache
                    if 'all_reports_generated' in st.session_state:
                        del st.session_state.all_reports_generated
                    if 'filtered_articles' in st.session_state:
                        del st.session_state.filtered_articles
                    if 'search_query' in st.session_state:
                        del st.session_state.search_query
                    if 'search_results_count' in st.session_state:
                        del st.session_state.search_results_count
                    if 'years_input' in st.session_state:
                        del st.session_state.years_input
                
                st.session_state.selected_topic = topic
                
                for work in st.session_state.works_data:
                    if work.get('primary_topic') == topic:
                        topic_id = work.get('topic_id')
                        if topic_id:
                            st.session_state.selected_topic_id = topic_id
                            break
                
                st.rerun()
    
    if 'selected_topic' in st.session_state and 'selected_topic_id' in st.session_state:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⏰ Select Years", type="primary", use_container_width=True):
                st.session_state.current_step = 4
                st.rerun()

def step_year_selection():
    """Step 4: Select publication years - free text input"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">⏰ Step 4: Select Publication Years</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Enter the publication years for analysis (any format supported).</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'selected_topic_id' not in st.session_state:
        st.error("❌ Topic not selected. Please go back to Step 3.")
        return
    
    # Back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 3
            # Keep selected topic but clear years and dependent data
            if 'selected_years' in st.session_state:
                del st.session_state.selected_years
            if 'all_works' in st.session_state:
                del st.session_state.all_works
            if 'enriched_count' in st.session_state:
                del st.session_state.enriched_count
            if 'pdf_cache' in st.session_state:
                del st.session_state.pdf_cache
            if 'all_reports_generated' in st.session_state:
                del st.session_state.all_reports_generated
            if 'filtered_articles' in st.session_state:
                del st.session_state.filtered_articles
            if 'search_query' in st.session_state:
                del st.session_state.search_query
            if 'search_results_count' in st.session_state:
                del st.session_state.search_results_count
            if 'years_input' in st.session_state:
                del st.session_state.years_input
            st.rerun()
    
    topic_id = st.session_state.selected_topic_id
    topic_name = st.session_state.get('selected_topic', 'Selected Topic')
    
    st.markdown(f"""
    <div style="background: white; border-radius: 8px; padding: 12px; border: 1px solid #ced4da; margin-bottom: 15px;">
        <strong>Selected Topic:</strong> {topic_name}
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
    
    # Remove the Reset Cached Data button as per requirement
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📊 Generate Reports", type="primary", use_container_width=True):
            if not years_input:
                st.error("❌ Please enter at least one year.")
                return
            
            years = parse_year_filter(years_input)
            if not years:
                st.error("❌ Invalid year format. Please check your input.")
                return
            
            # Clear cached data when years change
            if 'selected_years' in st.session_state and st.session_state.selected_years != years:
                if 'all_works' in st.session_state:
                    del st.session_state.all_works
                if 'enriched_count' in st.session_state:
                    del st.session_state.enriched_count
                if 'pdf_cache' in st.session_state:
                    del st.session_state.pdf_cache
                if 'all_reports_generated' in st.session_state:
                    del st.session_state.all_reports_generated
                if 'filtered_articles' in st.session_state:
                    del st.session_state.filtered_articles
                if 'search_query' in st.session_state:
                    del st.session_state.search_query
                if 'search_results_count' in st.session_state:
                    del st.session_state.search_results_count
            
            st.session_state.selected_years = years
            st.session_state.years_input = years_input
            st.session_state.current_step = 5
            st.rerun()

def step_results():
    """Step 5: Results with 3 PDF reports"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">📊 Step 5: Analysis Results</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Download reports for your research topic.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'selected_topic_id' not in st.session_state:
        st.error("❌ Topic not selected. Please go back.")
        return
    
    # Back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 4
            # Keep years but allow changes
            st.rerun()
    
    topic_id = st.session_state.selected_topic_id
    topic_name = st.session_state.get('selected_topic', 'Selected Topic')
    years = st.session_state.get('selected_years', [])
    
    if not years:
        st.error("❌ Years not selected. Please go back.")
        return
    
    # Fetch ALL works for the topic with given years (no citation filtering)
    if 'all_works' not in st.session_state:
        with st.spinner(f"Loading ALL works for topic '{topic_name}'..."):
            all_works = fetch_all_works_by_topic_sync(topic_id, years)
            
            if not all_works:
                st.error("❌ No works found for this topic and year range.")
                return
            
            enriched_works = []
            for work in all_works:
                enriched = enrich_work_data_full(work)
                if enriched.get('title') and enriched.get('title') != 'No title':
                    enriched_works.append(enriched)
            
            st.session_state.all_works = enriched_works
            st.session_state.enriched_count = len(enriched_works)
    else:
        enriched_works = st.session_state.all_works
    
    if not enriched_works:
        st.warning("⚠️ No valid works found after enrichment.")
        return
    
    # Use filtered articles if available, otherwise use all works
    if 'filtered_articles' in st.session_state and st.session_state.filtered_articles:
        current_articles = st.session_state.filtered_articles
        st.info(f"🔍 Showing {len(current_articles)} filtered articles (out of {len(enriched_works)} total)")
    else:
        current_articles = enriched_works
    
    # Statistics
    total_articles = len(current_articles)
    total_citations = sum(w.get('cited_by_count', 0) for w in current_articles)
    avg_citations = total_citations / total_articles if total_articles > 0 else 0
    
    # Sorting options
    st.markdown("### ⚙️ Report Sorting Options")
    
    col_sort1, col_sort2, col_sort3 = st.columns(3)
    
    with col_sort1:
        sort_publisher = st.radio(
            "Publisher → Journal sorting:",
            options=["Alphabetical", "By Article Count"],
            index=0,
            key="sort_publisher"
        )
    
    with col_sort2:
        sort_citations = st.radio(
            "Citations Report sorting:",
            options=["Citations per Year", "Total Citations", "Publication Date (Newest First)"],
            index=0,
            key="sort_citations"
        )
    
    with col_sort3:
        sort_country = st.radio(
            "Country → Affiliation sorting:",
            options=["Alphabetical", "By Article Count"],
            index=0,
            key="sort_country"
        )
    
    # Convert UI options to function parameters
    sort_publisher_param = 'alphabetical' if sort_publisher == "Alphabetical" else 'by_count'
    sort_citations_param = 'citations_per_year' if sort_citations == "Citations per Year" else ('total_citations' if sort_citations == "Total Citations" else 'publication_date')
    sort_country_param = 'alphabetical' if sort_country == "Alphabetical" else 'by_count'
    
    # Generate groupings with caching using unique keys
    with st.spinner("Generating report groupings..."):
        # Create unique cache keys based on all parameters
        filter_hash = hashlib.md5(str(sorted([a.get('doi', '') for a in current_articles])).encode()).hexdigest()[:8]
        
        publisher_hierarchy = cached_group_articles_by_publisher_journal(
            tuple(current_articles), 
            sort_publisher_param
        )
        
        country_hierarchy = cached_group_articles_by_country_affiliation(
            tuple(current_articles), 
            sort_country_param
        )
        
        citations_sorted = cached_sort_articles_by_citations(
            tuple(current_articles), 
            sort_citations_param
        )
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_articles:,}</div>
            <div class="metric-label">Total Articles</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(publisher_hierarchy)}</div>
            <div class="metric-label">Publishers</div>
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
            <div class="metric-value">{avg_citations:.1f}</div>
            <div class="metric-label">Avg Citations/Year</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📥 Download Reports")
    
    journal_name = topic_name
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
    
    # Create unique cache keys including all parameters
    filter_hash = hashlib.md5(str(sorted([a.get('doi', '') for a in current_articles])).encode()).hexdigest()[:8]
    years_hash = hashlib.md5(','.join(map(str, years)).encode()).hexdigest()[:8]
    
    cache_key_publisher = f"publisher_{topic_id}_{years_hash}_{filter_hash}_{sort_publisher_param}"
    cache_key_citations = f"citations_{topic_id}_{years_hash}_{filter_hash}_{sort_citations_param}"
    cache_key_country = f"country_{topic_id}_{years_hash}_{filter_hash}_{sort_country_param}"
    
    # Advanced Search button
    col_adv1, col_adv2, col_adv3 = st.columns([1, 2, 1])
    with col_adv2:
        if st.button("🔍 Advanced Search (Filter Articles)", type="secondary", use_container_width=True):
            st.session_state.current_step = 6
            st.rerun()
    
    st.markdown("---")
    
    col_gen1, col_gen2, col_gen3 = st.columns([1, 1, 1])
    with col_gen2:
        if not st.session_state.all_reports_generated:
            if st.button("⚡ Generate All Reports", type="primary", use_container_width=True):
                with st.spinner("Generating all reports..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("Generating Publisher → Journal report...")
                    if cache_key_publisher not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_publisher] = generate_pdf_by_publisher_journal(
                            journal_name, journal_abbr, years,
                            publisher_hierarchy, logo_path,
                            "Report by Publisher & Journal",
                            sort_publisher_param
                        )
                    progress_bar.progress(0.33)
                    
                    status_text.text("Generating Citations per Year report...")
                    if cache_key_citations not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_citations] = generate_pdf_by_citations(
                            journal_name, journal_abbr, years,
                            citations_sorted, logo_path,
                            "Report by Citations",
                            sort_citations_param
                        )
                    progress_bar.progress(0.66)
                    
                    status_text.text("Generating Country → Affiliation report...")
                    if cache_key_country not in st.session_state.pdf_cache:
                        st.session_state.pdf_cache[cache_key_country] = generate_pdf_by_country_affiliation(
                            journal_name, journal_abbr, years,
                            country_hierarchy, logo_path,
                            "Report by Country & Affiliation",
                            sort_country_param
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
        st.markdown("**📚 Report 1: Publisher → Journal**")
        st.markdown(f"*{sort_publisher} sorting*")
        
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
                    pdf_data = generate_pdf_by_publisher_journal(
                        journal_name, journal_abbr, years,
                        publisher_hierarchy, logo_path,
                        "Report by Publisher & Journal",
                        sort_publisher_param
                    )
                    st.session_state.pdf_cache[cache_key_publisher] = pdf_data
                    st.rerun()
    
    with col2:
        st.markdown("**📈 Report 2: Citations**")
        st.markdown(f"*{sort_citations} sorting*")
        
        if cache_key_citations in st.session_state.pdf_cache:
            pdf_data = st.session_state.pdf_cache[cache_key_citations]
        else:
            pdf_data = None
        
        if pdf_data is not None:
            filename = f"{journal_abbr}_{format_year_filter_for_filename(years)}_citations.pdf"
            st.download_button(
                label="📄 Download Citations Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_citations_download_{cache_key_citations}"
            )
        else:
            if st.button("📄 Generate Citations Report", key=f"gen_citations_{cache_key_citations}", use_container_width=True):
                with st.spinner("Generating Citations Report..."):
                    pdf_data = generate_pdf_by_citations(
                        journal_name, journal_abbr, years,
                        citations_sorted, logo_path,
                        "Report by Citations",
                        sort_citations_param
                    )
                    st.session_state.pdf_cache[cache_key_citations] = pdf_data
                    st.rerun()
    
    with col3:
        st.markdown("**🌍 Report 3: Country → Affiliation**")
        st.markdown(f"*{sort_country} sorting*")
        
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
                    pdf_data = generate_pdf_by_country_affiliation(
                        journal_name, journal_abbr, years,
                        country_hierarchy, logo_path,
                        "Report by Country & Affiliation",
                        sort_country_param
                    )
                    st.session_state.pdf_cache[cache_key_country] = pdf_data
                    st.rerun()
    
    st.markdown("---")
    
    if st.session_state.all_reports_generated:
        if all(key in st.session_state.pdf_cache for key in [cache_key_publisher, cache_key_citations, cache_key_country]):
            try:
                import zipfile
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.writestr(f"{journal_abbr}_{format_year_filter_for_filename(years)}_publisher_journal.pdf", 
                                     st.session_state.pdf_cache[cache_key_publisher])
                    zip_file.writestr(f"{journal_abbr}_{format_year_filter_for_filename(years)}_citations.pdf", 
                                     st.session_state.pdf_cache[cache_key_citations])
                    zip_file.writestr(f"{journal_abbr}_{format_year_filter_for_filename(years)}_country_affiliation.pdf", 
                                     st.session_state.pdf_cache[cache_key_country])
                
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
        keys_to_clear = ['current_step', 'dois', 'works_data', 'topic_counter', 
                        'keyword_counter', 'successful', 'failed', 'selected_topic',
                        'selected_topic_id', 'selected_years', 'all_works', 
                        'enriched_count', 'years_input', 'pdf_cache', 'all_reports_generated',
                        'filtered_articles', 'search_query', 'search_results_count']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.current_step = 1
        st.rerun()

# ============================================================================
# STEP 6: ADVANCED SEARCH
# ============================================================================

def step_advanced_search():
    """Step 6: Advanced search and filtering of articles"""
    st.markdown("""
    <div class="step-card">
        <h3 style="margin: 0; font-size: 1.3rem;">🔍 Step 6: Advanced Search</h3>
        <p style="margin: 5px 0; font-size: 0.9rem;">Filter articles by title using advanced search syntax.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'all_works' not in st.session_state:
        st.error("❌ No data available. Please go back to Step 5.")
        return
    
    # Back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("← Back to Reports", use_container_width=True):
            st.session_state.current_step = 5
            st.rerun()
    
    all_articles = st.session_state.all_works
    total_articles = len(all_articles)
    
    st.markdown(f"""
    <div style="background: white; border-radius: 8px; padding: 12px; border: 1px solid #ced4da; margin-bottom: 15px;">
        <strong>Total articles available:</strong> {total_articles}
        <br><small style="color: #666;">Enter search query to filter articles by title</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="filter-section" style="background: rgba(255, 255, 255, 0.9); border-radius: 20px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(102, 126, 234, 0.2);">
        <div class="filter-header" style="font-size: 1.1rem; font-weight: 600; color: #495057; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #667eea;">
            🔍 Search Syntax
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.9rem; color: #666; margin-bottom: 10px;">
        <strong>Supported syntax:</strong>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 8px 12px; border-radius: 6px; border-left: 3px solid #667eea; margin-bottom: 8px;">
            <code style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-family: monospace;">"high temperature"</code> — Exact phrase match
        </div>
        <div style="background: #f8f9fa; padding: 8px 12px; border-radius: 6px; border-left: 3px solid #27ae60; margin-bottom: 8px;">
            <code style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-family: monospace;">high temperature</code> — Both words must appear (AND logic)
        </div>
        <div style="background: #f8f9fa; padding: 8px 12px; border-radius: 6px; border-left: 3px solid #e67e22; margin-bottom: 8px;">
            <code style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-family: monospace;">catal*</code> — Wildcard: matches catalysis, catalyst, catalytic, etc.
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 8px 12px; border-radius: 6px; border-left: 3px solid #8e44ad; margin-bottom: 8px;">
            <code style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-family: monospace;">fuel cell</code> — Automatically matches "fuel cells" (plural support)
        </div>
        <div style="background: #f8f9fa; padding: 8px 12px; border-radius: 6px; border-left: 3px solid #e74c3c; margin-bottom: 8px;">
            <code style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-family: monospace;">"high temperature" catalysis*</code> — Combined: exact phrase AND wildcard
        </div>
        """, unsafe_allow_html=True)
    
    # Search input
    search_query = st.text_input(
        "Enter search query:",
        value=st.session_state.get('search_query', ''),
        placeholder='Example: "high temperature" catalysis* OR "fuel cell" polymer',
        help="Use quotes for exact phrases, * for wildcards"
    )
    
    col_search1, col_search2, col_search3 = st.columns([1, 1, 1])
    
    with col_search1:
        if st.button("🔍 Search", type="primary", use_container_width=True):
            if search_query and search_query.strip():
                with st.spinner("Filtering articles..."):
                    filtered = filter_articles_by_query(all_articles, search_query)
                    st.session_state.filtered_articles = filtered
                    st.session_state.search_query = search_query
                    st.session_state.search_results_count = len(filtered)
                    st.rerun()
            else:
                st.warning("⚠️ Please enter a search query.")
    
    with col_search2:
        if st.button("🔄 Reset Filter", use_container_width=True):
            if 'filtered_articles' in st.session_state:
                del st.session_state.filtered_articles
            if 'search_query' in st.session_state:
                del st.session_state.search_query
            if 'search_results_count' in st.session_state:
                del st.session_state.search_results_count
            st.rerun()
    
    with col_search3:
        if st.button("📊 Generate Reports from Filtered", use_container_width=True, type="secondary"):
            if 'filtered_articles' in st.session_state and st.session_state.filtered_articles:
                st.session_state.current_step = 5
                st.rerun()
            else:
                st.warning("⚠️ No filtered articles to generate reports from.")
    
    # Show results
    if 'filtered_articles' in st.session_state and st.session_state.filtered_articles:
        filtered = st.session_state.filtered_articles
        query = st.session_state.get('search_query', '')
        
        st.markdown("---")
        st.markdown(f"### 📋 Search Results: {len(filtered)} articles found")
        
        if query:
            st.markdown(f"**Query:** `{query}`")
        
        # Show preview of filtered articles
        with st.expander(f"Show {len(filtered)} filtered articles", expanded=False):
            for idx, article in enumerate(filtered[:50], 1):
                title = article.get('title', 'No title')
                year = article.get('publication_year', '')
                journal = article.get('journal_name', '')
                
                # Get publication type info
                type_label = article.get('type_label', 'Other')
                type_icon = article.get('type_icon', '📎')
                type_color = article.get('type_color', '#7f8c8d')
                
                st.markdown(f"""
                <div class="result-card" style="padding: 10px; margin-bottom: 6px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-weight: 600; color: #667eea;">{idx}.</span>
                        <span style="font-weight: 500;">{title}</span>
                        <span style="color: {type_color}; font-size: 0.85rem;">{type_icon} {type_label}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #666; margin-top: 4px;">
                        {f'Year: {year} ' if year else ''}
                        {f'| Journal: {journal}' if journal else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(filtered) > 50:
                st.info(f"Showing first 50 of {len(filtered)} articles")
        
        # Show statistics
        st.markdown("---")
        st.markdown("### 📊 Filtered Statistics")
        
        filtered_years = [a.get('publication_year', 0) for a in filtered if a.get('publication_year', 0) > 0]
        filtered_citations = sum(a.get('cited_by_count', 0) for a in filtered)
        filtered_avg_citations = filtered_citations / len(filtered) if filtered else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(filtered)}</div>
                <div class="metric-label">Filtered Articles</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{filtered_citations}</div>
                <div class="metric-label">Total Citations</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{filtered_avg_citations:.1f}</div>
                <div class="metric-label">Avg Citations/Article</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Generate reports button
        col_go1, col_go2, col_go3 = st.columns([1, 2, 1])
        with col_go2:
            if st.button("📊 Generate Reports from Filtered Articles", type="primary", use_container_width=True):
                st.session_state.current_step = 5
                st.rerun()
    
    elif 'filtered_articles' in st.session_state and not st.session_state.filtered_articles:
        st.warning("⚠️ No articles match your search query. Try a different query or reset the filter.")
    
    st.markdown("---")
    
    # New analysis button
    if st.button("🔄 New Analysis", use_container_width=True):
        keys_to_clear = ['current_step', 'dois', 'works_data', 'topic_counter', 
                        'keyword_counter', 'successful', 'failed', 'selected_topic',
                        'selected_topic_id', 'selected_years', 'all_works', 
                        'enriched_count', 'years_input', 'pdf_cache', 'all_reports_generated',
                        'filtered_articles', 'search_query', 'search_results_count']
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
    steps = ["Input", "Analysis", "Topic", "Years", "Reports", "Search"]
    current_step = st.session_state.current_step
    progress = (current_step - 1) / 5
    
    st.markdown(f"""
    <div class="progress-container" style="background: #f5f5f5; border-radius: 8px; height: 6px; margin: 20px 0; overflow: hidden;">
        <div class="progress-bar" style="height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 8px; transition: width 0.5s ease; width: {progress * 100}%;"></div>
    </div>
    <div class="step-indicator" style="display: flex; justify-content: space-between; margin: 15px 0; font-size: 0.85rem; color: #666;">
        <span class="{'active' if current_step >= 1 else ''}" style="color: {'#667eea' if current_step >= 1 else '#666'}; font-weight: {'600' if current_step >= 1 else '400'};">📥 Input</span>
        <span class="{'active' if current_step >= 2 else ''}" style="color: {'#667eea' if current_step >= 2 else '#666'}; font-weight: {'600' if current_step >= 2 else '400'};">🔍 Analysis</span>
        <span class="{'active' if current_step >= 3 else ''}" style="color: {'#667eea' if current_step >= 3 else '#666'}; font-weight: {'600' if current_step >= 3 else '400'};">🎯 Topic</span>
        <span class="{'active' if current_step >= 4 else ''}" style="color: {'#667eea' if current_step >= 4 else '#666'}; font-weight: {'600' if current_step >= 4 else '400'};">⏰ Years</span>
        <span class="{'active' if current_step >= 5 else ''}" style="color: {'#667eea' if current_step >= 5 else '#666'}; font-weight: {'600' if current_step >= 5 else '400'};">📊 Reports</span>
        <span class="{'active' if current_step >= 6 else ''}" style="color: {'#667eea' if current_step >= 6 else '#666'}; font-weight: {'600' if current_step >= 6 else '400'};">🔍 Search</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Display current step
    if st.session_state.current_step == 1:
        step_data_input()
    elif st.session_state.current_step == 2:
        step_analysis()
    elif st.session_state.current_step == 3:
        step_topic_selection()
    elif st.session_state.current_step == 4:
        step_year_selection()
    elif st.session_state.current_step == 5:
        step_results()
    elif st.session_state.current_step == 6:
        step_advanced_search()
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>© CTA, https://chimicatechnoacta.ru / developed by daM©</p>
        <p style="font-size: 0.7rem; color: #aaa;">CTA Article Recommender Pro*2 with multi-report generation</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
