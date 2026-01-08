import streamlit as st
import pandas as pd
from collections import Counter
from itertools import combinations
import plotly.express as px
import plotly.graph_objects as go
import random

# הגדרות דף ו-RTL
st.set_page_config(page_title="לוטו אסטרטגי", page_icon="🎰", layout="wide")

# עיצוב RTL וסטיילינג
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap');
html, body, [data-testid="stSidebar"], .main {
    direction: rtl;
    text-align: right;
    font-family: 'Assistant', sans-serif;
}
div[data-testid="stMetricValue"] { text-align: right; }
.stTabs [data-baseweb="tab-list"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

st.header("🎰 ניתוח נתוני לוטו - אסטרטגיה ובדיקה")
uploaded_file = st.file_uploader("העלה את קובץ ה-Lotto.csv שלך", type="csv")

if uploaded_file:
    try:
        # 1. טעינת נתונים
        df_all = pd.read_csv(uploaded_file, encoding="cp1255")
        df_all.columns = [c.strip() for c in df_all.columns]

        # זיהוי עמודות
        num_cols = ["1", "2", "3", "4", "5", "6"]
        strong_col = "המספר החזק/נוסף"
        lotto_winners_col = "מספר_זוכים_לוטו"
        double_winners_col = "מספר_זוכים_דאבל_לוטו"
        draw_id_col = "הגרלה"

        # המרת עמודות למספרים
        df_all[lotto_winners_col] = pd.to_numeric(df_all[lotto_winners_col], errors='coerce').fillna(0).astype(int)
        df_all[double_winners_col] = pd.to_numeric(df_all[double_winners_col], errors='coerce').fillna(0).astype(int)
        for col in num_cols + [strong_col, draw_id_col]:
            df_all[col] = pd.to_numeric(df_all[col], errors='coerce').fillna(0).astype(int)

        # 2. בחירת 50 הגרלות אחרונות לניתוח חלון
        df_window = df_all.head(50).copy()

        # --- חישובי זכיות ---
        total_lotto_v = int(df_window[lotto_winners_col].sum())
        total_double_v = int(df_window[double_winners_col].sum())
        grand_total_winners = total_lotto_v + total_double_v

        # --- סטטיסטיקה בסיסית ---
        all_nums = df_window[num_cols].values.flatten()
        freq = Counter([n for n in all_nums if n > 0])
        strong_freq = Counter([n for n in df_window[strong_col] if n > 0])
        draws_with_winners = len(df_window[(df_window[lotto_winners_col] > 0) | (df_window[double_winners_col] > 0)])
        last_draw_nums = set(df_all.iloc[0][num_cols].values)

        # --- חישוב מדדים אסטרטגיים ---
        df_window['sum_val'] = df_window[num_cols].sum(axis=1)
        df_window['even_count'] = df_window[num_cols].apply(lambda row: sum(1 for x in row if x % 2 == 0), axis=1)
        even_odd_dist = df_window['even_count'].value_counts().sort_index()


        def calc_avg_gap(row):
            sorted_row = sorted([n for n in row if n > 0])
            if len(sorted_row) < 2: return 0
            gaps = [sorted_row[i + 1] - sorted_row[i] for i in range(len(sorted_row) - 1)]
            return sum(gaps) / len(gaps)


        df_window['avg_gap'] = df_window[num_cols].apply(calc_avg_gap, axis=1)

        repeats = []
        rows_data = df_all.head(51)[num_cols].values
        for i in range(min(50, len(rows_data) - 1)):
            current = set(rows_data[i])
            prev = set(rows_data[i + 1])
            repeats.append(len(current.intersection(prev)))
        df_window['repeats_count'] = repeats[:len(df_window)]

        # --- תצוגת מדדים ראשיים (שורות עליונות) ---
        st.subheader(f"📊 סיכום 50 הגרלות אחרונות")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("👥 סה\"כ זוכים (משולב)", grand_total_winners)
        with m2:
            st.metric("🎫 זוכים בלוטו רגיל", total_lotto_v)
        with m3:
            st.metric("💎 זוכים בדאבל לוטו", total_double_v)

        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("🔥 מספר חם ביותר", freq.most_common(1)[0][0] if freq else "-")
        with s2:
            st.metric("⭐ חזק נפוץ", strong_freq.most_common(1)[0][0] if strong_freq else "-")
        with s3:
            st.metric("📅 הגרלות עם זכייה", draws_with_winners)

        st.divider()

        # --- טאבים ---
        tab1, tab_strat, tab_checker, tab2, tab3 = st.tabs(
            ["📈 ניתוח גרפי", "🎯 ניתוח אסטרטגי", "🧐 בודק טופס חכם", "🎲 המלצות מילוי", "📋 הנתונים הגולמיים"])

        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                df_chart = pd.DataFrame(freq.items(), columns=["מספר", "הופעות"]).sort_values("מספר")
                fig1 = px.bar(df_chart, x="מספר", y="הופעות", title="שכיחות מספרים רגילים", color="הופעות",
                              color_continuous_scale="Reds")
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                fig2 = px.line(df_window, x=draw_id_col, y=[lotto_winners_col, double_winners_col],
                               title="זכיות בפרס ראשון לאורך זמן")
                st.plotly_chart(fig2, use_container_width=True)

        with tab_strat:
            st.subheader("🧬 ניתוח מבנה הגרלות (Data Science)")
            col_a, col_b = st.columns(2)
            with col_a:
                fig_pie = px.pie(values=even_odd_dist.values, names=[f"{x} זוגיים" for x in even_odd_dist.index],
                                 title="התפלגות זוגי/אי-זוגי", color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig_pie, use_container_width=True)
                fig_scatter = px.scatter(df_window, x='sum_val', y='avg_gap', color='repeats_count',
                                         title="מפת פיזור: סכום מול מרחק ממוצע", color_continuous_scale="Viridis")
                st.plotly_chart(fig_scatter, use_container_width=True)
            with col_b:
                fig_sum = px.histogram(df_window, x='sum_val', nbins=15, title="התפלגות סכומי הגרלות (היעד: 100-170)",
                                       color_discrete_sequence=['#FF4B4B'])
                fig_sum.add_vline(x=135, line_dash="dash", line_color="white")
                st.plotly_chart(fig_sum, use_container_width=True)
                repeat_dist = df_window['repeats_count'].value_counts().sort_index()
                fig_rep = px.bar(x=repeat_dist.index, y=repeat_dist.values, title="כמה מספרים חזרו מהגרלה קודמת?",
                                 color_continuous_scale="Teal")
                st.plotly_chart(fig_rep, use_container_width=True)

        with tab_checker:
            st.subheader("🔍 בדוק את הטופס שלך")
            u_cols = st.columns(6)
            u_nums = []
            for j in range(6):
                u_nums.append(u_cols[j].number_input(f"מספר {j + 1}", 1, 37, value=j + 1, key=f"user_{j}"))

            if st.button("נתח את הטופס שלי"):
                u_nums = sorted(u_nums)
                u_sum = sum(u_nums)
                u_evens = sum(1 for x in u_nums if x % 2 == 0)
                u_repeats = len(set(u_nums).intersection(last_draw_nums))

                c_1, c_2, c_3 = st.columns(3)
                with c_1:
                    if 100 <= u_sum <= 170:
                        st.success(f"✅ סכום: {u_sum}")
                    else:
                        st.error(f"❌ סכום: {u_sum} (חריג)")
                with c_2:
                    if u_evens in [2, 3, 4]:
                        st.success(f"✅ זוגי: {u_evens}")
                    else:
                        st.warning(f"⚠️ זוגי: {u_evens} (לא מאוזן)")
                with c_3:
                    if u_repeats > 0:
                        st.success(f"✅ חוזרים: {u_repeats}")
                    else:
                        st.info("💡 אין מספרים חוזרים")

                # בדיקה על כל הקובץ
                match = df_all[df_all[num_cols].apply(lambda r: set(r.values) == set(u_nums), axis=1)]
                if not match.empty:
                    st.warning(f"😲 הצירוף זכה בפרס ראשון בהגרלה {match.iloc[0][draw_id_col]}!")
                else:
                    st.write("✨ צירוף חדש - לא זכה מעולם בפרס ראשון.")

        with tab2:
            st.subheader("🎯 10 קומבינציות מומלצות")
            hot_pool = [n for n, _ in freq.most_common(12)]
            ca, cb = st.columns(2)
            for i in range(1, 11):
                target = ca if i % 2 != 0 else cb
                p_hot = random.sample(hot_pool, 4) if len(hot_pool) >= 4 else random.sample(range(1, 38), 4)
                p_other = random.sample([n for n in range(1, 38) if n not in p_hot], 2)
                combo = sorted(p_hot + p_other)
                strong = random.choice(list(strong_freq.keys())) if strong_freq else random.randint(1, 7)
                with target:
                    st.markdown(f"""
                    <div style="background:#262730; padding:15px; border-radius:10px; border-right:5px solid #FF4B4B; margin-bottom:15px;">
                        <div style="color:#FF4B4B; font-size:14px; font-weight:bold; margin-bottom:8px;">טופס {i}</div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:22px; font-weight:bold; letter-spacing:2px;">{' &nbsp; '.join(map(str, combo))}</span>
                            <span style="background:#FF4B4B; color:white; width:35px; height:35px; display:flex; align-items:center; justify-content:center; border-radius:50%; font-weight:bold; font-size:18px;">{strong}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)

        with tab3:
            st.dataframe(
                df_window[[draw_id_col, "תאריך"] + num_cols + [strong_col, lotto_winners_col, double_winners_col]])

    except Exception as e:

        st.error(f"שגיאה בעיבוד הנתונים: {e}")
