import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(
    page_title="專業臥室空間設計 & 坐向方位系統",
    page_icon="📐",
    layout="wide"
)

# 附圖原始預設數據
DEFAULT_ROOM = {"width": 460, "depth": 360, "height": 280}
DEFAULT_COMPASS = {"x": 255, "y": 185, "rotation": 0, "show": True}
DEFAULT_VOID = {"x": 370, "y": 240, "w": 90, "d": 120}
DEFAULT_WINDOWS = [
    {"id": "win1", "name": "主窗", "x": 65, "y": 38, "w": 130, "d": 12},
    {"id": "win2", "name": "小窗", "x": 355, "y": 38, "w": 20, "d": 12}
]

DEFAULT_ITEMS = [
    {"id": "bed", "name": "床", "x": 200, "y": 140, "w": 152, "d": 195, "h": 55, "rot": 0, "color": "#FAD785", "texture": ""},
    {"id": "stand_l", "name": "床頭櫃(左)", "x": 175, "y": 295, "w": 25, "d": 40, "h": 45, "rot": 0, "color": "#FAD785", "texture": ""},
    {"id": "stand_r", "name": "床頭櫃(右)", "x": 352, "y": 295, "w": 25, "d": 40, "h": 45, "rot": 0, "color": "#FAD785", "texture": ""},
    {"id": "wardrobe_new", "name": "新衣櫃", "x": 30, "y": 260, "w": 121, "d": 72, "h": 210, "rot": 0, "color": "#A0CB88", "texture": ""},
    {"id": "desk", "name": "書桌", "x": 30, "y": 150, "w": 123, "d": 71, "h": 75, "rot": 0, "color": "#8232FA", "texture": ""},
    {"id": "drybox", "name": "防潮箱", "x": 265, "y": 50, "w": 40, "d": 45, "h": 50, "rot": 0, "color": "#DC7CF5", "texture": ""},
    {"id": "wardrobe_white", "name": "白衣櫃", "x": 305, "y": 50, "w": 60, "d": 55, "h": 190, "rot": 0, "color": "#AADE8D", "texture": ""},
    {"id": "wardrobe_old", "name": "舊衣櫃", "x": 365, "y": 50, "w": 120, "d": 51, "h": 200, "rot": 0, "color": "#9EC484", "texture": ""},
    {"id": "bookcase", "name": "玻書櫃", "x": 450, "y": 180, "w": 32, "d": 63, "h": 180, "rot": 0, "color": "#DC7CF5", "texture": ""}
]

initial_data = {
    "room": DEFAULT_ROOM,
    "compass": DEFAULT_COMPASS,
    "void": DEFAULT_VOID,
    "windows": DEFAULT_WINDOWS,
    "items": DEFAULT_ITEMS
}

initial_data_json = json.dumps(initial_data)

html_code = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: #0E1117; color: #E0E0E0; overflow: hidden; }}
    .app-container {{ display: flex; height: 100vh; width: 100vw; }}
    
    /* 側邊欄面板 */
    .left-panel {{ width: 310px; background: #16191E; border-right: 1px solid #282C34; display: flex; flex-direction: column; height: 100vh; }}
    .center-canvas {{ flex: 1; display: flex; flex-direction: column; position: relative; background: #090B0E; }}
    .right-panel {{ width: 280px; background: #16191E; border-left: 1px solid #282C34; padding: 16px; display: flex; flex-direction: column; overflow-y: auto; height: 100vh; }}

    /* 標籤頁切換 (左面板) */
    .tab-bar {{ display: flex; background: #1F232B; border-bottom: 1px solid #282C34; }}
    .tab-btn {{ flex: 1; padding: 12px 6px; font-size: 13px; font-weight: 600; text-align: center; color: #8F96A0; cursor: pointer; border-bottom: 2px solid transparent; }}
    .tab-btn.active {{ color: #FFF; border-bottom: 2px solid #3B82F6; background: #16191E; }}
    .tab-content {{ padding: 16px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }}

    /* 工具列 */
    .toolbar {{ height: 50px; background: #16191E; border-bottom: 1px solid #282C34; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; z-index: 10; }}
    .btn-group {{ display: flex; gap: 8px; align-items: center; }}
    button {{ background: #262B35; color: #FFF; border: 1px solid #3A4150; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.2s; }}
    button:hover {{ background: #353C4A; }}
    button.active {{ background: #2563EB; border-color: #2563EB; color: #FFF; }}
    button.primary {{ background: #059669; border-color: #059669; }}
    button.primary:hover {{ background: #047857; }}
    
    .panel-title {{ font-size: 14px; font-weight: 600; color: #FFF; border-bottom: 1px solid #282C34; padding-bottom: 6px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }}
    .field-group {{ display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }}
    .field-group label {{ font-size: 11px; color: #9AA0A6; font-weight: 500; }}
    .field-row {{ display: flex; gap: 8px; }}
    .field-row input {{ width: 100%; }}
    input[type="text"], input[type="number"] {{ background: #0E1117; border: 1px solid #333842; color: #FFF; padding: 6px 8px; border-radius: 4px; font-size: 12px; }}
    input[type="color"] {{ width: 100%; height: 32px; border: none; background: transparent; cursor: pointer; }}
    
    /* 右側清單 */
    .item-list {{ display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }}
    .item-card {{ background: #1F232B; border: 1px solid #2B303A; border-radius: 6px; padding: 10px; cursor: pointer; transition: all 0.2s; }}
    .item-card:hover {{ border-color: #3B82F6; background: #252A35; }}
    .item-card.selected {{ border-color: #3B82F6; background: #1E293B; box-shadow: 0 0 0 1px #3B82F6; }}
    .item-card .name {{ font-weight: 600; font-size: 13px; color: #FFF; display: flex; justify-content: space-between; align-items: center; }}
    .item-card .dims {{ font-size: 11px; color: #94A3B8; margin-top: 4px; }}

    /* 畫布視角控制浮動鈕 */
    .view-controls {{ position: absolute; top: 62px; left: 16px; display: flex; gap: 6px; z-index: 10; background: rgba(22,25,30,0.85); padding: 4px; border-radius: 6px; border: 1px solid #282C34; backdrop-filter: blur(4px); }}
    .view-controls button {{ padding: 4px 8px; font-size: 11px; }}

    #canvas-container, #three-container {{ width: 100%; height: calc(100vh - 50px); position: absolute; top: 50px; left: 0; }}
    #three-container {{ display: none; }}
  </style>
</head>
<body>

<div class="app-container">
  <!-- 左側面板 (標籤頁：物件編輯 / 地面空間與坐向 / 存檔專案) -->
  <div class="left-panel">
    <div class="tab-bar">
      <div class="tab-btn active" id="tab-btn-item" onclick="switchLeftTab('item')">物件編輯</div>
      <div class="tab-btn" id="tab-btn-room" onclick="switchLeftTab('room')">地面與坐向</div>
      <div class="tab-btn" id="tab-btn-save" onclick="switchLeftTab('save')">專案存檔</div>
    </div>

    <!-- 標籤 1：選取物件編輯 -->
    <div class="tab-content" id="tab-content-item">
      <div id="no-selection" style="color: #6E7681; font-size: 13px; margin: 40px 0; text-align: center; line-height: 1.6;">
        👈 點選畫面上或右側列表中的物件<br>即時修改長寬高、顏色與旋轉角度
      </div>

      <div id="prop-editor" style="display: none;">
        <div class="panel-title">✏️ 物件細部規格</div>
        <div class="field-group">
          <label>名稱</label>
          <input type="text" id="prop-name">
        </div>

        <div class="field-group">
          <label>寬度 (W) × 深度 (D) (cm)</label>
          <div class="field-row">
            <input type="number" id="prop-w" title="寬度 W">
            <input type="number" id="prop-d" title="深度 D">
          </div>
        </div>

        <div class="field-group">
          <label>高度 (H) (cm, 未填則預設 30cm)</label>
          <input type="number" id="prop-h" placeholder="預設 30">
        </div>

        <div class="field-group">
          <label>旋轉角度 (度 °) [或按住上方旋轉圓點]</label>
          <input type="number" id="prop-rot" min="0" max="360">
        </div>

        <div class="field-group">
          <label>位置 X × Y 坐標 (cm)</label>
          <div class="field-row">
            <input type="number" id="prop-x" title="X 坐標">
            <input type="number" id="prop-y" title="Y 坐標">
          </div>
        </div>

        <div class="field-group">
          <label>顏色外觀</label>
          <input type="color" id="prop-color">
        </div>

        <div class="field-group">
          <label>🎨 上傳貼圖 / 材質紋理</label>
          <input type="file" id="prop-texture-file" accept="image/*" style="font-size: 11px; color: #8F96A0;">
        </div>

        <div style="display: flex; gap: 8px; margin-top: 10px;">
          <button id="btn-duplicate" style="flex: 1;">複製物件</button>
          <button id="btn-delete" style="flex: 1; background: #DC2626; border-color: #DC2626;">刪除物件</button>
        </div>
      </div>

      <div style="margin-top: auto; padding-top: 10px;">
        <button id="btn-add-new" style="background: #2563EB; border-color: #2563EB; width: 100%; padding: 8px;">➕ 新增家具物件</button>
      </div>
    </div>

    <!-- 標籤 2：地面格局與風水坐向設定 -->
    <div class="tab-content" id="tab-content-room" style="display: none;">
      <div class="panel-title">🏠 房間地面總體尺寸 (cm)</div>
      <div class="field-group">
        <label>長寬尺寸 (X × Y)</label>
        <div class="field-row">
          <input type="number" id="room-w" title="寬度 X">
          <input type="number" id="room-d" title="深度 Y">
        </div>
      </div>
      <div class="field-group">
        <label>天花板高度 (Z)</label>
        <input type="number" id="room-h">
      </div>

      <div class="panel-title" style="margin-top: 10px;">🧭 專業八方坐向羅盤盤面</div>
      <div class="field-group" style="flex-direction: row; align-items: center; justify-content: space-between;">
        <label style="margin: 0;">顯示羅盤八方盤面</label>
        <input type="checkbox" id="compass-show" checked style="cursor: pointer;">
      </div>
      <div class="field-group">
        <label>羅盤中心點 (X, Y 坐標)</label>
        <div class="field-row">
          <input type="number" id="compass-x">
          <input type="number" id="compass-y">
        </div>
      </div>
      <div class="field-group">
        <label>坐向旋轉偏角 (0°～360°)</label>
        <input type="number" id="compass-rot" min="0" max="360">
      </div>

      <div class="panel-title" style="margin-top: 10px;">🔲 右上留白凹位 (cm)</div>
      <div class="field-group">
        <label>留白尺寸 (寬 × 深)</label>
        <div class="field-row">
          <input type="number" id="void-w">
          <input type="number" id="void-d">
        </div>
      </div>
      <div class="field-group">
        <label>留白起始位置 (X, Y)</label>
        <div class="field-row">
          <input type="number" id="void-x">
          <input type="number" id="void-y">
        </div>
      </div>

      <button id="btn-apply-room" style="background: #3B82F6; border-color: #3B82F6; width: 100%; margin-top: 6px;">套用格局修改</button>
    </div>

    <!-- 標籤 3：專案存檔、下載與上傳 -->
    <div class="tab-content" id="tab-content-save" style="display: none;">
      <div class="panel-title">💾 儲存與讀取 (本地 App)</div>
      <div style="font-size: 12px; color: #94A3B8; line-height: 1.5;">
        直接保存在瀏覽器緩存中，關閉或重新整理網頁後隨時一鍵回復。
      </div>
      <button id="btn-save-local" class="primary" style="width: 100%;">儲存目前設計至 App</button>
      <button id="btn-load-local" style="width: 100%;">讀取已儲存之設計</button>

      <div class="panel-title" style="margin-top: 16px;">📁 檔案下載與匯入 (永續備份)</div>
      <div style="font-size: 12px; color: #94A3B8; line-height: 1.5;">
        將整套設計下載為 JSON 檔案，可在任何電腦隨時上傳載入。
      </div>
      <button id="btn-export-file" style="width: 100%; background: #4F46E5; border-color: #4F46E5;">📥 匯出並下載專案檔案 (.json)</button>
      
      <div class="field-group" style="margin-top: 8px;">
        <label>📤 載入先前儲存的專案檔案</label>
        <input type="file" id="file-import" accept=".json" style="font-size: 11px; color: #8F96A0;">
      </div>

      <div style="margin-top: 20px;">
        <button id="btn-reset-default" style="width: 100%; background: #475569; border-color: #475569;">🔄 重置回附圖原始配置</button>
      </div>
    </div>
  </div>

  <!-- 中間畫布區 -->
  <div class="center-canvas">
    <div class="toolbar">
      <div class="btn-group">
        <button id="btn-mode-2d" class="active">2D 平面互動配置</button>
        <button id="btn-mode-3d">3D 立體全景視圖</button>
      </div>
      <div style="font-size: 12px; color: #94A3B8;">
        🖱️ <b>視角控制</b>：滾輪縮放 | 中鍵拖曳平移 (或按住 Alt / 空白鍵 + 左鍵平移)
      </div>
    </div>

    <!-- 浮動畫布視角按鈕 -->
    <div class="view-controls">
      <button id="btn-zoom-fit">🔍 適配畫面</button>
      <button id="btn-zoom-reset">1:1 重置視角</button>
    </div>
    
    <div id="canvas-container">
      <canvas id="fabric-canvas"></canvas>
    </div>
    <div id="three-container"></div>
  </div>

  <!-- 右側物件清單 -->
  <div class="right-panel">
    <div class="panel-title">
      <span>📋 房間物件列表</span>
      <span id="obj-count" style="font-size: 12px; color: #94A3B8;">0</span>
    </div>
    <div class="item-list" id="item-list-container"></div>
  </div>
</div>

<script>
  // 核心狀態數據
  let appState = {initial_data_json};
  let activeId = null;
  let canvas, scene, camera, renderer, controls;
  let currentMode = "2D";
  
  // 畫布縮放平移狀態
  let isPanning = false;
  let lastPosX = 0, lastPosY = 0;

  // --- 1. 左側標籤頁切換 ---
  function switchLeftTab(tab) {{
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
    
    document.getElementById("tab-btn-" + tab).classList.add("active");
    document.getElementById("tab-content-" + tab).style.display = "flex";
  }}

  // --- 2. 初始化 Fabric 2D 互動畫布 ---
  function initFabric() {{
    const container = document.getElementById("canvas-container");
    canvas = new fabric.Canvas('fabric-canvas', {{
      width: container.clientWidth,
      height: container.clientHeight,
      backgroundColor: '#0A0C10',
      selection: true,
      preserveObjectStacking: true
    }});

    // 註冊畫布平移與滾輪縮放 (Pan & Zoom)
    canvas.on('mouse:wheel', function(opt) {{
      const delta = opt.e.deltaY;
      let zoom = canvas.getZoom();
      zoom *= 0.999 ** delta;
      if (zoom > 5) zoom = 5;
      if (zoom < 0.2) zoom = 0.2;
      canvas.zoomToPoint({{ x: opt.e.offsetX, y: opt.e.offsetY }}, zoom);
      opt.e.preventDefault();
      opt.e.stopPropagation();
    }});

    // 支援滑鼠中鍵 或 按住 Alt/Space 拖曳畫布
    canvas.on('mouse:down', function(opt) {{
      const evt = opt.e;
      if (evt.button === 1 || evt.altKey || evt.spaceKey) {{
        isPanning = true;
        canvas.selection = false;
        lastPosX = evt.clientX;
        lastPosY = evt.clientY;
      }}
    }});

    canvas.on('mouse:move', function(opt) {{
      if (isPanning) {{
        const evt = opt.e;
        const vpt = canvas.viewportTransform;
        vpt[4] += evt.clientX - lastPosX;
        vpt[5] += evt.clientY - lastPosY;
        canvas.requestRenderAll();
        lastPosX = evt.clientX;
        lastPosY = evt.clientY;
      }}
    }});

    canvas.on('mouse:up', function() {{
      if (isPanning) {{
        isPanning = false;
        canvas.selection = true;
      }}
    }});

    // 物件互動監聽
    canvas.on('selection:created', onObjectSelected);
    canvas.on('selection:updated', onObjectSelected);
    canvas.on('selection:cleared', onObjectDeselected);
    canvas.on('object:modified', onObjectModified);
    canvas.on('object:moving', onObjectModified);
    canvas.on('object:scaling', onObjectModified);
    canvas.on('object:rotating', onObjectModified);

    renderFullScene();
    initRoomFormValues();
    zoomToFit();
  }}

  // 繪製整套場景（背景格局、專業坐向盤、家具）
  function renderFullScene() {{
    canvas.clear();
    canvas.backgroundColor = '#0A0C10';

    // 1. 房間地面可使用區域 (藍色底盤)
    const floor = new fabric.Rect({{
      left: 0, top: 0,
      width: appState.room.width,
      height: appState.room.depth,
      fill: '#5089C6',
      stroke: '#28588E',
      strokeWidth: 2,
      selectable: false,
      evented: false
    }});
    canvas.add(floor);

    // 2. 右上留白凹位 (白色留白)
    const v = appState.void;
    const voidBox = new fabric.Rect({{
      left: v.x, top: v.y, width: v.w, height: v.d,
      fill: '#FFFFFF', stroke: '#CBD5E1', strokeWidth: 1,
      selectable: false, evented: false
    }});
    canvas.add(voidBox);

    // 3. 窗戶 (主窗、小窗)
    appState.windows.forEach(w => {{
      const win = new fabric.Rect({{
        left: w.x, top: w.y, width: w.w, height: w.d,
        fill: '#F59E0B', stroke: '#B45309', strokeWidth: 1.5,
        selectable: false, evented: false
      }});
      canvas.add(win);
    }});

    // 4. 專家級八方風水／坐向羅盤盤面
    if (appState.compass.show) {{
      renderExpertCompass();
    }}

    // 5. 家具物件
    appState.items.forEach(item => createFabricItem(item));

    renderRightPanel();
    canvas.requestRenderAll();
  }}

  // 專家級八方羅盤渲染
  function renderExpertCompass() {{
    const cx = appState.compass.x;
    const cy = appState.compass.y;
    const rot = appState.compass.rotation || 0;
    const radius = Math.max(appState.room.width, appState.room.depth) * 0.75;

    const compassGroup = [];

    // 同心測距圓環 (多層科技風測距)
    [radius * 0.25, radius * 0.5, radius * 0.75, radius].forEach((r, idx) => {{
      compassGroup.push(new fabric.Circle({{
        left: cx - r, top: cy - r, radius: r,
        fill: 'transparent',
        stroke: idx === 3 ? 'rgba(255, 255, 255, 0.4)' : 'rgba(255, 255, 255, 0.15)',
        strokeWidth: idx === 3 ? 1.5 : 1,
        strokeDashArray: idx % 2 === 1 ? [4, 4] : null,
        selectable: false, evented: false
      }}));
    }});

    // 八方 45 度精密分割線與方位文字 (以附圖東在左、北在下為基準)
    // 0°: 西, 45°: 西北, 90°: 南, 135°: 東南, 180°: 東, 225°: 東北, 270°: 北, 315°: 西南
    const directions = [
      {{ deg: 0, label: "正西 [兌]", primary: true }},
      {{ deg: 45, label: "西北 [乾]", primary: false }},
      {{ deg: 90, label: "正南 [離]", primary: true }},
      {{ deg: 135, label: "東南 [巽]", primary: false }},
      {{ deg: 180, label: "正東 [震]", primary: true }},
      {{ deg: 225, label: "東北 [艮]", primary: false }},
      {{ deg: 270, label: "正北 [坎]", primary: true }},
      {{ deg: 315, label: "西南 [坤]", primary: false }}
    ];

    directions.forEach(dir => {{
      const totalDeg = dir.deg + rot;
      const rad = totalDeg * Math.PI / 180;
      const ex = cx + radius * Math.cos(rad);
      const ey = cy + radius * Math.sin(rad);

      // 放射輔助線
      compassGroup.push(new fabric.Line([cx, cy, ex, ey], {{
        stroke: dir.primary ? 'rgba(255, 255, 255, 0.75)' : 'rgba(255, 255, 255, 0.3)',
        strokeWidth: dir.primary ? 2 : 1,
        selectable: false, evented: false
      }}));

      // 方位端點科技標籤
      const tx = cx + (radius + 20) * Math.cos(rad);
      const ty = cy + (radius + 20) * Math.sin(rad);
      compassGroup.push(new fabric.Text(dir.label, {{
        left: tx, top: ty,
        fontSize: dir.primary ? 13 : 11,
        fontWeight: dir.primary ? 'bold' : 'normal',
        fill: dir.primary ? '#F3E8FF' : '#94A3B8',
        originX: 'center', originY: 'center',
        selectable: false, evented: false
      }}));
    }});

    // 中心天心點 (帶內光暈效果)
    compassGroup.push(new fabric.Circle({{
      left: cx - 5, top: cy - 5, radius: 5,
      fill: '#A855F7', stroke: '#FFFFFF', strokeWidth: 2,
      selectable: false, evented: false
    }}));

    compassGroup.forEach(obj => canvas.add(obj));
  }}

  // 建立可直接移動、旋轉、拉伸的家具群組
  function createFabricItem(item) {{
    const rect = new fabric.Rect({{
      width: item.w,
      height: item.d,
      fill: item.color,
      stroke: '#1E293B',
      strokeWidth: 1.5,
      originX: 'center', originY: 'center'
    }});

    const hVal = item.h || 30;
    const label = `${{item.name}}\\n${{Math.round(item.w)}}×${{Math.round(item.d)}}`;
    const text = new fabric.Text(label, {{
      fontSize: 12,
      fill: '#FFFFFF',
      originX: 'center', originY: 'center',
      textAlign: 'center',
      fontFamily: '-apple-system, sans-serif'
    }});

    const group = new fabric.Group([rect, text], {{
      left: item.x + item.w / 2,
      top: item.y + item.d / 2,
      angle: item.rot || 0,
      originX: 'center', originY: 'center',
      itemId: item.id
    }});

    group.setControlsVisibility({{
      mt: true, mb: true, ml: true, mr: true,
      tl: true, tr: true, bl: true, br: true,
      mtr: true // 頂部旋轉圓點
    }});

    // 若有材質貼圖則套用
    if (item.texture) {{
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

  // --- 3. 雙向選取與聯動監聽 ---
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

    // 計算拉伸後的實際寬深
    const actualW = Math.round(target.width * target.scaleX);
    const actualD = Math.round(target.height * target.scaleY);

    item.w = actualW;
    item.d = actualD;
    item.rot = Math.round(target.angle % 360);
    item.x = Math.round(target.left - actualW / 2);
    item.y = Math.round(target.top - actualD / 2);

    target.set({{ scaleX: 1, scaleY: 1 }});
    target.item(0).set({{ width: item.w, height: item.d }});
    target.item(1).set({{ text: `${{item.name}}\\n${{item.w}}×${{item.d}}` }});

    updateLeftItemPanel();
    renderRightPanel();
  }}

  function updateLeftItemPanel() {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;

    document.getElementById("no-selection").style.display = "none";
    document.getElementById("prop-editor").style.display = "block";

    document.getElementById("prop-name").value = item.name;
    document.getElementById("prop-w").value = Math.round(item.w);
    document.getElementById("prop-d").value = Math.round(item.d);
    document.getElementById("prop-h").value = item.h || 30;
    document.getElementById("prop-rot").value = item.rot || 0;
    document.getElementById("prop-x").value = Math.round(item.x);
    document.getElementById("prop-y").value = Math.round(item.y);
    document.getElementById("prop-color").value = item.color;
  }}

  // 左側表單輸入監聽
  document.getElementById("prop-name").addEventListener("input", e => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.name = e.target.value;
    syncCanvasItem(item);
  }});
  document.getElementById("prop-w").addEventListener("input", e => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.w = parseFloat(e.target.value) || 10;
    syncCanvasItem(item);
  }});
  document.getElementById("prop-d").addEventListener("input", e => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.d = parseFloat(e.target.value) || 10;
    syncCanvasItem(item);
  }});
  document.getElementById("prop-h").addEventListener("input", e => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.h = parseFloat(e.target.value) || 30;
    renderRightPanel();
  }});
  document.getElementById("prop-rot").addEventListener("input", e => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.rot = parseFloat(e.target.value) || 0;
    syncCanvasItem(item);
  }});
  document.getElementById("prop-x").addEventListener("input", e => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.x = parseFloat(e.target.value) || 0;
    syncCanvasItem(item);
  }});
  document.getElementById("prop-y").addEventListener("input", e => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.y = parseFloat(e.target.value) || 0;
    syncCanvasItem(item);
  }});
  document.getElementById("prop-color").addEventListener("input", e => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.color = e.target.value;
    item.texture = "";
    syncCanvasItem(item);
  }});

  // 材質上傳
  document.getElementById("prop-texture-file").addEventListener("change", function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(f) {{
      const item = appState.items.find(i => i.id === activeId);
      if (!item) return;
      item.texture = f.target.result;
      syncCanvasItem(item);
    }};
    reader.readAsDataURL(file);
  }});

  function syncCanvasItem(item) {{
    const group = canvas.getObjects().find(o => o.itemId === item.id);
    if (!group) return;

    group.set({{
      left: item.x + item.w / 2,
      top: item.y + item.d / 2,
      angle: item.rot
    }});

    const rect = group.item(0);
    rect.set({{ width: item.w, height: item.d, fill: item.color }});
    group.item(1).set({{ text: `${{item.name}}\\n${{Math.round(item.w)}}×${{Math.round(item.d)}}` }});

    if (item.texture) {{
      fabric.Image.fromURL(item.texture, function(img) {{
        img.scaleToWidth(item.w);
        img.scaleToHeight(item.d);
        const pattern = new fabric.Pattern({{ source: img.getElement(), repeat: 'repeat' }});
        rect.set('fill', pattern);
        canvas.requestRenderAll();
      }});
    }}

    group.setCoords();
    canvas.requestRenderAll();
    renderRightPanel();
  }}

  // 刪除、複製與新增
  document.getElementById("btn-delete").addEventListener("click", () => {{
    if (!activeId) return;
    appState.items = appState.items.filter(i => i.id !== activeId);
    const group = canvas.getObjects().find(o => o.itemId === activeId);
    if (group) canvas.remove(group);
    canvas.discardActiveObject();
    onObjectDeselected();
    renderRightPanel();
  }});

  document.getElementById("btn-duplicate").addEventListener("click", () => {{
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    const newItem = JSON.parse(JSON.stringify(item));
    newItem.id = "item_" + Date.now();
    newItem.name = item.name + " (複本)";
    newItem.x += 25; newItem.y += 25;
    appState.items.push(newItem);
    createFabricItem(newItem);
    selectItemById(newItem.id);
  }});

  document.getElementById("btn-add-new").addEventListener("click", () => {{
    const newItem = {{
      id: "item_" + Date.now(),
      name: "新家具",
      x: 120, y: 120,
      w: 60, d: 50, h: 30, // 預設 30cm
      rot: 0,
      color: "#38BDF8",
      texture: ""
    }};
    appState.items.push(newItem);
    createFabricItem(newItem);
    selectItemById(newItem.id);
  }});

  // --- 4. 地面格局與坐向面板設定 ---
  function initRoomFormValues() {{
    document.getElementById("room-w").value = appState.room.width;
    document.getElementById("room-d").value = appState.room.depth;
    document.getElementById("room-h").value = appState.room.height;

    document.getElementById("compass-show").checked = appState.compass.show;
    document.getElementById("compass-x").value = appState.compass.x;
    document.getElementById("compass-y").value = appState.compass.y;
    document.getElementById("compass-rot").value = appState.compass.rotation || 0;

    document.getElementById("void-w").value = appState.void.w;
    document.getElementById("void-d").value = appState.void.d;
    document.getElementById("void-x").value = appState.void.x;
    document.getElementById("void-y").value = appState.void.y;
  }}

  document.getElementById("btn-apply-room").addEventListener("click", () => {{
    appState.room.width = parseFloat(document.getElementById("room-w").value) || 400;
    appState.room.depth = parseFloat(document.getElementById("room-d").value) || 300;
    appState.room.height = parseFloat(document.getElementById("room-h").value) || 280;

    appState.compass.show = document.getElementById("compass-show").checked;
    appState.compass.x = parseFloat(document.getElementById("compass-x").value) || 200;
    appState.compass.y = parseFloat(document.getElementById("compass-y").value) || 150;
    appState.compass.rotation = parseFloat(document.getElementById("compass-rot").value) || 0;

    appState.void.w = parseFloat(document.getElementById("void-w").value) || 0;
    appState.void.d = parseFloat(document.getElementById("void-d").value) || 0;
    appState.void.x = parseFloat(document.getElementById("void-x").value) || 0;
    appState.void.y = parseFloat(document.getElementById("void-y").value) || 0;

    renderFullScene();
  }});

  // --- 5. 右側清單與高亮 ---
  function renderRightPanel() {{
    const container = document.getElementById("item-list-container");
    document.getElementById("obj-count").innerText = appState.items.length;
    container.innerHTML = "";

    appState.items.forEach(item => {{
      const card = document.createElement("div");
      card.className = "item-card" + (item.id === activeId ? " selected" : "");
      card.onclick = () => selectItemById(item.id);

      const hVal = item.h || 30;
      card.innerHTML = `
        <div class="name">
          <span>${{item.name}}</span>
          <span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${{item.color}};"></span>
        </div>
        <div class="dims">${{Math.round(item.w)}} × ${{Math.round(item.d)}} × ${{hVal}} cm | ${{item.rot || 0}}°</div>
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

  // --- 6. 畫布視角適配 (Zoom & Pan Controls) ---
  function zoomToFit() {{
    const rw = appState.room.width;
    const rd = appState.room.depth;
    const container = document.getElementById("canvas-container");
    const cw = container.clientWidth - 80;
    const ch = container.clientHeight - 80;

    const scale = Math.min(cw / rw, ch / rd, 1.8);
    const offsetX = (container.clientWidth - rw * scale) / 2;
    const offsetY = (container.clientHeight - rd * scale) / 2;

    canvas.setViewportTransform([scale, 0, 0, scale, offsetX, offsetY]);
    canvas.requestRenderAll();
  }}

  document.getElementById("btn-zoom-fit").addEventListener("click", zoomToFit);
  document.getElementById("btn-zoom-reset").addEventListener("click", () => {{
    canvas.setViewportTransform([1, 0, 0, 1, 50, 50]);
    canvas.requestRenderAll();
  }});

  // --- 7. 存檔與匯入匯出機制 ---
  // 本地儲存
  document.getElementById("btn-save-local").addEventListener("click", () => {{
    localStorage.setItem("room_planner_data", JSON.stringify(appState));
    alert("✅ 專案已成功儲存至本機瀏覽器！");
  }});

  document.getElementById("btn-load-local").addEventListener("click", () => {{
    const saved = localStorage.getItem("room_planner_data");
    if (saved) {{
      appState = JSON.parse(saved);
      initRoomFormValues();
      renderFullScene();
      zoomToFit();
      alert("✅ 已成功讀取儲存的專案！");
    }} else {{
      alert("⚠️ 目前尚無本機儲存紀錄！");
    }}
  }});

  // 下載 JSON 檔案
  document.getElementById("btn-export-file").addEventListener("click", () => {{
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(appState, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", "room_design_" + new Date().toISOString().slice(0, 10) + ".json");
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }});

  // 上傳 JSON 檔案
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
        alert("✅ 專案檔案上傳成功並已載入！");
      }} catch(err) {{
        alert("❌ 檔案解析失敗，請確認是否為正確的 JSON 格式！");
      }}
    }};
    reader.readAsText(file);
  }});

  // 重置回預設
  document.getElementById("btn-reset-default").addEventListener("click", () => {{
    if (confirm("確定要重置為附圖原始配置嗎？未儲存的變更將會遺失。")) {{
      appState = JSON.parse(JSON.stringify({initial_data_json}));
      initRoomFormValues();
      renderFullScene();
      zoomToFit();
    }}
  }});

  // --- 8. 3D 視圖與模式切換 (Three.js) ---
  function initThree() {{
    const container = document.getElementById("three-container");
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0E1117);

    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 1, 4000);
    camera.position.set(appState.room.width / 2, 450, appState.room.depth + 300);

    renderer = new THREE.WebGLRenderer({{ antialias: true }});
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.target.set(appState.room.width / 2, 0, appState.room.depth / 2);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight.position.set(200, 500, 200);
    scene.add(dirLight);

    animateThree();
  }}

  function updateThreeScene() {{
    while (scene.children.length > 2) {{
      scene.remove(scene.children[scene.children.length - 1]);
    }}

    // 地板
    const floorGeo = new THREE.PlaneGeometry(appState.room.width, appState.room.depth);
    const floorMat = new THREE.MeshLambertMaterial({{ color: 0x5089C6 }});
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(appState.room.width / 2, 0, appState.room.depth / 2);
    scene.add(floor);

    // 留白
    const v = appState.void;
    const voidGeo = new THREE.PlaneGeometry(v.w, v.d);
    const voidMat = new THREE.MeshBasicMaterial({{ color: 0xffffff }});
    const voidMesh = new THREE.Mesh(voidGeo, voidMat);
    voidMesh.rotation.x = -Math.PI / 2;
    voidMesh.position.set(v.x + v.w / 2, 0.2, v.y + v.d / 2);
    scene.add(voidMesh);

    // 3D 坐向輔助線
    if (appState.compass.show) {{
      const cx = appState.compass.x;
      const cy = appState.compass.y;
      const rot = appState.compass.rotation || 0;
      const radius = Math.max(appState.room.width, appState.room.depth) * 0.7;

      for (let ang = 0; ang < 360; ang += 45) {{
        const rad = (ang + rot) * Math.PI / 180;
        const pts = [
          new THREE.Vector3(cx, 1, cy),
          new THREE.Vector3(cx + radius * Math.cos(rad), 1, cy + radius * Math.sin(rad))
        ];
        const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
        const lineMat = new THREE.LineBasicMaterial({{ color: 0xBA68C8, linewidth: 2 }});
        scene.add(new THREE.Line(lineGeo, lineMat));
      }}
    }}

    // 家具物件長方體
    appState.items.forEach(item => {{
      const h = item.h || 30;
      const geo = new THREE.BoxGeometry(item.w, h, item.d);
      let mat;

      if (item.texture) {{
        const tex = new THREE.TextureLoader().load(item.texture);
        mat = new THREE.MeshLambertMaterial({{ map: tex }});
      }} else {{
        mat = new THREE.MeshLambertMaterial({{ color: item.color }});
      }}

      const mesh = new THREE.Mesh(geo, mat);
      const rad = -(item.rot || 0) * Math.PI / 180;
      mesh.rotation.y = rad;
      mesh.position.set(item.x + item.w / 2, h / 2, item.y + item.d / 2);
      scene.add(mesh);
    }});
  }}

  function animateThree() {{
    requestAnimationFrame(animateThree);
    if (controls) controls.update();
    if (renderer && scene && camera) renderer.render(scene, camera);
  }}

  // 模式切換按鈕
  document.getElementById("btn-mode-2d").addEventListener("click", () => {{
    document.getElementById("btn-mode-2d").classList.add("active");
    document.getElementById("btn-mode-3d").classList.remove("active");
    document.getElementById("canvas-container").style.display = "block";
    document.getElementById("three-container").style.display = "none";
  }});

  document.getElementById("btn-mode-3d").addEventListener("click", () => {{
    document.getElementById("btn-mode-3d").classList.add("active");
    document.getElementById("btn-mode-2d").classList.remove("active");
    document.getElementById("canvas-container").style.display = "none";
    document.getElementById("three-container").style.display = "block";
    if (!renderer) initThree();
    updateThreeScene();
  }});

  window.addEventListener("load", initFabric);
</script>
</body>
</html>
"""

# 渲染應用畫布
components.html(html_code, height=940, scrolling=False)
