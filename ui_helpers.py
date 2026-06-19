# ui_helpers.py — مكونات واجهة المستخدم القابلة للإعادة

import streamlit as st


def inject_css():
    """حقن CSS لدعم العربية RTL وتنسيق الواجهة"""
    st.markdown("""
    <style>
        /* ─── RTL العام ─── */
        .main .block-container {
            direction: rtl;
            font-family: 'Tahoma', 'Arial Unicode MS', Arial, sans-serif;
            max-width: 1400px;
        }
        /* الشريط الجانبي */
        section[data-testid="stSidebar"] > div:first-child {
            direction: rtl;
        }
        /* حقول الإدخال */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input {
            direction: rtl;
            text-align: right;
        }
        /* الجداول */
        .stDataFrame { direction: ltr; }   /* الجداول تبقى LTR للأرقام */

        /* ─── بطاقات الإحصاء ─── */
        .stat-card {
            border-radius: 12px;
            padding: 18px 14px;
            color: white;
            text-align: center;
            margin: 4px 0;
            min-height: 90px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        .stat-value {
            font-size: 1.75rem;
            font-weight: 700;
            line-height: 1.2;
            letter-spacing: -0.5px;
        }
        .stat-label {
            font-size: 0.83rem;
            opacity: 0.90;
            margin-top: 6px;
            font-weight: 500;
        }

        /* ─── شارة الحالة ─── */
        .badge-active {
            background: #1a7f3c; color: white;
            padding: 3px 10px; border-radius: 12px;
            font-size: 0.82rem; font-weight: 600;
        }
        .badge-deleted {
            background: #C00000; color: white;
            padding: 3px 10px; border-radius: 12px;
            font-size: 0.82rem; font-weight: 600;
        }

        /* ─── ترويسات ─── */
        h1, h2, h3, h4 { direction: rtl; }
        .stTabs [data-baseweb="tab"] { direction: rtl; }

        /* ─── رسائل ─── */
        .stAlert { direction: rtl; text-align: right; }

        /* ─── أزرار ─── */
        .stButton > button { direction: rtl; }

        /* ─── عنوان الشريط الجانبي ─── */
        .sidebar-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: #1F4E79;
            text-align: center;
            padding: 8px 0;
        }

        /* ─── الـ Divider ─── */
        hr { margin: 12px 0; opacity: 0.3; }
    </style>
    """, unsafe_allow_html=True)


def metric_card(label: str, value, icon: str = "",
                color: str = "#1F4E79", text_color: str = "white"):
    """بطاقة إحصاء ملوّنة"""
    if isinstance(value, int):
        val_str = f"{value:,}"
    elif isinstance(value, float):
        val_str = f"{value:,.1f}"
    else:
        val_str = str(value)

    if len(val_str) > 22:
        val_str = val_str[:19] + "..."

    st.markdown(f"""
    <div class="stat-card" style="background:{color};">
        <div class="stat-value">{icon}&nbsp;{val_str}</div>
        <div class="stat-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def pagination_controls(total: int, per_page: int, page_key: str) -> tuple:
    """
    عرض أزرار التنقل بين الصفحات.
    يُرجع (limit, offset) للاستخدام في استعلام SQL.
    """
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    page = st.session_state[page_key]
    total_pages = max(1, (total + per_page - 1) // per_page)

    # تقييد الصفحة في النطاق الصحيح
    page = max(1, min(page, total_pages))
    st.session_state[page_key] = page

    c1, c2, c3, c4, c5 = st.columns([1, 1, 3, 1, 1])

    with c1:
        if st.button("⏮", key=f"{page_key}_first", help="الصفحة الأولى"):
            st.session_state[page_key] = 1
            st.rerun()
    with c2:
        if st.button("◀", key=f"{page_key}_prev", help="الصفحة السابقة"):
            if page > 1:
                st.session_state[page_key] = page - 1
                st.rerun()
    with c3:
        st.markdown(
            f"<div style='text-align:center;padding-top:6px;'>"
            f"صفحة <b>{page}</b> من <b>{total_pages}</b> "
            f"&nbsp;|&nbsp; إجمالي: <b>{total:,}</b></div>",
            unsafe_allow_html=True
        )
    with c4:
        if st.button("▶", key=f"{page_key}_next", help="الصفحة التالية"):
            if page < total_pages:
                st.session_state[page_key] = page + 1
                st.rerun()
    with c5:
        if st.button("⏭", key=f"{page_key}_last", help="الصفحة الأخيرة"):
            st.session_state[page_key] = total_pages
            st.rerun()

    offset = (page - 1) * per_page
    return per_page, offset


def status_badge(is_deleted: int) -> str:
    if is_deleted:
        return '<span class="badge-deleted">🗑 محذوف</span>'
    return '<span class="badge-active">✅ نشط</span>'


def format_json_safe(json_str) -> dict:
    """فك JSON بأمان مع معالجة الأخطاء"""
    if not json_str:
        return {}
    try:
        if isinstance(json_str, dict):
            return json_str
        return __import__('json').loads(json_str)
    except Exception:
        return {}


def reset_page_if_changed(filter_key: str, current_val, page_state_key: str):
    """إعادة ضبط رقم الصفحة إلى 1 عند تغيير الفلتر"""
    prev_key = f"_prev_{filter_key}"
    if st.session_state.get(prev_key) != current_val:
        st.session_state[prev_key] = current_val
        st.session_state[page_state_key] = 1
