import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# 設置頁面標題與佈局
st.set_page_config(
    page_title="臥室空間設計 & 坐向方位規劃",
    page_icon="📐",
    layout="wide"
)

# --- 1. 預設數據初始化 (完美對照附圖內容) ---
DEFAULT_ROOM = {
    "width": 460,   # 房間總寬度 (X軸, cm)
    "depth": 360,   # 房間總深度 (Y軸, cm)
    "height": 280   # 房間天花板高 (Z軸, cm)
}

# 附圖中的所有物件預設值
DEFAULT_OBJECTS = [
    {
        "id": "obj_bed",
        "name": "床",
        "w": 152, "d": 195, "h": 55,
        "x": 200, "y": 140,
        "color": "#FAD785",
        "text_color": "#FFFFFF",
        "label": "195 x 152\n床"
    },
    {
        "id": "obj_stand_l",
        "name": "床頭櫃 (左)",
        "w": 25, "d": 40, "h": 45,
        "x": 175, "y": 295,
        "color": "#FAD785",
        "text_color": "#FFFFFF",
        "label": "40x25\n床頭櫃"
    },
    {
        "id": "obj_stand_r",
        "name": "床頭櫃 (右)",
        "w": 25, "d": 40, "h": 45,
        "x": 352, "y": 295,
        "color": "#FAD785",
        "text_color": "#FFFFFF",
        "label": "40x25\n床頭櫃"
    },
    {
        "id": "obj_wardrobe_new",
        "name": "新衣櫃",
        "w": 121, "d": 72, "h": 210,
        "x": 30, "y": 260,
        "color": "#A0CB88",
        "text_color": "#FFFFFF",
        "label": "72 x 121 新衣櫃"
    },
    {
        "id": "obj_desk",
        "name": "書桌",
        "w": 123, "d": 71, "h": 75,
        "x": 30, "y": 150,
        "color": "#8232FA",
        "text_color": "#FFFFFF",
        "label": "123 x 71 書桌"
    },
    {
        "id": "obj_drybox",
        "name": "防潮箱",
        "w": 40, "d": 45, "h": 50,
        "x": 265, "y": 50,
        "color": "#DC7CF5",
        "text_color": "#FFFFFF",
        "label": "45 x 40\n防潮箱"
    },
    {
        "id": "obj_wardrobe_white",
        "name": "白衣櫃",
        "w": 60, "d": 55, "h": 190,
        "x": 305, "y": 50,
        "color": "#AADE8D",
        "text_color": "#FFFFFF",
        "label": "55 x 60\n白衣櫃"
    },
    {
        "id": "obj_wardrobe_old",
        "name": "舊衣櫃",
        "w": 120, "d": 51, "h": 200,
        "x": 365, "y": 50,
        "color": "#9EC484",
        "text_color": "#FFFFFF",
        "label": "51 x 120 舊衣櫃"
    },
    {
        "id": "obj_bookcase",
        "name": "玻書櫃",
        "w": 32, "d": 63, "h": 180,
        "x": 450, "y": 180,
        "color": "#DC7CF5",
        "text_color": "#FFFFFF",
        "label": "63 x 32 玻書櫃"
    }
]

# 留白 (右上缺口/凹位)
DEFAULT_VOID = {
    "x": 380, "y": 240, "w": 100, "d": 120, "color": "#FFFFFF", "label": "留白空間"
}

# 窗戶 (底部)
DEFAULT_WINDOWS = [
    {"x": 65, "y": 38, "w": 130, "d": 12, "color": "#FDB813", "label": "窗戶 (主)"},
    {"x": 355, "y": 38, "w": 20, "d": 12, "color": "#FDB813", "label": "小窗"}
]

# Session State 初始化
if "room" not in st.session_state:
    st.session_state.room = DEFAULT_ROOM.copy()
if "objects" not in st.session_state:
    st.session_state.objects = [dict(item) for item in DEFAULT_OBJECTS]
if "void_area" not in st.session_state:
    st.session_state.void_area = DEFAULT_VOID.copy()
if "windows" not in st.session_state:
    st.session_state.windows = [dict(item) for item in DEFAULT_WINDOWS]

# 方位中心 (放射線交叉點，預設位在床的靠前中心點)
if "compass_center" not in st.session_state:
    st.session_state.compass_center = {"x": 260, "y": 200}

# --- 側邊欄控制面板 ---
st.sidebar.title("🛠️ 平面與格局設定")

view_mode = st.sidebar.radio("📐 檢視模式切換", ["2D 平面配置圖", "3D 空間建模視圖"], index=0)

with st.sidebar.expander("🏠 房間基礎尺寸 (cm)", expanded=False):
    st.session_state.room["width"] = st.number_input("房間寬度 (X)", value=st.session_state.room["width"], step=10)
    st.session_state.room["depth"] = st.number_input("房間深度 (Y)", value=st.session_state.room["depth"], step=10)
    st.session_state.room["height"] = st.number_input("樓層高度 (Z)", value=st.session_state.room["height"], step=10)

with st.sidebar.expander("🧭 八方坐向設定 (東西南北交叉線)", expanded=True):
    show_compass = st.checkbox("顯示坐向八方放射線", value=True)
    st.session_state.compass_center["x"] = st.number_input("放射中心點 X (cm)", value=st.session_state.compass_center["x"], step=5)
    st.session_state.compass_center["y"] = st.number_input("放射中心點 Y (cm)", value=st.session_state.compass_center["y"], step=5)
    compass_rotation = st.slider("羅盤旋轉角度 (度)", min_value=0, max_value=360, value=0, step=1)
    st.caption("💡 附圖方位為傳統坐向：**東在左、北在下、南在上、西在右**。")

with st.sidebar.expander("🔲 留白空間與窗戶尺寸", expanded=False):
    st.markdown("**右上留白區**")
    st.session_state.void_area["w"] = st.number_input("留白寬 (cm)", value=st.session_state.void_area["w"], step=5)
    st.session_state.void_area["d"] = st.number_input("留白深 (cm)", value=st.session_state.void_area["d"], step=5)
    st.session_state.void_area["x"] = st.number_input("留白 X 座標", value=st.session_state.void_area["x"], step=5)
    st.session_state.void_area["y"] = st.number_input("留白 Y 座標", value=st.session_state.void_area["y"], step=5)

with st.sidebar.expander("➕ 新增物件 / 家具", expanded=False):
    with st.form("add_obj_form"):
        new_name = st.text_input("物件名稱", value="置物架")
        new_w = st.number_input("寬度 W (cm)", value=60, min_value=1)
        new_d = st.number_input("深度 D (cm)", value=40, min_value=1)
        new_h = st.number_input("高度 H (cm, 留空或為0則預設 30cm)", value=0, min_value=0)
        new_x = st.number_input("X 座標 (cm)", value=100, min_value=0)
        new_y = st.number_input("Y 座標 (cm)", value=100, min_value=0)
        new_color = st.color_picker("物件顏色", "#FF9999")
        submitted = st.form_submit_button("新增至空間")
        if submitted:
            actual_h = new_h if new_h > 0 else 30
            st.session_state.objects.append({
                "id": f"obj_{len(st.session_state.objects)+1}",
                "name": new_name,
                "w": new_w, "d": new_d, "h": actual_h,
                "x": new_x, "y": new_y,
                "color": new_color,
                "text_color": "#FFFFFF",
                "label": f"{new_w}x{new_d}\n{new_name}"
            })
            st.success(f"已新增 {new_name}（高度：{actual_h} cm）！")
            st.rerun()

# --- 2D 平面圖渲染函數 ---
def render_2d_view():
    fig = go.Figure()
    rw = st.session_state.room["width"]
    rd = st.session_state.room["depth"]

    # 1. 地面藍色可使用底色
    fig.add_shape(
        type="rect",
        x0=20, y0=40, x1=rw+20, y1=rd+40,
        fillcolor="#5794CE",
        line=dict(color="#295B91", width=2),
        layer="below"
    )

    # 2. 留白區域 (白色方塊)
    v = st.session_state.void_area
    fig.add_shape(
        type="rect",
        x0=v["x"], y0=v["y"], x1=v["x"]+v["w"], y1=v["y"]+v["d"],
        fillcolor=v["color"],
        line=dict(color="#D0D0D0", width=1)
    )

    # 3. 窗戶 (底部黃色線條)
    for win in st.session_state.windows:
        fig.add_shape(
            type="rect",
            x0=win["x"], y0=win["y"], x1=win["x"]+win["w"], y1=win["y"]+win["d"],
            fillcolor=win["color"],
            line=dict(color="#D48806", width=2)
        )

    # 4. 繪製所有家具物件
    for obj in st.session_state.objects:
        x0, y0 = obj["x"], obj["y"]
        x1, y1 = x0 + obj["w"], y0 + obj["d"]
        fig.add_shape(
            type="rect",
            x0=x0, y0=y0, x1=x1, y1=y1,
            fillcolor=obj["color"],
            line=dict(color="#333333", width=1.5),
            layer="above"
        )
        # 標籤文字
        fig.add_annotation(
            x=(x0 + x1) / 2,
            y=(y0 + y1) / 2,
            text=obj["label"].replace("\n", "<br>"),
            showarrow=False,
            font=dict(color=obj.get("text_color", "#FFFFFF"), size=13, family="Microsoft JhengHei, Arial"),
            align="center"
        )

    # 5. 繪製八方坐向線 (東西南北放射線)
    if show_compass:
        cx = st.session_state.compass_center["x"]
        cy = st.session_state.compass_center["y"]
        # 附圖方位：東在左 (180°), 北在下 (270°), 南在上 (90°), 西在右 (0°)
        # 8方位線 (每45度一條線，穿過全房間)
        angles_deg = [0, 45, 90, 135, 180, 225, 270, 315]
        labels = {
            180: "東",
            270: "北",
            90: "南",
            0: "西"
        }
        line_len = max(rw, rd) * 1.5

        for ang in angles_deg:
            rad = np.deg2rad(ang + compass_rotation)
            ex = cx + line_len * np.cos(rad)
            ey = cy + line_len * np.sin(rad)
            fig.add_trace(go.Scatter(
                x=[cx, ex],
                y=[cy, ey],
                mode="lines",
                line=dict(color="#FFFFFF", width=3.5),
                hoverinfo="none",
                showlegend=False
            ))

        # 方位標註方塊 (如圖中的紫色標籤)
        # 東 (左方)
        fig.add_shape(
            type="rect",
            x0=-15, y0=cy-25, x1=25, y1=cy+25,
            fillcolor="#BA68C8", line=dict(color="#BA68C8")
        )
        fig.add_annotation(
            x=5, y=cy, text="東", showarrow=False,
            font=dict(color="#FFFFFF", size=24, family="KaiTi, SimHei, Microsoft JhengHei")
        )

        # 北 (下方)
        fig.add_shape(
            type="rect",
            x0=cx-25, y0=-15, x1=cx+25, y1=25,
            fillcolor="#BA68C8", line=dict(color="#BA68C8")
        )
        fig.add_annotation(
            x=cx, y=5, text="北", showarrow=False,
            font=dict(color="#FFFFFF", size=24, family="KaiTi, SimHei, Microsoft JhengHei")
        )

    # 畫布邊界與樣式設定
    fig.update_layout(
        plot_bgcolor="#0A0A0A",
        paper_bgcolor="#0A0A0A",
        width=1000,
        height=750,
        xaxis=dict(
            range=[-30, rw + 50],
            showgrid=False,
            zeroline=False,
            showticklabels=True,
            tickfont=dict(color="#777")
        ),
        yaxis=dict(
            range=[-30, rd + 60],
            showgrid=False,
            zeroline=False,
            showticklabels=True,
            tickfont=dict(color="#777"),
            scaleanchor="x",
            scaleratio=1
        ),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    return fig

# --- 3D 立體建模渲染函數 ---
def create_3d_box(x, y, z, dx, dy, dz, color, name):
    """生成 3D 長方體網格"""
    x_corners = [x, x+dx, x+dx, x, x, x+dx, x+dx, x]
    y_corners = [y, y, y+dy, y+dy, y, y, y+dy, y+dy]
    z_corners = [z, z, z, z, z+dz, z+dz, z+dz, z+dz]
    return go.Mesh3d(
        x=x_corners, y=y_corners, z=z_corners,
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color,
        opacity=0.9,
        flatshading=True,
        name=name,
        hoverinfo="name"
    )

def render_3d_view():
    fig = go.Figure()
    rw = st.session_state.room["width"]
    rd = st.session_state.room["depth"]

    # 地板網格
    fig.add_trace(go.Mesh3d(
        x=[20, rw+20, rw+20, 20],
        y=[40, 40, rd+40, rd+40],
        z=[0, 0, 0, 0],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color="#5794CE", opacity=0.7, name="地板"
    ))

    # 留白區域 (厚度為 0 的白色墊面或凸起台度)
    v = st.session_state.void_area
    fig.add_trace(go.Mesh3d(
        x=[v["x"], v["x"]+v["w"], v["x"]+v["w"], v["x"]],
        y=[v["y"], v["y"], v["y"]+v["d"], v["y"]+v["d"]],
        z=[0.5, 0.5, 0.5, 0.5],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color="#FFFFFF", opacity=1.0, name="留白處"
    ))

    # 渲染所有家具物件立體幾何
    for obj in st.session_state.objects:
        h = obj.get("h", 30)
        h = h if h > 0 else 30
        box = create_3d_box(
            x=obj["x"], y=obj["y"], z=0,
            dx=obj["w"], dy=obj["d"], dz=h,
            color=obj["color"],
            name=f"{obj['name']} ({obj['w']}x{obj['d']}x{h}cm)"
        )
        fig.add_trace(box)

    # 3D 八方坐向線
    if show_compass:
        cx = st.session_state.compass_center["x"]
        cy = st.session_state.compass_center["y"]
        line_len = max(rw, rd) * 1.2
        for ang in [0, 45, 90, 135, 180, 225, 270, 315]:
            rad = np.deg2rad(ang + compass_rotation)
            ex = cx + line_len * np.cos(rad)
            ey = cy + line_len * np.sin(rad)
            fig.add_trace(go.Scatter3d(
                x=[cx, ex], y=[cy, ey], z=[5, 5],
                mode="lines",
                line=dict(color="#FFFFFF", width=4),
                name="坐向線",
                hoverinfo="none",
                showlegend=False
            ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="寬度 X (cm)", backgroundcolor="#111", gridcolor="#333"),
            yaxis=dict(title="深度 Y (cm)", backgroundcolor="#111", gridcolor="#333"),
            zaxis=dict(title="高度 Z (cm)", backgroundcolor="#111", gridcolor="#333", range=[0, st.session_state.room["height"]]),
            aspectmode="data"
        ),
        paper_bgcolor="#0A0A0A",
        margin=dict(l=0, r=0, t=10, b=0),
        height=750
    )
    return fig

# --- 主展示區 ---
st.title("🛏️ 空間平面與 3D 視覺化配置系統")
st.caption("支援長寬高公分（cm）設定、預設高度 30cm、留白與窗戶劃分、八方坐向線條。")

col1, col2 = st.columns([3.5, 1.5])

with col1:
    if view_mode == "2D 平面配置圖":
        fig_2d = render_2d_view()
        st.plotly_chart(fig_2d, use_container_width=True)
    else:
        fig_3d = render_3d_view()
        st.plotly_chart(fig_3d, use_container_width=True)

with col2:
    st.subheader("📋 物件清單與微調")
    df_data = []
    for i, obj in enumerate(st.session_state.objects):
        df_data.append({
            "名稱": obj["name"],
            "寬 (W)": obj["w"],
            "深 (D)": obj["d"],
            "高 (H)": obj["h"],
            "X 軸": obj["x"],
            "Y 軸": obj["y"]
        })
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🗑️ 刪除或重置物件")
    del_target = st.selectbox("選擇要刪除的物件", options=[obj["name"] for obj in st.session_state.objects])
    if st.button("刪除所選物件"):
        st.session_state.objects = [o for o in st.session_state.objects if o["name"] != del_target]
        st.success(f"已刪除 {del_target}")
        st.rerun()

    if st.button("🔄 重置為附圖原始預設配置"):
        st.session_state.objects = [dict(item) for item in DEFAULT_OBJECTS]
        st.session_state.room = DEFAULT_ROOM.copy()
        st.session_state.compass_center = {"x": 260, "y": 200}
        st.session_state.void_area = DEFAULT_VOID.copy()
        st.session_state.windows = [dict(item) for item in DEFAULT_WINDOWS]
        st.rerun()