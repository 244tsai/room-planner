const STORAGE_KEY_PRIMARY = "home_design_v12_saved";
const STORAGE_KEYS_LEGACY = [
  "home_design_v12_saved", "room_planner_v11_saved", "room_planner_v10_saved",
  "room_planner_v9", "room_planner_v8", "room_planner_v7"
];

function getHomeDesign(state) {
  if (!state) return null;
  if (state.home_design) return state.home_design;
  if (state.room) {
    state.home_design = state.room;
    return state.home_design;
  }
  return null;
}

function loadInitialAppState() {
  for (let i = 0; i < STORAGE_KEYS_LEGACY.length; i++) {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS_LEGACY[i]);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && (parsed.home_design || parsed.room) && Array.isArray(parsed.items)) {
          parsed.default_fuji = INITIAL_CONFIG.default_fuji;
          return parsed;
        }
      }
    } catch (e) {
      console.warn("讀取 localStorage 失敗:", e);
    }
  }
  return JSON.parse(JSON.stringify(INITIAL_CONFIG));
}

function normalizeAppState(state) {
  let hd = getHomeDesign(state);
  if (!hd) {
    hd = { width: 460, depth: 360, height: 280, editable: false, lock_scale: false, auto_save: false, show_walls: true, show_ceiling: false, wall_color: "#F8FAFC", ceiling_color: "#FFFFFF" };
    state.home_design = hd;
  }
  // 雙向相容
  state.room = hd;

  if (!state.voids && state.void) {
    state.voids = [{ id: "void_1", name: "留白處 1", x: state.void.x, y: state.void.y, w: state.void.w, d: state.void.d }];
  }
  if (!state.voids) state.voids = [];
  if (!state.categories) state.categories = ["床", "大型家具", "收納櫃體", "椅子", "門窗建材", "機電開關", "牆面裝飾"];
  if (!state.categories.includes("床")) state.categories.unshift("床");
  if (!state.categories.includes("椅子")) state.categories.splice(3, 0, "椅子");

  state.items.forEach(it => {
    if (it.id === "bed" || it.name === "床") it.category = "床";
    if (it.item_type === "chair" && it.seat_h === undefined) it.seat_h = 45;
    if (!it.stroke_color) it.stroke_color = "#1E293B";
  });

  if (!state.recent_colors || !Array.isArray(state.recent_colors) || state.recent_colors.length === 0) {
    state.recent_colors = ["#38BDF8", "#FAD785", "#DC7CF5", "#A0CB88", "#F97316"];
  }

  if (!state.human) state.human = {};
  state.human = Object.assign({
    x: 230, y: 230, z: 0, height: 178, rot: 0, pitch: 0,
    posture: "stand", sit_mode: "bed_edge", sit_chair_id: "chair_desk", seat_h: 55,
    lock_horizontal: false, fov_h: 100, fov_up: 50, fov_down: 65
  }, state.human);

  if (hd.show_walls === undefined) hd.show_walls = true;
  if (hd.show_ceiling === undefined) hd.show_ceiling = false;
  if (hd.lock_scale === undefined) hd.lock_scale = false;
  if (hd.auto_save === undefined) hd.auto_save = false;
  if (state.compass.auto_center === undefined) state.compass.auto_center = true;

  if (state.compass.auto_center) {
    state.compass.x = Math.round(hd.width / 2);
    state.compass.y = Math.round(hd.depth / 2);
  }
  state.default_fuji = INITIAL_CONFIG.default_fuji;
}

let appState = loadInitialAppState();
normalizeAppState(appState);

function persistAppStateToLocal(isAutoTrigger = false) {
  const hd = getHomeDesign(appState);
  if (isAutoTrigger && !hd.auto_save) return;
  try {
    const serialized = JSON.stringify(appState);
    localStorage.setItem(STORAGE_KEY_PRIMARY, serialized);
    if (!isAutoTrigger) {
      showToast("💾 設計已成功儲存於 App 中！");
    }
  } catch (e) {
    if (!isAutoTrigger) alert("⚠️ 儲存失敗，請檢查材質貼圖大小！");
  }
}

let activeId = null;
let clipboardItem = null;
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

let lastValidItemMap = {};
let expandedCategories = new Set();

function showToast(msg) {
  const el = document.getElementById("toast-msg");
  if (!el) return;
  el.innerText = msg;
  el.classList.add("show");
  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => el.classList.remove("show"), 1800);
}

function isBedItem(it) {
  return it.category === "床" || it.id === "bed" || (it.name && it.name.includes("床") && !it.name.includes("櫃"));
}

function isChairItem(it) {
  return it.item_type === "chair" || it.category === "椅子" || (it.name && it.name.includes("椅"));
}

function isZAdjustableWallType(t) {
  return ["window", "socket", "switch", "wall_item"].includes(t);
}

function isOuterWallProtrudingType(t) {
  return ["window", "socket", "switch"].includes(t);
}

function computeChairSitPose(chair) {
  const rotDeg = ((chair.rot || 0) % 360 + 360) % 360;
  const rad = rotDeg * Math.PI / 180;
  const cx = chair.x + chair.w / 2;
  const cy = chair.y + chair.d / 2;
  const backOffset = Math.max(0, Math.min(8, chair.d * 0.14));
  const sitX = Math.round(cx - Math.sin(rad) * backOffset);
  const sitY = Math.round(cy + Math.cos(rad) * backOffset);
  return {
    x: sitX,
    y: sitY,
    z: 0,
    seat_h: chair.seat_h || 45,
    rot: rotDeg
  };
}

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
    bw: bw,
    bd: bd,
    z0: it.z || 0,
    z1: (it.z || 0) + (it.h || 30)
  };
}

function isTwoItemsOverlapping(a, b) {
  const boxA = getItemAABB(a);
  const boxB = getItemAABB(b);
  const eps = 0.4;
  const overlapX = (boxA.x0 + eps < boxB.x1) && (boxA.x1 - eps > boxB.x0);
  const overlapY = (boxA.y0 + eps < boxB.y1) && (boxA.y1 - eps > boxB.y0);
  const overlapZ = (boxA.z0 + eps < boxB.z1) && (boxA.z1 - eps > boxB.z0);
  return overlapX && overlapY && overlapZ;
}

function isItemOverlappingVoid(item, voidObj) {
  const box = getItemAABB(item);
  const vLeft = voidObj.x;
  const vRight = voidObj.x + voidObj.w;
  const vTop = voidObj.y;
  const vBottom = voidObj.y + voidObj.d;
  const eps = 0.5;
  return (box.x0 + eps < vRight) && (box.x1 - eps > vLeft) &&
         (box.y0 + eps < vBottom) && (box.y1 - eps > vTop);
}

function hasAnyCollision(item) {
  for (let i = 0; i < appState.items.length; i++) {
    const other = appState.items[i];
    if (other.id === item.id) continue;
    if (isTwoItemsOverlapping(item, other)) return other;
  }
  for (let i = 0; i < (appState.voids || []).length; i++) {
    const v = appState.voids[i];
    if (isItemOverlappingVoid(item, v)) {
      return { isVoid: true, name: v.name };
    }
  }
  return null;
}

function saveValidItemBackup(item) {
  lastValidItemMap[item.id] = {
    x: item.x, y: item.y, z: item.z || 0,
    w: item.w, d: item.d, h: item.h || 30, seat_h: item.seat_h || 45, rot: item.rot || 0
  };
}

function recordRecentColor(colorHex) {
  if (!colorHex || typeof colorHex !== "string") return;
  const upper = colorHex.toUpperCase();
  if (!appState.recent_colors) appState.recent_colors = [];
  appState.recent_colors = [upper, ...appState.recent_colors.filter(c => c !== upper)].slice(0, 5);
  renderRecentColorsPalette();
  persistAppStateToLocal(true);
}

function renderRecentColorsPalette() {
  const fillPal = document.getElementById("recent-colors-fill");
  const strokePal = document.getElementById("recent-colors-stroke");
  if (!fillPal && !strokePal) return;

  const createSwatches = (container, onColorPick) => {
    if (!container) return;
    container.innerHTML = "";
    (appState.recent_colors || []).forEach(color => {
      const sw = document.createElement("div");
      sw.style.cssText = `width:20px;height:20px;border-radius:4px;background:${color};border:1px solid #64748B;cursor:pointer;flex-shrink:0;`;
      sw.title = `點擊套用 ${color}`;
      sw.onclick = () => onColorPick(color);
      container.appendChild(sw);
    });
  };

  createSwatches(fillPal, (c) => {
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.color = c;
    const colorPicker = document.getElementById("prop-color");
    if (colorPicker) colorPicker.value = c;
    recordRecentColor(c);
    updateSingleItemVisual(item, "move");
  });

  createSwatches(strokePal, (c) => {
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;
    item.stroke_color = c;
    const strokePicker = document.getElementById("prop-stroke-color");
    if (strokePicker) strokePicker.value = c;
    recordRecentColor(c);
    updateSingleItemVisual(item, "move");
  });
}

function enforceItemConstraints(item, mode = "move", showMsg = false) {
  const hd = getHomeDesign(appState);
  const rw = hd.width;
  const rd = hd.depth;
  const rh = hd.height;
  const t = item.item_type || "furniture";
  const prev = lastValidItemMap[item.id] || { x: item.x, y: item.y, z: item.z || 0, w: item.w, d: item.d, h: item.h || 30, seat_h: item.seat_h || 45, rot: item.rot || 0 };

  item.h = Math.max(4, Math.min(rh, Math.round(item.h || 30)));
  if (t === "chair") {
    item.seat_h = Math.max(15, Math.min(item.h - 5, Math.round(item.seat_h || 45)));
  }

  if (isZAdjustableWallType(t)) {
    item.z = Math.max(0, Math.min(rh - item.h, Math.round(item.z || 0)));
  } else {
    item.z = 0;
  }

  if (["window", "socket", "switch", "wall_item", "door"].includes(t)) {
    const cx = item.x + item.w / 2;
    const cy = item.y + item.d / 2;
    const distN = Math.abs(cy - 0);
    const distS = Math.abs(cy - rd);
    const distW = Math.abs(cx - 0);
    const distE = Math.abs(cx - rw);
    const minDist = Math.min(distN, distS, distW, distE);

    const protrudeOut = isOuterWallProtrudingType(t);
    const longSide = Math.max(item.w, item.d);
    const shortSide = Math.min(item.w, item.d);

    if (minDist === distN || minDist === distS) {
      item.w = Math.min(rw, longSide);
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
      item.w = Math.min(shortSide, 24);
      item.d = Math.min(rd, longSide);
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
    const box = getItemAABB(item);
    const bw = Math.max(1, box.bw);
    const bd = Math.max(1, box.bd);

    const overLeftRatio = (0 - box.x0) / bw;
    const overRightRatio = (box.x1 - rw) / bw;
    const overTopRatio = (0 - box.y0) / bd;
    const overBottomRatio = (box.y1 - rd) / bd;
    const maxOverRatio = Math.max(overLeftRatio, overRightRatio, overTopRatio, overBottomRatio);
    const completelyOutside = (box.x1 <= -8 || box.x0 >= rw + 8 || box.y1 <= -8 || box.y0 >= rd + 8);

    if (!completelyOutside && maxOverRatio > 0) {
      if (maxOverRatio >= 0.75) {
        const gap = 24;
        if (maxOverRatio === overLeftRatio) item.x = Math.round(-bw - gap + (bw - item.w) / 2);
        else if (maxOverRatio === overRightRatio) item.x = Math.round(rw + gap + (bw - item.w) / 2);
        else if (maxOverRatio === overTopRatio) item.y = Math.round(-bd - gap + (bd - item.d) / 2);
        else item.y = Math.round(rd + gap + (bd - item.d) / 2);
        if (showMsg) showToast("📦 超過邊界 3/4，已移至室外備用區！");
      } else {
        if (mode === "scale") {
          if (box.x0 < 0 || box.x1 > rw) item.w = prev.w;
          if (box.y0 < 0 || box.y1 > rd) item.d = prev.d;
        }
        const clampedBox = getItemAABB(item);
        if (clampedBox.x0 < 0) item.x += (0 - clampedBox.x0);
        if (clampedBox.x1 > rw) item.x -= (clampedBox.x1 - rw);
        if (clampedBox.y0 < 0) item.y += (0 - clampedBox.y0);
        if (clampedBox.y1 > rd) item.y -= (clampedBox.y1 - rd);
        item.x = Math.round(item.x);
        item.y = Math.round(item.y);
      }
    }
  }

  let hitOther = hasAnyCollision(item);
  if (hitOther) {
    if (hitOther.isVoid) {
      item.x = prev.x; item.y = prev.y; item.w = prev.w; item.d = prev.d; item.rot = prev.rot;
      if (showMsg) showToast(`⛔ 留白處「${hitOther.name}」無法擺設物件！`);
    } else if (mode === "scale") {
      item.w = prev.w; item.d = prev.d; item.h = prev.h;
    } else if (mode === "rotate") {
      item.rot = prev.rot;
      item.x = prev.x; item.y = prev.y;
    } else {
      const boxA = getItemAABB(item);
      const boxB = getItemAABB(hitOther);
      const pushLeft = boxA.x1 - boxB.x0;
      const pushRight = boxB.x1 - boxA.x0;
      const pushUp = boxA.y1 - boxB.y0;
      const pushDown = boxB.y1 - boxA.y0;
      const minPush = Math.min(pushLeft, pushRight, pushUp, pushDown);
      if (minPush === pushLeft) item.x -= pushLeft;
      else if (minPush === pushRight) item.x += pushRight;
      else if (minPush === pushUp) item.y -= pushUp;
      else item.y += pushDown;

      if (hasAnyCollision(item)) {
        item.x = prev.x; item.y = prev.y;
      }
      item.x = Math.round(item.x);
      item.y = Math.round(item.y);
    }
  }

  if (appState.human.posture === "sit" && appState.human.sit_mode === "chair" && appState.human.sit_chair_id === item.id) {
    const pose = computeChairSitPose(item);
    appState.human.x = pose.x;
    appState.human.y = pose.y;
    appState.human.seat_h = pose.seat_h;
    appState.human.rot = pose.rot;
    initHumanFormValues();
    if (currentMode === "FPV") syncFPVCamera();
  }

  saveValidItemBackup(item);
  persistAppStateToLocal(true);
  return true;
}

function findNonOverlappingSpot(newItem) {
  const hd = getHomeDesign(appState);
  saveValidItemBackup(newItem);
  if (!hasAnyCollision(newItem)) {
    enforceItemConstraints(newItem, "move", false);
    return;
  }
  const rw = hd.width, rd = hd.depth;
  for (let y = 10; y <= rd - newItem.d - 10; y += 20) {
    for (let x = 10; x <= rw - newItem.w - 10; x += 20) {
      newItem.x = x; newItem.y = y;
      if (!hasAnyCollision(newItem)) {
        saveValidItemBackup(newItem);
        return;
      }
    }
  }
  newItem.x = rw + 30;
  newItem.y = 20;
  saveValidItemBackup(newItem);
}

function checkHumanWalkable(nx, ny) {
  const hd = getHomeDesign(appState);
  const isSittingBedEdge = (appState.human.posture === "sit" && appState.human.sit_mode === "bed_edge");
  const radius = isSittingBedEdge ? 2 : 12;
  const rw = hd.width, rd = hd.depth;

  if (hd.show_walls) {
    const wallPad = isSittingBedEdge ? 2 : radius;
    if (nx < wallPad || nx > rw - wallPad || ny < wallPad || ny > rd - wallPad) {
      return { allowed: false, baseZ: appState.human.z || 0 };
    }
  }

  if (appState.human.posture === "sit" && appState.human.sit_mode === "chair") {
    const ch = appState.items.find(i => i.id === appState.human.sit_chair_id);
    if (ch) return { allowed: true, baseZ: 0 };
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
      if (Math.abs(lx) <= halfW + 8 && Math.abs(ly) <= halfD + 8) {
        if (isSittingBedEdge) {
          appState.human.seat_h = (it.z || 0) + (it.h || 55);
          supportZ = 0;
        } else {
          supportZ = Math.max(supportZ, (it.z || 0) + (it.h || 55));
        }
      }
    } else if (it.item_type === "furniture" || it.item_type === "chair" || it.item_type === "wall_item") {
      if (isSittingBedEdge) {
        if (Math.abs(lx) < halfW - 2 && Math.abs(ly) < halfD - 2) {
          return { allowed: false, baseZ: 0 };
        }
      } else {
        if (Math.abs(lx) < halfW + radius && Math.abs(ly) < halfD + radius) {
          return { allowed: false, baseZ: appState.human.z || 0 };
        }
      }
    }
  }
  return { allowed: true, baseZ: supportZ };
}

function clampToBedEdge(nx, ny) {
  const bed = appState.items.find(i => isBedItem(i));
  if (!bed) return { x: nx, y: ny, edge: "bottom" };

  const pad = 3;
  const minX = bed.x + pad;
  const maxX = bed.x + bed.w - pad;
  const minY = bed.y + pad;
  const maxY = bed.y + bed.d - pad;

  const cx = Math.max(minX, Math.min(maxX, nx));
  const cy = Math.max(minY, Math.min(maxY, ny));

  const dBottom = Math.abs(cy - maxY);
  const dLeft = Math.abs(cx - minX);
  const dRight = Math.abs(cx - maxX);
  const dTop = Math.abs(cy - minY);

  const candidates = [
    { edge: "bottom", dist: dBottom, x: cx, y: maxY, rot: 180 },
    { edge: "left", dist: dLeft, x: minX, y: cy, rot: 270 },
    { edge: "right", dist: dRight, x: maxX, y: cy, rot: 90 }
  ];
  if (bed.y > 20) {
    candidates.push({ edge: "top", dist: dTop, x: cx, y: minY, rot: 0 });
  }
  candidates.sort((a, b) => a.dist - b.dist);
  const chosen = candidates[0];

  appState.human.seat_h = (bed.z || 0) + (bed.h || 55);
  appState.human.z = 0;

  return { x: Math.round(chosen.x), y: Math.round(chosen.y), edge: chosen.edge, suggestRot: chosen.rot };
}

function tryMoveHumanTo(nx, ny, showBlockMsg = false) {
  if (appState.human.posture === "sit" && appState.human.sit_mode === "chair") {
    const distFromChair = Math.hypot(nx - appState.human.x, ny - appState.human.y);
    if (distFromChair > 1.5) {
      appState.human.sit_mode = "bed_edge";
    }
  }

  if (appState.human.posture === "sit" && appState.human.sit_mode === "bed_edge") {
    const edgePt = clampToBedEdge(nx, ny);
    appState.human.x = edgePt.x;
    appState.human.y = edgePt.y;
    appState.human.z = 0;
    persistAppStateToLocal(true);
    return true;
  }

  const res = checkHumanWalkable(nx, ny);
  if (res.allowed) {
    appState.human.x = nx;
    appState.human.y = ny;
    appState.human.z = res.baseZ;
    persistAppStateToLocal(true);
    return true;
  }
  const resX = checkHumanWalkable(nx, appState.human.y);
  if (resX.allowed) {
    appState.human.x = nx;
    appState.human.z = resX.baseZ;
    persistAppStateToLocal(true);
    return true;
  }
  const resY = checkHumanWalkable(appState.human.x, ny);
  if (resY.allowed) {
    appState.human.y = ny;
    appState.human.z = resY.baseZ;
    persistAppStateToLocal(true);
    return true;
  }
  if (showBlockMsg) showToast("⚠️ 前方有家具阻擋，已貼齊邊界！");
  return false;
}

function getHumanEyeHeight() {
  const h = appState.human;
  const stature = h.height || 178;
  const baseZ = h.z || 0;

  if (h.posture === "lie") {
    return Math.round(baseZ + 22);
  } else if (h.posture === "sit") {
    const seatH = h.seat_h || 45;
    return Math.round(seatH + stature * 0.44);
  }
  return Math.round(baseZ + stature * 0.93);
}

function renderChairSelectOptions() {
  const chairs = appState.items.filter(it => isChairItem(it));
  const selLeft = document.getElementById("sit-chair-select");
  const selHud = document.getElementById("hud-chair-select");
  if (!selLeft || !selHud) return;

  selLeft.innerHTML = "";
  selHud.innerHTML = "";

  if (chairs.length === 0) {
    selLeft.add(new Option("目前無椅子 (請先新增椅子)", ""));
    selHud.add(new Option("無椅子", ""));
    return;
  }

  chairs.forEach(ch => {
    const sh = ch.seat_h || 45;
    selLeft.add(new Option(`🪑 ${ch.name} (坐墊高 ${sh}cm)`, ch.id));
    selHud.add(new Option(`🪑坐:${ch.name}(${sh}cm)`, ch.id));
  });

  if (appState.human.sit_chair_id && chairs.some(c => c.id === appState.human.sit_chair_id)) {
    selLeft.value = appState.human.sit_chair_id;
    selHud.value = appState.human.sit_chair_id;
  } else {
    appState.human.sit_chair_id = chairs[0].id;
    selLeft.value = chairs[0].id;
    selHud.value = chairs[0].id;
  }
}

window.sitAtBedEdge = function() {
  walkTarget = null;
  const bed = appState.items.find(i => isBedItem(i));
  appState.human.posture = "sit";
  appState.human.sit_mode = "bed_edge";
  appState.human.z = 0;
  if (bed) {
    appState.human.seat_h = (bed.z || 0) + (bed.h || 55);
    const isNearBed = (
      appState.human.x >= bed.x - 25 && appState.human.x <= bed.x + bed.w + 25 &&
      appState.human.y >= bed.y - 25 && appState.human.y <= bed.y + bed.d + 25
    );
    const targetX = isNearBed ? appState.human.x : Math.round(bed.x + bed.w / 2);
    const targetY = isNearBed ? appState.human.y : Math.round(bed.y + bed.d);
    const pt = clampToBedEdge(targetX, targetY);
    appState.human.x = pt.x;
    appState.human.y = pt.y;
    appState.human.rot = pt.suggestRot !== undefined ? pt.suggestRot : 180;
  } else {
    appState.human.seat_h = 45;
  }
  if (!appState.human.lock_horizontal) appState.human.pitch = -5;
  initHumanFormValues();
  renderFullScene();
  if (currentMode === "FPV") syncFPVCamera();
  persistAppStateToLocal(true);
};

window.sitOnSelectedChair = function(explicitChairId) {
  walkTarget = null;
  renderChairSelectOptions();
  const selEl = document.getElementById("sit-chair-select");
  const targetChairId = explicitChairId || (selEl ? selEl.value : "") || appState.human.sit_chair_id;
  let chair = appState.items.find(i => i.id === targetChairId && isChairItem(i));
  if (!chair) chair = appState.items.find(i => isChairItem(i));
  if (!chair) {
    showToast("💡 尚無椅子，請先新增椅子！");
    return;
  }

  appState.human.posture = "sit";
  appState.human.sit_mode = "chair";
  appState.human.sit_chair_id = chair.id;

  const selLeft = document.getElementById("sit-chair-select");
  const selHud = document.getElementById("hud-chair-select");
  if (selLeft) selLeft.value = chair.id;
  if (selHud) selHud.value = chair.id;

  const pose = computeChairSitPose(chair);
  appState.human.x = pose.x;
  appState.human.y = pose.y;
  appState.human.z = 0;
  appState.human.seat_h = pose.seat_h;
  appState.human.rot = pose.rot;
  if (!appState.human.lock_horizontal) appState.human.pitch = -4;

  initHumanFormValues();
  renderFullScene();
  if (currentMode === "3D" && renderer) updateThreeScene();
  else if (currentMode === "FPV") { updateThreeScene(); syncFPVCamera(); }
  persistAppStateToLocal(true);
  showToast(`🪑 已坐在「${chair.name}」(背靠椅背)`);
};

window.onHudChairSelectChange = function() {
  const val = document.getElementById("hud-chair-select").value;
  if (val) {
    const selLeft = document.getElementById("sit-chair-select");
    if (selLeft) selLeft.value = val;
    window.sitOnSelectedChair(val);
  }
};

window.rotateActiveItemBy = function(deltaDeg) {
  const item = appState.items.find(i => i.id === activeId);
  if (!item) {
    showToast("💡 請先選取要旋轉的家具！");
    return;
  }
  item.rot = Math.round((((item.rot || 0) + deltaDeg) % 360 + 360) % 360);
  updateSingleItemVisual(item, "rotate");
  showToast(`🔄 「${item.name}」已轉至 ${item.rot}°`);
};

window.copySelectedItem = function(targetId) {
  const idToCopy = targetId || activeId;
  if (!idToCopy || idToCopy === "HUMAN") {
    showToast("💡 請先點選要複製的家具！");
    return false;
  }
  const item = appState.items.find(i => i.id === idToCopy);
  if (!item) return false;
  clipboardItem = JSON.parse(JSON.stringify(item));
  showToast(`📄 已複製「${item.name}」！可按 Ctrl+V 或「貼上」`);
  return true;
};

window.pasteCopiedItem = function() {
  if (!clipboardItem && activeId && activeId !== "HUMAN") {
    const cur = appState.items.find(i => i.id === activeId);
    if (cur) clipboardItem = JSON.parse(JSON.stringify(cur));
  }
  if (!clipboardItem) {
    showToast("⚠️ 剪貼簿尚無物件，請先點選物件並按「複製」！");
    return;
  }
  const copy = JSON.parse(JSON.stringify(clipboardItem));
  copy.id = "item_" + Date.now() + "_" + Math.floor(Math.random() * 1000);
  const baseName = copy.name.replace(/\(複本\d*\)$/, "");
  copy.name = baseName + "(複本)";
  copy.x = Math.round((copy.x || 0) + 25);
  copy.y = Math.round((copy.y || 0) + 25);

  expandedCategories.add(copy.category || appState.categories[0]);
  findNonOverlappingSpot(copy);
  appState.items.push(copy);
  clipboardItem = JSON.parse(JSON.stringify(copy));
  activeId = copy.id;
  renderFullScene();
  selectItemById(copy.id);
  persistAppStateToLocal(true);
  showToast(`📋 已貼上「${copy.name}」！`);
};

window.duplicateItemById = function(id, evt) {
  if (evt) evt.stopPropagation();
  if (window.copySelectedItem(id)) {
    window.pasteCopiedItem();
  }
};

window.toggleSectionCollapse = function(bodyId, iconId) {
  const el = document.getElementById(bodyId);
  const ic = document.getElementById(iconId);
  if (!el) return;
  const isHidden = (el.style.display === "none");
  el.style.display = isHidden ? "block" : "none";
  if (ic) ic.innerText = isHidden ? "▾" : "▸";
};

window.openSectionCollapse = function(bodyId, iconId) {
  const el = document.getElementById(bodyId);
  const ic = document.getElementById(iconId);
  if (el) el.style.display = "block";
  if (ic) ic.innerText = "▾";
};

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
  const mLeft = document.getElementById("mnav-left");
  const mRight = document.getElementById("mnav-right");
  const mCanvas = document.getElementById("mnav-canvas");
  if (mLeft) mLeft.classList.toggle("active", target === 'left');
  if (mRight) mRight.classList.toggle("active", target === 'right');
  if (mCanvas) mCanvas.classList.toggle("active", target === 'canvas');

  if (target === 'left') {
    if (lp) lp.classList.toggle("open");
    if (rp) rp.classList.remove("open");
  } else if (target === 'right') {
    if (rp) rp.classList.toggle("open");
    if (lp) lp.classList.remove("open");
  } else {
    if (lp) lp.classList.remove("open");
    if (rp) rp.classList.remove("open");
  }
}

function switchLeftTab(tab) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
  const btn = document.getElementById("tab-btn-" + tab);
  const content = document.getElementById("tab-content-" + tab);
  if (btn) btn.classList.add("active");
  if (content) content.style.display = "flex";
}

window.toggleLockScaleBtn = function() {
  const hd = getHomeDesign(appState);
  hd.lock_scale = !hd.lock_scale;
  syncLockScaleUI();
  renderFullScene();
  persistAppStateToLocal(true);
};

function syncLockScaleUI() {
  const hd = getHomeDesign(appState);
  const locked = !!hd.lock_scale;
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
  if (bScaleGizmo) bScaleGizmo.style.opacity = locked ? "0.4" : "1";
  if (locked && gizmoMode === "scale") window.set3DGizmoMode("translate");
}

function renderCategoryUI() {
  const newCatSel = document.getElementById("new-obj-category");
  const propCatSel = document.getElementById("prop-category");
  const tagsBox = document.getElementById("category-tags-container");
  if (!newCatSel || !propCatSel || !tagsBox) return;

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
  persistAppStateToLocal(true);
}

window.addCategory = function() {
  const inp = document.getElementById("new-cat-input");
  if (!inp) return;
  const val = inp.value.trim();
  if (!val) return;
  if (!appState.categories.includes(val)) {
    appState.categories.push(val);
    inp.value = "";
    renderCategoryUI();
    renderRightPanel();
    persistAppStateToLocal(true);
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
  persistAppStateToLocal(true);
};

window.addEventListener("keydown", function(e) {
  const tag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
  const isEditingInput = (tag === "input" || tag === "textarea" || tag === "select");
  if (isEditingInput) return;

  if ((e.ctrlKey || e.metaKey) && (e.key === "c" || e.key === "C")) {
    if (activeId && activeId !== "HUMAN") {
      e.preventDefault();
      window.copySelectedItem(activeId);
    }
    return;
  }

  if ((e.ctrlKey || e.metaKey) && (e.key === "v" || e.key === "V")) {
    e.preventDefault();
    window.pasteCopiedItem();
    return;
  }

  if (e.key === "Delete" || e.key === "Backspace") {
    if (activeId && activeId !== "HUMAN") {
      e.preventDefault();
      deleteItemById(activeId);
    }
    return;
  }

  if (currentMode === "FPV" || currentMode === "3D" || (appState.human.posture === "sit" && appState.human.sit_mode === "bed_edge")) {
    if (e.key === "w" || e.key === "W" || e.key === "ArrowUp") { fpvMoveDir.forward = 1; walkTarget = null; }
    if (e.key === "s" || e.key === "S" || e.key === "ArrowDown") { fpvMoveDir.forward = -1; walkTarget = null; }
    if (e.key === "a" || e.key === "A" || e.key === "ArrowLeft") { fpvMoveDir.right = -1; walkTarget = null; }
    if (e.key === "d" || e.key === "D" || e.key === "ArrowRight") { fpvMoveDir.right = 1; walkTarget = null; }

    if (currentMode === "2D" && (fpvMoveDir.forward !== 0 || fpvMoveDir.right !== 0)) {
      const yawRad = (appState.human.rot || 0) * Math.PI / 180;
      const fx = Math.sin(yawRad), fz = -Math.cos(yawRad);
      const rx = Math.cos(yawRad), rz = Math.sin(yawRad);
      const step = 8;
      const nx = appState.human.x + (fx * fpvMoveDir.forward + rx * fpvMoveDir.right) * step;
      const ny = appState.human.y + (fz * fpvMoveDir.forward + rz * fpvMoveDir.right) * step;
      tryMoveHumanTo(nx, ny, false);
      initHumanFormValues();
      renderFullScene();
    }
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
  if (!container) return;

  canvas = new fabric.Canvas('fabric-canvas', {
    width: container.clientWidth || 800,
    height: container.clientHeight || 600,
    backgroundColor: '#0A0C10',
    selection: false,
    preserveObjectStacking: true
  });

  appState.items.forEach(it => saveValidItemBackup(it));

  bindDpadBtn("dpad-up", 0, 1);
  bindDpadBtn("dpad-down", 0, -1);
  bindDpadBtn("dpad-left", -1, 0);
  bindDpadBtn("dpad-right", 1, 0);

  const lockScaleChk = document.getElementById("lock-scale-chk");
  if (lockScaleChk) {
    lockScaleChk.addEventListener("change", e => {
      const hd = getHomeDesign(appState);
      hd.lock_scale = e.target.checked;
      syncLockScaleUI();
      renderFullScene();
      persistAppStateToLocal(true);
    });
  }

  const autoSaveChk = document.getElementById("auto-save-chk");
  if (autoSaveChk) {
    const hd = getHomeDesign(appState);
    autoSaveChk.checked = !!hd.auto_save;
    autoSaveChk.addEventListener("change", e => {
      hd.auto_save = e.target.checked;
      showToast(hd.auto_save ? "✅ 已開啟自動儲存" : "ℹ️ 已切換為手動儲存模式");
      persistAppStateToLocal(false);
    });
  }

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
    const hd = getHomeDesign(appState);
    const isSelectable = target && (target.itemId || target.isHuman || (target.voidId && hd.editable));

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
    if (trashEl && trashEl.classList.contains("show")) {
      if (isOverTrash && activeId && activeId !== "HUMAN") {
        deleteItemById(activeId);
      }
      trashEl.classList.remove("show", "hover");
      isOverTrash = false;
    }
  });

  const upperCanvas = canvas.upperCanvasEl;
  if (upperCanvas) {
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
  }

  canvas.on('selection:created', onObjectSelected);
  canvas.on('selection:updated', onObjectSelected);
  canvas.on('selection:cleared', onObjectDeselected);
  canvas.on('object:moving', e => onObjectLiveTransform(e, "move"));
  canvas.on('object:scaling', e => onObjectLiveTransform(e, "scale"));
  canvas.on('object:rotating', e => onObjectLiveTransform(e, "rotate"));
  canvas.on('object:modified', onObjectModifiedComplete);

  if (appState.human.posture === "sit" && appState.human.sit_mode === "chair") {
    const ch = appState.items.find(i => i.id === appState.human.sit_chair_id && isChairItem(i));
    if (ch) {
      const pose = computeChairSitPose(ch);
      appState.human.x = pose.x;
      appState.human.y = pose.y;
      appState.human.z = 0;
      appState.human.seat_h = pose.seat_h;
      appState.human.rot = pose.rot;
    }
  } else {
    const initWalk = checkHumanWalkable(appState.human.x, appState.human.y);
    appState.human.z = initWalk.baseZ;
  }

  renderCategoryUI();
  renderChairSelectOptions();
  renderRecentColorsPalette();
  initRoomFormValues();
  initHumanFormValues();
  syncLockScaleUI();
  renderVoidListUI();
  renderFullScene();
  zoomToFit();
  initPanelResizers();
  initFPVHudDragAndResize();
}

function renderFullScene() {
  if (!canvas) return;
  canvas.clear();
  canvas.backgroundColor = '#0A0C10';

  const hd = getHomeDesign(appState);
  const rw = hd.width || 460, rd = hd.depth || 360;

  canvas.add(new fabric.Rect({
    left: 0, top: 0, width: rw, height: rd,
    fill: '#5089C6', stroke: '#38BDF8', strokeWidth: 2,
    selectable: false, evented: false
  }));

  canvas.add(new fabric.Text(`◀ 室內設計寬 ${rw} cm ▶`, {
    left: rw / 2, top: -24, fontSize: 13, fill: '#94A3B8', originX: 'center', selectable: false, evented: false
  }));
  canvas.add(new fabric.Text(`◀ 室內設計深 ${rd} cm ▶`, {
    left: -24, top: rd / 2, fontSize: 13, fill: '#94A3B8', originX: 'center', angle: -90, selectable: false, evented: false
  }));

  const canEditGround = !!hd.editable && !forcePanMode;
  (appState.voids || []).forEach(v => {
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

  const isTypingNow = document.activeElement && (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "SELECT");
  if (!isTypingNow) {
    if (activeId === "HUMAN") {
      const hg = canvas.getObjects().find(o => o.isHuman);
      if (hg && !forcePanMode) canvas.setActiveObject(hg);
    } else if (activeId) {
      const g = canvas.getObjects().find(o => o.itemId === activeId);
      if (g && !forcePanMode) canvas.setActiveObject(g);
    }
  }

  renderChairSelectOptions();
  renderRightPanel();
  canvas.requestRenderAll();
  if ((currentMode === "3D" || currentMode === "FPV") && renderer) updateThreeScene();
}

function createFabricHuman() {
  const h = appState.human;
  const halfFovRad = ((h.fov_h || 100) / 2) * Math.PI / 180;
  const coneLen = 48;
  const coneHalfW = Math.round(Math.tan(halfFovRad) * coneLen);

  const fovCone = new fabric.Polygon([
    { x: 0, y: 0 }, { x: -coneHalfW, y: -coneLen }, { x: coneHalfW, y: -coneLen }
  ], {
    fill: 'rgba(168, 85, 247, 0.30)', stroke: '#C084FC', strokeWidth: 1.5,
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
  const strokeColor = item.stroke_color || '#1E293B';
  const rect = new fabric.Rect({
    width: item.w, height: item.d,
    fill: item.color, stroke: strokeColor, strokeWidth: 2.0,
    originX: 'center', originY: 'center'
  });
  subElements.push(rect);

  if (item.item_type === "chair") {
    const backrest = new fabric.Rect({
      width: item.w * 0.85, height: Math.max(5, item.d * 0.18),
      fill: '#0284C7', stroke: '#E0F2FE', strokeWidth: 1,
      originX: 'center', originY: 'center',
      top: item.d / 2 - Math.max(3, item.d * 0.1)
    });
    subElements.push(backrest);
  }

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

  const hd = getHomeDesign(appState);
  const lockS = !!hd.lock_scale;
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
  const hd = getHomeDesign(appState);
  const rw = hd.width, rd = hd.depth;
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
  const hd = getHomeDesign(appState);
  const radius = Math.max(hd.width, hd.depth) * 0.72;

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
    const clickedItem = appState.items.find(i => i.id === target.itemId);
    if (clickedItem && isChairItem(clickedItem) && appState.human.posture === "sit") {
      appState.human.sit_mode = "chair";
      appState.human.sit_chair_id = clickedItem.id;
      const pose = computeChairSitPose(clickedItem);
      appState.human.x = pose.x;
      appState.human.y = pose.y;
      appState.human.z = 0;
      appState.human.seat_h = pose.seat_h;
      appState.human.rot = pose.rot;
      initHumanFormValues();
    }
    switchLeftTab('item');
    openSectionCollapse("collapse-body-edit", "collapse-icon-edit");
    updateLeftItemPanel();
    highlightRightPanel();
  } else if (target.voidId) {
    switchLeftTab('room');
  }
}

function onObjectDeselected() {
  activeId = null;
  const noSel = document.getElementById("no-selection");
  const propEd = document.getElementById("prop-editor");
  if (noSel) noSel.style.display = "block";
  if (propEd) propEd.style.display = "none";
  highlightRightPanel();
}

function onObjectLiveTransform(e, mode) {
  const target = e.target;
  if (!target) return;

  if (target.itemId && e.e) {
    const trashEl = document.getElementById("trash-dropzone");
    if (trashEl) {
      trashEl.classList.add("show");
      const pt = (e.e.touches && e.e.touches[0]) ? e.e.touches[0] : e.e;
      const rect = trashEl.getBoundingClientRect();
      isOverTrash = (pt.clientX >= rect.left && pt.clientX <= rect.right && pt.clientY >= rect.top && pt.clientY <= rect.bottom);
      trashEl.classList.toggle("hover", isOverTrash);
    }
  }

  if (target.isHuman) {
    const nx = Math.round(target.left);
    const ny = Math.round(target.top);
    tryMoveHumanTo(nx, ny, false);
    target.set({ left: appState.human.x, top: appState.human.y });
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
    const hd = getHomeDesign(appState);
    if (mode === "scale" && !hd.lock_scale) {
      item.w = Math.max(4, Math.round(baseRect.width * Math.abs(target.scaleX)));
      item.d = Math.max(4, Math.round(baseRect.height * Math.abs(target.scaleY)));
    }
    item.rot = Math.round((target.angle % 360 + 360) % 360);
    item.x = Math.round(target.left - item.w / 2);
    item.y = Math.round(target.top - item.d / 2);

    enforceItemConstraints(item, mode, false);

    if (mode === "scale") {
      target.set({
        scaleX: item.w / baseRect.width,
        scaleY: item.d / baseRect.height,
        left: item.x + item.w / 2,
        top: item.y + item.d / 2
      });
    } else if (mode === "rotate") {
      target.set({ angle: item.rot });
    } else {
      target.set({
        left: item.x + item.w / 2,
        top: item.y + item.d / 2
      });
    }
    updateLeftItemPanel();

  } else if (target.voidId) {
    const v = (appState.voids || []).find(x => x.id === target.voidId);
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
    if (trashEl) trashEl.classList.remove("show", "hover");
    isOverTrash = false;
    deleteItemById(activeId);
    return;
  }
  if (trashEl) trashEl.classList.remove("show", "hover");
  isOverTrash = false;
  persistAppStateToLocal(true);
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

  const noSel = document.getElementById("no-selection");
  const propEd = document.getElementById("prop-editor");
  if (noSel) noSel.style.display = "none";
  if (propEd) propEd.style.display = "block";

  const typeNames = {
    furniture: "🛋️ 家具 / 床 (貼地)",
    chair: "🪑 椅子 (可設坐墊高)",
    wall_item: "🖼️ 牆壁上物品 (貼牆可調Z)",
    door: "🚪 房門 (貼牆貼地)",
    window: "🪟 窗戶 (貼牆外突)",
    socket: "🔌 插座 (貼牆外突)",
    switch: "💡 開關 (貼牆外突)"
  };
  const t = item.item_type || "furniture";
  const badgeEl = document.getElementById("prop-type-badge");
  if (badgeEl) badgeEl.innerText = typeNames[t] || typeNames.furniture;

  setInputValueSafe("prop-name", item.name);
  setInputValueSafe("prop-category", item.category || appState.categories[0]);
  setInputValueSafe("prop-type", t);
  setInputValueSafe("prop-w", Math.round(item.w));
  setInputValueSafe("prop-d", Math.round(item.d));
  setInputValueSafe("prop-h", item.h || 30);
  setInputValueSafe("prop-seath", item.seat_h || 45);
  setInputValueSafe("prop-x", Math.round(item.x));
  setInputValueSafe("prop-y", Math.round(item.y));
  setInputValueSafe("prop-z", Math.round(item.z || 0));
  setInputValueSafe("prop-rot", item.rot || 0);
  setInputValueSafe("prop-rot-slider", item.rot || 0);
  const rotValEl = document.getElementById("prop-rot-val");
  if (rotValEl) rotValEl.innerText = (item.rot || 0) + "°";
  setInputValueSafe("prop-color", item.color);
  setInputValueSafe("prop-stroke-color", item.stroke_color || "#1E293B");

  const hd = getHomeDesign(appState);
  const lockS = !!hd.lock_scale;
  const pw = document.getElementById("prop-w");
  const pd = document.getElementById("prop-d");
  const ph = document.getElementById("prop-h");
  if (pw) pw.disabled = lockS;
  if (pd) pd.disabled = lockS;
  if (ph) ph.disabled = lockS;

  const seathRow = document.getElementById("prop-seath-row");
  if (seathRow) seathRow.style.display = (t === "chair") ? "flex" : "none";

  const canZ = isZAdjustableWallType(t);
  const zRow = document.getElementById("prop-z-row");
  const zHint = document.getElementById("prop-z-hint");
  if (zRow) zRow.style.display = canZ ? "flex" : "none";
  if (zHint) zHint.style.display = canZ ? "inline" : "none";

  const dSwing = document.getElementById("door-swing-group");
  const sUpload = document.getElementById("scenery-upload-group");
  if (dSwing) dSwing.style.display = (t === "door") ? "flex" : "none";
  if (sUpload) sUpload.style.display = (t === "window") ? "flex" : "none";
}

function updateSingleItemVisual(item, mode = "move") {
  enforceItemConstraints(item, mode, true);
  updateLeftItemPanel();
  renderFullScene();
}

["prop-name", "prop-category", "prop-type", "prop-w", "prop-d", "prop-h", "prop-seath", "prop-x", "prop-y", "prop-z", "prop-rot", "prop-color", "prop-stroke-color"].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;

  const handleValChange = (isFinalCommit) => {
    const item = appState.items.find(i => i.id === activeId);
    if (!item) return;

    const rawVal = el.value;
    let mode = "move";
    const hd = getHomeDesign(appState);

    if (id === "prop-name") item.name = rawVal;
    else if (id === "prop-category") {
      item.category = rawVal;
      expandedCategories.add(rawVal);
    } else if (id === "prop-type") {
      item.item_type = rawVal;
      if (rawVal === "chair" && !item.seat_h) { item.seat_h = 45; item.h = Math.max(item.h, 80); }
      if (rawVal === "window" && !item.scenery) item.scenery = appState.default_fuji;
      if (!isZAdjustableWallType(rawVal)) item.z = 0;
      enforceItemConstraints(item, "move", true);
      updateLeftItemPanel();
      renderFullScene();
      return;
    } else if (id === "prop-color") {
      item.color = rawVal;
      recordRecentColor(rawVal);
    } else if (id === "prop-stroke-color") {
      item.stroke_
