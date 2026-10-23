import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(
    page_title="專業臥室空間設計 & 坐向方位系統",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 隱藏 Streamlit 預設的多餘邊界，讓 App 在電腦與手機上都能滿版操作
st.markdown("""
<style>
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    header { display: none !important; }
    footer { display: none !important; }
</style>
""", unsafe_allow_html=True)

# 預設富士山美景 SVG Data URI (免網路依賴、秒開、高畫質向量風景，亦可自由上傳照片替換)
FUJI_SVG = """data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 500' width='800' height='500'>
<defs>
  <linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'>
    <stop offset='0%' stop-color='%231e3c72'/>
    <stop offset='45%' stop-color='%232a5298'/>
    <stop offset='80%' stop-color='%23f6d365'/>
    <stop offset='100%' stop-color='%23fda085'/>
  </linearGradient>
  <linearGradient id='fuji' x1='0' y1='0' x2='0' y2='1'>
    <stop offset='0%' stop-color='%233b4d71'/>
    <stop offset='100%' stop-color='%231a233a'/>
  </linearGradient>
  <linearGradient id='lake' x1='0' y1='0' x2='0' y2='1'>
    <stop offset='0%' stop-color='%232a486b'/>
    <stop offset='100%' stop-color='%230f1c2e'/>
  </linearGradient>
</defs>
<rect width='800' height='360' fill='url(%23sky)'/>
<circle cx='620' cy='130' r='55' fill='%23ffefba' opacity='0.85'/>
<!-- 遠山雲彩 -->
<ellipse cx='180' cy='240' rx='140' ry='22' fill='%23ffffff' opacity='0.25'/>
<ellipse cx='650' cy='210' rx='160' ry='18' fill='%23ffffff' opacity='0.2'/>
<!-- 富士山主體 -->
<path d='M 80 360 Q 290 270 355 110 L 445 110 Q 510 270 720 360 Z' fill='url(%23fuji)'/>
<!-- 富士山頂白雪 -->
<path d='M 355 110 L 445 110 Q 470 175 492 215 L 460 195 L 435 225 L 408 188 L 385 225 L 358 192 L 312 215 Q 332 175 355 110 Z' fill='%23ffffff'/>
<!-- 河口湖水與倒影 -->
<rect y='360' width='800' height='140' fill='url(%23lake)'/>
<path d='M 220 360 Q 340 410 365 465 L 435 465 Q 460 410 580 360 Z' fill='%233b4d71' opacity='0.45'/>
<path d='M 362 435 L 438 435 L 425 465 L 375 465 Z' fill='%23ffffff' opacity='0.35'/>
<!-- 櫻花前景點綴 -->
<circle cx='90' cy='60' r='35' fill='%23ffb7c5' opacity='0.8'/>
<circle cx='140' cy='40' r='45' fill='%23ffc0cb' opacity='0.85'/>
<circle cx='50' cy='100' r='30' fill='%23ff9ebb' opacity='0.75'/>
</svg>"""

# --- 預設格局與所有物件 (包含家具 + 窗戶與牆壁插座) ---
DEFAULT_ROOM = {"width": 460, "depth": 360, "height": 280}
DEFAULT_COMPASS = {"x": 255, "y": 185, "rotation": 0, "show": True}
DEFAULT_VOID = {"x": 370, "y": 240, "w": 90, "d": 120}

DEFAULT_ITEMS = [
    # 一般家具 (item_type: "furniture", z 預設為 0 貼地)
    {"id": "bed", "name": "床", "item_type": "furniture", "x": 200, "y": 140, "z": 0, "w": 152, "d": 195, "h": 55, "rot": 0, "color": "#FAD785", "texture": "", "scenery": ""},
    {"id": "stand_l", "name": "床頭櫃(左)", "item_type": "furniture", "x": 175, "y": 295, "z": 0, "w": 25, "d": 40, "h": 45, "rot": 0, "color": "#FAD785", "texture": "", "scenery": ""},
    {"id": "stand_r", "name": "床頭櫃(右)", "item_type": "furniture", "x": 352, "y": 295, "z": 0, "w": 25, "d": 40, "h": 45, "rot": 0, "color": "#FAD785", "texture": "", "scenery": ""},
    {"id": "wardrobe_new", "name": "新衣櫃", "item_type": "furniture", "x": 30, "y": 260, "z": 0, "w": 121, "d": 72, "h": 210, "rot": 0, "color": "#A0CB88", "texture": "", "scenery": ""},
    {"id": "desk", "name": "書桌", "item_type": "furniture", "x": 30, "y": 150, "z": 0, "w": 123, "d": 71, "h": 75, "rot": 0, "color": "#8232FA", "texture": "", "scenery": ""},
    {"id": "drybox", "name": "防潮箱", "item_type": "furniture", "x": 265, "y": 50, "z": 0, "w": 40, "d": 45, "h": 50, "rot": 0, "color": "#DC7CF5", "texture": "", "scenery": ""},
    {"id": "wardrobe_white", "name": "白衣櫃", "item_type": "furniture", "x": 305, "y": 50, "z": 0, "w": 60, "d": 55, "h": 190, "rot": 0, "color": "#AADE8D", "texture": "", "scenery": ""},
    {"id": "wardrobe_old", "name": "舊衣櫃", "item_type": "furniture", "x": 365, "y": 50, "z": 0, "w": 120, "d": 51, "h": 200, "rot": 0, "color": "#9EC484", "texture": "", "scenery": ""},
    {"id": "bookcase", "name": "玻書櫃", "item_type": "furniture", "x": 450, "y": 180, "z": 0, "w": 32, "d": 63, "h": 180, "rot": 0, "color": "#DC7CF5", "texture": "", "scenery": ""},
    
    # 附圖底部的兩個橘色矩形框：窗戶與牆壁插座 (具備 Z 軸離地高度，2D 加強顯示，3D 垂直立起且帶富士山窗景)
    {"id": "win_main", "name": "主景觀窗", "item_type": "window", "x": 65, "y": 340, "z": 85, "w": 150, "d": 18, "h": 135, "rot": 0, "color": "#F59E0B", "texture": "", "scenery": FUJI_SVG},
    {"id": "socket_wall", "name": "牆壁插座/小窗", "item_type": "socket", "x": 335, "y": 340, "z": 35, "w": 35, "d": 18, "h": 25, "rot": 0, "color": "#F97316", "texture": "", "scenery": FUJI_SVG}
]

initial_data = {
    "room": DEFAULT_ROOM,
    "compass": DEFAULT_COMPASS,
    "void": DEFAULT_VOID,
    "items": DEFAULT_ITEMS,
    "default_fuji": FUJI_SVG
}

initial_data_json = json.dumps(initial_data)

html_code = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; -webkit-user-select: none; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft JhengHei", sans-serif; background: #0E1117; color: #E0E0E0; overflow: hidden; touch-action: none; }}
    .app-container {{ display: flex; height: 100vh; width: 100vw; position: relative; }}
    
    /* 左側與右側面板 */
    .left-panel {{ width: 320px; background: #16191E; border-right: 1px solid #282C34; display: flex; flex-direction: column; height: 100vh; z-index: 20; transition: transform 0.25s ease; }}
    .center-canvas {{ flex: 1; display: flex; flex-direction: column; position: relative; background: #090B0E; height: 100vh; overflow: hidden; }}
    .right-panel {{ width: 300px; background: #16191E; border-left: 1px solid #282C34; padding: 14px; display: flex; flex-direction: column; height: 100vh; z-index: 20; transition: transform 0.25s ease; }}

    /* 標籤頁切換 (左面板) */
    .tab-bar {{ display: flex; background: #1F232B; border-bottom: 1px solid #282C34; }}
    .tab-btn {{ flex: 1; padding: 12px 4px; font-size: 13px; font-weight: 600; text-align: center; color: #8F96A0; cursor: pointer; border-bottom: 2px solid transparent; }}
    .tab-btn.active {{ color: #FFF; border-bottom: 2px solid #3B82F6; background: #16191E; }}
    .tab-content {{ padding: 14px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }}

    /* 頂部工具列 */
    .toolbar {{ min-height: 52px; background: #16191E; border-bottom: 1px solid #282C34; display: flex; align-items: center; justify-content: space-between; padding: 6px 14px; z-index: 15; flex-wrap: wrap; gap: 8px; }}
    .btn-group {{ display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }}
    button {{ background: #262B35; color: #FFF; border: 1px solid #3A4150; padding: 6px 11px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.15s; display: inline-flex; align-items: center; justify-content: center; gap: 4px; }}
    button:hover {{ background: #353C4A; }}
    button.active {{ background: #2563EB; border-color: #2563EB; color: #FFF; }}
    button.primary {{ background: #059669; border-color: #059669; }}
    button.primary:hover {{ background: #047857; }}
    button.warn {{ background: #D97706; border-color: #D97706; }}
    button.danger {{ background: #DC2626; border-color: #DC2626; }}
    
    .panel-title {{ font-size: 13px; font-weight: 600; color: #FFF; border-bottom: 1px solid #282C34; padding-bottom: 6px; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }}
    .field-group {{ display: flex; flex-direction: column; gap: 4px; margin-bottom: 6px; }}
    .field-group label {{ font-size: 11px; color: #9AA0A6; font-weight: 500; display: flex; justify-content: space-between; }}
    .field-row {{ display: flex; gap: 6px; }}
    .field-row > div {{ flex: 1; display: flex; flex-direction: column; gap: 2px; }}
    .field-row input, select {{ width: 100%; }}
    input[type="text"], input[type="number"], select {{ background: #0E1117; border: 1px solid #333842; color: #FFF; padding: 6px 8px; border-radius: 4px; font-size: 12px; }}
    input[type="color"] {{ width: 100%; height: 32px; border: 1px solid #333842; border-radius: 4px; background: #0E1117; cursor: pointer; }}
    
    /* 新增物件快捷列 */
    .quick-add-bar {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 8px; }}
    .quick-add-bar button {{ padding: 7px 4px; font-size: 11px; }}

    /* 右側清單 */
    .item-list {{ display: flex; flex-direction: column; gap: 6px; margin-top: 6px; flex: 1; overflow-y: auto; padding-right: 2px; }}
    .item-card {{ background: #1F232B; border: 1px solid #2B303A; border-radius: 6px; padding: 8px 10px; cursor: pointer; transition: all 0.15s; display: flex; flex-direction: column; gap: 4px; }}
    .item-card:hover {{ border-color: #3B82F6; background: #252A35; }}
    .item-card.selected {{ border-color: #3B82F6; background: #1E293B; box-shadow: 0 0 0 1px #3B82F6; }}
    .item-card-header {{ display: flex; justify-content: space-between; align-items: center; }}
    .item-card .name {{ font-weight: 600; font-size: 13px; color: #FFF; display: flex; align-items: center; gap: 6px; }}
    .item-card .badge {{ font-size: 10px; padding: 1px 5px; border-radius: 4px; background: #334155; color: #E2E8F0; }}
    .item-card .badge.win {{ background: #B45309; color: #FEF3C7; }}
    .item-card .dims {{ font-size: 11px; color: #94A3B8; }}
    .card-del-btn {{ background: transparent; border: none; color: #94A3B8; padding: 2px 6px; font-size: 13px; border-radius: 4px; }}
    .card-del-btn:hover {{ background: #DC2626; color: #FFF; }}

    /* 畫布視角控制浮動鈕 */
    .view-controls {{ position: absolute; top: 62px; left: 12px; display: flex; gap: 6px; z-index: 12; background: rgba(22,25,30,0.88); padding: 5px; border-radius: 8px; border: 1px solid #282C34; backdrop-filter: blur(4px); flex-wrap: wrap; }}
    .view-controls button {{ padding: 5px 9px; font-size: 11px; }}

    #canvas-container, #three-container {{ width: 100%; height: calc(100vh - 52px); position: absolute; top: 52px; left: 0; touch-action: none; }}
    #three-container {{ display: none; }}

    /* 手機版響應式抽屜導覽 */
    .mobile-nav {{ display: none; position: fixed; bottom: 0; left: 0; width: 100vw; height: 50px; background: #16191E; border-top: 1px solid #282C34; z-index: 30; justify-content: space-around; align-items: center; }}
    @media (max-width: 900px) {{
      .left-panel {{ position: fixed; left: 0; top: 0; height: calc(100vh - 50px); transform: translateX(-100%); width: 88vw; max-width: 340px; box-shadow: 4px 0 15px rgba(0,0,0,0.5); }}
      .left-panel.open {{ transform: translateX(0); }}
      .right-panel {{ position: fixed; right: 0; top: 0; height: calc(100vh - 50px); transform: translateX(100%); width: 88vw; max-width: 320px; box-shadow: -4px 0 15px rgba(0,0,0,0.5); }}
      .right-panel.open {{ transform: translateX(0); }}
      .mobile-nav {{ display: flex; }}
      #canvas-container, #three-container {{ height: calc(100vh - 102px); }}
      .toolbar .hint-text {{ display: none; }}
    }}
  </style>
</head>
<body>

<div class="app-container">
  <!-- 左側面板 -->
  <div class="left-panel" id="left-panel">
    <div class="tab-bar">
      <div class="tab-btn active" id="tab-btn-item" onclick="switchLeftTab('item')">✏️ 物件編輯</div>
      <div class="tab-btn" id="tab-btn-room" onclick="switchLeftTab('room')">🧭 地面與坐向</div>
      <div class="tab-btn" id="tab-btn-save" onclick="switchLeftTab('save')">💾 存檔專案</div>
    </div>

    <!-- 標籤 1：選取物件編輯 + 新增刪除 -->
    <div class="tab-content" id="tab-content-item">
      <div class="panel-title">➕ 快速新增物件</div>
      <div class="quick-add-bar">
        <button onclick="addNewObject('furniture')" style="background:#2563EB;border-color:#2563EB;">🛋️ 新增家具</button>
        <button onclick="addNewObject('window')" style="background:#D97706;border-color:#D97706;">🪟 新增窗戶</button>
        <button onclick="addNewObject('socket')" style="background:#EA580C;border-color:#EA580C;">🔌 新增插座</button>
      </div>

      <div id="no-selection" style="color: #94A3B8; font-size: 12px; margin: 25px 0; text-align: center; line-height: 1.6; background: #1F232B; padding: 16px; border-radius: 8px; border: 1px dashed #334155;">
        👈 <b>點選畫面或右側清單中的物件</b><br>即可直接修改尺寸、Z軸高度、角度、顏色與窗景圖片
      </div>

      <div id="prop-editor" style="display: none;">
        <div class="panel-title">
          <span>✏️ 編輯選取物件</span>
          <span id="prop-type-badge" style="font-size:11px; color:#F59E0B;"></span>
        </div>

        <div class="field-group">
          <label>名稱與物件類型</label>
          <div class="field-row">
            <input type="text" id="prop-name" style="flex:1.5;">
            <select id="prop-type" style="flex:1;">
              <option value="furniture">一般家具</option>
              <option value="window">景觀窗戶</option>
              <option value="socket">牆壁插座/小窗</option>
            </select>
          </div>
        </div>

        <div class="field-group">
          <label>尺寸：寬度 (W) × 深度/厚度 (D) × 高度 (H) cm</label>
          <div class="field-row">
            <div><span style="font-size:10px;color:#64748B;">寬度 W</span><input type="number" id="prop-w"></div>
            <div><span style="font-size:10px;color:#64748B;">深度 D</span><input type="number" id="prop-d"></div>
            <div><span style="font-size:10px;color:#64748B;">高度 H</span><input type="number" id="prop-h" placeholder="30"></div>
          </div>
        </div>

        <div class="field-group">
          <label>坐標位置：X × Y × <span style="color:#F59E0B;font-weight:bold;">Z (離地高度 cm)</span></label>
          <div class="field-row">
            <div><span style="font-size:10px;color:#64748B;">X 坐標</span><input type="number" id="prop-x"></div>
            <div><span style="font-size:10px;color:#64748B;">Y 坐標</span><input type="number" id="prop-y"></div>
            <div><span style="font-size:10px;color:#F59E0B;">Z 離地高</span><input type="number" id="prop-z"></div>
          </div>
        </div>

        <div class="field-group">
          <label>旋轉角度 (度 °)</label>
          <input type="number" id="prop-rot" min="0" max="360">
        </div>

        <div class="field-group">
          <label>顏色外觀 (調色盤)</label>
          <input type="color" id="prop-color">
        </div>

        <div class="field-group" id="scenery-upload-group" style="display:none; background:#1E293B; padding:8px; border-radius:6px; border:1px solid #3B82F6;">
          <label style="color:#60A5FA; font-weight:600;">🗾 3D 窗戶景色 (預設：富士山美景)</label>
          <input type="file" id="prop-scenery-file" accept="image/*" style="font-size: 11px; color: #CBD5E1; margin-top:4px;">
          <button id="btn-reset-fuji" style="margin-top:6px; font-size:11px; padding:4px 8px;">🗻 恢復預設富士山景</button>
        </div>

        <div class="field-group">
          <label>🎨 上傳物件表面材質 / 貼圖</label>
          <input type="file" id="prop-texture-file" accept="image/*" style="font-size: 11px; color: #8F96A0;">
        </div>

        <div style="display: flex; gap: 8px; margin-top: 10px;">
          <button id="btn-duplicate" style="flex: 1;">📋 複製此物件</button>
          <button id="btn-delete" class="danger" style="flex: 1;">🗑️ 刪除此物件</button>
        </div>
      </div>
    </div>

    <!-- 標籤 2：地面格局與風水坐向設定 (全部即時連動) -->
    <div class="tab-content" id="tab-content-room" style="display: none;">
      <div style="font-size:11px; color:#34D399; margin-bottom:4px;">⚡ 所有數值修改皆為「即時連動」，無需按套用</div>
      <div class="panel-title">🏠 房間地面總體尺寸 (cm)</div>
      <div class="field-group">
        <label>房間總寬度 (X) × 總深度 (Y) × 高度 (Z)</label>
        <div class="field-row">
          <div><span style="font-size:10px;color:#64748B;">寬度 X</span><input type="number" id="room-w" class="live-room-input"></div>
          <div><span style="font-size:10px;color:#64748B;">深度 Y</span><input type="number" id="room-d" class="live-room-input"></div>
          <div><span style="font-size:10px;color:#64748B;">高度 Z</span><input type="number" id="room-h" class="live-room-input"></div>
        </div>
      </div>

      <div class="panel-title" style="margin-top: 8px;">🧭 專家級八方坐向羅盤 (即時連動)</div>
      <div class="field-group" style="flex-direction: row; align-items: center; justify-content: space-between;">
        <label style="margin: 0;">顯示八方羅盤格線</label>
        <input type="checkbox" id="compass-show" class="live-room-input" checked style="cursor: pointer; width:16px; height:16px;">
      </div>
      <div class="field-group">
        <label>羅盤天心十字座標 (X, Y cm)</label>
        <div class="field-row">
          <input type="number" id="compass-x" class="live-room-input">
          <input type="number" id="compass-y" class="live-room-input">
        </div>
      </div>
      <div class="field-group">
        <label><span>坐向旋轉角度 (0°～360°)</span><span id="compass-rot-val">0°</span></label>
        <input type="range" id="compass-rot-slider" min="0" max="360" value="0" style="width:100%;">
        <input type="number" id="compass-rot" class="live-room-input" min="0" max="360">
      </div>

      <div class="panel-title" style="margin-top: 8px;">🔲 右上留白凹位尺寸 (cm)</div>
      <div class="field-group">
        <label>留白寬度 (W) × 留白深度 (D)</label>
        <div class="field-row">
          <input type="number" id="void-w" class="live-room-input">
          <input type="number" id="void-d" class="live-room-input">
        </div>
      </div>
      <div class="field-group">
        <label>留白起始位置 (X, Y)</label>
        <div class="field-row">
          <input type="number" id="void-x" class="live-room-input">
          <input type="number" id="void-y" class="live-room-input">
        </div>
      </div>
    </div>

    <!-- 標籤 3：專案存檔、下載與上傳 -->
    <div class="tab-content" id="tab-content-save" style="display: none;">
      <div class="panel-title">💾 1. 存於 App 內 (瀏覽器本地保存)</div>
      <button id="btn-save-local" class="primary" style="width: 100%; padding:9px;">💾 儲存目前設計至 App</button>
      <button id="btn-load-local" style="width: 100%; padding:9px;">📂 讀取上次儲存的設計</button>

      <div class="panel-title" style="margin-top: 14px;">📁 2. 下載檔案與上傳繼續使用</div>
      <button id="btn-export-file" style="width: 100%; padding:9px; background: #4F46E5; border-color: #4F46E5;">📥 下載設計資料檔 (.json)</button>
      
      <div class="field-group" style="margin-top: 8px; background:#1F232B; padding:10px; border-radius:6px;">
        <label style="color:#FFF;">📤 上傳先前的設計檔 (.json) 繼續編輯</label>
        <input type="file" id="file-import" accept=".json" style="font-size: 11px; color: #8F96A0; margin-top:4px;">
      </div>

      <div style="margin-top: auto; padding-top: 14px;">
        <button id="btn-reset-default" style="width: 100%; background: #475569; border-color: #475569;">🔄 重置回附圖原始預設配置</button>
      </div>
    </div>
  </div>

  <!-- 中間畫布區 -->
  <div class="center-canvas">
    <div class="toolbar">
      <div class="btn-group">
        <button id="btn-mode-2d" class="active">📐 2D 平面配置</button>
        <button id="btn-mode-3d">🧊 3D 立體與窗景視圖</button>
      </div>
      <div class="hint-text" style="font-size: 12px; color: #94A3B8;">
        🖱️ <b>滑鼠左鍵按住空白處拉動</b>即可平移畫面 | 滾輪縮放 | 手機支援單指平移與雙指縮放
      </div>
    </div>

    <!-- 浮動畫布視角按鈕 -->
    <div class="view-controls">
      <button id="btn-zoom-in">➕ 放大</button>
      <button id="btn-zoom-out">➖ 縮小</button>
      <button id="btn-zoom-fit">🔍 適配居中</button>
      <button id="btn-pan-toggle" title="切換強制平移模式">✋ 左鍵拖曳平移: 開啟</button>
    </div>
    
    <div id="canvas-container">
      <canvas id="fabric-canvas"></canvas>
    </div>
    <div id="three-container"></div>
  </div>

  <!-- 右側物件清單 -->
  <div class="right-panel" id="right-panel">
    <div class="panel-title">
      <span>📋 空間物件列表 (點選同步高亮)</span>
      <span id="obj-count" style="font-size: 12px; color: #94A3B8;">0</span>
    </div>
    <div class="quick-add-bar">
      <button onclick="addNewObject('furniture')" style="background:#2563EB;border-color:#2563EB;">+ 家具</button>
      <button onclick="addNewObject('window')" style="background:#D97706;border-color:#D97706;">+ 窗戶</button>
      <button onclick="addNewObject('socket')" style="background:#EA580C;border-color:#EA580C;">+ 插座</button>
    </div>
    <div class="item-list" id="item-list-container"></div>
  </div>

  <!-- 手機版底部導覽列 -->
  <div class="mobile-nav">
    <button onclick="toggleMobilePanel('left')">⚙️ 屬性與坐向</button>
    <button onclick="toggleMobilePanel('canvas')" class="active">📐 畫布視角</button>
    <button onclick="toggleMobilePanel('right')">📋 物件清單</button>
  </div>
</div>

<script>
  let appState = {initial_data_json};
  let activeId = null;
  let canvas, scene, camera, renderer, controls;
  let currentMode = "2D";
  
  // 畫布左鍵平移與手機雙指觸控狀態
  let isDraggingCanvas = false;
  let forcePanMode = false; // 若開啟，連點在物件上也會平移畫布
  let lastClientX = 0, lastClientY = 0;
  let touchStartDist = 0;
  let touchStartZoom = 1;

  // 手機版抽屜開關
  function toggleMobilePanel(target) {{
    const lp = document.getElementById("left-panel");
    const rp = document.getElementById("right-panel");
    if (target === 'left') {{
      lp.classList.toggle("open");
      rp.classList.remove("open");
    }} else if (target === 'right') {{
      rp.classList.toggle("open");
      lp.classList.remove("open");
    }} else {{
      lp.classList.remove("open");
      rp.classList.remove("open");
    }}
  }}

  // 左側標籤頁切換
  function switchLeftTab(tab) {{
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
    document.getElementById("tab-btn-" + tab).classList.add("active");
    document.getElementById("tab-content-" + tab).style.display = "flex";
  }}

  // --- 初始化 Fabric 2D 互動畫布 ---
  function initFabric() {{
    const container = document.getElementById("canvas-container");
    canvas = new fabric.Canvas('fabric-canvas', {{
      width: container.clientWidth,
      height: container.clientHeight,
      backgroundColor: '#0A0C10',
      selection: false, // 關閉框選，讓滑鼠左鍵拉動空白處時直接平移畫面！
      preserveObjectStacking: true
    }});

    // 1. 滾輪縮放
    canvas.on('mouse:wheel', function(opt) {{
      const delta = opt.e.deltaY;
      let zoom = canvas.getZoom();
      zoom *= 0.999 ** delta;
      zoom = Math.min(Math.max(zoom, 0.25), 5);
      canvas.zoomToPoint({{ x: opt.e.offsetX, y: opt.e.offsetY }}, zoom);
      opt.e.preventDefault();
      opt.e.stopPropagation();
    }});

    // 2. 滑鼠左鍵按住空白處拉動平移 (或開啟強制平移模式 / 中鍵 / Alt)
    canvas.on('mouse:down', function(opt) {{
      const evt = opt.e;
      const clickedEmpty = !opt.target || !opt.target.itemId;
      if (clickedEmpty || forcePanMode || evt.button === 1 || evt.altKey) {{
        isDraggingCanvas = true;
        if (evt.touches && evt.touches.length === 1) {{
          lastClientX = evt.touches[0].clientX;
          lastClientY = evt.touches[0].clientY;
        }} else {{
          lastClientX = evt.clientX;
          lastClientY = evt.clientY;
        }}
      }}
    }});

    canvas.on('mouse:move', function(opt) {{
      if (!isDraggingCanvas) return;
      const evt = opt.e;
      let currX, currY;
      if (evt.touches && evt.touches.length === 1) {{
        currX = evt.touches[0].clientX;
        currY = evt.touches[0].clientY;
      }} else if (!evt.touches) {{
        currX = evt.clientX;
        currY = evt.clientY;
      }} else {{
        return;
      }}
      const vpt = canvas.viewportTransform;
      vpt[4] += currX - lastClientX;
      vpt[5] += currY - lastClientY;
      canvas.requestRenderAll();
      lastClientX = currX;
      lastClientY = currY;
    }});

    canvas.on('mouse:up', function() {{
      isDraggingCanvas = false;
    }});

    // 3. 手機雙指捏合縮放 (Pinch to Zoom) 與單指平移支援
    const upperCanvas = canvas.upperCanvasEl;
    upperCanvas.addEventListener('touchstart', function(e) {{
      if (e.touches.length === 2) {{
        isDraggingCanvas = false;
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        touchStartDist = Math.hypot(dx, dy);
        touchStartZoom = canvas.getZoom();
      }}
    }}, {{ passive: false }});

    upperCanvas.addEventListener('touchmove', function(e) {{
      if (e.touches.length === 2 && touchStartDist > 0) {{
        e.preventDefault();
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const dist = Math.hypot(dx, dy);
        let newZoom = touchStartZoom * (dist / touchStartDist);
        newZoom = Math.min(Math.max(newZoom, 0.25), 4.5);
        const centerX = (e.touches[0].clientX + e.touches[1].clientX) / 2;
        const centerY = (e.touches[0].clientY + e.touches[1].clientY) / 2;
        canvas.zoomToPoint({{ x: centerX, y: centerY }}, newZoom);
      }}
    }}, {{ passive: false }});

    // 物件選取與變形事件
    canvas.on('selection:created', onObjectSelected);
    canvas.on('selection:updated', onObjectSelected);
    canvas.on('selection:cleared', onObjectDeselected);
    canvas.on('object:modified', onObjectModified);
    canvas.on('object:moving', onObjectModified);
    canvas.on('object:scaling', onObjectModified);
    canvas.on('object:rotating', onObjectModified);

    initRoomFormValues();
    renderFullScene();
    zoomToFit();
  }}

  // 繪製 2D 場景（地面、留白、坐向盤、家具、高辨識度窗戶與插座）
  function renderFullScene() {{
    canvas.clear();
    canvas.backgroundColor = '#0A0C10';

    // 1. 房間地面可使用區域 (藍色底盤 + 尺寸標尺文字)
    const rw = appState.room.width;
    const rd = appState.room.depth;
    const floor = new fabric.Rect({{
      left: 0, top: 0, width: rw, height: rd,
      fill: '#5089C6', stroke: '#38BDF8', strokeWidth: 2,
      selectable: false, evented: false
    }});
    canvas.add(floor);

    // 房間總寬深標註
    const dimTop = new fabric.Text(`◀ 總寬 ${{rw}} cm ▶`, {{
      left: rw / 2, top: -18, fontSize: 13, fill: '#94A3B8', originX: 'center', selectable: false, evented: false
    }});
    const dimLeft = new fabric.Text(`◀ 總深 ${{rd}} cm ▶`, {{
      left: -18, top: rd / 2, fontSize: 13, fill: '#94A3B8', originX: 'center', angle: -90, selectable: false, evented: false
    }});
    canvas.add(dimTop, dimLeft);

    // 2. 右上留白凹位 (白色留白)
    const v = appState.void;
    const voidBox = new fabric.Rect({{
      left: v.x, top: v.y, width: v.w, height: v.d,
      fill: '#FFFFFF', stroke: '#CBD5E1', strokeWidth: 1.5,
      selectable: false, evented: false
    }});
    const voidText = new fabric.Text(`留白區\n${{v.w}}×${{v.d}}`, {{
      left: v.x + v.w / 2, top: v.y + v.d / 2, fontSize: 12, fill: '#475569',
      originX: 'center', originY: 'center', textAlign: 'center', selectable: false, evented: false
    }});
    canvas.add(voidBox, voidText);

    // 3. 專家級八方風水／坐向羅盤盤面
    if (appState.compass.show) {{
      renderExpertCompass();
    }}

    // 4. 繪製所有家具、窗戶與插座
    appState.items.forEach(item => createFabricItem(item));

    // 若原本有選中的物件，保持選中狀態
    if (activeId) {{
      const g = canvas.getObjects().find(o => o.itemId === activeId);
      if (g) canvas.setActiveObject(g);
    }}

    renderRightPanel();
    canvas.requestRenderAll();
    if (currentMode === "3D" && renderer) updateThreeScene();
  }}

  // 專家級八方羅盤渲染
  function renderExpertCompass() {{
    const cx = appState.compass.x;
    const cy = appState.compass.y;
    const rot = appState.compass.rotation || 0;
    const radius = Math.max(appState.room.width, appState.room.depth) * 0.72;

    // 同心測距圓環
    [radius * 0.25, radius * 0.5, radius * 0.75, radius].forEach((r, idx) => {{
      canvas.add(new fabric.Circle({{
        left: cx - r, top: cy - r, radius: r,
        fill: 'transparent',
        stroke: idx === 3 ? 'rgba(255, 255, 255, 0.45)' : 'rgba(255, 255, 255, 0.16)',
        strokeWidth: idx === 3 ? 1.8 : 1,
        strokeDashArray: idx % 2 === 1 ? [5, 5] : null,
        selectable: false, evented: false
      }}));
    }});

    // 附圖方位：東在左 (180°), 北在下 (90° Canvas Y向下為正), 西在右 (0°), 南在上 (270°)
    const directions = [
      {{ deg: 0, label: "正西 [兌]", primary: true }},
      {{ deg: 45, label: "西北 [乾]", primary: false }},
      {{ deg: 90, label: "正北 [坎]", primary: true }},
      {{ deg: 135, label: "東北 [艮]", primary: false }},
      {{ deg: 180, label: "正東 [震]", primary: true }},
      {{ deg: 225, label: "東南 [巽]", primary: false }},
      {{ deg: 270, label: "正南 [離]", primary: true }},
      {{ deg: 315, label: "西南 [坤]", primary: false }}
    ];

    directions.forEach(dir => {{
      const totalDeg = dir.deg + rot;
      const rad = totalDeg * Math.PI / 180;
      const ex = cx + radius * Math.cos(rad);
      const ey = cy + radius * Math.sin(rad);

      canvas.add(new fabric.Line([cx, cy, ex, ey], {{
        stroke: dir.primary ? 'rgba(255, 255, 255, 0.8)' : 'rgba(255, 255, 255, 0.35)',
        strokeWidth: dir.primary ? 2.2 : 1.2,
        selectable: false, evented: false
      }}));

      const tx = cx + (radius + 24) * Math.cos(rad);
      const ty = cy + (radius + 24) * Math.sin(rad);
      canvas.add(new fabric.Text(dir.label, {{
        left: tx, top: ty,
        fontSize: dir.primary ? 14 : 11,
        fontWeight: dir.primary ? 'bold' : 'normal',
        fill: dir.primary ? '#F3E8FF' : '#CBD5E1',
        backgroundColor: dir.primary ? 'rgba(107, 33, 168, 0.75)' : 'rgba(15, 23, 42, 0.65)',
        originX: 'center', originY: 'center',
        selectable: false, evented: false
      }}));
    }});

    canvas.add(new fabric.Circle({{
      left: cx - 5, top: cy - 5, radius: 5,
      fill: '#C084FC', stroke: '#FFFFFF', strokeWidth: 2,
      selectable: false, evented: false
    }}));
  }}

  // 建立 2D 物件（針對窗戶與插座做高辨識度視覺強化，不再只是一條細線）
  function createFabricItem(item) {{
    const isWallItem = item.item_type === "window" || item.item_type === "socket";
    // 在 2D 顯示時，確保窗戶/插座最小視覺厚度至少 16cm，方便看清楚與點選拖拉
    const visualD = isWallItem ? Math.max(item.d, 16) : item.d;

    const rect = new fabric.Rect({{
      width: item.w,
      height: visualD,
      fill: item.color,
      stroke: isWallItem ? '#FEF08A' : '#1E293B',
      strokeWidth: isWallItem ? 2.5 : 1.5,
      strokeDashArray: item.item_type === "socket" ? [4, 2] : null,
      originX: 'center', originY: 'center'
    }});

    const subElements = [rect];

    if (isWallItem) {{
      // 加上工程立面窗框中線與高對比膠囊標籤 (顯示名稱 + Z軸離地高)
      const midLine = new fabric.Line([-item.w/2 + 4, 0, item.w/2 - 4, 0], {{
        stroke: '#FFFFFF', strokeWidth: 2, originX: 'center', originY: 'center'
      }});
      const icon = item.item_type === "window" ? "🪟" : "🔌";
      const zText = `${{icon}} ${{item.name}} (Z:${{item.z || 0}}cm)`;
      const badge = new fabric.Text(zText, {{
        fontSize: 11,
        fontWeight: 'bold',
        fill: '#FEF3C7',
        backgroundColor: 'rgba(180, 83, 9, 0.92)',
        originX: 'center', originY: 'center',
        top: -visualD / 2 - 11
      }});
      subElements.push(midLine, badge);
    }} else {{
      const label = `${{item.name}}\n${{Math.round(item.w)}}×${{Math.round(item.d)}}`;
      const text = new fabric.Text(label, {{
        fontSize: 12,
        fill: '#FFFFFF',
        originX: 'center', originY: 'center',
        textAlign: 'center'
      }});
      subElements.push(text);
    }}

    const group = new fabric.Group(subElements, {{
      left: item.x + item.w / 2,
      top: item.y + visualD / 2,
      angle: item.rot || 0,
      originX: 'center', originY: 'center',
      itemId: item.id
    }});

    group.setControlsVisibility({{
      mt: true, mb: true, ml: true, mr: true,
      tl: true, tr: true, bl: true, br: true,
      mtr: true
    }});

    if (item.texture && !isWallItem) {{
      fabric.Image.fromURL(item.texture, function(img) {{
        img.scaleToWidth(item.w);
        img.scaleToHeight(item.d);
        const pattern = new fabric.Pattern({{ source: img.getElement(), repeat: 'repeat' }});
        rect.set('fill', pattern);
        canvas.requestRenderAll();
      }});
    }}

    canvas.add(group);
  }}

  // --- 選取與修改雙向連動 ---
  function onObjectSelected(e) {{
    const target = e.selected ? e.selected[0] : null;
    if (!target || !target.itemId) return;
    activeId = target.itemId;
    switchLeftTab('item');
    updateLeftItemPanel();
    highlightRightPanel();
  }}

  function onObjectDeselected() {{
    activeId = null;
    document.getElementById("no-selection").style.display = "block";
    document.getElementById("prop-editor").style.display = "none";
    highlightRightPanel();
  }}

  function onObjectModified(e) {{
    const target = e.target;
    if (!target || !target.itemId) return;
    const item = appState.items.find(i => i.id === target.itemId);
    if (!item) return;

    const baseRect = target.item(0);
    const actualW = Math.max(10, Math.round(baseRect.width * target.scaleX));
    const actualD = Math.max(8, Math.round(baseRect.height * target.scaleY));

    item.w = actualW;
    item.d = actualD;
    item.rot = Math.round((target.angle % 360 + 360) % 360);
    item.x = Math.round(target.left - actualW / 2);
    item.y = Math.round(target.top - actualD / 2);

    // 重新渲染該物件以保持標籤字體清晰不變形
    renderFullScene();
    updateLeftItemPanel();
  }}

  function updateLeftItemPanel() {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;

    document.getElementById("no-selection").style.display = "none";
    document.getElementById("prop-editor").style.display = "block";

    const typeNames = {{ furniture: "🛋️ 一般家具", window: "🪟 景觀窗戶 (3D立面)", socket: "🔌 牆壁插座 (3D立面)" }};
    document.getElementById("prop-type-badge").innerText = typeNames[item.item_type || "furniture"];

    document.getElementById("prop-name").value = item.name;
    document.getElementById("prop-type").value = item.item_type || "furniture";
    document.getElementById("prop-w").value = Math.round(item.w);
    document.getElementById("prop-d").value = Math.round(item.d);
    document.getElementById("prop-h").value = item.h || 30;
    document.getElementById("prop-x").value = Math.round(item.x);
    document.getElementById("prop-y").value = Math.round(item.y);
    document.getElementById("prop-z").value = Math.round(item.z || 0);
    document.getElementById("prop-rot").value = item.rot || 0;
    document.getElementById("prop-color").value = item.color;

    // 若為窗戶或插座，顯示窗景上傳區塊
    const sceneryGroup = document.getElementById("scenery-upload-group");
    sceneryGroup.style.display = (item.item_type === "window" || item.item_type === "socket") ? "flex" : "none";
  }}

  // 左側物件屬性即時輸入綁定
  ["prop-name", "prop-type", "prop-w", "prop-d", "prop-h", "prop-x", "prop-y", "prop-z", "prop-rot", "prop-color"].forEach(id => {{
    document.getElementById(id).addEventListener("input", () => {{
      const item = appState.items.find(i => i.id === activeId);
      if (!item) return;
      item.name = document.getElementById("prop-name").value;
      item.item_type = document.getElementById("prop-type").value;
      item.w = parseFloat(document.getElementById("prop-w").value) || 10;
      item.d = parseFloat(document.getElementById("prop-d").value) || 10;
      item.h = parseFloat(document.getElementById("prop-h").value) || 30;
      item.x = parseFloat(document.getElementById("prop-x").value) || 0;
      item.y = parseFloat(document.getElementById("prop-y").value) || 0;
      item.z = parseFloat(document.getElementById("prop-z").value) || 0;
      item.rot = parseFloat(document.getElementById("prop-rot").value) || 0;
      if (id === "prop-color") {{
        item.color = document.getElementById("prop-color").value;
        item.texture = "";
      }}
      if (id === "prop-type" && (item.item_type === "window" || item.item_type === "socket") && !item.scenery) {{
        item.scenery = appState.default_fuji;
      }}
      updateLeftItemPanel();
      renderFullScene();
    }});
  }});

  // 上傳自訂 3D 窗景圖片
  document.getElementById("prop-scenery-file").addEventListener("change", function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(f) {{
      const item = appState.items.find(i => i.id === activeId);
      if (!item) return;
      item.scenery = f.target.result;
      if (currentMode === "3D" && renderer) updateThreeScene();
      alert("✅ 已更新窗戶景色！切換至 3D 視圖即可觀賞。");
    }};
    reader.readAsDataURL(file);
  }});

  document.getElementById("btn-reset-fuji").addEventListener("click", () => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.scenery = appState.default_fuji;
    if (currentMode === "3D" && renderer) updateThreeScene();
  }});

  // 上傳一般表面材質
  document.getElementById("prop-texture-file").addEventListener("change", function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(f) {{
      const item = appState.items.find(i => i.id === activeId);
      if (!item) return;
      item.texture = f.target.result;
      renderFullScene();
    }};
    reader.readAsDataURL(file);
  }});

  // --- 新增、複製、刪除功能 ---
  function addNewObject(type) {{
    let newItem;
    if (type === 'window') {{
      newItem = {{
        id: "win_" + Date.now(), name: "新景觀窗", item_type: "window",
        x: 150, y: 340, z: 85, w: 120, d: 18, h: 130, rot: 0,
        color: "#F59E0B", texture: "", scenery: appState.default_fuji
      }};
    }} else if (type === 'socket') {{
      newItem = {{
        id: "soc_" + Date.now(), name: "牆壁插座", item_type: "socket",
        x: 280, y: 340, z: 30, w: 30, d: 16, h: 20, rot: 0,
        color: "#F97316", texture: "", scenery: appState.default_fuji
      }};
    }} else {{
      newItem = {{
        id: "item_" + Date.now(), name: "新家具", item_type: "furniture",
        x: 120, y: 120, z: 0, w: 60, d: 50, h: 30, rot: 0,
        color: "#38BDF8", texture: "", scenery: ""
      }};
    }}
    appState.items.push(newItem);
    activeId = newItem.id;
    renderFullScene();
    selectItemById(newItem.id);
  }}

  function deleteItemById(id, evt) {{
    if (evt) evt.stopPropagation();
    appState.items = appState.items.filter(i => i.id !== id);
    if (activeId === id) {{
      activeId = null;
      onObjectDeselected();
    }}
    renderFullScene();
  }}

  document.getElementById("btn-delete").addEventListener("click", () => {{
    if (activeId) deleteItemById(activeId);
  }});

  document.getElementById("btn-duplicate").addEventListener("click", () => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    const copy = JSON.parse(JSON.stringify(item));
    copy.id = "item_" + Date.now();
    copy.name = item.name + " (複本)";
    copy.x += 20; copy.y += 20;
    appState.items.push(copy);
    activeId = copy.id;
    renderFullScene();
    selectItemById(copy.id);
  }});

  // --- 地面格局與坐向「即時連動」綁定 ---
  function initRoomFormValues() {{
    document.getElementById("room-w").value = appState.room.width;
    document.getElementById("room-d").value = appState.room.depth;
    document.getElementById("room-h").value = appState.room.height;

    document.getElementById("compass-show").checked = appState.compass.show;
    document.getElementById("compass-x").value = appState.compass.x;
    document.getElementById("compass-y").value = appState.compass.y;
    document.getElementById("compass-rot").value = appState.compass.rotation || 0;
    document.getElementById("compass-rot-slider").value = appState.compass.rotation || 0;
    document.getElementById("compass-rot-val").innerText = (appState.compass.rotation || 0) + "°";

    document.getElementById("void-w").value = appState.void.w;
    document.getElementById("void-d").value = appState.void.d;
    document.getElementById("void-x").value = appState.void.x;
    document.getElementById("void-y").value = appState.void.y;
  }}

  function syncRoomFromInputs() {{
    appState.room.width = parseFloat(document.getElementById("room-w").value) || 400;
    appState.room.depth = parseFloat(document.getElementById("room-d").value) || 300;
    appState.room.height = parseFloat(document.getElementById("room-h").value) || 280;

    appState.compass.show = document.getElementById("compass-show").checked;
    appState.compass.x = parseFloat(document.getElementById("compass-x").value) || 200;
    appState.compass.y = parseFloat(document.getElementById("compass-y").value) || 150;
    appState.compass.rotation = parseFloat(document.getElementById("compass-rot").value) || 0;
    document.getElementById("compass-rot-slider").value = appState.compass.rotation;
    document.getElementById("compass-rot-val").innerText = appState.compass.rotation + "°";

    appState.void.w = parseFloat(document.getElementById("void-w").value) || 0;
    appState.void.d = parseFloat(document.getElementById("void-d").value) || 0;
    appState.void.x = parseFloat(document.getElementById("void-x").value) || 0;
    appState.void.y = parseFloat(document.getElementById("void-y").value) || 0;

    renderFullScene();
  }}

  document.querySelectorAll(".live-room-input").forEach(el => {{
    el.addEventListener("input", syncRoomFromInputs);
    el.addEventListener("change", syncRoomFromInputs);
  }});

  document.getElementById("compass-rot-slider").addEventListener("input", e => {{
    document.getElementById("compass-rot").value = e.target.value;
    syncRoomFromInputs();
  }});

  // --- 右側物件清單 (附帶直接刪除鈕與類別標籤) ---
  function renderRightPanel() {{
    const container = document.getElementById("item-list-container");
    document.getElementById("obj-count").innerText = `共 ${{appState.items.length}} 項`;
    container.innerHTML = "";

    appState.items.forEach(item => {{
      const card = document.createElement("div");
      card.className = "item-card" + (item.id === activeId ? " selected" : "");
      card.onclick = () => selectItemById(item.id);

      const isWall = item.item_type === "window" || item.item_type === "socket";
      const badgeText = item.item_type === "window" ? "🪟 窗戶" : (item.item_type === "socket" ? "🔌 插座" : "家具");
      const hVal = item.h || 30;
      const zVal = item.z || 0;

      card.innerHTML = `
        <div class="item-card-header">
          <div class="name">
            <span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${{item.color}};border:1px solid #fff;"></span>
            <span>${{item.name}}</span>
            <span class="badge ${{isWall ? 'win' : ''}}">${{badgeText}}</span>
          </div>
          <button class="card-del-btn" title="刪除此物件" onclick="deleteItemById('${{item.id}}', event)">🗑️</button>
        </div>
        <div class="dims">
          尺寸: ${{Math.round(item.w)}}×${{Math.round(item.d)}}×${{hVal}} cm | 離地 Z: <b>${{zVal}}cm</b> | ${{item.rot || 0}}°
        </div>
      `;
      container.appendChild(card);
    }});
  }}

  function highlightRightPanel() {{
    document.querySelectorAll(".item-card").forEach((card, idx) => {{
      if (appState.items[idx] && appState.items[idx].id === activeId) {{
        card.classList.add("selected");
        card.scrollIntoView({{ behavior: "smooth", block: "nearest" }});
      }} else {{
        card.classList.remove("selected");
      }}
    }});
  }}

  function selectItemById(id) {{
    activeId = id;
    const group = canvas.getObjects().find(o => o.itemId === id);
    if (group) {{
      canvas.setActiveObject(group);
      canvas.requestRenderAll();
    }}
    switchLeftTab('item');
    updateLeftItemPanel();
    highlightRightPanel();
  }}

  // --- 視角控制按鈕 ---
  function zoomToFit() {{
    const rw = appState.room.width;
    const rd = appState.room.depth;
    const container = document.getElementById("canvas-container");
    const cw = container.clientWidth - 90;
    const ch = container.clientHeight - 90;

    const scale = Math.min(cw / rw, ch / rd, 1.8);
    const offsetX = (container.clientWidth - rw * scale) / 2;
    const offsetY = (container.clientHeight - rd * scale) / 2;

    canvas.setViewportTransform([scale, 0, 0, scale, offsetX, offsetY]);
    canvas.requestRenderAll();
  }}

  document.getElementById("btn-zoom-fit").addEventListener("click", zoomToFit);
  document.getElementById("btn-zoom-in").addEventListener("click", () => {{
    canvas.setZoom(Math.min(canvas.getZoom() * 1.2, 5));
  }});
  document.getElementById("btn-zoom-out").addEventListener("click", () => {{
    canvas.setZoom(Math.max(canvas.getZoom() / 1.2, 0.25));
  }});
  document.getElementById("btn-pan-toggle").addEventListener("click", function() {{
    forcePanMode = !forcePanMode;
    this.innerText = forcePanMode ? "✋ 強制平移模式: 開啟中" : "✋ 左鍵拖曳平移: 開啟";
    this.classList.toggle("active", forcePanMode);
  }});

  // --- 存檔與匯入匯出 ---
  document.getElementById("btn-save-local").addEventListener("click", () => {{
    localStorage.setItem("room_planner_v3", JSON.stringify(appState));
    alert("✅ 已成功儲存於 App 本地記憶中！");
  }});

  document.getElementById("btn-load-local").addEventListener("click", () => {{
    const saved = localStorage.getItem("room_planner_v3");
    if (saved) {{
      appState = JSON.parse(saved);
      initRoomFormValues();
      renderFullScene();
      zoomToFit();
      alert("✅ 已成功載入儲存的設計！");
    }} else {{
      alert("⚠️ 尚未找到本地存檔紀錄！");
    }}
  }});

  document.getElementById("btn-export-file").addEventListener("click", () => {{
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(appState, null, 2));
    const a = document.createElement('a');
    a.setAttribute("href", dataStr);
    a.setAttribute("download", "room_design_" + new Date().toISOString().slice(0, 10) + ".json");
    document.body.appendChild(a);
    a.click();
    a.remove();
  }});

  document.getElementById("file-import").addEventListener("change", function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(evt) {{
      try {{
        appState = JSON.parse(evt.target.result);
        initRoomFormValues();
        renderFullScene();
        zoomToFit();
        alert("✅ 專案檔案載入成功！");
      }} catch(err) {{
        alert("❌ 檔案格式錯誤！");
      }}
    }};
    reader.readAsText(file);
  }});

  document.getElementById("btn-reset-default").addEventListener("click", () => {{
    if (confirm("確定要重置回附圖原始預設配置嗎？")) {{
      appState = JSON.parse(JSON.stringify({initial_data_json}));
      initRoomFormValues();
      renderFullScene();
      zoomToFit();
    }}
  }});

  // --- 3D 立體全景與富士山窗景渲染 (Three.js) ---
  function initThree() {{
    const container = document.getElementById("three-container");
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0B0F17);

    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 1, 5000);
    camera.position.set(appState.room.width / 2, 420, appState.room.depth + 360);

    renderer = new THREE.WebGLRenderer({{ antialias: true }});
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(appState.room.width / 2, 60, appState.room.depth / 2);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.65);
    dirLight.position.set(250, 500, 300);
    scene.add(dirLight);

    animateThree();
  }}

  function updateThreeScene() {{
    if (!scene) return;
    while (scene.children.length > 2) {{
      scene.remove(scene.children[scene.children.length - 1]);
    }}

    const rw = appState.room.width;
    const rd = appState.room.depth;
    const rh = appState.room.height;

    // 1. 地板
    const floorGeo = new THREE.PlaneGeometry(rw, rd);
    const floorMat = new THREE.MeshLambertMaterial({{ color: 0x5089C6, side: THREE.DoubleSide }});
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(rw / 2, 0, rd / 2);
    scene.add(floor);

    // 房間半透明立體牆面外框線 (幫助清楚辨識窗戶與插座在牆上的 Z 軸立體位置)
    const wallBoxGeo = new THREE.BoxGeometry(rw, rh, rd);
    const wallEdges = new THREE.EdgesGeometry(wallBoxGeo);
    const wallLine = new THREE.LineSegments(wallEdges, new THREE.LineBasicMaterial({{ color: 0x334155 }}));
    wallLine.position.set(rw / 2, rh / 2, rd / 2);
    scene.add(wallLine);

    // 2. 右上留白區
    const v = appState.void;
    const voidGeo = new THREE.PlaneGeometry(v.w, v.d);
    const voidMat = new THREE.MeshBasicMaterial({{ color: 0xffffff, side: THREE.DoubleSide }});
    const voidMesh = new THREE.Mesh(voidGeo, voidMat);
    voidMesh.rotation.x = -Math.PI / 2;
    voidMesh.position.set(v.x + v.w / 2, 0.3, v.y + v.d / 2);
    scene.add(voidMesh);

    // 3. 3D 坐向羅盤線
    if (appState.compass.show) {{
      const cx = appState.compass.x;
      const cy = appState.compass.y;
      const rot = appState.compass.rotation || 0;
      const radius = Math.max(rw, rd) * 0.7;

      for (let ang = 0; ang < 360; ang += 45) {{
        const rad = (ang + rot) * Math.PI / 180;
        const pts = [
          new THREE.Vector3(cx, 1, cy),
          new THREE.Vector3(cx + radius * Math.cos(rad), 1, cy + radius * Math.sin(rad))
        ];
        const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
        const lineMat = new THREE.LineBasicMaterial({{ color: 0xC084FC }});
        scene.add(new THREE.Line(lineGeo, lineMat));
      }}
    }}

    // 4. 繪製所有家具、立體窗戶(含富士山美景)與牆壁插座(含Z軸離地高度)
    const texLoader = new THREE.TextureLoader();

    appState.items.forEach(item => {{
      const h = item.h || 30;
      const zBottom = item.z || 0; // Z軸離地高度
      const isWindow = item.item_type === "window";
      const isSocket = item.item_type === "socket";

      if (isWindow) {{
        // 建立立體窗框 + 富士山窗景平面
        const winGroup = new THREE.Group();
        const frameDepth = Math.max(item.d, 8);

        // 窗框外圍
        const frameGeo = new THREE.BoxGeometry(item.w, h, frameDepth);
        const frameEdges = new THREE.EdgesGeometry(frameGeo);
        const frameLine = new THREE.LineSegments(frameEdges, new THREE.LineBasicMaterial({{ color: 0xF59E0B, linewidth: 3 }}));
        winGroup.add(frameLine);

        // 窗景圖片本體 (預設富士山美景或使用者上傳圖片)
        const sceneryUrl = item.scenery || appState.default_fuji;
        const sceneryTex = texLoader.load(sceneryUrl);
        const glassGeo = new THREE.BoxGeometry(item.w - 4, h - 4, frameDepth * 0.6);
        const glassMat = new THREE.MeshBasicMaterial({{ map: sceneryTex }});
        const glassMesh = new THREE.Mesh(glassGeo, glassMat);
        winGroup.add(glassMesh);

        winGroup.rotation.y = -(item.rot || 0) * Math.PI / 180;
        winGroup.position.set(item.x + item.w / 2, zBottom + h / 2, item.y + item.d / 2);
        scene.add(winGroup);

      }} else {{
        // 一般家具或牆壁插座 (依照 zBottom + h/2 定位立體高度)
        const geo = new THREE.BoxGeometry(item.w, h, item.d);
        let mat;
        if (item.texture) {{
          const tex = texLoader.load(item.texture);
          mat = new THREE.MeshLambertMaterial({{ map: tex }});
        }} else {{
          mat = new THREE.MeshLambertMaterial({{ color: item.color }});
        }}
        const mesh = new THREE.Mesh(geo, mat);

        // 加上立體邊線讓結構更清晰
        const edges = new THREE.EdgesGeometry(geo);
        const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({{ color: isSocket ? 0xFEF08A : 0x1E293B }}));
        mesh.add(line);

        mesh.rotation.y = -(item.rot || 0) * Math.PI / 180;
        mesh.position.set(item.x + item.w / 2, zBottom + h / 2, item.y + item.d / 2);
        scene.add(mesh);
      }}
    }});
  }}

  function animateThree() {{
    requestAnimationFrame(animateThree);
    if (controls) controls.update();
    if (renderer && scene && camera) renderer.render(scene, camera);
  }}

  // 2D / 3D 模式切換
  document.getElementById("btn-mode-2d").addEventListener("click", () => {{
    currentMode = "2D";
    document.getElementById("btn-mode-2d").classList.add("active");
    document.getElementById("btn-mode-3d").classList.remove("active");
    document.getElementById("canvas-container").style.display = "block";
    document.getElementById("three-container").style.display = "none";
  }});

  document.getElementById("btn-mode-3d").addEventListener("click", () => {{
    currentMode = "3D";
    document.getElementById("btn-mode-3d").classList.add("active");
    document.getElementById("btn-mode-2d").classList.remove("active");
    document.getElementById("canvas-container").style.display = "none";
    document.getElementById("three-container").style.display = "block";
    if (!renderer) initThree();
    updateThreeScene();
  }});

  window.addEventListener("resize", () => {{
    const c2d = document.getElementById("canvas-container");
    if (canvas && c2d.clientWidth > 0) {{
      canvas.setWidth(c2d.clientWidth);
      canvas.setHeight(c2d.clientHeight);
    }}
    const c3d = document.getElementById("three-container");
    if (renderer && camera && c3d.clientWidth > 0) {{
      camera.aspect = c3d.clientWidth / c3d.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(c3d.clientWidth, c3d.clientHeight);
    }}
  }});

  window.addEventListener("load", initFabric);
</script>
</body>
</html>
"""

components.html(html_code, height=960, scrolling=False)
