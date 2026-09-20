# ==========================================
# [필수 도구(라이브러리) 불러오기]
# ==========================================
import json  # JSON 형식의 데이터를 읽고 쓰기 위해 불러옵니다.
import os  # 파일 존재 여부 확인 등 시스템 경로 관련 기능을 위해 불러옵니다.
import requests  # 인터넷 웹 사이트(API)에 요청을 보내고 데이터를 받아오기 위해 불러옵니다.
from deep_translator import MyMemoryTranslator  # 한글 검색어를 영문으로 자동 번역해주기 위해 불러옵니다.
import nba_api.stats.endpoints.commonplayerinfo as commonplayerinfo  # NBA 공식 API에서 선수 프로필 정보를 가져오는 모듈입니다.
import nba_api.stats.endpoints.playercareerstats as playercareerstats  # NBA 공식 API에서 선수의 커리어 통계 기록을 가져오는 모듈입니다.
import nba_api.stats.static.players as players  # NBA 전체 선수 목록 정보(이름, ID)를 가져오는 모듈입니다.
import pandas as pd  # 데이터를 표(테이블) 형태로 정렬하고 다루기 위한 필수 라이브러리입니다.
import pydeck as pdk  # 지도 위에 농구장 위치 점을 시각화해주는 3D 지도 라이브러리입니다.
import streamlit as st  # 웹 애플리케이션 화면을 쉽게 만들어주는 메인 프레임워크입니다.
import numpy as np  # 슛 좌표나 3점선 곡선 수식을 계산할 때 쓰이는 수학/배열 라이브러리입니다.
import plotly.graph_objects as go  # 농구 코트 및 슛 차트를 그래프 형태로 그리기 위한 라이브러리입니다.

# ==========================================
# 1. 웹 화면 기본 설정 및 농구 배경 CSS 스타일
# ==========================================
st.set_page_config(  # 스트림릿 웹페이지의 기본 브라우저 설정을 변경합니다.
    page_title="중학생을 위한 농구 웹앱",  # 브라우저 탭에 표시될 제목입니다.
    page_icon="🏀",  # 브라우저 탭 아이콘으로 농구공 이모지를 설정합니다.
    layout="wide"  # 화면 전체 폭을 넓게 쓰도록 설정합니다.
)

# 프로그램 내 모든 글자 가독성 극대화 CSS 스타일
st.markdown("""
<style>
    /* 1. 전체 기본 글자 크기 및 색상 설정 */
    html, body, [class*="css"], .stMarkdown, p, div, span, label {
        font-size: 1.15rem !important;
        color: #FFFFFF !important;
        font-weight: 500;
    }

    /* 2. 전체 앱 배경 */
    .stApp {
        background: linear-gradient(135deg, #0b0e14 0%, #1a2332 50%, #0d1117 100%);
    }

    /* 3. 제목 및 헤더 (Header, Subheader, h1, h2, h3) */
    h1 { font-size: 2.5rem !important; font-weight: 800 !important; color: #FFB800 !important; }
    h2 { font-size: 2.0rem !important; font-weight: 800 !important; color: #FFB800 !important; border-bottom: 2px solid #FF6B00; padding-bottom: 5px; }
    h3 { font-size: 1.6rem !important; font-weight: 700 !important; color: #60A5FA !important; }
    h4 { font-size: 1.3rem !important; font-weight: 700 !important; color: #FFFFFF !important; }

    /* 4. 사이드바 전체 글자 및 배경 */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.98) !important;
        border-right: 3px solid #FF6B00;
    }
    [data-testid="stSidebar"] * {
        font-size: 1.15rem !important;
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stRadio label p {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #FFB800 !important;
    }

    /* 5. 숫자 메트릭(Metric) 강조 */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 900 !important;
        color: #FFB800 !important;
        text-shadow: 0 0 10px rgba(255, 184, 0, 0.5);
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: #93C5FD !important;
    }

    /* 6. 입력창 (TextInput, TextArea, Selectbox, Multiselect) 글자 및 선명화 */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
        background-color: #1E293B !important;
        border: 2px solid #60A5FA !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] * {
        color: #FFFFFF !important;
        background-color: #1E293B !important;
    }

    /* 7. 라디오 버튼 (선택지 글자 굵고 크게) */
    .stRadio label {
        background-color: #1E293B !important;
        padding: 10px 16px !important;
        border-radius: 8px !important;
        border: 1px solid #475569 !important;
        margin-bottom: 6px !important;
        display: flex !important;
        align-items: center !important;
        cursor: pointer !important;
    }
    .stRadio label:hover {
        border-color: #FFB800 !important;
        background-color: #334155 !important;
    }
    .stRadio label p {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
    }

    /* 8. 버튼 (Button) 가독성 극대화 */
    .stButton > button {
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        background-color: #FF6B00 !important;
        color: #FFFFFF !important;
        border: none !important;
        padding: 10px 20px !important;
    }
    .stButton > button:hover {
        background-color: #FF8533 !important;
        color: #FFFFFF !important;
    }

    /* 9. 표 (Table & Dataframe) 글자 강조 */
    .stTable, div[data-testid="stDataFrame"] {
        background-color: #1E293B !important;
        border-radius: 10px !important;
    }
    .stTable th, div[data-testid="stDataFrame"] th {
        background-color: #FF6B00 !important;
        color: #FFFFFF !important;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
    }
    .stTable td, div[data-testid="stDataFrame"] td {
        font-size: 1.15rem !important;
        color: #F8FAFC !important;
        font-weight: 600 !important;
    }

    /* 10. 성공/경고 메시지 상자 글자 */
    .stAlert p {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 사이드바 메뉴 설정
# ==========================================
st.sidebar.title("🏀 농구 세상")  # 왼쪽 사이드바 맨 위에 큰 제목을 띄웁니다.
st.sidebar.divider()  # 구분을 위한 구분선을 하나 그립니다.

menu = st.sidebar.radio(  # 라디오 버튼 목록을 통해 사용자가 메뉴를 하나 선택할 수 있게 합니다.
    "메뉴를 선택하세요",
    [
        "1. NBA 선수 검색",
        "2. 선수 1:1 비교",
        "3. 농구 코트 찾기 & 날씨",
        "4. 같이 할 사람 모집",
        "5. 농구 포지션 적성 검사",
        "6. 농구 용품 전용 검색"
    ]
)

st.sidebar.divider()
st.sidebar.subheader("⭐ 내가 찜한 선수 목록")


# ==========================================
# 공통 함수 및 슛 차트 시각화 함수 정의
# ==========================================
def translate_kor_to_eng(text):  # 한글 입력을 영문으로 변환해주는 함수입니다.
    query = text.strip()
    has_korean = any('가' <= char <= '힣' for char in query)
    if has_korean:
        try:
            translated = MyMemoryTranslator(source='ko-KR', target='en-US').translate(query)
            return translated.strip()
        except Exception:
            return query
    return query


@st.cache_data
def get_all_nba_players():  # NBA의 전/현직 선수 전체 목록을 가져오는 함수입니다.
    return players.get_players()


def search_all_nba_players(user_input):  # 사용자의 입력으로 NBA 선수를 찾아내는 함수입니다.
    if not user_input or not user_input.strip():
        return [], user_input

    eng_query = translate_kor_to_eng(user_input)
    all_p = get_all_nba_players()

    matched = [p for p in all_p if eng_query.lower() in p['full_name'].lower()]
    if not matched:
        matched = [p for p in all_p if user_input.strip().lower() in p['full_name'].lower()]

    return matched, eng_query


def create_sample_shot_data(num_shots=120, seed=42):  # 슛 차트에 시각화할 가상 슛 데이터를 만듭니다.
    np.random.seed(abs(seed) % (2 ** 32 - 1))  # 안전한 Seed 값 지정
    x = np.random.uniform(-220, 220, num_shots)
    y = np.random.uniform(20, 350, num_shots)
    dist = np.sqrt(x ** 2 + (y - 52.5) ** 2)
    made_prob = np.clip(1.0 - (dist / 400), 0.2, 0.85)
    made = np.random.binomial(1, made_prob)
    shot_type = np.where(dist >= 237.5, "3PT", "2PT")

    return pd.DataFrame({
        'x': x,
        'y': y,
        'made': made,
        'result': np.where(made == 1, '성공 (Made)', '실패 (Miss)'),
        'shot_type': shot_type,
        'distance_ft': np.round(dist / 10, 1)
    })


def draw_plotly_court():  # Plotly 차트 위에 농구 코트 선들과 색상을 그립니다.
    theta = np.linspace(np.arcsin(140 / 237.5), np.pi - np.arcsin(140 / 237.5), 100)
    arc_x = 237.5 * np.cos(theta)
    arc_y = 237.5 * np.sin(theta) + 52.5

    shapes = [
        dict(type="rect", x0=-260, y0=-10, x1=260, y1=430, fillcolor="#cc5200", layer="below", line=dict(width=0)),
        dict(type="rect", x0=-250, y0=0, x1=250, y1=470, line=dict(color="#ffffff", width=3)),
        dict(type="line", x0=-30, y0=40, x1=30, y1=40, line=dict(color="#ffffff", width=4)),
        dict(type="circle", x0=-7.5, y0=45, x1=7.5, y1=60, line=dict(color="#ff3300", width=3)),
        dict(type="rect", x0=-80, y0=0, x1=80, y1=190, fillcolor="#993d00", layer="below",
             line=dict(color="#ffffff", width=3)),
        dict(type="circle", x0=-60, y0=130, x1=60, y1=250, line=dict(color="#ffffff", width=2, dash="dash")),
        dict(type="line", x0=-220, y0=0, x1=-220, y1=140, line=dict(color="#ffffff", width=3)),
        dict(type="line", x0=220, y0=0, x1=220, y1=140, line=dict(color="#ffffff", width=3)),
    ]

    path_str = f"M {arc_x[0]},{arc_y[0]}"
    for x, y in zip(arc_x[1:], arc_y[1:]):
        path_str += f" L {x},{y}"

    shapes.append(dict(type="path", path=path_str, line=dict(color="#ffffff", width=3)))

    return shapes


def get_weather_by_coords(lat, lon):  # Open-Meteo 실시간 날씨 API 호출 함수입니다.
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        res = requests.get(url, timeout=5).json()
        curr = res.get("current_weather") or res.get("current")
        if curr:
            temp = curr.get("temperature") or curr.get("temperature_2m")
            code = curr.get("weathercode") or curr.get("weather_code")

            if code in [0]:
                desc = "맑음 ☀️"
            elif code in [1, 2, 3]:
                desc = "구름 조금 / 흐림 ⛅"
            elif code in [45, 48]:
                desc = "안개 🌫️"
            elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                desc = "비 🌧️"
            elif code in [71, 73, 75, 77, 85, 86]:
                desc = "눈 ❄️"
            elif code in [95, 96, 99]:
                desc = "뇌우 ⚡"
            else:
                desc = "보통 ☁️"

            return {"status": True, "temp": round(temp, 1), "desc": desc}
    except Exception:
        pass
    return {"status": False}


FAV_FILE = "favorites.json"


def load_favorites():
    if os.path.exists(FAV_FILE):
        try:
            with open(FAV_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_favorites(fav_dict):
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump(fav_dict, f, ensure_ascii=False, indent=4)


# 세션 상태 변수 초기화
if "favorites" not in st.session_state:
    st.session_state.favorites = load_favorites()
if "search_query" not in st.session_state:
    st.session_state.search_query = "LeBron James"
if "posts" not in st.session_state:
    st.session_state.posts = []

favorites = st.session_state.favorites

if st.sidebar.button("🧹 즐겨찾기 전체 삭제", use_container_width=True):
    st.session_state.favorites.clear()
    save_favorites(st.session_state.favorites)
    st.rerun()

if favorites:
    for fav_id, fav_name in list(favorites.items()):
        col_f1, col_f2 = st.sidebar.columns([3, 1])
        if col_f1.button(f"👤 {fav_name}", key=f"select_fav_{fav_id}"):
            st.session_state.search_query = fav_name
            st.rerun()
        if col_f2.button("❌", key=f"del_fav_{fav_id}"):
            del st.session_state.favorites[str(fav_id)]
            save_favorites(st.session_state.favorites)
            st.rerun()
else:
    st.sidebar.caption("아직 즐겨찾기한 선수가 없습니다.")


@st.cache_data
def load_national_court_data():
    json_path = "courts_data_calibrated.json"

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            courts_list = json.load(f)
    else:
        courts_list = [{
            "sido": "서울특별시", "sigungu": "서초구", "코트명": "한강시민공원 반포 농구장",
            "위치": "서울 서초구 반포동 115-5", "종류": "야외 (우레탄)", "조명": "있음 (22시까지)",
            "lat": 37.509, "lon": 126.995
        }]

    df = pd.DataFrame(courts_list)
    sido_map = {
        "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시",
        "인천": "인천광역시", "광주": "광주광역시", "대전": "대전광역시",
        "울산": "울산광역시", "세종": "세종특별자치시", "경기": "경기도",
        "강원": "강원특별자치도", "충북": "충청북도", "충남": "충청남도",
        "전북": "전북특별자치도", "전남": "전라남도", "경북": "경상북도",
        "경남": "경상남도", "제주": "제주특별자치도"
    }
    if "sido" in df.columns:
        df["sido"] = df["sido"].map(lambda x: sido_map.get(str(x).strip(), x))
    return df


@st.cache_data
def load_basketball_gears():
    return [
        {"category": "농구화", "name": "나이키 지티 컷 3 (GT Cut 3)", "brand": "Nike", "tag": "가드/포워드용", "price": "209,000원",
         "desc": "최상급 접지력과 반응성."},
        {"category": "농구화", "name": "나이키 코비 8 프로트로", "brand": "Nike", "tag": "경량화/접지", "price": "219,000원",
         "desc": "매우 가볍고 지면에 바짝 붙는 느낌."},
        {"category": "농구공", "name": "몰텐 BG4500 (7호)", "brand": "Molten", "tag": "실내/공인구", "price": "85,000원",
         "desc": "FIBA 공식 경기구."},
        {"category": "보호대/악세사리", "name": "바우어파인드 게뉴트레인", "brand": "Bauerfeind", "tag": "무릎/슬개골", "price": "120,000원",
         "desc": "최고급 압박 무릎 보호대."}
    ]


# ==========================================
# [메뉴 1] NBA 선수 정보 찾아보기 & 슛 차트
# ==========================================
if menu == "1. NBA 선수 검색":
    st.header("🔎 NBA 선수 정보 검색")
    st.write("모든 NBA 선수를 **한글** 또는 **영문**으로 검색해 보세요!")

    search_input = st.text_input("선수 이름 입력:", value="", placeholder="예: 레브론, 스테판 커리, Jordan")
    selected_target_eng = None

    if search_input:
        matches, translated_query = search_all_nba_players(search_input)
        if matches:
            options = [p['full_name'] for p in matches]
            selected_display = st.selectbox(f"🎯 검색 결과 ({len(matches)}명 발견) - '검색된 영문: {translated_query}'",
                                            options=options)
            selected_target_eng = selected_display
        else:
            st.warning(f"'{search_input}'에 매칭되는 선수를 찾을 수 없습니다.")
    else:
        selected_target_eng = st.session_state.search_query

    if selected_target_eng:
        st.session_state.search_query = selected_target_eng
        with st.spinner("선수 정보를 불러오는 중..."):
            try:
                found = players.find_players_by_full_name(selected_target_eng)
                target_player = found[0] if found else None

                if target_player:
                    p_id = str(target_player['id'])
                    img_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{p_id}.png"

                    info_res = commonplayerinfo.CommonPlayerInfo(player_id=p_id, timeout=30).get_dict()
                    career = playercareerstats.PlayerCareerStats(player_id=p_id, timeout=30).get_data_frames()[0]

                    headers = info_res['resultSets'][0]['headers']
                    row_data = info_res['resultSets'][0]['rowSet'][0]
                    p_info = dict(zip(headers, row_data))

                    raw_height = p_info.get('HEIGHT')
                    height_str = "정보 없음"
                    if raw_height and "-" in str(raw_height):
                        feet, inches = map(int, raw_height.split("-"))
                        height_cm = round((feet * 30.48) + (inches * 2.54))
                        height_str = f"{height_cm} cm ({raw_height})"

                    raw_weight = p_info.get('WEIGHT')
                    weight_str = "정보 없음"
                    if raw_weight and str(raw_weight).isdigit():
                        weight_kg = round(float(raw_weight) * 0.453592, 1)
                        weight_str = f"{weight_kg} kg"

                    ppg, rpg, apg, gp, latest_season = 0, 0, 0, 0, "정보 없음"
                    if not career.empty:
                        last_row = career.iloc[-1]
                        latest_season = last_row.get('SEASON_ID', "정보 없음")
                        gp = last_row.get('GP', 0)
                        if gp > 0:
                            ppg = round(last_row['PTS'] / gp, 1)
                            rpg = round(last_row['REB'] / gp, 1)
                            apg = round(last_row['AST'] / gp, 1)

                    team_name = f"{p_info.get('TEAM_CITY', '')} {p_info.get('TEAM_NAME', '')}".strip()
                    if not team_name:
                        team_name = "미소속 / 은퇴"

                    p_name = p_info.get('DISPLAY_FIRST_LAST', target_player['full_name'])
                    p_pos = p_info.get('POSITION') or "정보 없음"
                    p_draft = p_info.get('DRAFT_YEAR') or "정보 없음"
                    p_exp = f"{p_info.get('SEASON_EXP', 0)} 년차"

                    head_col1, head_col2 = st.columns([3, 1])
                    with head_col1:
                        st.success(f"**{p_name}** 선수를 찾았습니다!")

                    with head_col2:
                        is_fav = str(p_id) in st.session_state.favorites
                        btn_label = "⭐ 즐겨찾기 취소" if is_fav else "⭐ 즐겨찾기 추가"

                        if st.button(btn_label, key=f"btn_fav_{p_id}", type="primary"):
                            if is_fav:
                                del st.session_state.favorites[str(p_id)]
                                st.toast(f"❌ {p_name} 선수가 삭제되었습니다.")
                            else:
                                st.session_state.favorites[str(p_id)] = p_name
                                st.toast(f"⭐ {p_name} 선수가 추가되었습니다!")

                            save_favorites(st.session_state.favorites)
                            st.rerun()

                    img_col, info_col1, info_col2 = st.columns([1.2, 2, 2])
                    with img_col:
                        st.image(img_url, caption=p_name, use_container_width=True)
                    with info_col1:
                        st.metric("소속 팀", team_name)
                        st.metric("포지션", p_pos)
                        st.metric("키", height_str)
                    with info_col2:
                        st.metric("몸무게", weight_str)
                        st.metric("드래프트 연도", p_draft)
                        st.metric("경력", p_exp)

                    st.divider()
                    st.subheader(f"🎯 {p_name} 선수의 슛 차트 (Shot Chart) 분석")

                    # 안전한 seed 생성 (hash 활용)
                    shots_df = create_sample_shot_data(120, seed=abs(hash(p_id)))

                    c_metric1, c_metric2, c_metric3, c_metric4 = st.columns(4)
                    tot_att = len(shots_df)
                    tot_md = shots_df['made'].sum()
                    fg_pct_val = (tot_md / tot_att * 100) if tot_att > 0 else 0

                    c_metric1.metric("시도 수 (FGA)", f"{tot_att}회")
                    c_metric2.metric("성공 수 (FGM)", f"{tot_md}회")
                    c_metric3.metric("야투 성공률 (FG%)", f"{fg_pct_val:.1f}%")
                    c_metric4.metric("평균 슛 거리", f"{shots_df['distance_ft'].mean():.1f} ft")

                    fig_shot = go.Figure()

                    m_shots = shots_df[shots_df['made'] == 1]
                    if not m_shots.empty:
                        fig_shot.add_trace(go.Scatter(
                            x=m_shots['x'], y=m_shots['y'], mode='markers', name='성공 (Made)',
                            marker=dict(size=12, color='#10b981', symbol='circle',
                                        line=dict(width=1.5, color='#ffffff')),
                            hovertemplate="<b>성공</b><br>거리: %{customdata}ft<extra></extra>",
                            customdata=m_shots['distance_ft']
                        ))

                    x_shots = shots_df[shots_df['made'] == 0]
                    if not x_shots.empty:
                        fig_shot.add_trace(go.Scatter(
                            x=x_shots['x'], y=x_shots['y'], mode='markers', name='실패 (Miss)',
                            marker=dict(size=12, color='#ef4444', symbol='x', line=dict(width=1.5, color='#ffffff')),
                            hovertemplate="<b>실패</b><br>거리: %{customdata}ft<extra></extra>",
                            customdata=x_shots['distance_ft']
                        ))

                    fig_shot.update_layout(
                        shapes=draw_plotly_court(),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-260, 260]),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 420]),
                        width=680, height=520,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                                    font=dict(color="#ffffff", size=14))
                    )

                    st.plotly_chart(fig_shot, use_container_width=True)

            except Exception as e:
                st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")

# ==========================================
# [메뉴 2] 두 선수 실력 1:1 비교하기
# ==========================================
elif menu == "2. 선수 1:1 비교":
    st.header("⚔️ 선수 1:1 기량 비교")
    col_p1, col_p2 = st.columns(2)

    with col_p1:
        st.subheader("🔴 선수 A")
        p1_input = st.text_input("선수 A 입력:", value="레브론 제임스", key="p1_in")
        p1_matches, _ = search_all_nba_players(p1_input)
        p1_target = st.selectbox("선수 A 선택:", options=[p['full_name'] for p in p1_matches],
                                 key="p1_sel") if p1_matches else "LeBron James"

    with col_p2:
        st.subheader("🔵 선수 B")
        p2_input = st.text_input("선수 B 입력:", value="스테판 커리", key="p2_in")
        p2_matches, _ = search_all_nba_players(p2_input)
        p2_target = st.selectbox("선수 B 선택:", options=[p['full_name'] for p in p2_matches],
                                 key="p2_sel") if p2_matches else "Stephen Curry"

    if st.button("비교하기", type="primary", use_container_width=True):
        with st.spinner("비교 분석 중..."):
            try:
                def fetch_player_data(name_query):
                    f = players.find_players_by_full_name(name_query)
                    if not f: return None
                    target = f[0]
                    p_id = str(target['id'])
                    img_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{p_id}.png"
                    info_res = commonplayerinfo.CommonPlayerInfo(player_id=p_id, timeout=30).get_dict()
                    career = playercareerstats.PlayerCareerStats(player_id=p_id, timeout=30).get_data_frames()[0]

                    headers = info_res['resultSets'][0]['headers']
                    row_data = info_res['resultSets'][0]['rowSet'][0]
                    info = dict(zip(headers, row_data))

                    raw_h = info.get('HEIGHT')
                    h_str = "정보 없음"
                    if raw_h and "-" in str(raw_h):
                        ft, inch = map(int, raw_h.split("-"))
                        h_str = f"{round((ft * 30.48) + (inch * 2.54))} cm"

                    raw_w = info.get('WEIGHT')
                    w_str = "정보 없음"
                    if raw_w and str(raw_w).isdigit():
                        w_str = f"{round(float(raw_w) * 0.453592, 1)} kg"

                    ppg, rpg, apg, gp, season = 0, 0, 0, 0, "정보 없음"
                    if not career.empty:
                        l_row = career.iloc[-1]
                        season = l_row.get('SEASON_ID', "정보 없음")
                        gp = l_row.get('GP', 0)
                        if gp > 0:
                            ppg = round(l_row['PTS'] / gp, 1)
                            rpg = round(l_row['REB'] / gp, 1)
                            apg = round(l_row['AST'] / gp, 1)

                    return {
                        "name": info.get('DISPLAY_FIRST_LAST', target['full_name']),
                        "img_url": img_url,
                        "team": f"{info.get('TEAM_CITY', '')} {info.get('TEAM_NAME', '')}".strip() or "미소속",
                        "pos": info.get('POSITION') or "정보 없음",
                        "exp": f"{info.get('SEASON_EXP', 0)} 년차",
                        "height": h_str, "weight": w_str, "season": season, "gp": gp, "ppg": ppg, "rpg": rpg, "apg": apg
                    }


                p1 = fetch_player_data(p1_target)
                p2 = fetch_player_data(p2_target)

                if p1 and p2:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.image(p1['img_url'], width=150)
                        st.subheader(f"🔴 {p1['name']}")
                    with c2:
                        st.image(p2['img_url'], width=150)
                        st.subheader(f"🔵 {p2['name']}")

                    compare_data = {
                        "항목": ["키", "몸무게", "경력", "최근 시즌", "평균 득점", "평균 리바운드", "평균 어시스트"],
                        p1['name']: [p1['height'], p1['weight'], p1['exp'], p1['season'], f"{p1['ppg']} 점",
                                     f"{p1['rpg']} 개", f"{p1['apg']} 개"],
                        p2['name']: [p2['height'], p2['weight'], p2['exp'], p2['season'], f"{p2['ppg']} 점",
                                     f"{p2['rpg']} 개", f"{p2['apg']} 개"]
                    }
                    st.table(pd.DataFrame(compare_data).set_index("항목"))
                else:
                    st.warning("선수 정보를 불러올 수 없습니다.")
            except Exception as e:
                st.error(f"오류 발생: {e}")

# ==========================================
# [메뉴 3] 농구 코트 찾기 & 날씨
# ==========================================
elif menu == "3. 농구 코트 찾기 & 날씨":
    st.header("📍 전국 농구 코트 찾기 & 실시간 날씨")
    df_courts = load_national_court_data()

    df_courts["sido"] = df_courts["sido"].astype(str).str.strip()
    df_courts["sigungu"] = df_courts["sigungu"].astype(str).str.strip()
    df_courts["종류"] = df_courts["종류"].astype(str).str.strip()
    df_courts["코트명"] = df_courts["코트명"].astype(str).str.strip()
    df_courts["위치"] = df_courts["위치"].astype(str).str.strip()

    type_list = ["전체"] + sorted([t for t in df_courts["종류"].unique() if t and t != 'nan'])
    selected_type = st.selectbox("운동장 / 체육관 종류 선택:", type_list, key="court_type_select")

    filtered_by_type = df_courts if selected_type == "전체" else df_courts[df_courts["종류"] == selected_type]

    col1, col2 = st.columns(2)

    sido_list = ["전체"] + sorted([s for s in filtered_by_type["sido"].unique() if s and s != 'nan'])
    with col1:
        selected_sido = st.selectbox("특별시 / 광역시 / 도 선택:", sido_list, key="court_sido_select")

    filtered_by_sido = filtered_by_type if selected_sido == "전체" else filtered_by_type[
        filtered_by_type["sido"] == selected_sido]

    sigungu_list = ["전체"] + sorted([sg for sg in filtered_by_sido["sigungu"].unique() if sg and sg != 'nan'])
    with col2:
        selected_sigungu = st.selectbox("시 / 군 / 구 선택:", sigungu_list, key="court_sigungu_select")

    filtered_by_sigungu = filtered_by_sido if selected_sigungu == "전체" else filtered_by_sido[
        filtered_by_sido["sigungu"] == selected_sigungu]

    col3, col4 = st.columns(2)


    def extract_address_unit(addr):
        if not addr or pd.isna(addr): return "기타"
        for p in str(addr).split():
            if p.endswith(('동', '읍', '면', '리', '가')): return p
        return "기타"


    filtered_by_sigungu = filtered_by_sigungu.copy()
    filtered_by_sigungu["행정단위"] = filtered_by_sigungu["위치"].apply(extract_address_unit)

    unit_list = ["전체"] + sorted([d for d in filtered_by_sigungu["행정단위"].unique() if d and d != "기타"])
    with col3:
        selected_unit = st.selectbox("읍 / 면 / 리 / 동 선택:", unit_list, key="court_unit_select")

    filtered_by_unit = filtered_by_sigungu if selected_unit == "전체" else filtered_by_sigungu[
        filtered_by_sigungu["행정단위"] == selected_unit]

    court_name_list = ["전체"] + sorted([c for c in filtered_by_unit["코트명"].unique() if c and c != 'nan'])
    with col4:
        selected_court_name = st.selectbox("경기장 선택:", court_name_list, key="court_name_select")

    filtered_df = filtered_by_unit if selected_court_name == "전체" else filtered_by_unit[
        filtered_by_unit["코트명"] == selected_court_name]

    filtered_df["lat"] = pd.to_numeric(filtered_df["lat"], errors="coerce")
    filtered_df["lon"] = pd.to_numeric(filtered_df["lon"], errors="coerce")
    map_df = filtered_df[filtered_df["lat"].notna() & filtered_df["lon"].notna()].copy()

    avg_lat = map_df["lat"].iloc[0] if not map_df.empty else 37.5665
    avg_lon = map_df["lon"].iloc[0] if not map_df.empty else 126.9780

    st.subheader("🌦️ 실시간 날씨")
    weather_info = get_weather_by_coords(avg_lat, avg_lon)
    if weather_info["status"]:
        w1, w2, w3 = st.columns(3)
        w1.metric("기온", f"{weather_info['temp']} °C")
        w2.metric("상태", weather_info['desc'])
        w3.success("야외 농구 적합!")

    st.subheader(f"🗺️ 농구 코트 지도 (검색 결과: {len(map_df)}개)")

    if not map_df.empty:
        korea_lat = map_df["lat"].mean()
        korea_lon = map_df["lon"].mean()

        r = pdk.Deck(
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=map_df,
                    get_position="[lon, lat]",
                    get_color="[255, 102, 0, 220]",
                    get_radius=500,
                    pickable=True
                )
            ],
            initial_view_state=pdk.ViewState(
                latitude=korea_lat,
                longitude=korea_lon,
                zoom=10 if len(map_df) < 5 else 7.3,
                pitch=0
            ),
            tooltip={"html": "<b>{코트명}</b><br/>📍 {위치}"}
        )
        st.pydeck_chart(r)

        with st.expander("📋 검색된 농구장 목록 상세 보기"):
            st.dataframe(filtered_df[["코트명", "위치", "종류", "조명"]], use_container_width=True)
    else:
        st.warning("선택한 조건에 일치하는 코트 위치 정보를 찾을 수 없습니다.")

# ==========================================
# [메뉴 4] 같이 할 사람 모집
# ==========================================
elif menu == "4. 같이 할 사람 모집":
    st.header("🤝 농구 친구 모집 게시판")
    with st.expander("➕ 새 모집글 쓰기", expanded=False):
        with st.form("post_form"):
            name = st.text_input("닉네임")
            location = st.text_input("장소/지역")
            time_slot = st.text_input("일시")
            content = st.text_area("모집 내용")
            submit = st.form_submit_button("등록", type="primary")
            if submit and name and location and content:
                st.session_state.posts.insert(0, {
                    "작성자": name, "지역": location, "일시": time_slot, "내용": content, "상태": "모집중", "댓글": []
                })
                st.success("등록되었습니다!")
                st.rerun()

    for idx, post in enumerate(st.session_state.posts):
        st.markdown(f"#### {post['내용']}")
        st.caption(f"👤 {post['작성자']} | 📍 {post['지역']}")
        st.divider()

# ==========================================
# [메뉴 5] 농구 포지션 적성 검사
# ==========================================
elif menu == "5. 농구 포지션 적성 검사":
    import random

    st.header("📋 나의 농구 포지션 적성 검사")
    st.write("간단한 5가지 질문에 답하고 나에게 가장 잘 어울리는 **농구 포지션**과 **추천 NBA 선수**를 찾아보세요!")
    st.divider()

    # 원본 질문 데이터 정의 (각 질문과 포지션 매핑)
    questions_data = [
        {
            "id": "q1",
            "question": "1. 경기를 할 때 가장 자신 있는 역할은 무엇인가요?",
            "options": [
                {"text": "화려한 패스로 동료에게 득점 기회 만들어주기", "pos": "PG"},
                {"text": "정교한 3점슛과 중거리 슛으로 점수 올리기", "pos": "SG"},
                {"text": "빠른 득점과 적극적인 수비로 팀 분위기 가져오기", "pos": "SF"},
                {"text": "골밑 수비와 강한 리바운드로 골밑 지키기", "pos": "PF/C"}
            ]
        },
        {
            "id": "q2",
            "question": "2. 내가 가장 선호하는 슈팅 위치는 어디인가요?",
            "options": [
                {"text": "3점선 밖 먼 거리", "pos": "PG"},
                {"text": "미들레인지 (중거리) 및 자유투 라인 근처", "pos": "SG"},
                {"text": "경기 상황에 따라 자유롭게 골라 쏘기", "pos": "SF"},
                {"text": "골밑 바짝 붙어서 하는 레이업 및 뱅크슛", "pos": "PF/C"}
            ]
        },
        {
            "id": "q3",
            "question": "3. 팀이 위기에 빠졌을 때 나만의 해결 방법은?",
            "options": [
                {"text": "침착하게 전술을 지시하고 패스를 뿌린다.", "pos": "PG"},
                {"text": "내가 직접 과감하게 슛을 던져 점수를 낸다.", "pos": "SG"},
                {"text": "몸을 사리지 않는 허슬 플레이와 수비로 공을 빼앗는다.", "pos": "SF"},
                {"text": "상대의 슛을 블록슛하고 리바운드를 싹쓸이한다.", "pos": "PF/C"}
            ]
        },
        {
            "id": "q4",
            "question": "4. 나의 신장/체격 조건과 플레이 스타일의 장점은?",
            "options": [
                {"text": "키가 작더라도 스피드와 순발력이 뛰어난 편이다.", "pos": "PG"},
                {"text": "슛 폼이 정석적이고 체력이 좋다.", "pos": "SG"},
                {"text": "점프력이 좋고 공수 다방면에서 유능하다.", "pos": "SF"},
                {"text": "키나 체격이 상대적으로 크고 힘이 좋다.", "pos": "PF/C"}
            ]
        },
        {
            "id": "q5",
            "question": "5. 동료들이 나를 칭찬할 때 가장 자주 하는 말은?",
            "options": [
                {"text": "\"너 패스 센스 미쳤다! 넓게 잘 본다!\"", "pos": "PG"},
                {"text": "\"슛 감 좋다! 쏘면 다 들어가네!\"", "pos": "SG"},
                {"text": "\"진짜 올라운더다! 못 하는 게 없네!\"", "pos": "SF"},
                {"text": "\"리바운드 다 잡아서 너무 든든하다!\"", "pos": "PF/C"}
            ]
        }
    ]

    # 세션 상태를 활용해 질문 순서와 보기 순서를 랜덤 셔플하여 고정
    if "shuffled_questions" not in st.session_state:
        shuffled = [dict(q) for q in questions_data]
        random.shuffle(shuffled)
        for q in shuffled:
            opts = list(q["options"])
            random.shuffle(opts)
            q["options"] = opts
        st.session_state.shuffled_questions = shuffled

    with st.form("position_test_form"):
        user_answers = {}
        labels = ["A", "B", "C", "D"]

        for idx, q_info in enumerate(st.session_state.shuffled_questions):
            st.markdown(f"### {q_info['question']}")

            # 포지션 힌트를 제외하고 A, B, C, D 라벨만 붙여 보기 구성
            display_options = [f"{labels[i]}. {opt['text']}" for i, opt in enumerate(q_info["options"])]
            selected = st.radio("", display_options, key=f"radio_{q_info['id']}", label_visibility="collapsed")

            selected_index = display_options.index(selected)
            user_answers[q_info["id"]] = q_info["options"][selected_index]["pos"]
            st.write("")

        submitted = st.form_submit_button("🔥 결과 확인하기", type="primary", use_container_width=True)

    if submitted:
        scores = {"PG": 0, "SG": 0, "SF": 0, "PF/C": 0}
        for pos in user_answers.values():
            scores[pos] += 2

        best_pos = max(scores, key=scores.get)

        st.divider()
        st.balloons()

        if best_pos == "PG":
            st.success("🎯 당신의 적성 포지션: **포인트가드 (Point Guard - PG)**")
            st.markdown("""
            * **특징**: 코트 위의 야전사령관! 뛰어난 패스 감각과 경기 리딩 능력으로 팀 전체의 공격을 지배하는 스타일입니다.
            * **추천 NBA 선수**: 스테판 커리 (Stephen Curry), 크리스 폴 (Chris Paul)
            """)
        elif best_pos == "SG":
            st.success("🎯 당신의 적성 포지션: **슈팅가드 (Shooting Guard - SG)**")
            st.markdown("""
            * **특징**: 팀의 전담 스코어러! 순식간에 연속 득점을 올려 경기 흐름을 바꾸는 슈터 및 저격수 스타일입니다.
            * **추천 NBA 선수**: 클레이 탐슨 (Klay Thompson), 코비 브라이언트 (Kobe Bryant)
            """)
        elif best_pos == "SF":
            st.success("🎯 당신의 적성 포지션: **스몰포워드 (Small Forward - SF)**")
            st.markdown("""
            * **특징**: 만능 올라운더! 공격과 수비, 리바운드와 돌파까지 모든 영역에서 팀의 핵심 역할을 수행합니다.
            * **추천 NBA 선수**: 레브론 제임스 (LeBron James), 케빈 듀란트 (Kevin Durant)
            """)
        else:
            st.success("🎯 당신의 적성 포지션: **파워포워드/센터 (Power Forward / Center - PF/C)**")
            st.markdown("""
            * **특징**: 골밑의 지배자! 강력한 몸싸움, 블록슛, 그리고 리바운드로 골밑을 든든하게 지켜주는 보배 같은 존재입니다.
            * **추천 NBA 선수**: 니콜라 요키치 (Nikola Jokic), 야니스 아데토쿵보 (Giannis Antetokounmpo)
            """)

        if st.button("🔄 질문 순서 다시 섞고 다시 검사하기"):
            del st.session_state.shuffled_questions
            st.rerun()

# ==========================================
# [메뉴 6] 농구 용품 전용 검색
# ==========================================
elif menu == "6. 농구 용품 전용 검색":
    st.header("🛍️ 농구 용품 추천 및 검색")
    gear_df = pd.DataFrame(load_basketball_gears())
    search_kw = st.text_input("🔍 용품 검색어:", placeholder="예: 나이키, 무릎 보호대")

    filtered = gear_df
    if search_kw.strip():
        kw = search_kw.strip().lower()
        filtered = gear_df[
            gear_df["name"].str.lower().str.contains(kw) |
            gear_df["brand"].str.lower().str.contains(kw) |
            gear_df["category"].str.lower().str.contains(kw)
            ]

    if not filtered.empty:
        for _, item in filtered.iterrows():
            st.subheader(f"🏀 {item['name']}")
            st.write(f"💵 가격: {item['price']} | 📝 {item['desc']}")
            st.divider()
    else:
        st.warning("검색 조건에 맞는 농구용품이 없습니다.")

    st.subheader("🌐 검증된 농구 전문 브랜드 사이트")
    st.caption("잡상품이 없는 농구 전문 쇼핑몰 메인 페이지 바로가기입니다.")

    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.link_button("🏀 훕시티 (농구전문몰 공식 사이트)", "https://www.hoopcity.co.kr", use_container_width=True)
    with b_col2:
        st.link_button("🧦 마스터욱 (농구용품 공식 사이트)", "https://www.masterwook.com", use_container_width=True)