# 雲端部署支援
def get_api_key():
    if hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    elif "GOOGLE_API_KEY" in os.environ:
        return os.environ["GOOGLE_API_KEY"]
    return None

api_key = get_api_key()
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import time
from datetime import datetime, timedelta
import uuid
import pandas as pd
import yfinance as yf
import requests
import feedparser
from bs4 import BeautifulSoup
from typing import Dict, List
import threading
import schedule

load_dotenv()

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
    
    .stock-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .stock-card:hover {
        transform: translateY(-5px);
    }
    
    .news-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #4CAF50;
        transition: all 0.3s ease;
    }
    
    .news-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 25px rgba(0,0,0,0.15);
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
    
    .error-card {
        background: #ffe6e6;
        border: 1px solid #ffcccc;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .success-card {
        background: #e6ffe6;
        border: 1px solid #ccffcc;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 股票代碼匹配功能
class StockSymbolMatcher:
    def __init__(self):
        # 常見股票名稱對應代碼的字典
        self.stock_mapping = {
            # 科技股
            'apple': 'AAPL', 'tesla': 'TSLA', 'microsoft': 'MSFT', 'google': 'GOOGL',
            'amazon': 'AMZN', 'meta': 'META', 'nvidia': 'NVDA', 'netflix': 'NFLX',
            'intel': 'INTC', 'amd': 'AMD', 'oracle': 'ORCL', 'salesforce': 'CRM',
            # 金融股
            'jpmorgan': 'JPM', 'visa': 'V', 'mastercard': 'MA', 'paypal': 'PYPL',
            'bank of america': 'BAC', 'goldman sachs': 'GS', 'morgan stanley': 'MS',
            # 其他知名股票
            'coca cola': 'KO', 'disney': 'DIS', 'nike': 'NKE', 'mcdonalds': 'MCD',
            'johnson & johnson': 'JNJ', 'pfizer': 'PFE', 'walmart': 'WMT',
            # 中文名稱對應
            '蘋果': 'AAPL', '特斯拉': 'TSLA', '微軟': 'MSFT', '谷歌': 'GOOGL',
            '亞馬遜': 'AMZN', '臉書': 'META', '輝達': 'NVDA', '網飛': 'NFLX',
            '英特爾': 'INTC', '超微': 'AMD', '甲骨文': 'ORCL',
        }
    
    def get_suggestions(self, query):
        """根據輸入獲取股票代碼建議"""
        if not query:
            return []
        
        query = query.lower().strip()
        suggestions = []
        
        # 精確匹配
        if query in self.stock_mapping:
            suggestions.append(self.stock_mapping[query])
        
        # 模糊匹配
        for name, symbol in self.stock_mapping.items():
            if query in name or name in query:
                if symbol not in suggestions:
                    suggestions.append(symbol)
        
        # 如果輸入的就是股票代碼
        if query.upper().isalpha() and len(query) <= 5:
            suggestions.append(query.upper())
        
        return suggestions[:5]  # 最多返回5個建議

# 真實股市數據獲取
class StockDataManager:
    def __init__(self):
        self.cache = {}
        self.cache_expiry = 300  # 5分鐘緩存
    
    def get_stock_data(self, symbol):
        """獲取真實股票數據"""
        current_time = time.time()
        
        # 檢查緩存
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
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('trailingPE', 'N/A'),
                    'name': info.get('longName', symbol)
                }
                
                # 更新緩存
                self.cache[symbol] = {
                    'data': data,
                    'timestamp': current_time
                }
                
                return data
            
        except Exception as e:
            st.error(f"獲取 {symbol} 數據失敗：{e}")
            return None
    
    def get_market_indices(self):
        """獲取主要市場指數"""
        indices = {
            '^DJI': '道瓊工業',
            '^GSPC': '標普500',
            '^IXIC': '納斯達克'
        }
        
        results = {}
        for symbol, name in indices.items():
            data = self.get_stock_data(symbol)
            if data:
                results[name] = data
        
        return results

# AI新聞數據管理
class NewsManager:
    def __init__(self):
        self.cache = {}
        self.cache_expiry = 1800  # 30分鐘緩存
    
    def get_ai_news(self):
        """獲取AI相關新聞"""
        current_time = time.time()
        
        # 檢查緩存
        if 'ai_news' in self.cache:
            if current_time - self.cache['ai_news']['timestamp'] < self.cache_expiry:
                return self.cache['ai_news']['data']
        
        try:
            # 使用RSS訂閱獲取新聞
            feeds = [
                'https://techcrunch.com/category/artificial-intelligence/feed/',
                'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml',
                'https://venturebeat.com/ai/feed/'
            ]
            
            all_news = []
            
            for feed_url in feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:5]:  # 每個來源取5篇
                        all_news.append({
                            'title': entry.title,
                            'summary': entry.summary[:200] + '...' if len(entry.summary) > 200 else entry.summary,
                            'link': entry.link,
                            'published': entry.published if hasattr(entry, 'published') else '未知時間',
                            'source': feed.feed.title if hasattr(feed.feed, 'title') else '未知來源'
                        })
                except Exception as e:
                    continue
            
            # 按發布時間排序
            all_news.sort(key=lambda x: x['published'], reverse=True)
            
            # 更新緩存
            self.cache['ai_news'] = {
                'data': all_news[:15],  # 取前15篇
                'timestamp': current_time
            }
            
            return all_news[:15]
            
        except Exception as e:
            st.error(f"獲取新聞失敗：{e}")
            return self.get_fallback_news()
    
    def get_fallback_news(self):
        """備用新聞數據"""
        return [
            {
                'title': 'Google Gemini 2.5 Flash 性能突破',
                'summary': 'Google最新發布的Gemini 2.5 Flash在多項AI基準測試中表現優異，特別在程式碼生成和數學推理方面有顯著提升...',
                'link': '#',
                'published': '2小時前',
                'source': 'AI科技新聞'
            },
            {
                'title': 'OpenAI GPT-5 開發進展曝光',
                'summary': '據內部消息，OpenAI正在加速GPT-5的開發，預計將在推理能力和多模態處理方面帶來革命性改進...',
                'link': '#',
                'published': '4小時前',
                'source': 'TechCrunch'
            }
        ]
    
    def search_news(self, query, max_results=10):
        """搜尋特定主題新聞"""
        try:
            # 使用Google News API或其他新聞API
            # 這裡使用簡化版本
            all_news = self.get_ai_news()
            filtered_news = [
                news for news in all_news 
                if query.lower() in news['title'].lower() or query.lower() in news['summary'].lower()
            ]
            return filtered_news[:max_results]
        except:
            return []

# 智能推薦系統
class RecommendationEngine:
    def __init__(self, chat_manager):
        self.chat_manager = chat_manager
    
    def get_chat_recommendations(self):
        """基於聊天記錄推薦相關主題"""
        # 分析聊天記錄中的關鍵詞
        keywords = {}
        for chat in self.chat_manager.chats.values():
            for message in chat['messages']:
                if message['role'] == 'user':
                    content = message['content'].lower()
                    # 簡單的關鍵詞提取
                    for word in ['python', 'javascript', 'ai', '股票', '投資', '學習']:
                        if word in content:
                            keywords[word] = keywords.get(word, 0) + 1
        
        # 基於關鍵詞生成推薦
        recommendations = []
        if keywords.get('python', 0) > 2:
            recommendations.append("🐍 Python進階教學")
        if keywords.get('股票', 0) > 1:
            recommendations.append("📈 投資策略分析")
        if keywords.get('ai', 0) > 3:
            recommendations.append("🤖 AI技術深度探討")
        
        return recommendations[:5]
    
    def get_stock_recommendations(self, watched_stocks):
        """基於關注股票推薦相關股票"""
        recommendations = []
        
        # 基於已關注股票的行業推薦相關股票
        tech_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        finance_stocks = ['JPM', 'BAC', 'GS', 'MS']
        
        for stock in watched_stocks:
            if stock in tech_stocks:
                recommendations.extend(['NVDA', 'AMD', 'CRM'])
            elif stock in finance_stocks:
                recommendations.extend(['V', 'MA', 'PYPL'])
        
        # 去重並限制數量
        return list(set(recommendations))[:5]

# 修正聊天管理器，添加missing方法
class ChatManager:
    def __init__(self):
        self.data_file = "will_chat_data_pro.json"
        self.load_data()
    
    def load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.folders = data.get('folders', {'預設': []})
                self.chats = data.get('chats', {})
                self.settings = data.get('settings', {})
        except:
            self.folders = {'預設': [], '編程': [], '學習': [], '工作': [], '生活': [], '投資': []}
            self.chats = {}
            self.settings = {
                'theme': '明亮',
                'language': '繁體中文',
                'personality': '友善',
                'response_length': 3,
                'auto_save': True,
                'notifications': True
            }
    
    def save_data(self):
        data = {
            'folders': self.folders,
            'chats': self.chats,
            'settings': self.settings
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def create_new_chat(self, title="新對話", folder="預設"):
        chat_id = str(uuid.uuid4())
        self.chats[chat_id] = {
            'id': chat_id,
            'title': title,
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'tags': [],
            'importance': 'normal'
        }
        if folder not in self.folders:
            self.folders[folder] = []
        self.folders[folder].append(chat_id)
        self.save_data()
        return chat_id
    
    def update_chat(self, chat_id, messages, title=None):
        if chat_id in self.chats:
            self.chats[chat_id]['messages'] = messages
            self.chats[chat_id]['updated_at'] = datetime.now().isoformat()
            if title:
                self.chats[chat_id]['title'] = title
            if self.settings.get('auto_save', True):
                self.save_data()
    
    def delete_chat(self, chat_id):
        """刪除指定的聊天記錄"""
        if chat_id in self.chats:
            # 從所有資料夾中移除
            for folder_name, chat_list in self.folders.items():
                if chat_id in chat_list:
                    chat_list.remove(chat_id)
            
            # 刪除聊天記錄
            del self.chats[chat_id]
            self.save_data()
            return True
        return False
    
    def search_chats(self, query):
        """搜尋聊天記錄"""
        results = []
        for chat_id, chat in self.chats.items():
            if query.lower() in chat['title'].lower():
                results.append(chat_id)
            else:
                for message in chat['messages']:
                    if query.lower() in message['content'].lower():
                        results.append(chat_id)
                        break
        return results
    
    def update_settings(self, new_settings):
        """更新設定並保存"""
        self.settings.update(new_settings)
        self.save_data()

# 初始化管理器
if "stock_manager" not in st.session_state:
    st.session_state.stock_manager = StockDataManager()

if "news_manager" not in st.session_state:
    st.session_state.news_manager = NewsManager()

if "stock_matcher" not in st.session_state:
    st.session_state.stock_matcher = StockSymbolMatcher()

# 原有的聊天管理器和Gemini初始化代碼
@st.cache_resource
def init_gemini():
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"初始化Gemini失敗：{e}")
        return None

model = init_gemini()

# 初始化
if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "主頁"

if "watched_stocks" not in st.session_state:
    st.session_state.watched_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False  # 預設關閉自動刷新

if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = time.time()

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
        st.markdown(f"⏰ {datetime.now().strftime('%H:%M')}")
    
    # 頁面導航
    st.markdown("### 📋 功能選單")
    pages = {
        "🏠 智能主頁": "主頁",
        "💬 AI對話": "對話", 
        "📊 即時股市": "股市",
        "📰 AI新知": "新知",
        "🎯 智能推薦": "推薦",
        "⚙️ 進階設定": "設定"
    }
    
    for page_name, page_key in pages.items():
        if st.button(page_name, use_container_width=True, 
                     type="primary" if st.session_state.current_page == page_key else "secondary"):
            st.session_state.current_page = page_key
            st.rerun()
    
    # 快速搜尋
    st.markdown("### 🔍 快速搜尋")
    search_query = st.text_input("搜尋對話...", placeholder="輸入關鍵詞")
    if search_query:
        results = st.session_state.chat_manager.search_chats(search_query)
        if results:
            st.write(f"找到 {len(results)} 個結果")
            for result_id in results[:5]:
                chat = st.session_state.chat_manager.chats[result_id]
                if st.button(f"📄 {chat['title'][:15]}...", key=f"search_{result_id}"):
                    st.session_state.current_chat_id = result_id
                    st.session_state.current_page = "對話"
                    st.rerun()

# 自動刷新邏輯修正
def should_auto_refresh():
    """檢查是否需要自動刷新"""
    if not st.session_state.auto_refresh:
        return False
    
    current_time = time.time()
    if current_time - st.session_state.last_refresh_time > 60:  # 每60秒檢查一次
        st.session_state.last_refresh_time = current_time
        return True
    return False

# 主要內容區域
if st.session_state.current_page == "主頁":
    # 智能主頁
    st.markdown("""
    <div class="main-header">
        <h1>🎉 歡迎回來，Will！</h1>
        <p>你的專屬AI助手 Pro版 已準備就緒</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 自動刷新控制
    if should_auto_refresh():
        st.rerun()
    
    # 即時數據儀表板
    col1, col2, col3, col4 = st.columns(4)
    
    # 獲取市場指數
    market_data = st.session_state.stock_manager.get_market_indices()
    
    with col1:
        if '道瓊工業' in market_data:
            data = market_data['道瓊工業']
            color = "green" if data['change'] >= 0 else "red"
            st.markdown(f"""
            <div class="metric-card">
                <h4>📈 道瓊工業</h4>
                <h3>{data['price']}</h3>
                <p style="color: white;">{data['change']:+.2f} ({data['change_percent']:+.2f}%)</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if '標普500' in market_data:
            data = market_data['標普500']
            st.markdown(f"""
            <div class="metric-card">
                <h4>📊 標普500</h4>
                <h3>{data['price']}</h3>
                <p style="color: white;">{data['change']:+.2f} ({data['change_percent']:+.2f}%)</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if '納斯達克' in market_data:
            data = market_data['納斯達克']
            st.markdown(f"""
            <div class="metric-card">
                <h4>💻 納斯達克</h4>
                <h3>{data['price']}</h3>
                <p style="color: white;">{data['change']:+.2f} ({data['change_percent']:+.2f}%)</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        # 投資組合總覽
        portfolio_value = 0
        for stock in st.session_state.watched_stocks[:3]:
            stock_data = st.session_state.stock_manager.get_stock_data(stock)
            if stock_data:
                portfolio_value += stock_data['price']
        
        st.markdown(f"""
        <div class="metric-card">
            <h4>💰 關注組合</h4>
            <h3>${portfolio_value:.2f}</h3>
            <p style="color: white;">前3檔股票價格總和</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 智能推薦系統
    st.markdown("### 🎯 今日智能推薦")
    
    recommendation_engine = RecommendationEngine(st.session_state.chat_manager)
    chat_recommendations = recommendation_engine.get_chat_recommendations()
    stock_recommendations = recommendation_engine.get_stock_recommendations(st.session_state.watched_stocks)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💡 基於你的對話記錄")
        if chat_recommendations:
            for rec in chat_recommendations:
                st.markdown(f"- {rec}")
        else:
            st.info("開始對話來獲得個人化推薦！")
    
    with col2:
        st.markdown("#### 📈 推薦關注股票")
        if stock_recommendations:
            for stock in stock_recommendations:
                stock_data = st.session_state.stock_manager.get_stock_data(stock)
                if stock_data:
                    st.markdown(f"- **{stock}**: ${stock_data['price']} ({stock_data['change_percent']:+.2f}%)")
        else:
            st.info("添加關注股票來獲得智能推薦！")

elif st.session_state.current_page == "股市":
    # 即時股市頁面
    st.markdown("""
    <div class="main-header">
        <h1>📊 即時美股追蹤</h1>
        <p>真實數據 · 即時更新 · 智能分析</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 自動刷新控制
    if should_auto_refresh():
        st.rerun()
    
    # 市場指數
    st.markdown("### 📈 主要市場指數")
    market_data = st.session_state.stock_manager.get_market_indices()
    
    if market_data:
        cols = st.columns(len(market_data))
        for i, (name, data) in enumerate(market_data.items()):
            with cols[i]:
                color = "#28a745" if data['change'] >= 0 else "#dc3545"
                st.markdown(f"""
                <div class="stock-card">
                    <h4>{name}</h4>
                    <h2>${data['price']}</h2>
                    <p>{data['change']:+.2f} ({data['change_percent']:+.2f}%)</p>
                    <small>成交量: {data.get('volume', 'N/A')}</small>
                </div>
                """, unsafe_allow_html=True)
    
    # 個股管理 - 修正股票輸入功能
    st.markdown("### 💼 我的股票追蹤")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        # 智能股票輸入
        stock_input = st.text_input(
            "添加股票 (輸入公司名稱或代碼)", 
            placeholder="例如: Tesla, AAPL, 蘋果, 特斯拉",
            key="stock_input"
        )
        
        # 顯示匹配建議
        if stock_input:
            suggestions = st.session_state.stock_matcher.get_suggestions(stock_input)
            if suggestions:
                selected_stock = st.selectbox(
                    "選擇股票代碼：", 
                    suggestions,
                    key="stock_selector"
                )
                if selected_stock:
                    st.info(f"將添加：{selected_stock}")
    
    with col2:
        if st.button("➕ 添加股票"):
            if stock_input:
                suggestions = st.session_state.stock_matcher.get_suggestions(stock_input)
                if suggestions:
                    new_stock = suggestions[0]  # 取第一個建議
                    if new_stock.upper() not in st.session_state.watched_stocks:
                        # 驗證股票代碼
                        test_data = st.session_state.stock_manager.get_stock_data(new_stock.upper())
                        if test_data:
                            st.session_state.watched_stocks.append(new_stock.upper())
                            st.success(f"已添加 {new_stock.upper()}")
                            st.rerun()
                        else:
                            st.error("無效的股票代碼")
                    else:
                        st.warning("股票已在關注清單中")
                else:
                    st.error("找不到匹配的股票")
            else:
                st.error("請輸入股票名稱或代碼")