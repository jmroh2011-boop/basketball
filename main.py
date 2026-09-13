# ==========================================
# [필수 도구(라이브러리) 불러오기]
# ==========================================
import json  # json: 파이썬의 사전(dict) 데이터를 파일로 저장하거나 불러올 때 사용하는 데이터 변환 도구 라이브러리
import os  # os: 컴퓨터 파일 시스템 경로 확인, 파일 존재 여부(path.exists) 검사 등을 수행하는 시스템 제어 라이브러리
import requests  # requests: 인터넷 웹 주소(URL)로 HTTP 요청을 보내서 날씨 등 외부 API 데이터를 가져오는 통신 라이브러리
from deep_translator import MyMemoryTranslator  # MyMemoryTranslator: 한국어 선수 이름을 영문 이름으로 무료 번역해주는 번역기 라이브러리
import nba_api.stats.endpoints.commonplayerinfo as commonplayerinfo  # commonplayerinfo: NBA API에서 선수의 기본 신상정보(키, 몸무게, 소속팀 등)를 가져오는 모듈
import nba_api.stats.endpoints.playercareerstats as playercareerstats  # playercareerstats: NBA API에서 선수의 통산 시즌별 기록(득점, 리바운드 등)을 가져오는 모듈
import nba_api.stats.static.players as players  # players: NBA의 전체 선수 목록 데이터베이스를 가져오고 이름을 검색하는 모듈
import pandas as pd  # pd: 데이터를 표(Dataframe) 형태 구조로 깔끔하게 정리하고 필터링해주는 데이터 분석 라이브러리
import pydeck as pdk  # pdk: 지도 상에 농구장 위치를 입체적인 점(Scatterplot)으로 표시해주는 시각화 지도 라이브러리
import streamlit as st  # st: 파이썬 코드로 웹 화면 인터페이스(버튼, 입력창, 수치 등)를 쉽게 만들어주는 웹 앱 라이브러리

# ==========================================
# 1. 웹 화면 기본 모양 만들기
# ==========================================
st.set_page_config(  # Streamlit 웹 브라우저 탭의 제목, 아이콘, 레이아웃 너비를 설정하는 함수
    page_title="중학생을 위한 농구 웹앱",  # page_title: 브라우저 탭에 표시될 웹 페이지 제목 문자열
    page_icon="🏀",  # page_icon: 브라우저 탭 제목 옆에 표시될 이모지 아이콘
    layout="wide"  # layout: 웹 화면 너비를 넓은 화면 모드로 설정
)

# ==========================================
# 2. 사이드바 사용자 인증 설정 (구글 API 실시간 검증 적용)
# ==========================================
# ==========================================
# 2. 사이드바 사용자 인증 설정 (세션 기반 최적화 적용)
# ==========================================
st.sidebar.title("🏀 농구 세상")
st.sidebar.divider()

st.sidebar.subheader("🔑 사용자 인증 설정")

# 세션 상태 초기화 (입력 중 반복적인 구글 서버 호출 방지)
if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = False
if "api_key_msg" not in st.session_state:
    st.session_state.api_key_msg = ""
if "validated_key" not in st.session_state:
    st.session_state.validated_key = ""

user_api_key = st.sidebar.text_input(
    "Gemini API Key를 입력하세요",
    type="password",
    placeholder="Gemini API Key 입력 후 Enter",
    help="Google AI Studio에서 발급받은 API Key를 입력하세요."
)

# 구글 서버 검증 함수
def verify_gemini_key(key):
    if not key or not key.strip():
        return False, "API Key가 입력되지 않았습니다."
    try:
        from google import genai
        client = genai.Client(api_key=key.strip())
        # 가장 경량화된 테스트 호출
        client.models.generate_content(
            model='gemini-3.6-flash',
            contents='Hi'
        )
        return True, "✅ API Key 실시간 서버 승인 완료!"
    except Exception as e:
        return False, f"❌ 유효하지 않은 API Key입니다. (사유: {e})"

# [개선] 버튼 클릭 시 또는 새로운 Key 입력 후 엔터 시에만 1회 검증 실행
btn_check = st.sidebar.button("🔑 API Key 확인/저장", use_container_width=True)
key_changed = bool(user_api_key and user_api_key != st.session_state.validated_key)

if btn_check or key_changed:
    with st.sidebar.spinner("API Key 검증 중..."):
        is_valid, msg = verify_gemini_key(user_api_key)
        st.session_state.api_key_valid = is_valid
        st.session_state.api_key_msg = msg
        st.session_state.validated_key = user_api_key

# 검증 결과 출력 및 메인 조건 판단용 변수 매핑
is_api_key_valid = st.session_state.api_key_valid
api_key_msg = st.session_state.api_key_msg

if not user_api_key:
    st.sidebar.warning("⚠️ API Key를 입력해 주세요.")
elif not is_api_key_valid:
    st.sidebar.error(api_key_msg)
else:
    st.sidebar.success(api_key_msg)

st.sidebar.divider()

# ==========================================
# 3. 메뉴판 설정
# ==========================================
menu = st.sidebar.radio(  # menu: 사용자가 사이드바 라디오 버튼에서 선택한 메뉴 이름을 문자열로 저장하는 변수
    "메뉴를 선택하세요",  # 라디오 버튼 그룹 상단 안내 라벨
    [  # 라디오 버튼으로 보여줄 메뉴 옵션들의 리스트
        "1. NBA 선수 검색",
        "2. 선수 1:1 비교",
        "3. 농구 코트 찾기 & 날씨",
        "4. AI 농구 코치 (Q&A)",
        "5. 같이 할 사람 모집",
        "6. 농구 용품 전용 검색"
    ]
)

st.sidebar.divider()  # 사이드바 가로 구획선 표시
st.sidebar.subheader("⭐ 내가 찜한 선수 목록")  # 사이드바에 '내가 찜한 선수' 소제목 표시

# ==========================================
# 공통 함수 정의
# ==========================================
def translate_kor_to_eng(text):  # text: 번역하고자 하는 사용자 입력 문자열 (예: "레브론")
    query = text.strip()  # query: 입력 문자열의 앞뒤 공백을 제거한 변수
    has_korean = any('가' <= char <= '힣' for char in query)  # has_korean: 입력된 문자에 한글이 포함되어 있는지 여부(True/False)
    if has_korean:  # 한글이 포함되어 있다면 번역 진행
        try:  # 번역 중 발생할 수 있는 에러 예외처리 구문
            translated = MyMemoryTranslator(source='ko-KR', target='en-US').translate(query)  # translated: 한글을 영문으로 번역한 결과 문자열
            return translated.strip()  # 번역된 영문 텍스트의 공백을 제거하여 반환
        except Exception:  # 번역 서버 통신 문제 등 에러 발생 시
            return query  # 번역 실패 시 원본 입력값 그대로 반환
    return query  # 한글이 없으면 원본 입력값 그대로 반환

@st.cache_data  # Streamlit 캐싱 데코레이터: 반복적으로 전체 선수 목록을 불러오지 않고 메모리에 저장해 속도 향상
def get_all_nba_players():  # NBA 전체 선수 목록을 가져오는 함수
    return players.get_players()  # NBA API에서 제공하는 전체 선수 리스트(dict 형태들의 list) 반환

def search_all_nba_players(user_input):  # user_input: 사용자가 검색창에 입력한 검색어
    if not user_input or not user_input.strip():  # 검색어가 비어있거나 공백뿐일 경우
        return [], user_input  # 빈 리스트와 입력값을 그대로 반환

    eng_query = translate_kor_to_eng(user_input)  # eng_query: 사용자 입력 한글을 영문으로 번역한 변수
    all_p = get_all_nba_players()  # all_p: get_all_nba_players()로 불러온 NBA 전체 선수 리스트

    matched = [p for p in all_p if eng_query.lower() in p['full_name'].lower()]  # matched: 번역된 영문 검색어가 풀네임에 포함된 선수 리스트
    if not matched:  # 번역된 영문으로 검색 결과가 없는 경우
        matched = [p for p in all_p if user_input.strip().lower() in p['full_name'].lower()]  # 번역 전 원본 입력값으로 다시 일치하는 선수 검색

    return matched, eng_query  # matched: 검색된 선수 리스트, eng_query: 번역된 영문 검색어 반환

def get_weather_by_coords(lat, lon):  # lat: 위도(latitude), lon: 경도(longitude) 수치값
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"  # url: Open-Meteo 날씨 API 요청 인터넷 주소 문자열
    try:  # 인터넷 통신 실패 등에 대비한 예외처리
        res = requests.get(url, timeout=5).json()  # res: Open-Meteo 서버에서 받아온 날씨 데이터(JSON -> 파이썬 dict)
        if "current_weather" in res:  # 응답 데이터 안에 현재 날씨 정보가 존재하는지 확인
            curr = res["current_weather"]  # curr: 현재 날씨 데이터가 들어있는 내부 사전(dict)
            temp = curr["temperature"]  # temp: 현재 기온 수치 (섭씨)
            code = curr["weathercode"]  # code: WMO 날씨 상태 코드 번호 (0: 맑음, 61: 비 등)

            if code in [0]: desc = "맑음 ☀️"  # desc: 날씨 코드 숫자를 사람이 읽기 쉬운 한글/이모지로 변환한 문자열
            elif code in [1, 2, 3]: desc = "구름 조금 / 흐림 ⛅"
            elif code in [45, 48]: desc = "안개 🌫️"
            elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: desc = "비 🌧️"
            elif code in [71, 73, 75, 77, 85, 86]: desc = "눈 ❄️"
            elif code in [95, 96, 99]: desc = "뇌우 ⚡"
            else: desc = "보통 ☁️"

            return {"status": True, "temp": round(temp, 1), "desc": desc}  # 날씨 조회 성공 시 상태, 반올림된 기온, 상태 설명 반환
    except Exception:  # 에러 발생 시
        pass  # 아무 작업도 하지 않고 넘어감
    return {"status": False}  # 날씨 조회 실패 시 status: False 반환

FAV_FILE = "favorites.json"  # FAV_FILE: 즐겨찾기 선수 데이터를 저장할 로컬 파일 이름

def load_favorites():  # 즐겨찾기 파일을 읽어오는 함수
    if os.path.exists(FAV_FILE):  # favorites.json 파일이 컴퓨터 경로에 존재하는지 확인
        try:  # 파일 읽기 에러 예외처리
            with open(FAV_FILE, "r", encoding="utf-8") as f:  # f: 열린 파일 객체
                return json.load(f)  # JSON 파일 내용을 파이썬 사전(dict) 구조로 읽어서 반환
        except Exception:  # 파일 손상 등의 에러 발생 시
            return {}  # 빈 사전 반환
    return {}  # 파일이 존재하지 않으면 빈 사전 반환

def save_favorites(fav_dict):  # fav_dict: 파일에 저장할 즐겨찾기 선수 사전 데이터
    with open(FAV_FILE, "w", encoding="utf-8") as f:  # f: 쓰기 모드로 열린 파일 객체
        json.dump(fav_dict, f, ensure_ascii=False, indent=4)  # fav_dict 데이터를 favorites.json에 한글 깨짐 없이 예쁘게 저장

if "favorites" not in st.session_state:  # Streamlit 세션 상태 메모리에 favorites 항목이 없는 경우 초기화
    st.session_state.favorites = load_favorites()  # 파일에서 저장된 즐겨찾기 목록을 가져와 세션에 저장
if "search_query" not in st.session_state:  # 세션 메모리에 search_query가 없는 경우
    st.session_state.search_query = "LeBron James"  # 기본 검색어로 "LeBron James" 설정
if "posts" not in st.session_state:  # 세션 메모리에 posts(게시글 리스트)가 없는 경우
    st.session_state.posts = []  # 빈 리스트로 초기화

favorites = st.session_state.favorites  # favorites: 세션 상태의 즐겨찾기 사전을 간결하게 쓰기 위한 변수

if st.sidebar.button("🧹 즐겨찾기 전체 삭제", use_container_width=True):  # 사이드바 전체 삭제 버튼 클릭 시
    st.session_state.favorites.clear()  # 즐겨찾기 사전 내용을 모두 비움
    save_favorites(st.session_state.favorites)  # 비워진 사전을 파일에도 반영하여 저장
    st.rerun()  # 웹 화면을 다시 불러와 업데이트

if favorites:  # 즐겨찾기 목록에 선수가 1명 이상 있는 경우
    for fav_id, fav_name in list(favorites.items()):  # fav_id: 선수의 NBA ID(키), fav_name: 선수의 이름(값)
        col_f1, col_f2 = st.sidebar.columns([3, 1])  # col_f1, col_f2: 사이드바 내부 3:1 비율의 2개 컬럼 변수
        if col_f1.button(f"👤 {fav_name}", key=f"select_fav_{fav_id}"):  # 선수 이름 버튼 클릭 시
            st.session_state.search_query = fav_name  # 해당 선수 이름을 검색어로 설정
            st.rerun()  # 화면 새로고침하여 해당 선수 정보 조회
        if col_f2.button("❌", key=f"del_fav_{fav_id}"):  # ❌ 삭제 버튼 클릭 시
            del st.session_state.favorites[str(fav_id)]  # 해당 ID 선수를 즐겨찾기 사전에서 삭제
            save_favorites(st.session_state.favorites)  # 변경사항 파일에 저장
            st.rerun()  # 화면 새로고침
else:  # 즐겨찾기한 선수가 없을 경우
    st.sidebar.caption("아직 즐겨찾기한 선수가 없습니다.")  # 사이드바에 작은 필기체로 안내문구 출력

@st.cache_data  # 전국 농구 코트 데이터 파일 캐싱
def load_national_court_data():  # 코트 데이터를 불러오는 함수
    json_path = "courts_data_calibrated.json"  # json_path: 농구장 데이터가 들어있는 파일 경로 문자열

    if os.path.exists(json_path):  # courts_data.json 파일이 존재하는지 검사
        with open(json_path, "r", encoding="utf-8") as f:  # f: 파일 객체
            courts_list = json.load(f)  # courts_list: 코트 정보들이 담긴 리스트 변수
    else:  # 파일이 없는 경우 기본 예시 코트 데이터 리스트 생성
        courts_list = [{
            "sido": "서울특별시", "sigungu": "서초구", "코트명": "한강시민공원 반포 농구장",
            "위치": "서울 서초구 반포동 115-5", "종류": "야외 (우레탄)", "조명": "있음 (22시까지)",
            "lat": 37.509, "lon": 126.995
        }]

    df = pd.DataFrame(courts_list)  # df: courts_list 데이터를 판다스 데이터프레임(표)으로 변환한 변수
    sido_map = {  # sido_map: 축약된 시/도 이름을 표준 정식 명칭으로 변경해주는 사전 변수
        "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시",
        "인천": "인천광역시", "광주": "광주광역시", "대전": "대전광역시",
        "울산": "울산광역시", "세종": "세종특별자치시", "경기": "경기도",
        "강원": "강원특별자치도", "충북": "충청북도", "충남": "충청남도",
        "전북": "전북특별자치도", "전남": "전라남도", "경북": "경상북도",
        "경남": "경상남도", "제주": "제주특별자치도"
    }
    if "sido" in df.columns:  # 데이터프레임 칼럼에 "sido"가 있는지 확인
        df["sido"] = df["sido"].map(lambda x: sido_map.get(str(x).strip(), x))  # sido 칼럼의 축약 명칭을 sido_map을 사용해 표준 명칭으로 치환
    return df  # 정돈된 코트 데이터프레임 반환

@st.cache_data  # 농구 용품 목록 데이터 캐싱
def load_basketball_gears():  # 추천 농구 용품 데이터를 불러오는 함수
    return [  # 추천 용품 정보가 담긴 사전(dict)들의 리스트 반환
        {"category": "농구화", "name": "나이키 지티 컷 3 (GT Cut 3)", "brand": "Nike", "tag": "가드/포워드용", "price": "209,000원", "desc": "최상급 접지력과 반응성."},
        {"category": "농구화", "name": "나이키 코비 8 프로트로", "brand": "Nike", "tag": "경량화/접지", "price": "219,000원", "desc": "매우 가볍고 지면에 바짝 붙는 느낌."},
        {"category": "농구공", "name": "몰텐 BG4500 (7호)", "brand": "Molten", "tag": "실내/공인구", "price": "85,000원", "desc": "FIBA 공식 경기구."},
        {"category": "보호대/악세사리", "name": "바우어파인드 게뉴트레인", "brand": "Bauerfeind", "tag": "무릎/슬개골", "price": "120,000원", "desc": "최고급 압박 무릎 보호대."}
    ]

# ==========================================
# 🔒 API Key 검문소 (실제 구글 서버 인증 결과로 판정)
# ==========================================
if not is_api_key_valid:  # 구글 서버 검증 결과 is_api_key_valid가 False(유효하지 않음)일 경우 실행
    st.error("🔒 **API Key가 올바르지 않거나 구글 서버 인증에 실패했습니다.**")  # 메인 화면에 에러 메세지 안내
    st.info("👈 왼쪽 사이드바에 본인의 **Gemini API Key**를 정확히 입력해 주세요.")  # 이용 안내 파란색 인포 박스 출력
    st.stop()  # 이후 아래의 모든 코드 실행을 즉시 중단(접근 차단 검문소 역할)

# ==========================================
# [메뉴 1] NBA 선수 정보 찾아보기
# ==========================================
if menu == "1. NBA 선수 검색":  # 메인 메뉴가 "1. NBA 선수 검색"일 때 동작
    st.header("🔎 NBA 선수 정보 검색")  # 메인 화면에 큰 헤더 제목 표시
    st.write("모든 NBA 선수를 **한글** 또는 **영문**으로 검색해 보세요!")  # 본문 안내 문구 출력

    search_input = st.text_input("선수 이름 입력:", value="", placeholder="예: 레브론, 스테판 커리, Jordan")  # search_input: 사용자가 입력한 검색어 변수
    selected_target_eng = None  # selected_target_eng: 최종 조회할 선수의 영문 풀네임 변수 (초기값 None)

    if search_input:  # 사용자가 검색창에 텍스트를 입력했을 경우
        matches, translated_query = search_all_nba_players(search_input)  # matches: 매칭된 선수 리스트, translated_query: 영문 번역 결과
        if matches:  # 매칭된 선수가 1명 이상 존재할 때
            options = [p['full_name'] for p in matches]  # options: 셀렉트박스에 보여줄 매칭된 선수들의 풀네임 리스트
            selected_display = st.selectbox(f"🎯 검색 결과 ({len(matches)}명 발견) - '검색된 영문: {translated_query}'", options=options)  # selected_display: 드롭다운에서 최종 선택한 선수 이름
            selected_target_eng = selected_display  # 선택한 이름을 최종 검색 대상으로 지정
        else:  # 일치하는 선수가 없을 경우
            st.warning(f"'{search_input}'에 매칭되는 선수를 찾을 수 없습니다.")  # 경고 문구 출력
    else:  # 검색창이 비어있을 때는 세션에 저장된 기본 검색어 사용
        selected_target_eng = st.session_state.search_query  # 기존에 저장되어 있던 search_query 적용

    if selected_target_eng:  # 최종 조회할 선수의 이름이 확정된 경우
        st.session_state.search_query = selected_target_eng  # 현재 선택된 선수를 세션 상태에 저장
        with st.spinner("선수 정보를 불러오는 중..."):  # 데이터를 가져오는 동안 로딩 스피너 애니메이션 표시
            try:  # API 데이터 수신 중 오류 대비 예외처리
                found = players.find_players_by_full_name(selected_target_eng)  # found: 해당 영문 이름으로 찾은 선수 데이터 리스트
                target_player = found[0] if found else None  # target_player: 찾은 선수 중 첫 번째 선수 정보 사전

                if target_player:  # 선수 정보가 정상 조회된 경우
                    p_id = str(target_player['id'])  # p_id: 선수의 고유 NBA ID 문자열 (예: "2544")
                    img_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{p_id}.png"  # img_url: NBA 공식 CDN의 선수 프로필 이미지 URL 주소

                    info_res = commonplayerinfo.CommonPlayerInfo(player_id=p_id, timeout=30).get_dict()  # info_res: NBA API에서 받아온 선수의 기본 신상정보 사전
                    career = playercareerstats.PlayerCareerStats(player_id=p_id, timeout=30).get_data_frames()[0]  # career: 선수의 커리어 통계 데이터프레임(표)

                    headers = info_res['resultSets'][0]['headers']  # headers: API 응답 결과 데이터의 항목 제목들(컬럼명 리스트)
                    row_data = info_res['resultSets'][0]['rowSet'][0]  # row_data: 실제 선수 정보 데이터의 값 리스트
                    p_info = dict(zip(headers, row_data))  # p_info: 컬럼명과 데이터를 1:1로 매핑하여 만든 선수 신상 사전

                    raw_height = p_info.get('HEIGHT')  # raw_height: 미국식 키 표현 문자열 (예: "6-9")
                    height_str = "정보 없음"  # height_str: 변환된 cm 단위 키 텍스트 변수
                    if raw_height and "-" in str(raw_height):  # 키 데이터가 피트-인치 형태일 때
                        feet, inches = map(int, raw_height.split("-"))  # feet: 피트 숫자, inches: 인치 숫자
                        height_cm = round((feet * 30.48) + (inches * 2.54))  # height_cm: 피트와 인치를 cm로 계산하여 반올림한 수치
                        height_str = f"{height_cm} cm ({raw_height})"  # cm와 원본 피트 수치를 조합한 결과 텍스트

                    raw_weight = p_info.get('WEIGHT')  # raw_weight: 미국식 파운드(lbs) 단위 몸무게 문자열
                    weight_str = "정보 없음"  # weight_str: 변환된 kg 단위 몸무게 텍스트 변수
                    if raw_weight and str(raw_weight).isdigit():  # 몸무게가 숫자로 제공되는 경우
                        weight_kg = round(float(raw_weight) * 0.453592, 1)  # weight_kg: 파운드를 kg으로 변환하여 소수점 첫째자리까지 반올림한 수치
                        weight_str = f"{weight_kg} kg"  # kg 수치 결과 텍스트

                    ppg, rpg, apg, gp, latest_season = 0, 0, 0, 0, "정보 없음"  # 통계 수치 변수 초기화 (득점, 리바운드, 어시스트, 경기수, 최근시즌)
                    if not career.empty:  # 커리어 기록 데이터프레임이 비어있지 않을 때
                        last_row = career.iloc[-1]  # last_row: 통계 표의 가장 최근 시즌(마지막 행) 데이터
                        latest_season = last_row.get('SEASON_ID', "정보 없음")  # latest_season: 최근 시즌 이름 (예: "2023-24")
                        gp = last_row.get('GP', 0)  # gp: 해당 시즌 출전 경기 수
                        if gp > 0:  # 출전 경기 수가 1경기 이상일 때 경기당 평균 기록 계산
                            ppg = round(last_row['PTS'] / gp, 1)  # ppg: 경기당 평균 득점 (Points Per Game)
                            rpg = round(last_row['REB'] / gp, 1)  # rpg: 경기당 평균 리바운드 (Rebounds Per Game)
                            apg = round(last_row['AST'] / gp, 1)  # apg: 경기당 평균 어시스트 (Assists Per Game)

                    team_name = f"{p_info.get('TEAM_CITY', '')} {p_info.get('TEAM_NAME', '')}".strip()  # team_name: 연고지와 팀명을 합친 전체 팀 이름 (예: "Los Angeles Lakers")
                    if not team_name:  # 팀 이름 정보가 비어있을 경우
                        team_name = "미소속 / 은퇴"  # 소속팀 없음 처리

                    p_name = p_info.get('DISPLAY_FIRST_LAST', target_player['full_name'])  # p_name: 화면에 표시할 선수의 최종 영문 성명
                    p_pos = p_info.get('POSITION') or "정보 없음"  # p_pos: 선수의 포지션 (예: "Forward")
                    p_draft = p_info.get('DRAFT_YEAR') or "정보 없음"  # p_draft: 드래프트 지명 연도
                    p_exp = f"{p_info.get('SEASON_EXP', 0)} 년차"  # p_exp: NBA 리그 경력 연수 텍스트

                    head_col1, head_col2 = st.columns([3, 1])  # head_col1, head_col2: 상단 영역을 3:1 비율로 나눈 컬럼 변수
                    with head_col1:  # 왼쪽 3 비율 컬럼
                        st.success(f"**{p_name}** 선수를 찾았습니다!")  # 검색 성공 초록색 박스 출력

                    with head_col2:  # 오른쪽 1 비율 컬럼 (즐겨찾기 버튼 위치)
                        is_fav = str(p_id) in st.session_state.favorites  # is_fav: 현재 선수가 이미 즐겨찾기에 등록되어 있는지 여부(True/False)
                        btn_label = "⭐ 즐겨찾기 취소" if is_fav else "⭐ 즐겨찾기 추가"  # btn_label: 즐겨찾기 여부에 따라 동적으로 변경되는 버튼 텍스트

                        if st.button(btn_label, key=f"btn_fav_{p_id}", type="primary"):  # 즐겨찾기 추가/취소 버튼 클릭 시
                            if is_fav:  # 이미 즐겨찾기에 있던 경우
                                del st.session_state.favorites[str(p_id)]  # 세션에서 제거
                                st.toast(f"❌ {p_name} 선수가 삭제되었습니다.")  # 하단 팝업 토스트 메세지 출력
                            else:  # 즐겨찾기에 없던 경우
                                st.session_state.favorites[str(p_id)] = p_name  # 세션 즐겨찾기에 선수의 ID와 이름을 새로 추가
                                st.toast(f"⭐ {p_name} 선수가 추가되었습니다!")  # 하단 팝업 토스트 메세지 출력

                            save_favorites(st.session_state.favorites)  # 변경된 즐겨찾기 사전을 favorites.json 파일에 저장
                            st.rerun()  # 화면을 새로고침하여 사이드바와 UI 업데이트

                    img_col, info_col1, info_col2 = st.columns([1.2, 2, 2])  # 상세 정보를 보여주기 위해 화면을 1.2 : 2 : 2 비율로 3개 컬럼 생성
                    with img_col:  # 첫 번째 컬럼 (이미지)
                        st.image(img_url, caption=p_name, use_container_width=True)  # 선수 프로필 이미지 출력
                    with info_col1:  # 두 번째 컬럼 (신상 정보)
                        st.metric("소속 팀", team_name)  # 팀 이름 강조 카드 출력
                        st.metric("포지션", p_pos)  # 포지션 강조 카드 출력
                        st.metric("키", height_str)  # 키 강조 카드 출력
                    with info_col2:  # 세 번째 컬럼 (기타 신상 정보)
                        st.metric("몸무게", weight_str)  # 몸무게 강조 카드 출력
                        st.metric("드래프트 연도", p_draft)  # 드래프트 연도 카드 출력
                        st.metric("경력", p_exp)  # 경력 연수 카드 출력
            except Exception as e:  # 통신 실패 등의 에러 발생 시
                st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")  # 에러 메세지 화면 출력

# ==========================================
# [메뉴 2] 두 선수 실력 1:1 비교하기
# ==========================================
elif menu == "2. 선수 1:1 비교":  # 메인 메뉴가 "2. 선수 1:1 비교"일 때 동작
    st.header("⚔️ 선수 1:1 기량 비교")  # 메뉴 헤더 출력
    col_p1, col_p2 = st.columns(2)  # 화면을 좌우 1:1 비율로 나눈 컬럼 변수 (선수 A / 선수 B 용)

    with col_p1:  # 좌측 선수 A 설정 컬럼
        st.subheader("🔴 선수 A")  # 서브 헤더
        p1_input = st.text_input("선수 A 입력:", value="레브론 제임스", key="p1_in")  # p1_input: 선수 A 검색창 입력값 변수
        p1_matches, _ = search_all_nba_players(p1_input)  # p1_matches: 입력값에 매칭되는 선수 리스트
        p1_target = st.selectbox("선수 A 선택:", options=[p['full_name'] for p in p1_matches], key="p1_sel") if p1_matches else "LeBron James"  # p1_target: 드롭다운에서 선택한 선수 A의 풀네임 변수

    with col_p2:  # 우측 선수 B 설정 컬럼
        st.subheader("🔵 선수 B")  # 서브 헤더
        p2_input = st.text_input("선수 B 입력:", value="스테판 커리", key="p2_in")  # p2_input: 선수 B 검색창 입력값 변수
        p2_matches, _ = search_all_nba_players(p2_input)  # p2_matches: 입력값에 매칭되는 선수 리스트
        p2_target = st.selectbox("선수 B 선택:", options=[p['full_name'] for p in p2_matches], key="p2_sel") if p2_matches else "Stephen Curry"  # p2_target: 드롭다운에서 선택한 선수 B의 풀네임 변수

    if st.button("비교하기", type="primary", use_container_width=True):  # "비교하기" 버튼 클릭 시 동작
        with st.spinner("비교 분석 중..."):  # 분석 중 로딩 스피너 애니메이션 표시
            try:  # 데이터 로딩 중 에러 예외처리
                def fetch_player_data(name_query):  # name_query: 조회할 선수의 영문 풀네임 문자열 매개변수
                    f = players.find_players_by_full_name(name_query)  # f: 선수 검색 결과 리스트
                    if not f: return None  # 선수가 없으면 None 반환
                    target = f[0]  # target: 찾은 첫 번째 선수 사전 정보
                    p_id = str(target['id'])  # p_id: 선수 고유 ID
                    img_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{p_id}.png"  # img_url: 이미지 주소
                    info_res = commonplayerinfo.CommonPlayerInfo(player_id=p_id, timeout=30).get_dict()  # info_res: 신상 정보 API 응답 데이터
                    career = playercareerstats.PlayerCareerStats(player_id=p_id, timeout=30).get_data_frames()[0]  # career: 커리어 데이터프레임
                    info = dict(zip(info_res['resultSets'][0]['headers'], info_res['resultSets'][0]['rowSet'][0]))  # info: 신상 데이터 사전 변환

                    raw_h = info.get('HEIGHT')  # raw_h: 원본 키 문자열
                    h_str = "정보 없음"  # h_str: cm 단위 키 문자열
                    if raw_h and "-" in str(raw_h):  # 키 단위 변환 (피트/인치 -> cm)
                        ft, inch = map(int, raw_h.split("-"))  # ft: 피트, inch: 인치
                        h_str = f"{round((ft * 30.48) + (inch * 2.54))} cm"

                    raw_w = info.get('WEIGHT')  # raw_w: 원본 파운드 몸무게
                    w_str = "정보 없음"  # w_str: kg 단위 몸무게
                    if raw_w and str(raw_w).isdigit():  # 몸무게 단위 변환 (lbs -> kg)
                        w_str = f"{round(float(raw_w) * 0.453592, 1)} kg"

                    ppg, rpg, apg, gp, season = 0, 0, 0, 0, "정보 없음"  # 기록 수치 초기화
                    if not career.empty:  # 커리어 통계가 있는 경우
                        l_row = career.iloc[-1]  # l_row: 가장 최근 시즌 통계 행
                        season = l_row.get('SEASON_ID', "정보 없음")  # season: 최근 시즌명
                        gp = l_row.get('GP', 0)  # gp: 경기 수
                        if gp > 0:  # 경기수가 있을 경우 평균 수치 계산
                            ppg = round(l_row['PTS'] / gp, 1)  # ppg: 평균 득점
                            rpg = round(l_row['REB'] / gp, 1)  # rpg: 평균 리바운드
                            apg = round(l_row['AST'] / gp, 1)  # apg: 평균 어시스트

                    return {  # 선수의 주요 비교 정보를 정돈된 사전(dict) 형태로 최종 반환
                        "name": info.get('DISPLAY_FIRST_LAST', target['full_name']), "img_url": img_url,
                        "team": f"{info.get('TEAM_CITY', '')} {info.get('TEAM_NAME', '')}".strip() or "미소속",
                        "pos": info.get('POSITION') or "정보 없음", "exp": f"{info.get('SEASON_EXP', 0)} 년차",
                        "height": h_str, "weight": w_str, "season": season, "gp": gp, "ppg": ppg, "rpg": rpg, "apg": apg
                    }

                p1 = fetch_player_data(p1_target)  # p1: 선수 A의 상세 수치 정보 사전 변수
                p2 = fetch_player_data(p2_target)  # p2: 선수 B의 상세 수치 정보 사전 변수

                if p1 and p2:  # 두 선수의 데이터를 모두 성공적으로 가져왔을 때
                    c1, c2 = st.columns(2)  # 이미지와 이름을 나란히 보여주기 위한 좌우 컬럼 변수
                    with c1:  # 선수 A 카드
                        st.image(p1['img_url'], width=150)  # 선수 A 얼굴 사진
                        st.subheader(f"🔴 {p1['name']}")  # 선수 A 이름
                    with c2:  # 선수 B 카드
                        st.image(p2['img_url'], width=150)  # 선수 B 얼굴 사진
                        st.subheader(f"🔵 {p2['name']}")  # 선수 B 이름

                    compare_data = {  # compare_data: 1:1 비교표(Table)로 출력하기 위한 판다스용 사전 데이터 Structure
                        "항목": ["키", "몸무게", "경력", "최근 시즌", "평균 득점", "평균 리바운드", "평균 어시스트"],  # 비교 항목 라벨 리스트
                        p1['name']: [p1['height'], p1['weight'], p1['exp'], p1['season'], f"{p1['ppg']} 점", f"{p1['rpg']} 개", f"{p1['apg']} 개"],  # 선수 A의 값 리스트
                        p2['name']: [p2['height'], p2['weight'], p2['exp'], p2['season'], f"{p2['ppg']} 점", f"{p2['rpg']} 개", f"{p2['apg']} 개"]   # 선수 B의 값 리스트
                    }
                    st.table(pd.DataFrame(compare_data).set_index("항목"))  # '항목'을 인덱스로 삼는 비교 표(Table) 화면 출력
            except Exception as e:  # 예외 발생 시
                st.error(f"오류 발생: {e}")  # 오류 내용 출력

# ==========================================
# [메뉴 3] 농구 코트 찾기 & 날씨
# ==========================================
elif menu == "3. 농구 코트 찾기 & 날씨":  # 메인 메뉴가 "3. 농구 코트 찾기 & 날씨"일 때 동작
    st.header("📍 전국 농구 코트 찾기 & 실시간 날씨")  # 메뉴 헤더 출력
    df_courts = load_national_court_data()  # df_courts: courts_data.json에서 읽어온 전체 코트 정보 데이터프레임(표)

    df_courts["sido"] = df_courts["sido"].astype(str).str.strip()  # sido 컬럼의 데이터 타입을 문자열로 변환하고 양끝 공백 제거
    df_courts["sigungu"] = df_courts["sigungu"].astype(str).str.strip()  # sigungu 컬럼 공백 제거
    df_courts["종류"] = df_courts["종류"].astype(str).str.strip()  # 종류(우레탄, 실내 등) 컬럼 공백 제거
    df_courts["코트명"] = df_courts["코트명"].astype(str).str.strip()  # 코트명 컬럼 공백 제거
    df_courts["위치"] = df_courts["위치"].astype(str).str.strip()  # 위치(주소) 컬럼 공백 제거

    type_list = ["전체"] + sorted([t for t in df_courts["종류"].unique() if t and t != 'nan'])  # type_list: 종류 드롭다운 선택지에 넣을 중복 제거된 코트 종류 리스트
    selected_type = st.selectbox("운동장 / 체육관 종류 선택:", type_list, key="court_type_select")  # selected_type: 사용자가 선택한 코트 종류 변수

    filtered_by_type = df_courts if selected_type == "전체" else df_courts[df_courts["종류"] == selected_type]  # filtered_by_type: 종류 조건에 맞게 1차 필터링된 데이터프레임

    col1, col2 = st.columns(2)  # 화면을 반으로 나누는 2개 컬럼 변수

    sido_list = ["전체"] + sorted([s for s in filtered_by_type["sido"].unique() if s and s != 'nan'])  # sido_list: 선택할 수 있는 시/도 목록 리스트
    with col1:  # 첫 번째 컬럼
        selected_sido = st.selectbox("특별시 / 광역시 / 도 선택:", sido_list, key="court_sido_select")  # selected_sido: 선택한 시/도 이름 변수

    filtered_by_sido = filtered_by_type if selected_sido == "전체" else filtered_by_type[filtered_by_type["sido"] == selected_sido]  # filtered_by_sido: 시/도 조건까지 반영된 2차 필터링 데이터프레임

    sigungu_list = ["전체"] + sorted([sg for sg in filtered_by_sido["sigungu"].unique() if sg and sg != 'nan'])  # sigungu_list: 선택한 시/도 내의 시/군/구 목록 리스트
    with col2:  # 두 번째 컬럼
        selected_sigungu = st.selectbox("시 / 군 / 구 선택:", sigungu_list, key="court_sigungu_select")  # selected_sigungu: 선택한 시/군/구 이름 변수

    filtered_by_sigungu = filtered_by_sido if selected_sigungu == "전체" else filtered_by_sido[filtered_by_sido["sigungu"] == selected_sigungu]  # filtered_by_sigungu: 시/군/구 조건까지 반영된 3차 필터링 데이터프레임

    col3, col4 = st.columns(2)  # 추가 2개 컬럼 생성

    def extract_address_unit(addr):  # addr: 코트 주소 문자열 매개변수
        if not addr or pd.isna(addr): return "기타"  # 주소가 없으면 "기타" 반환
        for p in str(addr).split():  # 주소를 띄어쓰기로 단어별 분할
            if p.endswith(('동', '읍', '면', '리', '가')): return p  # 단어가 '동', '읍', '면', '리', '가'로 끝나면 해당 읍/면/동 단위 단어 반환
        return "기타"  # 단위 단어를 못 찾으면 "기타" 반환

    filtered_by_sigungu = filtered_by_sigungu.copy()  # 경고 방지를 위해 판다스 데이터프레임 복사본 생성
    filtered_by_sigungu["행정단위"] = filtered_by_sigungu["위치"].apply(extract_address_unit)  # 위치 주소에서 읍/면/동 단위를 추출해 "행정단위" 신규 칼럼 추가

    unit_list = ["전체"] + sorted([d for d in filtered_by_sigungu["행정단위"].unique() if d and d != "기타"])  # unit_list: 읍/면/동 드롭다운 옵션 목록 리스트
    with col3:  # 세 번째 컬럼
        selected_unit = st.selectbox("읍 / 면 / 리 / 동 선택:", unit_list, key="court_unit_select")  # selected_unit: 선택된 읍/면/동 변수

    filtered_by_unit = filtered_by_sigungu if selected_unit == "전체" else filtered_by_sigungu[filtered_by_sigungu["행정단위"] == selected_unit]  # filtered_by_unit: 읍/면/동 조건 반영 4차 필터링 데이터프레임

    court_name_list = ["전체"] + sorted([c for c in filtered_by_unit["코트명"].unique() if c and c != 'nan'])  # court_name_list: 최종 특정 농구장 선택을 위한 코트명 리스트
    with col4:  # 네 번째 컬럼
        selected_court_name = st.selectbox("경기장 선택:", court_name_list, key="court_name_select")  # selected_court_name: 최종 선택된 농구 코트 이름 변수

    filtered_df = filtered_by_unit if selected_court_name == "전체" else filtered_by_unit[filtered_by_unit["코트명"] == selected_court_name]  # filtered_df: 모든 검색 조건이 다 적용된 최종 필터링 데이터프레임

    filtered_df["lat"] = pd.to_numeric(filtered_df["lat"], errors="coerce")  # lat(위도) 칼럼을 숫자로 형변환 (잘못된 데이터는 NaN 처리)
    filtered_df["lon"] = pd.to_numeric(filtered_df["lon"], errors="coerce")  # lon(경도) 칼럼을 숫자로 형변환 (잘못된 데이터는 NaN 처리)
    map_df = filtered_df[filtered_df["lat"].notna() & filtered_df["lon"].notna()].copy()  # map_df: 지도에 찍기 위해 유효한 위도/경도가 존재하는 행만 추출한 데이터프레임

    avg_lat = map_df["lat"].iloc[0] if not map_df.empty else 37.5665  # avg_lat: 지도 중심점 및 날씨 조회를 위한 위도값 (데이터가 없으면 서울 위도 사용)
    avg_lon = map_df["lon"].iloc[0] if not map_df.empty else 126.9780  # avg_lon: 지도 중심점 및 날씨 조회를 위한 경도값 (데이터가 없으면 서울 경도 사용)

    st.subheader("🌦️ 실시간 날씨")  # 실시간 날씨 섹션 제목 출력
    weather_info = get_weather_by_coords(avg_lat, avg_lon)  # weather_info: 해당 위도/경도 위치의 실시간 날씨 정보를 가져온 사전 변수
    if weather_info["status"]:  # 날씨 정보를 정상적으로 읽어왔을 때
        w1, w2, w3 = st.columns(3)  # 날씨 정보를 나란히 보여줄 3개 컬럼 생성
        w1.metric("기온", f"{weather_info['temp']} °C")  # 기온 강조 표시
        w2.metric("상태", weather_info['desc'])  # 날씨 상태(맑음, 비 등) 강조 표시
        w3.success("야외 농구 적합!")  # 야외 활동 안내 메세지 표시

    st.subheader(f"🗺️ 농구 코트 지도 (검색 결과: {len(map_df)}개)")  # 지도 영역 소제목 및 검색 개수 표시

    if not map_df.empty:  # 검색된 코트가 1개 이상 있을 때 지도를 생성
        korea_lat, korea_lon = 37.5665, 126.9780  # korea_lat, korea_lon: 대한민국 전체 지도를 중앙에 맞추기 위한 대한민국 중심 위경도 좌표

        r = pdk.Deck(  # r: PyDeck 지도 객체 변수
            layers=[  # 지도 위에 올릴 레이어(시각화 요소) 정의 리스트
                pdk.Layer(
                    "ScatterplotLayer",  # 좌표 지점에 동그란 점을 찍어주는 스캐터플롯 레이어 타입
                    data=map_df,  # 점을 찍을 데이터프레임 지정
                    get_position="[lon, lat]",  # 위치 좌표 지정 (경도, 위도 순서)
                    get_color="[255, 102, 0, 220]",  # 점의 색상 지정 (RGBA -> 주황색 농구공 색상)
                    get_radius=500,  # 점의 반경(크기, 미터 단위) 지정
                    pickable=True  # 마우스 올렸을 때 툴팁 설명창이 뜨도록 설정
                )
            ],
            initial_view_state=pdk.ViewState(  # 지도의 초기 시점/시야 위치 설정
                latitude=korea_lat,  # 초기 위도 (대한민국 중심)
                longitude=korea_lon,  # 초기 경도 (대한민국 중심)
                zoom=7.3,  # 초기 확대/축소 비율 (대한민국 전체가 잘 보이는 줌 레벨)
                pitch=0  # 지도의 경사각(기울기) 0도로 지정
            ),
            tooltip={"html": "<b>{코트명}</b><br/>📍 {위치}"}  # 마우스를 점에 올렸을 때 팝업으로 나타날 HTML 설명 툴팁
        )
        st.pydeck_chart(r)  # 생성된 PyDeck 지도를 Streamlit 메인 화면에 출력

        with st.expander("📋 검색된 농구장 목록 상세 보기"):  # 클릭해서 열 수 있는 접이식 아코디언 상자 생성
            st.dataframe(filtered_df[["코트명", "위치", "종류", "조명"]], use_container_width=True)  # 필터링된 코트 목록을 데이터 표로 보여줌
    else:  # 조건에 일치하는 코트가 하나도 없을 경우
        st.warning("선택한 조건에 일치하는 코트 위치 정보를 찾을 수 없습니다.")  # 노란색 경고 문구 출력

# ==========================================
# [메뉴 4] AI 농구 코치 (Q&A)
# ==========================================
elif menu == "4. AI 농구 코치 (Q&A)":  # 메인 메뉴가 "4. AI 농구 코치 (Q&A)"일 때 동작
    st.header("🤖 AI 농구 코치")  # 헤더 출력
    st.write("농구에 대해 궁금한 점을 직접 물어보거나, 아래 **추천 질문**을 클릭해 바로 답변을 확인해 보세요!")  # 본문 안내 문구 출력

    if "selected_ai_question" not in st.session_state:  # 세션 상태에 선택된 AI 질문 저장이 없으면 초기화
        st.session_state.selected_ai_question = ""  # 빈 문자열 세팅
    if "ai_answer_result" not in st.session_state:  # 세션 상태에 AI 답변 결과 저장이 없으면 초기화
        st.session_state.ai_answer_result = ""  # 빈 문자열 세팅

    st.subheader("💡 추천 질문 바로가기 (즉시 답변)")  # 추천 질문 영역 소제목 출력

    canned_answers = {  # canned_answers: 미리 준비된 자주 묻는 질문(키)과 즉시 답변(값) 사전 데이터 구조 변수
        "🏀 레이업 슈팅 성공률을 높이는 꿀팁 알려줘!": "🏀 **레이업 꿀팁:** 골대 근처에서는 백보드 상단의 사각형 모서리를 가볍게 맞춘다는 느낌으로 공을 올려놓으세요! 손목의 스냅을 부드럽게 쓰면 성공률이 확 올라갑니다.",
        "👟 중학생이 신기 좋은 가성비 농구화 추천해줘!": "👟 **추천 농구화:** 나이키 임파서블 시리즈나 에어 조던 줌 트레이너 계열이 접지력과 충격 흡수가 좋아 중학생들에게 가장 가성비가 훌륭합니다!",
        "🏃 자유투 던질 때 자세 잡는 법 알려줘!": "🏃 **자유투 팁:** 숨을 깊게 내쉬고 무릎을 살짝 낮췄다가 펴는 반동을 이용하세요. 팔꿈치가 골대를 향해 일직선이 되도록 유지하는 것이 핵심입니다!",
        "🛡️ 맨투맨 수비할 때 자리를 잘 잡는 방법은?": "🛡️ **맨투맨 수비 팁:** 상대방 선수와 골대의 일직선 상(중간 위치)에 내 몸을 두세요! 공과 사람을 동시에 시야에 담는 '오프볼 디펜스' 자세가 중요합니다."
    }

    recommendations = list(canned_answers.keys())  # recommendations: 미리 준비된 질문 텍스트들의 리스트 변수

    rec_col1, rec_col2 = st.columns(2)  # 추천 질문 버튼들을 2열로 배치하기 위한 컬럼 변수
    for idx, q_text in enumerate(recommendations):  # idx: 인덱스 번호(0,1,2,3), q_text: 각 추천 질문 텍스트
        col = rec_col1 if idx % 2 == 0 else rec_col2  # 짝수번 질문은 왼쪽 컬럼, 홀수번 질문은 오른쪽 컬럼에 배치
        if col.button(q_text, key=f"rec_btn_{idx}", use_container_width=True):  # 추천 질문 버튼 클릭 시
            st.session_state.selected_ai_question = q_text  # 클릭한 질문을 선택된 질문 세션에 저장
            st.session_state.ai_answer_result = canned_answers[q_text]  # 준비된 답변을 세션에 바로 즉시 반영
            st.rerun()  # 화면을 새로고침하여 답변 보여주기

    st.divider()  # 가로 구획선

    user_question = st.text_input(  # user_question: 사용자가 직접 입력한 질문 문자열 변수
        "💬 AI 코치에게 직접 질문하기:",  # 라벨
        value=st.session_state.selected_ai_question,  # 현재 선택된 질문 텍스트를 기본값으로 채워둠
        placeholder="예: 드리블 잘 치는 법 알려줘!"  # 가이드 문구
    )

    if st.button("질문하기", type="primary"):  # "질문하기" 버튼을 클릭했을 때 실행
        if not user_question.strip():  # 입력된 질문이 비어있는 경우
            st.warning("질문을 입력해 주세요!")  # 경고 메세지 출력
        else:  # 질문이 제대로 입력되었을 때
            st.session_state.selected_ai_question = user_question  # 입력한 질문을 세션 상태에 저장
            with st.spinner("🤖 AI 코치가 답변을 작성 중입니다..."):  # 로딩 애니메이션 표시
                try:  # Gemini API 호출 중 예외 발생에 대비
                    from google import genai  # google.genai: Google의 최신 Gemini API 공식 패키지 불러오기
                    client = genai.Client(api_key=user_api_key.strip())  # client: 사용자가 사이드바에 입력한 API 키로 생성한 Gemini 통신 클라이언트 객체
                    prompt = (  # prompt: Gemini AI 모델에 전달할 프롬프트 지시문 통합 문자열
                        "너는 친절하고 전문적인 NBA 출신 농구 코치야. "
                        "중학생도 이해하기 쉽게 이모지를 섞어가며 친절하게 답변해줘.\n"
                        f"질문: {user_question}"
                    )
                    response = client.models.generate_content(  # response: Gemini 모델이 생성하여 반환한 답변 응답 객체
                        model='gemini-3.6-flash',  # model: 호출할 Gemini AI의 모델명
                        contents=prompt  # contents: AI에게 전달할 프롬프트 문자열
                    )
                    st.session_state.ai_answer_result = response.text  # AI가 응답한 최종 텍스트 결과물을 ai_answer_result 세션에 저장
                except Exception as e:  # API 키 오류 등 실패 시 예외 처리
                    st.session_state.ai_answer_result = f"API Key가 올바르지 않거나 오류가 발생했습니다: {e}"  # 에러 메세지를 결과 세션에 저장
            st.rerun()  # 화면을 새로고침하여 답변 갱신

    if st.session_state.ai_answer_result:  # 세션에 저장된 AI 답변 결과가 존재할 때 화면에 출력
        st.markdown("---")  # 구분선 표시
        st.success(f"**📌 질문:** {st.session_state.selected_ai_question}")  # 사용자가 했던 질문 표시
        st.info(st.session_state.ai_answer_result)  # AI의 답변 내용 파란색 상자 안에 표시

# ==========================================
# [메뉴 5] 같이 할 사람 모집
# ==========================================
elif menu == "5. 같이 할 사람 모집":  # 메인 메뉴가 "5. 같이 할 사람 모집"일 때 동작
    st.header("🤝 농구 친구 모집 게시판")  # 게시판 메인 헤더 출력
    with st.expander("➕ 새 모집글 쓰기", expanded=False):  # 새 글 작성을 위한 접이식 아코디언 상자 생성 (기본 닫힘)
        with st.form("post_form"):  # post_form: 여러 입력값을 한 번에 제출받는 스트림릿 폼 객체
            name = st.text_input("닉네임")  # name: 작성자 닉네임 입력 변수
            location = st.text_input("장소/지역")  # location: 농구할 모임 장소 입력 변수
            time_slot = st.text_input("일시")  # time_slot: 모임 시간/날짜 입력 변수
            content = st.text_area("모집 내용")  # content: 상세 모집 내용 입력 변수 (여러 줄)
            submit = st.form_submit_button("등록", type="primary")  # submit: 폼 제출 버튼 클릭 상태(True/False)
            if submit and name and location and content:  # 등록 버튼이 눌렸고 필수 항목이 모두 채워졌을 때
                st.session_state.posts.insert(0, {"작성자": name, "지역": location, "일시": time_slot, "내용": content, "상태": "모집중", "댓글": []})  # 신규 모집글을 세션의 게시글 리스트 가장 최신 위치(0번 인덱스)에 추가
                st.success("등록되었습니다!")  # 성공 메세지 출력
                st.rerun()  # 화면 새로고침하여 등록된 새 게시글 즉시 표시

    for idx, post in enumerate(st.session_state.posts):  # idx: 게시글 인덱스 번호, post: 각 게시글 정보 사전(dict)
        st.markdown(f"#### {post['내용']}")  # 게시글 제목/내용 출력
        st.caption(f"👤 {post['작성자']} | 📍 {post['지역']}")  # 작성자와 장소 정보를 작고 옅은 글씨로 표시
        st.divider()  # 게시글 간 구분선 표시

# ==========================================
# [메뉴 6] 농구 용품 전용 검색
# ==========================================
elif menu == "6. 농구 용품 전용 검색":  # 메인 메뉴가 "6. 농구 용품 전용 검색"일 때 동작
    st.header("🛍️ 농구 용품 추천 및 검색")  # 헤더 출력
    gear_df = pd.DataFrame(load_basketball_gears())  # gear_df: 추천 용품 리스트를 데이터프레임(표)으로 변환한 변수
    search_kw = st.text_input("🔍 용품 검색어:", placeholder="예: 나이키, 무릎 보호대")  # search_kw: 사용자가 용품 검색창에 입력한 키워드 변수

    filtered = gear_df  # filtered: 필터링 결과를 담을 데이터프레임 (초기값은 전체 용품)
    if search_kw.strip():  # 검색창에 검색어가 입력되어 있을 때
        kw = search_kw.strip().lower()  # kw: 검색어를 소문자로 변환한 공백 없는 문자열 변수
        filtered = gear_df[gear_df["name"].str.lower().str.contains(kw) | gear_df["brand"].str.lower().str.contains(kw) | gear_df["category"].str.lower().str.contains(kw)]  # 용품명, 브랜드명, 카테고리명 중 하나라도 검색어가 포함된 항목만 필터링

    if not filtered.empty:  # 필터링된 결과 용품이 1개 이상 존재할 경우
        for _, item in filtered.iterrows():  # item: 필터링된 데이터프레임의 각 용품 행(Series) 데이터
            st.subheader(f"🏀 {item['name']}")  # 용품 이름 출력
            st.write(f"💵 가격: {item['price']} | 📝 {item['desc']}")  # 가격과 상세 설명 출력
            st.divider()  # 구분선 표시
    else:  # 반복문 끝에 바로 붙어있는 원래 코드의 else문 (필터링 결과가 비어있으면 동작)
        st.warning("검색 조건에 맞는 농구용품이 없습니다.")  # 검색 결과 없음 문구 출력

    st.subheader("🌐 검증된 농구 전문 브랜드 사이트")  # 쇼핑몰 안내 서브헤더 출력
    st.caption("잡상품이 없는 농구 전문 쇼핑몰 메인 페이지 바로가기입니다.")  # 안내 문구 출력

    b_col1, b_col2 = st.columns(2)  # 사이트 링크 버튼을 나란히 놓기 위한 좌우 컬럼 변수
    with b_col1:  # 첫 번째 컬럼
        st.link_button("🏀 훕시티 (농구전문몰 공식 사이트)", "https://www.hoopcity.co.kr", use_container_width=True)  # 훕시티 쇼핑몰 이동 링크 버튼
    with b_col2:  # 두 번째 컬럼
        st.link_button("🧦 마스터욱 (농구용품 공식 사이트)", "https://www.masterwook.com", use_container_width=True)  # 마스터욱 쇼핑몰 이동 링크 버튼