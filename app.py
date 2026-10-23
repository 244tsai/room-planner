import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(
    page_title="臥室空間設計 & 互動編輯系統",
    page_icon="📐",
    layout="wide"
)

# --- 預設格局與物件數據 (公分 cm) ---
DEFAULT_ROOM = {"width": 460, "depth": 360, "height": 280}
DEFAULT_COMPASS = {"x": 255, "y": 185}
DEFAULT_VOID = {"x": 370, "y": 240, "w": 90, "d": 120}
DEFAULT_WINDOWS = [
    {"x": 65, "y": 38, "w": 130, "d": 12},
    {"x": 355, "y": 38, "w": 20, "d": 12}
]

# 附圖原始預設家具
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

initial_data_json = json.dumps({
    "room": DEFAULT_ROOM,
    "compass": DEFAULT_COMPASS,
    "void": DEFAULT_VOID,
    "windows": DEFAULT_WINDOWS,
    "items": DEFAULT_ITEMS
})

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
    
    /* 左側編輯面板 */
    .left-panel {{ width: 280px; background: #181B20; border-right: 1px solid #2B303A; padding: 16px; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }}
    /* 中間畫布區域 */
    .center-canvas {{ flex: 1; display: flex; flex-direction: column; position: relative; background: #0A0D10; }}
    /* 右側清單面板 */
    .right-panel {{ width: 260px; background: #181B20; border-left: 1px solid #2B303A; padding: 16px; display: flex; flex-direction: column; overflow-y: auto; }}

    .toolbar {{ height: 50px; background: #15181E; border-bottom: 1px solid #2B303A; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; }}
    .btn-group {{ display: flex; gap: 8px; }}
    button {{ background: #262B35; color: #FFF; border: 1px solid #3A4150; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; }}
    button:hover {{ background: #3A4150; }}
    button.active {{ background: #FF4B4B; border-color: #FF4B4B; color: #FFF; }}
    
    .panel-title {{ font-size: 15px; font-weight: 600; color: #FFF; border-bottom: 1px solid #2B303A; padding-bottom: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; }}
    .field-group {{ display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }}
    .field-group label {{ font-size: 12px; color: #9AA0A6; }}
    .field-row {{ display: flex; gap: 8px; }}
    .field-row input {{ width: 100%; }}
    input[type="text"], input[type="number"] {{ background: #0E1117; border: 1px solid #3A4150; color: #FFF; padding: 6px 8px; border-radius: 4px; font-size: 13px; }}
    input[type="color"] {{ width: 100%; height: 36px; border: none; background: transparent; cursor: pointer; }}
    
    .item-list {{ display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }}
    .item-card {{ background: #20242D; border: 1px solid #2E3440; border-radius: 6px; padding: 10px; cursor: pointer; transition: all 0.2s; }}
    .item-card:hover {{ border-color: #4C566A; background: #252A35; }}
    .item-card.selected {{ border-color: #FF4B4B; background: #2D2328; }}
    .item-card .name {{ font-weight: 600; font-size: 13px; color: #FFF; display: flex; justify-content: space-between; }}
    .item-card .dims {{ font-size: 11px; color: #8F96A0; margin-top: 4px; }}

    #canvas-container, #three-container {{ width: 100%; height: calc(100vh - 50px); position: absolute; top: 50px; left: 0; }}
    #three-container {{ display: none; }}
  </style>
</head>
<body>

<div class="app-container">
  <!-- 左側編輯面板 -->
  <div class="left-panel">
    <div class="panel-title">✏️ 物件屬性編輯</div>
    
    <div id="no-selection" style="color: #6E7681; font-size: 13px; margin-top: 20px; text-align: center;">
      👈 請點選畫面上或右側列表中的物件進行即時編輯
    </div>

    <div id="prop-editor" style="display: none;">
      <div class="field-group">
        <label>名稱 (Name)</label>
        <input type="text" id="prop-name">
      </div>

      <div class="field-group">
        <label>長寬 (cm) [直接拖曳控制點也能拉伸]</label>
        <div class="field-row">
          <input type="number" id="prop-w" title="寬度 W">
          <input type="number" id="prop-d" title="深度 D">
        </div>
      </div>

      <div class="field-group">
        <label>高度 (cm, 預設 30cm)</label>
        <input type="number" id="prop-h" placeholder="預設 30">
      </div>

      <div class="field-group">
        <label>旋轉角度 (度 °) [或用上方圓點旋轉]</label>
        <input type="number" id="prop-rot" min="0" max="360">
      </div>

      <div class="field-group">
        <label>顏色外觀 (調色盤)</label>
        <input type="color" id="prop-color">
      </div>

      <div class="field-group">
        <label>🎨 上傳貼圖 / 材質</label>
        <input type="file" id="prop-texture-file" accept="image/*" style="font-size: 12px; color: #8F96A0;">
      </div>

      <div style="display: flex; gap: 8px; margin-top: 10px;">
        <button id="btn-duplicate" style="flex: 1;">複製此物件</button>
        <button id="btn-delete" style="flex: 1; background: #8B0000; border-color: #8B0000;">刪除</button>
      </div>
    </div>

    <hr style="border: 0; border-top: 1px solid #2B303A; margin: 10px 0;">
    
    <div class="panel-title">➕ 新增自訂物件</div>
    <button id="btn-add-new" style="background: #1F6FEB; border-color: #1F6FEB; width: 100%;">新增物件</button>
  </div>

  <!-- 中間畫布區 -->
  <div class="center-canvas">
    <div class="toolbar">
      <div class="btn-group">
        <button id="btn-mode-2d" class="active">2D 平面互動配置</button>
        <button id="btn-mode-3d">3D 立體全景視圖</button>
      </div>
      <div style="font-size: 12px; color: #8F96A0;">
        💡 提示：點擊直接移動，拉邊角控制點縮放，拉頂部圓點旋轉
      </div>
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
      <span id="obj-count" style="font-size: 12px; color: #8F96A0;">0</span>
    </div>
    <div class="item-list" id="item-list-container"></div>
  </div>
</div>

<script>
  const config = {initial_data_json};
  let items = config.items;
  let activeId = null;
  let scaleRatio = 1.6; // cm 轉 畫布 px 比例
  let canvas, scene, camera, renderer, controls;
  let currentMode = "2D";

  // --- 初始化 Fabric 2D 畫布 ---
  function initFabric() {{
    const container = document.getElementById("canvas-container");
    const width = container.clientWidth;
    const height = container.clientHeight;

    canvas = new fabric.Canvas('fabric-canvas', {{
      width: width,
      height: height,
      backgroundColor: '#0A0A0A',
      selection: true
    }});

    // 繪製背景底圖、窗戶、留白、坐向線條
    renderBackgroundElements();

    // 載入所有家具物件
    items.forEach(item => createFabricItem(item));

    // 物件互動監聽
    canvas.on('selection:created', onObjectSelected);
    canvas.on('selection:updated', onObjectSelected);
    canvas.on('selection:cleared', onObjectDeselected);
    canvas.on('object:modified', onObjectModified);
    canvas.on('object:moving', onObjectModified);
    canvas.on('object:scaling', onObjectModified);
    canvas.on('object:rotating', onObjectModified);

    renderRightPanel();
  }}

  // 繪製背景元素（地面藍色、右上留白、窗戶、八方坐向）
  function renderBackgroundElements() {{
    const rw = config.room.width * scaleRatio;
    const rd = config.room.depth * scaleRatio;
    const ox = 50, oy = 50;

    // 地面（可使用空間）
    const floor = new fabric.Rect({{
      left: ox, top: oy, width: rw, height: rd,
      fill: '#5794CE', stroke: '#295B91', strokeWidth: 2,
      selectable: false, evented: false
    }});
    canvas.add(floor);

    // 右上留白區
    const voidArea = new fabric.Rect({{
      left: ox + config.void.x * scaleRatio,
      top: oy + config.void.y * scaleRatio,
      width: config.void.w * scaleRatio,
      height: config.void.d * scaleRatio,
      fill: '#FFFFFF', stroke: '#DDDDDD', strokeWidth: 1,
      selectable: false, evented: false
    }});
    canvas.add(voidArea);

    // 下方窗戶 (主窗、小窗)
    config.windows.forEach(w => {{
      const win = new fabric.Rect({{
        left: ox + w.x * scaleRatio,
        top: oy + w.y * scaleRatio,
        width: w.w * scaleRatio,
        height: w.d * scaleRatio,
        fill: '#FDB813', stroke: '#C88D00', strokeWidth: 1,
        selectable: false, evented: false
      }});
      canvas.add(win);
    }});

    // 八方放射坐向線 (交叉中心)
    const cx = ox + config.compass.x * scaleRatio;
    const cy = oy + config.compass.y * scaleRatio;
    const angles = [0, 45, 90, 135, 180, 225, 270, 315];
    const lineLen = Math.max(rw, rd) * 1.5;

    angles.forEach(ang => {{
      const rad = ang * Math.PI / 180;
      const ex = cx + lineLen * Math.cos(rad);
      const ey = cy + lineLen * Math.sin(rad);
      const line = new fabric.Line([cx, cy, ex, ey], {{
        stroke: '#FFFFFF', strokeWidth: 3,
        selectable: false, evented: false
      }});
      canvas.add(line);
    }});

    // 紫色坐向方位標籤 (附圖傳統坐向：東在左、北在下)
    // 東
    const tagEast = new fabric.Rect({{ left: ox - 40, top: cy - 25, width: 45, height: 45, fill: '#BA68C8', selectable: false, evented: false }});
    const textEast = new fabric.Text('東', {{ left: ox - 28, top: cy - 18, fontSize: 26, fill: '#FFF', selectable: false, evented: false }});
    canvas.add(tagEast, textEast);

    // 北
    const tagNorth = new fabric.Rect({{ left: cx - 22, top: oy - 40, width: 45, height: 45, fill: '#BA68C8', selectable: false, evented: false }});
    const textNorth = new fabric.Text('北', {{ left: cx - 10, top: oy - 33, fontSize: 26, fill: '#FFF', selectable: false, evented: false }});
    canvas.add(tagNorth, textNorth);
  }}

  // 建立可直接移動、旋轉、拉伸的 Fabric 家具群組
  function createFabricItem(item) {{
    const ox = 50, oy = 50;
    const w = item.w * scaleRatio;
    const d = item.d * scaleRatio;

    const rect = new fabric.Rect({{
      width: w,
      height: d,
      fill: item.color,
      stroke: '#333333',
      strokeWidth: 1.5,
      originX: 'center',
      originY: 'center'
    }});

    const labelText = item.name + "\\n" + Math.round(item.w) + "x" + Math.round(item.d);
    const text = new fabric.Text(labelText, {{
      fontSize: 13,
      fill: '#FFFFFF',
      originX: 'center',
      originY: 'center',
      textAlign: 'center'
    }});

    const group = new fabric.Group([rect, text], {{
      left: ox + item.x * scaleRatio + w / 2,
      top: oy + item.y * scaleRatio + d / 2,
      angle: item.rot || 0,
      originX: 'center',
      originY: 'center',
      itemId: item.id
    }});

    // 設置控制點樣式（方便縮放與旋轉）
    group.setControlsVisibility({{
      mt: true, mb: true, ml: true, mr: true,
      tl: true, tr: true, bl: true, br: true,
      mtr: true // 頂部旋轉控制點
    }});

    canvas.add(group);
  }}

  // --- 選取與同步邏輯 ---
  function onObjectSelected(e) {{
    const target = e.selected ? e.selected[0] : null;
    if (!target || !target.itemId) return;
    activeId = target.itemId;
    updateLeftPanel();
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
    
    const item = items.find(i => i.id === target.itemId);
    if (!item) return;

    // 計算實際寬高（考慮拉伸縮放 scaleX, scaleY）
    const actualW = (target.width * target.scaleX) / scaleRatio;
    const actualD = (target.height * target.scaleY) / scaleRatio;
    
    item.w = Math.round(actualW);
    item.d = Math.round(actualD);
    item.rot = Math.round(target.angle % 360);
    item.x = Math.round((target.left - (target.width * target.scaleX) / 2 - 50) / scaleRatio);
    item.y = Math.round((target.top - (target.height * target.scaleY) / 2 - 50) / scaleRatio);

    // 重設 group 尺寸與內部文字
    target.set({{ scaleX: 1, scaleY: 1 }});
    target.item(0).set({{ width: item.w * scaleRatio, height: item.d * scaleRatio }});
    target.item(1).set({{ text: item.name + "\\n" + item.w + "x" + item.d }});

    updateLeftPanel();
    renderRightPanel();
  }}

  // 更新左側編輯欄數值
  function updateLeftPanel() {{
    const item = items.find(i => i.id === activeId);
    if (!item) return;

    document.getElementById("no-selection").style.display = "none";
    document.getElementById("prop-editor").style.display = "block";

    document.getElementById("prop-name").value = item.name;
    document.getElementById("prop-w").value = Math.round(item.w);
    document.getElementById("prop-d").value = Math.round(item.d);
    document.getElementById("prop-h").value = item.h || 30;
    document.getElementById("prop-rot").value = item.rot || 0;
    document.getElementById("prop-color").value = item.color;
  }}

  // 左側輸入變更事件綁定
  document.getElementById("prop-name").addEventListener("input", e => {{
    const item = items.find(i => i.id === activeId);
    if (!item) return;
    item.name = e.target.value;
    syncCanvasItem(item);
  }});
  document.getElementById("prop-w").addEventListener("input", e => {{
    const item = items.find(i => i.id === activeId);
    if (!item) return;
    item.w = parseFloat(e.target.value) || 10;
    syncCanvasItem(item);
  }});
  document.getElementById("prop-d").addEventListener("input", e => {{
    const item = items.find(i => i.id === activeId);
    if (!item) return;
    item.d = parseFloat(e.target.value) || 10;
    syncCanvasItem(item);
  }});
  document.getElementById("prop-h").addEventListener("input", e => {{
    const item = items.find(i => i.id === activeId);
    if (!item) return;
    item.h = parseFloat(e.target.value) || 30;
  }});
  document.getElementById("prop-rot").addEventListener("input", e => {{
    const item = items.find(i => i.id === activeId);
    if (!item) return;
    item.rot = parseFloat(e.target.value) || 0;
    syncCanvasItem(item);
  }});
  document.getElementById("prop-color").addEventListener("input", e => {{
    const item = items.find(i => i.id === activeId);
    if (!item) return;
    item.color = e.target.value;
    item.texture = ""; // 切換顏色時清除自訂貼圖
    syncCanvasItem(item);
  }});

  // 貼圖上傳與材質套用
  document.getElementById("prop-texture-file").addEventListener("change", function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(f) {{
      const item = items.find(i => i.id === activeId);
      if (!item) return;
      item.texture = f.target.result;
      
      fabric.Image.fromURL(item.texture, function(img) {{
        const group = canvas.getObjects().find(o => o.itemId === item.id);
        if (group) {{
          img.scaleToWidth(item.w * scaleRatio);
          img.scaleToHeight(item.d * scaleRatio);
          const pattern = new fabric.Pattern({{
            source: img.getElement(),
            repeat: 'repeat'
          }});
          group.item(0).set('fill', pattern);
          canvas.renderAll();
        }}
      }});
    }};
    reader.readAsDataURL(file);
  }});

  // 將資料同步回 Fabric 畫布圖元
  function syncCanvasItem(item) {{
    const group = canvas.getObjects().find(o => o.itemId === item.id);
    if (!group) return;

    const w = item.w * scaleRatio;
    const d = item.d * scaleRatio;
    group.item(0).set({{ width: w, height: d, fill: item.color }});
    group.item(1).set({{ text: item.name + "\\n" + Math.round(item.w) + "x" + Math.round(item.d) }});
    group.set({{ angle: item.rot }});
    group.setCoords();
    canvas.renderAll();
    renderRightPanel();
  }}

  // 刪除與複製物件
  document.getElementById("btn-delete").addEventListener("click", () => {{
    if (!activeId) return;
    items = items.filter(i => i.id !== activeId);
    const group = canvas.getObjects().find(o => o.itemId === activeId);
    if (group) canvas.remove(group);
    canvas.discardActiveObject();
    onObjectDeselected();
    renderRightPanel();
  }});

  document.getElementById("btn-duplicate").addEventListener("click", () => {{
    const item = items.find(i => i.id === activeId);
    if (!item) return;
    const newItem = JSON.parse(JSON.stringify(item));
    newItem.id = "item_" + Date.now();
    newItem.name = item.name + " (複本)";
    newItem.x += 20;
    newItem.y += 20;
    items.push(newItem);
    createFabricItem(newItem);
    selectItemById(newItem.id);
    renderRightPanel();
  }});

  document.getElementById("btn-add-new").addEventListener("click", () => {{
    const newItem = {{
      id: "item_" + Date.now(),
      name: "新家具",
      x: 100, y: 100,
      w: 60, d: 50, h: 30, // 預設 30cm 高
      rot: 0,
      color: "#FF9999",
      texture: ""
    }};
    items.push(newItem);
    createFabricItem(newItem);
    selectItemById(newItem.id);
    renderRightPanel();
  }});

  // 右側清單渲染與聯動
  function renderRightPanel() {{
    const container = document.getElementById("item-list-container");
    document.getElementById("obj-count").innerText = items.length;
    container.innerHTML = "";

    items.forEach(item => {{
      const card = document.createElement("div");
      card.className = "item-card" + (item.id === activeId ? " selected" : "");
      card.onclick = () => selectItemById(item.id);

      const hVal = item.h || 30;
      card.innerHTML = `
        <div class="name">
          <span>${{item.name}}</span>
          <span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:${{item.color}};"></span>
        </div>
        <div class="dims">尺寸: ${{Math.round(item.w)}} × ${{Math.round(item.d)}} × ${{hVal}} cm | ${{item.rot || 0}}°</div>
      `;
      container.appendChild(card);
    }});
  }}

  function highlightRightPanel() {{
    document.querySelectorAll(".item-card").forEach((card, idx) => {{
      if (items[idx] && items[idx].id === activeId) {{
        card.classList.add("selected");
        card.scrollIntoView({{ behavior: "smooth", block: "nearest" }});
      }} else {{
        card.classList.remove("selected");
      }}
    }});
  }}

  // 點擊右邊列表物件時，畫面上同時選取
  function selectItemById(id) {{
    activeId = id;
    const group = canvas.getObjects().find(o => o.itemId === id);
    if (group) {{
      canvas.setActiveObject(group);
      canvas.renderAll();
    }}
    updateLeftPanel();
    highlightRightPanel();
  }}

  // --- 3D 視圖渲染 (Three.js) ---
  function initThree() {{
    const container = document.getElementById("three-container");
    const width = container.clientWidth;
    const height = container.clientHeight;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0E1117);

    camera = new THREE.PerspectiveCamera(45, width / height, 1, 3000);
    camera.position.set(250, 400, 500);

    renderer = new THREE.WebGLRenderer({{ antialias: true }});
    renderer.setSize(width, height);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.target.set(config.room.width / 2, 0, config.room.depth / 2);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight.position.set(200, 400, 200);
    scene.add(dirLight);

    animateThree();
  }}

  function updateThreeScene() {{
    // 清除舊模型
    while (scene.children.length > 2) {{
      scene.remove(scene.children[scene.children.length - 1]);
    }}

    // 地板
    const floorGeo = new THREE.PlaneGeometry(config.room.width, config.room.depth);
    const floorMat = new THREE.MeshLambertMaterial({{ color: 0x5794CE }});
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(config.room.width / 2, 0, config.room.depth / 2);
    scene.add(floor);

    // 留白區
    const voidGeo = new THREE.PlaneGeometry(config.void.w, config.void.d);
    const voidMat = new THREE.MeshBasicMaterial({{ color: 0xffffff }});
    const voidMesh = new THREE.Mesh(voidGeo, voidMat);
    voidMesh.rotation.x = -Math.PI / 2;
    voidMesh.position.set(config.void.x + config.void.w / 2, 0.2, config.void.y + config.void.d / 2);
    scene.add(voidMesh);

    // 家具物件 3D 長方體
    items.forEach(item => {{
      const h = item.h || 30;
      const geo = new THREE.BoxGeometry(item.w, h, item.d);
      
      let mat;
      if (item.texture) {{
        const texture = new THREE.TextureLoader().load(item.texture);
        mat = new THREE.MeshLambertMaterial({{ map: texture }});
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

  // 啟動應用
  window.addEventListener("load", initFabric);
</script>
</body>
</html>
"""

# 渲染整合應用
components.html(html_code, height=920, scrolling=False)
