# 🚀 Will AI Assistant Pro

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://will-ai-assistant-pro.streamlit.app)
[![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Powered by Google Gemini](https://img.shields.io/badge/Powered%20by-Google%20Gemini-4285F4?logo=google)](https://ai.google.dev/)

> 一個企業級的多功能AI助手平台，整合智能對話、即時金融數據、新聞分析與個人化推薦系統。

## 📑 目錄

- [✨ 特色功能](#-特色功能)
- [🎯 核心優勢](#-核心優勢)
- [🚀 快速開始](#-快速開始)
- [📊 功能展示](#-功能展示)
- [🛠️ 技術架構](#️-技術架構)
- [⚙️ 環境配置](#️-環境配置)
- [📈 使用指南](#-使用指南)
- [🔒 安全與隱私](#-安全與隱私)
- [📞 支援與聯絡](#-支援與聯絡)

## ✨ 特色功能

### 🤖 智能對話系統
- **多會話管理**: 支援無限對話，智能分類整理
- **個人化AI**: 可調節回答風格（專業/友善/幽默/簡潔）
- **上下文記憶**: 維持對話連貫性，提供個人化體驗
- **對話匯出**: 支援完整對話記錄導出與備份

### 📊 即時金融數據
- **美股實時追蹤**: 道瓊、標普500、納斯達克指數監控
- **智能股票匹配**: 支援中英文公司名稱自動轉換股票代碼
- **投資組合分析**: 自動計算收益率、風險評估與趨勢分析
- **市場洞察**: 基於真實數據的投資建議與風險提醒

### 📰 AI新聞分析
- **多源新聞聚合**: 整合TechCrunch、The Verge等權威科技媒體
- **智能內容解讀**: AI深度分析新聞影響與趨勢預測
- **個人化推薦**: 基於閱讀偏好的新聞內容篩選
- **實時更新**: 30分鐘自動更新，掌握最新科技動態

### 🎯 智能推薦引擎
- **行為分析**: 基於使用模式的個人化學習建議
- **投資優化**: 智能股票推薦與投資組合調整建議
- **技能提升**: 程式設計、AI技術等領域的學習路徑規劃

## 🎯 核心優勢

| 優勢 | 說明 | 效益 |
|------|------|------|
| 🔄 **實時數據** | 5分鐘更新金融數據，30分鐘更新新聞 | 確保決策基於最新資訊 |
| 🧠 **AI驅動** | Google Gemini 2.5 Flash 強力驅動 | 提供準確、快速的智能分析 |
| 🎨 **個人化** | 可自訂介面、回答風格、數據偏好 | 打造專屬的使用體驗 |
| 🔒 **隱私保護** | 本地數據存儲，無第三方數據收集 | 保障個人隱私與數據安全 |
| 📱 **跨平台** | 響應式設計，支援桌面與移動設備 | 隨時隨地存取你的AI助手 |

## 🚀 快速開始

### 💻 本地運行

```bash
# 1. 克隆專案
git clone https://github.com/williams17-ai/will-ai-assistant-pro.git
cd will-ai-assistant-pro

# 2. 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 配置環境變數
cp .env.example .env
# 編輯 .env 文件，填入你的 Gemini API Key

# 5. 啟動應用
streamlit run app.py
```

### ☁️ 雲端部署

[![Deploy on Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)

1. Fork 此專案到你的 GitHub 帳戶
2. 前往 [Streamlit Cloud](https://share.streamlit.io/) 部署
3. 在 Secrets 中設定你的 API 金鑰

## 📊 功能展示

### 智能主頁儀表板
```
📈 道瓊工業     📊 標普500      💻 納斯達克     💰 投資組合
   34,567.89      4,234.56       13,987.65      $1,245.67
   +1.23%         +0.89%         +2.45%         +3.21%
```

### AI對話範例
```
👤 用戶: 請分析Tesla的投資潛力

🤖 AI助手: 基於目前數據分析，Tesla (TSLA) 呈現以下特點：

📊 技術指標:
• 股價: $248.50 (+2.3%)
• P/E比: 65.2
• 市值: $789B

💡 投資觀點:
• 電動車市場領導地位穩固
• 自動駕駛技術持續突破
• 能源業務成長潛力大

⚠️ 風險提醒:
• 估值偏高，注意市場波動
• 競爭加劇，需關注市占率變化
```

## 🛠️ 技術架構

### 核心技術棧
- **前端框架**: Streamlit 1.28+
- **AI模型**: Google Gemini 2.5 Flash
- **數據源**: Yahoo Finance API, RSS Feeds
- **程式語言**: Python 3.8+
- **部署平台**: Streamlit Cloud

### 系統架構圖
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   Core Engine    │    │  Data Sources   │
│                 │◄──►│                  │◄──►│                 │
│ • 對話介面      │    │ • ChatManager    │    │ • Yahoo Finance │
│ • 數據儀表板    │    │ • StockManager   │    │ • RSS Feeds     │
│ • 設定管理      │    │ • NewsManager    │    │ • Gemini API    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 數據流程
1. **用戶輸入** → Streamlit UI接收
2. **請求處理** → 路由到對應管理器
3. **數據獲取** → 從外部API或緩存獲取
4. **AI處理** → Gemini分析與生成回應
5. **結果展示** → 格式化後返回用戶界面

## ⚙️ 環境配置

### 必要依賴
```txt
streamlit>=1.28.0
google-generativeai>=0.3.0
python-dotenv>=1.0.0
pandas>=2.0.0
yfinance>=0.2.0
requests>=2.31.0
feedparser>=6.0.0
beautifulsoup4>=4.12.0
```

### API 金鑰設定
| 服務 | 申請地址 | 用途 | 費用 |
|------|----------|------|------|
| Google Gemini | [AI Studio](https://makersuite.google.com/app/apikey) | AI對話與分析 | 免費額度 |

### 環境變數配置
```bash
# .env 檔案配置
GOOGLE_API_KEY=your_gemini_api_key_here
APP_DEBUG=False
APP_VERSION=1.0.0
```

## 📈 使用指南

### 🎯 首次設定
1. **獲取API金鑰**: 前往Google AI Studio申請免費API金鑰
2. **個人化設定**: 調整AI回答風格、更新頻率等偏好
3. **添加關注股票**: 輸入公司名稱自動匹配股票代碼
4. **開始對話**: 嘗試投資諮詢、技術問題等各種話題

### 💡 最佳實踐
- **股票輸入**: 支援中英文，如 "Tesla"、"特斯拉"、"TSLA"
- **新聞搜尋**: 使用關鍵字如 "GPT"、"機器學習" 獲得精準結果
- **對話管理**: 使用資料夾分類不同主題的對話
- **數據備份**: 定期匯出重要對話與設定

### 📊 進階功能
- **投資組合分析**: 自動計算持股表現與風險分散
- **AI新聞解讀**: 一鍵獲得新聞深度分析與影響評估
- **學習建議**: 基於對話歷史的個人化技能提升建議

## 🔒 安全與隱私

### 數據保護
- ✅ **本地存儲**: 所有對話記錄僅存於本地/雲端應用
- ✅ **加密傳輸**: 所有API調用使用HTTPS加密
- ✅ **無追蹤**: 不收集任何個人識別資訊
- ✅ **可刪除**: 支援完整數據清除與匯出

### API 安全
- 🔐 **金鑰保護**: API金鑰僅存於環境變數
- 🔄 **權限最小化**: 僅申請必要的API權限
- ⏰ **定期更新**: 建議定期更換API金鑰

## 🔄 更新日誌

### v1.0.0 (2024-12-21)
- 🎉 **首次發布**: 完整功能上線
- 💬 **智能對話**: 多會話管理與個人化設定
- 📊 **股市追蹤**: 實時美股數據與智能分析
- 📰 **新聞分析**: AI驅動的科技新聞解讀
- 🎯 **推薦系統**: 基於行為的個人化建議

### 開發計劃
- 🔮 **v1.1**: 支援更多國際股市
- 🌐 **v1.2**: 多語言介面支援
- 📱 **v1.3**: 移動端APP版本
- 🤖 **v1.4**: 進階AI分析功能

## 🤝 貢獻指南

歡迎參與專案改進！

### 如何貢獻
1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 開發規範
- 📝 **代碼註釋**: 保持代碼可讀性
- 🧪 **測試覆蓋**: 新功能需包含測試
- 📚 **文檔更新**: 同步更新相關文檔
- 🎨 **代碼風格**: 遵循PEP 8規範

## 📞 支援與聯絡

### 🆘 獲得幫助
- 📧 **Email**: [b.williams.yang@gmail.com](mailto:b.williams.yang@gmail.com)
- 🐛 **Bug回報**: [GitHub Issues](https://github.com/williams17-ai/will-ai-assistant-pro/issues)
- 💡 **功能建議**: [GitHub Discussions](https://github.com/williams17-ai/will-ai-assistant-pro/discussions)

### 📱 社群連結
- 🔗 **GitHub**: [@williams17-ai](https://github.com/williams17-ai)
- 💼 **LinkedIn**: [專案展示](https://linkedin.com/in/your-profile)

## 📄 授權協議

本專案採用 MIT 授權協議 - 詳見 [LICENSE](LICENSE) 文件

```
MIT License

Copyright (c) 2024 Williams Yang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 🙏 致謝

特別感謝以下技術與服務提供者：

- 🤖 **Google Gemini AI** - 強大的AI對話能力
- 📊 **Yahoo Finance** - 可靠的金融數據來源
- 🚀 **Streamlit** - 優秀的Web應用框架
- 📰 **RSS新聞源** - 豐富的科技資訊內容

---

<div align="center">

**🌟 如果這個專案對你有幫助，請給個星星支持！🌟**

[![GitHub stars](https://img.shields.io/github/stars/williams17-ai/will-ai-assistant-pro?style=social)](https://github.com/williams17-ai/will-ai-assistant-pro/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/williams17-ai/will-ai-assistant-pro?style=social)](https://github.com/williams17-ai/will-ai-assistant-pro/network/members)

</div>
