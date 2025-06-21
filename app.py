# ========== 修正1: 時區設定 (在文件開頭添加) ==========
import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import time
from datetime import datetime, timedelta
import pytz  # 添加時區支援
import uuid
import pandas as pd
import yfinance as yf
import requests
import feedparser
from bs4 import BeautifulSoup
from typing import Dict, List

# 設定台灣時區
TAIWAN_TZ = pytz.timezone('Asia/Taipei')

def get_taiwan_time():
    """獲取台灣時間"""
    return datetime.now(TAIWAN_TZ)

# ========== 修正2: 側邊欄頁面導航 (替換原有的側邊欄代碼) ==========
with st.sidebar:
    st.markdown("""
    <div class="main-header" style="margin-bottom: 1rem;">
        <h2>🚀 Will的AI小幫手</h2>
        <span class="pro-badge">PRO</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 即時狀態指示器 - 使用台灣時間
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<span class="real-time-badge">🔴 即時數據</span>', unsafe_allow_html=True)
    with col2:
        taiwan_time = get_taiwan_time()
        st.markdown(f"⏰ {taiwan_time.strftime('%H:%M')}")
    
    # 頁面導航 - 使用selectbox避免按鈕重渲染問題
    st.markdown("### 📋 功能選單")
    
    page_options = {
        "🏠 智能主頁": "主頁",
        "💬 AI對話": "對話", 
        "📊 即時股市": "股市",
        "📰 AI新知": "新知",
        "🎯 智能推薦": "推薦",
        "⚙️ 進階設定": "設定"
    }
    
    # 使用selectbox代替按鈕
    current_display = "🏠 智能主頁"
    for display, page in page_options.items():
        if st.session_state.current_page == page:
            current_display = display
            break
    
    selected = st.selectbox(
        "選擇功能",
        list(page_options.keys()),
        index=list(page_options.keys()).index(current_display),
        key="page_nav"
    )
    
    if page_options[selected] != st.session_state.current_page:
        st.session_state.current_page = page_options[selected]
        st.rerun()

# ========== 修正3: AI對話頁面 (完整替換) ==========
elif st.session_state.current_page == "對話":
    st.markdown("## 💬 AI智能對話")
    
    # 創建對話容器
    chat_container = st.container()
    
    # 如果沒有當前對話，創建一個
    if st.session_state.current_chat_id is None:
        st.markdown("### 🚀 開始新對話")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            chat_title = st.text_input("對話標題", value="新對話", key="new_chat_title")
        with col2:
            if st.button("創建對話", key="create_chat"):
                try:
                    new_chat_id = st.session_state.chat_manager.create_new_chat(chat_title)
                    st.session_state.current_chat_id = new_chat_id
                    st.success("對話已創建！")
                    st.rerun()
                except Exception as e:
                    st.error(f"創建對話失敗：{e}")
        
        # 快速開始選項
        st.markdown("#### 💡 快速開始")
        quick_topics = [
            "請介紹一下最新的AI技術趨勢",
            "幫我分析目前的股市情況", 
            "我想學習Python程式設計",
            "給我一些投資理財的建議"
        ]
        
        for i, topic in enumerate(quick_topics):
            if st.button(f"💭 {topic}", key=f"quick_{i}"):
                try:
                    new_chat_id = st.session_state.chat_manager.create_new_chat(f"快速對話 {i+1}")
                    st.session_state.current_chat_id = new_chat_id
                    # 添加初始訊息
                    chat = st.session_state.chat_manager.chats[new_chat_id]
                    chat['messages'].append({"role": "user", "content": topic})
                    st.session_state.chat_manager.update_chat(new_chat_id, chat['messages'])
                    st.rerun()
                except Exception as e:
                    st.error(f"創建對話失敗：{e}")
    
    else:
        # 顯示現有對話
        try:
            current_chat = st.session_state.chat_manager.chats[st.session_state.current_chat_id]
            
            # 對話控制
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**當前對話:** {current_chat['title']}")
            with col2:
                if st.button("🔄 重新開始", key="restart_chat"):
                    current_chat['messages'] = []
                    st.session_state.chat_manager.update_chat(st.session_state.current_chat_id, [])
                    st.rerun()
            with col3:
                if st.button("➕ 新對話", key="new_chat"):
                    st.session_state.current_chat_id = None
                    st.rerun()
            
            # 顯示對話歷史
            with chat_container:
                if current_chat['messages']:
                    for message in current_chat['messages']:
                        if message["role"] == "user":
                            with st.chat_message("user"):
                                st.write(message["content"])
                        else:
                            with st.chat_message("assistant"):
                                st.write(message["content"])
                else:
                    st.info("👋 開始新的對話吧！在下方輸入你的問題。")
            
            # 對話輸入
            if prompt := st.chat_input("輸入你的問題...", key="chat_input"):
                # 添加用戶訊息
                current_chat['messages'].append({"role": "user", "content": prompt})
                
                # 顯示用戶訊息
                with st.chat_message("user"):
                    st.write(prompt)
                
                # AI回應
                with st.chat_message("assistant"):
                    if model:
                        try:
                            with st.spinner("🤔 AI正在思考..."):
                                # 簡化的提示
                                system_prompt = "你是一個專業的AI助手，請用繁體中文回答問題。"
                                full_prompt = f"{system_prompt}\n\n用戶問題：{prompt}"
                                
                                response = model.generate_content(full_prompt)
                                response_text = response.text
                                
                                st.write(response_text)
                                current_chat['messages'].append({"role": "assistant", "content": response_text})
                                
                                # 保存對話
                                st.session_state.chat_manager.update_chat(st.session_state.current_chat_id, current_chat['messages'])
                                
                        except Exception as e:
                            st.error(f"AI回應錯誤：{e}")
                    else:
                        st.error("AI模型未初始化，請檢查API設定")
        
        except KeyError:
            st.error("對話不存在，請創建新對話")
            st.session_state.current_chat_id = None
            st.rerun()
        except Exception as e:
            st.error(f"對話頁面錯誤：{e}")

# ========== 修正4: AI新知頁面 (完整替換) ==========
elif st.session_state.current_page == "新知":
    st.markdown("## 📰 AI新知與科技資訊")
    
    # 控制面板
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 刷新新聞", key="refresh_news"):
            st.session_state.news_manager.cache.clear()
            st.success("已清除緩存，正在載入最新新聞...")
            st.rerun()
    
    with col2:
        news_count = st.selectbox("顯示數量", [5, 10, 15, 20], index=1, key="news_count")
    
    with col3:
        st.write(f"**更新時間:** {get_taiwan_time().strftime('%H:%M')}")
    
    # 新聞搜尋
    search_term = st.text_input("🔍 搜尋新聞", placeholder="輸入關鍵字搜尋...", key="news_search")
    
    # 載入新聞
    try:
        with st.spinner("📰 正在載入新聞..."):
            if search_term:
                news_list = st.session_state.news_manager.search_news(search_term)
                if not news_list:
                    st.warning("沒有找到相關新聞，顯示預設新聞")
                    news_list = st.session_state.news_manager.get_fallback_news()
            else:
                news_list = st.session_state.news_manager.get_ai_news()
                if not news_list:
                    news_list = st.session_state.news_manager.get_fallback_news()
        
        # 顯示新聞
        if news_list:
            st.markdown(f"### 📊 找到 {len(news_list)} 篇新聞")
            
            for i, news in enumerate(news_list[:news_count]):
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
                                    with st.spinner("AI正在分析..."):
                                        analysis_prompt = f"""
                                        請簡要分析這則新聞：
                                        標題：{news['title']}
                                        摘要：{news['summary']}
                                        
                                        請提供：1.核心重點 2.產業影響 3.趨勢預測
                                        用繁體中文回答，保持簡潔。
                                        """
                                        response = model.generate_content(analysis_prompt)
                                        st.markdown("**🤖 AI分析：**")
                                        st.write(response.text)
                                except Exception as e:
                                    st.error(f"AI分析失敗：{e}")
                            else:
                                st.error("AI模型未初始化")
        else:
            st.error("無法載入新聞，請稍後再試")
            
    except Exception as e:
        st.error(f"新聞載入錯誤：{e}")
        # 顯示備用新聞
        fallback_news = st.session_state.news_manager.get_fallback_news()
        for news in fallback_news:
            st.markdown(f"**{news['title']}**")
            st.write(news['summary'])
            st.caption(f"來源：{news['source']}")

# ========== 修正5: 智能推薦頁面 (完整替換) ==========
elif st.session_state.current_page == "推薦":
    st.markdown("## 🎯 智能推薦系統")
    
    try:
        # 學習推薦
        st.markdown("### 📚 學習建議")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🔥 熱門學習主題")
            popular_topics = [
                "🐍 Python程式設計",
                "🤖 機器學習入門", 
                "📊 數據分析技能",
                "🌐 網頁開發",
                "☁️ 雲端技術"
            ]
            for topic in popular_topics:
                st.markdown(f"- {topic}")
        
        with col2:
            st.markdown("#### 💡 個人化建議")
            
            # 分析對話記錄
            chat_count = len(st.session_state.chat_manager.chats)
            if chat_count > 0:
                suggestions = [
                    f"📈 你已進行了 {chat_count} 次對話",
                    "🎯 建議深入學習感興趣的技術領域",
                    "📖 可以嘗試更多技術問題討論"
                ]
            else:
                suggestions = [
                    "🚀 開始與AI對話來獲得個人化建議",
                    "💬 多使用對話功能來分析你的興趣",
                    "📚 探索不同主題的學習內容"
                ]
            
            for suggestion in suggestions:
                st.markdown(f"- {suggestion}")
        
        # 投資建議
        st.markdown("### 💰 投資組合建議")
        
        if st.session_state.watched_stocks:
            stock_count = len(st.session_state.watched_stocks)
            st.info(f"💼 你目前關注 {stock_count} 檔股票")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📊 組合分析")
                st.write("• 定期檢視投資組合表現")
                st.write("• 注意風險分散")
                st.write("• 關注市場趨勢變化")
            
            with col2:
                st.markdown("#### 🎯 優化建議")
                st.write("• 考慮增加不同產業股票")
                st.write("• 設定停損停利點")
                st.write("• 定期調整投資策略")
        else:
            st.info("🔍 開始添加關注股票來獲得投資建議")
        
        # 使用統計
        st.markdown("### 📊 使用統計")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("對話數量", len(st.session_state.chat_manager.chats))
        with col2:
            st.metric("關注股票", len(st.session_state.watched_stocks))
        with col3:
            taiwan_time = get_taiwan_time()
            st.metric("今日登入", taiwan_time.strftime('%H:%M'))
            
    except Exception as e:
        st.error(f"推薦系統錯誤：{e}")
        st.info("推薦功能暫時不可用，請稍後再試")

# ========== 修正6: 進階設定頁面 (完整替換) ==========
elif st.session_state.current_page == "設定":
    st.markdown("## ⚙️ 進階設定")
    
    try:
        # API狀態
        st.markdown("### 🔑 API設定狀態")
        api_status = "🟢 已連接" if model else "🔴 未連接"
        st.write(f"**Gemini API狀態**: {api_status}")
        
        if not model:
            st.warning("請檢查API密鑰設定是否正確")
            st.info("在Streamlit Cloud的Secrets中設定 GOOGLE_API_KEY")
        
        # 個人化設定
        st.markdown("### 🎨 個人化設定")
        
        col1, col2 = st.columns(2)
        with col1:
            personality = st.selectbox(
                "AI回答風格",
                ["友善", "專業", "幽默", "簡潔"],
                index=0,
                key="personality_setting"
            )
            
            response_length = st.slider(
                "回答詳細程度",
                1, 5, 3,
                help="1=簡潔, 5=詳細",
                key="response_length_setting"
            )
        
        with col2:
            auto_save = st.checkbox("自動保存對話", value=True, key="auto_save_setting")
            auto_refresh = st.checkbox("自動刷新數據", value=st.session_state.auto_refresh, key="auto_refresh_setting")
        
        # 保存設定
        if st.button("💾 保存設定", type="primary", key="save_settings"):
            try:
                new_settings = {
                    'personality': personality,
                    'response_length': response_length,
                    'auto_save': auto_save,
                    'notifications': True
                }
                st.session_state.chat_manager.update_settings(new_settings)
                st.session_state.auto_refresh = auto_refresh
                st.success("設定已保存！")
            except Exception as e:
                st.error(f"保存設定失敗：{e}")
        
        # 數據管理
        st.markdown("### 💾 數據管理")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 匯出數據", key="export_data"):
                try:
                    export_data = {
                        "export_time": get_taiwan_time().isoformat(),
                        "chats": st.session_state.chat_manager.chats,
                        "settings": st.session_state.chat_manager.settings,
                        "watched_stocks": st.session_state.watched_stocks
                    }
                    
                    st.download_button(
                        "💾 下載備份文件",
                        data=json.dumps(export_data, ensure_ascii=False, indent=2),
                        file_name=f"will_ai_backup_{get_taiwan_time().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_backup"
                    )
                except Exception as e:
                    st.error(f"匯出失敗：{e}")
        
        with col2:
            if st.button("🧹 清理數據", key="clean_data"):
                if st.checkbox("確認清理所有數據", key="confirm_clean"):
                    try:
                        st.session_state.chat_manager.chats = {}
                        st.session_state.chat_manager.folders = {'預設': []}
                        st.session_state.chat_manager.save_data()
                        st.session_state.current_chat_id = None
                        st.success("數據已清理")
                        st.rerun()
                    except Exception as e:
                        st.error(f"清理失敗：{e}")
        
        # 系統資訊
        st.markdown("### ℹ️ 系統資訊")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**版本**: Will AI Pro v1.0")
            st.write(f"**台灣時間**: {get_taiwan_time().strftime('%Y-%m-%d %H:%M:%S')}")
        
        with col2:
            st.write(f"**對話數**: {len(st.session_state.chat_manager.chats)}")
            st.write(f"**關注股票**: {len(st.session_state.watched_stocks)}")
            
    except Exception as e:
        st.error(f"設定頁面錯誤：{e}")
        st.info("設定功能暫時不可用，請稍後再試")

# ========== 修正7: 更新requirements.txt ==========
# 需要在requirements.txt中添加：
# pytz>=2023.3
