let appState = JSON.parse(JSON.stringify(INITIAL_CONFIG));
if (!appState.voids && appState.void) {
  appState.voids = [{ id: "void_1", name: "留白處 1", x: appState.void.x, y: appState.void.y, w: appState.void.w, d: appState.void.d }];
}
if (!appState.categories) appState.categories = ["床", "大型家具", "收納櫃體", "門窗建材", "機電開關", "牆面裝飾"];
if (!appState.categories.includes("床")) appState.categories.unshift("床");
appState.items.forEach(it => { if (it.id === "bed" || it.name === "床") it.category = "床"; });
if (!appState.human) appState.human = { x: 230, y: 230, z: 0, height: 178, rot: 0, pitch: 0, posture: "stand", lock_horizontal: false };
if (appState.room.show_walls === undefined) appState.room.show_walls = true;
if (appState.room.show_ceiling === undefined) appState.room.show_ceiling = false;
if (appState.room.lock_scale === undefined) appState.room.lock_scale = false;
if (appState.compass.auto_center === undefined) appState.compass.auto_center = true;

// 若啟用自動置中，確保初始八方座向中心位於地基長寬除以2
if (appState.compass.auto_center) {
  appState.compass.x = Math.round(appState.room.width / 2);
  appState.compass.y = Math.round(appState.room.depth / 2);
}

let activeId = null;
let canvas, scene, camera, renderer, controls, transformControl;
let currentMode = "2D";
let gizmoMode = "translate";
let selectable3DMeshes = [];
let walkable3DMeshes = [];
let human3DGroup = null;
let targetRingMesh = null;

let isDraggingCanvas = false;
let forcePanMode = false;
let lastClientX = 0, lastClientY = 0;
let touchStartDist = 0, touchStartZoom = 1;
let isOverTrash = false;

let fpvMoveDir = { forward: 0, right: 0 };
let walkTarget = null;
let isLookingFPV = false;
let fpvLastX = 0, fpvLastY = 0;
let toastTimeout = null;
let draggedItemId = null;

// 記錄每個物件最後一次合法不重疊的位置與尺寸，供碰撞退回使用
let lastValidItemMap = {};

// 右側分類展開狀態：預設全部收合
let expandedCategories = new Set();

function showToast(msg) {
  const el = document.getElementById("toast-msg");
  if (!el) return;
  el.innerText = msg;
  el.classList.add("show");
  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => el.classList.remove("show"), 1900);
}

function isBedItem(it) {
  return it.category === "床" || it.id === "bed" || (it.name && it.name.includes("床") && !it.name.includes("櫃"));
}

// 判斷是否為可調整 Z 軸的牆面物件 (窗戶、插座、開關、牆壁上物品)
function isZAdjustableWallType(t) {
  return ["window", "socket", "switch", "wall_item"].includes(t);
}

// 判斷是否為往牆壁外側突出的牆面設施 (窗戶、插座、開關)
function isOuterWallProtrudingType(t) {
  return ["window", "socket", "switch"].includes(t);
}

// 取得物件旋轉後的軸對齊邊界框 (AABB)
function getItemAABB(it) {
  const rad = (it.rot || 0) * Math.PI / 180;
  const cx = it.x + it.w / 2;
  const cy = it.y + it.d / 2;
  const cos = Math.abs(Math.cos(rad));
  const sin = Math.abs(Math.sin(rad));
  const bw = it.w * cos + it.d * sin;
  const bd = it.w * sin + it.d * cos;
  return {
    x0: cx - bw / 2,
    y0: cy - bd / 2,
    x1: cx + bw / 2,
    y1: cy + bd / 2,
    z0: it.z || 0,
    z1: (it.z || 0) + (it.h || 30)
  };
}

// 檢查兩個物件是否在 3D 空間 (X, Y, Z) 發生穿模重疊
function isTwoItemsOverlapping(a, b) {
  const boxA = getItemAABB(a);
  const boxB = getItemAABB(b);
  const eps = 0.5; // 允許貼齊邊界 0.5cm 容差
  const overlapX = (boxA.x0 + eps < boxB.x1) && (boxA.x1 - eps > boxB.x0);
  const overlapY = (boxA.y0 + eps < boxB.y1) && (boxA.y1 - eps > boxB.y0);
  const overlapZ = (boxA.z0 + eps < boxB.z1) && (boxA.z1 - eps > boxB.z0);
  return overlapX && overlapY && overlapZ;
}

// 強制執行所有物理約束：
// 1. 高度防穿模 (不可低於地板 Z<0、不可高於天花板 Z+H > roomH)
// 2. 除窗戶/插座/開關/牆壁上物品外，其餘物件一律強制在地板上 (Z=0)
// 3. 牆上物品/窗戶/開關/插座/門：強制吸附於四面牆壁，不可懸空飄在房內；其中窗戶/插座/開關往牆壁外側突出
// 4. 一般地面物件若超過牆壁邊界，直接移出至房間外備用區 (不卡在牆上穿模)
// 5. 檢查與其他所有物品是否重疊穿模
function enforceItemConstraints(item, showMsg = true) {
  const rw = appState.room.width;
  const rd = appState.room.depth;
  const rh = appState.room.height;
  const t = item.item_type || "furniture";

  // 限制物品自身高度不可超過天花板
  if ((item.h || 30) > rh) item.h = rh;

  // Z 軸與地板/天花板防穿模
  if (isZAdjustableWallType(t)) {
    item.z = Math.max(0, Math.min(rh - (item.h || 30), Math.round(item.z || 0)));
  } else {
    // 除窗戶、開關、插座、牆壁上物品外，所有家具與房門皆固定在地板上，不可懸浮
    item.z = 0;
  }

  // 牆面專屬物件吸附邏輯 (只能在牆壁上移動，不可飄進房間中央)
  if (["window", "socket", "switch", "wall_item", "door"].includes(t)) {
    const cx = item.x + item.w / 2;
    const cy = item.y + item.d / 2;
    const distN = Math.abs(cy - 0);
    const distS = Math.abs(cy - rd);
    const distW = Math.abs(cx - 0);
    const distE = Math.abs(cx - rw);
    const minDist = Math.min(distN, distS, distW, distE);

    const protrudeOut = isOuterWallProtrudingType(t); // 窗戶/開關/插座往牆壁外面突出，不佔房內空間
    const longSide = Math.max(item.w, item.d);
    const shortSide = Math.min(item.w, item.d);

    if (minDist === distN || minDist === distS) {
      // 吸附於北牆 (y=0) 或 南牆 (y=rd)
      item.w = longSide;
      item.d = Math.min(shortSide, 24);
      item.rot = 0;
      item.x = Math.max(0, Math.min(rw - item.w, Math.round(cx - item.w / 2)));
      if (minDist === distN) {
        item.y = protrudeOut ? -item.d : 0;
        item.wall = "north";
      } else {
        item.y = protrudeOut ? rd : rd - item.d;
        item.wall = "south";
      }
    } else {
      // 吸附於西牆 (x=0) 或 東牆 (x=rw)
      item.w = Math.min(shortSide, 24);
      item.d = longSide;
      item.rot = 0;
      item.y = Math.max(0, Math.min(rd - item.d, Math.round(cy - item.d / 2)));
      if (minDist === distW) {
        item.x = protrudeOut ? -item.w : 0;
        item.wall = "west";
      } else {
        item.x = protrudeOut ? rw : rw - item.w;
        item.wall = "east";
      }
    }
  } else {
    // 一般地面家具：檢查是否跨過牆壁穿模
    const box = getItemAABB(item);
    const insideRoom = (box.x0 >= 0 && box.x1 <= rw && box.y0 >= 0 && box.y1 <= rd);
    const completelyOutside = (box.x1 <= -5 || box.x0 >= rw + 5 || box.y1 <= -5 || box.y0 >= rd + 5);

    if (!insideRoom && !completelyOutside) {
      // 物件壓在牆壁上（超過牆壁）：直接將物品移出房間外備用區（不刪除）
      const cx = (box.x0 + box.x1) / 2;
      const cy = (box.y0 + box.y1) / 2;
      const bw = box.x1 - box.x0;
      const bd = box.y1 - box.y0;
      const gap = 25; // 移出牆外 25cm 備用區

      const overL = -box.x0;
      const overR = box.x1 - rw;
      const overT = -box.y0;
      const overB = box.y1 - rd;
      const maxOver = Math.max(overL, overR, overT, overB);

      if (maxOver === overL) item.x = Math.round(-bw - gap);
      else if (maxOver === overR) item.x = Math.round(rw + gap);
      else if (maxOver === overT) item.y = Math.round(-bd - gap);
      else item.y = Math.round(rd + gap);

      if (showMsg) showToast("📦 物品超過牆壁，已自動移至房間外備用區！");
    }
  }

  // 檢查物品與其他物品間是否互相穿模疊在一起
  for (let i = 0; i < appState.items.length; i++) {
    const other = appState.items[i];
    if (other.id === item.id) continue;
    if (isTwoItemsOverlapping(item, other)) {
      // 發生重疊：退回最後合法位置與尺寸
      const backup = lastValidItemMap[item.id];
      if (backup) {
        item.x = backup.x;
        item.y = backup.y;
        item.z = backup.z;
        item.w = backup.w;
        item.d = backup.d;
        item.h = backup.h;
        item.rot = backup.rot;
      }
      if (showMsg) showToast(`⚠️ 不可與「${other.name}」重疊穿模！`);
      return false;
    }
  }

  // 紀錄此次合法狀態
  saveValidItemBackup(item);
  return true;
}

function saveValidItemBackup(item) {
  lastValidItemMap[item.id] = {
    x: item.x, y: item.y, z: item.z || 0,
    w: item.w, d: item.d, h: item.h || 30, rot: item.rot || 0
  };
}

// 為新物件尋找不重疊的初始擺放位置
function findNonOverlappingSpot(newItem) {
  if (enforceItemConstraints(newItem, false)) return;
  const rw = appState.room.width, rd = appState.room.depth;
  for (let y = 10; y <= rd - newItem.d - 10; y += 25) {
    for (let x = 10; x <= rw - newItem.w - 10; x += 25) {
      newItem.x = x; newItem.y = y;
      if (enforceItemConstraints(newItem, false)) return;
    }
  }
  // 若房間內已滿，直接放置於房間右側外備用區
  newItem.x = rw + 30;
  newItem.y = 20;
  saveValidItemBackup(newItem);
}

// 人物行走碰撞檢測
function checkHumanWalkable(nx, ny) {
  const radius = 14;
  const rw = appState.room.width, rd = appState.room.depth;

  if (appState.room.show_walls) {
    if (nx < radius || nx > rw - radius || ny < radius || ny > rd - radius) {
      return { allowed: false, baseZ: appState.human.z || 0 };
    }
  }

  let supportZ = 0;
  for (let i = 0; i < appState.items.length; i++) {
    const it = appState.items[i];
    if (isOuterWallProtrudingType(it.item_type)) continue;
    if ((it.z || 0) > 120) continue;

    const rad = -(it.rot || 0) * Math.PI / 180;
    const cx = it.x + it.w / 2;
    const cy = it.y + it.d / 2;
    const dx = nx - cx;
    const dy = ny - cy;
    const lx = dx * Math.cos(rad) - dy * Math.sin(rad);
    const ly = dx * Math.sin(rad) + dy * Math.cos(rad);

    const halfW = it.w / 2;
    const halfD = it.d / 2;

    if (isBedItem(it)) {
      if (Math.abs(lx) <= halfW && Math.abs(ly) <= halfD) {
        supportZ = Math.max(supportZ, (it.z || 0) + (it.h || 55));
      }
    } else if (it.item_type === "furniture" || it.item_type === "wall_item") {
      if (Math.abs(lx) < halfW + radius && Math.abs(ly) < halfD + radius) {
        return { allowed: false, baseZ: appState.human.z || 0 };
      }
    }
  }
  return { allowed: true, baseZ: supportZ };
}

function tryMoveHumanTo(nx, ny, showBlockMsg = false) {
  const res = checkHumanWalkable(nx, ny);
  if (res.allowed) {
    appState.human.x = nx;
    appState.human.y = ny;
    appState.human.z = res.baseZ;
    return true;
  }
  const resX = checkHumanWalkable(nx, appState.human.y);
  if (resX.allowed) {
    appState.human.x = nx;
    appState.human.z = resX.baseZ;
    return true;
  }
  const resY = checkHumanWalkable(appState.human.x, ny);
  if (resY.allowed) {
    appState.human.y = ny;
    appState.human.z = resY.baseZ;
    return true;
  }
  if (showBlockMsg) showToast("⚠️ 前方有家具阻擋，人物無法穿越！");
  return false;
}

function getHumanEyeHeight() {
  const h = appState.human;
  const stature = h.height || 178;
  const baseZ = h.z || 0;

  if (h.posture === "lie") {
    return Math.round(baseZ + 22);
  } else if (h.posture === "sit") {
    if (baseZ > 0) return Math.round(baseZ + stature * 0.44);
    return Math.round(43 + stature * 0.44);
  }
  return Math.round(baseZ + stature * 0.93);
}

const FEIXING_META = {
  1: { name: "一白貪狼", el: "水", luck: "大吉 · 桃花/人緣", color: "#38BDF8", bg: "rgba(14, 116, 144, 0.28)", tip: "利感情、貴人、文昌" },
  2: { name: "二黑巨門", el: "土", luck: "凶 · 病符星", color: "#F87171", bg: "rgba(153, 27, 27, 0.30)", tip: "注意健康，宜掛金屬葫蘆化解" },
  3: { name: "三碧祿存", el: "木", luck: "凶 · 是非/官非", color: "#FB923C", bg: "rgba(154, 52, 18, 0.28)", tip: "易爭執，宜用紅色物件洩木氣" },
  4: { name: "四綠文曲", el: "木", luck: "吉 · 文昌/考運", color: "#4ADE80", bg: "rgba(21, 128, 61, 0.28)", tip: "利學業、研發、企劃創意" },
  5: { name: "五黃廉貞", el: "土", luck: "大凶 · 五黃煞", color: "#EF4444", bg: "rgba(185, 28, 28, 0.42)", tip: "忌動土動工，宜擺銅器或六帝錢" },
  6: { name: "六白武曲", el: "金", luck: "吉 · 偏財/貴人", color: "#FACC15", bg: "rgba(161, 98, 7, 0.28)", tip: "利事業升遷、技術與偏財運" },
  7: { name: "七赤破軍", el: "金", luck: "凶 · 破財/口舌", color: "#F472B6", bg: "rgba(157, 23, 77, 0.28)", tip: "防漏財小人，宜靜置或水局化解" },
  8: { name: "八白左輔", el: "土", luck: "大吉 · 正財星", color: "#FBBF24", bg: "rgba(180, 83, 9, 0.35)", tip: "利正財置產，宜保持明亮整潔" },
  9: { name: "九紫右弼", el: "火", luck: "大吉 · 當運喜慶", color: "#C084FC", bg: "rgba(107, 33, 168, 0.35)", tip: "九運當旺大吉星，利姻緣與百業" }
};
const LUOSHU_OFFSETS = { "SE": -1, "S": 4, "SW": -3, "E": -2, "C": 0, "W": 2, "NE": 3, "N": -4, "NW": 1 };

function getCenterStarByYear(year) {
  let mod = (2026 - year) % 9;
  let star = (1 + mod) % 9;
  return star <= 0 ? star + 9 : star;
}
function getStarAtDir(centerStar, dirKey) {
  let s = (centerStar + LUOSHU_OFFSETS[dirKey]) % 9;
  return s <= 0 ? s + 9 : s;
}

function toggleMobilePanel(target) {
  const lp = document.getElementById("left-panel");
  const rp = document.getElementById("right-panel");
  document.getElementById("mnav-left").classList.toggle("active", target === 'left');
  document.getElementById("mnav-right").classList.toggle("active", target === 'right');
  document.getElementById("mnav-canvas").classList.toggle("active", target === 'canvas');

  if (target === 'left') {
    lp.classList.toggle("open"); rp.classList.remove("open");
  } else if (target === 'right') {
    rp.classList.toggle("open"); lp.classList.remove("open");
  } else {
    lp.classList.remove("open"); rp.classList.remove("open");
  }
}

function switchLeftTab(tab) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
  document.getElementById("tab-btn-" + tab).classList.add("active");
  document.getElementById("tab-content-" + tab).style.display = "flex";
}

// 鎖定既有物品縮放 (2D 與 3D 同步)
window.toggleLockScaleBtn = function() {
  appState.room.lock_scale = !appState.room.lock_scale;
  syncLockScaleUI();
  renderFullScene();
};

function syncLockScaleUI() {
  const locked = !!appState.room.lock_scale;
  const chk = document.getElementById("lock-scale-chk");
  if (chk) chk.checked = locked;
  const b2d = document.getElementById("btn-lock-scale-2d");
  if (b2d) {
    b2d.innerText = locked ? "🔒 縮放: 鎖定" : "🔓 縮放: 開";
    b2d.classList.toggle("active", locked);
  }
  const b3d = document.getElementById("btn-lock-scale-3d");
  if (b3d) {
    b3d.innerText = locked ? "🔒 縮放: 鎖定" : "🔓 縮放: 開";
    b3d.classList.toggle("active", locked);
  }
  const bScaleGizmo = document.getElementById("btn-3d-scale");
  if (bScaleGizmo) {
    bScaleGizmo.style.opacity = locked ? "0.4" : "1";
  }
  if (locked && gizmoMode === "scale") {
    window.set3DGizmoMode("translate");
  }
}

function renderCategoryUI() {
  const newCatSel = document.getElementById("new-obj-category");
  const propCatSel = document.getElementById("prop-category");
  const tagsBox = document.getElementById("category-tags-container");

  const curNewVal = newCatSel.value;
  const curPropVal = propCatSel.value;

  newCatSel.innerHTML = "";
  propCatSel.innerHTML = "";
  tagsBox.innerHTML = "";

  appState.categories.forEach((cat, idx) => {
    newCatSel.add(new Option(cat, cat));
    propCatSel.add(new Option(cat, cat));

    const tag = document.createElement("div");
    tag.style.cssText = "background:#1F232B; border:1px solid #3B82F6; border-radius:14px; padding:4px 9px; font-size:11px; display:flex; align-items:center; gap:5px; transition:all 0.15s;";
    tag.setAttribute("data-cat", cat);
    tag.innerHTML = `<span>🏷️ ${cat}</span><span style="cursor:pointer;color:#F87171;font-weight:bold;" onclick="deleteCategory(${idx})">✕</span>`;

    tag.addEventListener("dragover", e => { e.preventDefault(); tag.style.background = "#2563EB"; });
    tag.addEventListener("dragleave", () => { tag.style.background = "#1F232B"; });
    tag.addEventListener("drop", e => {
      e.preventDefault();
      tag.style.background = "#1F232B";
      if (draggedItemId) moveItemToCategory(draggedItemId, cat);
    });

    tagsBox.appendChild(tag);
  });

  if (appState.categories.includes(curNewVal)) newCatSel.value = curNewVal;
  if (appState.categories.includes(curPropVal)) propCatSel.value = curPropVal;
}

function moveItemToCategory(itemId, targetCat) {
  const item = appState.items.find(i => i.id === itemId);
  if (!item) return;
  item.category = targetCat;
  expandedCategories.add(targetCat);
  draggedItemId = null;
  updateLeftItemPanel();
  renderRightPanel();
  const check = checkHumanWalkable(appState.human.x, appState.human.y);
  appState.human.z = check.baseZ;
  initHumanFormValues();
  if (renderer) updateThreeScene();
}

window.addCategory = function() {
  const inp = document.getElementById("new-cat-input");
  const val = inp.value.trim();
  if (!val) return;
  if (!appState.categories.includes(val)) {
    appState.categories.push(val);
    inp.value = "";
    renderCategoryUI();
    renderRightPanel();
  }
};

window.deleteCategory = function(idx) {
  if (appState.categories.length <= 1) {
    alert("至少需保留一個分類！");
    return;
  }
  const removed = appState.categories.splice(idx, 1)[0];
  const fallback = appState.categories[0];
  appState.items.forEach(it => { if (it.category === removed) it.category = fallback; });
  renderCategoryUI();
  renderRightPanel();
};

window.addEventListener("keydown", function(e) {
  const tag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
  if (tag === "input" || tag === "textarea" || tag === "select") return;

  if (e.key === "Delete" || e.key === "Backspace") {
    if (activeId && activeId !== "HUMAN") {
      e.preventDefault();
      deleteItemById(activeId);
    }
  }
  if (currentMode === "FPV" || currentMode === "3D") {
    if (e.key === "w" || e.key === "W" || e.key === "ArrowUp") { fpvMoveDir.forward = 1; walkTarget = null; }
    if (e.key === "s" || e.key === "S" || e.key === "ArrowDown") { fpvMoveDir.forward = -1; walkTarget = null; }
    if (e.key === "a" || e.key === "A" || e.key === "ArrowLeft") { fpvMoveDir.right = -1; walkTarget = null; }
    if (e.key === "d" || e.key === "D" || e.key === "ArrowRight") { fpvMoveDir.right = 1; walkTarget = null; }
  }
});

window.addEventListener("keyup", function(e) {
  if (["w","W","s","S","ArrowUp","ArrowDown"].includes(e.key)) fpvMoveDir.forward = 0;
  if (["a","A","d","D","ArrowLeft","ArrowRight"].includes(e.key)) fpvMoveDir.right = 0;
});

function bindDpadBtn(btnId, rightVal, forwardVal) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  const start = (e) => { e.preventDefault(); e.stopPropagation(); walkTarget = null; fpvMoveDir.right = rightVal; fpvMoveDir.forward = forwardVal; };
  const end = (e) => { e.preventDefault(); e.stopPropagation(); fpvMoveDir.right = 0; fpvMoveDir.forward = 0; };
  btn.addEventListener("pointerdown", start);
  btn.addEventListener("pointerup", end);
  btn.addEventListener("pointerleave", end);
  btn.addEventListener("pointercancel", end);
}

function initFabric() {
  const container = document.getElementById("canvas-container");
  canvas = new fabric.Canvas('fabric-canvas', {
    width: container.clientWidth,
    height: container.clientHeight,
    backgroundColor: '#0A0C10',
    selection: false,
    preserveObjectStacking: true
  });

  // 初始化所有預設物件的合法備份快照
  appState.items.forEach(it => saveValidItemBackup(it));

  bindDpadBtn("dpad-up", 0, 1);
  bindDpadBtn("dpad-down", 0, -1);
  bindDpadBtn("dpad-left", -1, 0);
  bindDpadBtn("dpad-right", 1, 0);

  document.getElementById("lock-scale-chk").addEventListener("change", e => {
    appState.room.lock_scale = e.target.checked;
    syncLockScaleUI();
    renderFullScene();
  });

  canvas.on('mouse:wheel', function(opt) {
    const delta = opt.e.deltaY;
    let zoom = canvas.getZoom() * (0.999 ** delta);
    zoom = Math.min(Math.max(zoom, 0.2), 5);
    canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
    opt.e.preventDefault();
    opt.e.stopPropagation();
  });

  canvas.on('mouse:down', function(opt) {
    const evt = opt.e;
    const target = opt.target;
    const isSelectable = target && (target.itemId || target.isHuman || (target.voidId && appState.room.editable));

    if (!isSelectable || forcePanMode || evt.button === 1 || evt.altKey) {
      isDraggingCanvas = true;
      const pt = (evt.touches && evt.touches[0]) ? evt.touches[0] : evt;
      lastClientX = pt.clientX;
      lastClientY = pt.clientY;
    }
  });

  canvas.on('mouse:move', function(opt) {
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
  });

  canvas.on('mouse:up', function() {
    isDraggingCanvas = false;
    const trashEl = document.getElementById("trash-dropzone");
    if (trashEl.classList.contains("show")) {
      if (isOverTrash && activeId && activeId !== "HUMAN") {
        deleteItemById(activeId);
      }
      trashEl.classList.remove("show", "hover");
      isOverTrash = false;
    }
  });

  const upperCanvas = canvas.upperCanvasEl;
  upperCanvas.addEventListener('touchstart', function(e) {
    if (e.touches.length === 2) {
      isDraggingCanvas = false;
      touchStartDist = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
      touchStartZoom = canvas.getZoom();
    }
  }, { passive: false });

  upperCanvas.addEventListener('touchmove', function(e) {
    if (e.touches.length === 2 && touchStartDist > 0) {
      e.preventDefault();
      const dist = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
      let newZoom = Math.min(Math.max(touchStartZoom * (dist / touchStartDist), 0.2), 4.5);
      const cx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
      const cy = (e.touches[0].clientY + e.touches[1].clientY) / 2;
      canvas.zoomToPoint({ x: cx, y: cy }, newZoom);
    }
  }, { passive: false });

  canvas.on('selection:created', onObjectSelected);
  canvas.on('selection:updated', onObjectSelected);
  canvas.on('selection:cleared', onObjectDeselected);
  canvas.on('object:moving', onObjectLiveMoving);
  canvas.on('object:scaling', onObjectLiveMoving);
  canvas.on('object:rotating', onObjectLiveMoving);
  canvas.on('object:modified', onObjectModifiedComplete);

  const initWalk = checkHumanWalkable(appState.human.x, appState.human.y);
  appState.human.z = initWalk.baseZ;

  renderCategoryUI();
  initRoomFormValues();
  initHumanFormValues();
  syncLockScaleUI();
  renderVoidListUI();
  renderFullScene();
  zoomToFit();
  initPanelResizers();
}

function renderFullScene() {
  if (!canvas) return;
  canvas.clear();
  canvas.backgroundColor = '#0A0C10';

  const rw = appState.room.width, rd = appState.room.depth;

  canvas.add(new fabric.Rect({
    left: 0, top: 0, width: rw, height: rd,
    fill: '#5089C6', stroke: '#38BDF8', strokeWidth: 2,
    selectable: false, evented: false
  }));

  canvas.add(new fabric.Text(`◀ 房間寬 ${rw} cm ▶`, {
    left: rw / 2, top: -24, fontSize: 13, fill: '#94A3B8', originX: 'center', selectable: false, evented: false
  }));
  canvas.add(new fabric.Text(`◀ 房間深 ${rd} cm ▶`, {
    left: -24, top: rd / 2, fontSize: 13, fill: '#94A3B8', originX: 'center', angle: -90, selectable: false, evented: false
  }));

  const canEditGround = !!appState.room.editable && !forcePanMode;
  appState.voids.forEach(v => {
    const vRect = new fabric.Rect({
      width: v.w, height: v.d, fill: '#FFFFFF',
      stroke: canEditGround ? '#2563EB' : '#CBD5E1',
      strokeWidth: canEditGround ? 2.5 : 1.5,
      strokeDashArray: canEditGround ? [5, 3] : null,
      originX: 'center', originY: 'center'
    });
    const vLabel = new fabric.Text(`${v.name}\n${Math.round(v.w)}×${Math.round(v.d)}`, {
      fontSize: 12, fill: '#334155', originX: 'center', originY: 'center', textAlign: 'center'
    });
    const vGroup = new fabric.Group([vRect, vLabel], {
      left: v.x + v.w / 2, top: v.y + v.d / 2,
      originX: 'center', originY: 'center',
      selectable: canEditGround, evented: canEditGround, voidId: v.id
    });
    vGroup.setControlsVisibility({ mtr: false });
    canvas.add(vGroup);
  });

  appState.items.forEach(item => createFabricItem(item));

  if (appState.compass.show_feixing) renderNinePalaceFeixing();
  if (appState.compass.show) renderExpertCompass();

  createFabricHuman();

  if (activeId === "HUMAN") {
    const hg = canvas.getObjects().find(o => o.isHuman);
    if (hg && !forcePanMode) canvas.setActiveObject(hg);
  } else if (activeId) {
    const g = canvas.getObjects().find(o => o.itemId === activeId);
    if (g && !forcePanMode) canvas.setActiveObject(g);
  }

  renderRightPanel();
  canvas.requestRenderAll();
  if ((currentMode === "3D" || currentMode === "FPV") && renderer) updateThreeScene();
}

function createFabricHuman() {
  const h = appState.human;
  const fovCone = new fabric.Polygon([
    { x: 0, y: 0 }, { x: -32, y: -65 }, { x: 32, y: -65 }
  ], {
    fill: 'rgba(168, 85, 247, 0.32)', stroke: '#C084FC', strokeWidth: 1.5,
    originX: 'center', originY: 'bottom', top: 0
  });

  const postureColor = h.posture === 'lie' ? '#EC4899' : (h.posture === 'sit' ? '#0EA5E9' : '#9333EA');
  const postureIcon = h.posture === 'lie' ? "🛏️" : (h.posture === 'sit' ? "🪑" : "🧍");

  const bodyCircle = new fabric.Circle({
    radius: 14, fill: postureColor, stroke: '#FFFFFF', strokeWidth: 2.5,
    originX: 'center', originY: 'center'
  });

  const iconTxt = new fabric.Text(postureIcon, {
    fontSize: 14, originX: 'center', originY: 'center'
  });

  const humanGroup = new fabric.Group([fovCone, bodyCircle, iconTxt], {
    left: h.x, top: h.y, angle: h.rot || 0,
    originX: 'center', originY: 'center',
    selectable: !forcePanMode, evented: !forcePanMode,
    isHuman: true
  });

  humanGroup.setControlsVisibility({
    mt: false, mb: false, ml: false, mr: false,
    tl: false, tr: false, bl: false, br: false,
    mtr: true
  });

  canvas.add(humanGroup);
}

function createFabricItem(item) {
  const subElements = [];
  const rect = new fabric.Rect({
    width: item.w, height: item.d,
    fill: item.color, stroke: '#1E293B', strokeWidth: 1.5,
    originX: 'center', originY: 'center'
  });
  subElements.push(rect);

  if (item.item_type === "door") {
    const fx = item.flip_x ? -1 : 1;
    const fy = item.flip_y ? -1 : 1;
    const hx = -item.w / 2 * fx;
    const hy = item.d / 2 * fy;
    const openX = hx;
    const openY = hy + item.w * fy;
    const closedX = item.w / 2 * fx;
    const closedY = hy;
    const sweep = (fx * fy > 0) ? 0 : 1;

    const arcPath = new fabric.Path(`M ${hx} ${hy} L ${openX} ${openY} A ${item.w} ${item.w} 0 0 ${sweep} ${closedX} ${closedY}`, {
      fill: 'rgba(251, 146, 60, 0.18)', stroke: '#FDBA74', strokeWidth: 1.5, strokeDashArray: [4, 3]
    });
    subElements.push(arcPath);
  }

  const labelStr = `${item.name}\n${Math.round(item.w)}×${Math.round(item.d)}`;
  const fontSize = Math.max(9, Math.min(12, Math.min(item.w, item.d) * 0.45));
  const text = new fabric.Text(labelStr, {
    fontSize: fontSize, fill: '#FFFFFF',
    originX: 'center', originY: 'center', textAlign: 'center'
  });
  subElements.push(text);

  const lockS = !!appState.room.lock_scale;
  const group = new fabric.Group(subElements, {
    left: item.x + item.w / 2, top: item.y + item.d / 2,
    angle: item.rot || 0, originX: 'center', originY: 'center',
    lockScalingX: lockS, lockScalingY: lockS,
    selectable: !forcePanMode, evented: !forcePanMode, itemId: item.id
  });

  group.setControlsVisibility({
    mt: !lockS, mb: !lockS, ml: !lockS, mr: !lockS,
    tl: !lockS, tr: !lockS, bl: !lockS, br: !lockS,
    mtr: true
  });

  if (item.texture && item.item_type !== "window") {
    fabric.Image.fromURL(item.texture, function(img) {
      img.scaleToWidth(item.w);
      img.scaleToHeight(item.d);
      rect.set('fill', new fabric.Pattern({ source: img.getElement(), repeat: 'repeat' }));
      canvas.requestRenderAll();
    });
  }

  canvas.add(group);
}

function renderNinePalaceFeixing() {
  const rw = appState.room.width, rd = appState.room.depth;
  const cw = rw / 3, cd = rd / 3;
  const year = parseInt(appState.compass.feixing_year) || 2026;
  const centerStar = getCenterStarByYear(year);

  const infoEl = document.getElementById("feixing-center-info");
  if (infoEl) infoEl.innerText = `${year}年: ${FEIXING_META[centerStar].name}入中宮`;

  const rot = appState.compass.rotation || 0;
  const dirAngles = [
    { key: "W", deg: 0, label: "正西" }, { key: "NW", deg: 45, label: "西北" },
    { key: "N", deg: 90, label: "正北" }, { key: "NE", deg: 135, label: "東北" },
    { key: "E", deg: 180, label: "正東" }, { key: "SE", deg: 225, label: "東南" },
    { key: "S", deg: 270, label: "正南" }, { key: "SW", deg: 315, label: "西南" }
  ];

  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 3; col++) {
      const gx = col * cw, gy = row * cd;
      let dirKey = "C", dirLabel = "中宮";
      if (!(row === 1 && col === 1)) {
        let cellDeg = Math.atan2(row - 1, col - 1) * 180 / Math.PI;
        if (cellDeg < 0) cellDeg += 360;
        let relDeg = (cellDeg - rot) % 360;
        if (relDeg < 0) relDeg += 360;
        const idx = Math.round(relDeg / 45) % 8;
        dirKey = dirAngles[idx].key;
        dirLabel = dirAngles[idx].label;
      }
      const starNum = getStarAtDir(centerStar, dirKey);
      const meta = FEIXING_META[starNum];

      canvas.add(new fabric.Rect({
        left: gx, top: gy, width: cw, height: cd,
        fill: meta.bg, stroke: '#F59E0B', strokeWidth: 1.5, strokeDashArray: [6, 4],
        selectable: false, evented: false
      }));
      canvas.add(new fabric.Text(`【${dirLabel}】${meta.name} (${meta.el})`, {
        left: gx + cw / 2, top: gy + 18, fontSize: 13, fontWeight: 'bold', fill: meta.color,
        backgroundColor: 'rgba(10, 12, 16, 0.82)', originX: 'center', originY: 'center', selectable: false, evented: false
      }));
      canvas.add(new fabric.Text(`${meta.luck}\n${meta.tip}`, {
        left: gx + cw / 2, top: gy + 42, fontSize: 11, fill: '#F8FAFC',
        backgroundColor: 'rgba(15, 23, 42, 0.78)', originX: 'center', originY: 'center', textAlign: 'center', selectable: false, evented: false
      }));
    }
  }
}

function renderExpertCompass() {
  const cx = appState.compass.x, cy = appState.compass.y;
  const rot = appState.compass.rotation || 0;
  const radius = Math.max(appState.room.width, appState.room.depth) * 0.72;

  [radius * 0.25, radius * 0.5, radius * 0.75, radius].forEach((r, idx) => {
    canvas.add(new fabric.Circle({
      left: cx - r, top: cy - r, radius: r, fill: 'transparent',
      stroke: idx === 3 ? 'rgba(255, 255, 255, 0.45)' : 'rgba(255, 255, 255, 0.16)',
      strokeWidth: idx === 3 ? 1.8 : 1, strokeDashArray: idx % 2 === 1 ? [5, 5] : null,
      selectable: false, evented: false
    }));
  });

  const directions = [
    { deg: 0, label: "正西 [兌]", primary: true }, { deg: 45, label: "西北 [乾]", primary: false },
    { deg: 90, label: "正北 [坎]", primary: true }, { deg: 135, label: "東北 [艮]", primary: false },
    { deg: 180, label: "正東 [震]", primary: true }, { deg: 225, label: "東南 [巽]", primary: false },
    { deg: 270, label: "正南 [離]", primary: true }, { deg: 315, label: "西南 [坤]", primary: false }
  ];

  directions.forEach(dir => {
    const rad = (dir.deg + rot) * Math.PI / 180;
    canvas.add(new fabric.Line([cx, cy, cx + radius * Math.cos(rad), cy + radius * Math.sin(rad)], {
      stroke: dir.primary ? 'rgba(255, 255, 255, 0.8)' : 'rgba(255, 255, 255, 0.35)',
      strokeWidth: dir.primary ? 2.2 : 1.2, selectable: false, evented: false
    }));
    canvas.add(new fabric.Text(dir.label, {
      left: cx + (radius + 24) * Math.cos(rad), top: cy + (radius + 24) * Math.sin(rad),
      fontSize: dir.primary ? 14 : 11, fontWeight: dir.primary ? 'bold' : 'normal',
      fill: dir.primary ? '#F3E8FF' : '#CBD5E1',
      backgroundColor: dir.primary ? 'rgba(107, 33, 168, 0.78)' : 'rgba(15, 23, 42, 0.68)',
      originX: 'center', originY: 'center', selectable: false, evented: false
    }));
  });
}

function onObjectSelected(e) {
  const target = e.selected ? e.selected[0] : null;
  if (!target) return;
  if (target.isHuman) {
    activeId = "HUMAN";
    switchLeftTab('human');
    initHumanFormValues();
    highlightRightPanel();
  } else if (target.itemId) {
    activeId = target.itemId;
    switchLeftTab('item');
    updateLeftItemPanel();
    highlightRightPanel();
  } else if (target.voidId) {
    switchLeftTab('room');
  }
}

function onObjectDeselected() {
  activeId = null;
  document.getElementById("no-selection").style.display = "block";
  document.getElementById("prop-editor").style.display = "none";
  highlightRightPanel();
}

function onObjectLiveMoving(e) {
  const target = e.target;
  if (!target) return;

  if (target.itemId && e.e) {
    const trashEl = document.getElementById("trash-dropzone");
    trashEl.classList.add("show");
    const pt = (e.e.touches && e.e.touches[0]) ? e.e.touches[0] : e.e;
    const rect = trashEl.getBoundingClientRect();
    isOverTrash = (pt.clientX >= rect.left - 20 && pt.clientX <= rect.right + 20 && pt.clientY >= rect.top - 20 && pt.clientY <= rect.bottom + 20);
    trashEl.classList.toggle("hover", isOverTrash);
  }

  if (target.isHuman) {
    const nx = Math.round(target.left);
    const ny = Math.round(target.top);
    const check = checkHumanWalkable(nx, ny);
    if (check.allowed) {
      appState.human.x = nx;
      appState.human.y = ny;
      appState.human.z = check.baseZ;
    } else {
      target.set({ left: appState.human.x, top: appState.human.y });
      showToast("⚠️ 人物不可穿越家具物件！");
    }
    appState.human.rot = Math.round((target.angle % 360 + 360) % 360);
    initHumanFormValues();
  } else if (target.itemId) {
    const item = appState.items.find(i => i.id === target.itemId);
    if (!item) return;

    if (target.flipX) {
      item.flip_x = !item.flip_x;
      target.set('flipX', false);
    }
    if (target.flipY) {
      item.flip_y = !item.flip_y;
      target.set('flipY', false);
    }

    const baseRect = target.item(0);
    if (!appState.room.lock_scale) {
      item.w = Math.max(4, Math.round(baseRect.width * Math.abs(target.scaleX)));
      item.d = Math.max(4, Math.round(baseRect.height * Math.abs(target.scaleY)));
    }
    item.rot = Math.round((target.angle % 360 + 360) % 360);
    item.x = Math.round(target.left - item.w / 2);
    item.y = Math.round(target.top - item.d / 2);
    updateLeftItemPanel();
  } else if (target.voidId) {
    const v = appState.voids.find(x => x.id === target.voidId);
    if (!v) return;
    const baseRect = target.item(0);
    v.w = Math.max(10, Math.round(baseRect.width * Math.abs(target.scaleX)));
    v.d = Math.max(10, Math.round(baseRect.height * Math.abs(target.scaleY)));
    v.x = Math.round(target.left - v.w / 2);
    v.y = Math.round(target.top - v.d / 2);
    renderVoidListUI();
  }
}

function onObjectModifiedComplete(e) {
  const trashEl = document.getElementById("trash-dropzone");
  if (isOverTrash && activeId && activeId !== "HUMAN") {
    trashEl.classList.remove("show", "hover");
    isOverTrash = false;
    deleteItemById(activeId);
    return;
  }
  trashEl.classList.remove("show", "hover");
  isOverTrash = false;
  onObjectLiveMoving(e);

  if (e.target && e.target.itemId) {
    const item = appState.items.find(i => i.id === e.target.itemId);
    if (item) {
      enforceItemConstraints(item, true);
      updateLeftItemPanel();
    }
  }
  renderFullScene();
}

function setInputValueSafe(id, val) {
  const el = document.getElementById(id);
  if (el && document.activeElement !== el) {
    el.value = val;
  }
}

function updateLeftItemPanel() {
  const item = appState.items.find(i => i.id === activeId);
  if (!item) return;

  document.getElementById("no-selection").style.display = "none";
  document.getElementById("prop-editor").style.display = "block";

  const typeNames = {
    furniture: "🛋️ 家具 / 床 (貼地)",
    wall_item: "🖼️ 牆壁上物品 (貼牆可調Z)",
    door: "🚪 房門 (貼牆貼地)",
    window: "🪟 窗戶 (貼牆外突)",
    socket: "🔌 插座 (貼牆外突)",
    switch: "💡 開關 (貼牆外突)"
  };
  const t = item.item_type || "furniture";
  document.getElementById("prop-type-badge").innerText = typeNames[t] || typeNames.furniture;

  setInputValueSafe("prop-name", item.name);
  setInputValueSafe("prop-category", item.category || appState.categories[0]);
  setInputValueSafe("prop-type", t);
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

  // 鎖定縮放時，寬深高欄位設為唯讀
  const lockS = !!appState.room.lock_scale;
  document.getElementById("prop-w").disabled = lockS;
  document.getElementById("prop-d").disabled = lockS;
  document.getElementById("prop-h").disabled = lockS;

  // 只有窗戶/開關/插座/牆壁上物品可調整 Z 軸離地高度，其餘隱藏或鎖定 Z=0
  const canZ = isZAdjustableWallType(t);
  document.getElementById("prop-z-row").style.display = canZ ? "flex" : "none";
  document.getElementById("prop-z-hint").style.display = canZ ? "inline" : "none";

  document.getElementById("door-swing-group").style.display = (t === "door") ? "flex" : "none";
  document.getElementById("scenery-upload-group").style.display = (t === "window") ? "flex" : "none";
}

function updateSingleItemVisual(item) {
  enforceItemConstraints(item, true);
  updateLeftItemPanel();
  renderFullScene();
}

["prop-name", "prop-category", "prop-type", "prop-w", "prop-d", "prop-h", "prop-x", "prop-y", "prop-z", "prop-rot", "prop-color"].forEach(id => {
  document.getElementById(id).addEventListener("input", (e) => {
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;

    const rawVal = e.target.value;
    if (id === "prop-name") item.name = rawVal;
    else if (id === "prop-category") {
      item.category = rawVal;
      expandedCategories.add(rawVal);
    } else if (id === "prop-type") {
      item.item_type = rawVal;
      if (rawVal === "window" && !item.scenery) item.scenery = appState.default_fuji;
      if (!isZAdjustableWallType(rawVal)) item.z = 0;
      enforceItemConstraints(item, true);
      updateLeftItemPanel();
      renderFullScene();
      return;
    } else if (id === "prop-color") {
      item.color = rawVal;
    } else {
      if (rawVal === "" || rawVal === "-") return;
      const num = parseFloat(rawVal);
      if (isNaN(num)) return;
      if (id === "prop-w" && !appState.room.lock_scale) item.w = Math.max(1, num);
      if (id === "prop-d" && !appState.room.lock_scale) item.d = Math.max(1, num);
      if (id === "prop-h" && !appState.room.lock_scale) item.h = Math.max(1, Math.min(appState.room.height, num));
      if (id === "prop-x") item.x = num;
      if (id === "prop-y") item.y = num;
      if (id === "prop-z" && isZAdjustableWallType(item.item_type)) item.z = Math.max(0, num);
      if (id === "prop-rot") {
        item.rot = ((num % 360) + 360) % 360;
        document.getElementById("prop-rot-slider").value = item.rot;
        document.getElementById("prop-rot-val").innerText = Math.round(item.rot) + "°";
      }
    }
    updateSingleItemVisual(item);
  });
});

document.getElementById("prop-rot-slider").addEventListener("input", e => {
  const item = appState.items.find(i => i.id === activeId);
  if (!item) return;
  item.rot = parseFloat(e.target.value) || 0;
  document.getElementById("prop-rot").value = item.rot;
  document.getElementById("prop-rot-val").innerText = item.rot + "°";
  updateSingleItemVisual(item);
});

document.getElementById("btn-door-flip-x").addEventListener("click", () => {
  const item = appState.items.find(i => i.id === activeId);
  if (!item) return;
  item.flip_x = !item.flip_x;
  renderFullScene();
});
document.getElementById("btn-door-flip-y").addEventListener("click", () => {
  const item = appState.items.find(i => i.id === activeId);
  if (!item) return;
  item.flip_y = !item.flip_y;
  renderFullScene();
});

document.getElementById("prop-scenery-file").addEventListener("change", function(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(f) {
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.scenery = f.target.result;
    if (renderer) updateThreeScene();
  };
  reader.readAsDataURL(file);
});
document.getElementById("btn-reset-fuji").addEventListener("click", () => {
  const item = appState.items.find(i => i.id === activeId);
  if (!item) return;
  item.scenery = appState.default_fuji;
  if (renderer) updateThreeScene();
});
document.getElementById("prop-texture-file").addEventListener("change", function(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(f) {
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.texture = f.target.result;
    renderFullScene();
  };
  reader.readAsDataURL(file);
});
document.getElementById("btn-clear-texture").addEventListener("click", () => {
  const item = appState.items.find(i => i.id === activeId);
  if (!item) return;
  item.texture = "";
  renderFullScene();
});

window.onNewObjTypeChange = function() {
  const t = document.getElementById("new-obj-type").value;
  const cat = document.getElementById("new-obj-category").value;
  const nameEl = document.getElementById("new-obj-name");
  const wEl = document.getElementById("new-obj-w");
  const dEl = document.getElementById("new-obj-d");
  const hEl = document.getElementById("new-obj-h");
  const zEl = document.getElementById("new-obj-z");
  const zRow = document.getElementById("new-obj-z-row");

  zRow.style.display = isZAdjustableWallType(t) ? "flex" : "none";

  if (t === "window") {
    nameEl.value = "窗戶"; wEl.value = 120; dEl.value = 12; hEl.value = 130; zEl.value = 85;
  } else if (t === "socket") {
    nameEl.value = "插座"; wEl.value = 22; dEl.value = 12; hEl.value = 14; zEl.value = 30;
  } else if (t === "switch") {
    nameEl.value = "開關"; wEl.value = 22; dEl.value = 12; hEl.value = 14; zEl.value = 110;
  } else if (t === "wall_item") {
    nameEl.value = "壁掛冷氣/掛畫"; wEl.value = 85; dEl.value = 18; hEl.value = 30; zEl.value = 210;
  } else if (t === "door") {
    nameEl.value = "房門"; wEl.value = 90; dEl.value = 14; hEl.value = 210; zEl.value = 0;
  } else {
    if (cat === "床") {
      nameEl.value = "雙人床"; wEl.value = 152; dEl.value = 195; hEl.value = 55; zEl.value = 0;
    } else {
      nameEl.value = "新家具"; wEl.value = 60; dEl.value = 50; hEl.value = 30; zEl.value = 0;
    }
  }
};

window.confirmAddNewObject = function() {
  const chosenCat = document.getElementById("new-obj-category").value || appState.categories[0];
  const type = document.getElementById("new-obj-type").value || "furniture";
  const name = document.getElementById("new-obj-name").value.trim() || "新物件";
  const w = Math.max(4, parseFloat(document.getElementById("new-obj-w").value) || 60);
  const d = Math.max(4, parseFloat(document.getElementById("new-obj-d").value) || 50);
  const h = Math.max(4, Math.min(appState.room.height, parseFloat(document.getElementById("new-obj-h").value) || 30));
  const z = isZAdjustableWallType(type) ? Math.max(0, parseFloat(document.getElementById("new-obj-z").value) || 0) : 0;

  const colorMap = { window: "#F59E0B", socket: "#F97316", switch: "#0EA5E9", wall_item: "#10B981", door: "#8B5A2B", furniture: chosenCat === "床" ? "#FAD785" : "#38BDF8" };
  const newItem = {
    id: "item_" + Date.now(),
    name: name,
    category: chosenCat,
    item_type: type,
    x: 130, y: ["window", "socket", "switch", "wall_item", "door"].includes(type) ? appState.room.depth : 210, z: z,
    w: w, d: d, h: h, rot: 0,
    color: colorMap[type] || "#38BDF8",
    texture: "",
    scenery: type === "window" ? appState.default_fuji : "",
    flip_x: false, flip_y: false
  };
  expandedCategories.add(chosenCat);
  findNonOverlappingSpot(newItem);
  appState.items.push(newItem);
  activeId = newItem.id;
  renderFullScene();
  selectItemById(newItem.id);
};

window.clearWallTexture = function() {
  appState.room.wall_texture = "";
  document.getElementById("wall-texture-file").value = "";
  renderFullScene();
  if (renderer) updateThreeScene();
};

window.clearCeilTexture = function() {
  appState.room.ceiling_texture = "";
  document.getElementById("ceil-texture-file").value = "";
  renderFullScene();
  if (renderer) updateThreeScene();
};

window.deleteSelectedActive = function() {
  if (activeId && activeId !== "HUMAN") deleteItemById(activeId);
};

function deleteItemById(id, evt) {
  if (evt) evt.stopPropagation();
  appState.items = appState.items.filter(i => i.id !== id);
  delete lastValidItemMap[id];
  if (activeId === id) {
    activeId = null;
    if (transformControl) transformControl.detach();
    onObjectDeselected();
  }
  renderFullScene();
}

document.getElementById("btn-delete").addEventListener("click", () => {
  if (activeId && activeId !== "HUMAN") deleteItemById(activeId);
});

document.getElementById("btn-duplicate").addEventListener("click", () => {
  const item = appState.items.find(i => i.id === activeId);
  if (!item) return;
  const copy = JSON.parse(JSON.stringify(item));
  copy.id = "item_" + Date.now();
  copy.name = item.name + "(複本)";
  copy.x += 25; copy.y += 25;
  findNonOverlappingSpot(copy);
  appState.items.push(copy);
  activeId = copy.id;
  renderFullScene();
  selectItemById(copy.id);
});

document.getElementById("room-editable-lock").addEventListener("change", function(e) {
  appState.room.editable = e.target.checked;
  renderVoidListUI();
  renderFullScene();
});

function renderVoidListUI() {
  const container = document.getElementById("void-list-container");
  container.innerHTML = "";
  const disabledAttr = appState.room.editable ? "" : "disabled";

  appState.voids.forEach((v, idx) => {
    const card = document.createElement("div");
    card.style.cssText = "background:#1F232B; border:1px solid #334155; border-radius:6px; padding:7px; margin-bottom:5px; display:flex; flex-direction:column; gap:5px;";
    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; gap:4px;">
        <input type="text" value="${v.name}" ${disabledAttr} oninput="updateVoidField(${idx}, 'name', this.value)" style="font-weight:600;">
        <button class="danger" ${disabledAttr} onclick="deleteVoidArea(${idx})" style="padding:3px 6px; font-size:11px; flex-shrink:0;">🗑️</button>
      </div>
      <div class="field-row">
        <div><span style="font-size:10px;color:#94A3B8;">寬 W</span><input type="number" value="${Math.round(v.w)}" ${disabledAttr} oninput="updateVoidField(${idx}, 'w', this.value)"></div>
        <div><span style="font-size:10px;color:#94A3B8;">深 D</span><input type="number" value="${Math.round(v.d)}" ${disabledAttr} oninput="updateVoidField(${idx}, 'd', this.value)"></div>
        <div><span style="font-size:10px;color:#94A3B8;">X 坐標</span><input type="number" value="${Math.round(v.x)}" ${disabledAttr} oninput="updateVoidField(${idx}, 'x', this.value)"></div>
        <div><span style="font-size:10px;color:#94A3B8;">Y 坐標</span><input type="number" value="${Math.round(v.y)}" ${disabledAttr} oninput="updateVoidField(${idx}, 'y', this.value)"></div>
      </div>
    `;
    container.appendChild(card);
  });
}

window.updateVoidField = function(idx, field, val) {
  if (!appState.voids[idx]) return;
  if (field === 'name') appState.voids[idx].name = val;
  else {
    if (val === "" || val === "-") return;
    appState.voids[idx][field] = parseFloat(val) || 0;
  }
  renderFullScene();
};

window.addVoidArea = function() {
  if (!appState.room.editable) {
    alert("💡 請先勾選上方「🔓 勾選才可拖曳/改動留白處」！");
    return;
  }
  appState.voids.push({ id: "void_" + Date.now(), name: `留白處 ${appState.voids.length + 1}`, x: 50, y: 50, w: 80, d: 80 });
  renderVoidListUI();
  renderFullScene();
};

window.deleteVoidArea = function(idx) {
  appState.voids.splice(idx, 1);
  renderVoidListUI();
  renderFullScene();
};

function initRoomFormValues() {
  document.getElementById("room-editable-lock").checked = !!appState.room.editable;
  setInputValueSafe("room-w", appState.room.width);
  setInputValueSafe("room-d", appState.room.depth);
  setInputValueSafe("room-h", appState.room.height);
  document.getElementById("room-show-walls").checked = !!appState.room.show_walls;
  document.getElementById("room-show-ceiling").checked = !!appState.room.show_ceiling;
  setInputValueSafe("room-wall-color", appState.room.wall_color || "#F8FAFC");
  setInputValueSafe("room-ceil-color", appState.room.ceiling_color || "#FFFFFF");

  document.getElementById("compass-show").checked = appState.compass.show;
  document.getElementById("compass-auto-center").checked = !!appState.compass.auto_center;
  setInputValueSafe("compass-x", appState.compass.x);
  setInputValueSafe("compass-y", appState.compass.y);
  setInputValueSafe("compass-rot", appState.compass.rotation || 0);
  setInputValueSafe("compass-rot-slider", appState.compass.rotation || 0);
  document.getElementById("compass-rot-val").innerText = (appState.compass.rotation || 0) + "°";

  document.getElementById("feixing-show").checked = !!appState.compass.show_feixing;
  setInputValueSafe("feixing-year", appState.compass.feixing_year || 2026);
}

function syncRoomFromInputs(e) {
  if (e && (e.target.value === "" || e.target.value === "-")) return;
  const targetId = e ? e.target.id : "";

  appState.room.width = parseFloat(document.getElementById("room-w").value) || 400;
  appState.room.depth = parseFloat(document.getElementById("room-d").value) || 300;
  appState.room.height = parseFloat(document.getElementById("room-h").value) || 280;
  appState.room.show_walls = document.getElementById("room-show-walls").checked;
  appState.room.show_ceiling = document.getElementById("room-show-ceiling").checked;
  appState.room.wall_color = document.getElementById("room-wall-color").value;
  appState.room.ceiling_color = document.getElementById("room-ceil-color").value;

  appState.compass.show = document.getElementById("compass-show").checked;
  appState.compass.auto_center = document.getElementById("compass-auto-center").checked;

  // 若使用者手動改了 compass-x 或 compass-y，取消自動置中；否則只要地基改變或勾選自動置中，自動設為 (width/2, depth/2)
  if (targetId === "compass-x" || targetId === "compass-y") {
    appState.compass.auto_center = false;
    document.getElementById("compass-auto-center").checked = false;
    appState.compass.x = parseFloat(document.getElementById("compass-x").value) || 200;
    appState.compass.y = parseFloat(document.getElementById("compass-y").value) || 150;
  } else if (appState.compass.auto_center || targetId === "room-w" || targetId === "room-d") {
    appState.compass.x = Math.round(appState.room.width / 2);
    appState.compass.y = Math.round(appState.room.depth / 2);
    setInputValueSafe("compass-x", appState.compass.x);
    setInputValueSafe("compass-y", appState.compass.y);
  }

  appState.compass.rotation = parseFloat(document.getElementById("compass-rot").value) || 0;
  setInputValueSafe("compass-rot-slider", appState.compass.rotation);
  document.getElementById("compass-rot-val").innerText = appState.compass.rotation + "°";

  appState.compass.show_feixing = document.getElementById("feixing-show").checked;
  appState.compass.feixing_year = parseInt(document.getElementById("feixing-year").value) || 2026;

  // 地基改變時，重新校正牆上物品吸附位置與高度防穿模
  appState.items.forEach(it => enforceItemConstraints(it, false));
  renderFullScene();
}

document.querySelectorAll(".live-room-input").forEach(el => {
  el.addEventListener("input", syncRoomFromInputs);
});
document.getElementById("compass-rot-slider").addEventListener("input", e => {
  document.getElementById("compass-rot").value = e.target.value;
  syncRoomFromInputs();
});

document.getElementById("wall-texture-file").addEventListener("change", function(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(f) {
    appState.room.wall_texture = f.target.result;
    if (renderer) updateThreeScene();
  };
  reader.readAsDataURL(file);
});
document.getElementById("ceil-texture-file").addEventListener("change", function(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(f) {
    appState.room.ceiling_texture = f.target.result;
    appState.room.show_ceiling = true;
    document.getElementById("room-show-ceiling").checked = true;
    if (renderer) updateThreeScene();
  };
  reader.readAsDataURL(file);
});

// 第一人稱「僅水平轉動」切換
window.toggleLockHorizFPV = function() {
  appState.human.lock_horizontal = !appState.human.lock_horizontal;
  if (appState.human.lock_horizontal) {
    appState.human.pitch = 0;
  }
  initHumanFormValues();
  if (currentMode === "FPV") syncFPVCamera();
};

document.getElementById("human-lock-horiz").addEventListener("change", e => {
  appState.human.lock_horizontal = e.target.checked;
  if (appState.human.lock_horizontal) {
    appState.human.pitch = 0;
  }
  initHumanFormValues();
  if (currentMode === "FPV") syncFPVCamera();
});

function initHumanFormValues() {
  const h = appState.human;
  const eyeH = getHumanEyeHeight();
  const lockH = !!h.lock_horizontal;

  document.getElementById("human-lock-horiz").checked = lockH;
  const hudLockBtn = document.getElementById("hud-btn-lock-h");
  if (hudLockBtn) {
    hudLockBtn.innerText = lockH ? "🔒 僅水平" : "🔓 自由視角";
    hudLockBtn.classList.toggle("active", lockH);
  }
  document.getElementById("human-pitch-slider").disabled = lockH;
  document.getElementById("human-pitch").disabled = lockH;
  document.getElementById("hud-pitch-slider").disabled = lockH;

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

  document.getElementById("human-eye-info").innerText = `眼高: ${eyeH} cm`;
  document.getElementById("human-basez-info").innerText = `踏面Z: ${Math.round(h.z || 0)} cm ${h.z > 0 ? '(床上)' : ''}`;
  const hudEyeLbl = document.getElementById("hud-eye-height-lbl");
  if (hudEyeLbl) hudEyeLbl.innerText = `目前眼高: ${eyeH} cm (踏面Z:${Math.round(h.z || 0)})`;

  const p = h.posture || "stand";
  ["stand", "sit", "lie"].forEach(mode => {
    const b1 = document.getElementById("btn-posture-" + mode);
    const b2 = document.getElementById("hud-btn-" + mode);
    if (b1) b1.classList.toggle("active", p === mode);
    if (b2) b2.classList.toggle("active", p === mode);
  });
}

["human-height", "human-x", "human-y", "human-rot", "human-pitch"].forEach(id => {
  document.getElementById(id).addEventListener("input", e => {
    if (e.target.value === "" || e.target.value === "-") return;
    const val = parseFloat(e.target.value) || 0;
    if (id === "human-height") appState.human.height = Math.max(60, val);
    if (id === "human-x") tryMoveHumanTo(val, appState.human.y, true);
    if (id === "human-y") tryMoveHumanTo(appState.human.x, val, true);
    if (id === "human-rot") appState.human.rot = ((val % 360) + 360) % 360;
    if (id === "human-pitch" && !appState.human.lock_horizontal) appState.human.pitch = Math.max(-85, Math.min(85, val));
    initHumanFormValues();
    renderFullScene();
    if (currentMode === "FPV") syncFPVCamera();
  });
});

document.getElementById("human-rot-slider").addEventListener("input", e => {
  appState.human.rot = parseFloat(e.target.value) || 0;
  initHumanFormValues();
  renderFullScene();
  if (currentMode === "FPV") syncFPVCamera();
});

document.getElementById("human-pitch-slider").addEventListener("input", e => {
  if (appState.human.lock_horizontal) return;
  appState.human.pitch = parseFloat(e.target.value) || 0;
  initHumanFormValues();
  if (currentMode === "FPV") syncFPVCamera();
});

document.getElementById("hud-pitch-slider").addEventListener("input", e => {
  if (appState.human.lock_horizontal) return;
  appState.human.pitch = parseFloat(e.target.value) || 0;
  initHumanFormValues();
  if (currentMode === "FPV") syncFPVCamera();
});

window.setHumanPosture = function(p) {
  appState.human.posture = p;
  if (!appState.human.lock_horizontal) {
    if (p === "lie") {
      appState.human.pitch = 35;
      appState.room.show_ceiling = true;
      document.getElementById("room-show-ceiling").checked = true;
    } else if (p === "sit") {
      appState.human.pitch = -5;
    } else {
      appState.human.pitch = 0;
    }
  }
  const check = checkHumanWalkable(appState.human.x, appState.human.y);
  appState.human.z = check.baseZ;
  initHumanFormValues();
  renderFullScene();
  if (currentMode === "FPV") syncFPVCamera();
};

window.placeHumanOnBed = function(targetPosture = 'lie') {
  const bed = appState.items.find(i => isBedItem(i));
  if (bed) {
    appState.human.x = Math.round(bed.x + bed.w / 2);
    appState.human.y = Math.round(bed.y + (targetPosture === 'sit' ? bed.d * 0.78 : bed.d * 0.35));
    appState.human.z = (bed.z || 0) + (bed.h || 55);
    appState.human.rot = 180;
  }
  setHumanPosture(targetPosture);
  enterHumanFPV();
};

function renderRightPanel() {
  const container = document.getElementById("item-list-container");
  document.getElementById("obj-count").innerText = `共 ${appState.items.length} 項`;
  container.innerHTML = "";

  const badgeMap = {
    furniture: { text: "家具", cls: "" },
    wall_item: { text: "🖼️ 牆物", cls: "win" },
    door: { text: "🚪 門", cls: "door" },
    window: { text: "🪟 窗", cls: "win" },
    socket: { text: "🔌 插座", cls: "win" },
    switch: { text: "💡 開關", cls: "win" }
  };

  appState.categories.forEach(cat => {
    const catItems = appState.items.filter(it => (it.category || appState.categories[0]) === cat);
    const sec = document.createElement("div");
    sec.className = "cat-section";
    sec.setAttribute("data-cat", cat);

    sec.addEventListener("dragover", e => {
      e.preventDefault();
      sec.classList.add("drag-over");
    });
    sec.addEventListener("dragleave", () => sec.classList.remove("drag-over"));
    sec.addEventListener("drop", e => {
      e.preventDefault();
      sec.classList.remove("drag-over");
      if (draggedItemId) moveItemToCategory(draggedItemId, cat);
    });

    const isExpanded = expandedCategories.has(cat);
    const header = document.createElement("div");
    header.className = "cat-header";
    header.innerHTML = `<span>${isExpanded ? '📂' : '📁'} ${cat} ${cat === '床' ? '🛏️' : ''}</span><span style="font-size:11px;color:#64748B;">${catItems.length} 項 ${isExpanded ? '▾' : '▸'}</span>`;

    const listBox = document.createElement("div");
    listBox.className = "cat-items";
    listBox.style.display = isExpanded ? "flex" : "none";

    header.onclick = () => {
      if (expandedCategories.has(cat)) expandedCategories.delete(cat);
      else expandedCategories.add(cat);
      renderRightPanel();
    };

    catItems.forEach(item => {
      const card = document.createElement("div");
      card.className = "item-card" + (item.id === activeId ? " selected" : "");
      card.draggable = true;
      card.onclick = () => selectItemById(item.id);

      card.addEventListener("dragstart", e => {
        draggedItemId = item.id;
        card.classList.add("dragging");
        e.dataTransfer.setData("text/plain", item.id);
      });
      card.addEventListener("dragend", () => {
        card.classList.remove("dragging");
        draggedItemId = null;
        document.querySelectorAll(".cat-section").forEach(s => s.classList.remove("drag-over"));
      });

      let touchTimer = null;
      let isTouchDraggingCard = false;
      card.addEventListener("touchstart", e => {
        touchTimer = setTimeout(() => {
          isTouchDraggingCard = true;
          draggedItemId = item.id;
          card.classList.add("dragging");
        }, 280);
      }, { passive: true });

      card.addEventListener("touchmove", e => {
        if (!isTouchDraggingCard) { clearTimeout(touchTimer); return; }
        e.preventDefault();
        const t = e.touches[0];
        const elUnder = document.elementFromPoint(t.clientX, t.clientY);
        document.querySelectorAll(".cat-section").forEach(s => s.classList.remove("drag-over"));
        const targetSec = elUnder ? elUnder.closest(".cat-section") : null;
        if (targetSec) targetSec.classList.add("drag-over");
      }, { passive: false });

      card.addEventListener("touchend", e => {
        clearTimeout(touchTimer);
        if (!isTouchDraggingCard) return;
        isTouchDraggingCard = false;
        card.classList.remove("dragging");
        const t = e.changedTouches[0];
        const elUnder = document.elementFromPoint(t.clientX, t.clientY);
        const targetSec = elUnder ? elUnder.closest(".cat-section") : null;
        document.querySelectorAll(".cat-section").forEach(s => s.classList.remove("drag-over"));
        if (targetSec && targetSec.getAttribute("data-cat")) {
          moveItemToCategory(item.id, targetSec.getAttribute("data-cat"));
        }
        draggedItemId = null;
      });

      const b = badgeMap[item.item_type || "furniture"] || badgeMap.furniture;
      card.innerHTML = `
        <div class="item-card-header">
          <div class="name">
            <span style="color:#64748B;font-size:11px;cursor:grab;">⠿</span>
            <span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${item.color};border:1px solid #fff;"></span>
            <span>${item.name}</span>
            <span class="badge ${b.cls}">${b.text}</span>
          </div>
          <button class="card-del-btn" title="刪除" onclick="deleteItemById('${item.id}', event)">🗑️</button>
        </div>
        <div class="dims">
          ${Math.round(item.w)}×${Math.round(item.d)}×${item.h || 30} | Z:${item.z || 0} | ${item.rot || 0}°
        </div>
      `;
      listBox.appendChild(card);
    });

    sec.appendChild(header);
    sec.appendChild(listBox);
    container.appendChild(sec);
  });
}

function highlightRightPanel() {
  renderRightPanel();
}

function selectItemById(id) {
  activeId = id;
  if (currentMode === "2D") {
    const group = canvas.getObjects().find(o => o.itemId === id);
    if (group && !forcePanMode) {
      canvas.setActiveObject(group);
      canvas.requestRenderAll();
    }
  } else if (currentMode === "3D" && transformControl) {
    const mesh = selectable3DMeshes.find(m => m.userData.itemId === id);
    if (mesh) attachGizmoWithRules(mesh);
  }
  switchLeftTab('item');
  updateLeftItemPanel();
  highlightRightPanel();
}

function zoomToFit() {
  if (!canvas) return;
  const rw = appState.room.width, rd = appState.room.depth;
  const container = document.getElementById("canvas-container");
  const cw = container.clientWidth - 90, ch = container.clientHeight - 90;
  const scale = Math.min(cw / rw, ch / rd, 1.65);
  const offsetX = (container.clientWidth - rw * scale) / 2;
  const offsetY = (container.clientHeight - rd * scale) / 2;
  canvas.setViewportTransform([scale, 0, 0, scale, offsetX, offsetY]);
  canvas.requestRenderAll();
}

document.getElementById("btn-zoom-fit").addEventListener("click", zoomToFit);
document.getElementById("btn-zoom-in").addEventListener("click", () => canvas.setZoom(Math.min(canvas.getZoom() * 1.2, 5)));
document.getElementById("btn-zoom-out").addEventListener("click", () => canvas.setZoom(Math.max(canvas.getZoom() / 1.2, 0.2)));
document.getElementById("btn-pan-toggle").addEventListener("click", function() {
  forcePanMode = !forcePanMode;
  this.innerText = forcePanMode ? "✋ 平移: 開" : "✋ 平移: 關";
  this.classList.toggle("active", forcePanMode);
  renderFullScene();
});

document.getElementById("btn-save-local").addEventListener("click", () => {
  localStorage.setItem("room_planner_v7", JSON.stringify(appState));
  alert("✅ 已成功儲存於 App 本地記憶中！");
});

document.getElementById("btn-load-local").addEventListener("click", () => {
  const saved = localStorage.getItem("room_planner_v7") || localStorage.getItem("room_planner_v6");
  if (saved) {
    appState = JSON.parse(saved);
    if (!appState.categories) appState.categories = ["床", "大型家具", "收納櫃體", "門窗建材", "機電開關", "牆面裝飾"];
    if (!appState.categories.includes("床")) appState.categories.unshift("床");
    if (!appState.human) appState.human = { x: 230, y: 230, z: 0, height: 178, rot: 0, pitch: 0, posture: "stand", lock_horizontal: false };
    appState.items.forEach(it => saveValidItemBackup(it));
    renderCategoryUI();
    initRoomFormValues();
    initHumanFormValues();
    syncLockScaleUI();
    renderVoidListUI();
    renderFullScene();
    zoomToFit();
    alert("✅ 已成功載入儲存的設計！");
  } else {
    alert("⚠️ 尚未找到本地存檔紀錄！");
  }
});

document.getElementById("btn-export-file").addEventListener("click", () => {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(appState, null, 2));
  const a = document.createElement('a');
  a.setAttribute("href", dataStr);
  a.setAttribute("download", "room_design_" + new Date().toISOString().slice(0, 10) + ".json");
  document.body.appendChild(a);
  a.click();
  a.remove();
});

document.getElementById("file-import").addEventListener("change", function(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(evt) {
    try {
      appState = JSON.parse(evt.target.result);
      if (!appState.categories) appState.categories = ["床", "大型家具", "收納櫃體", "門窗建材", "機電開關", "牆面裝飾"];
      if (!appState.categories.includes("床")) appState.categories.unshift("床");
      if (!appState.human) appState.human = { x: 230, y: 230, z: 0, height: 178, rot: 0, pitch: 0, posture: "stand", lock_horizontal: false };
      appState.items.forEach(it => saveValidItemBackup(it));
      renderCategoryUI();
      initRoomFormValues();
      initHumanFormValues();
      syncLockScaleUI();
      renderVoidListUI();
      renderFullScene();
      zoomToFit();
      alert("✅ 專案檔案載入成功！");
    } catch(err) {
      alert("❌ 檔案格式錯誤！");
    }
  };
  reader.readAsText(file);
});

document.getElementById("btn-reset-default").addEventListener("click", () => {
  if (confirm("確定要重置回附圖原始預設配置嗎？")) {
    appState = JSON.parse(JSON.stringify(INITIAL_CONFIG));
    appState.items.forEach(it => saveValidItemBackup(it));
    renderCategoryUI();
    initRoomFormValues();
    initHumanFormValues();
    syncLockScaleUI();
    renderVoidListUI();
    renderFullScene();
    zoomToFit();
  }
});

function initPanelResizers() {
  const leftPanel = document.getElementById("left-panel");
  const rightPanel = document.getElementById("right-panel");
  const leftResizer = document.getElementById("left-resizer");
  const rightResizer = document.getElementById("right-resizer");

  let resizingSide = null;

  const startResize = (side, e) => {
    e.preventDefault();
    e.stopPropagation();
    resizingSide = side;
  };

  if (leftResizer) leftResizer.addEventListener("pointerdown", e => startResize("left", e));
  if (rightResizer) rightResizer.addEventListener("pointerdown", e => startResize("right", e));

  window.addEventListener("pointermove", e => {
    if (!resizingSide) return;
    if (resizingSide === "left") {
      const newW = Math.max(145, Math.min(window.innerWidth * 0.88, e.clientX));
      leftPanel.style.width = newW + "px";
    } else if (resizingSide === "right") {
      const newW = Math.max(145, Math.min(window.innerWidth * 0.88, window.innerWidth - e.clientX));
      rightPanel.style.width = newW + "px";
    }
    window.dispatchEvent(new Event("resize"));
  });

  window.addEventListener("pointerup", () => {
    resizingSide = null;
  });

  document.querySelectorAll("input, select").forEach(el => {
    el.addEventListener("focus", () => {
      setTimeout(() => {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 280);
    });
  });

  const newCatSel = document.getElementById("new-obj-category");
  if (newCatSel) newCatSel.addEventListener("change", window.onNewObjTypeChange);
}
