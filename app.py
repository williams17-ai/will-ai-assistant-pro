# 智能推薦系統
    st.markdown("### 🎯 今日智能推薦")
    
    try:
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
            st.markdown("#### 💡 個人化建議")
            
            personalization_tips = []
            
            if total_chats > 20:
                personalization_tips.append("🗂️ 考慮創建更多主題資料夾來組織對話")
            
            if len(recent_chats) < 3:
                personalization_tips.append("💬 增加使用頻率可以獲得更好的個人化體驗")
            
            if len(st.session_state.watched_stocks) < 5:
                personalization_tips.append("📊 添加更多關注股票來獲得更全面的市場洞察")
            
            if not personalization_tips:
                personalization_tips = [
                    "✨ 你的使用模式很理想！",
                    "🚀 繼續保持這樣的互動頻率",
                    "📚 嘗試問一些新領域的問題來拓展視野"
                ]
            
            for tip in personalization_tips:
                st.markdown(f"- {tip}")
                
    except Exception as e:
        st.error(f"推薦系統錯誤：{e}")
        st.info("推薦功能暫時不可用，請稍後再試")

elif st.session_state.current_page == "設定":
    # 進階設定頁面
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ 進階設定</h1>
        <p>自訂你的Pro版AI助手體驗</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API設定
    st.markdown("### 🔑 API設定")
    current_api_key = os.getenv("GOOGLE_API_KEY", "")
    masked_key = current_api_key[:8] + "..." + current_api_key[-4:] if current_api_key else "未設定"
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("Gemini API Key", value=masked_key, disabled=True, help="在.env文件中修改")
    with col2:
        api_status = "🟢 已連接" if model else "🔴 未連接"
        st.markdown(f"**狀態**: {api_status}")
    
    if not model:
        st.warning("請檢查API密鑰設定是否正確")
        with st.expander("📋 如何設定API密鑰"):
            st.markdown("""
            **Streamlit Cloud部署：**
            1. 前往 [Google AI Studio](https://makersuite.google.com/app/apikey) 獲取API密鑰
            2. 在Streamlit Cloud點擊右下角 "Manage app"
            3. 選擇 "Secrets" 標籤
            4. 添加：`GOOGLE_API_KEY = "你的API密鑰"`
            5. 保存並重新啟動應用
            
            **本地開發：**
            1. 創建 `.env` 文件
            2. 添加：`GOOGLE_API_KEY=你的API密鑰`
            """)
    
    # 個人化設定 - 修正保存功能
    st.markdown("### 🎨 個人化設定")
    
    col1, col2 = st.columns(2)
    with col1:
        new_personality = st.selectbox(
            "AI回答風格", 
            ["專業", "友善", "幽默", "簡潔"], 
            index=["專業", "友善", "幽默", "簡潔"].index(st.session_state.chat_manager.settings.get('personality', '友善')),
            key="personality_select"
        )
        
        new_response_length = st.slider(
            "回答詳細程度", 
            1, 5, 
            st.session_state.chat_manager.settings.get('response_length', 3),
            help="1=簡潔, 5=詳細",
            key="response_length_slider"
        )
    
    with col2:
        auto_save = st.checkbox(
            "自動保存對話", 
            value=st.session_state.chat_manager.settings.get('auto_save', True),
            key="auto_save_checkbox"
        )
        
        notifications = st.checkbox(
            "啟用通知", 
            value=st.session_state.chat_manager.settings.get('notifications', True),
            key="notifications_checkbox"
        )
        
        # 新增自動刷新全域設定
        global_auto_refresh = st.checkbox(
            "全域自動刷新", 
            value=st.session_state.auto_refresh,
            key="global_auto_refresh_checkbox"
        )
    
    # 保存設定按鈕
    if st.button("💾 保存設定", type="primary", key="save_settings_button"):
        try:
            new_settings = {
                'personality': new_personality,
                'response_length': new_response_length,
                'auto_save': auto_save,
                'notifications': notifications
            }
            st.session_state.chat_manager.update_settings(new_settings)
            st.session_state.auto_refresh = global_auto_refresh
            st.success("設定已保存！")
            st.rerun()
        except Exception as e:
            st.error(f"保存設定失敗：{e}")
    
    # 數據管理
    st.markdown("### 💾 數據管理")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📤 完整備份", use_container_width=True, key="backup_button"):
            try:
                backup_data = {
                    "backup_time": get_taiwan_time().isoformat(),
                    "version": "Pro 1.0",
                    "chat_data": st.session_state.chat_manager.chats,
                    "folders": st.session_state.chat_manager.folders,
                    "settings": st.session_state.chat_manager.settings,
                    "watched_stocks": st.session_state.watched_stocks
                }
                
                st.download_button(
                    "💾 下載備份檔案",
                    data=json.dumps(backup_data, ensure_ascii=False, indent=2),
                    file_name=f"will_ai_pro_backup_{get_taiwan_time().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="download_backup_button"
                )
            except Exception as e:
                st.error(f"備份失敗：{e}")
    
    with col2:
        uploaded_file = st.file_uploader("📂 匯入備份", type=['json'], key="import_backup")
        if uploaded_file and st.button("匯入", use_container_width=True, key="import_button"):
            try:
                backup_data = json.load(uploaded_file)
                st.session_state.chat_manager.chats = backup_data.get('chat_data', {})
                st.session_state.chat_manager.folders = backup_data.get('folders', {})
                st.session_state.chat_manager.settings = backup_data.get('settings', {})
                if 'watched_stocks' in backup_data:
                    st.session_state.watched_stocks = backup_data['watched_stocks']
                st.session_state.chat_manager.save_data()
                st.success("備份匯入成功！")
                st.rerun()
            except Exception as e:
                st.error(f"匯入失敗：{e}")
    
    with col3:
        if st.button("🧹 清理優化", use_container_width=True, key="cleanup_button"):
            try:
                # 清理30天前的對話
                cutoff_date = get_taiwan_time() - timedelta(days=30)
                deleted_count = 0
                
                for chat_id, chat in list(st.session_state.chat_manager.chats.items()):
                    try:
                        chat_date = datetime.fromisoformat(chat['updated_at'].replace('Z', '+00:00'))
                        if chat_date < cutoff_date:
                            st.session_state.chat_manager.delete_chat(chat_id)
                            deleted_count += 1
                    except:
                        continue
                
                # 清理股票緩存
                st.session_state.stock_manager.cache.clear()
                st.session_state.news_manager.cache.clear()
                
                st.success(f"已清理 {deleted_count} 個舊對話和所有緩存")
            except Exception as e:
                st.error(f"清理失敗：{e}")
    
    with col4:
        if st.button("⚠️ 重置全部", use_container_width=True, key="reset_button"):
            if st.checkbox("確認重置所有數據", key="confirm_reset"):
                try:
                    st.session_state.chat_manager.folders = {'預設': [], '編程': [], '學習': [], '工作': [], '生活': [], '投資': []}
                    st.session_state.chat_manager.chats = {}
                    st.session_state.chat_manager.settings = {
                        'theme': '明亮',
                        'personality': '友善',
                        'response_length': 3,
                        'auto_save': True,
                        'notifications': True
                    }
                    st.session_state.watched_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
                    st.session_state.chat_manager.save_data()
                    st.success("所有數據已重置")
                    st.rerun()
                except Exception as e:
                    st.error(f"重置失敗：{e}")
    
    # 進階功能設定
    st.markdown("### 🚀 進階功能")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 股市功能")
        st.text_input("股市API頻率限制", value="每5分鐘", disabled=True, key="stock_api_limit")
        st.selectbox("預設股市", ["美股", "台股", "港股"], index=0, key="default_market")
        st.number_input("最大關注股票數", min_value=5, max_value=50, value=20, key="max_stocks")
    
    with col2:
        st.markdown("#### 📰 新聞功能")
        st.selectbox("新聞語言偏好", ["繁體中文", "英文", "雙語"], index=0, key="news_language")
        st.selectbox("新聞更新頻率", ["即時", "每小時", "每日"], index=1, key="news_frequency")
        st.multiselect(
            "新聞來源", 
            ["TechCrunch", "The Verge", "Wired", "科技新報", "數位時代"],
            default=["TechCrunch", "The Verge"],
            key="news_sources"
        )
    
    # 系統資訊
    st.markdown("### ℹ️ 系統資訊")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**版本資訊**")
        st.text("Will AI Pro v1.0")
        st.text(f"最後更新: {get_taiwan_time().strftime('%Y-%m-%d')}")
    
    with col2:
        st.markdown("**使用統計**")
        st.text(f"總對話: {len(st.session_state.chat_manager.chats)}")
        st.text(f"關注股票: {len(st.session_state.watched_stocks)}")
    
    with col3:
        st.markdown("**性能指標**")
        cache_size = len(st.session_state.stock_manager.cache) + len(st.session_state.news_manager.cache)
        st.text(f"緩存項目: {cache_size}")
        auto_status = "開啟" if st.session_state.auto_refresh else "關閉"
        st.text(f"自動刷新: {auto_status}")

else:
    # 默認頁面（防止空白）
    st.title("🚀 Will的AI小幫手 Pro")
    st.info("請從左側選單選擇功能")
    st.markdown("### 可用功能：")
    st.write("• 💬 AI智能對話")
    st.write("• 📊 即時股市追蹤") 
    st.write("• 📰 AI新知資訊")
    st.write("• 🎯 智能推薦")
    st.write("• ⚙️ 進階設定")

# 添加側邊欄中的聊天管理功能
if st.session_state.current_page == "對話":
    with st.sidebar:
        st.divider()
        
        # 新對話按鈕
        if st.button("➕ 新對話", use_container_width=True, type="primary", key="sidebar_new_chat"):
            new_chat_id = st.session_state.chat_manager.create_new_chat()
            st.session_state.current_chat_id = new_chat_id
            st.rerun()
        
        # 顯示聊天記錄
        st.markdown("### 📁 對話記錄")
        
        for folder_name, chat_ids in st.session_state.chat_manager.folders.items():
            if chat_ids:
                with st.expander(f"📁 {folder_name} ({len(chat_ids)})", expanded=folder_name=="預設"):
                    for chat_id in chat_ids:
                        if chat_id in st.session_state.chat_manager.chats:
                            chat = st.session_state.chat_manager.chats[chat_id]
                            
                            # 顯示對話項目
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                if st.button(
                                    f"💬 {chat['title'][:15]}...", 
                                    key=f"chat_{chat_id}",
                                    help=f"建立於: {chat['created_at'][:16]}",
                                    use_container_width=True
                                ):
                                    st.session_state.current_chat_id = chat_id
                                    st.rerun()
                            
                            with col2:
                                if st.button("🗑️", key=f"del_{chat_id}", help="刪除對話"):
                                    st.session_state.chat_manager.delete_chat(chat_id)
                                    if st.session_state.current_chat_id == chat_id:
                                        st.session_state.current_chat_id = None
                                    st.rerun()

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
    # 美股交易時間考慮時區 (美東時間 9:30-16:00，台灣時間約 22:30-05:00)
    market_status = "🟢 開盤中" if 22 <= current_hour or current_hour <= 5 else "🔴 休市"
    st.markdown(f"**{market_status}**")
    st.caption("美股交易狀態")

with col4:
    taiwan_time = get_taiwan_time()
    st.markdown(f"**⏰ {taiwan_time.strftime('%H:%M:%S')}**")
    auto_status = "🔄 自動刷新開啟" if st.session_state.auto_refresh else "⏸️ 手動模式"
    st.caption(auto_status).markdown("#### 📈 推薦關注股票")
            if stock_recommendations:
                for stock in stock_recommendations:
                    stock_data = st.session_state.stock_manager.get_stock_data(stock)
                    if stock_data:
                        st.markdown(f"- **{stock}**: ${stock_data['price']} ({stock_data['change_percent']:+.2f}%)")
            else:
                st.info("添加關注股票來獲得智能推薦！")
    except Exception as e:
        st.info("推薦功能載入中...")

elif st.session_state.current_page == "對話":
    # AI對話頁面
    st.title("💬 AI智能對話")
    
    # 顯示API狀態
    if not model:
        st.error("❌ AI模型未初始化，請檢查API密鑰設定")
        st.info("請在Streamlit Cloud的Secrets中正確設定 GOOGLE_API_KEY")
        
        # 顯示如何設定的說明
        with st.expander("📋 如何設定API密鑰"):
            st.markdown("""
            1. 前往 [Google AI Studio](https://makersuite.google.com/app/apikey) 獲取API密鑰
            2. 在Streamlit Cloud點擊右下角 "Manage app"
            3. 選擇 "Secrets" 標籤
            4. 添加：`GOOGLE_API_KEY = "你的API密鑰"`
            5. 保存並重新啟動應用
            """)
        return
    
    # 如果沒有當前對話，創建一個
    if st.session_state.current_chat_id is None:
        st.markdown("### 🚀 開始新對話")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            chat_title = st.text_input("對話標題", value="新對話", key="new_chat_title")
        with col2:
            if st.button("創建對話", key="create_chat", type="primary"):
                try:
                    new_chat_id = st.session_state.chat_manager.create_new_chat(chat_title)
                    st.session_state.current_chat_id = new_chat_id
                    st.success("對話已創建！")
                    st.rerun()
                except Exception as e:
                    st.error(f"創建對話失敗：{e}")
        
        # 快速開始選項
        st.markdown("#### 💡 快速開始話題")
        quick_topics = [
            "請介紹一下最新的AI技術趨勢",
            "幫我分析目前的股市情況", 
            "我想學習Python程式設計",
            "給我一些投資理財的建議"
        ]
        
        cols = st.columns(2)
        for i, topic in enumerate(quick_topics):
            with cols[i % 2]:
                if st.button(f"💭 {topic}", key=f"quick_{i}", use_container_width=True):
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
                        st.info("請檢查網路連接或稍後再試")
        
        except KeyError:
            st.error("對話不存在，請創建新對話")
            st.session_state.current_chat_id = None
            st.rerun()
        except Exception as e:
            st.error(f"對話頁面錯誤：{e}")

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
    with st.spinner("載入市場指數..."):
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
    else:
        st.info("正在載入市場指數數據...")
    
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
    
    with col3:
        if st.button("🔄 刷新數據"):
            # 清除緩存以強制刷新
            st.session_state.stock_manager.cache.clear()
            st.success("數據已刷新")
            st.rerun()
    
    # 自動刷新開關
    col1, col2 = st.columns([1, 3])
    with col1:
        auto_refresh_stocks = st.checkbox("自動刷新股市數據", value=st.session_state.auto_refresh)
        if auto_refresh_stocks != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto_refresh_stocks
    
    # 顯示關注的股票
    if st.session_state.watched_stocks:
        st.markdown("### 📊 關注股票詳情")
        for i, stock in enumerate(st.session_state.watched_stocks):
            stock_data = st.session_state.stock_manager.get_stock_data(stock)
            
            if stock_data:
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{stock_data['name'][:20]}**")
                    st.caption(f"({stock})")
                
                with col2:
                    st.metric("股價", f"${stock_data['price']}")
                
                with col3:
                    change_color = "green" if stock_data['change'] >= 0 else "red"
                    st.markdown(f"<span style='color: {change_color};'>{stock_data['change']:+.2f}</span>", 
                              unsafe_allow_html=True)
                
                with col4:
                    change_color = "green" if stock_data['change_percent'] >= 0 else "red"
                    st.markdown(f"<span style='color: {change_color};'>{stock_data['change_percent']:+.2f}%</span>", 
                              unsafe_allow_html=True)
                
                with col5:
                    if stock_data['pe_ratio'] != 'N/A':
                        st.caption(f"P/E: {stock_data['pe_ratio']:.2f}")
                    else:
                        st.caption("P/E: N/A")
                
                with col6:
                    if st.button("❌", key=f"remove_{stock}_{i}"):
                        st.session_state.watched_stocks.remove(stock)
                        st.rerun()
            
            else:
                st.error(f"無法獲取 {stock} 的數據")
        
        # 投資組合分析
        st.markdown("### 📊 投資組合分析")
        portfolio_df = []
        
        for stock in st.session_state.watched_stocks:
            stock_data = st.session_state.stock_manager.get_stock_data(stock)
            if stock_data:
                portfolio_df.append({
                    '股票': stock,
                    '股價': stock_data['price'],
                    '漲跌': stock_data['change'],
                    '漲跌幅': f"{stock_data['change_percent']:.2f}%",
                    'P/E比': stock_data['pe_ratio'] if stock_data['pe_ratio'] != 'N/A' else 'N/A'
                })
        
        if portfolio_df:
            df = pd.DataFrame(portfolio_df)
            st.dataframe(df, use_container_width=True)
            
            # 簡單的投資組合統計
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_change = sum([float(row['漲跌幅'].replace('%', '')) for row in portfolio_df]) / len(portfolio_df)
                st.metric("平均漲跌幅", f"{avg_change:.2f}%")
            
            with col2:
                gainers = len([row for row in portfolio_df if float(row['漲跌幅'].replace('%', '')) > 0])
                st.metric("上漲股票數", f"{gainers}/{len(portfolio_df)}")
            
            with col3:
                total_value = sum([row['股價'] for row in portfolio_df])
                st.metric("組合總價值", f"${total_value:.2f}")
    else:
        st.info("還沒有關注的股票，請添加一些股票開始追蹤")

elif st.session_state.current_page == "新知":
    # AI新知頁面
    st.markdown("""
    <div class="main-header">
        <h1>📰 AI新知與科技資訊</h1>
        <p>即時新聞 · 深度分析 · 趨勢洞察</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 新聞訂閱控制
    col1, col2, col3 = st.columns(3)
    with col1:
        auto_refresh_news = st.checkbox("自動刷新新聞", value=st.session_state.auto_refresh, key="auto_refresh_news")
        if auto_refresh_news != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto_refresh_news
    with col2:
        if st.button("🔄 手動刷新新聞", key="manual_refresh_news"):
            st.session_state.news_manager.cache.clear()
            st.success("新聞數據已刷新")
            st.rerun()
    with col3:
        news_count = st.selectbox("顯示數量", [5, 10, 15, 20], index=2, key="news_count_select")
    
    # 自動刷新邏輯
    if should_auto_refresh():
        st.rerun()
    
    # 新聞搜尋
    st.markdown("### 🔍 新聞搜尋")
    search_term = st.text_input("搜尋特定主題", placeholder="例如: GPT, 機器學習, 自動駕駛", key="news_search")
    
    # 載入新聞數據
    with st.spinner("📰 正在載入最新新聞..."):
        try:
            if search_term:
                search_results = st.session_state.news_manager.search_news(search_term)
                if search_results:
                    st.success(f"找到 {len(search_results)} 篇相關新聞")
                    news_to_show = search_results
                else:
                    st.warning("沒有找到相關新聞，顯示最新AI新聞")
                    news_to_show = st.session_state.news_manager.get_ai_news()
            else:
                news_to_show = st.session_state.news_manager.get_ai_news()
            
            # 檢查新聞數據
            if not news_to_show:
                st.warning("暫時無法獲取新聞數據，顯示備用新聞")
                news_to_show = st.session_state.news_manager.get_fallback_news()
                
        except Exception as e:
            st.error(f"載入新聞時發生錯誤：{e}")
            news_to_show = st.session_state.news_manager.get_fallback_news()
    
    # 顯示新聞
    st.markdown("### 🔥 最新AI新聞")
    
    if news_to_show:
        for i, news in enumerate(news_to_show[:news_count]):
            # 使用expander來組織新聞內容
            with st.expander(f"📰 {news['title']}", expanded=False):
                st.write(f"**摘要：** {news['summary']}")
                st.write(f"**發布時間：** {news['published']}")
                st.write(f"**來源：** {news['source']}")
                
                # 操作按鈕
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📖 閱讀原文", key=f"read_news_{i}"):
                        if news['link'] != '#':
                            st.info(f"原文連結：{news['link']}")
                            st.markdown(f"[👆 點擊這裡開啟原文]({news['link']})")
                        else:
                            st.info("這是範例新聞，無原文連結")
                
                with col2:
                    if st.button("💬 AI解讀", key=f"analyze_news_{i}"):
                        # 使用Gemini分析新聞
                        if model:
                            with st.spinner("🤖 AI正在分析新聞內容..."):
                                try:
                                    # 簡化的系統提示，不包含持股信息
                                    analysis_prompt = f"""
                                    請分析以下AI新聞：
                                    
                                    標題：{news['title']}
                                    摘要：{news['summary']}
                                    
                                    請簡潔地提供：
                                    1. 核心重點是什麼？
                                    2. 對AI產業的影響
                                    3. 對一般用戶的意義
                                    
                                    請用繁體中文回答，保持簡潔易懂。
                                    """
                                    
                                    response = model.generate_content(analysis_prompt)
                                    st.markdown("**🤖 AI分析結果：**")
                                    st.markdown(response.text)
                                    
                                except Exception as e:
                                    st.error(f"AI分析失敗：{e}")
                                    st.info("請稍後再試或檢查API設定")
                        else:
                            st.error("AI模型未初始化，請檢查API設定")
                
                with col3:
                    if st.button("📋 複製摘要", key=f"copy_news_{i}"):
                        # 顯示可複製的文本
                        copy_text = f"標題：{news['title']}\n摘要：{news['summary']}\n來源：{news['source']}\n時間：{news['published']}"
                        st.text_area("複製以下內容：", copy_text, height=100, key=f"copy_area_{i}")
            
            # 分隔線
            if i < len(news_to_show[:news_count]) - 1:
                st.divider()
    else:
        st.error("無法載入新聞內容，請檢查網路連線或稍後再試")
        
    # 新聞訂閱設定
    with st.expander("📮 訂閱偏好設定"):
        col1, col2 = st.columns(2)
        with col1:
            selected_topics = st.multiselect(
                "感興趣的AI領域",
                ["大語言模型", "電腦視覺", "自動駕駛", "機器人", "量子計算", "神經網路", "自然語言處理"],
                default=["大語言模型", "電腦視覺"],
                key="ai_topics_select"
            )
        with col2:
            news_source_pref = st.selectbox("新聞來源偏好", ["全部", "英文媒體", "中文媒體", "學術期刊"], key="news_source_pref")
            news_freshness = st.slider("新聞新鮮度（小時）", 1, 48, 12, key="news_freshness_slider")
            
        if st.button("💾 保存訂閱設定", key="save_news_prefs"):
            # 這裡可以保存用戶的新聞偏好設定
            st.success("訂閱設定已保存！")

elif st.session_state.current_page == "推薦":
    # 智能推薦頁面
    st.markdown("""
    <div class="main-header">
        <h1>🎯 智能推薦系統</h1>
        <p>基於你的行為模式提供個人化建議</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        recommendation_engine = RecommendationEngine(st.session_state.chat_manager)
        
        # 學習主題推薦
        st.markdown("### 📚 學習主題推薦")
        
        # 分析用戶聊天記錄
        chat_analysis = {}
        programming_langs = ['python', 'javascript', 'java', 'cpp', 'go', 'rust']
        topics = ['ai', 'machine learning', '機器學習', 'data science', '數據科學', 'web development']
        
        if st.session_state.chat_manager.chats:
            for chat in st.session_state.chat_manager.chats.values():
                for message in chat['messages']:
                    if message['role'] == 'user':
                        content = message['content'].lower()
                        for lang in programming_langs:
                            if lang in content:
                                chat_analysis[lang] = chat_analysis.get(lang, 0) + 1
                        for topic in topics:
                            if topic in content:
                                chat_analysis[topic] = chat_analysis.get(topic, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔥 你最常討論的主題")
            if chat_analysis:
                sorted_topics = sorted(chat_analysis.items(), key=lambda x: x[1], reverse=True)
                for topic, count in sorted_topics[:5]:
                    st.markdown(f"- **{topic.title()}**: {count} 次提及")
            else:
                st.info("開始使用AI對話來獲得個人化推薦！")
        
        with col2:
            st.markdown("#### 💡 建議學習方向")
            recommendations = []
            
            if chat_analysis.get('python', 0) > 3:
                recommendations.append("🐍 Python進階：異步編程與性能優化")
            if chat_analysis.get('javascript', 0) > 2:
                recommendations.append("⚛️ React/Vue.js前端開發")
            if chat_analysis.get('ai', 0) + chat_analysis.get('machine learning', 0) > 2:
                recommendations.append("🤖 深度學習實戰項目")
            if chat_analysis.get('web development', 0) > 1:
                recommendations.append("🌐 全棧開發：從前端到後端")
            
            if not recommendations:
                recommendations = [
                    "🚀 開始你的編程之旅：Python基礎",
                    "💻 現代網頁開發入門",
                    "🤖 AI與機器學習概念"
                ]
            
            for rec in recommendations:
                st.markdown(f"- {rec}")
        
        # 投資建議
        st.markdown("### 💰 投資組合優化建議")
        
        if st.session_state.watched_stocks:
            # 分析當前投資組合
            portfolio_analysis = {}
            sectors = {
                'AAPL': '科技', 'GOOGL': '科技', 'MSFT': '科技', 'AMZN': '電商',
                'TSLA': '電動車', 'NVDA': '半導體', 'META': '社交媒體',
                'JPM': '金融', 'JNJ': '醫療', 'V': '金融服務'
            }
            
            for stock in st.session_state.watched_stocks:
                sector = sectors.get(stock, '其他')
                portfolio_analysis[sector] = portfolio_analysis.get(sector, 0) + 1
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 目前投資組合分布")
                for sector, count in portfolio_analysis.items():
                    percentage = (count / len(st.session_state.watched_stocks)) * 100
                    st.markdown(f"- **{sector}**: {count} 檔股票 ({percentage:.1f}%)")
            
            with col2:
                st.markdown("#### 🎯 多元化建議")
                suggestions = []
                
                if portfolio_analysis.get('科技', 0) > len(st.session_state.watched_stocks) * 0.7:
                    suggestions.append("⚠️ 科技股比重過高，建議增加其他產業")
                    suggestions.append("💊 考慮添加醫療保健股：JNJ, PFE")
                    suggestions.append("🏦 考慮添加金融股：JPM, BAC")
                
                if '金融' not in portfolio_analysis:
                    suggestions.append("🏦 建議添加金融服務股票作為平衡")
                
                if '醫療' not in portfolio_analysis:
                    suggestions.append("💊 醫療保健是防禦性投資的好選擇")
                
                if not suggestions:
                    suggestions.append("✅ 投資組合分布良好")
                    suggestions.append("📈 定期檢視並調整比重")
                
                for suggestion in suggestions:
                    st.markdown(f"- {suggestion}")
        else:
            st.info("🔍 開始添加關注股票來獲得投資建議")
        
        # 個人化AI助手建議
        st.markdown("### 🤖 AI助手個人化建議")
        
        # 基於使用模式提供建議
        total_chats = len(st.session_state.chat_manager.chats)
        taiwan_time = get_taiwan_time()
        recent_chats = [chat for chat in st.session_state.chat_manager.chats.values() 
                       if datetime.fromisoformat(chat['updated_at'].replace('Z', '+00:00')) > taiwan_time - timedelta(days=7)]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 使用模式分析")
            st.metric("總對話數", total_chats)
            st.metric("本週活躍度", len(recent_chats))
            st.metric("關注股票", len(st.session_state.watched_stocks))
        
        with col2:
            stimport streamlit as st
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
    """獲取台灣時間"""
    return datetime.now(TAIWAN_TZ)

# 支援Streamlit Cloud的環境變數讀取
def get_api_key():
    # 優先從Streamlit secrets讀取
    if hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    # 其次從環境變數讀取
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
            },
            {
                'title': 'AI在醫療診斷領域的新突破',
                'summary': '最新研究顯示，AI系統在某些疾病診斷方面已經超越了人類醫生的準確率，為醫療行業帶來革命性變化...',
                'link': '#',
                'published': '6小時前',
                'source': 'The Verge'
            }
        ]
    
    def search_news(self, query, max_results=10):
        """搜尋特定主題新聞"""
        try:
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

# 聊天管理器
class ChatManager:
    def __init__(self):
        self.data_file = "will_chat_data_pro.json"
        self.load_data()
    
    def load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.folders = data.get('folders', {})
                self.chats = data.get('chats', {})
                self.settings = data.get('settings', {})
        except (FileNotFoundError, json.JSONDecodeError):
            # 初始化默認數據結構
            self.folders = {
                '預設': [], 
                '編程': [], 
                '學習': [], 
                '工作': [], 
                '生活': [], 
                '投資': []
            }
            self.chats = {}
            self.settings = {
                'theme': '明亮',
                'language': '繁體中文',
                'personality': '友善',
                'response_length': 3,
                'auto_save': True,
                'notifications': True
            }
            # 創建初始數據文件
            self.save_data()
    
    def save_data(self):
        data = {
            'folders': self.folders,
            'chats': self.chats,
            'settings': self.settings
        }
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass  # 雲端環境可能無法寫文件
    
    def create_new_chat(self, title="新對話", folder="預設"):
        chat_id = str(uuid.uuid4())
        self.chats[chat_id] = {
            'id': chat_id,
            'title': title,
            'messages': [],
            'created_at': get_taiwan_time().isoformat(),
            'updated_at': get_taiwan_time().isoformat(),
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
            self.chats[chat_id]['updated_at'] = get_taiwan_time().isoformat()
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

# 自動刷新檢查函數
def should_auto_refresh():
    """檢查是否需要自動刷新"""
    if not st.session_state.auto_refresh:
        return False
    
    current_time = time.time()
    if 'last_refresh_time' not in st.session_state:
        st.session_state.last_refresh_time = current_time
        return False
        
    if current_time - st.session_state.last_refresh_time > 60:  # 每60秒檢查一次
        st.session_state.last_refresh_time = current_time
        return True
    return False

# 初始化管理器
if "stock_manager" not in st.session_state:
    st.session_state.stock_manager = StockDataManager()

if "news_manager" not in st.session_state:
    st.session_state.news_manager = NewsManager()

if "stock_matcher" not in st.session_state:
    st.session_state.stock_matcher = StockSymbolMatcher()

if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "主頁"

if "watched_stocks" not in st.session_state:
    st.session_state.watched_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

# 初始化Gemini
@st.cache_resource
def init_gemini():
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
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
    
    # 即時狀態指示器 - 使用台灣時間
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<span class="real-time-badge">🔴 即時數據</span>', unsafe_allow_html=True)
    with col2:
        taiwan_time = get_taiwan_time()
        st.markdown(f"⏰ {taiwan_time.strftime('%H:%M')}")
    
    # 頁面導航
    st.markdown("### 📋 功能選單")
    
    # 使用按鈕進行頁面導航
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
    
    # 快速搜尋
    st.markdown("### 🔍 快速搜尋")
    search_query = st.text_input("搜尋對話...", placeholder="輸入關鍵詞", key="sidebar_search")
    if search_query:
        results = st.session_state.chat_manager.search_chats(search_query)
        if results:
            st.write(f"找到 {len(results)} 個結果")
            for result_id in results[:3]:
                chat = st.session_state.chat_manager.chats[result_id]
                if st.button(f"📄 {chat['title'][:15]}...", key=f"search_{result_id}"):
                    st.session_state.current_chat_id = result_id
                    st.session_state.current_page = "對話"
                    st.rerun()

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
    
    # 快速功能測試
    st.markdown("### 🚀 快速開始")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🤖 開始AI對話", key="test_ai", use_container_width=True):
            st.session_state.current_page = "對話"
            st.rerun()
    with col2:
        if st.button("📰 查看AI新聞", key="test_news", use_container_width=True):
            st.session_state.current_page = "新知"
            st.rerun()
    with col3:
        if st.button("📊 查看股市", key="test_stock", use_container_width=True):
            st.session_state.current_page = "股市"
            st.rerun()
    
    # 即時數據儀表板
    col1, col2, col3, col4 = st.columns(4)
    
    # 獲取市場指數
    with st.spinner("載入市場數據..."):
        market_data = st.session_state.stock_manager.get_market_indices()
    
    with col1:
        if '道瓊工業' in market_data:
            data = market_data['道瓊工業']
            st.markdown(f"""
            <div class="metric-card">
                <h4>📈 道瓊工業</h4>
                <h3>{data['price']}</h3>
                <p style="color: white;">{data['change']:+.2f} ({data['change_percent']:+.2f}%)</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card">
                <h4>📈 道瓊工業</h4>
                <h3>載入中...</h3>
                <p style="color: white;">數據更新中</p>
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
        else:
            st.markdown("""
            <div class="metric-card">
                <h4>📊 標普500</h4>
                <h3>載入中...</h3>
                <p style="color: white;">數據更新中</p>
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
        else:
            st.markdown("""
            <div class="metric-card">
                <h4>💻 納斯達克</h4>
                <h3>載入中...</h3>
                <p style="color: white;">數據更新中</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        # 投資組合總覽
        api_status = "🟢 正常" if model else "🔴 錯誤"
        stock_count = len(st.session_state.watched_stocks)
        st.markdown(f"""
        <div class="metric-card">
            <h4>🤖 系統狀態</h4>
            <h3>{api_status}</h3>
            <p style="color: white;">關注股票: {stock_count}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 智能推薦系統
    st.markdown("### 🎯 今日智能推薦")
