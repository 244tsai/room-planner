import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(
    page_title="專業臥室空間設計 & 九宮飛星風水系統",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    header { display: none !important; }
    footer { display: none !important; }
</style>
""", unsafe_allow_html=True)

# 預設富士山美景 SVG Data URI
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
<ellipse cx='180' cy='240' rx='140' ry='22' fill='%23ffffff' opacity='0.25'/>
<ellipse cx='650' cy='210' rx='160' ry='18' fill='%23ffffff' opacity='0.2'/>
<path d='M 80 360 Q 290 270 355 110 L 445 110 Q 510 270 720 360 Z' fill='url(%23fuji)'/>
<path d='M 355 110 L 445 110 Q 470 175 492 215 L 460 195 L 435 225 L 408 188 L 385 225 L 358 192 L 312 215 Q 332 175 355 110 Z' fill='%23ffffff'/>
<rect y='360' width='800' height='140' fill='url(%23lake)'/>
<path d='M 220 360 Q 340 410 365 465 L 435 465 Q 460 410 580 360 Z' fill='%233b4d71' opacity='0.45'/>
<path d='M 362 435 L 438 435 L 425 465 L 375 465 Z' fill='%23ffffff' opacity='0.35'/>
<circle cx='90' cy='60' r='35' fill='%23ffb7c5' opacity='0.8'/>
<circle cx='140' cy='40' r='45' fill='%23ffc0cb' opacity='0.85'/>
<circle cx='50' cy='100' r='30' fill='%23ff9ebb' opacity='0.75'/>
</svg>"""

# --- 預設格局、留白處清單、九宮飛星與物件數據 ---
DEFAULT_ROOM = {"width": 460, "depth": 360, "height": 280, "editable": False}
DEFAULT_COMPASS = {
    "x": 255, "y": 185, "rotation": 0, "show": True,
    "show_feixing": False, "feixing_year": 2026
}

# 留白處改為陣列，支援多組新增、編輯、刪除與畫布拖曳
DEFAULT_VOIDS = [
    {"id": "void_1", "name": "留白處 1", "x": 370, "y": 0, "w": 90, "d": 120}
]

# 附圖所有物件預設值 (座標對齊附圖：上方為床與新衣櫃、下方為窗戶/插座/防潮箱/白衣櫃/舊衣櫃)
DEFAULT_ITEMS = [
    {"id": "bed", "name": "床", "item_type": "furniture", "x": 200, "y": 0, "z": 0, "w": 152, "d": 195, "h": 55, "rot": 0, "color": "#FAD785", "texture": "", "scenery": ""},
    {"id": "stand_l", "name": "床頭櫃(左)", "item_type": "furniture", "x": 175, "y": 0, "z": 0, "w": 25, "d": 40, "h": 45, "rot": 0, "color": "#FAD785", "texture": "", "scenery": ""},
    {"id": "stand_r", "name": "床頭櫃(右)", "item_type": "furniture", "x": 352, "y": 0, "z": 0, "w": 25, "d": 40, "h": 45, "rot": 0, "color": "#FAD785", "texture": "", "scenery": ""},
    {"id": "wardrobe_new", "name": "新衣櫃", "item_type": "furniture", "x": 0, "y": 0, "z": 0, "w": 121, "d": 72, "h": 210, "rot": 0, "color": "#A0CB88", "texture": "", "scenery": ""},
    {"id": "desk", "name": "書桌", "item_type": "furniture", "x": 0, "y": 135, "z": 0, "w": 123, "d": 71, "h": 75, "rot": 0, "color": "#8232FA", "texture": "", "scenery": ""},
    {"id": "drybox", "name": "防潮箱", "item_type": "furniture", "x": 235, "y": 315, "z": 0, "w": 40, "d": 45, "h": 50, "rot": 0, "color": "#DC7CF5", "texture": "", "scenery": ""},
    {"id": "wardrobe_white", "name": "白衣櫃", "item_type": "furniture", "x": 275, "y": 305, "z": 0, "w": 60, "d": 55, "h": 190, "rot": 0, "color": "#AADE8D", "texture": "", "scenery": ""},
    {"id": "wardrobe_old", "name": "舊衣櫃", "item_type": "furniture", "x": 335, "y": 299, "z": 0, "w": 120, "d": 61, "h": 200, "rot": 0, "color": "#9EC484", "texture": "", "scenery": ""},
    {"id": "bookcase", "name": "玻書櫃", "item_type": "furniture", "x": 428, "y": 120, "z": 0, "w": 32, "d": 63, "h": 180, "rot": 0, "color": "#DC7CF5", "texture": "", "scenery": ""},
    # 附圖下方兩個橘色矩形框：窗戶與插座 (2D備註與普通物件相同，3D立體渲染)
    {"id": "win_main", "name": "窗戶", "item_type": "window", "x": 35, "y": 348, "z": 85, "w": 135, "d": 12, "h": 130, "rot": 0, "color": "#F59E0B", "texture": "", "scenery": FUJI_SVG},
    {"id": "socket_wall", "name": "插座", "item_type": "socket", "x": 325, "y": 348, "z": 35, "w": 22, "d": 12, "h": 14, "rot": 0, "color": "#F97316", "texture": "", "scenery": ""}
]

initial_data = {
    "room": DEFAULT_ROOM,
    "compass": DEFAULT_COMPASS,
    "voids": DEFAULT_VOIDS,
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
    
    /* 左右側邊欄與中間畫布 */
    .left-panel {{ width: 335px; background: #16191E; border-right: 1px solid #282C34; display: flex; flex-direction: column; height: 100vh; z-index: 20; transition: transform 0.25s ease; }}
    .center-canvas {{ flex: 1; display: flex; flex-direction: column; position: relative; background: #090B0E; height: 100vh; overflow: hidden; }}
    .right-panel {{ width: 300px; background: #16191E; border-left: 1px solid #282C34; padding: 14px; display: flex; flex-direction: column; height: 100vh; z-index: 20; transition: transform 0.25s ease; }}

    /* 左面板標籤頁 */
    .tab-bar {{ display: flex; background: #1F232B; border-bottom: 1px solid #282C34; }}
    .tab-btn {{ flex: 1; padding: 11px 4px; font-size: 12px; font-weight: 600; text-align: center; color: #8F96A0; cursor: pointer; border-bottom: 2px solid transparent; }}
    .tab-btn.active {{ color: #FFF; border-bottom: 2px solid #3B82F6; background: #16191E; }}
    .tab-content {{ padding: 14px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }}

    /* 工具列與按鈕 */
    .toolbar {{ min-height: 50px; background: #16191E; border-bottom: 1px solid #282C34; display: flex; align-items: center; justify-content: space-between; padding: 6px 14px; z-index: 15; flex-wrap: wrap; gap: 8px; }}
    .btn-group {{ display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }}
    button {{ background: #262B35; color: #FFF; border: 1px solid #3A4150; padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.15s; display: inline-flex; align-items: center; justify-content: center; gap: 4px; }}
    button:hover {{ background: #353C4A; }}
    button.active {{ background: #2563EB; border-color: #2563EB; color: #FFF; }}
    button.primary {{ background: #059669; border-color: #059669; }}
    button.primary:hover {{ background: #047857; }}
    button.danger {{ background: #DC2626; border-color: #DC2626; }}
    
    .panel-title {{ font-size: 13px; font-weight: 600; color: #FFF; border-bottom: 1px solid #282C34; padding-bottom: 6px; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }}
    .field-group {{ display: flex; flex-direction: column; gap: 4px; margin-bottom: 6px; }}
    .field-group label {{ font-size: 11px; color: #9AA0A6; font-weight: 500; display: flex; justify-content: space-between; }}
    .field-row {{ display: flex; gap: 6px; }}
    .field-row > div {{ flex: 1; display: flex; flex-direction: column; gap: 2px; }}
    .field-row input, select {{ width: 100%; }}
    input[type="text"], input[type="number"], select {{ background: #0E1117; border: 1px solid #333842; color: #FFF; padding: 6px 8px; border-radius: 4px; font-size: 12px; }}
    input[type="color"] {{ width: 100%; height: 32px; border: 1px solid #333842; border-radius: 4px; background: #0E1117; cursor: pointer; }}
    
    /* 整合新增物件區 */
    .quick-add-box {{ background: #1C2029; border: 1px solid #2E3440; border-radius: 8px; padding: 10px; display: flex; flex-direction: column; gap: 6px; }}
    .quick-add-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }}
    .quick-add-sub {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 5px; }}
    .quick-add-sub button {{ padding: 6px 4px; font-size: 11px; }}

    /* 清單卡片 */
    .item-list {{ display: flex; flex-direction: column; gap: 6px; margin-top: 6px; flex: 1; overflow-y: auto; padding-right: 2px; }}
    .item-card {{ background: #1F232B; border: 1px solid #2B303A; border-radius: 6px; padding: 8px 10px; cursor: pointer; transition: all 0.15s; display: flex; flex-direction: column; gap: 4px; }}
    .item-card:hover {{ border-color: #3B82F6; background: #252A35; }}
    .item-card.selected {{ border-color: #3B82F6; background: #1E293B; box-shadow: 0 0 0 1px #3B82F6; }}
    .item-card-header {{ display: flex; justify-content: space-between; align-items: center; }}
    .item-card .name {{ font-weight: 600; font-size: 13px; color: #FFF; display: flex; align-items: center; gap: 6px; }}
    .item-card .badge {{ font-size: 10px; padding: 1px 5px; border-radius: 4px; background: #334155; color: #E2E8F0; }}
    .item-card .badge.win {{ background: #B45309; color: #FEF3C7; }}
    .item-card .badge.door {{ background: #7C2D12; color: #FFEDD5; }}
    .item-card .dims {{ font-size: 11px; color: #94A3B8; }}
    .card-del-btn {{ background: transparent; border: none; color: #94A3B8; padding: 2px 6px; font-size: 13px; border-radius: 4px; }}
    .card-del-btn:hover {{ background: #DC2626; color: #FFF; }}

    /* 留白處管理小卡 */
    .void-card {{ background: #1F232B; border: 1px solid #334155; border-radius: 6px; padding: 8px; margin-bottom: 6px; display: flex; flex-direction: column; gap: 6px; }}

    /* 畫布視角浮動控制 */
    .view-controls {{ position: absolute; top: 60px; left: 12px; display: flex; gap: 6px; z-index: 12; background: rgba(22,25,30,0.88); padding: 5px; border-radius: 8px; border: 1px solid #282C34; backdrop-filter: blur(4px); flex-wrap: wrap; }}
    .view-controls button {{ padding: 5px 9px; font-size: 11px; }}

    #canvas-container, #three-container {{ width: 100%; height: calc(100vh - 50px); position: absolute; top: 50px; left: 0; touch-action: none; }}
    #three-container {{ display: none; }}

    /* 手機底部導覽 */
    .mobile-nav {{ display: none; position: fixed; bottom: 0; left: 0; width: 100vw; height: 50px; background: #16191E; border-top: 1px solid #282C34; z-index: 30; justify-content: space-around; align-items: center; }}
    @media (max-width: 900px) {{
      .left-panel {{ position: fixed; left: 0; top: 0; height: calc(100vh - 50px); transform: translateX(-100%); width: 88vw; max-width: 340px; box-shadow: 4px 0 15px rgba(0,0,0,0.5); }}
      .left-panel.open {{ transform: translateX(0); }}
      .right-panel {{ position: fixed; right: 0; top: 0; height: calc(100vh - 50px); transform: translateX(100%); width: 88vw; max-width: 320px; box-shadow: -4px 0 15px rgba(0,0,0,0.5); }}
      .right-panel.open {{ transform: translateX(0); }}
      .mobile-nav {{ display: flex; }}
      #canvas-container, #three-container {{ height: calc(100vh - 100px); }}
      .toolbar .hint-text {{ display: none; }}
    }}
  </style>
</head>
<body>

<div class="app-container">
  <!-- 左側面板 -->
  <div class="left-panel" id="left-panel">
    <div class="tab-bar">
      <div class="tab-btn active" id="tab-btn-item" onclick="switchLeftTab('item')">✏️ 物件與門窗</div>
      <div class="tab-btn" id="tab-btn-room" onclick="switchLeftTab('room')">🧭 地面與飛星</div>
      <div class="tab-btn" id="tab-btn-save" onclick="switchLeftTab('save')">💾 存檔專案</div>
    </div>

    <!-- 標籤 1：物件編輯 + 家具/門/窗戶與插座開關整合新增 -->
    <div class="tab-content" id="tab-content-item">
      <div class="quick-add-box">
        <div style="font-size:11px; color:#94A3B8; font-weight:600;">➕ 新增物件（可拖曳至畫面任意處或房間外）</div>
        <div class="quick-add-row">
          <button onclick="addNewObject('furniture')" style="background:#2563EB;border-color:#2563EB;">🛋️ 新增家具</button>
          <button onclick="addNewObject('door')" style="background:#9A3412;border-color:#9A3412;">🚪 新增房門</button>
        </div>
        <div style="font-size:11px; color:#F59E0B; margin-top:2px;">⚡ 牆面立面設施（窗戶 / 插座 / 開關）：</div>
        <div class="quick-add-sub">
          <button onclick="addNewObject('window')" style="background:#D97706;border-color:#D97706;">🪟 窗戶</button>
          <button onclick="addNewObject('socket')" style="background:#EA580C;border-color:#EA580C;">🔌 插座</button>
          <button onclick="addNewObject('switch')" style="background:#0284C7;border-color:#0284C7;">💡 開關</button>
        </div>
      </div>

      <div id="no-selection" style="color: #94A3B8; font-size: 12px; margin: 18px 0; text-align: center; line-height: 1.6; background: #1F232B; padding: 14px; border-radius: 8px; border: 1px dashed #334155;">
        👈 <b>直接點選畫面上或右側清單的物件</b><br>可直接在畫布拖曳移動、拉伸縮放、旋轉，或於此處輸入精準數值
      </div>

      <div id="prop-editor" style="display: none;">
        <div class="panel-title">
          <span>✏️ 編輯選取物件</span>
          <span id="prop-type-badge" style="font-size:11px; color:#F59E0B;"></span>
        </div>

        <div class="field-group">
          <label>名稱與物件類別（窗戶/插座/開關/門可隨時切換）</label>
          <div class="field-row">
            <input type="text" id="prop-name" style="flex:1.3;">
            <select id="prop-type" style="flex:1.1;">
              <option value="furniture">🛋️ 一般家具</option>
              <option value="door">🚪 房門 (Door)</option>
              <option value="window">🪟 窗戶 (Window)</option>
              <option value="socket">🔌 插座 (Socket)</option>
              <option value="switch">💡 開關 (Switch)</option>
            </select>
          </div>
        </div>

        <div class="field-group">
          <label>尺寸：寬度 (W) × 深度 (D) × 高度 (H, 預設30) cm</label>
          <div class="field-row">
            <div><span style="font-size:10px;color:#64748B;">寬度 W</span><input type="number" id="prop-w"></div>
            <div><span style="font-size:10px;color:#64748B;">深度 D</span><input type="number" id="prop-d"></div>
            <div><span style="font-size:10px;color:#64748B;">高度 H</span><input type="number" id="prop-h" placeholder="30"></div>
          </div>
        </div>

        <div class="field-group">
          <label>位置：X × Y (可為負數拉出房外) × <span style="color:#F59E0B;font-weight:bold;">Z 離地高</span></label>
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

        <!-- 窗景上傳區 (僅窗戶顯示) -->
        <div class="field-group" id="scenery-upload-group" style="display:none; background:#1E293B; padding:8px; border-radius:6px; border:1px solid #3B82F6;">
          <label style="color:#60A5FA; font-weight:600;">🗾 3D 窗戶景色 (預設：富士山美景)</label>
          <input type="file" id="prop-scenery-file" accept="image/*" style="font-size: 11px; color: #CBD5E1; margin-top:4px;">
          <button id="btn-reset-fuji" style="margin-top:6px; font-size:11px; padding:4px 8px;">🗻 恢復預設富士山景</button>
        </div>

        <!-- 表面材質/門板貼圖上傳區 -->
        <div class="field-group" style="background:#1F232B; padding:8px; border-radius:6px; border:1px solid #334155;">
          <label id="texture-label" style="color:#E2E8F0;">🎨 上傳物件 / 門扇表面材質貼圖</label>
          <input type="file" id="prop-texture-file" accept="image/*" style="font-size: 11px; color: #8F96A0; margin-top:4px;">
          <button id="btn-clear-texture" style="margin-top:4px; font-size:11px; padding:3px 8px;">清除自訂材質</button>
        </div>

        <div style="display: flex; gap: 8px; margin-top: 8px;">
          <button id="btn-duplicate" style="flex: 1;">📋 複製物件</button>
          <button id="btn-delete" class="danger" style="flex: 1;">🗑️ 刪除物件</button>
        </div>
      </div>
    </div>

    <!-- 標籤 2：地面、留白處、坐向與流年九宮飛星 -->
    <div class="tab-content" id="tab-content-room" style="display: none;">
      <div style="background:#1E293B; border:1px solid #3B82F6; padding:8px 10px; border-radius:6px; display:flex; align-items:center; justify-content:space-between;">
        <span style="font-size:12px; font-weight:600; color:#93C5FD;">🔓 勾選才可拖曳/改動地面與留白處</span>
        <input type="checkbox" id="room-editable-lock" style="width:18px; height:18px; cursor:pointer;">
      </div>

      <div class="panel-title" style="margin-top:4px;">🏠 房間地面尺寸 (cm, 即時連動)</div>
      <div class="field-group">
        <div class="field-row">
          <div><span style="font-size:10px;color:#64748B;">總寬度 X</span><input type="number" id="room-w" class="live-room-input"></div>
          <div><span style="font-size:10px;color:#64748B;">總深度 Y</span><input type="number" id="room-d" class="live-room-input"></div>
          <div><span style="font-size:10px;color:#64748B;">天花板高 Z</span><input type="number" id="room-h" class="live-room-input"></div>
        </div>
      </div>

      <!-- 留白處管理 (可新增、刪除、編輯、勾選後可拖曳) -->
      <div class="panel-title" style="margin-top: 6px;">
        <span>🔲 留白處管理</span>
        <button onclick="addVoidArea()" style="padding:3px 8px; font-size:11px; background:#2563EB; border-color:#2563EB;">➕ 新增留白處</button>
      </div>
      <div id="void-list-container"></div>

      <!-- 八方羅盤設定 -->
      <div class="panel-title" style="margin-top: 6px;">🧭 八方坐向羅盤設定</div>
      <div class="field-group" style="flex-direction: row; align-items: center; justify-content: space-between;">
        <label style="margin: 0;">顯示八方坐向羅盤</label>
        <input type="checkbox" id="compass-show" class="live-room-input" checked style="cursor: pointer; width:16px; height:16px;">
      </div>
      <div class="field-group">
        <label>羅盤中心座標 (X, Y cm)</label>
        <div class="field-row">
          <input type="number" id="compass-x" class="live-room-input">
          <input type="number" id="compass-y" class="live-room-input">
        </div>
      </div>
      <div class="field-group">
        <label><span>羅盤旋轉角度 (0°～360°)</span><span id="compass-rot-val">0°</span></label>
        <input type="range" id="compass-rot-slider" min="0" max="360" value="0" style="width:100%;">
        <input type="number" id="compass-rot" class="live-room-input" min="0" max="360">
      </div>

      <!-- 流年九宮飛星設定 -->
      <div class="panel-title" style="margin-top: 8px; color:#FBBF24;">☯️ 流年九宮飛星風水盤</div>
      <div style="background:#1F232B; border:1px solid #B45309; border-radius:6px; padding:10px; display:flex; flex-direction:column; gap:8px;">
        <div style="display:flex; align-items:center; justify-content:space-between;">
          <span style="font-size:12px; font-weight:600; color:#FDE68A;">顯示房間九宮飛星與吉凶</span>
          <input type="checkbox" id="feixing-show" class="live-room-input" style="cursor:pointer; width:16px; height:16px;">
        </div>
        <div class="field-group" style="margin:0;">
          <label style="color:#FCD34D;">選擇流年西元年份 (自動推算中宮與八方飛星)</label>
          <div class="field-row" style="align-items:center;">
            <input type="number" id="feixing-year" class="live-room-input" value="2026" min="1900" max="2100" style="font-weight:bold; color:#FEF08A;">
            <span id="feixing-center-info" style="font-size:11px; color:#F59E0B; white-space:nowrap;">2026年: 一白入中宮</span>
          </div>
        </div>
        <div style="font-size:11px; color:#94A3B8; line-height:1.4;">
          💡 九宮格方位會自動跟隨上方「羅盤旋轉角度」對應東、西、南、北八方吉凶！
        </div>
      </div>
    </div>

    <!-- 標籤 3：專案存檔 -->
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
        <button id="btn-mode-2d" class="active">📐 2D 平面互動配置</button>
        <button id="btn-mode-3d">🧊 3D 擬真立體與窗景視圖</button>
      </div>
      <div class="hint-text" style="font-size: 12px; color: #94A3B8;">
        🖱️ <b>點選物件可直接拖曳（可拉出房間外）</b> | 按住空白處拉動平移視角 | 滾輪縮放
      </div>
    </div>

    <!-- 浮動畫布視角按鈕 -->
    <div class="view-controls">
      <button id="btn-zoom-in">➕ 放大</button>
      <button id="btn-zoom-out">➖ 縮小</button>
      <button id="btn-zoom-fit">🔍 適配居中</button>
      <button id="btn-pan-toggle" title="開啟後連點在物件上也會平移畫面">✋ 強制平移視角: 關</button>
    </div>
    
    <div id="canvas-container">
      <canvas id="fabric-canvas"></canvas>
    </div>
    <div id="three-container"></div>
  </div>

  <!-- 右側物件清單 -->
  <div class="right-panel" id="right-panel">
    <div class="panel-title">
      <span>📋 空間物件列表</span>
      <span id="obj-count" style="font-size: 12px; color: #94A3B8;">0</span>
    </div>
    <div class="quick-add-sub" style="margin-bottom:6px;">
      <button onclick="addNewObject('furniture')" style="background:#2563EB;border-color:#2563EB;">+ 家具</button>
      <button onclick="addNewObject('door')" style="background:#9A3412;border-color:#9A3412;">+ 門</button>
      <button onclick="addNewObject('window')" style="background:#D97706;border-color:#D97706;">+ 窗/電</button>
    </div>
    <div class="item-list" id="item-list-container"></div>
  </div>

  <!-- 手機版底部導覽列 -->
  <div class="mobile-nav">
    <button onclick="toggleMobilePanel('left')">⚙️ 編輯與飛星</button>
    <button onclick="toggleMobilePanel('canvas')" class="active">📐 畫布視角</button>
    <button onclick="toggleMobilePanel('right')">📋 物件清單</button>
  </div>
</div>

<script>
  let appState = {initial_data_json};
  // 相容舊版單一 void 結構自動轉為 voids 陣列
  if (!appState.voids && appState.void) {{
    appState.voids = [{{ id: "void_1", name: "留白處 1", x: appState.void.x, y: appState.void.y, w: appState.void.w, d: appState.void.d }}];
  }}

  let activeId = null;
  let canvas, scene, camera, renderer, controls;
  let currentMode = "2D";
  
  let isDraggingCanvas = false;
  let forcePanMode = false;
  let lastClientX = 0, lastClientY = 0;
  let touchStartDist = 0, touchStartZoom = 1;

  // 九宮飛星資料庫 (1~9星屬性與吉凶)
  const FEIXING_META = {{
    1: {{ name: "一白貪狼", el: "水", luck: "大吉 · 桃花/人緣", color: "#38BDF8", bg: "rgba(14, 116, 144, 0.28)", tip: "利感情、貴人、文昌" }},
    2: {{ name: "二黑巨門", el: "土", luck: "凶 · 病符星", color: "#F87171", bg: "rgba(153, 27, 27, 0.30)", tip: "注意健康，宜掛金屬葫蘆化解" }},
    3: {{ name: "三碧祿存", el: "木", luck: "凶 · 是非/官非", color: "#FB923C", bg: "rgba(154, 52, 18, 0.28)", tip: "易爭執，宜用紅色物件洩木氣" }},
    4: {{ name: "四綠文曲", el: "木", luck: "吉 · 文昌/考運", color: "#4ADE80", bg: "rgba(21, 128, 61, 0.28)", tip: "利學業、研發、企劃創意" }},
    5: {{ name: "五黃廉貞", el: "土", luck: "大凶 · 五黃煞", color: "#EF4444", bg: "rgba(185, 28, 28, 0.42)", tip: "忌動土動工，宜擺銅器或六帝錢" }},
    6: {{ name: "六白武曲", el: "金", luck: "吉 · 偏財/貴人", color: "#FACC15", bg: "rgba(161, 98, 7, 0.28)", tip: "利事業升遷、技術與偏財運" }},
    7: {{ name: "七赤破軍", el: "金", luck: "凶 · 破財/口舌", color: "#F472B6", bg: "rgba(157, 23, 77, 0.28)", tip: "防漏財小人，宜靜置或水局化解" }},
    8: {{ name: "八白左輔", el: "土", luck: "大吉 · 正財星", color: "#FBBF24", bg: "rgba(180, 83, 9, 0.35)", tip: "利正財置產，宜保持明亮整潔" }},
    9: {{ name: "九紫右弼", el: "火", luck: "大吉 · 當運喜慶", color: "#C084FC", bg: "rgba(107, 33, 168, 0.35)", tip: "九運當旺大吉星，利姻緣與百業" }}
  }};

  // 洛書九宮基礎飛伏偏移量 (相對中宮星曜的差值，對應：巽SE, 離S, 坤SW, 震E, 中C, 兌W, 艮NE, 坎N, 乾NW)
  // 洛書原盤中宮為5：SE=4(-1), S=9(+4), SW=2(-3), E=3(-2), C=5(0), W=7(+2), NE=8(+3), N=1(-4), NW=6(+1)
  const LUOSHU_OFFSETS = {{
    "SE": -1, "S": 4, "SW": -3,
    "E": -2,  "C": 0, "W": 2,
    "NE": 3,  "N": -4, "NW": 1
  }};

  function getCenterStarByYear(year) {{
    let mod = (2026 - year) % 9;
    let star = (1 + mod) % 9;
    if (star <= 0) star += 9;
    return star;
  }}

  function getStarAtDir(centerStar, dirKey) {{
    let s = (centerStar + LUOSHU_OFFSETS[dirKey]) % 9;
    if (s <= 0) s += 9;
    return s;
  }}

  // 手機版抽屜開關
  function toggleMobilePanel(target) {{
    const lp = document.getElementById("left-panel");
    const rp = document.getElementById("right-panel");
    if (target === 'left') {{
      lp.classList.toggle("open"); rp.classList.remove("open");
    }} else if (target === 'right') {{
      rp.classList.toggle("open"); lp.classList.remove("open");
    }} else {{
      lp.classList.remove("open"); rp.classList.remove("open");
    }}
  }}

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
      selection: false,
      preserveObjectStacking: true
    }});

    // 1. 滾輪縮放
    canvas.on('mouse:wheel', function(opt) {{
      const delta = opt.e.deltaY;
      let zoom = canvas.getZoom();
      zoom *= 0.999 ** delta;
      zoom = Math.min(Math.max(zoom, 0.2), 5);
      canvas.zoomToPoint({{ x: opt.e.offsetX, y: opt.e.offsetY }}, zoom);
      opt.e.preventDefault();
      opt.e.stopPropagation();
    }});

    // 2. 點選物件時直接拖曳物件；點選空白地板或開啟強制平移時平移視角
    canvas.on('mouse:down', function(opt) {{
      const evt = opt.e;
      const target = opt.target;
      const isSelectableTarget = target && (target.itemId || (target.voidId && appState.room.editable));

      if (!isSelectableTarget || forcePanMode || evt.button === 1 || evt.altKey) {{
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

    // 3. 手機雙指縮放支援
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
        let newZoom = Math.min(Math.max(touchStartZoom * (dist / touchStartDist), 0.2), 4.5);
        const cx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
        const cy = (e.touches[0].clientY + e.touches[1].clientY) / 2;
        canvas.zoomToPoint({{ x: cx, y: cy }}, newZoom);
      }}
    }}, {{ passive: false }});

    // 重要修復：moving / scaling / rotating 過程僅同步數據，絕不呼叫 canvas.clear()，確保拖曳絲滑不中斷！
    canvas.on('selection:created', onObjectSelected);
    canvas.on('selection:updated', onObjectSelected);
    canvas.on('selection:cleared', onObjectDeselected);
    canvas.on('object:moving', onObjectLiveMoving);
    canvas.on('object:scaling', onObjectLiveMoving);
    canvas.on('object:rotating', onObjectLiveMoving);
    canvas.on('object:modified', onObjectModifiedComplete);

    initRoomFormValues();
    renderVoidListUI();
    renderFullScene();
    zoomToFit();
  }}

  // 繪製 2D 完整場景
  function renderFullScene() {{
    if (!canvas) return;
    canvas.clear();
    canvas.backgroundColor = '#0A0C10';

    const rw = appState.room.width;
    const rd = appState.room.depth;

    // 1. 房間地面藍色底盤
    const floor = new fabric.Rect({{
      left: 0, top: 0, width: rw, height: rd,
      fill: '#5089C6', stroke: '#38BDF8', strokeWidth: 2,
      selectable: false, evented: false
    }});
    canvas.add(floor);

    // 房間外圍尺寸標尺
    canvas.add(new fabric.Text(`◀ 房間寬 ${{rw}} cm ▶`, {{
      left: rw / 2, top: -20, fontSize: 13, fill: '#94A3B8', originX: 'center', selectable: false, evented: false
    }}));
    canvas.add(new fabric.Text(`◀ 房間深 ${{rd}} cm ▶`, {{
      left: -20, top: rd / 2, fontSize: 13, fill: '#94A3B8', originX: 'center', angle: -90, selectable: false, evented: false
    }}));

    // 2. 繪製所有「留白處」 (依據是否勾選「改動地面」決定可否拖曳與拉伸)
    const canEditGround = !!appState.room.editable && !forcePanMode;
    appState.voids.forEach(v => {{
      const vRect = new fabric.Rect({{
        width: v.w, height: v.d,
        fill: '#FFFFFF',
        stroke: canEditGround ? '#2563EB' : '#CBD5E1',
        strokeWidth: canEditGround ? 2.5 : 1.5,
        strokeDashArray: canEditGround ? [5, 3] : null,
        originX: 'center', originY: 'center'
      }});
      const vLabel = new fabric.Text(`${{v.name}}\n${{Math.round(v.w)}}×${{Math.round(v.d)}}`, {{
        fontSize: 12, fill: '#334155', originX: 'center', originY: 'center', textAlign: 'center'
      }});
      const vGroup = new fabric.Group([vRect, vLabel], {{
        left: v.x + v.w / 2,
        top: v.y + v.d / 2,
        originX: 'center', originY: 'center',
        selectable: canEditGround,
        evented: canEditGround,
        voidId: v.id
      }});
      vGroup.setControlsVisibility({{ mtr: false }});
      canvas.add(vGroup);
    }});

    // 3. 繪製所有家具、門、窗戶、插座與開關
    appState.items.forEach(item => createFabricItem(item));

    // 4. 繪製「流年九宮飛星」專業風水盤 (置於上層但滑鼠穿透 evented: false，不阻擋拖曳物件)
    if (appState.compass.show_feixing) {{
      renderNinePalaceFeixing();
    }}

    // 5. 繪製八方坐向羅盤
    if (appState.compass.show) {{
      renderExpertCompass();
    }}

    // 恢復選中狀態
    if (activeId) {{
      const g = canvas.getObjects().find(o => o.itemId === activeId);
      if (g && !forcePanMode) canvas.setActiveObject(g);
    }}

    renderRightPanel();
    canvas.requestRenderAll();
    if (currentMode === "3D" && renderer) updateThreeScene();
  }}

  // --- 專業流年九宮飛星盤渲染 ---
  function renderNinePalaceFeixing() {{
    const rw = appState.room.width;
    const rd = appState.room.depth;
    const cw = rw / 3;
    const cd = rd / 3;
    const year = parseInt(appState.compass.feixing_year) || 2026;
    const centerStar = getCenterStarByYear(year);

    const infoEl = document.getElementById("feixing-center-info");
    if (infoEl) infoEl.innerText = `${{year}}年: ${{FEIXING_META[centerStar].name}}入中宮`;

    // 計算房間九宮格每一格相對於中心點的幾何角度，並對照羅盤旋轉角度映射真實八方方位
    // 預設羅盤 (rot=0)：左(180°)=東(E), 下(90°)=北(N), 右(0°)=西(W), 上(270°)=南(S)
    const rot = appState.compass.rotation || 0;
    const dirAngles = [
      {{ key: "W",  deg: 0,   label: "正西" }},
      {{ key: "NW", deg: 45,  label: "西北" }},
      {{ key: "N",  deg: 90,  label: "正北" }},
      {{ key: "NE", deg: 135, label: "東北" }},
      {{ key: "E",  deg: 180, label: "正東" }},
      {{ key: "SE", deg: 225, label: "東南" }},
      {{ key: "S",  deg: 270, label: "正南" }},
      {{ key: "SW", deg: 315, label: "西南" }}
    ];

    for (let row = 0; row < 3; row++) {{
      for (let col = 0; col < 3; col++) {{
        const gx = col * cw;
        const gy = row * cd;
        let dirKey = "C";
        let dirLabel = "中宮";

        if (!(row === 1 && col === 1)) {{
          const dx = (col - 1);
          const dy = (row - 1);
          let cellDeg = Math.atan2(dy, dx) * 180 / Math.PI;
          if (cellDeg < 0) cellDeg += 360;
          // 扣除羅盤旋轉偏角，取得對應的基礎方位
          let relDeg = (cellDeg - rot) % 360;
          if (relDeg < 0) relDeg += 360;
          const idx = Math.round(relDeg / 45) % 8;
          dirKey = dirAngles[idx].key;
          dirLabel = dirAngles[idx].label;
        }}

        const starNum = getStarAtDir(centerStar, dirKey);
        const meta = FEIXING_META[starNum];

        // 九宮格半透明底色框
        canvas.add(new fabric.Rect({{
          left: gx, top: gy, width: cw, height: cd,
          fill: meta.bg,
          stroke: '#F59E0B',
          strokeWidth: 1.5,
          strokeDashArray: [6, 4],
          selectable: false, evented: false
        }}));

        // 飛星標題與吉凶文字
        const titleStr = `【${{dirLabel}}】${{meta.name}} (${{meta.el}})`;
        const luckStr = `${{meta.luck}}\n${{meta.tip}}`;

        canvas.add(new fabric.Text(titleStr, {{
          left: gx + cw / 2, top: gy + 18,
          fontSize: 13, fontWeight: 'bold',
          fill: meta.color,
          backgroundColor: 'rgba(10, 12, 16, 0.82)',
          originX: 'center', originY: 'center',
          selectable: false, evented: false
        }}));

        canvas.add(new fabric.Text(luckStr, {{
          left: gx + cw / 2, top: gy + 42,
          fontSize: 11,
          fill: '#F8FAFC',
          backgroundColor: 'rgba(15, 23, 42, 0.78)',
          originX: 'center', originY: 'center', textAlign: 'center',
          selectable: false, evented: false
        }}));
      }}
    }}
  }}

  // --- 專家級八方坐向羅盤渲染 ---
  function renderExpertCompass() {{
    const cx = appState.compass.x;
    const cy = appState.compass.y;
    const rot = appState.compass.rotation || 0;
    const radius = Math.max(appState.room.width, appState.room.depth) * 0.72;

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
        backgroundColor: dir.primary ? 'rgba(107, 33, 168, 0.78)' : 'rgba(15, 23, 42, 0.68)',
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

  // --- 建立可自由拖曳、縮放、旋轉的 2D 物件（插座/開關 2D 備註與普通物件完全相同） ---
  function createFabricItem(item) {{
    const subElements = [];

    const rect = new fabric.Rect({{
      width: item.w,
      height: item.d,
      fill: item.color,
      stroke: '#1E293B',
      strokeWidth: 1.5,
      originX: 'center', originY: 'center'
    }});
    subElements.push(rect);

    // 若為房門 (Door)，在 2D 加上專業開門弧線示意
    if (item.item_type === "door") {{
      const arcPath = new fabric.Path(`M ${{-item.w/2}} ${{item.d/2}} L ${{-item.w/2}} ${{item.d/2 + item.w}} A ${{item.w}} ${{item.w}} 0 0 0 ${{item.w/2}} ${{item.d/2}}`, {{
        fill: 'rgba(251, 146, 60, 0.15)',
        stroke: '#FDBA74',
        strokeWidth: 1.5,
        strokeDashArray: [4, 3],
        originX: 'center', originY: 'center',
        top: item.w / 2
      }});
      subElements.push(arcPath);
    }}

    // 2D 標籤：所有物件（含插座、開關、窗戶、門、家具）皆採用一致的簡潔置中顯示
    const labelStr = `${{item.name}}\n${{Math.round(item.w)}}×${{Math.round(item.d)}}`;
    const fontSize = Math.max(9, Math.min(12, Math.min(item.w, item.d) * 0.45));
    const text = new fabric.Text(labelStr, {{
      fontSize: fontSize,
      fill: '#FFFFFF',
      originX: 'center', originY: 'center',
      textAlign: 'center'
    }});
    subElements.push(text);

    const group = new fabric.Group(subElements, {{
      left: item.x + item.w / 2,
      top: item.y + item.d / 2,
      angle: item.rot || 0,
      originX: 'center', originY: 'center',
      selectable: !forcePanMode,
      evented: !forcePanMode,
      itemId: item.id
    }});

    group.setControlsVisibility({{
      mt: true, mb: true, ml: true, mr: true,
      tl: true, tr: true, bl: true, br: true,
      mtr: true
    }});

    if (item.texture && item.item_type !== "window") {{
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

  // --- 拖曳與變形事件處理（不重繪畫布，支援拉出房間外） ---
  function onObjectSelected(e) {{
    const target = e.selected ? e.selected[0] : null;
    if (!target) return;
    if (target.itemId) {{
      activeId = target.itemId;
      switchLeftTab('item');
      updateLeftItemPanel();
      highlightRightPanel();
    }} else if (target.voidId) {{
      switchLeftTab('room');
    }}
  }}

  function onObjectDeselected() {{
    activeId = null;
    document.getElementById("no-selection").style.display = "block";
    document.getElementById("prop-editor").style.display = "none";
    highlightRightPanel();
  }}

  // 拖曳/縮放/旋轉進行中：只即時更新座標與面板數字，完全不清除畫布！
  function onObjectLiveMoving(e) {{
    const target = e.target;
    if (!target) return;

    if (target.itemId) {{
      const item = appState.items.find(i => i.id === target.itemId);
      if (!item) return;
      const baseRect = target.item(0);
      const newW = Math.max(4, Math.round(baseRect.width * target.scaleX));
      const newD = Math.max(4, Math.round(baseRect.height * target.scaleY));
      item.w = newW;
      item.d = newD;
      item.rot = Math.round((target.angle % 360 + 360) % 360);
      item.x = Math.round(target.left - newW / 2);
      item.y = Math.round(target.top - newD / 2);
      updateLeftItemPanel();
    }} else if (target.voidId) {{
      const v = appState.voids.find(x => x.id === target.voidId);
      if (!v) return;
      const baseRect = target.item(0);
      v.w = Math.max(10, Math.round(baseRect.width * target.scaleX));
      v.d = Math.max(10, Math.round(baseRect.height * target.scaleY));
      v.x = Math.round(target.left - v.w / 2);
      v.y = Math.round(target.top - v.d / 2);
      renderVoidListUI();
    }}
  }}

  // 滑鼠放開完成變形後：更新文字標籤與右側清單
  function onObjectModifiedComplete(e) {{
    onObjectLiveMoving(e);
    renderFullScene();
  }}

  function updateLeftItemPanel() {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;

    document.getElementById("no-selection").style.display = "none";
    document.getElementById("prop-editor").style.display = "block";

    const typeNames = {{
      furniture: "🛋️ 一般家具",
      door: "🚪 房門 (3D擬真門)",
      window: "🪟 窗戶 (3D富士山窗景)",
      socket: "🔌 牆壁插座 (3D擬真插座)",
      switch: "💡 牆壁開關 (3D擬真開關)"
    }};
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

    document.getElementById("scenery-upload-group").style.display = (item.item_type === "window") ? "flex" : "none";
    document.getElementById("texture-label").innerText = (item.item_type === "door")
      ? "🚪 上傳自訂門扇圖片 / 木紋材質"
      : "🎨 上傳物件表面材質 / 貼圖";
  }}

  // 左側物件輸入框即時連動
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
      }}
      if (id === "prop-type" && item.item_type === "window" && !item.scenery) {{
        item.scenery = appState.default_fuji;
      }}
      updateLeftItemPanel();
      renderFullScene();
    }});
  }});

  // 窗景與材質貼圖上傳
  document.getElementById("prop-scenery-file").addEventListener("change", function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(f) {{
      const item = appState.items.find(i => i.id === activeId);
      if (!item) return;
      item.scenery = f.target.result;
      if (currentMode === "3D" && renderer) updateThreeScene();
      alert("✅ 已更新 3D 窗戶景色！");
    }};
    reader.readAsDataURL(file);
  }});

  document.getElementById("btn-reset-fuji").addEventListener("click", () => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.scenery = appState.default_fuji;
    if (currentMode === "3D" && renderer) updateThreeScene();
  }});

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

  document.getElementById("btn-clear-texture").addEventListener("click", () => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.texture = "";
    renderFullScene();
  }});

  // --- 新增物件（家具 / 門 / 窗戶 / 插座 / 開關） ---
  function addNewObject(type) {{
    let newItem;
    if (type === 'window') {{
      newItem = {{
        id: "win_" + Date.now(), name: "窗戶", item_type: "window",
        x: 150, y: 348, z: 85, w: 120, d: 12, h: 130, rot: 0,
        color: "#F59E0B", texture: "", scenery: appState.default_fuji
      }};
    }} else if (type === 'socket') {{
      newItem = {{
        id: "soc_" + Date.now(), name: "插座", item_type: "socket",
        x: 280, y: 348, z: 30, w: 22, d: 12, h: 14, rot: 0,
        color: "#F97316", texture: "", scenery: ""
      }};
    }} else if (type === 'switch') {{
      newItem = {{
        id: "sw_" + Date.now(), name: "開關", item_type: "switch",
        x: 240, y: 348, z: 110, w: 22, d: 12, h: 14, rot: 0,
        color: "#0EA5E9", texture: "", scenery: ""
      }};
    }} else if (type === 'door') {{
      newItem = {{
        id: "door_" + Date.now(), name: "房門", item_type: "door",
        x: 20, y: 346, z: 0, w: 90, d: 14, h: 210, rot: 0,
        color: "#8B5A2B", texture: "", scenery: ""
      }};
    }} else {{
      newItem = {{
        id: "item_" + Date.now(), name: "新家具", item_type: "furniture",
        x: 140, y: 140, z: 0, w: 60, d: 50, h: 30, rot: 0,
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
    copy.name = item.name + "(複本)";
    copy.x += 20; copy.y += 20;
    appState.items.push(copy);
    activeId = copy.id;
    renderFullScene();
    selectItemById(copy.id);
  }});

  // --- 「留白處」多組新增、編輯、刪除與安全鎖定 ---
  document.getElementById("room-editable-lock").addEventListener("change", function(e) {{
    appState.room.editable = e.target.checked;
    renderVoidListUI();
    renderFullScene();
  }});

  function renderVoidListUI() {{
    const container = document.getElementById("void-list-container");
    container.innerHTML = "";
    const disabledAttr = appState.room.editable ? "" : "disabled";

    appState.voids.forEach((v, idx) => {{
      const card = document.createElement("div");
      card.className = "void-card";
      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <input type="text" value="${{v.name}}" ${{disabledAttr}} oninput="updateVoidField(${{idx}}, 'name', this.value)" style="width:130px; font-weight:600;">
          <button class="danger" ${{disabledAttr}} onclick="deleteVoidArea(${{idx}})" style="padding:2px 7px; font-size:11px;">🗑️ 刪除</button>
        </div>
        <div class="field-row">
          <div><span style="font-size:10px;color:#64748B;">寬 W</span><input type="number" value="${{Math.round(v.w)}}" ${{disabledAttr}} oninput="updateVoidField(${{idx}}, 'w', this.value)"></div>
          <div><span style="font-size:10px;color:#64748B;">深 D</span><input type="number" value="${{Math.round(v.d)}}" ${{disabledAttr}} oninput="updateVoidField(${{idx}}, 'd', this.value)"></div>
          <div><span style="font-size:10px;color:#64748B;">X 坐標</span><input type="number" value="${{Math.round(v.x)}}" ${{disabledAttr}} oninput="updateVoidField(${{idx}}, 'x', this.value)"></div>
          <div><span style="font-size:10px;color:#64748B;">Y 坐標</span><input type="number" value="${{Math.round(v.y)}}" ${{disabledAttr}} oninput="updateVoidField(${{idx}}, 'y', this.value)"></div>
        </div>
      `;
      container.appendChild(card);
    }});
  }}

  window.updateVoidField = function(idx, field, val) {{
    if (!appState.voids[idx]) return;
    if (field === 'name') appState.voids[idx].name = val;
    else appState.voids[idx][field] = parseFloat(val) || 0;
    renderFullScene();
  }};

  window.addVoidArea = function() {{
    if (!appState.room.editable) {{
      alert("💡 請先勾選上方「🔓 勾選才可拖曳/改動地面與留白處」，即可新增或移動留白處！");
      return;
    }}
    appState.voids.push({{
      id: "void_" + Date.now(),
      name: `留白處 ${{appState.voids.length + 1}}`,
      x: 50, y: 50, w: 80, d: 80
    }});
    renderVoidListUI();
    renderFullScene();
  }};

  window.deleteVoidArea = function(idx) {{
    appState.voids.splice(idx, 1);
    renderVoidListUI();
    renderFullScene();
  }};

  // --- 地面、羅盤與九宮飛星「即時連動」 ---
  function initRoomFormValues() {{
    document.getElementById("room-editable-lock").checked = !!appState.room.editable;
    document.getElementById("room-w").value = appState.room.width;
    document.getElementById("room-d").value = appState.room.depth;
    document.getElementById("room-h").value = appState.room.height;

    document.getElementById("compass-show").checked = appState.compass.show;
    document.getElementById("compass-x").value = appState.compass.x;
    document.getElementById("compass-y").value = appState.compass.y;
    document.getElementById("compass-rot").value = appState.compass.rotation || 0;
    document.getElementById("compass-rot-slider").value = appState.compass.rotation || 0;
    document.getElementById("compass-rot-val").innerText = (appState.compass.rotation || 0) + "°";

    document.getElementById("feixing-show").checked = !!appState.compass.show_feixing;
    document.getElementById("feixing-year").value = appState.compass.feixing_year || 2026;
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

    appState.compass.show_feixing = document.getElementById("feixing-show").checked;
    appState.compass.feixing_year = parseInt(document.getElementById("feixing-year").value) || 2026;

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

  // --- 右側物件清單 ---
  function renderRightPanel() {{
    const container = document.getElementById("item-list-container");
    document.getElementById("obj-count").innerText = `共 ${{appState.items.length}} 項`;
    container.innerHTML = "";

    const badgeMap = {{
      furniture: {{ text: "家具", cls: "" }},
      door: {{ text: "🚪 門", cls: "door" }},
      window: {{ text: "🪟 窗戶", cls: "win" }},
      socket: {{ text: "🔌 插座", cls: "win" }},
      switch: {{ text: "💡 開關", cls: "win" }}
    }};

    appState.items.forEach(item => {{
      const card = document.createElement("div");
      card.className = "item-card" + (item.id === activeId ? " selected" : "");
      card.onclick = () => selectItemById(item.id);

      const b = badgeMap[item.item_type || "furniture"] || badgeMap.furniture;
      const hVal = item.h || 30;
      const zVal = item.z || 0;

      card.innerHTML = `
        <div class="item-card-header">
          <div class="name">
            <span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${{item.color}};border:1px solid #fff;"></span>
            <span>${{item.name}}</span>
            <span class="badge ${{b.cls}}">${{b.text}}</span>
          </div>
          <button class="card-del-btn" title="刪除此物件" onclick="deleteItemById('${{item.id}}', event)">🗑️</button>
        </div>
        <div class="dims">
          ${{Math.round(item.w)}}×${{Math.round(item.d)}}×${{hVal}} cm | Z離地: <b>${{zVal}}cm</b> | ${{item.rot || 0}}°
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
    if (group && !forcePanMode) {{
      canvas.setActiveObject(group);
      canvas.requestRenderAll();
    }}
    switchLeftTab('item');
    updateLeftItemPanel();
    highlightRightPanel();
  }}

  // --- 畫布縮放與強制平移控制 ---
  function zoomToFit() {{
    const rw = appState.room.width;
    const rd = appState.room.depth;
    const container = document.getElementById("canvas-container");
    const cw = container.clientWidth - 100;
    const ch = container.clientHeight - 100;

    const scale = Math.min(cw / rw, ch / rd, 1.7);
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
    canvas.setZoom(Math.max(canvas.getZoom() / 1.2, 0.2));
  }});
  document.getElementById("btn-pan-toggle").addEventListener("click", function() {{
    forcePanMode = !forcePanMode;
    this.innerText = forcePanMode ? "✋ 強制平移視角: 開啟中" : "✋ 強制平移視角: 關";
    this.classList.toggle("active", forcePanMode);
    renderFullScene();
  }});

  // --- 專案存檔與匯出入 ---
  document.getElementById("btn-save-local").addEventListener("click", () => {{
    localStorage.setItem("room_planner_v4", JSON.stringify(appState));
    alert("✅ 已成功儲存於 App 本地記憶中！");
  }});

  document.getElementById("btn-load-local").addEventListener("click", () => {{
    const saved = localStorage.getItem("room_planner_v4") || localStorage.getItem("room_planner_v3");
    if (saved) {{
      appState = JSON.parse(saved);
      if (!appState.voids && appState.void) {{
        appState.voids = [{{ id: "void_1", name: "留白處 1", x: appState.void.x, y: appState.void.y, w: appState.void.w, d: appState.void.d }}];
      }}
      initRoomFormValues();
      renderVoidListUI();
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
        if (!appState.voids && appState.void) {{
          appState.voids = [{{ id: "void_1", name: "留白處 1", x: appState.void.x, y: appState.void.y, w: appState.void.w, d: appState.void.d }}];
        }}
        initRoomFormValues();
        renderVoidListUI();
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
      renderVoidListUI();
      renderFullScene();
      zoomToFit();
    }}
  }});

  // --- 3D 擬真立體渲染 (Three.js：擬真插座、擬真開關、立體門與把手、富士山窗景) ---
  function initThree() {{
    const container = document.getElementById("three-container");
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0B0F17);

    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 1, 6000);
    camera.position.set(appState.room.width / 2, 430, appState.room.depth + 380);

    renderer = new THREE.WebGLRenderer({{ antialias: true }});
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(appState.room.width / 2, 60, appState.room.depth / 2);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.82);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.65);
    dirLight.position.set(250, 520, 320);
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

    // 1. 地板與立體空間外框
    const floorGeo = new THREE.PlaneGeometry(rw, rd);
    const floorMat = new THREE.MeshLambertMaterial({{ color: 0x5089C6, side: THREE.DoubleSide }});
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(rw / 2, 0, rd / 2);
    scene.add(floor);

    const wallBoxGeo = new THREE.BoxGeometry(rw, rh, rd);
    const wallEdges = new THREE.EdgesGeometry(wallBoxGeo);
    const wallLine = new THREE.LineSegments(wallEdges, new THREE.LineBasicMaterial({{ color: 0x334155 }}));
    wallLine.position.set(rw / 2, rh / 2, rd / 2);
    scene.add(wallLine);

    // 2. 多組留白處
    appState.voids.forEach(v => {{
      const voidGeo = new THREE.PlaneGeometry(v.w, v.d);
      const voidMat = new THREE.MeshBasicMaterial({{ color: 0xffffff, side: THREE.DoubleSide }});
      const voidMesh = new THREE.Mesh(voidGeo, voidMat);
      voidMesh.rotation.x = -Math.PI / 2;
      voidMesh.position.set(v.x + v.w / 2, 0.4, v.y + v.d / 2);
      scene.add(voidMesh);
    }});

    // 3. 3D 羅盤線
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
        scene.add(new THREE.Line(lineGeo, new THREE.LineBasicMaterial({{ color: 0xC084FC }})));
      }}
    }}

    // 4. 針對不同類別進行 3D 擬真建模渲染
    const texLoader = new THREE.TextureLoader();

    appState.items.forEach(item => {{
      const h = item.h || 30;
      const zBottom = item.z || 0;
      const t = item.item_type || "furniture";

      if (t === "window") {{
        // 🪟 窗戶：立體窗框 + 十字窗櫺 + 富士山窗景
        const winGroup = new THREE.Group();
        const fDepth = Math.max(item.d, 8);

        const frameGeo = new THREE.BoxGeometry(item.w, h, fDepth);
        const frameEdges = new THREE.EdgesGeometry(frameGeo);
        winGroup.add(new THREE.LineSegments(frameEdges, new THREE.LineBasicMaterial({{ color: 0xF59E0B, linewidth: 3 }})));

        const sceneryUrl = item.scenery || appState.default_fuji;
        const sceneryTex = texLoader.load(sceneryUrl);
        const glassGeo = new THREE.BoxGeometry(Math.max(4, item.w - 4), Math.max(4, h - 4), fDepth * 0.5);
        const glassMesh = new THREE.Mesh(glassGeo, new THREE.MeshBasicMaterial({{ map: sceneryTex }}));
        winGroup.add(glassMesh);

        winGroup.rotation.y = -(item.rot || 0) * Math.PI / 180;
        winGroup.position.set(item.x + item.w / 2, zBottom + h / 2, item.y + item.d / 2);
        scene.add(winGroup);

      }} else if (t === "socket") {{
        // 🔌 3D 擬真牆壁插座：白色外框面板 + 雙插座內凹槽 + 黑色三孔插孔
        const socGroup = new THREE.Group();
        const w = Math.max(item.w, 12);
        const d = Math.max(item.d, 4);

        // 白色面板主體
        const plateGeo = new THREE.BoxGeometry(w, h, d);
        const plateMat = new THREE.MeshLambertMaterial({{ color: 0xF8FAFC }});
        const plateMesh = new THREE.Mesh(plateGeo, plateMat);
        plateMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(plateGeo), new THREE.LineBasicMaterial({{ color: 0x94A3B8 }})));
        socGroup.add(plateMesh);

        // 左右兩個插座孔組 (前後雙面皆渲染，無論從哪個角度看都清楚)
        [-w * 0.22, w * 0.22].forEach(offsetX => {{
          [-d/2 - 0.3, d/2 + 0.3].forEach(sideZ => {{
            // 左火線孔、右零線孔
            const slotGeo = new THREE.BoxGeometry(w * 0.06, h * 0.22, 0.8);
            const slotMat = new THREE.MeshBasicMaterial({{ color: 0x1E293B }});
            const s1 = new THREE.Mesh(slotGeo, slotMat);
            s1.position.set(offsetX - w * 0.07, h * 0.1, sideZ);
            const s2 = new THREE.Mesh(slotGeo, slotMat);
            s2.position.set(offsetX + w * 0.07, h * 0.1, sideZ);
            // 下方圓形接地孔
            const gndGeo = new THREE.BoxGeometry(w * 0.08, h * 0.15, 0.8);
            const gnd = new THREE.Mesh(gndGeo, slotMat);
            gnd.position.set(offsetX, -h * 0.2, sideZ);
            socGroup.add(s1, s2, gnd);
          }});
        }});

        socGroup.rotation.y = -(item.rot || 0) * Math.PI / 180;
        socGroup.position.set(item.x + item.w / 2, zBottom + h / 2, item.y + item.d / 2);
        scene.add(socGroup);

      }} else if (t === "switch") {{
        // 💡 3D 擬真牆壁開關：白色外框面板 + 立體翹板按鍵 + 綠色螢光指示條
        const swGroup = new THREE.Group();
        const w = Math.max(item.w, 12);
        const d = Math.max(item.d, 4);

        const plateGeo = new THREE.BoxGeometry(w, h, d);
        const plateMesh = new THREE.Mesh(plateGeo, new THREE.MeshLambertMaterial({{ color: 0xF1F5F9 }}));
        plateMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(plateGeo), new THREE.LineBasicMaterial({{ color: 0x64748B }})));
        swGroup.add(plateMesh);

        // 雙切翹板按鈕與螢光綠條
        [-w * 0.2, w * 0.2].forEach(offsetX => {{
          const btnGeo = new THREE.BoxGeometry(w * 0.32, h * 0.65, d + 2.2);
          const btnMesh = new THREE.Mesh(btnGeo, new THREE.MeshLambertMaterial({{ color: 0xE2E8F0 }}));
          btnMesh.rotation.x = 0.12; // 微傾按壓感
          btnMesh.position.set(offsetX, 0, 0);
          swGroup.add(btnMesh);

          const ledGeo = new THREE.BoxGeometry(w * 0.18, h * 0.08, d + 2.8);
          const ledMesh = new THREE.Mesh(ledGeo, new THREE.MeshBasicMaterial({{ color: 0x10B981 }}));
          ledMesh.position.set(offsetX, 0, 0);
          swGroup.add(ledMesh);
        }});

        swGroup.rotation.y = -(item.rot || 0) * Math.PI / 180;
        swGroup.position.set(item.x + item.w / 2, zBottom + h / 2, item.y + item.d / 2);
        scene.add(swGroup);

      }} else if (t === "door") {{
        // 🚪 3D 擬真房門：深色立體門框 + 門扇本體(支援自訂貼圖) + 金屬門把與鎖具
        const doorGroup = new THREE.Group();
        const w = item.w;
        const d = Math.max(item.d, 8);

        // 外部門框
        const frameGeo = new THREE.BoxGeometry(w + 6, h + 3, d + 2);
        const frameEdges = new THREE.EdgesGeometry(frameGeo);
        doorGroup.add(new THREE.LineSegments(frameEdges, new THREE.LineBasicMaterial({{ color: 0x451A03, linewidth: 2 }})));

        // 門扇本體
        const panelGeo = new THREE.BoxGeometry(w, h, d * 0.75);
        let panelMat;
        if (item.texture) {{
          panelMat = new THREE.MeshLambertMaterial({{ map: texLoader.load(item.texture) }});
        }} else {{
          panelMat = new THREE.MeshLambertMaterial({{ color: item.color || 0x8B5A2B }});
        }}
        const panelMesh = new THREE.Mesh(panelGeo, panelMat);
        panelMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(panelGeo), new THREE.LineBasicMaterial({{ color: 0x271206 }})));
        doorGroup.add(panelMesh);

        // 門扇上下裝飾內框線
        const trimGeo1 = new THREE.BoxGeometry(w * 0.72, h * 0.35, d * 0.82);
        const trimEdges1 = new THREE.LineSegments(new THREE.EdgesGeometry(trimGeo1), new THREE.LineBasicMaterial({{ color: 0xD97706 }}));
        trimEdges1.position.set(0, h * 0.22, 0);
        const trimGeo2 = new THREE.BoxGeometry(w * 0.72, h * 0.35, d * 0.82);
        const trimEdges2 = new THREE.LineSegments(new THREE.EdgesGeometry(trimGeo2), new THREE.LineBasicMaterial({{ color: 0xD97706 }}));
        trimEdges2.position.set(0, -h * 0.22, 0);
        doorGroup.add(trimEdges1, trimEdges2);

        // 金屬水平門把 (前後雙面)
        const handleMat = new THREE.MeshLambertMaterial({{ color: 0xFBBF24 }});
        const handleAxis = new THREE.Mesh(new THREE.BoxGeometry(3, 3, d + 8), handleMat);
        handleAxis.position.set(w * 0.36, -h * 0.04, 0);
        const leverFront = new THREE.Mesh(new THREE.BoxGeometry(12, 2.5, 2.5), handleMat);
        leverFront.position.set(w * 0.36 - 4, -h * 0.04, d / 2 + 3.5);
        const leverBack = new THREE.Mesh(new THREE.BoxGeometry(12, 2.5, 2.5), handleMat);
        leverBack.position.set(w * 0.36 - 4, -h * 0.04, -d / 2 - 3.5);
        doorGroup.add(handleAxis, leverFront, leverBack);

        doorGroup.rotation.y = -(item.rot || 0) * Math.PI / 180;
        doorGroup.position.set(item.x + item.w / 2, zBottom + h / 2, item.y + item.d / 2);
        scene.add(doorGroup);

      }} else {{
        // 🛋️ 一般家具物件
        const geo = new THREE.BoxGeometry(item.w, h, item.d);
        let mat;
        if (item.texture) {{
          mat = new THREE.MeshLambertMaterial({{ map: texLoader.load(item.texture) }});
        }} else {{
          mat = new THREE.MeshLambertMaterial({{ color: item.color }});
        }}
        const mesh = new THREE.Mesh(geo, mat);
        mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({{ color: 0x1E293B }})));
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
