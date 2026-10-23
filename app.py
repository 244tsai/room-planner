import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(
    page_title="專業臥室空間設計 & 3D人類視角風水系統",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    header { display: none !important; }
    footer { display: none !important; }
    iframe { height: 100dvh !important; min-height: 680px !important; border: none !important; }
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

# --- 預設格局、3D牆面/天花板、人物模型、分類與物件數據 ---
DEFAULT_ROOM = {
    "width": 460, "depth": 360, "height": 280,
    "editable": False,
    "show_walls": True,
    "show_ceiling": False,
    "wall_color": "#F8FAFC",
    "ceiling_color": "#FFFFFF",
    "wall_texture": "",
    "ceiling_texture": ""
}

DEFAULT_HUMAN = {
    "x": 230, "y": 230, "z": 0,
    "height": 178,           # 預設身高 178cm (僅能於左側面板修改，3D畫布鎖定高度防誤觸)
    "rot": 0,                # 水平視角面向角度 (度)
    "pitch": 0,              # 垂直仰角/俯角 (度)
    "posture": "stand"       # "stand" (站立) | "sit" (坐姿) | "lie" (躺姿)
}

DEFAULT_COMPASS = {
    "x": 255, "y": 185, "rotation": 0, "show": True,
    "show_feixing": False, "feixing_year": 2026
}

DEFAULT_VOIDS = [
    {"id": "void_1", "name": "留白處 1", "x": 370, "y": 0, "w": 90, "d": 120}
]

# 「床」獨立為專屬分類項目
DEFAULT_CATEGORIES = ["床", "大型家具", "收納櫃體", "門窗建材", "機電開關"]

DEFAULT_ITEMS = [
    {"id": "bed", "name": "床", "category": "床", "item_type": "furniture", "x": 200, "y": 0, "z": 0, "w": 152, "d": 195, "h": 55, "rot": 0, "color": "#FAD785", "texture": "", "scenery": "", "flip_x": False, "flip_y": False},
    {"id": "stand_l", "name": "床頭櫃(左)", "category": "收納櫃體", "item_type": "furniture", "x": 175, "y": 0, "z": 0, "w": 25, "d": 40, "h": 45, "rot": 0, "color": "#FAD785", "texture": "", "scenery": "", "flip_x": False, "flip_y": False},
    {"id": "stand_r", "name": "床頭櫃(右)", "category": "收納櫃體", "item_type": "furniture", "x": 352, "y": 0, "z": 0, "w": 25, "d": 40, "h": 45, "rot": 0, "color": "#FAD785", "texture": "", "scenery": "", "flip_x": False, "flip_y": False},
    {"id": "wardrobe_new", "name": "新衣櫃", "category": "收納櫃體", "item_type": "furniture", "x": 0, "y": 0, "z": 0, "w": 121, "d": 72, "h": 210, "rot": 0, "color": "#A0CB88", "texture": "", "scenery": "", "flip_x": False, "flip_y": False},
    {"id": "desk", "name": "書桌", "category": "大型家具", "item_type": "furniture", "x": 0, "y": 135, "z": 0, "w": 123, "d": 71, "h": 75, "rot": 0, "color": "#8232FA", "texture": "", "scenery": "", "flip_x": False, "flip_y": False},
    {"id": "drybox", "name": "防潮箱", "category": "收納櫃體", "item_type": "furniture", "x": 235, "y": 315, "z": 0, "w": 40, "d": 45, "h": 50, "rot": 0, "color": "#DC7CF5", "texture": "", "scenery": "", "flip_x": False, "flip_y": False},
    {"id": "wardrobe_white", "name": "白衣櫃", "category": "收納櫃體", "item_type": "furniture", "x": 275, "y": 305, "z": 0, "w": 60, "d": 55, "h": 190, "rot": 0, "color": "#AADE8D", "texture": "", "scenery": "", "flip_x": False, "flip_y": False},
    {"id": "wardrobe_old", "name": "舊衣櫃", "category": "收納櫃體", "item_type": "furniture", "x": 335, "y": 299, "z": 0, "w": 120, "d": 61, "h": 200, "rot": 0, "color": "#9EC484", "texture": "", "scenery": "", "flip_x": False, "flip_y": False},
    {"id": "bookcase", "name": "玻書櫃", "category": "收納櫃體", "item_type": "furniture", "x": 428, "y": 120, "z": 0, "w": 32, "d": 63, "h": 180, "rot": 0, "color": "#DC7CF5", "texture": "", "scenery": "", "flip_x": False, "flip_y": False},
    {"id": "win_main", "name": "窗戶", "category": "門窗建材", "item_type": "window", "x": 35, "y": 348, "z": 85, "w": 135, "d": 12, "h": 130, "rot": 0, "color": "#F59E0B", "texture": "", "scenery": FUJI_SVG, "flip_x": False, "flip_y": False},
    {"id": "socket_wall", "name": "插座", "category": "機電開關", "item_type": "socket", "x": 325, "y": 348, "z": 35, "w": 22, "d": 12, "h": 14, "rot": 0, "color": "#F97316", "texture": "", "scenery": "", "flip_x": False, "flip_y": False}
]

initial_data = {
    "room": DEFAULT_ROOM,
    "human": DEFAULT_HUMAN,
    "compass": DEFAULT_COMPASS,
    "voids": DEFAULT_VOIDS,
    "categories": DEFAULT_CATEGORIES,
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
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/TransformControls.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; -webkit-user-select: none; }}
    input, select, textarea {{ user-select: text !important; -webkit-user-select: text !important; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft JhengHei", sans-serif; background: #0E1117; color: #E0E0E0; overflow: hidden; touch-action: none; height: 100dvh; width: 100vw; }}
    .app-container {{ display: flex; height: 100dvh; width: 100vw; position: relative; overflow: hidden; }}
    
    /* 左右側邊欄與中間畫布 */
    .left-panel {{ width: 345px; background: #16191E; border-right: 1px solid #282C34; display: flex; flex-direction: column; height: 100%; z-index: 30; transition: transform 0.25s ease; }}
    .center-canvas {{ flex: 1; display: flex; flex-direction: column; position: relative; background: #090B0E; height: 100%; overflow: hidden; }}
    .right-panel {{ width: 315px; background: #16191E; border-left: 1px solid #282C34; padding: 12px; display: flex; flex-direction: column; height: 100%; z-index: 30; transition: transform 0.25s ease; }}

    /* 左面板標籤頁 */
    .tab-bar {{ display: flex; background: #1F232B; border-bottom: 1px solid #282C34; flex-shrink: 0; }}
    .tab-btn {{ flex: 1; padding: 10px 2px; font-size: 12px; font-weight: 600; text-align: center; color: #8F96A0; cursor: pointer; border-bottom: 2px solid transparent; }}
    .tab-btn.active {{ color: #FFF; border-bottom: 2px solid #3B82F6; background: #16191E; }}
    .tab-content {{ padding: 12px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 9px; -webkit-overflow-scrolling: touch; }}

    /* 工具列與按鈕 */
    .toolbar {{ min-height: 48px; background: #16191E; border-bottom: 1px solid #282C34; display: flex; align-items: center; justify-content: space-between; padding: 4px 10px; z-index: 20; flex-wrap: wrap; gap: 6px; flex-shrink: 0; }}
    .btn-group {{ display: flex; gap: 5px; align-items: center; flex-wrap: wrap; }}
    button {{ background: #262B35; color: #FFF; border: 1px solid #3A4150; padding: 5px 9px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.15s; display: inline-flex; align-items: center; justify-content: center; gap: 4px; }}
    button:hover {{ background: #353C4A; }}
    button.active {{ background: #2563EB; border-color: #2563EB; color: #FFF; }}
    button.primary {{ background: #059669; border-color: #059669; }}
    button.danger {{ background: #DC2626; border-color: #DC2626; }}
    button.purple {{ background: #7C3AED; border-color: #7C3AED; }}
    
    .panel-title {{ font-size: 13px; font-weight: 600; color: #FFF; border-bottom: 1px solid #282C34; padding-bottom: 5px; margin-bottom: 2px; display: flex; justify-content: space-between; align-items: center; }}
    .field-group {{ display: flex; flex-direction: column; gap: 3px; margin-bottom: 4px; }}
    .field-group label {{ font-size: 11px; color: #9AA0A6; font-weight: 500; display: flex; justify-content: space-between; align-items: center; }}
    .field-row {{ display: flex; gap: 5px; }}
    .field-row > div {{ flex: 1; display: flex; flex-direction: column; gap: 2px; }}
    .field-row input, select {{ width: 100%; }}
    input[type="text"], input[type="number"], select {{ background: #0E1117; border: 1px solid #333842; color: #FFF; padding: 6px 7px; border-radius: 4px; font-size: 12px; }}
    input[type="text"]:focus, input[type="number"]:focus {{ border-color: #3B82F6; outline: none; }}
    input[type="color"] {{ width: 100%; height: 30px; border: 1px solid #333842; border-radius: 4px; background: #0E1117; cursor: pointer; }}
    
    /* 新增物件區 */
    .quick-add-box {{ background: #1C2029; border: 1px solid #2E3440; border-radius: 8px; padding: 8px; display: flex; flex-direction: column; gap: 5px; }}
    .quick-add-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }}
    .quick-add-sub {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 5px; }}
    .quick-add-sub button {{ padding: 5px 3px; font-size: 11px; }}

    /* 右側與左側分類拖曳清單 */
    .item-list {{ display: flex; flex-direction: column; gap: 8px; margin-top: 4px; flex: 1; overflow-y: auto; padding-right: 2px; -webkit-overflow-scrolling: touch; }}
    .cat-section {{ background: #14171C; border: 1px solid #262B35; border-radius: 6px; overflow: hidden; transition: border-color 0.2s, background 0.2s; }}
    .cat-section.drag-over {{ border: 2px dashed #3B82F6 !important; background: rgba(37, 99, 235, 0.15) !important; }}
    .cat-header {{ background: #1E222B; padding: 7px 10px; font-size: 12px; font-weight: 600; color: #93C5FD; display: flex; justify-content: space-between; align-items: center; cursor: pointer; }}
    .cat-items {{ padding: 6px; display: flex; flex-direction: column; gap: 5px; min-height: 28px; }}
    .item-card {{ background: #1F232B; border: 1px solid #2B303A; border-radius: 6px; padding: 7px 9px; cursor: grab; transition: all 0.15s; display: flex; flex-direction: column; gap: 3px; position: relative; }}
    .item-card:active {{ cursor: grabbing; }}
    .item-card:hover {{ border-color: #3B82F6; background: #252A35; }}
    .item-card.selected {{ border-color: #3B82F6; background: #1E293B; box-shadow: 0 0 0 1px #3B82F6; }}
    .item-card.dragging {{ opacity: 0.45; border: 1px dashed #60A5FA; }}
    .item-card-header {{ display: flex; justify-content: space-between; align-items: center; }}
    .item-card .name {{ font-weight: 600; font-size: 12px; color: #FFF; display: flex; align-items: center; gap: 5px; }}
    .item-card .badge {{ font-size: 10px; padding: 1px 4px; border-radius: 4px; background: #334155; color: #E2E8F0; }}
    .item-card .dims {{ font-size: 11px; color: #94A3B8; }}
    .card-del-btn {{ background: transparent; border: none; color: #94A3B8; padding: 2px 5px; font-size: 12px; border-radius: 4px; }}
    .card-del-btn:hover {{ background: #DC2626; color: #FFF; }}

    /* 畫布視角浮動控制 */
    .view-controls {{ position: absolute; top: 56px; left: 10px; display: flex; gap: 5px; z-index: 15; background: rgba(22,25,30,0.9); padding: 5px; border-radius: 8px; border: 1px solid #282C34; backdrop-filter: blur(4px); flex-wrap: wrap; max-width: calc(100vw - 20px); }}
    .view-controls button {{ padding: 4px 8px; font-size: 11px; }}

    /* 3D 人類視角與互動浮動控制面板 (HUD) */
    .fpv-hud {{ position: absolute; bottom: 60px; left: 50%; transform: translateX(-50%); z-index: 18; background: rgba(15, 23, 42, 0.94); border: 1px solid #3B82F6; border-radius: 12px; padding: 8px 12px; display: none; flex-direction: column; gap: 6px; align-items: center; box-shadow: 0 8px 25px rgba(0,0,0,0.7); min-width: 310px; max-width: 95vw; }}
    .dpad-grid {{ display: grid; grid-template-columns: repeat(3, 40px); gap: 4px; justify-content: center; }}
    .dpad-grid button {{ height: 36px; font-size: 14px; padding: 0; touch-action: none; }}

    /* 拖曳丟棄垃圾桶感應區 */
    .trash-dropzone {{ position: absolute; bottom: 68px; left: 50%; transform: translateX(-50%) scale(0.8); opacity: 0; pointer-events: none; z-index: 40; background: rgba(185, 28, 28, 0.92); border: 2px dashed #FCA5A5; color: #FFF; padding: 12px 24px; border-radius: 40px; font-size: 14px; font-weight: bold; display: flex; align-items: center; gap: 8px; transition: all 0.2s ease; box-shadow: 0 8px 24px rgba(220, 38, 38, 0.6); }}
    .trash-dropzone.show {{ opacity: 1; transform: translateX(-50%) scale(1); pointer-events: auto; }}
    .trash-dropzone.hover {{ background: #EF4444; transform: translateX(-50%) scale(1.12); border-color: #FFF; }}

    /* 碰撞提示吐司 */
    .toast-msg {{ position: absolute; top: 96px; left: 50%; transform: translateX(-50%); background: rgba(220, 38, 38, 0.9); color: #FFF; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; z-index: 35; opacity: 0; pointer-events: none; transition: opacity 0.2s; }}
    .toast-msg.show {{ opacity: 1; }}

    #canvas-container, #three-container {{ width: 100%; height: calc(100% - 48px); position: absolute; top: 48px; left: 0; touch-action: none; }}
    #three-container {{ display: none; }}

    /* 手機版響應式抽屜與導覽 */
    .mobile-top-toggles {{ display: none; gap: 4px; }}
    .mobile-nav {{ display: none; position: fixed; bottom: 0; left: 0; width: 100vw; height: 52px; background: #16191E; border-top: 1px solid #282C34; z-index: 50; justify-content: space-around; align-items: center; padding: 0 6px; }}
    .mobile-close-bar {{ display: none; justify-content: space-between; align-items: center; background: #1E293B; padding: 8px 12px; border-bottom: 1px solid #334155; font-size: 13px; font-weight: bold; color: #93C5FD; }}

    @media (max-width: 960px) {{
      .left-panel {{ position: fixed; left: 0; top: 0; height: calc(100dvh - 52px); transform: translateX(-105%); width: 88vw; max-width: 350px; box-shadow: 6px 0 20px rgba(0,0,0,0.7); }}
      .left-panel.open {{ transform: translateX(0); }}
      .right-panel {{ position: fixed; right: 0; top: 0; height: calc(100dvh - 52px); transform: translateX(105%); width: 88vw; max-width: 330px; box-shadow: -6px 0 20px rgba(0,0,0,0.7); }}
      .right-panel.open {{ transform: translateX(0); }}
      .mobile-nav {{ display: flex; }}
      .mobile-top-toggles {{ display: flex; }}
      .mobile-close-bar {{ display: flex; }}
      #canvas-container, #three-container {{ height: calc(100dvh - 100px); }}
      .toolbar .hint-text {{ display: none; }}
    }}
  </style>
</head>
<body>

<div class="app-container">
  <!-- 左側面板 -->
  <div class="left-panel" id="left-panel">
    <div class="mobile-close-bar">
      <span>⚙️ 物件編輯與空間設定</span>
      <button onclick="toggleMobilePanel('canvas')" class="danger" style="padding:3px 8px;">✕ 返回畫布</button>
    </div>
    <div class="tab-bar">
      <div class="tab-btn active" id="tab-btn-item" onclick="switchLeftTab('item')">✏️ 物件與分類</div>
      <div class="tab-btn" id="tab-btn-room" onclick="switchLeftTab('room')">🧭 地面/牆/飛星</div>
      <div class="tab-btn" id="tab-btn-human" onclick="switchLeftTab('human')">🚶 人物視角</div>
      <div class="tab-btn" id="tab-btn-save" onclick="switchLeftTab('save')">💾 存檔</div>
    </div>

    <!-- 標籤 1：物件編輯 + 分類選擇 + 門向控制 -->
    <div class="tab-content" id="tab-content-item">
      <div class="quick-add-box">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:11px; color:#93C5FD; font-weight:600;">➕ 新增時指派分類：</span>
          <select id="new-obj-category" style="width:135px; padding:3px 6px; font-size:11px;"></select>
        </div>
        <div class="quick-add-row">
          <button onclick="addNewObject('furniture')" style="background:#2563EB;border-color:#2563EB;">🛋️ 新增家具</button>
          <button onclick="addNewObject('door')" style="background:#9A3412;border-color:#9A3412;">🚪 新增房門</button>
        </div>
        <div class="quick-add-sub">
          <button onclick="addNewObject('window')" style="background:#D97706;border-color:#D97706;">🪟 窗戶</button>
          <button onclick="addNewObject('socket')" style="background:#EA580C;border-color:#EA580C;">🔌 插座</button>
          <button onclick="addNewObject('switch')" style="background:#0284C7;border-color:#0284C7;">💡 開關</button>
        </div>
      </div>

      <div id="no-selection" style="color: #94A3B8; font-size: 12px; margin: 6px 0; text-align: center; line-height: 1.5; background: #1F232B; padding: 10px; border-radius: 8px; border: 1px dashed #334155;">
        👈 <b>點選畫面或列表中的物件進行編輯</b><br>💡 右側與下方列表皆支援「按住物件拖曳至其他分類」自動改分類！
      </div>

      <div id="prop-editor" style="display: none;">
        <div class="panel-title">
          <span>✏️ 編輯選取物件</span>
          <span id="prop-type-badge" style="font-size:11px; color:#F59E0B;"></span>
        </div>

        <div class="field-group">
          <label>名稱與所屬分類 (選「床」則人物可踏上並疊加高度)</label>
          <div class="field-row">
            <input type="text" id="prop-name" style="flex:1.2;">
            <select id="prop-category" style="flex:1;"></select>
          </div>
        </div>

        <div class="field-group">
          <label>物件模型種類</label>
          <select id="prop-type">
            <option value="furniture">🛋️ 一般家具 / 床</option>
            <option value="door">🚪 房門 (Door)</option>
            <option value="window">🪟 窗戶 (Window)</option>
            <option value="socket">🔌 插座 (Socket)</option>
            <option value="switch">💡 開關 (Switch)</option>
          </select>
        </div>

        <div class="field-group">
          <label>尺寸：寬度 (W) × 深度 (D) × 高度 (H) cm</label>
          <div class="field-row">
            <div><span style="font-size:10px;color:#64748B;">寬度 W</span><input type="number" id="prop-w"></div>
            <div><span style="font-size:10px;color:#64748B;">深度 D</span><input type="number" id="prop-d"></div>
            <div><span style="font-size:10px;color:#64748B;">高度 H</span><input type="number" id="prop-h" placeholder="30"></div>
          </div>
        </div>

        <div class="field-group">
          <label>坐標：X × Y (可拉出房外) × <span style="color:#F59E0B;font-weight:bold;">Z 離地高</span></label>
          <div class="field-row">
            <div><span style="font-size:10px;color:#64748B;">X 坐標</span><input type="number" id="prop-x"></div>
            <div><span style="font-size:10px;color:#64748B;">Y 坐標</span><input type="number" id="prop-y"></div>
            <div><span style="font-size:10px;color:#F59E0B;">Z 離地高</span><input type="number" id="prop-z"></div>
          </div>
        </div>

        <div class="field-group" style="background:#1C2029; padding:7px; border-radius:6px; border:1px solid #2E3440;">
          <label><span>🔄 旋轉角度 (拖曳滑桿或輸入)</span><span id="prop-rot-val" style="color:#60A5FA;font-weight:bold;">0°</span></label>
          <input type="range" id="prop-rot-slider" min="0" max="360" value="0" style="width:100%;">
          <input type="number" id="prop-rot" min="0" max="360">
        </div>

        <!-- 房門專屬：開門方向與軸向翻轉控制 -->
        <div class="field-group" id="door-swing-group" style="display:none; background:#271712; padding:8px; border-radius:6px; border:1px solid #9A3412;">
          <label style="color:#FDBA74; font-weight:600;">🚪 門扇開啟方向編輯</label>
          <div class="field-row" style="margin-top:4px;">
            <button id="btn-door-flip-x" style="flex:1; background:#7C2D12;">↔️ 左右換邊開</button>
            <button id="btn-door-flip-y" style="flex:1; background:#7C2D12;">↕️ 內外推拉反轉</button>
          </div>
        </div>

        <div class="field-group">
          <label>顏色外觀 (調色盤)</label>
          <input type="color" id="prop-color">
        </div>

        <!-- 窗景上傳區 -->
        <div class="field-group" id="scenery-upload-group" style="display:none; background:#1E293B; padding:8px; border-radius:6px; border:1px solid #3B82F6;">
          <label style="color:#60A5FA; font-weight:600;">🗾 3D 窗戶景色 (預設：富士山美景)</label>
          <input type="file" id="prop-scenery-file" accept="image/*" style="font-size: 11px; color: #CBD5E1; margin-top:4px;">
          <button id="btn-reset-fuji" style="margin-top:4px; font-size:11px; padding:3px 8px;">🗻 恢復預設富士山景</button>
        </div>

        <!-- 表面材質上傳區 -->
        <div class="field-group" style="background:#1F232B; padding:7px; border-radius:6px; border:1px solid #334155;">
          <label id="texture-label" style="color:#E2E8F0;">🎨 上傳物件 / 門扇表面材質貼圖</label>
          <input type="file" id="prop-texture-file" accept="image/*" style="font-size: 11px; color: #8F96A0; margin-top:3px;">
          <button id="btn-clear-texture" style="margin-top:4px; font-size:11px; padding:3px 8px;">清除自訂材質</button>
        </div>

        <div style="display: flex; gap: 6px; margin-top: 6px;">
          <button id="btn-duplicate" style="flex: 1;">📋 複製物件</button>
          <button id="btn-delete" class="danger" style="flex: 1;">🗑️ 刪除 (Del)</button>
        </div>
      </div>

      <!-- 自訂分類增減管理區 -->
      <div class="panel-title" style="margin-top:8px;">🏷️ 分類管理 (可增減 / 可拖曳物件改分類)</div>
      <div class="field-row">
        <input type="text" id="new-cat-input" placeholder="輸入新分類名稱..." style="flex:1.5;">
        <button onclick="addCategory()" style="background:#2563EB;border-color:#2563EB;">➕ 新增分類</button>
      </div>
      <div id="category-tags-container" style="display:flex; flex-wrap:wrap; gap:5px; margin-top:4px;"></div>
    </div>

    <!-- 標籤 2：地面、3D白牆與天花板、留白處、坐向與九宮飛星 -->
    <div class="tab-content" id="tab-content-room" style="display: none;">
      <div style="background:#1E293B; border:1px solid #3B82F6; padding:7px 9px; border-radius:6px; display:flex; align-items:center; justify-content:space-between;">
        <span style="font-size:11px; font-weight:600; color:#93C5FD;">🔓 勾選才可拖曳/改動地面與留白處</span>
        <input type="checkbox" id="room-editable-lock" style="width:16px; height:16px; cursor:pointer;">
      </div>

      <div class="panel-title">🏠 房間地面尺寸 (cm)</div>
      <div class="field-row">
        <div><span style="font-size:10px;color:#64748B;">總寬度 X</span><input type="number" id="room-w" class="live-room-input"></div>
        <div><span style="font-size:10px;color:#64748B;">總深度 Y</span><input type="number" id="room-d" class="live-room-input"></div>
        <div><span style="font-size:10px;color:#64748B;">天花板高 Z</span><input type="number" id="room-h" class="live-room-input"></div>
      </div>

      <!-- 3D 牆壁與天花板顯示與貼圖設定 -->
      <div class="panel-title" style="margin-top:6px; color:#A7F3D0;">🧱 3D 牆壁與天花板設定 (預設白牆)</div>
      <div style="background:#1F232B; border:1px solid #334155; border-radius:6px; padding:8px; display:flex; flex-direction:column; gap:6px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:12px;">顯示四周實體牆壁 (3D)</span>
          <input type="checkbox" id="room-show-walls" class="live-room-input" checked style="width:16px;height:16px;">
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:12px;">顯示天花板頂面 (仰視推薦開啟)</span>
          <input type="checkbox" id="room-show-ceiling" class="live-room-input" style="width:16px;height:16px;">
        </div>
        <div class="field-row">
          <div><span style="font-size:10px;color:#94A3B8;">牆面顏色</span><input type="color" id="room-wall-color" class="live-room-input" value="#F8FAFC"></div>
          <div><span style="font-size:10px;color:#94A3B8;">天花板顏色</span><input type="color" id="room-ceil-color" class="live-room-input" value="#FFFFFF"></div>
        </div>
        <div class="field-group" style="margin:0;">
          <label>🖼️ 上傳牆壁材質貼圖</label>
          <input type="file" id="wall-texture-file" accept="image/*" style="font-size:11px;">
        </div>
        <div class="field-group" style="margin:0;">
          <label>🖼️ 上傳天花板材質貼圖</label>
          <input type="file" id="ceil-texture-file" accept="image/*" style="font-size:11px;">
        </div>
      </div>

      <!-- 留白處管理 -->
      <div class="panel-title" style="margin-top: 6px;">
        <span>🔲 留白處管理</span>
        <button onclick="addVoidArea()" style="padding:3px 7px; font-size:11px; background:#2563EB; border-color:#2563EB;">➕ 新增留白處</button>
      </div>
      <div id="void-list-container"></div>

      <!-- 八方羅盤設定 -->
      <div class="panel-title" style="margin-top: 6px;">🧭 八方坐向羅盤</div>
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:12px;">顯示八方坐向羅盤</span>
        <input type="checkbox" id="compass-show" class="live-room-input" checked style="width:16px; height:16px;">
      </div>
      <div class="field-row">
        <div><span style="font-size:10px;color:#64748B;">中心 X</span><input type="number" id="compass-x" class="live-room-input"></div>
        <div><span style="font-size:10px;color:#64748B;">中心 Y</span><input type="number" id="compass-y" class="live-room-input"></div>
      </div>
      <div class="field-group">
        <label><span>羅盤旋轉角度 (0°～360°)</span><span id="compass-rot-val">0°</span></label>
        <input type="range" id="compass-rot-slider" min="0" max="360" value="0" style="width:100%;">
        <input type="number" id="compass-rot" class="live-room-input" min="0" max="360">
      </div>

      <!-- 流年九宮飛星設定 -->
      <div class="panel-title" style="margin-top: 6px; color:#FBBF24;">☯️ 流年九宮飛星風水盤</div>
      <div style="background:#1F232B; border:1px solid #B45309; border-radius:6px; padding:8px; display:flex; flex-direction:column; gap:6px;">
        <div style="display:flex; align-items:center; justify-content:space-between;">
          <span style="font-size:12px; font-weight:600; color:#FDE68A;">顯示房間九宮飛星與吉凶</span>
          <input type="checkbox" id="feixing-show" class="live-room-input" style="width:16px; height:16px;">
        </div>
        <div class="field-row" style="align-items:center;">
          <input type="number" id="feixing-year" class="live-room-input" value="2026" min="1900" max="2100" style="font-weight:bold; color:#FEF08A;">
          <span id="feixing-center-info" style="font-size:11px; color:#F59E0B; white-space:nowrap;">2026年: 一白入中宮</span>
        </div>
      </div>
    </div>

    <!-- 標籤 3：人物模型與人類第一人稱視角設定 -->
    <div class="tab-content" id="tab-content-human" style="display: none;">
      <div class="panel-title" style="color:#C084FC;">🚶 人物身高與自然視角設定</div>
      <div style="font-size:11px; color:#94A3B8; line-height:1.4; background:#1F232B; padding:8px; border-radius:6px;">
        💡 <b>防誤觸保護</b>：3D 畫面中已鎖定人物高度拖拉，身高僅能在此處修改。<br>
        💡 <b>點擊地面移動</b>：在 3D 或人類視角中<b>直接點擊地板或床面</b>，人物會自動走過去（遇障礙物會阻擋、踏上床自動疊加床高）！
      </div>

      <div class="field-group">
        <label><span>👤 人物身高 (cm, 僅限此處編輯)</span><span id="human-eye-info" style="color:#A855F7;font-weight:bold;">自然眼高: 165 cm</span></label>
        <input type="number" id="human-height" value="178" min="80" max="230">
      </div>

      <div class="field-group">
        <label>人物姿勢切換 (同步影響 3D 人形與人類視角眼高)</label>
        <div class="quick-add-sub">
          <button id="btn-posture-stand" class="active" onclick="setHumanPosture('stand')">🧍 站立</button>
          <button id="btn-posture-sit" onclick="setHumanPosture('sit')">🪑 坐下</button>
          <button id="btn-posture-lie" onclick="setHumanPosture('lie')">🛏️ 躺下</button>
        </div>
      </div>

      <div class="field-group">
        <label><span>人物所在位置 X × Y (cm)</span><span id="human-basez-info" style="color:#34D399;">踏面高度 Z: 0 cm</span></label>
        <div class="field-row">
          <div><span style="font-size:10px;color:#64748B;">X 坐標</span><input type="number" id="human-x"></div>
          <div><span style="font-size:10px;color:#64748B;">Y 坐標</span><input type="number" id="human-y"></div>
        </div>
      </div>

      <div class="field-group">
        <label><span>🔄 人物水平視角面向 (0°～360°)</span><span id="human-rot-val" style="color:#C084FC;">0°</span></label>
        <input type="range" id="human-rot-slider" min="0" max="360" value="0" style="width:100%;">
        <input type="number" id="human-rot" min="0" max="360">
      </div>

      <div class="field-group">
        <label><span>📐 抬頭仰角 / 低頭俯角 (-85°～+85°)</span><span id="human-pitch-val" style="color:#38BDF8;">0°</span></label>
        <input type="range" id="human-pitch-slider" min="-85" max="85" value="0" style="width:100%;">
        <input type="number" id="human-pitch" min="-85" max="85">
      </div>

      <button onclick="enterHumanFPV()" class="purple" style="width:100%; padding:10px; font-size:13px; margin-top:4px;">
        👁️ 進入 3D 人類自然視角
      </button>
      <div class="field-row" style="margin-top:4px;">
        <button onclick="placeHumanOnBed('sit')" style="flex:1; padding:7px;">🪑 坐到床沿看房間</button>
        <button onclick="placeHumanOnBed('lie')" style="flex:1; padding:7px;">🛏️ 躺到床上仰視房間</button>
      </div>
    </div>

    <!-- 標籤 4：專案存檔 -->
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
        <div class="mobile-top-toggles">
          <button onclick="toggleMobilePanel('left')" style="background:#1E293B;border-color:#3B82F6;">⚙️ 編輯</button>
          <button onclick="toggleMobilePanel('right')" style="background:#1E293B;border-color:#3B82F6;">📋 分類列表</button>
        </div>
        <button id="btn-mode-2d" class="active">📐 2D 平面</button>
        <button id="btn-mode-3d">🧊 3D 鳥瞰互動</button>
        <button id="btn-mode-fpv" class="purple">👁️ 3D 人類視角</button>
      </div>
      <div class="hint-text" style="font-size: 11px; color: #94A3B8;">
        💡 3D與人類視角皆支援「<b>點擊地板或床面直接走過去</b>」 | 不可穿模，踏上床自動疊加高度
      </div>
    </div>

    <!-- 碰撞提示訊息 -->
    <div class="toast-msg" id="toast-msg">⚠️ 前方有家具或牆壁阻擋，無法穿越！</div>

    <!-- 2D 浮動控制列 -->
    <div class="view-controls" id="view-controls-2d">
      <button id="btn-zoom-in">➕ 放大</button>
      <button id="btn-zoom-out">➖ 縮小</button>
      <button id="btn-zoom-fit">🔍 居中</button>
      <button id="btn-pan-toggle">✋ 強制平移: 關</button>
      <button onclick="deleteSelectedActive()" class="danger">🗑️ 刪除選取</button>
    </div>

    <!-- 3D 互動控制器切換列 -->
    <div class="view-controls" id="view-controls-3d" style="display:none;">
      <span style="font-size:11px;color:#93C5FD;padding:3px 4px;">💡 點擊地面可讓人物走過去 | 點選物件：</span>
      <button id="btn-3d-translate" class="active" onclick="set3DGizmoMode('translate')">✥ 移動</button>
      <button id="btn-3d-rotate" onclick="set3DGizmoMode('rotate')">🔄 旋轉</button>
      <button id="btn-3d-scale" onclick="set3DGizmoMode('scale')">↔️ 縮放家具</button>
      <button onclick="deleteSelectedActive()" class="danger">🗑️ 刪除</button>
    </div>

    <!-- 3D 人類第一人稱視角 (FPV) 專屬操控 HUD -->
    <div class="fpv-hud" id="fpv-hud">
      <div style="display:flex; justify-content:space-between; width:100%; align-items:center; gap:6px;">
        <span id="fpv-status-text" style="font-size:11px; font-weight:bold; color:#DDD6FE;">👆 點擊地面走過去 | 拖曳畫面轉頭 | 按方向鍵移動</span>
        <button onclick="exitHumanFPV()" class="danger" style="padding:3px 8px; font-size:11px;">退出視角</button>
      </div>
      <!-- 姿勢同步切換列 (站 / 坐 / 躺) -->
      <div style="display:flex; gap:5px; width:100%;">
        <button id="hud-btn-stand" style="flex:1;" onclick="setHumanPosture('stand')">🧍 站立</button>
        <button id="hud-btn-sit" style="flex:1;" onclick="setHumanPosture('sit')">🪑 坐姿</button>
        <button id="hud-btn-lie" style="flex:1;" onclick="setHumanPosture('lie')">🛏️ 躺姿仰視</button>
      </div>
      <div style="display:flex; gap:12px; align-items:center; width:100%; justify-content:center;">
        <div class="dpad-grid">
          <div></div>
          <button id="dpad-up">▲</button>
          <div></div>
          <button id="dpad-left">◀</button>
          <button onclick="placeHumanOnBed('sit')" title="移至床上" style="font-size:12px;background:#7C3AED;">🛏️</button>
          <button id="dpad-right">▶</button>
          <div></div>
          <button id="dpad-down">▼</button>
          <div></div>
        </div>
        <div style="display:flex; flex-direction:column; gap:4px; flex:1; max-width:155px;">
          <label style="font-size:10px; color:#CBD5E1; display:flex; justify-content:space-between;">
            <span>視角仰角</span><span id="hud-pitch-lbl" style="color:#38BDF8;font-weight:bold;">0°</span>
          </label>
          <input type="range" id="hud-pitch-slider" min="-85" max="85" value="0" style="width:100%;">
          <div id="hud-eye-height-lbl" style="font-size:10px; color:#34D399; text-align:center;">目前眼高: 165 cm</div>
        </div>
      </div>
    </div>

    <!-- 畫面底部拖曳丟棄垃圾桶 -->
    <div class="trash-dropzone" id="trash-dropzone">
      🗑️ 放開滑鼠/手指即可刪除此物件
    </div>
    
    <div id="canvas-container">
      <canvas id="fabric-canvas"></canvas>
    </div>
    <div id="three-container"></div>
  </div>

  <!-- 右側分類物件清單 (支援拖曳物件改分類) -->
  <div class="right-panel" id="right-panel">
    <div class="mobile-close-bar">
      <span>📋 空間分類物件列表</span>
      <button onclick="toggleMobilePanel('canvas')" class="danger" style="padding:3px 8px;">✕ 返回畫布</button>
    </div>
    <div class="panel-title">
      <span>📋 分類列表 (按住物件可拖曳改分類)</span>
      <span id="obj-count" style="font-size: 11px; color: #94A3B8;">0</span>
    </div>
    <div class="quick-add-sub" style="margin-bottom:4px;">
      <button onclick="addNewObject('furniture')" style="background:#2563EB;border-color:#2563EB;">+ 家具</button>
      <button onclick="addNewObject('door')" style="background:#9A3412;border-color:#9A3412;">+ 房門</button>
      <button onclick="addNewObject('window')" style="background:#D97706;border-color:#D97706;">+ 窗/電</button>
    </div>
    <div class="item-list" id="item-list-container"></div>
  </div>

  <!-- 手機版底部固定導覽列 -->
  <div class="mobile-nav">
    <button id="mnav-left" onclick="toggleMobilePanel('left')">⚙️ 左側編輯</button>
    <button id="mnav-canvas" onclick="toggleMobilePanel('canvas')" class="active">📐 中間畫布</button>
    <button id="mnav-right" onclick="toggleMobilePanel('right')">📋 右側分類列表</button>
  </div>
</div>

<script>
  let appState = {initial_data_json};
  if (!appState.voids && appState.void) {{
    appState.voids = [{{ id: "void_1", name: "留白處 1", x: appState.void.x, y: appState.void.y, w: appState.void.w, d: appState.void.d }}];
  }}
  if (!appState.categories) appState.categories = ["床", "大型家具", "收納櫃體", "門窗建材", "機電開關"];
  if (!appState.categories.includes("床")) appState.categories.unshift("床");
  // 將名稱為床的物件預設歸入「床」分類
  appState.items.forEach(it => {{ if (it.id === "bed" || it.name === "床") it.category = "床"; }});

  if (!appState.human) appState.human = {{ x: 230, y: 230, z: 0, height: 178, rot: 0, pitch: 0, posture: "stand" }};
  if (appState.room.show_walls === undefined) appState.room.show_walls = true;
  if (appState.room.show_ceiling === undefined) appState.room.show_ceiling = false;

  let activeId = null;
  let canvas, scene, camera, renderer, controls, transformControl;
  let currentMode = "2D";
  let gizmoMode = "translate";
  let selectable3DMeshes = [];
  let walkable3DMeshes = []; // 地板與床面，供點擊走過去使用
  let human3DGroup = null;
  let targetRingMesh = null;
  
  let isDraggingCanvas = false;
  let forcePanMode = false;
  let lastClientX = 0, lastClientY = 0;
  let touchStartDist = 0, touchStartZoom = 1;
  let isOverTrash = false;

  // FPV 與 3D 點擊走動及碰撞狀態
  let fpvMoveDir = {{ forward: 0, right: 0 }};
  let walkTarget = null; // {{ x, y }} 點擊地面目標點
  let isLookingFPV = false;
  let fpvLastX = 0, fpvLastY = 0;
  let toastTimeout = null;

  // 清單拖曳改分類狀態
  let draggedItemId = null;

  function showToast(msg) {{
    const el = document.getElementById("toast-msg");
    if (!el) return;
    el.innerText = msg;
    el.classList.add("show");
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => el.classList.remove("show"), 1800);
  }}

  // --- 物理碰撞偵測與踏上床面高度計算 ---
  function isBedItem(it) {{
    return it.category === "床" || it.id === "bed" || (it.name && it.name.includes("床") && !it.name.includes("櫃"));
  }}

  // 檢查 (nx, ny) 座標是否可通行（不可穿越非床類家具與四周牆壁；床可踏上去並疊加高度）
  function checkHumanWalkable(nx, ny) {{
    const radius = 14; // 人體碰撞半徑 cm
    const rw = appState.room.width, rd = appState.room.depth;

    // 若開啟實體牆壁，限制在房間牆內
    if (appState.room.show_walls) {{
      if (nx < radius || nx > rw - radius || ny < radius || ny > rd - radius) {{
        return {{ allowed: false, baseZ: appState.human.z || 0 }};
      }}
    }}

    let supportZ = 0;
    for (let i = 0; i < appState.items.length; i++) {{
      const it = appState.items[i];
      // 忽略高處窗戶、牆上高處開關插座
      if (it.item_type === "window" || it.item_type === "socket" || it.item_type === "switch") continue;
      if ((it.z || 0) > 120) continue;

      const rad = -(it.rot || 0) * Math.PI / 180;
      const cx = it.x + it.w / 2;
      const cy = it.y + it.d / 2;
      const dx = nx - cx;
      const dy = ny - cy;
      // 轉換至物件局部座標系檢查碰撞
      const lx = dx * Math.cos(rad) - dy * Math.sin(rad);
      const ly = dx * Math.sin(rad) + dy * Math.cos(rad);

      const halfW = it.w / 2;
      const halfD = it.d / 2;

      if (isBedItem(it)) {{
        // 床：允許踏上去！若中心點在床範圍內，疊加床的高度
        if (Math.abs(lx) <= halfW && Math.abs(ly) <= halfD) {{
          supportZ = Math.max(supportZ, (it.z || 0) + (it.h || 55));
        }}
      }} else if (it.item_type === "furniture") {{
        // 其他家具（衣櫃、書桌、床頭櫃、防潮箱）：阻擋不可穿越！
        if (Math.abs(lx) < halfW + radius && Math.abs(ly) < halfD + radius) {{
          return {{ allowed: false, baseZ: appState.human.z || 0 }};
        }}
      }}
    }}
    return {{ allowed: true, baseZ: supportZ }};
  }}

  // 嘗試移動人物至 (nx, ny)，支援沿牆滑動與床面高度疊加
  function tryMoveHumanTo(nx, ny, showBlockMsg = false) {{
    const res = checkHumanWalkable(nx, ny);
    if (res.allowed) {{
      appState.human.x = nx;
      appState.human.y = ny;
      appState.human.z = res.baseZ;
      return true;
    }}
    // 嘗試單軸滑動 (X 或 Y 分別移動)
    const resX = checkHumanWalkable(nx, appState.human.y);
    if (resX.allowed) {{
      appState.human.x = nx;
      appState.human.z = resX.baseZ;
      return true;
    }}
    const resY = checkHumanWalkable(appState.human.x, ny);
    if (resY.allowed) {{
      appState.human.y = ny;
      appState.human.z = resY.baseZ;
      return true;
    }}
    if (showBlockMsg) showToast("⚠️ 前方有家具阻擋，人物無法穿越！");
    return false;
  }}

  // 計算真實人類視角眼高 (站立 / 坐下 / 躺下 + 疊加床高)
  function getHumanEyeHeight() {{
    const h = appState.human;
    const stature = h.height || 178;
    const baseZ = h.z || 0; // 地面為 0，踏上床則為床高 (55cm)

    if (h.posture === "lie") {{
      // 躺姿：踏面高度 + 頭部枕高約 22cm
      return Math.round(baseZ + 22);
    }} else if (h.posture === "sit") {{
      // 坐姿：若在床上，座面即為床高 baseZ，加上人體坐姿眼高(約身高的 0.44 倍)；若在地面，模擬坐於標準 43cm 椅高或席地坐高(約身高的 0.68 倍)
      if (baseZ > 0) {{
        return Math.round(baseZ + stature * 0.44);
      }} else {{
        return Math.round(43 + stature * 0.44);
      }}
    }}
    // 站立平視：踏面高度 + 身高 * 0.93
    return Math.round(baseZ + stature * 0.93);
  }}

  // 九宮飛星資料庫
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
  const LUOSHU_OFFSETS = {{ "SE": -1, "S": 4, "SW": -3, "E": -2, "C": 0, "W": 2, "NE": 3, "N": -4, "NW": 1 }};

  function getCenterStarByYear(year) {{
    let mod = (2026 - year) % 9;
    let star = (1 + mod) % 9;
    return star <= 0 ? star + 9 : star;
  }}
  function getStarAtDir(centerStar, dirKey) {{
    let s = (centerStar + LUOSHU_OFFSETS[dirKey]) % 9;
    return s <= 0 ? s + 9 : s;
  }}

  // --- 手機面板抽屜切換 ---
  function toggleMobilePanel(target) {{
    const lp = document.getElementById("left-panel");
    const rp = document.getElementById("right-panel");
    document.getElementById("mnav-left").classList.toggle("active", target === 'left');
    document.getElementById("mnav-right").classList.toggle("active", target === 'right');
    document.getElementById("mnav-canvas").classList.toggle("active", target === 'canvas');

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

  // --- 分類系統增刪與拖曳放置目標區 ---
  function renderCategoryUI() {{
    const newCatSel = document.getElementById("new-obj-category");
    const propCatSel = document.getElementById("prop-category");
    const tagsBox = document.getElementById("category-tags-container");

    const curNewVal = newCatSel.value;
    const curPropVal = propCatSel.value;

    newCatSel.innerHTML = "";
    propCatSel.innerHTML = "";
    tagsBox.innerHTML = "";

    appState.categories.forEach((cat, idx) => {{
      newCatSel.add(new Option(cat, cat));
      propCatSel.add(new Option(cat, cat));

      const tag = document.createElement("div");
      tag.style.cssText = "background:#1F232B; border:1px solid #3B82F6; border-radius:14px; padding:4px 9px; font-size:11px; display:flex; align-items:center; gap:5px; transition:all 0.15s;";
      tag.setAttribute("data-cat", cat);
      tag.innerHTML = `<span>🏷️ ${{cat}}</span><span style="cursor:pointer;color:#F87171;font-weight:bold;" onclick="deleteCategory(${{idx}})">✕</span>`;

      // 支援把物件直接拖曳到左側分類標籤上改分類
      tag.addEventListener("dragover", e => {{ e.preventDefault(); tag.style.background = "#2563EB"; }});
      tag.addEventListener("dragleave", () => {{ tag.style.background = "#1F232B"; }});
      tag.addEventListener("drop", e => {{
        e.preventDefault();
        tag.style.background = "#1F232B";
        if (draggedItemId) moveItemToCategory(draggedItemId, cat);
      }});

      tagsBox.appendChild(tag);
    }});

    if (appState.categories.includes(curNewVal)) newCatSel.value = curNewVal;
    if (appState.categories.includes(curPropVal)) propCatSel.value = curPropVal;
  }}

  function moveItemToCategory(itemId, targetCat) {{
    const item = appState.items.find(i => i.id === itemId);
    if (!item) return;
    item.category = targetCat;
    draggedItemId = null;
    updateLeftItemPanel();
    renderRightPanel();
    // 重新計算人物是否踏在床分類上
    const check = checkHumanWalkable(appState.human.x, appState.human.y);
    appState.human.z = check.baseZ;
    initHumanFormValues();
    if (renderer) updateThreeScene();
  }}

  window.addCategory = function() {{
    const inp = document.getElementById("new-cat-input");
    const val = inp.value.trim();
    if (!val) return;
    if (!appState.categories.includes(val)) {{
      appState.categories.push(val);
      inp.value = "";
      renderCategoryUI();
      renderRightPanel();
    }}
  }};

  window.deleteCategory = function(idx) {{
    if (appState.categories.length <= 1) {{
      alert("至少需保留一個分類！");
      return;
    }}
    const removed = appState.categories.splice(idx, 1)[0];
    const fallback = appState.categories[0];
    appState.items.forEach(it => {{ if (it.category === removed) it.category = fallback; }});
    renderCategoryUI();
    renderRightPanel();
  }};

  // --- 鍵盤與觸控 D-Pad 移動控制 ---
  window.addEventListener("keydown", function(e) {{
    const tag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
    if (tag === "input" || tag === "textarea" || tag === "select") return;

    if (e.key === "Delete" || e.key === "Backspace") {{
      if (activeId && activeId !== "HUMAN") {{
        e.preventDefault();
        deleteItemById(activeId);
      }}
    }}
    if (currentMode === "FPV" || currentMode === "3D") {{
      if (e.key === "w" || e.key === "W" || e.key === "ArrowUp") {{ fpvMoveDir.forward = 1; walkTarget = null; }}
      if (e.key === "s" || e.key === "S" || e.key === "ArrowDown") {{ fpvMoveDir.forward = -1; walkTarget = null; }}
      if (e.key === "a" || e.key === "A" || e.key === "ArrowLeft") {{ fpvMoveDir.right = -1; walkTarget = null; }}
      if (e.key === "d" || e.key === "D" || e.key === "ArrowRight") {{ fpvMoveDir.right = 1; walkTarget = null; }}
    }}
  }});

  window.addEventListener("keyup", function(e) {{
    if (["w","W","s","S","ArrowUp","ArrowDown"].includes(e.key)) fpvMoveDir.forward = 0;
    if (["a","A","d","D","ArrowLeft","ArrowRight"].includes(e.key)) fpvMoveDir.right = 0;
  }});

  // 綁定手機與電腦通用的 D-Pad pointer 事件
  function bindDpadBtn(btnId, rightVal, forwardVal) {{
    const btn = document.getElementById(btnId);
    if (!btn) return;
    const start = (e) => {{ e.preventDefault(); e.stopPropagation(); walkTarget = null; fpvMoveDir.right = rightVal; fpvMoveDir.forward = forwardVal; }};
    const end = (e) => {{ e.preventDefault(); e.stopPropagation(); fpvMoveDir.right = 0; fpvMoveDir.forward = 0; }};
    btn.addEventListener("pointerdown", start);
    btn.addEventListener("pointerup", end);
    btn.addEventListener("pointerleave", end);
    btn.addEventListener("pointercancel", end);
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

    bindDpadBtn("dpad-up", 0, 1);
    bindDpadBtn("dpad-down", 0, -1);
    bindDpadBtn("dpad-left", -1, 0);
    bindDpadBtn("dpad-right", 1, 0);

    canvas.on('mouse:wheel', function(opt) {{
      const delta = opt.e.deltaY;
      let zoom = canvas.getZoom() * (0.999 ** delta);
      zoom = Math.min(Math.max(zoom, 0.2), 5);
      canvas.zoomToPoint({{ x: opt.e.offsetX, y: opt.e.offsetY }}, zoom);
      opt.e.preventDefault();
      opt.e.stopPropagation();
    }});

    canvas.on('mouse:down', function(opt) {{
      const evt = opt.e;
      const target = opt.target;
      const isSelectable = target && (target.itemId || target.isHuman || (target.voidId && appState.room.editable));

      if (!isSelectable || forcePanMode || evt.button === 1 || evt.altKey) {{
        isDraggingCanvas = true;
        const pt = (evt.touches && evt.touches[0]) ? evt.touches[0] : evt;
        lastClientX = pt.clientX;
        lastClientY = pt.clientY;
      }}
    }});

    canvas.on('mouse:move', function(opt) {{
      if (!isDraggingCanvas) return;
      const evt = opt.e;
      if (evt.touches && evt.touches.length > 1) return;
      const pt = (evt.touches && evt.touches[0]) ? evt.touches[0] : evt;
      const vpt = canvas.viewportTransform;
      vpt[4] += pt.clientX - lastClientX;
      vpt[5] += pt.clientY - lastClientY;
      canvas.requestRenderAll();
      lastClientX = pt.clientX;
      lastClientY = pt.clientY;
    }});

    canvas.on('mouse:up', function() {{
      isDraggingCanvas = false;
      const trashEl = document.getElementById("trash-dropzone");
      if (trashEl.classList.contains("show")) {{
        if (isOverTrash && activeId && activeId !== "HUMAN") {{
          deleteItemById(activeId);
        }}
        trashEl.classList.remove("show", "hover");
        isOverTrash = false;
      }}
    }});

    const upperCanvas = canvas.upperCanvasEl;
    upperCanvas.addEventListener('touchstart', function(e) {{
      if (e.touches.length === 2) {{
        isDraggingCanvas = false;
        touchStartDist = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
        touchStartZoom = canvas.getZoom();
      }}
    }}, {{ passive: false }});

    upperCanvas.addEventListener('touchmove', function(e) {{
      if (e.touches.length === 2 && touchStartDist > 0) {{
        e.preventDefault();
        const dist = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
        let newZoom = Math.min(Math.max(touchStartZoom * (dist / touchStartDist), 0.2), 4.5);
        const cx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
        const cy = (e.touches[0].clientY + e.touches[1].clientY) / 2;
        canvas.zoomToPoint({{ x: cx, y: cy }}, newZoom);
      }}
    }}, {{ passive: false }});

    canvas.on('selection:created', onObjectSelected);
    canvas.on('selection:updated', onObjectSelected);
    canvas.on('selection:cleared', onObjectDeselected);
    canvas.on('object:moving', onObjectLiveMoving);
    canvas.on('object:scaling', onObjectLiveMoving);
    canvas.on('object:rotating', onObjectLiveMoving);
    canvas.on('object:modified', onObjectModifiedComplete);

    // 初始計算人物腳下高度
    const initWalk = checkHumanWalkable(appState.human.x, appState.human.y);
    appState.human.z = initWalk.baseZ;

    renderCategoryUI();
    initRoomFormValues();
    initHumanFormValues();
    renderVoidListUI();
    renderFullScene();
    zoomToFit();
  }}

  // --- 繪製 2D 完整場景 ---
  function renderFullScene() {{
    if (!canvas) return;
    canvas.clear();
    canvas.backgroundColor = '#0A0C10';

    const rw = appState.room.width, rd = appState.room.depth;

    canvas.add(new fabric.Rect({{
      left: 0, top: 0, width: rw, height: rd,
      fill: '#5089C6', stroke: '#38BDF8', strokeWidth: 2,
      selectable: false, evented: false
    }}));

    canvas.add(new fabric.Text(`◀ 房間寬 ${{rw}} cm ▶`, {{
      left: rw / 2, top: -20, fontSize: 13, fill: '#94A3B8', originX: 'center', selectable: false, evented: false
    }}));
    canvas.add(new fabric.Text(`◀ 房間深 ${{rd}} cm ▶`, {{
      left: -20, top: rd / 2, fontSize: 13, fill: '#94A3B8', originX: 'center', angle: -90, selectable: false, evented: false
    }}));

    const canEditGround = !!appState.room.editable && !forcePanMode;
    appState.voids.forEach(v => {{
      const vRect = new fabric.Rect({{
        width: v.w, height: v.d, fill: '#FFFFFF',
        stroke: canEditGround ? '#2563EB' : '#CBD5E1',
        strokeWidth: canEditGround ? 2.5 : 1.5,
        strokeDashArray: canEditGround ? [5, 3] : null,
        originX: 'center', originY: 'center'
      }});
      const vLabel = new fabric.Text(`${{v.name}}\n${{Math.round(v.w)}}×${{Math.round(v.d)}}`, {{
        fontSize: 12, fill: '#334155', originX: 'center', originY: 'center', textAlign: 'center'
      }});
      const vGroup = new fabric.Group([vRect, vLabel], {{
        left: v.x + v.w / 2, top: v.y + v.d / 2,
        originX: 'center', originY: 'center',
        selectable: canEditGround, evented: canEditGround, voidId: v.id
      }});
      vGroup.setControlsVisibility({{ mtr: false }});
      canvas.add(vGroup);
    }});

    appState.items.forEach(item => createFabricItem(item));

    if (appState.compass.show_feixing) renderNinePalaceFeixing();
    if (appState.compass.show) renderExpertCompass();

    createFabricHuman();

    if (activeId === "HUMAN") {{
      const hg = canvas.getObjects().find(o => o.isHuman);
      if (hg && !forcePanMode) canvas.setActiveObject(hg);
    }} else if (activeId) {{
      const g = canvas.getObjects().find(o => o.itemId === activeId);
      if (g && !forcePanMode) canvas.setActiveObject(g);
    }}

    renderRightPanel();
    canvas.requestRenderAll();
    if ((currentMode === "3D" || currentMode === "FPV") && renderer) updateThreeScene();
  }}

  function createFabricHuman() {{
    const h = appState.human;
    const fovCone = new fabric.Polygon([
      {{ x: 0, y: 0 }}, {{ x: -32, y: -65 }}, {{ x: 32, y: -65 }}
    ], {{
      fill: 'rgba(168, 85, 247, 0.32)', stroke: '#C084FC', strokeWidth: 1.5,
      originX: 'center', originY: 'bottom', top: 0
    }});

    const postureColor = h.posture === 'lie' ? '#EC4899' : (h.posture === 'sit' ? '#0EA5E9' : '#9333EA');
    const postureIcon = h.posture === 'lie' ? "🛏️" : (h.posture === 'sit' ? "🪑" : "🧍");

    const bodyCircle = new fabric.Circle({{
      radius: 14, fill: postureColor, stroke: '#FFFFFF', strokeWidth: 2.5,
      originX: 'center', originY: 'center'
    }});

    const iconTxt = new fabric.Text(postureIcon, {{
      fontSize: 14, originX: 'center', originY: 'center'
    }});

    const humanGroup = new fabric.Group([fovCone, bodyCircle, iconTxt], {{
      left: h.x, top: h.y, angle: h.rot || 0,
      originX: 'center', originY: 'center',
      selectable: !forcePanMode, evented: !forcePanMode,
      isHuman: true
    }});

    humanGroup.setControlsVisibility({{
      mt: false, mb: false, ml: false, mr: false,
      tl: false, tr: false, bl: false, br: false,
      mtr: true
    }});

    canvas.add(humanGroup);
  }}

  function createFabricItem(item) {{
    const subElements = [];
    const rect = new fabric.Rect({{
      width: item.w, height: item.d,
      fill: item.color, stroke: '#1E293B', strokeWidth: 1.5,
      originX: 'center', originY: 'center'
    }});
    subElements.push(rect);

    if (item.item_type === "door") {{
      const fx = item.flip_x ? -1 : 1;
      const fy = item.flip_y ? -1 : 1;
      const hx = -item.w / 2 * fx;
      const hy = item.d / 2 * fy;
      const openX = hx;
      const openY = hy + item.w * fy;
      const closedX = item.w / 2 * fx;
      const closedY = hy;
      const sweep = (fx * fy > 0) ? 0 : 1;

      const arcPath = new fabric.Path(`M ${{hx}} ${{hy}} L ${{openX}} ${{openY}} A ${{item.w}} ${{item.w}} 0 0 ${{sweep}} ${{closedX}} ${{closedY}}`, {{
        fill: 'rgba(251, 146, 60, 0.18)', stroke: '#FDBA74', strokeWidth: 1.5, strokeDashArray: [4, 3]
      }});
      subElements.push(arcPath);
    }}

    const labelStr = `${{item.name}}\n${{Math.round(item.w)}}×${{Math.round(item.d)}}`;
    const fontSize = Math.max(9, Math.min(12, Math.min(item.w, item.d) * 0.45));
    const text = new fabric.Text(labelStr, {{
      fontSize: fontSize, fill: '#FFFFFF',
      originX: 'center', originY: 'center', textAlign: 'center'
    }});
    subElements.push(text);

    const group = new fabric.Group(subElements, {{
      left: item.x + item.w / 2, top: item.y + item.d / 2,
      angle: item.rot || 0, originX: 'center', originY: 'center',
      selectable: !forcePanMode, evented: !forcePanMode, itemId: item.id
    }});

    group.setControlsVisibility({{
      mt: true, mb: true, ml: true, mr: true,
      tl: true, tr: true, bl: true, br: true, mtr: true
    }});

    if (item.texture && item.item_type !== "window") {{
      fabric.Image.fromURL(item.texture, function(img) {{
        img.scaleToWidth(item.w);
        img.scaleToHeight(item.d);
        rect.set('fill', new fabric.Pattern({{ source: img.getElement(), repeat: 'repeat' }}));
        canvas.requestRenderAll();
      }});
    }}

    canvas.add(group);
  }}

  function renderNinePalaceFeixing() {{
    const rw = appState.room.width, rd = appState.room.depth;
    const cw = rw / 3, cd = rd / 3;
    const year = parseInt(appState.compass.feixing_year) || 2026;
    const centerStar = getCenterStarByYear(year);

    const infoEl = document.getElementById("feixing-center-info");
    if (infoEl) infoEl.innerText = `${{year}}年: ${{FEIXING_META[centerStar].name}}入中宮`;

    const rot = appState.compass.rotation || 0;
    const dirAngles = [
      {{ key: "W", deg: 0, label: "正西" }}, {{ key: "NW", deg: 45, label: "西北" }},
      {{ key: "N", deg: 90, label: "正北" }}, {{ key: "NE", deg: 135, label: "東北" }},
      {{ key: "E", deg: 180, label: "正東" }}, {{ key: "SE", deg: 225, label: "東南" }},
      {{ key: "S", deg: 270, label: "正南" }}, {{ key: "SW", deg: 315, label: "西南" }}
    ];

    for (let row = 0; row < 3; row++) {{
      for (let col = 0; col < 3; col++) {{
        const gx = col * cw, gy = row * cd;
        let dirKey = "C", dirLabel = "中宮";
        if (!(row === 1 && col === 1)) {{
          let cellDeg = Math.atan2(row - 1, col - 1) * 180 / Math.PI;
          if (cellDeg < 0) cellDeg += 360;
          let relDeg = (cellDeg - rot) % 360;
          if (relDeg < 0) relDeg += 360;
          const idx = Math.round(relDeg / 45) % 8;
          dirKey = dirAngles[idx].key;
          dirLabel = dirAngles[idx].label;
        }}
        const starNum = getStarAtDir(centerStar, dirKey);
        const meta = FEIXING_META[starNum];

        canvas.add(new fabric.Rect({{
          left: gx, top: gy, width: cw, height: cd,
          fill: meta.bg, stroke: '#F59E0B', strokeWidth: 1.5, strokeDashArray: [6, 4],
          selectable: false, evented: false
        }}));
        canvas.add(new fabric.Text(`【${{dirLabel}}】${{meta.name}} (${{meta.el}})`, {{
          left: gx + cw / 2, top: gy + 18, fontSize: 13, fontWeight: 'bold', fill: meta.color,
          backgroundColor: 'rgba(10, 12, 16, 0.82)', originX: 'center', originY: 'center', selectable: false, evented: false
        }}));
        canvas.add(new fabric.Text(`${{meta.luck}}\n${{meta.tip}}`, {{
          left: gx + cw / 2, top: gy + 42, fontSize: 11, fill: '#F8FAFC',
          backgroundColor: 'rgba(15, 23, 42, 0.78)', originX: 'center', originY: 'center', textAlign: 'center', selectable: false, evented: false
        }}));
      }}
    }}
  }}

  function renderExpertCompass() {{
    const cx = appState.compass.x, cy = appState.compass.y;
    const rot = appState.compass.rotation || 0;
    const radius = Math.max(appState.room.width, appState.room.depth) * 0.72;

    [radius * 0.25, radius * 0.5, radius * 0.75, radius].forEach((r, idx) => {{
      canvas.add(new fabric.Circle({{
        left: cx - r, top: cy - r, radius: r, fill: 'transparent',
        stroke: idx === 3 ? 'rgba(255, 255, 255, 0.45)' : 'rgba(255, 255, 255, 0.16)',
        strokeWidth: idx === 3 ? 1.8 : 1, strokeDashArray: idx % 2 === 1 ? [5, 5] : null,
        selectable: false, evented: false
      }}));
    }});

    const directions = [
      {{ deg: 0, label: "正西 [兌]", primary: true }}, {{ deg: 45, label: "西北 [乾]", primary: false }},
      {{ deg: 90, label: "正北 [坎]", primary: true }}, {{ deg: 135, label: "東北 [艮]", primary: false }},
      {{ deg: 180, label: "正東 [震]", primary: true }}, {{ deg: 225, label: "東南 [巽]", primary: false }},
      {{ deg: 270, label: "正南 [離]", primary: true }}, {{ deg: 315, label: "西南 [坤]", primary: false }}
    ];

    directions.forEach(dir => {{
      const rad = (dir.deg + rot) * Math.PI / 180;
      canvas.add(new fabric.Line([cx, cy, cx + radius * Math.cos(rad), cy + radius * Math.sin(rad)], {{
        stroke: dir.primary ? 'rgba(255, 255, 255, 0.8)' : 'rgba(255, 255, 255, 0.35)',
        strokeWidth: dir.primary ? 2.2 : 1.2, selectable: false, evented: false
      }}));
      canvas.add(new fabric.Text(dir.label, {{
        left: cx + (radius + 24) * Math.cos(rad), top: cy + (radius + 24) * Math.sin(rad),
        fontSize: dir.primary ? 14 : 11, fontWeight: dir.primary ? 'bold' : 'normal',
        fill: dir.primary ? '#F3E8FF' : '#CBD5E1',
        backgroundColor: dir.primary ? 'rgba(107, 33, 168, 0.78)' : 'rgba(15, 23, 42, 0.68)',
        originX: 'center', originY: 'center', selectable: false, evented: false
      }}));
    }});
  }}

  // --- 2D 選取、人物防穿模拖曳與垃圾桶感應 ---
  function onObjectSelected(e) {{
    const target = e.selected ? e.selected[0] : null;
    if (!target) return;
    if (target.isHuman) {{
      activeId = "HUMAN";
      switchLeftTab('human');
      initHumanFormValues();
      highlightRightPanel();
    }} else if (target.itemId) {{
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

  function onObjectLiveMoving(e) {{
    const target = e.target;
    if (!target) return;

    if (target.itemId && e.e) {{
      const trashEl = document.getElementById("trash-dropzone");
      trashEl.classList.add("show");
      const pt = (e.e.touches && e.e.touches[0]) ? e.e.touches[0] : e.e;
      const rect = trashEl.getBoundingClientRect();
      isOverTrash = (pt.clientX >= rect.left - 20 && pt.clientX <= rect.right + 20 && pt.clientY >= rect.top - 20 && pt.clientY <= rect.bottom + 20);
      trashEl.classList.toggle("hover", isOverTrash);
    }}

    if (target.isHuman) {{
      // 2D 拖曳人物時同樣執行碰撞檢測與床高疊加
      const nx = Math.round(target.left);
      const ny = Math.round(target.top);
      const check = checkHumanWalkable(nx, ny);
      if (check.allowed) {{
        appState.human.x = nx;
        appState.human.y = ny;
        appState.human.z = check.baseZ;
      }} else {{
        // 阻擋穿模，退回原合法座標
        target.set({{ left: appState.human.x, top: appState.human.y }});
        showToast("⚠️ 人物不可穿越家具物件！");
      }}
      appState.human.rot = Math.round((target.angle % 360 + 360) % 360);
      initHumanFormValues();
    }} else if (target.itemId) {{
      const item = appState.items.find(i => i.id === target.itemId);
      if (!item) return;

      if (target.flipX) {{
        item.flip_x = !item.flip_x;
        target.set('flipX', false);
      }}
      if (target.flipY) {{
        item.flip_y = !item.flip_y;
        target.set('flipY', false);
      }}

      const baseRect = target.item(0);
      const newW = Math.max(4, Math.round(baseRect.width * Math.abs(target.scaleX)));
      const newD = Math.max(4, Math.round(baseRect.height * Math.abs(target.scaleY)));
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
      v.w = Math.max(10, Math.round(baseRect.width * Math.abs(target.scaleX)));
      v.d = Math.max(10, Math.round(baseRect.height * Math.abs(target.scaleY)));
      v.x = Math.round(target.left - v.w / 2);
      v.y = Math.round(target.top - v.d / 2);
      renderVoidListUI();
    }}
  }}

  function onObjectModifiedComplete(e) {{
    const trashEl = document.getElementById("trash-dropzone");
    if (isOverTrash && activeId && activeId !== "HUMAN") {{
      trashEl.classList.remove("show", "hover");
      isOverTrash = false;
      deleteItemById(activeId);
      return;
    }}
    trashEl.classList.remove("show", "hover");
    isOverTrash = false;
    onObjectLiveMoving(e);
    renderFullScene();
  }}

  function setInputValueSafe(id, val) {{
    const el = document.getElementById(id);
    if (el && document.activeElement !== el) {{
      el.value = val;
    }}
  }}

  function updateLeftItemPanel() {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;

    document.getElementById("no-selection").style.display = "none";
    document.getElementById("prop-editor").style.display = "block";

    const typeNames = {{
      furniture: "🛋️ 家具 / 床",
      door: "🚪 房門 (支援開向翻轉)",
      window: "🪟 窗戶 (3D富士山窗景)",
      socket: "🔌 牆壁插座 (3D擬真)",
      switch: "💡 牆壁開關 (3D擬真)"
    }};
    document.getElementById("prop-type-badge").innerText = typeNames[item.item_type || "furniture"];

    setInputValueSafe("prop-name", item.name);
    setInputValueSafe("prop-category", item.category || appState.categories[0]);
    setInputValueSafe("prop-type", item.item_type || "furniture");
    setInputValueSafe("prop-w", Math.round(item.w));
    setInputValueSafe("prop-d", Math.round(item.d));
    setInputValueSafe("prop-h", item.h || 30);
    setInputValueSafe("prop-x", Math.round(item.x));
    setInputValueSafe("prop-y", Math.round(item.y));
    setInputValueSafe("prop-z", Math.round(item.z || 0));
    setInputValueSafe("prop-rot", item.rot || 0);
    setInputValueSafe("prop-rot-slider", item.rot || 0);
    document.getElementById("prop-rot-val").innerText = (item.rot || 0) + "°";
    setInputValueSafe("prop-color", item.color);

    document.getElementById("door-swing-group").style.display = (item.item_type === "door") ? "flex" : "none";
    document.getElementById("scenery-upload-group").style.display = (item.item_type === "window") ? "flex" : "none";
  }}

  function updateSingleItemVisual(item) {{
    if (item.item_type === "door") {{
      renderFullScene();
      return;
    }}
    const group = canvas ? canvas.getObjects().find(o => o.itemId === item.id) : null;
    if (group) {{
      const rect = group.item(0);
      const txt = group.item(group.size() - 1);
      rect.set({{ width: item.w, height: item.d, fill: item.color }});
      const fontSize = Math.max(9, Math.min(12, Math.min(item.w, item.d) * 0.45));
      txt.set({{ text: `${{item.name}}\n${{Math.round(item.w)}}×${{Math.round(item.d)}}`, fontSize: fontSize }});
      group.set({{
        width: item.w, height: item.d,
        left: item.x + item.w / 2,
        top: item.y + item.d / 2,
        angle: item.rot || 0
      }});
      group.setCoords();
      canvas.requestRenderAll();
    }}
    renderRightPanel();
    if ((currentMode === "3D" || currentMode === "FPV") && renderer) updateThreeScene();
  }}

  ["prop-name", "prop-category", "prop-type", "prop-w", "prop-d", "prop-h", "prop-x", "prop-y", "prop-z", "prop-rot", "prop-color"].forEach(id => {{
    document.getElementById(id).addEventListener("input", (e) => {{
      const item = appState.items.find(i => i.id === activeId);
      if (!item) return;

      const rawVal = e.target.value;
      if (id === "prop-name") item.name = rawVal;
      else if (id === "prop-category") item.category = rawVal;
      else if (id === "prop-type") {{
        item.item_type = rawVal;
        if (rawVal === "window" && !item.scenery) item.scenery = appState.default_fuji;
        updateLeftItemPanel();
        renderFullScene();
        return;
      }} else if (id === "prop-color") {{
        item.color = rawVal;
      }} else {{
        if (rawVal === "" || rawVal === "-") return;
        const num = parseFloat(rawVal);
        if (isNaN(num)) return;
        if (id === "prop-w") item.w = Math.max(1, num);
        if (id === "prop-d") item.d = Math.max(1, num);
        if (id === "prop-h") item.h = Math.max(1, num);
        if (id === "prop-x") item.x = num;
        if (id === "prop-y") item.y = num;
        if (id === "prop-z") item.z = num;
        if (id === "prop-rot") {{
          item.rot = ((num % 360) + 360) % 360;
          document.getElementById("prop-rot-slider").value = item.rot;
          document.getElementById("prop-rot-val").innerText = Math.round(item.rot) + "°";
        }}
      }}
      updateSingleItemVisual(item);
    }});
  }});

  document.getElementById("prop-rot-slider").addEventListener("input", e => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.rot = parseFloat(e.target.value) || 0;
    document.getElementById("prop-rot").value = item.rot;
    document.getElementById("prop-rot-val").innerText = item.rot + "°";
    updateSingleItemVisual(item);
  }});

  document.getElementById("btn-door-flip-x").addEventListener("click", () => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.flip_x = !item.flip_x;
    renderFullScene();
  }});
  document.getElementById("btn-door-flip-y").addEventListener("click", () => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.flip_y = !item.flip_y;
    renderFullScene();
  }});

  document.getElementById("prop-scenery-file").addEventListener("change", function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(f) {{
      const item = appState.items.find(i => i.id === activeId);
      if (!item) return;
      item.scenery = f.target.result;
      if (renderer) updateThreeScene();
    }};
    reader.readAsDataURL(file);
  }});
  document.getElementById("btn-reset-fuji").addEventListener("click", () => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.scenery = appState.default_fuji;
    if (renderer) updateThreeScene();
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

  // --- 新增、複製、刪除物件 ---
  function addNewObject(type) {{
    const chosenCat = document.getElementById("new-obj-category").value || appState.categories[0];
    let newItem;
    if (type === 'window') {{
      newItem = {{ id: "win_" + Date.now(), name: "窗戶", category: chosenCat, item_type: "window", x: 150, y: 348, z: 85, w: 120, d: 12, h: 130, rot: 0, color: "#F59E0B", texture: "", scenery: appState.default_fuji, flip_x: false, flip_y: false }};
    }} else if (type === 'socket') {{
      newItem = {{ id: "soc_" + Date.now(), name: "插座", category: chosenCat, item_type: "socket", x: 280, y: 348, z: 30, w: 22, d: 12, h: 14, rot: 0, color: "#F97316", texture: "", scenery: "", flip_x: false, flip_y: false }};
    }} else if (type === 'switch') {{
      newItem = {{ id: "sw_" + Date.now(), name: "開關", category: chosenCat, item_type: "switch", x: 240, y: 348, z: 110, w: 22, d: 12, h: 14, rot: 0, color: "#0EA5E9", texture: "", scenery: "", flip_x: false, flip_y: false }};
    }} else if (type === 'door') {{
      newItem = {{ id: "door_" + Date.now(), name: "房門", category: chosenCat, item_type: "door", x: 20, y: 346, z: 0, w: 90, d: 14, h: 210, rot: 0, color: "#8B5A2B", texture: "", scenery: "", flip_x: false, flip_y: false }};
    }} else {{
      newItem = {{ id: "item_" + Date.now(), name: chosenCat === "床" ? "雙人床" : "新家具", category: chosenCat, item_type: "furniture", x: 140, y: 140, z: 0, w: chosenCat === "床" ? 152 : 60, d: chosenCat === "床" ? 195 : 50, h: chosenCat === "床" ? 55 : 30, rot: 0, color: chosenCat === "床" ? "#FAD785" : "#38BDF8", texture: "", scenery: "", flip_x: false, flip_y: false }};
    }}
    appState.items.push(newItem);
    activeId = newItem.id;
    renderFullScene();
    selectItemById(newItem.id);
  }}

  window.deleteSelectedActive = function() {{
    if (activeId && activeId !== "HUMAN") deleteItemById(activeId);
  }};

  function deleteItemById(id, evt) {{
    if (evt) evt.stopPropagation();
    appState.items = appState.items.filter(i => i.id !== id);
    if (activeId === id) {{
      activeId = null;
      if (transformControl) transformControl.detach();
      onObjectDeselected();
    }}
    renderFullScene();
  }}

  document.getElementById("btn-delete").addEventListener("click", () => {{
    if (activeId && activeId !== "HUMAN") deleteItemById(activeId);
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

  // --- 地面、3D牆壁/天花板、留白處設定 ---
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
      card.style.cssText = "background:#1F232B; border:1px solid #334155; border-radius:6px; padding:7px; margin-bottom:5px; display:flex; flex-direction:column; gap:5px;";
      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <input type="text" value="${{v.name}}" ${{disabledAttr}} oninput="updateVoidField(${{idx}}, 'name', this.value)" style="width:125px; font-weight:600;">
          <button class="danger" ${{disabledAttr}} onclick="deleteVoidArea(${{idx}})" style="padding:2px 6px; font-size:11px;">🗑️ 刪除</button>
        </div>
        <div class="field-row">
          <div><span style="font-size:10px;color:#64748B;">寬 W</span><input type="number" value="${{Math.round(v.w)}}" ${{disabledAttr}} oninput="updateVoidField(${{idx}}, 'w', this.value)"></div>
          <div><span style="font-size:10px;color:#64748B;">深 D</span><input type="number" value="${{Math.round(v.d)}}" ${{disabledAttr}} oninput="updateVoidField(${{idx}}, 'd', this.value)"></div>
          <div><span style="font-size:10px;color:#64748B;">X</span><input type="number" value="${{Math.round(v.x)}}" ${{disabledAttr}} oninput="updateVoidField(${{idx}}, 'x', this.value)"></div>
          <div><span style="font-size:10px;color:#64748B;">Y</span><input type="number" value="${{Math.round(v.y)}}" ${{disabledAttr}} oninput="updateVoidField(${{idx}}, 'y', this.value)"></div>
        </div>
      `;
      container.appendChild(card);
    }});
  }}

  window.updateVoidField = function(idx, field, val) {{
    if (!appState.voids[idx]) return;
    if (field === 'name') appState.voids[idx].name = val;
    else {{
      if (val === "" || val === "-") return;
      appState.voids[idx][field] = parseFloat(val) || 0;
    }}
    renderFullScene();
  }};

  window.addVoidArea = function() {{
    if (!appState.room.editable) {{
      alert("💡 請先勾選上方「🔓 勾選才可拖曳/改動地面與留白處」！");
      return;
    }}
    appState.voids.push({{ id: "void_" + Date.now(), name: `留白處 ${{appState.voids.length + 1}}`, x: 50, y: 50, w: 80, d: 80 }});
    renderVoidListUI();
    renderFullScene();
  }};

  window.deleteVoidArea = function(idx) {{
    appState.voids.splice(idx, 1);
    renderVoidListUI();
    renderFullScene();
  }};

  function initRoomFormValues() {{
    document.getElementById("room-editable-lock").checked = !!appState.room.editable;
    setInputValueSafe("room-w", appState.room.width);
    setInputValueSafe("room-d", appState.room.depth);
    setInputValueSafe("room-h", appState.room.height);
    document.getElementById("room-show-walls").checked = !!appState.room.show_walls;
    document.getElementById("room-show-ceiling").checked = !!appState.room.show_ceiling;
    setInputValueSafe("room-wall-color", appState.room.wall_color || "#F8FAFC");
    setInputValueSafe("room-ceil-color", appState.room.ceiling_color || "#FFFFFF");

    document.getElementById("compass-show").checked = appState.compass.show;
    setInputValueSafe("compass-x", appState.compass.x);
    setInputValueSafe("compass-y", appState.compass.y);
    setInputValueSafe("compass-rot", appState.compass.rotation || 0);
    setInputValueSafe("compass-rot-slider", appState.compass.rotation || 0);
    document.getElementById("compass-rot-val").innerText = (appState.compass.rotation || 0) + "°";

    document.getElementById("feixing-show").checked = !!appState.compass.show_feixing;
    setInputValueSafe("feixing-year", appState.compass.feixing_year || 2026);
  }}

  function syncRoomFromInputs(e) {{
    if (e && (e.target.value === "" || e.target.value === "-")) return;
    appState.room.width = parseFloat(document.getElementById("room-w").value) || 400;
    appState.room.depth = parseFloat(document.getElementById("room-d").value) || 300;
    appState.room.height = parseFloat(document.getElementById("room-h").value) || 280;
    appState.room.show_walls = document.getElementById("room-show-walls").checked;
    appState.room.show_ceiling = document.getElementById("room-show-ceiling").checked;
    appState.room.wall_color = document.getElementById("room-wall-color").value;
    appState.room.ceiling_color = document.getElementById("room-ceil-color").value;

    appState.compass.show = document.getElementById("compass-show").checked;
    appState.compass.x = parseFloat(document.getElementById("compass-x").value) || 200;
    appState.compass.y = parseFloat(document.getElementById("compass-y").value) || 150;
    appState.compass.rotation = parseFloat(document.getElementById("compass-rot").value) || 0;
    setInputValueSafe("compass-rot-slider", appState.compass.rotation);
    document.getElementById("compass-rot-val").innerText = appState.compass.rotation + "°";

    appState.compass.show_feixing = document.getElementById("feixing-show").checked;
    appState.compass.feixing_year = parseInt(document.getElementById("feixing-year").value) || 2026;

    renderFullScene();
  }}

  document.querySelectorAll(".live-room-input").forEach(el => {{
    el.addEventListener("input", syncRoomFromInputs);
  }});
  document.getElementById("compass-rot-slider").addEventListener("input", e => {{
    document.getElementById("compass-rot").value = e.target.value;
    syncRoomFromInputs();
  }});

  document.getElementById("wall-texture-file").addEventListener("change", function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(f) {{
      appState.room.wall_texture = f.target.result;
      if (renderer) updateThreeScene();
    }};
    reader.readAsDataURL(file);
  }});
  document.getElementById("ceil-texture-file").addEventListener("change", function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(f) {{
      appState.room.ceiling_texture = f.target.result;
      appState.room.show_ceiling = true;
      document.getElementById("room-show-ceiling").checked = true;
      if (renderer) updateThreeScene();
    }};
    reader.readAsDataURL(file);
  }});

  // --- 🚶 人物表單與站/坐/躺三種姿勢同步 ---
  function initHumanFormValues() {{
    const h = appState.human;
    const eyeH = getHumanEyeHeight();
    setInputValueSafe("human-height", h.height || 178);
    setInputValueSafe("human-x", Math.round(h.x));
    setInputValueSafe("human-y", Math.round(h.y));
    setInputValueSafe("human-rot", Math.round(h.rot || 0));
    setInputValueSafe("human-rot-slider", Math.round(h.rot || 0));
    document.getElementById("human-rot-val").innerText = Math.round(h.rot || 0) + "°";

    setInputValueSafe("human-pitch", Math.round(h.pitch || 0));
    setInputValueSafe("human-pitch-slider", Math.round(h.pitch || 0));
    setInputValueSafe("hud-pitch-slider", Math.round(h.pitch || 0));
    document.getElementById("human-pitch-val").innerText = Math.round(h.pitch || 0) + "°";
    document.getElementById("hud-pitch-lbl").innerText = Math.round(h.pitch || 0) + "°";

    document.getElementById("human-eye-info").innerText = `自然眼高: ${{eyeH}} cm`;
    document.getElementById("human-basez-info").innerText = `踏面高度 Z: ${{Math.round(h.z || 0)}} cm ${{h.z > 0 ? '(已在床上)' : ''}}`;
    const hudEyeLbl = document.getElementById("hud-eye-height-lbl");
    if (hudEyeLbl) hudEyeLbl.innerText = `目前眼高: ${{eyeH}} cm (踏面Z:${{Math.round(h.z || 0)}})`;

    const p = h.posture || "stand";
    ["stand", "sit", "lie"].forEach(mode => {{
      const b1 = document.getElementById("btn-posture-" + mode);
      const b2 = document.getElementById("hud-btn-" + mode);
      if (b1) b1.classList.toggle("active", p === mode);
      if (b2) b2.classList.toggle("active", p === mode);
    }});
  }}

  ["human-height", "human-x", "human-y", "human-rot", "human-pitch"].forEach(id => {{
    document.getElementById(id).addEventListener("input", e => {{
      if (e.target.value === "" || e.target.value === "-") return;
      const val = parseFloat(e.target.value) || 0;
      if (id === "human-height") appState.human.height = Math.max(60, val);
      if (id === "human-x") tryMoveHumanTo(val, appState.human.y, true);
      if (id === "human-y") tryMoveHumanTo(appState.human.x, val, true);
      if (id === "human-rot") appState.human.rot = ((val % 360) + 360) % 360;
      if (id === "human-pitch") appState.human.pitch = Math.max(-85, Math.min(85, val));
      initHumanFormValues();
      renderFullScene();
      if (currentMode === "FPV") syncFPVCamera();
    }});
  }});

  document.getElementById("human-rot-slider").addEventListener("input", e => {{
    appState.human.rot = parseFloat(e.target.value) || 0;
    initHumanFormValues();
    renderFullScene();
    if (currentMode === "FPV") syncFPVCamera();
  }});

  document.getElementById("human-pitch-slider").addEventListener("input", e => {{
    appState.human.pitch = parseFloat(e.target.value) || 0;
    initHumanFormValues();
    if (currentMode === "FPV") syncFPVCamera();
  }});

  document.getElementById("hud-pitch-slider").addEventListener("input", e => {{
    appState.human.pitch = parseFloat(e.target.value) || 0;
    initHumanFormValues();
    if (currentMode === "FPV") syncFPVCamera();
  }});

  window.setHumanPosture = function(p) {{
    appState.human.posture = p;
    if (p === "lie") {{
      appState.human.pitch = 35;
      appState.room.show_ceiling = true;
      document.getElementById("room-show-ceiling").checked = true;
    }} else if (p === "sit") {{
      appState.human.pitch = -5;
    }} else {{
      appState.human.pitch = 0;
    }}
    const check = checkHumanWalkable(appState.human.x, appState.human.y);
    appState.human.z = check.baseZ;
    initHumanFormValues();
    renderFullScene();
    if (currentMode === "FPV") syncFPVCamera();
  }};

  window.placeHumanOnBed = function(targetPosture = 'lie') {{
    const bed = appState.items.find(i => isBedItem(i));
    if (bed) {{
      appState.human.x = Math.round(bed.x + bed.w / 2);
      appState.human.y = Math.round(bed.y + (targetPosture === 'sit' ? bed.d * 0.78 : bed.d * 0.35));
      appState.human.z = (bed.z || 0) + (bed.h || 55);
      appState.human.rot = 180;
    }}
    setHumanPosture(targetPosture);
    enterHumanFPV();
  }};

  // --- 右側分類清單渲染 (支援滑鼠與觸控拖曳物件至其他分類) ---
  function renderRightPanel() {{
    const container = document.getElementById("item-list-container");
    document.getElementById("obj-count").innerText = `共 ${{appState.items.length}} 項`;
    container.innerHTML = "";

    const badgeMap = {{
      furniture: {{ text: "家具", cls: "" }},
      door: {{ text: "🚪 門", cls: "door" }},
      window: {{ text: "🪟 窗", cls: "win" }},
      socket: {{ text: "🔌 插座", cls: "win" }},
      switch: {{ text: "💡 開關", cls: "win" }}
    }};

    appState.categories.forEach(cat => {{
      const catItems = appState.items.filter(it => (it.category || appState.categories[0]) === cat);
      const sec = document.createElement("div");
      sec.className = "cat-section";
      sec.setAttribute("data-cat", cat);

      // 允許拖曳物件卡片放置到此分類區塊
      sec.addEventListener("dragover", e => {{
        e.preventDefault();
        sec.classList.add("drag-over");
      }});
      sec.addEventListener("dragleave", () => sec.classList.remove("drag-over"));
      sec.addEventListener("drop", e => {{
        e.preventDefault();
        sec.classList.remove("drag-over");
        if (draggedItemId) moveItemToCategory(draggedItemId, cat);
      }});

      const header = document.createElement("div");
      header.className = "cat-header";
      header.innerHTML = `<span>📁 ${{cat}} ${{cat === '床' ? '🛏️' : ''}}</span><span style="font-size:11px;color:#64748B;">${{catItems.length}} 項</span>`;

      const listBox = document.createElement("div");
      listBox.className = "cat-items";
      header.onclick = () => {{
        listBox.style.display = listBox.style.display === "none" ? "flex" : "none";
      }};

      catItems.forEach(item => {{
        const card = document.createElement("div");
        card.className = "item-card" + (item.id === activeId ? " selected" : "");
        card.draggable = true;
        card.onclick = () => selectItemById(item.id);

        // 桌面端 HTML5 Drag & Drop
        card.addEventListener("dragstart", e => {{
          draggedItemId = item.id;
          card.classList.add("dragging");
          e.dataTransfer.setData("text/plain", item.id);
        }});
        card.addEventListener("dragend", () => {{
          card.classList.remove("dragging");
          draggedItemId = null;
          document.querySelectorAll(".cat-section").forEach(s => s.classList.remove("drag-over"));
        }});

        // 手機觸控端長按拖曳改分類支援
        let touchTimer = null;
        let isTouchDraggingCard = false;
        card.addEventListener("touchstart", e => {{
          touchTimer = setTimeout(() => {{
            isTouchDraggingCard = true;
            draggedItemId = item.id;
            card.classList.add("dragging");
          }}, 280);
        }}, {{ passive: true }});

        card.addEventListener("touchmove", e => {{
          if (!isTouchDraggingCard) {{ clearTimeout(touchTimer); return; }}
          e.preventDefault();
          const t = e.touches[0];
          const elUnder = document.elementFromPoint(t.clientX, t.clientY);
          document.querySelectorAll(".cat-section").forEach(s => s.classList.remove("drag-over"));
          const targetSec = elUnder ? elUnder.closest(".cat-section") : null;
          if (targetSec) targetSec.classList.add("drag-over");
        }}, {{ passive: false }});

        card.addEventListener("touchend", e => {{
          clearTimeout(touchTimer);
          if (!isTouchDraggingCard) return;
          isTouchDraggingCard = false;
          card.classList.remove("dragging");
          const t = e.changedTouches[0];
          const elUnder = document.elementFromPoint(t.clientX, t.clientY);
          const targetSec = elUnder ? elUnder.closest(".cat-section") : null;
          document.querySelectorAll(".cat-section").forEach(s => s.classList.remove("drag-over"));
          if (targetSec && targetSec.getAttribute("data-cat")) {{
            moveItemToCategory(item.id, targetSec.getAttribute("data-cat"));
          }}
          draggedItemId = null;
        }});

        const b = badgeMap[item.item_type || "furniture"] || badgeMap.furniture;
        card.innerHTML = `
          <div class="item-card-header">
            <div class="name">
              <span style="color:#64748B;font-size:11px;cursor:grab;">⠿</span>
              <span style="display:inline-block;width:11px;height:11px;border-radius:3px;background:${{item.color}};border:1px solid #fff;"></span>
              <span>${{item.name}}</span>
              <span class="badge ${{b.cls}}">${{b.text}}</span>
            </div>
            <button class="card-del-btn" title="刪除" onclick="deleteItemById('${{item.id}}', event)">🗑️</button>
          </div>
          <div class="dims">
            ${{Math.round(item.w)}}×${{Math.round(item.d)}}×${{item.h || 30}} cm | Z:${{item.z || 0}} | ${{item.rot || 0}}°
          </div>
        `;
        listBox.appendChild(card);
      }});

      sec.appendChild(header);
      sec.appendChild(listBox);
      container.appendChild(sec);
    }});
  }}

  function highlightRightPanel() {{
    renderRightPanel();
  }}

  function selectItemById(id) {{
    activeId = id;
    if (currentMode === "2D") {{
      const group = canvas.getObjects().find(o => o.itemId === id);
      if (group && !forcePanMode) {{
        canvas.setActiveObject(group);
        canvas.requestRenderAll();
      }}
    }} else if (currentMode === "3D" && transformControl) {{
      const mesh = selectable3DMeshes.find(m => m.userData.itemId === id);
      if (mesh) attachGizmoWithRules(mesh);
    }}
    switchLeftTab('item');
    updateLeftItemPanel();
    highlightRightPanel();
  }}

  // --- 2D 視角控制 ---
  function zoomToFit() {{
    if (!canvas) return;
    const rw = appState.room.width, rd = appState.room.depth;
    const container = document.getElementById("canvas-container");
    const cw = container.clientWidth - 90, ch = container.clientHeight - 90;
    const scale = Math.min(cw / rw, ch / rd, 1.65);
    const offsetX = (container.clientWidth - rw * scale) / 2;
    const offsetY = (container.clientHeight - rd * scale) / 2;
    canvas.setViewportTransform([scale, 0, 0, scale, offsetX, offsetY]);
    canvas.requestRenderAll();
  }}

  document.getElementById("btn-zoom-fit").addEventListener("click", zoomToFit);
  document.getElementById("btn-zoom-in").addEventListener("click", () => canvas.setZoom(Math.min(canvas.getZoom() * 1.2, 5)));
  document.getElementById("btn-zoom-out").addEventListener("click", () => canvas.setZoom(Math.max(canvas.getZoom() / 1.2, 0.2)));
  document.getElementById("btn-pan-toggle").addEventListener("click", function() {{
    forcePanMode = !forcePanMode;
    this.innerText = forcePanMode ? "✋ 強制平移: 開" : "✋ 強制平移: 關";
    this.classList.toggle("active", forcePanMode);
    renderFullScene();
  }});

  // --- 存檔與匯出入 ---
  document.getElementById("btn-save-local").addEventListener("click", () => {{
    localStorage.setItem("room_planner_v6", JSON.stringify(appState));
    alert("✅ 已成功儲存於 App 本地記憶中！");
  }});

  document.getElementById("btn-load-local").addEventListener("click", () => {{
    const saved = localStorage.getItem("room_planner_v6") || localStorage.getItem("room_planner_v5");
    if (saved) {{
      appState = JSON.parse(saved);
      if (!appState.categories) appState.categories = ["床", "大型家具", "收納櫃體", "門窗建材", "機電開關"];
      if (!appState.categories.includes("床")) appState.categories.unshift("床");
      if (!appState.human) appState.human = {{ x: 230, y: 230, z: 0, height: 178, rot: 0, pitch: 0, posture: "stand" }};
      renderCategoryUI();
      initRoomFormValues();
      initHumanFormValues();
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
        if (!appState.categories) appState.categories = ["床", "大型家具", "收納櫃體", "門窗建材", "機電開關"];
        if (!appState.categories.includes("床")) appState.categories.unshift("床");
        if (!appState.human) appState.human = {{ x: 230, y: 230, z: 0, height: 178, rot: 0, pitch: 0, posture: "stand" }};
        renderCategoryUI();
        initRoomFormValues();
        initHumanFormValues();
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
      renderCategoryUI();
      initRoomFormValues();
      initHumanFormValues();
      renderVoidListUI();
      renderFullScene();
      zoomToFit();
    }}
  }});

  // --- 建構精緻 3D 擬真關節人形模型 (支援站立、屈膝坐姿、仰躺姿勢) ---
  function buildRealistic3DHuman(hData) {{
    const group = new THREE.Group();
    const stature = hData.height || 178;
    const s = stature / 175; // 相對比例尺
    const posture = hData.posture || "stand";

    const skinMat = new THREE.MeshLambertMaterial({{ color: 0xFFDCB1 }});
    const hairMat = new THREE.MeshLambertMaterial({{ color: 0x1E293B }});
    const shirtMat = new THREE.MeshLambertMaterial({{ color: 0x3B82F6 }});
    const pantsMat = new THREE.MeshLambertMaterial({{ color: 0x1E293B }});
    const shoeMat = new THREE.MeshLambertMaterial({{ color: 0xF8FAFC }});
    const eyeMat = new THREE.MeshBasicMaterial({{ color: 0x0F172A }});

    // 建立身體組件容器 (用於躺姿或坐姿的整體旋轉與位移)
    const rig = new THREE.Group();

    // 頭部 + 頭髮 + 雙眼 (朝向本地 -Z)
    const headGroup = new THREE.Group();
    const headMesh = new THREE.Mesh(new THREE.SphereGeometry(10.5 * s, 20, 20), skinMat);
    headGroup.add(headMesh);
    const hairMesh = new THREE.Mesh(new THREE.SphereGeometry(11 * s, 16, 16, 0, Math.PI * 2, 0, Math.PI * 0.58), hairMat);
    hairMesh.position.y = 1.5 * s;
    headGroup.add(hairMesh);
    // 雙眼標示臉部朝向 (-Z)
    const eyeL = new THREE.Mesh(new THREE.SphereGeometry(1.4 * s, 8, 8), eyeMat);
    eyeL.position.set(-3.6 * s, 1 * s, -9.8 * s);
    const eyeR = new THREE.Mesh(new THREE.SphereGeometry(1.4 * s, 8, 8), eyeMat);
    eyeR.position.set(3.6 * s, 1 * s, -9.8 * s);
    headGroup.add(eyeL, eyeR);

    // 頸部
    const neckMesh = new THREE.Mesh(new THREE.CylinderGeometry(4 * s, 4.5 * s, 8 * s, 12), skinMat);

    // 軀幹 (上衣) + 骨盆
    const torsoMesh = new THREE.Mesh(new THREE.BoxGeometry(32 * s, 50 * s, 17 * s), shirtMat);
    const pelvisMesh = new THREE.Mesh(new THREE.BoxGeometry(30 * s, 14 * s, 16 * s), pantsMat);

    // 雙臂 (肩膀圓潤 + 手臂)
    const armGeo = new THREE.CylinderGeometry(4.2 * s, 3.5 * s, 52 * s, 12);
    const armL = new THREE.Mesh(armGeo, shirtMat);
    const armR = new THREE.Mesh(armGeo, shirtMat);

    if (posture === "stand") {{
      headGroup.position.set(0, 158 * s, 0);
      neckMesh.position.set(0, 145 * s, 0);
      torsoMesh.position.set(0, 118 * s, 0);
      pelvisMesh.position.set(0, 86 * s, 0);
      armL.position.set(-20 * s, 114 * s, 0);
      armR.position.set(20 * s, 114 * s, 0);

      // 直立雙腿與鞋子
      const legGeo = new THREE.CylinderGeometry(6 * s, 4.5 * s, 74 * s, 12);
      const legL = new THREE.Mesh(legGeo, pantsMat);
      legL.position.set(-8.5 * s, 43 * s, 0);
      const legR = new THREE.Mesh(legGeo, pantsMat);
      legR.position.set(8.5 * s, 43 * s, 0);

      const shoeGeo = new THREE.BoxGeometry(10 * s, 7 * s, 22 * s);
      const shoeL = new THREE.Mesh(shoeGeo, shoeMat);
      shoeL.position.set(-8.5 * s, 3.5 * s, -4 * s);
      const shoeR = new THREE.Mesh(shoeGeo, shoeMat);
      shoeR.position.set(8.5 * s, 3.5 * s, -4 * s);
      rig.add(headGroup, neckMesh, torsoMesh, pelvisMesh, armL, armR, legL, legR, shoeL, shoeR);

    }} else if (posture === "sit") {{
      // 屈膝坐姿：臀部高度在座面 (若在地面則自帶一張隱形高度或坐姿高度)
      const seatOffset = (hData.z || 0) > 0 ? 0 : 42 * s;
      pelvisMesh.position.set(0, (8 + seatOffset) * s, 0);
      torsoMesh.position.set(0, (38 + seatOffset) * s, 0);
      neckMesh.position.set(0, (66 + seatOffset) * s, 0);
      headGroup.position.set(0, (78 + seatOffset) * s, 0);
      armL.position.set(-20 * s, (38 + seatOffset) * s, -6 * s);
      armL.rotation.x = 0.4;
      armR.position.set(20 * s, (38 + seatOffset) * s, -6 * s);
      armR.rotation.x = 0.4;

      // 水平大腿 + 垂直小腿
      const thighGeo = new THREE.BoxGeometry(11 * s, 11 * s, 38 * s);
      const thighL = new THREE.Mesh(thighGeo, pantsMat);
      thighL.position.set(-8.5 * s, (8 + seatOffset) * s, -16 * s);
      const thighR = new THREE.Mesh(thighGeo, pantsMat);
      thighR.position.set(8.5 * s, (8 + seatOffset) * s, -16 * s);

      const calfGeo = new THREE.CylinderGeometry(5 * s, 4 * s, 42 * s, 12);
      const calfL = new THREE.Mesh(calfGeo, pantsMat);
      calfL.position.set(-8.5 * s, (-12 + seatOffset) * s, -32 * s);
      const calfR = new THREE.Mesh(calfGeo, pantsMat);
      calfR.position.set(8.5 * s, (-12 + seatOffset) * s, -32 * s);

      rig.add(headGroup, neckMesh, torsoMesh, pelvisMesh, armL, armR, thighL, thighR, calfL, calfR);

    }} else {{
      // 躺姿 (仰躺在床/地面，臉朝上略偏前方 -Z)
      headGroup.position.set(0, 18 * s, 52 * s);
      headGroup.rotation.x = Math.PI / 2.3;
      neckMesh.position.set(0, 12 * s, 38 * s);
      neckMesh.rotation.x = Math.PI / 2;
      torsoMesh.position.set(0, 10 * s, 8 * s);
      torsoMesh.rotation.x = Math.PI / 2;
      pelvisMesh.position.set(0, 9 * s, -22 * s);
      pelvisMesh.rotation.x = Math.PI / 2;
      armL.position.set(-21 * s, 9 * s, 8 * s);
      armL.rotation.x = Math.PI / 2;
      armR.position.set(21 * s, 9 * s, 8 * s);
      armR.rotation.x = Math.PI / 2;

      const legGeo = new THREE.CylinderGeometry(5.8 * s, 4.5 * s, 70 * s, 12);
      const legL = new THREE.Mesh(legGeo, pantsMat);
      legL.rotation.x = Math.PI / 2;
      legL.position.set(-8.5 * s, 8 * s, -62 * s);
      const legR = new THREE.Mesh(legGeo, pantsMat);
      legR.rotation.x = Math.PI / 2;
      legR.position.set(8.5 * s, 8 * s, -62 * s);

      rig.add(headGroup, neckMesh, torsoMesh, pelvisMesh, armL, armR, legL, legR);
    }}

    // 視線方向指示光錐 (標示眼睛看出去的方向)
    const eyeLocalY = getHumanEyeHeight() - (hData.z || 0);
    const coneGeo = new THREE.ConeGeometry(11, 38, 12);
    coneGeo.rotateX(-Math.PI / 2);
    const coneMesh = new THREE.Mesh(coneGeo, new THREE.MeshBasicMaterial({{ color: 0xA855F7, wireframe: true }}));
    coneMesh.position.set(0, eyeLocalY, -28);
    rig.add(coneMesh);

    group.add(rig);
    group.position.set(hData.x, hData.z || 0, hData.y);
    group.rotation.y = -(hData.rot || 0) * Math.PI / 180;
    group.userData = {{ isHuman: true }};
    return group;
  }}

  // 根據選取的是「人物」還是「一般家具」，自動鎖定人物的垂直 Y 軸與 Scale，避免手機誤觸改到身高！
  function attachGizmoWithRules(mesh) {{
    if (!transformControl || !mesh) return;
    transformControl.attach(mesh);
    if (mesh.userData.isHuman) {{
      // 人物：禁止在 3D 畫面縮放身高，且移動時鎖定垂直 Y 軸
      if (gizmoMode === "scale") {{
        transformControl.setMode("translate");
      }} else {{
        transformControl.setMode(gizmoMode);
      }}
      transformControl.showY = (transformControl.getMode() === "rotate");
      transformControl.showX = (transformControl.getMode() !== "rotate");
      transformControl.showZ = (transformControl.getMode() !== "rotate");
    }} else {{
      transformControl.setMode(gizmoMode);
      transformControl.showX = true;
      transformControl.showY = true;
      transformControl.showZ = true;
    }}
  }}

  // --- 3D 場景、點擊地板/床面走過去、防穿模與第一人稱人類自然視角 ---
  function initThree() {{
    const container = document.getElementById("three-container");
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0B0F17);

    camera = new THREE.PerspectiveCamera(68, container.clientWidth / container.clientHeight, 2, 6000);
    camera.position.set(appState.room.width / 2, 420, appState.room.depth + 340);

    renderer = new THREE.WebGLRenderer({{ antialias: true }});
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(appState.room.width / 2, 60, appState.room.depth / 2);

    transformControl = new THREE.TransformControls(camera, renderer.domElement);
    transformControl.addEventListener('dragging-changed', function(event) {{
      if (currentMode === "3D") controls.enabled = !event.value;
      const trashEl = document.getElementById("trash-dropzone");
      if (event.value && activeId && activeId !== "HUMAN") {{
        trashEl.classList.add("show");
      }} else {{
        if (isOverTrash && activeId && activeId !== "HUMAN") {{
          deleteItemById(activeId);
        }}
        trashEl.classList.remove("show", "hover");
        isOverTrash = false;
      }}
    }});

    transformControl.addEventListener('change', function() {{
      if (!transformControl.object) return;
      const obj = transformControl.object;
      if (obj.userData.isHuman) {{
        // 3D 拖曳人物時：強制鎖定不可縮放身高，並進行碰撞防穿模與床高疊加檢測
        obj.scale.set(1, 1, 1);
        const nx = Math.round(obj.position.x);
        const ny = Math.round(obj.position.z);
        const check = checkHumanWalkable(nx, ny);
        if (check.allowed) {{
          appState.human.x = nx;
          appState.human.y = ny;
          appState.human.z = check.baseZ;
        }}
        // 強制將 3D 人物固定在合法位置與踏面高度 baseZ (絕不允許垂直拉高)
        obj.position.set(appState.human.x, appState.human.z || 0, appState.human.y);
        appState.human.rot = Math.round((-obj.rotation.y * 180 / Math.PI % 360 + 360) % 360);
        initHumanFormValues();
      }} else if (obj.userData.itemId) {{
        const item = appState.items.find(i => i.id === obj.userData.itemId);
        if (!item) return;
        if (gizmoMode === "scale") {{
          item.w = Math.max(5, Math.round(obj.userData.origW * obj.scale.x));
          item.h = Math.max(5, Math.round(obj.userData.origH * obj.scale.y));
          item.d = Math.max(5, Math.round(obj.userData.origD * obj.scale.z));
        }}
        item.x = Math.round(obj.position.x - item.w / 2);
        item.y = Math.round(obj.position.z - item.d / 2);
        item.z = Math.max(0, Math.round(obj.position.y - (item.h || 30) / 2));
        item.rot = Math.round((-obj.rotation.y * 180 / Math.PI % 360 + 360) % 360);
        updateLeftItemPanel();
        renderRightPanel();
      }}
    }});
    scene.add(transformControl);

    // 點擊選取物件 或 點擊地板/床面讓人物自動走過去
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let downX = 0, downY = 0, downTime = 0;

    renderer.domElement.addEventListener('pointerdown', function(e) {{
      downX = e.clientX; downY = e.clientY; downTime = Date.now();
      if (currentMode === "FPV") {{
        isLookingFPV = true;
        fpvLastX = e.clientX;
        fpvLastY = e.clientY;
      }}
    }});

    renderer.domElement.addEventListener('pointermove', function(e) {{
      if (transformControl && transformControl.dragging) {{
        const trashEl = document.getElementById("trash-dropzone");
        const rect = trashEl.getBoundingClientRect();
        isOverTrash = (e.clientX >= rect.left - 20 && e.clientX <= rect.right + 20 && e.clientY >= rect.top - 20 && e.clientY <= rect.bottom + 20);
        trashEl.classList.toggle("hover", isOverTrash);
      }}
      if (currentMode === "FPV" && isLookingFPV) {{
        const dx = e.clientX - fpvLastX;
        const dy = e.clientY - fpvLastY;
        fpvLastX = e.clientX;
        fpvLastY = e.clientY;
        appState.human.rot = ((appState.human.rot + dx * 0.35) % 360 + 360) % 360;
        appState.human.pitch = Math.max(-85, Math.min(85, (appState.human.pitch || 0) - dy * 0.35));
        initHumanFormValues();
        syncFPVCamera();
      }}
    }});

    renderer.domElement.addEventListener('pointerup', function(e) {{
      isLookingFPV = false;
      const moveDist = Math.hypot(e.clientX - downX, e.clientY - downY);
      const elapsed = Date.now() - downTime;
      if (moveDist > 8 || elapsed > 500) return; // 區分輕點(Tap)與拖曳旋轉視角

      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);

      // 1. 在 FPV 人類視角下輕點畫面：計算點擊方向或地板目標點，讓人物朝該處走過去
      if (currentMode === "FPV") {{
        const walkHits = raycaster.intersectObjects(walkable3DMeshes, true);
        if (walkHits.length > 0) {{
          const pt = walkHits[0].point;
          triggerWalkToTarget(pt.x, pt.z);
        }} else {{
          // 若點擊前方視野水平處，往視線方向前進 55cm
          const yawRad = (appState.human.rot || 0) * Math.PI / 180;
          triggerWalkToTarget(appState.human.x + Math.sin(yawRad) * 55, appState.human.y - Math.cos(yawRad) * 55);
        }}
        return;
      }}

      // 2. 在 3D 鳥瞰模式下輕點畫面：優先檢查是否點選了物件，若點擊地板或床面則讓人物走過去
      if (currentMode === "3D") {{
        const intersects = raycaster.intersectObjects(selectable3DMeshes, true);
        if (intersects.length > 0) {{
          let hit = intersects[0].object;
          while (hit.parent && !hit.userData.itemId && !hit.userData.isHuman) {{
            hit = hit.parent;
          }}
          if (hit.userData.isHuman) {{
            activeId = "HUMAN";
            attachGizmoWithRules(hit);
            switchLeftTab('human');
            initHumanFormValues();
            return;
          }} else if (hit.userData.itemId) {{
            const hitItem = appState.items.find(i => i.id === hit.userData.itemId);
            // 若目前已選中人物，且點擊的是「床」，則直接讓人物走上床！
            if (activeId === "HUMAN" && hitItem && isBedItem(hitItem)) {{
              const pt = intersects[0].point;
              triggerWalkToTarget(pt.x, pt.z);
              return;
            }}
            activeId = hit.userData.itemId;
            attachGizmoWithRules(hit);
            switchLeftTab('item');
            updateLeftItemPanel();
            highlightRightPanel();
            return;
          }}
        }}

        // 若點擊的是地板空白處，直接讓人物走向該點擊位置！
        const floorHits = raycaster.intersectObjects(walkable3DMeshes, true);
        if (floorHits.length > 0) {{
          const pt = floorHits[0].point;
          triggerWalkToTarget(pt.x, pt.z);
        }} else if (!transformControl.dragging) {{
          transformControl.detach();
        }}
      }}
    }});

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.65);
    dirLight.position.set(250, 520, 320);
    scene.add(dirLight);

    animateThree();
  }}

  // 觸發人物自動走向目標點 (tx, ty)
  function triggerWalkToTarget(tx, ty) {{
    walkTarget = {{ x: tx, y: ty }};
    // 自動將人物面向轉向目標點
    const dx = tx - appState.human.x;
    const dy = ty - appState.human.y;
    if (Math.hypot(dx, dy) > 2) {{
      let deg = Math.atan2(dx, -dy) * 180 / Math.PI;
      appState.human.rot = Math.round((deg % 360 + 360) % 360);
    }}
    if (targetRingMesh) {{
      const check = checkHumanWalkable(tx, ty);
      targetRingMesh.position.set(tx, (check.baseZ || 0) + 1.5, ty);
      targetRingMesh.visible = true;
    }}
  }}

  window.set3DGizmoMode = function(mode) {{
    gizmoMode = mode;
    document.getElementById("btn-3d-translate").classList.toggle("active", mode === "translate");
    document.getElementById("btn-3d-rotate").classList.toggle("active", mode === "rotate");
    document.getElementById("btn-3d-scale").classList.toggle("active", mode === "scale");
    if (transformControl && transformControl.object) {{
      attachGizmoWithRules(transformControl.object);
    }}
  }};

  function updateThreeScene() {{
    if (!scene) return;
    if (transformControl) transformControl.detach();
    selectable3DMeshes = [];
    walkable3DMeshes = [];

    const keep = [scene.children[0], scene.children[1], transformControl];
    scene.children = keep.filter(Boolean);

    const rw = appState.room.width, rd = appState.room.depth, rh = appState.room.height;
    const texLoader = new THREE.TextureLoader();

    // 1. 地板 (加入 walkable3DMeshes 供點擊移動)
    const floorGeo = new THREE.PlaneGeometry(rw, rd);
    const floorMat = new THREE.MeshLambertMaterial({{ color: 0x5089C6, side: THREE.DoubleSide }});
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(rw / 2, 0, rd / 2);
    scene.add(floor);
    walkable3DMeshes.push(floor);

    // 點擊走動目標指示光圈
    const ringGeo = new THREE.RingGeometry(8, 13, 24);
    ringGeo.rotateX(-Math.PI / 2);
    targetRingMesh = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({{ color: 0x38BDF8, side: THREE.DoubleSide }}));
    targetRingMesh.visible = !!walkTarget;
    if (walkTarget) targetRingMesh.position.set(walkTarget.x, (appState.human.z || 0) + 1.5, walkTarget.y);
    scene.add(targetRingMesh);

    // 2. 四周實體白牆
    if (appState.room.show_walls) {{
      let wallMat;
      if (appState.room.wall_texture) {{
        wallMat = new THREE.MeshLambertMaterial({{ map: texLoader.load(appState.room.wall_texture), side: THREE.DoubleSide }});
      }} else {{
        wallMat = new THREE.MeshLambertMaterial({{
          color: appState.room.wall_color || "#F8FAFC",
          side: THREE.DoubleSide,
          transparent: currentMode === "3D",
          opacity: currentMode === "3D" ? 0.52 : 1.0
        }});
      }}
      const wNorth = new THREE.Mesh(new THREE.PlaneGeometry(rw, rh), wallMat);
      wNorth.position.set(rw / 2, rh / 2, 0);
      const wSouth = new THREE.Mesh(new THREE.PlaneGeometry(rw, rh), wallMat);
      wSouth.position.set(rw / 2, rh / 2, rd);
      const wWest = new THREE.Mesh(new THREE.PlaneGeometry(rd, rh), wallMat);
      wWest.rotation.y = Math.PI / 2;
      wWest.position.set(0, rh / 2, rd / 2);
      const wEast = new THREE.Mesh(new THREE.PlaneGeometry(rd, rh), wallMat);
      wEast.rotation.y = Math.PI / 2;
      wEast.position.set(rw, rh / 2, rd / 2);
      scene.add(wNorth, wSouth, wWest, wEast);
    }}

    // 3. 天花板
    if (appState.room.show_ceiling) {{
      let ceilMat;
      if (appState.room.ceiling_texture) {{
        ceilMat = new THREE.MeshLambertMaterial({{ map: texLoader.load(appState.room.ceiling_texture), side: THREE.DoubleSide }});
      }} else {{
        ceilMat = new THREE.MeshLambertMaterial({{ color: appState.room.ceiling_color || "#FFFFFF", side: THREE.DoubleSide }});
      }}
      const ceilMesh = new THREE.Mesh(new THREE.PlaneGeometry(rw, rd), ceilMat);
      ceilMesh.rotation.x = Math.PI / 2;
      ceilMesh.position.set(rw / 2, rh, rd / 2);
      scene.add(ceilMesh);
    }}

    const wallLine = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(rw, rh, rd)), new THREE.LineBasicMaterial({{ color: 0x475569 }}));
    wallLine.position.set(rw / 2, rh / 2, rd / 2);
    scene.add(wallLine);

    appState.voids.forEach(v => {{
      const voidMesh = new THREE.Mesh(new THREE.PlaneGeometry(v.w, v.d), new THREE.MeshBasicMaterial({{ color: 0xffffff, side: THREE.DoubleSide }}));
      voidMesh.rotation.x = -Math.PI / 2;
      voidMesh.position.set(v.x + v.w / 2, 0.4, v.y + v.d / 2);
      scene.add(voidMesh);
    }});

    // 4. 3D 擬真關節人形模型 (在 3D 鳥瞰模式下顯示)
    if (currentMode === "3D") {{
      human3DGroup = buildRealistic3DHuman(appState.human);
      scene.add(human3DGroup);
      selectable3DMeshes.push(human3DGroup);
      if (activeId === "HUMAN") attachGizmoWithRules(human3DGroup);
    }} else {{
      human3DGroup = null;
    }}

    // 5. 繪製所有家具、床、門、窗戶、插座與開關
    appState.items.forEach(item => {{
      const h = item.h || 30;
      const zBottom = item.z || 0;
      const t = item.item_type || "furniture";
      let itemMesh;

      if (t === "window") {{
        itemMesh = new THREE.Group();
        const fDepth = Math.max(item.d, 8);
        const frameGeo = new THREE.BoxGeometry(item.w, h, fDepth);
        itemMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(frameGeo), new THREE.LineBasicMaterial({{ color: 0xF59E0B, linewidth: 3 }})));
        const sceneryTex = texLoader.load(item.scenery || appState.default_fuji);
        const glassMesh = new THREE.Mesh(new THREE.BoxGeometry(Math.max(4, item.w - 4), Math.max(4, h - 4), fDepth * 0.5), new THREE.MeshBasicMaterial({{ map: sceneryTex }}));
        itemMesh.add(glassMesh);

      }} else if (t === "socket") {{
        itemMesh = new THREE.Group();
        const w = Math.max(item.w, 12), d = Math.max(item.d, 4);
        const plateMesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshLambertMaterial({{ color: 0xF8FAFC }}));
        plateMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(plateMesh.geometry), new THREE.LineBasicMaterial({{ color: 0x94A3B8 }})));
        itemMesh.add(plateMesh);
        [-w * 0.22, w * 0.22].forEach(ox => {{
          [-d/2 - 0.3, d/2 + 0.3].forEach(sz => {{
            const slotMat = new THREE.MeshBasicMaterial({{ color: 0x1E293B }});
            const s1 = new THREE.Mesh(new THREE.BoxGeometry(w * 0.06, h * 0.22, 0.8), slotMat);
            s1.position.set(ox - w * 0.07, h * 0.1, sz);
            const s2 = new THREE.Mesh(new THREE.BoxGeometry(w * 0.06, h * 0.22, 0.8), slotMat);
            s2.position.set(ox + w * 0.07, h * 0.1, sz);
            const gnd = new THREE.Mesh(new THREE.BoxGeometry(w * 0.08, h * 0.15, 0.8), slotMat);
            gnd.position.set(ox, -h * 0.2, sz);
            itemMesh.add(s1, s2, gnd);
          }});
        }});

      }} else if (t === "switch") {{
        itemMesh = new THREE.Group();
        const w = Math.max(item.w, 12), d = Math.max(item.d, 4);
        const plateMesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshLambertMaterial({{ color: 0xF1F5F9 }}));
        itemMesh.add(plateMesh);
        [-w * 0.2, w * 0.2].forEach(ox => {{
          const btnMesh = new THREE.Mesh(new THREE.BoxGeometry(w * 0.32, h * 0.65, d + 2.2), new THREE.MeshLambertMaterial({{ color: 0xE2E8F0 }}));
          btnMesh.rotation.x = 0.12;
          btnMesh.position.set(ox, 0, 0);
          const ledMesh = new THREE.Mesh(new THREE.BoxGeometry(w * 0.18, h * 0.08, d + 2.8), new THREE.MeshBasicMaterial({{ color: 0x10B981 }}));
          ledMesh.position.set(ox, 0, 0);
          itemMesh.add(btnMesh, ledMesh);
        }});

      }} else if (t === "door") {{
        itemMesh = new THREE.Group();
        const w = item.w, d = Math.max(item.d, 8);
        itemMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(w + 6, h + 3, d + 2)), new THREE.LineBasicMaterial({{ color: 0x451A03 }})));
        const panelMat = item.texture ? new THREE.MeshLambertMaterial({{ map: texLoader.load(item.texture) }}) : new THREE.MeshLambertMaterial({{ color: item.color || 0x8B5A2B }});
        const panelMesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d * 0.75), panelMat);
        itemMesh.add(panelMesh);

        const handleSide = item.flip_x ? -1 : 1;
        const handleMat = new THREE.MeshLambertMaterial({{ color: 0xFBBF24 }});
        const handleAxis = new THREE.Mesh(new THREE.BoxGeometry(3, 3, d + 8), handleMat);
        handleAxis.position.set(handleSide * w * 0.36, -h * 0.04, 0);
        const leverF = new THREE.Mesh(new THREE.BoxGeometry(12, 2.5, 2.5), handleMat);
        leverF.position.set(handleSide * (w * 0.36 - 4), -h * 0.04, d / 2 + 3.5);
        const leverB = new THREE.Mesh(new THREE.BoxGeometry(12, 2.5, 2.5), handleMat);
        leverB.position.set(handleSide * (w * 0.36 - 4), -h * 0.04, -d / 2 - 3.5);
        itemMesh.add(handleAxis, leverF, leverB);

      }} else {{
        const geo = new THREE.BoxGeometry(item.w, h, item.d);
        const mat = item.texture ? new THREE.MeshLambertMaterial({{ map: texLoader.load(item.texture) }}) : new THREE.MeshLambertMaterial({{ color: item.color }});
        itemMesh = new THREE.Mesh(geo, mat);
        itemMesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({{ color: 0x1E293B }})));
      }}

      itemMesh.rotation.y = -(item.rot || 0) * Math.PI / 180;
      itemMesh.position.set(item.x + item.w / 2, zBottom + h / 2, item.y + item.d / 2);
      itemMesh.userData = {{ itemId: item.id, origW: item.w, origH: h, origD: item.d }};
      scene.add(itemMesh);
      selectable3DMeshes.push(itemMesh);

      // 若此物件為「床」，加入 walkable3DMeshes 讓點擊床面也能走上去
      if (isBedItem(item)) {{
        walkable3DMeshes.push(itemMesh);
      }}

      if (currentMode === "3D" && activeId === item.id) {{
        attachGizmoWithRules(itemMesh);
      }}
    }});
  }}

  // --- 第一人稱人類自然視角 (FPV) 攝影機同步與移動 ---
  function syncFPVCamera() {{
    if (!camera) return;
    const h = appState.human;
    const eyeY = getHumanEyeHeight();
    camera.position.set(h.x, eyeY, h.y);

    const yawRad = (h.rot || 0) * Math.PI / 180;
    const pitchRad = (h.pitch || 0) * Math.PI / 180;

    const dirX = Math.sin(yawRad) * Math.cos(pitchRad);
    const dirY = Math.sin(pitchRad);
    const dirZ = -Math.cos(yawRad) * Math.cos(pitchRad);

    camera.lookAt(h.x + dirX * 100, eyeY + dirY * 100, h.y + dirZ * 100);
  }}

  window.enterHumanFPV = function() {{
    currentMode = "FPV";
    document.getElementById("btn-mode-fpv").classList.add("active");
    document.getElementById("btn-mode-2d").classList.remove("active");
    document.getElementById("btn-mode-3d").classList.remove("active");
    document.getElementById("canvas-container").style.display = "none";
    document.getElementById("three-container").style.display = "block";
    document.getElementById("view-controls-2d").style.display = "none";
    document.getElementById("view-controls-3d").style.display = "none";
    document.getElementById("fpv-hud").style.display = "flex";

    if (!renderer) initThree();
    controls.enabled = false;
    if (transformControl) transformControl.detach();
    const check = checkHumanWalkable(appState.human.x, appState.human.y);
    appState.human.z = check.baseZ;
    initHumanFormValues();
    updateThreeScene();
    syncFPVCamera();
  }};

  window.exitHumanFPV = function() {{
    walkTarget = null;
    document.getElementById("btn-mode-3d").click();
    renderFullScene();
  }};

  function animateThree() {{
    requestAnimationFrame(animateThree);

    // 1. 處理點擊地面/床面的平滑自動走動 (3D 與 FPV 皆適用，且具防穿模與上床疊加高度)
    if (walkTarget) {{
      const dx = walkTarget.x - appState.human.x;
      const dy = walkTarget.y - appState.human.y;
      const dist = Math.hypot(dx, dy);
      if (dist < 3.5) {{
        tryMoveHumanTo(Math.round(walkTarget.x), Math.round(walkTarget.y), false);
        walkTarget = null;
        if (targetRingMesh) targetRingMesh.visible = false;
      }} else {{
        const step = Math.min(dist, 3.8);
        const nx = appState.human.x + (dx / dist) * step;
        const ny = appState.human.y + (dy / dist) * step;
        const moved = tryMoveHumanTo(nx, ny, true);
        if (!moved) {{
          walkTarget = null;
          if (targetRingMesh) targetRingMesh.visible = false;
        }}
      }}
      if (human3DGroup) {{
        human3DGroup.position.set(appState.human.x, appState.human.z || 0, appState.human.y);
        human3DGroup.rotation.y = -(appState.human.rot || 0) * Math.PI / 180;
      }}
      initHumanFormValues();
      if (currentMode === "FPV") syncFPVCamera();
    }}

    // 2. 處理方向鍵 / 虛擬搖桿持續移動 (具碰撞防穿模與床高疊加)
    if (fpvMoveDir.forward !== 0 || fpvMoveDir.right !== 0) {{
      const speed = 3.2;
      const yawRad = (appState.human.rot || 0) * Math.PI / 180;
      const fx = Math.sin(yawRad), fz = -Math.cos(yawRad);
      const rx = Math.cos(yawRad), rz = Math.sin(yawRad);
      const nx = appState.human.x + (fx * fpvMoveDir.forward + rx * fpvMoveDir.right) * speed;
      const ny = appState.human.y + (fz * fpvMoveDir.forward + rz * fpvMoveDir.right) * speed;
      tryMoveHumanTo(nx, ny, true);
      if (human3DGroup) {{
        human3DGroup.position.set(appState.human.x, appState.human.z || 0, appState.human.y);
      }}
      initHumanFormValues();
      if (currentMode === "FPV") syncFPVCamera();
    }}

    if (currentMode !== "FPV" && controls && controls.enabled) {{
      controls.update();
    }}
    if (renderer && scene && camera) renderer.render(scene, camera);
  }}

  // --- 頂部模式切換 (2D / 3D鳥瞰互動 / 3D人類視角) ---
  document.getElementById("btn-mode-2d").addEventListener("click", () => {{
    currentMode = "2D";
    walkTarget = null;
    document.getElementById("btn-mode-2d").classList.add("active");
    document.getElementById("btn-mode-3d").classList.remove("active");
    document.getElementById("btn-mode-fpv").classList.remove("active");
    document.getElementById("canvas-container").style.display = "block";
    document.getElementById("three-container").style.display = "none";
    document.getElementById("view-controls-2d").style.display = "flex";
    document.getElementById("view-controls-3d").style.display = "none";
    document.getElementById("fpv-hud").style.display = "none";
    renderFullScene();
  }});

  document.getElementById("btn-mode-3d").addEventListener("click", () => {{
    currentMode = "3D";
    walkTarget = null;
    document.getElementById("btn-mode-3d").classList.add("active");
    document.getElementById("btn-mode-2d").classList.remove("active");
    document.getElementById("btn-mode-fpv").classList.remove("active");
    document.getElementById("canvas-container").style.display = "none";
    document.getElementById("three-container").style.display = "block";
    document.getElementById("view-controls-2d").style.display = "none";
    document.getElementById("view-controls-3d").style.display = "flex";
    document.getElementById("fpv-hud").style.display = "none";

    if (!renderer) initThree();
    controls.enabled = true;
    camera.position.set(appState.room.width / 2, 420, appState.room.depth + 340);
    controls.target.set(appState.room.width / 2, 60, appState.room.depth / 2);
    updateThreeScene();
  }});

  document.getElementById("btn-mode-fpv").addEventListener("click", enterHumanFPV);

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
