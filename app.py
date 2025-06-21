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

# 設定API Key
api_key = get_api_key()
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key

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

# 簡化的新聞管理

# 步驟1: 找到現有的NewsManager類（大約在第60-80行），完全替換為以下代碼：

class NewsManager:
    def __init__(self):
        self.cache = {}
        self.cache_expiry = 1800  # 30分鐘緩存
        
        # 預設RSS源
        self.default_feeds = {
            'TechCrunch AI': 'https://techcrunch.com/category/artificial-intelligence/feed/',
            'The Verge AI': 'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml',
            'VentureBeat AI': 'https://venturebeat.com/ai/feed/',
            'MIT Technology Review': 'https://www.technologyreview.com/feed/',
            'Ars Technica': 'https://feeds.arstechnica.com/arstechnica/index',
            'Wired': 'https://www.wired.com/feed/rss',
            'Engadget': 'https://www.engadget.com/rss.xml'
        }
    
    def get_user_feeds(self):
        """獲取用戶自訂的RSS源"""
        if 'user_rss_feeds' not in st.session_state:
            st.session_state.user_rss_feeds = self.default_feeds.copy()
        return st.session_state.user_rss_feeds
    
    def add_rss_feed(self, name, url):
        """添加新的RSS源"""
        if 'user_rss_feeds' not in st.session_state:
            st.session_state.user_rss_feeds = self.default_feeds.copy()
        st.session_state.user_rss_feeds[name] = url
        return True
    
    def remove_rss_feed(self, name):
        """移除RSS源"""
        if 'user_rss_feeds' in st.session_state and name in st.session_state.user_rss_feeds:
            del st.session_state.user_rss_feeds[name]
            return True
        return False
    
    def test_rss_feed(self, url):
        """測試RSS源是否有效"""
        try:
            feed = feedparser.parse(url)
            if feed.bozo == 0 and len(feed.entries) > 0:
                return True, f"成功！找到 {len(feed.entries)} 篇文章"
            else:
                return False, "RSS源無效或沒有內容"
        except Exception as e:
            return False, f"測試失敗：{str(e)}"
    
    def get_news_from_feeds(self, selected_feeds=None):
        """從選定的RSS源獲取新聞"""
        current_time = time.time()
        
        # 檢查緩存
        cache_key = 'custom_news' if selected_feeds else 'all_news'
        if cache_key in self.cache:
            if current_time - self.cache[cache_key]['timestamp'] < self.cache_expiry:
                return self.cache[cache_key]['data']
        
        user_feeds = self.get_user_feeds()
        feeds_to_use = selected_feeds if selected_feeds else user_feeds
        
        all_news = []
        
        for feed_name, feed_url in feeds_to_use.items():
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]:  # 每個來源取5篇
                    # 處理摘要
                    summary = ""
                    if hasattr(entry, 'summary'):
                        # 清理HTML標籤
                        soup = BeautifulSoup(entry.summary, 'html.parser')
                        summary = soup.get_text()[:300] + '...' if len(soup.get_text()) > 300 else soup.get_text()
                    elif hasattr(entry, 'description'):
                        soup = BeautifulSoup(entry.description, 'html.parser')
                        summary = soup.get_text()[:300] + '...' if len(soup.get_text()) > 300 else soup.get_text()
                    else:
                        summary = "暫無摘要"
                    
                    # 處理發布時間
                    published = "未知時間"
                    if hasattr(entry, 'published'):
                        try:
                            pub_time = time.mktime(entry.published_parsed)
                            taiwan_time = datetime.fromtimestamp(pub_time, TAIWAN_TZ)
                            published = taiwan_time.strftime('%m-%d %H:%M')
                        except:
                            published = entry.published
                    
                    all_news.append({
                        'title': entry.title,
                        'summary': summary,
                        'link': entry.link,
                        'published': published,
                        'source': feed_name,
                        'feed_url': feed_url
                    })
                    
            except Exception as e:
                continue
        
        # 按發布時間排序
        all_news.sort(key=lambda x: x['published'], reverse=True)
        
        # 更新緩存
        self.cache[cache_key] = {
            'data': all_news[:20],  # 取前20篇
            'timestamp': current_time
        }
        
        return all_news[:20]
    
    def search_news(self, query, max_results=10):
        """搜尋特定主題新聞"""
        try:
            all_news = self.get_news_from_feeds()
            filtered_news = [
                news for news in all_news 
                if query.lower() in news['title'].lower() or query.lower() in news['summary'].lower()
            ]
            return filtered_news[:max_results]
        except:
            return []
    
    def get_fallback_news(self):
        """備用新聞數據"""
        return [
            {
                'title': 'Google Gemini 2.5 Flash 性能突破',
                'summary': 'Google最新發布的Gemini 2.5 Flash在多項AI基準測試中表現優異，特別在程式碼生成和數學推理方面有顯著提升。',
                'link': '#',
                'published': '2小時前',
                'source': '備用新聞'
            },
            {
                'title': 'OpenAI GPT-5 開發進展曝光',
                'summary': '據內部消息，OpenAI正在加速GPT-5的開發，預計將在推理能力和多模態處理方面帶來革命性改進。',
                'link': '#',
                'published': '4小時前',
                'source': '備用新聞'
            },
            {
                'title': 'AI在醫療診斷領域的新突破',
                'summary': '最新研究顯示，AI系統在某些疾病診斷方面已經超越了人類醫生的準確率，為醫療行業帶來革命性變化。',
                'link': '#',
                'published': '6小時前',
                'source': '備用新聞'
            }
        ]

# 步驟2: 找到新知頁面的代碼（搜索 elif st.session_state.current_page == "新知":），完全替換為以下代碼：

elif st.session_state.current_page == "新知":
    st.title("📰 AI新知與科技資訊")
    
    # 頁籤系統
    tab1, tab2 = st.tabs(["📰 瀏覽新聞", "⚙️ 管理RSS源"])
    
    with tab1:
        # 新聞瀏覽頁面
        st.markdown("### 🔍 新聞控制台")
        
        # 控制面板
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 刷新新聞", key="refresh_news"):
                st.session_state.news_manager.cache.clear()
                st.success("緩存已清除，正在載入最新新聞...")
                st.rerun()
        
        with col2:
            news_count = st.selectbox("顯示數量", [5, 10, 15, 20], index=1, key="news_count")
        
        with col3:
            # RSS源選擇
            available_feeds = st.session_state.news_manager.get_user_feeds()
            selected_feeds_names = st.multiselect(
                "選擇新聞源",
                list(available_feeds.keys()),
                default=list(available_feeds.keys())[:3],  # 預設選擇前3個
                key="selected_feeds"
            )
        
        with col4:
            st.write(f"**更新時間:** {get_taiwan_time().strftime('%H:%M')}")
        
        # 新聞搜尋
        search_term = st.text_input("🔍 搜尋新聞", placeholder="輸入關鍵字搜尋...", key="news_search")
        
        # 載入新聞數據
        with st.spinner("📰 正在載入新聞..."):
            try:
                if search_term:
                    # 搜尋模式
                    news_list = st.session_state.news_manager.search_news(search_term)
                    if news_list:
                        st.success(f"🔍 找到 {len(news_list)} 篇相關新聞")
                    else:
                        st.warning("沒有找到相關新聞")
                        news_list = []
                else:
                    # 一般瀏覽模式
                    if selected_feeds_names:
                        selected_feeds = {name: available_feeds[name] for name in selected_feeds_names}
                        news_list = st.session_state.news_manager.get_news_from_feeds(selected_feeds)
                    else:
                        news_list = st.session_state.news_manager.get_news_from_feeds()
                
                # 如果沒有新聞，使用備用新聞
                if not news_list:
                    st.warning("無法從RSS源載入新聞，顯示備用新聞")
                    news_list = st.session_state.news_manager.get_fallback_news()
                    
            except Exception as e:
                st.error(f"載入新聞時發生錯誤：{e}")
                news_list = st.session_state.news_manager.get_fallback_news()
        
        # 顯示新聞
        if news_list:
            st.markdown(f"### 📊 共 {len(news_list[:news_count])} 則新聞")
            
            for i, news in enumerate(news_list[:news_count]):
                # 使用expander來組織新聞內容
                with st.expander(f"📰 {news['title']}", expanded=False):
                    st.write(f"**摘要：** {news['summary']}")
                    st.write(f"**發布時間：** {news['published']}")
                    st.write(f"**來源：** {news['source']}")
                    
                    # 操作按鈕
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if news['link'] != '#':
                            st.markdown(f"[📖 閱讀原文]({news['link']})")
                        else:
                            st.info("範例新聞，無原文連結")
                    
                    with col2:
                        if st.button("🤖 AI解讀", key=f"analyze_news_{i}"):
                            if model:
                                with st.spinner("🤖 AI正在分析新聞內容..."):
                                    try:
                                        analysis_prompt = f"""
                                        請分析以下新聞文章：
                                        
                                        標題：{news['title']}
                                        摘要：{news['summary']}
                                        
                                        請提供：
                                        1. 🎯 核心重點：這篇新聞的主要內容是什麼？
                                        2. 📈 產業影響：對相關產業可能產生什麼影響？
                                        3. 🔮 趨勢預測：這反映了什麼技術或市場趨勢？
                                        4. 💡 實際意義：對一般用戶或企業有什麼實際意義？
                                        
                                        請用繁體中文回答，保持簡潔且具有洞察力。
                                        """
                                        
                                        response = model.generate_content(analysis_prompt)
                                        st.markdown("---")
                                        st.markdown("**🤖 AI深度分析：**")
                                        st.markdown(response.text)
                                        
                                    except Exception as e:
                                        st.error(f"AI分析失敗：{e}")
                                        st.info("請稍後再試或檢查API設定")
                            else:
                                st.error("AI模型未初始化，請檢查API設定")
                    
                    with col3:
                        if st.button("📋 複製內容", key=f"copy_news_{i}"):
                            copy_text = f"""標題：{news['title']}

摘要：{news['summary']}

來源：{news['source']}
時間：{news['published']}
連結：{news['link']}"""
                            st.text_area("複製以下內容：", copy_text, height=150, key=f"copy_area_{i}")
                
                # 分隔線
                if i < len(news_list[:news_count]) - 1:
                    st.divider()
        else:
            st.error("無法載入新聞內容，請檢查RSS源設定或網路連線")
    
    with tab2:
        # RSS源管理頁面
        st.markdown("### ⚙️ RSS新聞源管理")
        
        # 添加新RSS源
        st.markdown("#### ➕ 添加新的RSS源")
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            new_feed_name = st.text_input("RSS源名稱", placeholder="例如: BBC Technology", key="new_feed_name")
        
        with col2:
            new_feed_url = st.text_input("RSS URL", placeholder="例如: https://example.com/rss", key="new_feed_url")
        
        with col3:
            st.write("")  # 空白用於對齊
            st.write("")  # 空白用於對齊
            if st.button("🧪 測試", key="test_feed"):
                if new_feed_url:
                    with st.spinner("測試RSS源..."):
                        is_valid, message = st.session_state.news_manager.test_rss_feed(new_feed_url)
                        if is_valid:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.warning("請輸入RSS URL")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("➕ 添加RSS源", key="add_feed", type="primary"):
                if new_feed_name and new_feed_url:
                    if st.session_state.news_manager.add_rss_feed(new_feed_name, new_feed_url):
                        st.success(f"✅ 已添加 {new_feed_name}")
                        st.rerun()
                    else:
                        st.error("添加失敗")
                else:
                    st.warning("請填寫RSS源名稱和URL")
        
        # 管理現有RSS源
        st.markdown("#### 📋 管理現有RSS源")
        
        current_feeds = st.session_state.news_manager.get_user_feeds()
        
        if current_feeds:
            for feed_name, feed_url in current_feeds.items():
                col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
                
                with col1:
                    st.write(f"**{feed_name}**")
                
                with col2:
                    st.write(f"`{feed_url[:50]}...`" if len(feed_url) > 50 else f"`{feed_url}`")
                
                with col3:
                    if st.button("🧪", key=f"test_{feed_name}", help="測試此RSS源"):
                        with st.spinner("測試中..."):
                            is_valid, message = st.session_state.news_manager.test_rss_feed(feed_url)
                            if is_valid:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
                
                with col4:
                    if st.button("🗑️", key=f"remove_{feed_name}", help="移除此RSS源"):
                        if st.session_state.news_manager.remove_rss_feed(feed_name):
                            st.success(f"已移除 {feed_name}")
                            st.rerun()
        else:
            st.info("目前沒有RSS源")
        
        # 推薦RSS源
        st.markdown("#### 🌟 推薦RSS源")
        
        recommended_feeds = {
            'Reuters Technology': 'https://feeds.reuters.com/reuters/technologyNews',
            'BBC Technology': 'https://feeds.bbci.co.uk/news/technology/rss.xml',
            'The Next Web': 'https://thenextweb.com/feed/',
            'Digital Trends': 'https://www.digitaltrends.com/feed/',
            'Mashable Tech': 'https://mashable.com/feeds/rss/tech',
            'Gizmodo': 'https://gizmodo.com/rss'
        }
        
        st.write("點擊下面的RSS源可以快速添加：")
        
        cols = st.columns(2)
        for i, (name, url) in enumerate(recommended_feeds.items()):
            with cols[i % 2]:
                if st.button(f"➕ {name}", key=f"rec_{i}", use_container_width=True):
                    if st.session_state.news_manager.add_rss_feed(name, url):
                        st.success(f"✅ 已添加 {name}")
                        st.rerun()
        
        # 使用說明
        with st.expander("📖 使用說明"):
            st.markdown("""
            **如何使用RSS源管理：**
            
            1. **添加RSS源**：輸入名稱和RSS URL，點擊"測試"確認有效後添加
            2. **測試RSS源**：點擊🧪按鈕測試RSS源是否正常工作
            3. **移除RSS源**：點擊🗑️按鈕移除不需要的RSS源
            4. **選擇新聞源**：在"瀏覽新聞"頁籤中選擇要顯示的新聞源
            
            **如何找到RSS URL：**
            - 大多數新聞網站都有RSS訂閱連結
            - 通常在網站底部或"訂閱"頁面
            - 常見格式：/rss, /feed, /rss.xml, /feed.xml
            
            **推薦的科技新聞RSS源已提供，點擊即可快速添加！**
            """)

# 步驟1: 找到現有的NewsManager類（大約在第60-80行），完全替換為以下代碼：

class NewsManager:
    def __init__(self):
        self.cache = {}
        self.cache_expiry = 1800  # 30分鐘緩存
        
        # 預設RSS源
        self.default_feeds = {
            'TechCrunch AI': 'https://techcrunch.com/category/artificial-intelligence/feed/',
            'The Verge AI': 'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml',
            'VentureBeat AI': 'https://venturebeat.com/ai/feed/',
            'MIT Technology Review': 'https://www.technologyreview.com/feed/',
            'Ars Technica': 'https://feeds.arstechnica.com/arstechnica/index',
            'Wired': 'https://www.wired.com/feed/rss',
            'Engadget': 'https://www.engadget.com/rss.xml'
        }
    
    def get_user_feeds(self):
        """獲取用戶自訂的RSS源"""
        if 'user_rss_feeds' not in st.session_state:
            st.session_state.user_rss_feeds = self.default_feeds.copy()
        return st.session_state.user_rss_feeds
    
    def add_rss_feed(self, name, url):
        """添加新的RSS源"""
        if 'user_rss_feeds' not in st.session_state:
            st.session_state.user_rss_feeds = self.default_feeds.copy()
        st.session_state.user_rss_feeds[name] = url
        return True
    
    def remove_rss_feed(self, name):
        """移除RSS源"""
        if 'user_rss_feeds' in st.session_state and name in st.session_state.user_rss_feeds:
            del st.session_state.user_rss_feeds[name]
            return True
        return False
    
    def test_rss_feed(self, url):
        """測試RSS源是否有效"""
        try:
            feed = feedparser.parse(url)
            if feed.bozo == 0 and len(feed.entries) > 0:
                return True, f"成功！找到 {len(feed.entries)} 篇文章"
            else:
                return False, "RSS源無效或沒有內容"
        except Exception as e:
            return False, f"測試失敗：{str(e)}"
    
    def get_news_from_feeds(self, selected_feeds=None):
        """從選定的RSS源獲取新聞"""
        current_time = time.time()
        
        # 檢查緩存
        cache_key = 'custom_news' if selected_feeds else 'all_news'
        if cache_key in self.cache:
            if current_time - self.cache[cache_key]['timestamp'] < self.cache_expiry:
                return self.cache[cache_key]['data']
        
        user_feeds = self.get_user_feeds()
        feeds_to_use = selected_feeds if selected_feeds else user_feeds
        
        all_news = []
        
        for feed_name, feed_url in feeds_to_use.items():
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]:  # 每個來源取5篇
                    # 處理摘要
                    summary = ""
                    if hasattr(entry, 'summary'):
                        # 清理HTML標籤
                        soup = BeautifulSoup(entry.summary, 'html.parser')
                        summary = soup.get_text()[:300] + '...' if len(soup.get_text()) > 300 else soup.get_text()
                    elif hasattr(entry, 'description'):
                        soup = BeautifulSoup(entry.description, 'html.parser')
                        summary = soup.get_text()[:300] + '...' if len(soup.get_text()) > 300 else soup.get_text()
                    else:
                        summary = "暫無摘要"
                    
                    # 處理發布時間
                    published = "未知時間"
                    if hasattr(entry, 'published'):
                        try:
                            pub_time = time.mktime(entry.published_parsed)
                            taiwan_time = datetime.fromtimestamp(pub_time, TAIWAN_TZ)
                            published = taiwan_time.strftime('%m-%d %H:%M')
                        except:
                            published = entry.published
                    
                    all_news.append({
                        'title': entry.title,
                        'summary': summary,
                        'link': entry.link,
                        'published': published,
                        'source': feed_name,
                        'feed_url': feed_url
                    })
                    
            except Exception as e:
                continue
        
        # 按發布時間排序
        all_news.sort(key=lambda x: x['published'], reverse=True)
        
        # 更新緩存
        self.cache[cache_key] = {
            'data': all_news[:20],  # 取前20篇
            'timestamp': current_time
        }
        
        return all_news[:20]
    
    def search_news(self, query, max_results=10):
        """搜尋特定主題新聞"""
        try:
            all_news = self.get_news_from_feeds()
            filtered_news = [
                news for news in all_news 
                if query.lower() in news['title'].lower() or query.lower() in news['summary'].lower()
            ]
            return filtered_news[:max_results]
        except:
            return []
    
    def get_fallback_news(self):
        """備用新聞數據"""
        return [
            {
                'title': 'Google Gemini 2.5 Flash 性能突破',
                'summary': 'Google最新發布的Gemini 2.5 Flash在多項AI基準測試中表現優異，特別在程式碼生成和數學推理方面有顯著提升。',
                'link': '#',
                'published': '2小時前',
                'source': '備用新聞'
            },
            {
                'title': 'OpenAI GPT-5 開發進展曝光',
                'summary': '據內部消息，OpenAI正在加速GPT-5的開發，預計將在推理能力和多模態處理方面帶來革命性改進。',
                'link': '#',
                'published': '4小時前',
                'source': '備用新聞'
            },
            {
                'title': 'AI在醫療診斷領域的新突破',
                'summary': '最新研究顯示，AI系統在某些疾病診斷方面已經超越了人類醫生的準確率，為醫療行業帶來革命性變化。',
                'link': '#',
                'published': '6小時前',
                'source': '備用新聞'
            }
        ]

# 步驟2: 找到新知頁面的代碼（搜索 elif st.session_state.current_page == "新知":），完全替換為以下代碼：

elif st.session_state.current_page == "新知":
    st.title("📰 AI新知與科技資訊")
    
    # 頁籤系統
    tab1, tab2 = st.tabs(["📰 瀏覽新聞", "⚙️ 管理RSS源"])
    
    with tab1:
        # 新聞瀏覽頁面
        st.markdown("### 🔍 新聞控制台")
        
        # 控制面板
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 刷新新聞", key="refresh_news"):
                st.session_state.news_manager.cache.clear()
                st.success("緩存已清除，正在載入最新新聞...")
                st.rerun()
        
        with col2:
            news_count = st.selectbox("顯示數量", [5, 10, 15, 20], index=1, key="news_count")
        
        with col3:
            # RSS源選擇
            available_feeds = st.session_state.news_manager.get_user_feeds()
            selected_feeds_names = st.multiselect(
                "選擇新聞源",
                list(available_feeds.keys()),
                default=list(available_feeds.keys())[:3],  # 預設選擇前3個
                key="selected_feeds"
            )
        
        with col4:
            st.write(f"**更新時間:** {get_taiwan_time().strftime('%H:%M')}")
        
        # 新聞搜尋
        search_term = st.text_input("🔍 搜尋新聞", placeholder="輸入關鍵字搜尋...", key="news_search")
        
        # 載入新聞數據
        with st.spinner("📰 正在載入新聞..."):
            try:
                if search_term:
                    # 搜尋模式
                    news_list = st.session_state.news_manager.search_news(search_term)
                    if news_list:
                        st.success(f"🔍 找到 {len(news_list)} 篇相關新聞")
                    else:
                        st.warning("沒有找到相關新聞")
                        news_list = []
                else:
                    # 一般瀏覽模式
                    if selected_feeds_names:
                        selected_feeds = {name: available_feeds[name] for name in selected_feeds_names}
                        news_list = st.session_state.news_manager.get_news_from_feeds(selected_feeds)
                    else:
                        news_list = st.session_state.news_manager.get_news_from_feeds()
                
                # 如果沒有新聞，使用備用新聞
                if not news_list:
                    st.warning("無法從RSS源載入新聞，顯示備用新聞")
                    news_list = st.session_state.news_manager.get_fallback_news()
                    
            except Exception as e:
                st.error(f"載入新聞時發生錯誤：{e}")
                news_list = st.session_state.news_manager.get_fallback_news()
        
        # 顯示新聞
        if news_list:
            st.markdown(f"### 📊 共 {len(news_list[:news_count])} 則新聞")
            
            for i, news in enumerate(news_list[:news_count]):
                # 使用expander來組織新聞內容
                with st.expander(f"📰 {news['title']}", expanded=False):
                    st.write(f"**摘要：** {news['summary']}")
                    st.write(f"**發布時間：** {news['published']}")
                    st.write(f"**來源：** {news['source']}")
                    
                    # 操作按鈕
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if news['link'] != '#':
                            st.markdown(f"[📖 閱讀原文]({news['link']})")
                        else:
                            st.info("範例新聞，無原文連結")
                    
                    with col2:
                        if st.button("🤖 AI解讀", key=f"analyze_news_{i}"):
                            if model:
                                with st.spinner("🤖 AI正在分析新聞內容..."):
                                    try:
                                        analysis_prompt = f"""
                                        請分析以下新聞文章：
                                        
                                        標題：{news['title']}
                                        摘要：{news['summary']}
                                        
                                        請提供：
                                        1. 🎯 核心重點：這篇新聞的主要內容是什麼？
                                        2. 📈 產業影響：對相關產業可能產生什麼影響？
                                        3. 🔮 趨勢預測：這反映了什麼技術或市場趨勢？
                                        4. 💡 實際意義：對一般用戶或企業有什麼實際意義？
                                        
                                        請用繁體中文回答，保持簡潔且具有洞察力。
                                        """
                                        
                                        response = model.generate_content(analysis_prompt)
                                        st.markdown("---")
                                        st.markdown("**🤖 AI深度分析：**")
                                        st.markdown(response.text)
                                        
                                    except Exception as e:
                                        st.error(f"AI分析失敗：{e}")
                                        st.info("請稍後再試或檢查API設定")
                            else:
                                st.error("AI模型未初始化，請檢查API設定")
                    
                    with col3:
                        if st.button("📋 複製內容", key=f"copy_news_{i}"):
                            copy_text = f"""標題：{news['title']}

摘要：{news['summary']}

來源：{news['source']}
時間：{news['published']}
連結：{news['link']}"""
                            st.text_area("複製以下內容：", copy_text, height=150, key=f"copy_area_{i}")
                
                # 分隔線
                if i < len(news_list[:news_count]) - 1:
                    st.divider()
        else:
            st.error("無法載入新聞內容，請檢查RSS源設定或網路連線")
    
    with tab2:
        # RSS源管理頁面
        st.markdown("### ⚙️ RSS新聞源管理")
        
        # 添加新RSS源
        st.markdown("#### ➕ 添加新的RSS源")
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            new_feed_name = st.text_input("RSS源名稱", placeholder="例如: BBC Technology", key="new_feed_name")
        
        with col2:
            new_feed_url = st.text_input("RSS URL", placeholder="例如: https://example.com/rss", key="new_feed_url")
        
        with col3:
            st.write("")  # 空白用於對齊
            st.write("")  # 空白用於對齊
            if st.button("🧪 測試", key="test_feed"):
                if new_feed_url:
                    with st.spinner("測試RSS源..."):
                        is_valid, message = st.session_state.news_manager.test_rss_feed(new_feed_url)
                        if is_valid:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.warning("請輸入RSS URL")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("➕ 添加RSS源", key="add_feed", type="primary"):
                if new_feed_name and new_feed_url:
                    if st.session_state.news_manager.add_rss_feed(new_feed_name, new_feed_url):
                        st.success(f"✅ 已添加 {new_feed_name}")
                        st.rerun()
                    else:
                        st.error("添加失敗")
                else:
                    st.warning("請填寫RSS源名稱和URL")
        
        # 管理現有RSS源
        st.markdown("#### 📋 管理現有RSS源")
        
        current_feeds = st.session_state.news_manager.get_user_feeds()
        
        if current_feeds:
            for feed_name, feed_url in current_feeds.items():
                col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
                
                with col1:
                    st.write(f"**{feed_name}**")
                
                with col2:
                    st.write(f"`{feed_url[:50]}...`" if len(feed_url) > 50 else f"`{feed_url}`")
                
                with col3:
                    if st.button("🧪", key=f"test_{feed_name}", help="測試此RSS源"):
                        with st.spinner("測試中..."):
                            is_valid, message = st.session_state.news_manager.test_rss_feed(feed_url)
                            if is_valid:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
                
                with col4:
                    if st.button("🗑️", key=f"remove_{feed_name}", help="移除此RSS源"):
                        if st.session_state.news_manager.remove_rss_feed(feed_name):
                            st.success(f"已移除 {feed_name}")
                            st.rerun()
        else:
            st.info("目前沒有RSS源")
        
        # 推薦RSS源
        st.markdown("#### 🌟 推薦RSS源")
        
        recommended_feeds = {
            'Reuters Technology': 'https://feeds.reuters.com/reuters/technologyNews',
            'BBC Technology': 'https://feeds.bbci.co.uk/news/technology/rss.xml',
            'The Next Web': 'https://thenextweb.com/feed/',
            'Digital Trends': 'https://www.digitaltrends.com/feed/',
            'Mashable Tech': 'https://mashable.com/feeds/rss/tech',
            'Gizmodo': 'https://gizmodo.com/rss'
        }
        
        st.write("點擊下面的RSS源可以快速添加：")
        
        cols = st.columns(2)
        for i, (name, url) in enumerate(recommended_feeds.items()):
            with cols[i % 2]:
                if st.button(f"➕ {name}", key=f"rec_{i}", use_container_width=True):
                    if st.session_state.news_manager.add_rss_feed(name, url):
                        st.success(f"✅ 已添加 {name}")
                        st.rerun()
        
        # 使用說明
        with st.expander("📖 使用說明"):
            st.markdown("""
            **如何使用RSS源管理：**
            
            1. **添加RSS源**：輸入名稱和RSS URL，點擊"測試"確認有效後添加
            2. **測試RSS源**：點擊🧪按鈕測試RSS源是否正常工作
            3. **移除RSS源**：點擊🗑️按鈕移除不需要的RSS源
            4. **選擇新聞源**：在"瀏覽新聞"頁籤中選擇要顯示的新聞源
            
            **如何找到RSS URL：**
            - 大多數新聞網站都有RSS訂閱連結
            - 通常在網站底部或"訂閱"頁面
            - 常見格式：/rss, /feed, /rss.xml, /feed.xml
            
            **推薦的科技新聞RSS源已提供，點擊即可快速添加！**
            """)
# 簡化的聊天管理
class ChatManager:
    def __init__(self):
        self.chats = {}
        self.settings = {
            'personality': '友善',
            'response_length': 3,
            'auto_save': True
        }

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
        st.success("✅ AI模型已就緒，可以開始對話")
        
        # 簡單的對話介面
        user_input = st.text_area("輸入你的問題：", height=100, key="chat_input")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💬 發送", key="send_msg", type="primary"):
                if user_input.strip():
                    try:
                        with st.spinner("🤔 AI正在思考..."):
                            prompt = f"請用繁體中文回答以下問題：{user_input}"
                            response = model.generate_content(prompt)
                            
                            st.markdown("---")
                            st.markdown("**👤 你的問題：**")
                            st.write(user_input)
                            
                            st.markdown("**🤖 AI回應：**")
                            st.write(response.text)
                            
                    except Exception as e:
                        st.error(f"AI回應錯誤：{str(e)}")
                else:
                    st.warning("請輸入問題後再發送")
        
        with col2:
            if st.button("🔄 清除對話", key="clear_chat"):
                st.rerun()

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
    
    # 載入新聞
    news_list = st.session_state.news_manager.get_fallback_news()
    
    if news_list:
        st.markdown("### 🔥 最新AI新聞")
        
        for i, news in enumerate(news_list):
            with st.expander(f"📰 {news['title']}", expanded=(i == 0)):
                st.write(f"**摘要：** {news['summary']}")
                st.write(f"**來源：** {news['source']}")
                st.write(f"**時間：** {news['published']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if news['link'] != '#':
                        st.markdown(f"[📖 閱讀原文]({news['link']})")
                    else:
                        st.info("範例新聞，無原文連結")
                
                with col2:
                    if st.button("🤖 AI解讀", key=f"analyze_{i}"):
                        if model:
                            try:
                                analysis_prompt = f"""請分析這則新聞：
                                標題：{news['title']}
                                摘要：{news['summary']}
                                請用繁體中文簡要說明重點。"""
                                
                                response = model.generate_content(analysis_prompt)
                                st.markdown("**🤖 AI分析：**")
                                st.write(response.text)
                            except Exception as e:
                                st.error(f"分析失敗：{e}")
                        else:
                            st.error("AI模型未初始化")

elif st.session_state.current_page == "推薦":
    st.title("🎯 智能推薦系統")
    
    # 學習推薦
    st.markdown("### 📚 學習建議")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔥 熱門主題")
        topics = [
            "🐍 Python程式設計",
            "🤖 機器學習基礎",
            "📊 數據分析技能",
            "🌐 網頁開發入門",
            "☁️ 雲端服務應用"
        ]
        for topic in topics:
            st.write(f"• {topic}")
    
    with col2:
        st.markdown("#### 💡 個人化建議")
        chat_count = len(st.session_state.chat_manager.chats)
        stock_count = len(st.session_state.watched_stocks)
        
        recommendations = [
            f"📈 你關注了 {stock_count} 檔股票",
            f"💬 已進行 {chat_count} 次AI對話",
            "🚀 建議多嘗試不同功能",
            "📊 定期檢視投資組合"
        ]
        
        for rec in recommendations:
            st.write(f"• {rec}")
    
    # 投資建議
    st.markdown("### 💰 投資建議")
    if st.session_state.watched_stocks:
        st.success(f"你目前關注 {len(st.session_state.watched_stocks)} 檔股票")
        st.info("建議定期檢視投資組合，注意風險分散")
    else:
        st.info("開始添加關注股票來獲得投資建議")

elif st.session_state.current_page == "設定":
    st.title("⚙️ 進階設定")
    
    # API狀態檢查
    st.markdown("### 🔑 API設定狀態")
    if model:
        st.success("✅ Gemini API 連接正常")
    else:
        st.error("❌ Gemini API 未連接")
        st.info("請檢查Streamlit Cloud的Secrets設定中是否正確設定了 GOOGLE_API_KEY")
    
    # 基本設定
    st.markdown("### 🎨 基本設定")
    
    col1, col2 = st.columns(2)
    with col1:
        personality = st.selectbox(
            "AI回答風格",
            ["友善", "專業", "幽默", "簡潔"],
            key="ai_personality"
        )
    
    with col2:
        auto_refresh = st.checkbox(
            "自動刷新數據",
            value=True,
            key="auto_refresh_setting"
        )
    
    if st.button("💾 保存設定", key="save_settings"):
        st.success("設定已保存！")
    
    # 系統資訊
    st.markdown("### 📊 系統資訊")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("對話總數", len(st.session_state.chat_manager.chats))
    with col2:
        st.metric("關注股票", len(st.session_state.watched_stocks))
    with col3:
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
    st.caption("台灣時間")
