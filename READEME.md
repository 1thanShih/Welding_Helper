# PCB Studio Pro (洞洞板焊接助手)

PCB Studio Pro 是一個專為電子愛好者與創客設計的輕量級 Python 桌面應用程式。它的主要目的是解決在焊接洞洞板 (Perfboard) 時，因為翻面導致腳位左右顛倒、容易接錯線的痛點。

透過直觀的 GUI 介面，您可以在電腦上預先規劃佈局，並一鍵切換「正面元件視圖」與「背面焊接視圖」，讓焊接過程更精準、更輕鬆。

## 主要功能 (Key Features)

* **雙面視圖切換 (Dual View System)**
    * **Front View (Component Side)**：顯示元件實體、數值與走線。
    * **Back View (Solder Side)**：自動水平鏡像，顯示焊點與腳位名稱，模擬真實翻面焊接視角。

* **強大的連線系統 (Advanced Routing)**
    * 支援 **實線/虛線** 分層顯示（正面線條在背面會變細/變虛，反之亦然）。
    * **智慧吸附 (Snapping)**：自動吸附至腳位 (Pin) 或網格中心。
    * **物件化線段**：畫好的線可以被選取、移動、改色、更名或切換層級。

* **高度自定義元件 (Custom Components)**
    * **Standard Wizard**：快速生成標準 IC 或排針。
    * **Custom Drawer**：提供網格繪圖板，可自由繪製 L 型、T 型等不規則元件並定義腳位。
    * **自動存檔**：所有自訂元件會自動儲存於 user_library.json。

* **真實的視覺體驗**
    * 擬真的 PCB 綠色板身與孔位。
    * R/C/D 元件採用標準電路符號（鋸齒電阻、平行板電容）。
    * 清晰的座標標示 (Row: 1-N, Col: A-Z)。

* **直覺的操作體驗**
    * 支援滑鼠滾輪縮放 (Zoom) 與右鍵拖曳平移 (Pan)。
    * 完整的快捷鍵支援。

## 快速開始 (Quick Start)

### 系統需求
* Python 3.9 或更高版本。
* 本程式僅使用 Python 標準函式庫 (tkinter, json, math, os)，無需安裝任何 pip 套件。

### 執行方式

1. **下載專案**
   確保 main.py 與 models.py 在同一資料夾內。

2. **啟動程式**
   
   Windows (直接雙擊 run.bat 或執行):
   ```bash
   python main.py