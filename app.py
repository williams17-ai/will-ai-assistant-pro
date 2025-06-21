import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import time
from datetime import datetime, timedelta
import pytz
import uuid
import pandas as pd
import yfinance as yf
import requests
import feedparser
from bs4 import BeautifulSoup
from typing import Dict, List
import re
from urllib.parse import urljoin

load_dotenv()

# 設定台灣時區
TAIWAN_TZ = pytz.timezone('Asia/Taipei')

def get_taiwan_time():
    return datetime.now(TAIWAN_TZ)

# 支援Streamlit Cloud的環境變數讀取
def get_api_key():
    if hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    elif "GOOGLE_API_KEY" in os.environ:
        return os.environ["GOOGLE_API_KEY"]
    else:
        return None

# 新增：取得新聞API密鑰
def get_news_api_key():
    if hasattr(st, "secrets") and "NEWS_API_KEY" in st.secrets:
        return st.secrets["NEWS_API_KEY"]
    elif "NEWS_API_KEY" in os.environ:
        return os.environ["NEWS_API_KEY"]
    else:
        return None

# 設定API Key
api_key = get_api_key()
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key

news_api_key = get_news_api_key()

# 頁面設定
st.set_page_config(
    page_title="Will的AI小幫手 Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 2rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 15px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.pro-badge {
    background: linear-gradient(45deg, #FFD700, #FFA500);
    color: #333;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: bold;
    display: inline-block;
    margin-left: 0.5rem;
}

.real-time-badge {
    background: linear-gradient(45deg, #4CAF50, #45a049);
    color: white;
    padding: 0.2rem 0.6rem;
    border-radius: 15px;
    font-size: 0.7rem;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

.metric-card {
    background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    margin: 0.5rem 0;
}

.chat-message {
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 10px;
    border-left: 4px solid #667eea;
    background: #f8f9fa;
}

.search-highlight {
    background-color: yellow;
    font-weight: bold;
}

.news-card {
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 1rem;
    margin: 0.5rem 0;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.news-source {
    color: #666;
    font-size: 0.9rem;
}

.news-time {
    color: #888;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# 簡化的股票數據管理
class StockDataManager:
    def __init__(self):
        self.cache = {}
        self.cache_expiry = 300
    
    def get_stock_data(self, symbol):
        current_time = time.time()
        
        if symbol in self.cache:
            if current_time - self.cache[symbol]['timestamp'] < self.cache_expiry:
                return self.cache[symbol]['data']
        
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            info = stock.info
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                prev_close = info.get('previousClose', current_price)
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100
                
                data = {
                    'symbol': symbol,
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2),
                    'volume': info.get('volume', 0),
                    'name': info.get('longName', symbol)
                }
                
                self.cache[symbol] = {
                    'data': data,
                    'timestamp': current_time
                }
                
                return data
        except:
            pass
        return None

# 改進的新聞管理類
class NewsManager:
    def __init__(self):
        self.cache = {}
        self.cache_expiry = 1800  # 30分鐘快取
        self.rss_feeds = [
            'https://techcrunch.com/feed/',
            'https://www.theverge.com/rss/index.xml',
            'https://feeds.feedburner.com/venturebeat/SZYF',
            'https://www.wired.com/feed/rss',
            'https://arstechnica.com/feeds/rss/',
        ]
        
    def get_newsapi_news(self, query="artificial intelligence", language="en", page_size=10):
        """使用 NewsAPI 獲取新聞"""
        if not news_api_key:
            return []
            
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'language': language,
                'sortBy': 'publishedAt',
                'pageSize': page_size,
                'apiKey': news_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for article in data.get('articles', []):
                    # 解析發布時間
                    published_at = article.get('publishedAt', '')
                    if published_at:
                        try:
                            pub_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                            time_diff = datetime.now(pytz.UTC) - pub_time
                            if time_diff.days > 0:
                                time_str = f"{time_diff.days}天前"
                            elif time_diff.seconds > 3600:
                                time_str = f"{time_diff.seconds // 3600}小時前"
                            else:
                                time_str = f"{time_diff.seconds // 60}分鐘前"
                        except:
                            time_str = "時間未知"
                    else:
                        time_str = "時間未知"
                    
                    articles.append({
                        'title': article.get('title', '無標題'),
                        'summary': article.get('description', '無摘要'),
                        'link': article.get('url', '#'),
                        'published': time_str,
                        'source': article.get('source', {}).get('name', '未知來源'),
                        'image': article.get('urlToImage', '')
                    })
                
                return articles
        except Exception as e:
            print(f"NewsAPI 錯誤: {e}")
            
        return []
    
    def get_rss_news(self, max_articles=15):
        """從 RSS feeds 獲取新聞"""
        all_articles = []
        
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]:  # 每個feed最多取5篇
                    # 解析發布時間
                    published_time = "時間未知"
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            pub_time = datetime(*entry.published_parsed[:6], tzinfo=pytz.UTC)
                            time_diff = datetime.now(pytz.UTC) - pub_time
                            if time_diff.days > 0:
                                published_time = f"{time_diff.days}天前"
                            elif time_diff.seconds > 3600:
                                published_time = f"{time_diff.seconds // 3600}小時前"
                            else:
                                published_time = f"{time_diff.seconds // 60}分鐘前"
                        except:
                            pass
                    
                    # 取得摘要
                    summary = ""
                    if hasattr(entry, 'summary'):
                        # 清理HTML標籤
                        soup = BeautifulSoup(entry.summary, 'html.parser')
                        summary = soup.get_text()[:200] + "..." if len(soup.get_text()) > 200 else soup.get_text()
                    
                    article = {
                        'title': entry.get('title', '無標題'),
                        'summary': summary or '無摘要',
                        'link': entry.get('link', '#'),
                        'published': published_time,
                        'source': feed.feed.get('title', '未知來源'),
                        'image': ''
                    }
                    
                    # 嘗試獲取圖片
                    if hasattr(entry, 'media_content') and entry.media_content:
                        article['image'] = entry.media_content[0].get('url', '')
                    elif hasattr(entry, 'enclosures') and entry.enclosures:
                        for enclosure in entry.enclosures:
                            if enclosure.type.startswith('image/'):
                                article['image'] = enclosure.href
                                break
                    
                    all_articles.append(article)
                    
            except Exception as e:
                print(f"RSS feed 錯誤 ({feed_url}): {e}")
                continue
        
        # 根據時間排序並限制數量
        return all_articles[:max_articles]
    
    def get_fallback_news(self):
        """備用新聞（當API都無法使用時）"""
        return [
            {
                'title': 'Google Gemini 2.5 Flash 效能大幅提升',
                'summary': 'Google最新發布的Gemini 2.5 Flash在多項AI基準測試中表現優異，特別在程式碼生成和數學推理方面有顯著提升，處理速度比前一版本快30%。',
                'link': '#',
                'published': '2小時前',
                'source': 'AI科技新聞',
                'image': ''
            },
            {
                'title': 'OpenAI GPT-5 開發進展最新消息',
                'summary': '據可靠消息來源，OpenAI正在加速GPT-5的開發進程，新模型預計將在推理能力、多模態處理和程式碼生成方面帶來革命性改進。',
                'link': '#',
                'published': '4小時前',
                'source': 'TechCrunch',
                'image': ''
            },
            {
                'title': 'AI醫療診斷準確率創新高',
                'summary': '最新研究顯示，AI系統在皮膚癌、眼科疾病等特定領域的診斷準確率已經超越資深醫生，為醫療行業數位轉型提供強力支撐。',
                'link': '#',
                'published': '6小時前',
                'source': 'The Verge',
                'image': ''
            },
            {
                'title': '微軟Copilot整合新功能發布',
                'summary': 'Microsoft宣布Copilot將整合更多Office應用，包括PowerPoint自動生成、Excel智能分析等功能，預計下月正式上線。',
                'link': '#',
                'published': '8小時前',
                'source': 'Microsoft新聞',
                'image': ''
            },
            {
                'title': 'AI晶片市場競爭白熱化',
                'summary': 'NVIDIA、AMD、Intel在AI晶片領域展開激烈競爭，新一代產品性能提升的同時，價格戰也正式開打，預計將促進AI技術普及。',
                'link': '#',
                'published': '12小時前',
                'source': 'Wired',
                'image': ''
            }
        ]
    
    def get_news(self, force_refresh=False):
        """統一的新聞獲取介面"""
        current_time = time.time()
        
        if not force_refresh and 'news' in self.cache:
            if current_time - self.cache['news']['timestamp'] < self.cache_expiry:
                return self.cache['news']['data']
        
        # 優先嘗試 NewsAPI
        news_articles = []
        if news_api_key:
            news_articles = self.get_newsapi_news()
        
        # 如果NewsAPI沒有結果，嘗試RSS
        if not news_articles:
            news_articles = self.get_rss_news()
        
        # 如果都沒有結果，使用備用新聞
        if not news_articles:
            news_articles = self.get_fallback_news()
        
        # 快取結果
        self.cache['news'] = {
            'data': news_articles,
            'timestamp': current_time
        }
        
        return news_articles

# 改進的聊天管理類
class ChatManager:
    def __init__(self):
        self.chats = {}
        self.settings = {
            'personality': '友善',
            'response_length': 3,
            'auto_save': True
        }
    
    def add_message(self, chat_id, user_message, ai_response, timestamp=None):
        """添加對話記錄"""
        if timestamp is None:
            timestamp = get_taiwan_time()
        
        if chat_id not in self.chats:
            self.chats[chat_id] = {
                'title': user_message[:30] + "..." if len(user_message) > 30 else user_message,
                'messages': [],
                'created_at': timestamp
            }
        
        self.chats[chat_id]['messages'].append({
            'user': user_message,
            'ai': ai_response,
            'timestamp': timestamp
        })
    
    def search_chats(self, keyword):
        """搜尋對話記錄"""
        results = []
        keyword_lower = keyword.lower()
        
        for chat_id, chat_data in self.chats.items():
            # 搜尋標題
            if keyword_lower in chat_data['title'].lower():
                results.append({
                    'chat_id': chat_id,
                    'title': chat_data['title'],
                    'type': 'title',
                    'content': chat_data['title'],
                    'timestamp': chat_data['created_at']
                })
            
            # 搜尋訊息內容
            for i, message in enumerate(chat_data['messages']):
                # 搜尋用戶訊息
                if keyword_lower in message['user'].lower():
                    results.append({
                        'chat_id': chat_id,
                        'title': chat_data['title'],
                        'type': 'user_message',
                        'content': message['user'],
                        'ai_response': message['ai'],
                        'timestamp': message['timestamp'],
                        'message_index': i
                    })
                
                # 搜尋AI回應
                if keyword_lower in message['ai'].lower():
                    results.append({
                        'chat_id': chat_id,
                        'title': chat_data['title'],
                        'type': 'ai_message',
                        'content': message['ai'],
                        'user_message': message['user'],
                        'timestamp': message['timestamp'],
                        'message_index': i
                    })
        
        # 按時間排序，最新的在前
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        return results
    
    def highlight_keyword(self, text, keyword):
        """高亮關鍵字"""
        if not keyword:
            return text
        
        # 使用正則表達式進行不區分大小寫的替換
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        return pattern.sub(f'<span class="search-highlight">{keyword}</span>', text)
    
    def get_chat_history(self, chat_id):
        """獲取特定對話的歷史記錄"""
        return self.chats.get(chat_id, None)
    
    def delete_chat(self, chat_id):
        """刪除對話"""
        if chat_id in self.chats:
            del self.chats[chat_id]
            return True
        return False

# 初始化
if "stock_manager" not in st.session_state:
    st.session_state.stock_manager = StockDataManager()

if "news_manager" not in st.session_state:
    st.session_state.news_manager = NewsManager()

if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()

if "current_page" not in st.session_state:
    st.session_state.current_page = "主頁"

if "watched_stocks" not in st.session_state:
    st.session_state.watched_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# 初始化Gemini
@st.cache_resource
def init_gemini():
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        return genai.GenerativeModel('gemini-2.5-flash')
    except:
        return None

model = init_gemini()

# 側邊欄
with st.sidebar:
    st.markdown("""
    <div class="main-header" style="margin-bottom: 1rem;">
        <h2>🚀 Will的AI小幫手</h2>
        <span class="pro-badge">PRO</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 即時狀態指示器
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<span class="real-time-badge">🔴 即時數據</span>', unsafe_allow_html=True)
    with col2:
        taiwan_time = get_taiwan_time()
        st.markdown(f"⏰ {taiwan_time.strftime('%H:%M')}")
    
    # 頁面導航
    st.markdown("### 📋 功能選單")
    
    if st.button("🏠 智能主頁", use_container_width=True, 
                 type="primary" if st.session_state.current_page == "主頁" else "secondary"):
        st.session_state.current_page = "主頁"
        st.rerun()
    
    if st.button("💬 AI對話", use_container_width=True,
                 type="primary" if st.session_state.current_page == "對話" else "secondary"):
        st.session_state.current_page = "對話"
        st.rerun()
    
    if st.button("📊 即時股市", use_container_width=True,
                 type="primary" if st.session_state.current_page == "股市" else "secondary"):
        st.session_state.current_page = "股市"
        st.rerun()
    
    if st.button("📰 AI新知", use_container_width=True,
                 type="primary" if st.session_state.current_page == "新知" else "secondary"):
        st.session_state.current_page = "新知"
        st.rerun()
    
    if st.button("🎯 智能推薦", use_container_width=True,
                 type="primary" if st.session_state.current_page == "推薦" else "secondary"):
        st.session_state.current_page = "推薦"
        st.rerun()
    
    if st.button("⚙️ 進階設定", use_container_width=True,
                 type="primary" if st.session_state.current_page == "設定" else "secondary"):
        st.session_state.current_page = "設定"
        st.rerun()

# 主要內容區域
if st.session_state.current_page == "主頁":
    st.markdown("""
    <div class="main-header">
        <h1>🎉 歡迎回來，Will！</h1>
        <p>你的專屬AI助手 Pro版 已準備就緒</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 快速功能
    st.markdown("### 🚀 快速開始")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤖 開始AI對話", key="quick_chat", use_container_width=True):
            st.session_state.current_page = "對話"
            st.rerun()
    
    with col2:
        if st.button("📰 查看AI新聞", key="quick_news", use_container_width=True):
            st.session_state.current_page = "新知"
            st.rerun()
    
    with col3:
        if st.button("📊 查看股市", key="quick_stock", use_container_width=True):
            st.session_state.current_page = "股市"
            st.rerun()
    
    # 系統狀態
    st.markdown("### 📊 系統狀態")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        api_status = "🟢 正常" if model else "🔴 錯誤"
        st.markdown(f"""
        <div class="metric-card">
            <h4>🤖 AI狀態</h4>
            <h3>{api_status}</h3>
            <p style="color: white;">Gemini API</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        stock_count = len(st.session_state.watched_stocks)
        st.markdown(f"""
        <div class="metric-card">
            <h4>📊 關注股票</h4>
            <h3>{stock_count}</h3>
            <p style="color: white;">檔股票</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        chat_count = len(st.session_state.chat_manager.chats)
        st.markdown(f"""
        <div class="metric-card">
            <h4>💬 對話記錄</h4>
            <h3>{chat_count}</h3>
            <p style="color: white;">個對話</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        current_time = get_taiwan_time().strftime('%H:%M')
        st.markdown(f"""
        <div class="metric-card">
            <h4>⏰ 台灣時間</h4>
            <h3>{current_time}</h3>
            <p style="color: white;">即時更新</p>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.current_page == "對話":
    st.title("💬 AI智能對話")
    
    if not model:
        st.error("❌ AI模型未初始化，請檢查API密鑰設定")
        st.info("請在Streamlit Cloud的Secrets中正確設定 GOOGLE_API_KEY")
        
        with st.expander("📋 如何設定API密鑰"):
            st.markdown("""
            1. 前往 [Google AI Studio](https://makersuite.google.com/app/apikey) 獲取API密鑰
            2. 在Streamlit Cloud點擊右下角 "Manage app"
            3. 選擇 "Secrets" 標籤
            4. 添加：`GOOGLE_API_KEY = "你的API密鑰"`
            5. 保存並重新啟動應用
            """)
    else:
        # 對話搜尋功能
        st.markdown("### 🔍 搜尋對話記錄")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_keyword = st.text_input("輸入關鍵字搜尋對話記錄", placeholder="例如：Python、股票、投資", key="search_input")
        
        with col2:
            if st.button("🔍 搜尋", key="search_chat"):
                if search_keyword.strip():
                    search_results = st.session_state.chat_manager.search_chats(search_keyword.strip())
                    
                    if search_results:
                        st.markdown(f"### 🎯 搜尋結果 ({len(search_results)} 筆)")
                        
                        for result in search_results[:10]:  # 限制顯示前10筆結果
                            with st.expander(f"📝 {result['title']} - {result['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                                if result['type'] == 'user_message':
                                    st.markdown("**👤 你的問題：**")
                                    highlighted_content = st.session_state.chat_manager.highlight_keyword(result['content'], search_keyword)
                                    st.markdown(highlighted_content, unsafe_allow_html=True)
                                    
                                    st.markdown("**🤖 AI回應：**")
                            st.write(response.text)
                            
                    except Exception as e:
                        st.error(f"AI回應錯誤：{str(e)}")
                else:
                    st.warning("請輸入問題後再發送")
        
        with col2:
            if st.button("🔄 新對話", key="new_chat"):
                st.session_state.current_chat_id = None
                st.rerun()
        
        # 顯示當前對話歷史
        if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chat_manager.chats:
            st.markdown("---")
            st.markdown("### 💬 當前對話記錄")
            
            chat_history = st.session_state.chat_manager.get_chat_history(st.session_state.current_chat_id)
            
            for i, message in enumerate(chat_history['messages']):
                with st.container():
                    st.markdown(f"""
                    <div class="chat-message">
                        <strong>👤 你：</strong> {message['user']}<br>
                        <strong>🤖 AI：</strong> {message['ai']}<br>
                        <small style="color: #666;">時間：{message['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</small>
                    </div>
                    """, unsafe_allow_html=True)

elif st.session_state.current_page == "股市":
    st.title("📊 即時美股追蹤")
    
    # 股票輸入
    col1, col2 = st.columns([3, 1])
    with col1:
        new_stock = st.text_input("輸入股票代碼", placeholder="例如: AAPL, TSLA, GOOGL", key="stock_input")
    with col2:
        if st.button("➕ 添加", key="add_stock"):
            if new_stock and new_stock.upper() not in st.session_state.watched_stocks:
                st.session_state.watched_stocks.append(new_stock.upper())
                st.success(f"已添加 {new_stock.upper()}")
                st.rerun()
    
    # 顯示關注的股票
    if st.session_state.watched_stocks:
        st.markdown("### 💼 我的關注股票")
        
        for i, stock in enumerate(st.session_state.watched_stocks):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                st.write(f"**{stock}**")
            
            with col2:
                try:
                    stock_data = st.session_state.stock_manager.get_stock_data(stock)
                    if stock_data:
                        st.write(f"${stock_data['price']}")
                    else:
                        st.write("載入中...")
                except:
                    st.write("無法載入")
            
            with col3:
                try:
                    if stock_data:
                        change_color = "green" if stock_data['change_percent'] >= 0 else "red"
                        st.markdown(f"<span style='color: {change_color};'>{stock_data['change_percent']:+.2f}%</span>", 
                                  unsafe_allow_html=True)
                except:
                    st.write("--")
            
            with col4:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.watched_stocks.remove(stock)
                    st.rerun()
    else:
        st.info("還沒有關注的股票，請添加一些股票開始追蹤")

elif st.session_state.current_page == "新知":
    st.title("📰 AI新知與科技資訊")
    
    # 新聞來源狀態
    col1, col2, col3 = st.columns(3)
    with col1:
        newsapi_status = "🟢 可用" if news_api_key else "🔴 未設定"
        st.metric("NewsAPI", newsapi_status)
    
    with col2:
        st.metric("RSS來源", "🟢 5個")
    
    with col3:
        if st.button("🔄 重新整理新聞", key="refresh_news"):
            # 強制重新取得新聞
            news_list = st.session_state.news_manager.get_news(force_refresh=True)
            st.success("新聞已更新！")
            st.rerun()
    
    # 如果沒有NewsAPI，顯示設定說明
    if not news_api_key:
        with st.expander("⚙️ 如何設定NewsAPI（獲取即時新聞）"):
            st.markdown("""
            **設定NewsAPI步驟：**
            1. 前往 [NewsAPI官網](https://newsapi.org/) 免費註冊
            2. 獲取API Key
            3. 在Streamlit Cloud的Secrets設定中添加：
            ```
            NEWS_API_KEY = "你的NewsAPI密鑰"
            ```
            4. 重新啟動應用即可獲取即時新聞
            
            **注意：** 免費版每日有100次請求限制，足夠一般使用
            """)
    
    # 載入新聞
    with st.spinner("📰 載入最新新聞..."):
        news_list = st.session_state.news_manager.get_news()
    
    if news_list:
        st.markdown("### 🔥 最新科技新聞")
        
        # 新聞篩選
        col1, col2 = st.columns([2, 1])
        with col1:
            search_news = st.text_input("🔍 搜尋新聞", placeholder="輸入關鍵字篩選新聞", key="news_search")
        
        # 篩選新聞
        filtered_news = news_list
        if search_news:
            filtered_news = [
                news for news in news_list 
                if search_news.lower() in news['title'].lower() or 
                   search_news.lower() in news['summary'].lower()
            ]
        
        if filtered_news:
            for i, news in enumerate(filtered_news):
                with st.container():
                    st.markdown(f"""
                    <div class="news-card">
                        <h4>📰 {news['title']}</h4>
                        <p>{news['summary']}</p>
                        <div style="margin-top: 10px;">
                            <span class="news-source">📡 {news['source']}</span>
                            <span class="news-time" style="margin-left: 20px;">⏰ {news['published']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if news['link'] != '#':
                            st.markdown(f"[📖 閱讀原文]({news['link']})")
                        else:
                            st.info("範例新聞")
                    
                    with col2:
                        if st.button("🤖 AI解讀", key=f"analyze_{i}"):
                            if model:
                                try:
                                    with st.spinner("🤔 AI分析中..."):
                                        analysis_prompt = f"""請分析這則新聞並用繁體中文回答：
                                        標題：{news['title']}
                                        摘要：{news['summary']}
                                        
                                        請提供：
                                        1. 新聞重點摘要
                                        2. 對科技產業的影響
                                        3. 未來發展預測
                                        """
                                        
                                        response = model.generate_content(analysis_prompt)
                                        
                                        with st.expander("🤖 AI深度分析", expanded=True):
                                            st.write(response.text)
                                except Exception as e:
                                    st.error(f"分析失敗：{e}")
                            else:
                                st.error("AI模型未初始化")
                    
                    with col3:
                        if st.button("📤 分享", key=f"share_{i}"):
                            share_text = f"📰 {news['title']}\n\n{news['summary']}\n\n來源：{news['source']}"
                            st.text_area("分享內容", value=share_text, height=100, key=f"share_text_{i}")
                    
                    st.markdown("---")
        else:
            st.info("沒有找到符合條件的新聞")
    else:
        st.error("無法載入新聞，請檢查網路連線或稍後再試")

elif st.session_state.current_page == "推薦":
    st.title("🎯 智能推薦系統")
    
    # 基於用戶活動的個人化推薦
    st.markdown("### 📊 個人化分析")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        chat_count = len(st.session_state.chat_manager.chats)
        st.metric("對話次數", chat_count)
        
        if chat_count > 0:
            # 分析最常討論的主題
            all_messages = []
            for chat in st.session_state.chat_manager.chats.values():
                for message in chat['messages']:
                    all_messages.append(message['user'])
            
            # 簡單的關鍵字分析
            tech_keywords = ['Python', 'AI', '程式', '開發', '學習', '技術']
            finance_keywords = ['股票', '投資', '金融', '市場', '經濟']
            
            tech_count = sum(1 for msg in all_messages for keyword in tech_keywords if keyword.lower() in msg.lower())
            finance_count = sum(1 for msg in all_messages for keyword in finance_keywords if keyword.lower() in msg.lower())
            
            if tech_count > finance_count:
                st.success("🔧 你偏好技術類話題")
            elif finance_count > tech_count:
                st.success("💰 你偏好金融類話題")
            else:
                st.info("🎯 興趣廣泛")
    
    with col2:
        stock_count = len(st.session_state.watched_stocks)
        st.metric("關注股票", stock_count)
        
        if stock_count > 0:
            # 股票類型分析
            tech_stocks = ['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA', 'META', 'AMZN']
            user_tech_stocks = [stock for stock in st.session_state.watched_stocks if stock in tech_stocks]
            
            if len(user_tech_stocks) / stock_count > 0.7:
                st.success("💻 偏愛科技股")
            else:
                st.info("📈 投資組合多元化")
    
    with col3:
        current_hour = get_taiwan_time().hour
        if 9 <= current_hour <= 12:
            activity_period = "🌅 晨間活躍"
        elif 13 <= current_hour <= 17:
            activity_period = "☀️ 午後活躍"
        elif 18 <= current_hour <= 22:
            activity_period = "🌆 晚間活躍"
        else:
            activity_period = "🌙 夜間活躍"
        
        st.metric("活動時段", activity_period)
    
    # 學習推薦
    st.markdown("### 📚 推薦學習資源")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔥 熱門技術課程")
        courses = [
            "🐍 Python進階程式設計",
            "🤖 機器學習實戰應用",
            "📊 數據科學與視覺化",
            "🌐 全端網頁開發",
            "☁️ 雲端架構設計"
        ]
        for course in courses:
            if st.button(course, key=f"course_{course}"):
                st.info(f"已將 {course} 加入學習清單")
    
    with col2:
        st.markdown("#### 💡 基於你的興趣推薦")
        
        # 基於對話記錄的智能推薦
        if len(st.session_state.chat_manager.chats) > 0:
            recommendations = []
            
            # 分析對話內容給出推薦
            all_text = ""
            for chat in st.session_state.chat_manager.chats.values():
                for message in chat['messages']:
                    all_text += message['user'] + " "
            
            if any(keyword in all_text.lower() for keyword in ['python', '程式', '開發']):
                recommendations.append("🐍 Python進階技巧")
                recommendations.append("🔧 開發工具使用")
            
            if any(keyword in all_text.lower() for keyword in ['股票', '投資', '金融']):
                recommendations.append("📈 量化投資策略")
                recommendations.append("💰 財務分析方法")
            
            if any(keyword in all_text.lower() for keyword in ['ai', '人工智慧', '機器學習']):
                recommendations.append("🤖 深度學習框架")
                recommendations.append("🧠 AI模型部署")
            
            if recommendations:
                for rec in recommendations:
                    st.write(f"• {rec}")
            else:
                st.write("• 🎯 多元化學習建議")
                st.write("• 📊 數據分析基礎")
                st.write("• 🔍 批判性思考")
        else:
            st.write("• 🎯 開始對話後獲得個人化推薦")
            st.write("• 📊 數據分析基礎")
            st.write("• 🔍 批判性思考")
    
    # 投資建議
    st.markdown("### 💰 投資組合建議")
    
    if st.session_state.watched_stocks:
        # 簡單的投資組合分析
        tech_stocks = ['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA', 'META', 'AMZN']
        financial_stocks = ['JPM', 'BAC', 'WFC', 'GS']
        healthcare_stocks = ['JNJ', 'PFE', 'UNH', 'ABBV']
        
        user_tech = [s for s in st.session_state.watched_stocks if s in tech_stocks]
        user_financial = [s for s in st.session_state.watched_stocks if s in financial_stocks]
        user_healthcare = [s for s in st.session_state.watched_stocks if s in healthcare_stocks]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📊 持股分析")
            st.write(f"科技股：{len(user_tech)} 檔")
            st.write(f"金融股：{len(user_financial)} 檔")
            st.write(f"醫療股：{len(user_healthcare)} 檔")
        
        with col2:
            st.markdown("#### 💡 多元化建議")
            total_stocks = len(st.session_state.watched_stocks)
            if len(user_tech) / total_stocks > 0.8:
                st.warning("⚠️ 科技股過度集中")
                st.info("建議增加其他類股")
            else:
                st.success("✅ 投資組合相對均衡")
        
        with col3:
            st.markdown("#### 🎯 推薦關注")
            if len(user_financial) == 0:
                st.write("• 金融類股 (JPM, BAC)")
            if len(user_healthcare) == 0:
                st.write("• 醫療類股 (JNJ, UNH)")
            if len(user_tech) < 3:
                st.write("• 更多科技股 (META, AMZN)")
    else:
        st.info("開始添加關注股票來獲得投資建議")

elif st.session_state.current_page == "設定":
    st.title("⚙️ 進階設定")
    
    # API狀態檢查
    st.markdown("### 🔑 API設定狀態")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🤖 Gemini AI")
        if model:
            st.success("✅ Gemini API 連接正常")
        else:
            st.error("❌ Gemini API 未連接")
            st.info("請檢查 GOOGLE_API_KEY 設定")
    
    with col2:
        st.markdown("#### 📰 新聞API")
        if news_api_key:
            st.success("✅ NewsAPI 已設定")
        else:
            st.warning("⚠️ NewsAPI 未設定")
            st.info("設定後可獲取即時新聞")
    
    # API設定說明
    with st.expander("📋 API設定指南"):
        st.markdown("""
        **在Streamlit Cloud設定API密鑰：**
        
        1. **Gemini API (必須):**
           - 前往 [Google AI Studio](https://makersuite.google.com/app/apikey)
           - 獲取免費API密鑰
           - 在Secrets中設定：`GOOGLE_API_KEY = "你的密鑰"`
        
        2. **NewsAPI (選用):**
           - 前往 [NewsAPI](https://newsapi.org/) 註冊
           - 獲取免費API密鑰（每日100次請求）
           - 在Secrets中設定：`NEWS_API_KEY = "你的密鑰"`
        
        **設定步驟：**
        1. 在應用右下角點擊 "Manage app"
        2. 選擇 "Secrets" 標籤
        3. 添加API密鑰
        4. 點擊 "Save" 並重新啟動應用
        """)
    
    # 基本設定
    st.markdown("### 🎨 應用設定")
    
    col1, col2 = st.columns(2)
    with col1:
        personality = st.selectbox(
            "AI回答風格",
            ["友善", "專業", "幽默", "簡潔"],
            index=0,
            key="ai_personality"
        )
        st.session_state.chat_manager.settings['personality'] = personality
    
    with col2:
        auto_refresh = st.checkbox(
            "自動刷新數據",
            value=True,
            key="auto_refresh_setting"
        )
    
    # 數據管理
    st.markdown("### 📊 數據管理")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ 清除對話記錄", key="clear_chats"):
            if st.session_state.chat_manager.chats:
                st.session_state.chat_manager.chats.clear()
                st.session_state.current_chat_id = None
                st.success("對話記錄已清除")
                st.rerun()
            else:
                st.info("沒有對話記錄需要清除")
    
    with col2:
        if st.button("📊 重置股票清單", key="reset_stocks"):
            st.session_state.watched_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
            st.success("股票清單已重置")
            st.rerun()
    
    with col3:
        if st.button("🔄 清除所有快取", key="clear_cache"):
            st.session_state.stock_manager.cache.clear()
            st.session_state.news_manager.cache.clear()
            st.success("快取已清除")
    
    # 匯出功能
    st.markdown("### 📤 數據匯出")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📁 匯出對話記錄", key="export_chats"):
            if st.session_state.chat_manager.chats:
                export_data = {
                    'export_time': get_taiwan_time().isoformat(),
                    'total_chats': len(st.session_state.chat_manager.chats),
                    'chats': {}
                }
                
                for chat_id, chat_data in st.session_state.chat_manager.chats.items():
                    export_data['chats'][chat_id] = {
                        'title': chat_data['title'],
                        'created_at': chat_data['created_at'].isoformat(),
                        'messages': [
                            {
                                'user': msg['user'],
                                'ai': msg['ai'],
                                'timestamp': msg['timestamp'].isoformat()
                            }
                            for msg in chat_data['messages']
                        ]
                    }
                
                st.download_button(
                    label="📥 下載對話記錄 (JSON)",
                    data=json.dumps(export_data, ensure_ascii=False, indent=2),
                    file_name=f"chat_history_{get_taiwan_time().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.info("沒有對話記錄可匯出")
    
    with col2:
        if st.button("📈 匯出股票清單", key="export_stocks"):
            stock_data = {
                'export_time': get_taiwan_time().isoformat(),
                'watched_stocks': st.session_state.watched_stocks
            }
            
            st.download_button(
                label="📥 下載股票清單 (JSON)",
                data=json.dumps(stock_data, ensure_ascii=False, indent=2),
                file_name=f"stocks_{get_taiwan_time().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # 系統資訊
    st.markdown("### 📊 系統統計")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("對話總數", len(st.session_state.chat_manager.chats))
    with col2:
        total_messages = sum(len(chat['messages']) for chat in st.session_state.chat_manager.chats.values())
        st.metric("訊息總數", total_messages)
    with col3:
        st.metric("關注股票", len(st.session_state.watched_stocks))
    with col4:
        current_time = get_taiwan_time().strftime('%H:%M')
        st.metric("當前時間", current_time)

else:
    st.title("🚀 Will的AI小幫手 Pro")
    st.info("請從左側選單選擇功能")

# 頁腳
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**🚀 Will的AI小幫手Pro**")
    st.caption("專業版AI生活助理")

with col2:
    st.markdown("**📊 實時數據**")
    st.caption(f"股票: {len(st.session_state.watched_stocks)} | 對話: {len(st.session_state.chat_manager.chats)}")

with col3:
    current_hour = get_taiwan_time().hour
    market_status = "🟢 開盤中" if 22 <= current_hour or current_hour <= 5 else "🔴 休市"
    st.markdown(f"**{market_status}**")
    st.caption("美股交易狀態")

with col4:
    taiwan_time = get_taiwan_time()
    st.markdown(f"**⏰ {taiwan_time.strftime('%H:%M:%S')}**")
    st.caption("台灣時間")")
                                    highlighted_response = st.session_state.chat_manager.highlight_keyword(result['ai_response'], search_keyword)
                                    st.markdown(highlighted_response, unsafe_allow_html=True)
                                
                                elif result['type'] == 'ai_message':
                                    st.markdown("**👤 你的問題：**")
                                    st.write(result['user_message'])
                                    
                                    st.markdown("**🤖 AI回應：**")
                                    highlighted_content = st.session_state.chat_manager.highlight_keyword(result['content'], search_keyword)
                                    st.markdown(highlighted_content, unsafe_allow_html=True)
                                
                                # 載入完整對話按鈕
                                if st.button(f"📖 查看完整對話", key=f"load_chat_{result['chat_id']}"):
                                    st.session_state.current_chat_id = result['chat_id']
                                    st.rerun()
                    else:
                        st.info("沒有找到相關的對話記錄")
                else:
                    st.warning("請輸入搜尋關鍵字")
        
        st.markdown("---")
        
        # 新對話區域
        st.markdown("### 💭 開始新對話")
        st.success("✅ AI模型已就緒，可以開始對話")
        
        # 對話介面
        user_input = st.text_area("輸入你的問題：", height=100, key="chat_input")
        
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("💬 發送", key="send_msg", type="primary"):
                if user_input.strip():
                    try:
                        with st.spinner("🤔 AI正在思考..."):
                            prompt = f"請用繁體中文回答以下問題：{user_input}"
                            response = model.generate_content(prompt)
                            
                            # 生成對話ID
                            if st.session_state.current_chat_id is None:
                                st.session_state.current_chat_id = str(uuid.uuid4())
                            
                            # 儲存對話記錄
                            st.session_state.chat_manager.add_message(
                                st.session_state.current_chat_id,
                                user_input,
                                response.text
                            )
                            
                            st.markdown("---")
                            st.markdown("**👤 你的問題：**")
                            st.write(user_input)
                            
                            st.markdown("**🤖 AI回應：**
