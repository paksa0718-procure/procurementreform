#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="US Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("default")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #ffffff;   /* 흰색 배경 */
    color: #000000;              /* 글씨 검정색 */
    text-align: center;
    padding: 15px 0;
    border-radius: 10px;         /* 모서리 둥글게 (선택사항) */
    border: 1px solid #ddd;      /* 옅은 테두리 (선택사항) */
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)


#######################
# Load data
df_reshaped = pd.read_excel('fake_data_100.xlsx', engine="openpyxl")  ## 분석 데이터 넣기

#######################
# Sidebar
with st.sidebar:
    st.title("개혁과제 대시보드")
    st.caption("필터를 선택해 보세요")

    # ================= 날짜/연도 파싱 =================
    # 처리기한이 '25.05.08' 같은 형식이라고 가정
    if "처리기한" in df_reshaped.columns:
        _deadline = pd.to_datetime(
            df_reshaped["처리기한"].astype(str),
            format="%y.%m.%d",
            errors="coerce",
        )
        df_reshaped["_처리기한_dt"] = _deadline
    else:
        df_reshaped["_처리기한_dt"] = pd.NaT

    # ================= 테마 =================
    theme = st.selectbox(
        "색상 테마",
        options=["default", "bright", "quartz", "ggplot2", "vox"],
        index=0,
        help="차트 색상 테마를 바꿉니다",
    )
    try:
        alt.themes.enable(theme)
    except Exception:
        alt.themes.enable("default")

    st.divider()

    # ================= 연/월 필터 =================
    if df_reshaped["_처리기한_dt"].notna().any():
        years = sorted(df_reshaped["_처리기한_dt"].dt.year.dropna().unique().tolist())
        sel_year = st.selectbox("연도 선택", options=["전체"] + years, index=0)

        # 월 선택(해당 연도에 한해)
        if sel_year == "전체":
            month_opts = list(range(1, 13))
        else:
            month_opts = (
                df_reshaped.loc[df_reshaped["_처리기한_dt"].dt.year == sel_year, "_처리기한_dt"]
                .dt.month.dropna().unique().tolist()
            )
            month_opts = sorted(month_opts) if month_opts else list(range(1, 13))

        sel_months = st.multiselect("월 선택", options=month_opts, default=month_opts)
    else:
        sel_year = "전체"
        sel_months = list(range(1, 13))

    # ================= 기본 필터 =================
    def _opts(col):
        return sorted([x for x in df_reshaped[col].dropna().unique().tolist()]) if col in df_reshaped.columns else []

    sel_sosok = st.multiselect("소속", options=_opts("소속"), default=_opts("소속"))
    sel_status = st.multiselect("진행상황", options=_opts("진행상황"), default=_opts("진행상황"))
    sel_dpt    = st.multiselect("담당과", options=_opts("담당과"), default=_opts("담당과"))

    # 협업 관련
    col1, col2 = st.columns(2)
    with col1:
        only_collab = st.checkbox("협업 과제만", value=False)
    with col2:
        sel_partner = st.multiselect("부처협업(타부처)", options=_opts("부처협업"), default=[])

    # 임박 기준(며칠 이내)
    due_days = st.number_input("임박 기준 (일)", min_value=1, max_value=60, value=7, step=1, help="오늘 기준 며칠 이내 마감")

    # ================= 리셋 & 상태 저장 =================
    reset = st.button("필터 초기화")
    if reset:
        st.experimental_rerun()

    # 후속 영역에서 사용할 필터를 세션에 저장
    st.session_state["filters"] = {
        "theme": theme,
        "year": sel_year,
        "months": sel_months,
        "소속": sel_sosok,
        "진행상황": sel_status,
        "담당과": sel_dpt,
        "only_collab": only_collab,
        "부처협업": sel_partner,
        "due_days": int(due_days),
    }

#######################
# Plots



#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]:
    st.markdown("### 📊 과제 요약 지표")

    # ===== 필터 적용 =====
    f = st.session_state.get("filters", {})
    df_filt = df_reshaped.copy()

    if f.get("year") != "전체":
        df_filt = df_filt[df_filt["_처리기한_dt"].dt.year == f["year"]]
    if f.get("months"):
        df_filt = df_filt[df_filt["_처리기한_dt"].dt.month.isin(f["months"])]
    if f.get("소속"):
        df_filt = df_filt[df_filt["소속"].isin(f["소속"])]
    if f.get("진행상황"):
        df_filt = df_filt[df_filt["진행상황"].isin(f["진행상황"])]
    if f.get("담당과"):
        df_filt = df_filt[df_filt["담당과"].isin(f["담당과"])]
    if f.get("only_collab"):
        df_filt = df_filt[df_filt["부처협업"].notna()]
    if f.get("부처협업"):
        df_filt = df_filt[df_filt["부처협업"].isin(f["부처협업"])]

    # ===== 요약 통계 =====
    total_tasks = len(df_filt)
    completed = (df_filt["진행상황"] == "완료").sum()
    delayed   = (df_filt["진행상황"] == "지연").sum()
    stopped   = (df_filt["진행상황"] == "중단").sum()
    ongoing   = (df_filt["진행상황"] == "원활").sum()

    # 임박 과제 (due_days 이내 마감 yet 미완료)
    today = pd.Timestamp.today()
    due_days = f.get("due_days", 7)
    imminent = df_filt[
        (df_filt["_처리기한_dt"].notna()) &
        (df_filt["_처리기한_dt"] <= today + pd.Timedelta(days=due_days)) &
        (df_filt["진행상황"].isin(["지연", "중단", "원활"]))
    ]
    imminent_count = len(imminent)

    # ===== 메트릭 카드 =====
    st.metric("전체 과제 수", total_tasks)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("완료", completed)
        st.metric("지연", delayed)
    with c2:
        st.metric("중단", stopped)
        st.metric("원활", ongoing)

    st.metric(f"임박 과제 ({due_days}일 이내)", imminent_count)

    # ===== 진행상황 분포 도넛 차트 =====
    status_counts = df_filt["진행상황"].value_counts().reset_index()
    status_counts.columns = ["진행상황", "건수"]

    if not status_counts.empty:
        fig = px.pie(
            status_counts,
            values="건수",
            names="진행상황",
            hole=0.4,
            title="진행상황 분포",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("선택된 조건에 맞는 데이터가 없습니다.")



with col[1]:
    st.markdown("### 🗺️ 부서별 분포 및 처리기한 히트맵")

    # ===== 필터 적용 (col[0]과 동일) =====
    f = st.session_state.get("filters", {})
    df_filt = df_reshaped.copy()

    if f.get("year") != "전체":
        df_filt = df_filt[df_filt["_처리기한_dt"].dt.year == f["year"]]
    if f.get("months"):
        df_filt = df_filt[df_filt["_처리기한_dt"].dt.month.isin(f["months"])]
    if f.get("소속"):
        df_filt = df_filt[df_filt["소속"].isin(f["소속"])]
    if f.get("진행상황"):
        df_filt = df_filt[df_filt["진행상황"].isin(f["진행상황"])]
    if f.get("담당과"):
        df_filt = df_filt[df_filt["담당과"].isin(f["담당과"])]
    if f.get("only_collab"):
        df_filt = df_filt[df_filt["부처협업"].notna()]
    if f.get("부처협업"):
        df_filt = df_filt[df_filt["부처협업"].isin(f["부처협업"])]

    # =====================
    # 📊 1) 부서별 진행상황 막대그래프
    # =====================
    if not df_filt.empty:
        dept_status = (
            df_filt.groupby(["소속", "진행상황"])
            .size()
            .reset_index(name="건수")
        )

        bar_chart = alt.Chart(dept_status).mark_bar().encode(
            x=alt.X("소속:N", title="소속"),
            y=alt.Y("건수:Q", title="과제 건수"),
            color=alt.Color("진행상황:N", legend=alt.Legend(title="진행상황")),
            tooltip=["소속", "진행상황", "건수"]
        ).properties(
            title="부서별 진행상황 분포",
            width="container",
            height=350
        )
        st.altair_chart(bar_chart, use_container_width=True)
    else:
        st.info("선택된 조건에 맞는 데이터가 없습니다.")

    st.divider()

    # =====================
    # 📊 2) 처리기한 히트맵 (타임라인)
    # =====================
    if df_filt["_처리기한_dt"].notna().any():
        df_filt["연도"] = df_filt["_처리기한_dt"].dt.year
        df_filt["월"] = df_filt["_처리기한_dt"].dt.month

        heatmap_data = (
            df_filt.groupby(["연도", "월", "소속"])
            .size()
            .reset_index(name="건수")
        )

        heatmap = alt.Chart(heatmap_data).mark_rect().encode(
            x=alt.X("월:O", title="월"),
            y=alt.Y("소속:N", title="소속"),
            color=alt.Color("건수:Q", scale=alt.Scale(scheme="blues")),
            tooltip=["연도", "월", "소속", "건수"]
        ).properties(
            title="소속별 처리기한 히트맵",
            width="container",
            height=400
        )

        st.altair_chart(heatmap, use_container_width=True)
    else:
        st.info("처리기한 데이터가 없습니다.")




with col[2]:
    st.markdown("### 🔎 세부 정보")

    # ===== 필터 적용 (col[0], col[1]과 동일) =====
    f = st.session_state.get("filters", {})
    df_filt = df_reshaped.copy()

    if f.get("year") != "전체":
        df_filt = df_filt[df_filt["_처리기한_dt"].dt.year == f["year"]]
    if f.get("months"):
        df_filt = df_filt[df_filt["_처리기한_dt"].dt.month.isin(f["months"])]
    if f.get("소속"):
        df_filt = df_filt[df_filt["소속"].isin(f["소속"])]
    if f.get("진행상황"):
        df_filt = df_filt[df_filt["진행상황"].isin(f["진행상황"])]
    if f.get("담당과"):
        df_filt = df_filt[df_filt["담당과"].isin(f["담당과"])]
    if f.get("only_collab"):
        df_filt = df_filt[df_filt["부처협업"].notna()]
    if f.get("부처협업"):
        df_filt = df_filt[df_filt["부처협업"].isin(f["부처협업"])]

    # =====================
    # 🟣 1) Top 지연/중단 과제 리스트
    # =====================
    st.markdown("#### ⚠️ 임박 지연/중단 과제")

    today = pd.Timestamp.today()
    due_days = f.get("due_days", 7)

    delayed_tasks = df_filt[
        (df_filt["_처리기한_dt"].notna()) &
        (df_filt["_처리기한_dt"] <= today + pd.Timedelta(days=due_days)) &
        (df_filt["진행상황"].isin(["지연", "중단"]))
    ][["소속", "개혁과제", "처리기한", "진행상황", "담당자", "담당과"]]

    if not delayed_tasks.empty:
        st.dataframe(
            delayed_tasks.sort_values("처리기한"),
            use_container_width=True,
            height=200
        )
    else:
        st.info("임박한 지연/중단 과제가 없습니다.")

    st.divider()

    # =====================
    # 🟣 2) 담당자별 과제 건수 랭킹
    # =====================
    st.markdown("#### 🏅 담당자별 과제 건수 랭킹")

    if not df_filt.empty:
        top_staff = (
            df_filt.groupby("담당자")
            .size()
            .reset_index(name="과제건수")
            .sort_values("과제건수", ascending=False)
            .head(10)
        )

        staff_chart = alt.Chart(top_staff).mark_bar().encode(
            x=alt.X("과제건수:Q", title="과제 건수"),
            y=alt.Y("담당자:N", sort="-x", title="담당자"),
            tooltip=["담당자", "과제건수"],
        ).properties(
            title="담당자별 과제 건수 TOP 10",
            width="container",
            height=350
        )

        st.altair_chart(staff_chart, use_container_width=True)
    else:
        st.info("담당자 데이터가 없습니다.")

    st.divider()

    # =====================
    # 🟣 3) 협업 현황
    # =====================
    st.markdown("#### 🤝 협업 현황")

    if "부처협업" in df_filt.columns and df_filt["부처협업"].notna().any():
        collab_counts = (
            df_filt.groupby("부처협업")
            .size()
            .reset_index(name="건수")
            .sort_values("건수", ascending=False)
        )

        collab_chart = alt.Chart(collab_counts).mark_bar().encode(
            x=alt.X("건수:Q", title="건수"),
            y=alt.Y("부처협업:N", sort="-x", title="협업 부처"),
            tooltip=["부처협업", "건수"]
        ).properties(
            title="부처별 협업 건수",
            width="container",
            height=300
        )

        st.altair_chart(collab_chart, use_container_width=True)
    else:
        st.info("협업 과제 데이터가 없습니다.")
