# app.py — نظام المعلومات المدنية للمواطنين
import streamlit as st
import db_ali as db
from pathlib import Path

st.set_page_config(
    page_title="المعلومات المدنية للمواطنين",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────
# التصميم المؤسسي الاحترافي — CSS ملف خارجي
# ─────────────────────────────────────────────────
_CSS_FILE = Path(__file__).parent / "style.css"
if _CSS_FILE.exists():
    st.html(f'<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet"><style>{_CSS_FILE.read_text(encoding="utf-8")}</style>')


# ─────────────────────────────────────────────────
# تهيئة قاعدة البيانات
# ─────────────────────────────────────────────────
db.init_db()


# ─────────────────────────────────────────────────
# صفحة تسجيل الدخول
# ─────────────────────────────────────────────────

def show_login():
    st.markdown("""
    <div class="login-container">
        <div class="login-logo">🏛️</div>
        <div class="login-title">المعلومات المدنية للمواطنين</div>
        <div class="login-subtitle">سجّل دخولك للوصول إلى النظام</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("اسم المستخدم", placeholder="admin")
            password = st.text_input("كلمة المرور", type="password", placeholder="••••••")
            submitted = st.form_submit_button("تسجيل الدخول", type="primary", use_container_width=True)

        if submitted:
            if not username.strip() or not password.strip():
                st.error("أدخل اسم المستخدم وكلمة المرور")
            else:
                user = db.authenticate(username, password)
                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")


if not st.session_state.get("logged_in"):
    show_login()
    st.stop()

USER = st.session_state["user"]
ROLE = USER["role"]


def has_permission(action: str) -> bool:
    perms = {
        'admin':  {'view', 'search', 'add', 'edit', 'delete', 'export', 'settings', 'users', 'mukhtars', 'regions', 'backup'},
        'editor': {'view', 'search', 'add', 'edit', 'export', 'mukhtars', 'regions'},
        'viewer': {'view', 'search'},
    }
    return action in perms.get(ROLE, set())


# ─────────────────────────────────────────────────
# حالة التطبيق
# ─────────────────────────────────────────────────
PAGES = ["📋 قائمة الأشخاص", "✏️ تفاصيل / تعديل"]
if has_permission('add'):
    PAGES.append("➕ إضافة شخص")
PAGES.append("📊 إحصائيات")
if has_permission('mukhtars'):
    PAGES.append("👑 المختارون")
if has_permission('regions'):
    PAGES.append("🗺 المناطق والأحياء")
if has_permission('settings'):
    PAGES.append("⚙️ الإعداد")

_DEF = {
    "current_page":    "📋 قائمة الأشخاص",
    "pending_page":    None,
    "selected_id":     None,
    "list_page":       1,
    "search":          "",
    "f_region":        "",
    "f_haya":          "",
    "f_mihna":         "",
    "f_mukhtar":       0,
    "del_filter":      "active",
    "do_export":       False,
    "editing_mukhtar": None,
}
for k, v in _DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state["pending_page"]:
    st.session_state["current_page"] = st.session_state["pending_page"]
    st.session_state["pending_page"] = None

if not st.session_state.get("regions_normalized"):
    try:
        db.normalize_all_regions()
    except Exception:
        pass
    st.session_state["regions_normalized"] = True

if not st.session_state.get("auto_backup_done"):
    try:
        backup = db.auto_backup_if_needed()
        if backup:
            db.cleanup_old_backups(keep_days=30)
    except Exception:
        pass
    st.session_state["auto_backup_done"] = True


# ─────────────────────────────────────────────────
# الشريط الجانبي
# ─────────────────────────────────────────────────
PAGE_ROWS_OPTS = [25, 50, 100, 200]


def nav_btn(label: str):
    active = st.session_state["current_page"] == label
    if st.sidebar.button(label, use_container_width=True,
                         type="primary" if active else "secondary",
                         key=f"nav_{label}"):
        st.session_state["current_page"] = label
        st.rerun()


with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:12px 0 6px">
        <div style="font-size:2rem">🏛️</div>
        <div style="font-size:0.95rem;font-weight:800;color:#fff !important">
            المعلومات المدنية للمواطنين
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ─ معلومات المستخدم ─
    role_label = db.ROLES.get(ROLE, ROLE)
    st.markdown(
        f"<div style='text-align:center;padding:2px 0;font-size:0.82rem'>"
        f"<b style='color:#d4a534 !important'>{USER['display_name']}</b>"
        f"<br><span style='font-size:0.72rem;color:rgba(255,255,255,0.5) !important'>{role_label}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if st.button("🚪 تسجيل الخروج", key="logout_btn", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.divider()

    # ─ قائمة التنقل ─
    for p in PAGES:
        nav_btn(p)

    st.divider()
    per_page = st.selectbox("سجلات/صفحة", PAGE_ROWS_OPTS, index=1, key="per_page")

    # ─ حقوق في أسفل الشريط ─
    st.divider()
    st.markdown(
        "<div class='sidebar-footer'>"
        "<div class='sidebar-footer-title'>تم إنشاء النظام بواسطة</div>"
        "<div class='sidebar-footer-name'>احمد الذهبي</div>"
        "<div class='sidebar-footer-phone'>07711228946</div>"
        "<div class='sidebar-footer-phone'>07822667735</div>"
        "</div>",
        unsafe_allow_html=True,
    )

# ─── شريط العنوان + الساعة أعلى المحتوى ───
import streamlit.components.v1 as components
components.html("""
<div style="background:#fff;border-bottom:2px solid #d1d5db;padding:8px 20px;display:flex;
    align-items:center;justify-content:space-between;border-radius:0 0 10px 10px;
    font-family:'Cairo',sans-serif;direction:rtl;margin-bottom:4px">
    <div style="display:flex;align-items:center;gap:10px">
        <span style="font-size:1.2rem">🏛️</span>
        <span style="font-size:1rem;font-weight:800;color:#0a3d62">المعلومات المدنية للمواطنين</span>
    </div>
    <div style="display:flex;align-items:center;gap:16px;direction:ltr">
        <span id="topDate" style="font-size:0.82rem;color:#4b5563"></span>
        <span id="topTime" style="font-size:1.1rem;font-weight:700;color:#b8860b;font-variant-numeric:tabular-nums">--:--:--</span>
    </div>
</div>
<script>
function updateTopClock(){
    var now=new Date(),utc=now.getTime()+now.getTimezoneOffset()*60000;
    var bd=new Date(utc+3*3600000),h=bd.getHours(),m=bd.getMinutes(),s=bd.getSeconds();
    var p=function(n){return String(n).padStart(2,'0')};
    var el=document.getElementById('topTime');
    if(el)el.textContent=p(h)+':'+p(m)+':'+p(s);
    var days=['الأحد','الإثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت'];
    var months=['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
    var dEl=document.getElementById('topDate');
    if(dEl)dEl.textContent=days[bd.getDay()]+' '+bd.getDate()+' '+months[bd.getMonth()]+' '+bd.getFullYear();
}
setInterval(updateTopClock,1000);updateTopClock();
</script>
""", height=52)


def goto(page: str, selected_id: int = None):
    st.session_state["pending_page"] = page
    if selected_id is not None:
        st.session_state["selected_id"] = selected_id
    st.rerun()


# ─────────────────────────────────────────────────
# مكوّنات مشتركة
# ─────────────────────────────────────────────────

def pager(total: int, page: int, per: int, key_prefix: str = "pg") -> int:
    pages = max(1, (total + per - 1) // per)
    if pages <= 1:
        return 1
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("◀ السابق", key=f"{key_prefix}_prev", disabled=(page <= 1)):
            return max(1, page - 1)
    with c2:
        st.markdown(
            f"<div style='text-align:center;padding-top:8px;font-weight:600;color:var(--primary)'>"
            f"صفحة {page} من {pages}</div>",
            unsafe_allow_html=True,
        )
    with c3:
        if st.button("التالي ▶", key=f"{key_prefix}_next", disabled=(page >= pages)):
            return min(pages, page + 1)
    return page


def field_row(label: str, value):
    v = str(value) if value is not None else "—"
    if not v.strip() or v.lower() in ('nan', 'none', ''):
        v = "—"
    st.markdown(
        f"<div class='field-row'>"
        f"<span class='field-label'>{label}</span>"
        f"<span class='field-value'>{v}</span></div>",
        unsafe_allow_html=True,
    )


def show_dup_warning(dups: list):
    if dups:
        names = "  |  ".join(f"[{d['id']}] {d['الاسم']}" for d in dups[:4])
        st.markdown(
            f"<div class='dup-warn'>⚠️ <b>اسم مكرر محتمل:</b> {names}</div>",
            unsafe_allow_html=True,
        )


def mukhtar_select(key: str, region: str = '', def_id: int = None) -> int | None:
    if region:
        mkhs = db.get_mukhtars_for_region(region)
        opts = {0: '— بدون مختار —', **{m['id']: m['الاسم'] for m in mkhs}}
    else:
        grouped = db.get_mukhtars_grouped_by_region()
        opts = {0: '— بدون مختار —'}
        for reg, mkhs in grouped.items():
            for m in mkhs:
                label = f"({reg}) {m['الاسم']}" if reg != 'غير مرتبط' else m['الاسم']
                if m['id'] not in opts:
                    opts[m['id']] = label
    def_val = def_id if def_id in opts else 0
    sel = st.selectbox(
        "المختار", list(opts.keys()),
        format_func=lambda x: opts[x],
        index=list(opts.keys()).index(def_val),
        key=key,
    )
    return sel or None


def region_haya_selects(key_pfx: str, def_region='', def_haya=''):
    c1, c2 = st.columns(2)
    with c1:
        reg_opts = [''] + db.MAIN_REGIONS
        reg_idx = reg_opts.index(def_region) if def_region in reg_opts else 0
        region = st.selectbox("المنطقة", reg_opts, index=reg_idx, key=f"{key_pfx}_region")
    with c2:
        db_h = [n['الاسم'] for n in db.get_neighborhoods(region)] if region else []
        pr_h = db.get_hayas_for_region(region) if region else []
        h_opts = [''] + sorted(set(db_h + pr_h))
        h_idx = h_opts.index(def_haya) if def_haya in h_opts else 0
        haya = st.selectbox("الحي", h_opts, index=h_idx, key=f"{key_pfx}_haya")
    return region, haya


# ─────────────────────────────────────────────────
# 1. قائمة الأشخاص
# ─────────────────────────────────────────────────

def page_list():
    st.markdown("# 📋 قائمة الأشخاص")

    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
        search = st.text_input("🔍 بحث (اسم / هاتف / عنوان)",
                               value=st.session_state["search"],
                               placeholder="ابحث هنا...", key="search_input")
    with c2:
        mihna = st.text_input("المهنة", value=st.session_state["f_mihna"], key="f_mihna_in")
    with c3:
        del_opts = {"active": "النشطة", "deleted": "المحذوفة", "all": "الكل"}
        del_filter = st.selectbox("الحالة", list(del_opts.keys()),
                                  format_func=lambda x: del_opts[x], key="del_filter_sel")

    region, haya = region_haya_selects("list",
                                       def_region=st.session_state["f_region"],
                                       def_haya=st.session_state["f_haya"])
    f_mukhtar = mukhtar_select("list_mukhtar", region=region,
                               def_id=st.session_state["f_mukhtar"] or None)

    filters_changed = (
        search != st.session_state["search"] or
        mihna != st.session_state["f_mihna"] or
        region != st.session_state["f_region"] or
        haya != st.session_state["f_haya"] or
        (f_mukhtar or 0) != (st.session_state["f_mukhtar"] or 0) or
        del_filter != st.session_state["del_filter"]
    )
    if filters_changed:
        st.session_state.update(search=search, f_mihna=mihna, f_region=region,
                                f_haya=haya, f_mukhtar=f_mukhtar or 0,
                                del_filter=del_filter, list_page=1)
        st.rerun()

    per = st.session_state.get("per_page", 50)
    offset = (st.session_state["list_page"] - 1) * per

    rows, total = db.get_persons(
        search=st.session_state["search"],
        region=st.session_state["f_region"],
        haya=st.session_state["f_haya"],
        mihna=st.session_state["f_mihna"],
        mukhtar_id=st.session_state["f_mukhtar"] or None,
        deleted_filter=st.session_state["del_filter"],
        limit=per, offset=offset,
    )

    ha, hb, hc = st.columns([5, 2, 2])
    with ha:
        st.markdown(
            f"<div style='padding:8px 0;font-size:0.9rem;color:var(--text-sec)'>"
            f"النتائج: <b style='color:var(--primary)'>{total:,}</b> "
            f"| الصفحة: <b>{st.session_state['list_page']}</b></div>",
            unsafe_allow_html=True,
        )
    with hb:
        if has_permission('add'):
            if st.button("➕ إضافة شخص جديد", use_container_width=True):
                goto("➕ إضافة شخص")
    with hc:
        if has_permission('export'):
            if st.button(f"📤 تصدير ({total:,})", use_container_width=True, key="export_trigger"):
                st.session_state["do_export"] = True

    if st.session_state.get("do_export"):
        st.session_state["do_export"] = False
        with st.spinner("جارٍ تحضير ملف Excel..."):
            excel_bytes = db.export_to_excel(
                search=st.session_state["search"],
                region=st.session_state["f_region"],
                haya=st.session_state["f_haya"],
                mihna=st.session_state["f_mihna"],
                mukhtar_id=st.session_state["f_mukhtar"] or None,
                deleted_filter=st.session_state["del_filter"],
            )
        st.download_button("⬇️ تحميل الملف", data=excel_bytes,
                           file_name="المعلومات_المدنية.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="dl_excel")

    if not rows:
        st.info("لا توجد نتائج مطابقة للفلاتر المحددة.")
        return

    # رأس الجدول + البيانات بأعمدة ثابتة
    _W = [3, 1, 2, 1.5, 2, 0.5]
    hdr = st.columns(_W)
    for col, txt in zip(hdr, ["الاسم", "الحالة", "المهنة", "المنطقة", "الهاتف", ""]):
        col.markdown(f"<div style='background:#0a3d62;color:#fff;font-weight:700;font-size:0.84rem;"
                     f"padding:8px 4px;border-radius:4px;text-align:center'>{txt}</div>",
                     unsafe_allow_html=True)

    for r in rows:
        deleted = r["is_deleted"] == 1
        name = r["الاسم"] or "—"
        hz = r.get("الحالة_الزوجية") or ""
        mhna = r["المهنة"] or "—"
        reg = r.get("المنطقة") or r["القضاء"] or "—"
        telph = r["الهاتف"] or "—"
        fam_ico = " 👨‍👩‍👧" if r.get("family_id") else ""
        _s = "font-size:.85rem;padding-top:8px;text-align:center;"

        c1, c2, c3, c4, c5, c6 = st.columns(_W)
        with c1:
            lbl = f"{'🗑 ' if deleted else ''}{name}{fam_ico}"
            if st.button(lbl, key=f"open_{r['id']}", use_container_width=True):
                goto("✏️ تفاصيل / تعديل", r["id"])
        c2.markdown(f"<div style='{_s}color:#4a5568'>{hz}</div>", unsafe_allow_html=True)
        c3.markdown(f"<div style='{_s}color:#1a1a2e'>{mhna}</div>", unsafe_allow_html=True)
        c4.markdown(f"<div style='{_s}color:#1a6fa0;font-weight:600'>{reg}</div>", unsafe_allow_html=True)
        c5.markdown(f"<div style='{_s}direction:ltr;color:#1a1a2e'>{telph}</div>", unsafe_allow_html=True)
        with c6:
            if has_permission('delete'):
                if not deleted:
                    if st.button("🗑", key=f"del_{r['id']}", help="حذف"):
                        db.soft_delete(r["id"])
                        st.rerun()
                else:
                    if st.button("↩", key=f"rst_{r['id']}", help="استعادة"):
                        db.restore(r["id"])
                        st.rerun()

    st.divider()
    new_pg = pager(total, st.session_state["list_page"], per, "list")
    if new_pg != st.session_state["list_page"]:
        st.session_state["list_page"] = new_pg
        st.rerun()


# ─────────────────────────────────────────────────
# 2. تفاصيل / تعديل
# ─────────────────────────────────────────────────

def page_details():
    st.markdown("# ✏️ تفاصيل الشخص")

    pid = st.session_state.get("selected_id")
    if not pid:
        st.warning("اختر شخصاً من القائمة أولاً.")
        if st.button("← العودة للقائمة"):
            goto("📋 قائمة الأشخاص")
        return

    person = db.get_person(pid)
    if not person:
        st.error(f"السجل {pid} غير موجود.")
        if st.button("← العودة للقائمة"):
            goto("📋 قائمة الأشخاص")
        return

    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← قائمة"):
            goto("📋 قائمة الأشخاص")
    with col_title:
        status = "🗑 محذوف" if person["is_deleted"] else "✅ نشط"
        fam = f"  |  👨‍👩‍👧 أسرة #{person['family_id']}" if person.get("family_id") else ""
        st.markdown(
            f"<div class='gov-card'>"
            f"<div class='gov-card-title'>{person['الاسم'] or 'بدون اسم'}</div>"
            f"<div class='gov-card-sub'>{status}{fam} | التسلسل: {pid}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    tabs_list = ["👁 عرض"]
    if has_permission('edit'):
        tabs_list.append("📝 تعديل")
    tabs_list.append("👨‍👩‍👧 الأسرة")
    tabs = st.tabs(tabs_list)

    with tabs[0]:
        fields_html = ""
        detail_fields = [
            ("الاسم الرباعي واللقب", person.get("الاسم")),
            ("تاريخ الميلاد", person.get("التولد")),
            ("المهنة", person.get("المهنة")),
            ("الحالة الزوجية", person.get("الحالة_الزوجية")),
            ("الصلة بالأسرة", person.get("الصلة")),
            ("المنطقة", person.get("المنطقة")),
            ("القضاء (أصلي)", person.get("القضاء")),
            ("الحي", person.get("الحي")),
            ("عنوان السكن", person.get("العنوان")),
            ("المحل / الزقاق", person.get("المحل")),
            ("رقم الهاتف", person.get("الهاتف")),
            ("المختار", person.get("mukhtar_name")),
            ("تاريخ الإضافة", person.get("created_at")),
        ]
        for lbl, val in detail_fields:
            v = str(val) if val is not None else "—"
            if not v.strip() or v.lower() in ('nan', 'none', ''):
                v = "—"
            fields_html += (
                f"<div class='field-row'>"
                f"<span class='field-label'>{lbl}</span>"
                f"<span class='field-value'>{v}</span></div>"
            )
        st.markdown(f"<div class='detail-card'>{fields_html}</div>", unsafe_allow_html=True)
        if has_permission('delete'):
            if not person["is_deleted"]:
                if st.button("🗑 حذف ناعم", key="v_del", type="secondary"):
                    db.soft_delete(pid)
                    goto("📋 قائمة الأشخاص")
            else:
                if st.button("↩ استعادة", key="v_rst", type="secondary"):
                    db.restore(pid)
                    st.rerun()

    if has_permission('edit'):
        with tabs[1]:
            with st.form(key=f"edit_{pid}"):
                اسم = st.text_input("الاسم الرباعي واللقب", value=person.get("الاسم") or "")
                c1, c2 = st.columns(2)
                with c1:
                    تولد = st.text_input("تاريخ الميلاد", value=person.get("التولد") or "")
                    قضاء = st.text_input("القضاء (أصلي)", value=person.get("القضاء") or "")
                    محل = st.text_input("المحل / الزقاق", value=person.get("المحل") or "")
                    hz_idx = db.MARITAL_STATUS.index(person.get("الحالة_الزوجية") or "") \
                        if person.get("الحالة_الزوجية") in db.MARITAL_STATUS else 0
                    حالة_ز = st.selectbox("الحالة الزوجية", db.MARITAL_STATUS, index=hz_idx)
                with c2:
                    مهنة = st.text_input("المهنة", value=person.get("المهنة") or "")
                    عنوان = st.text_input("عنوان السكن", value=person.get("العنوان") or "")
                    هاتف = st.text_input("رقم الهاتف", value=person.get("الهاتف") or "")
                    صلة_opts = [''] + db.FAMILY_RELATIONS
                    صلة_idx = صلة_opts.index(person.get("الصلة") or "") \
                        if person.get("الصلة") in صلة_opts else 0
                    صلة = st.selectbox("الصلة بالأسرة", صلة_opts, index=صلة_idx)

                st.markdown("---")
                cur_region = person.get("المنطقة") or ""
                cur_haya = person.get("الحي") or ""
                reg_opts = [''] + db.MAIN_REGIONS
                reg_idx = reg_opts.index(cur_region) if cur_region in reg_opts else 0
                منطقة = st.selectbox("المنطقة الرئيسية", reg_opts, index=reg_idx, key=f"e_reg_{pid}")

                db_h = [n['الاسم'] for n in db.get_neighborhoods(منطقة)] if منطقة else []
                pr_h = db.get_hayas_for_region(منطقة) if منطقة else []
                h_opts = [''] + sorted(set(db_h + pr_h))
                if cur_haya and cur_haya not in h_opts:
                    h_opts.append(cur_haya)
                حي = st.selectbox("الحي", h_opts,
                                   index=h_opts.index(cur_haya) if cur_haya in h_opts else 0,
                                   key=f"e_hay_{pid}")

                mid_sel = mukhtar_select(f"e_muk_{pid}", region=منطقة, def_id=person.get("mukhtar_id"))
                save = st.form_submit_button("💾 حفظ التغييرات", type="primary")

            dups = db.find_duplicate_persons(اسم if 'اسم' in dir() else '', exclude_id=pid)
            show_dup_warning(dups)

            if save:
                dup_check = db.find_duplicate_persons(اسم, exclude_id=pid)
                if dup_check:
                    dup_ids = ' ، '.join(f"التسلسل {d['id']}" for d in dup_check)
                    st.error(f"⛔ لا يمكن الحفظ — يوجد تكرار في الاسم! ({dup_ids})")
                    for d in dup_check:
                        st.warning(f"🔁 مكرر: [{d['id']}] {d['الاسم']} — {d.get('المنطقة') or ''} / {d.get('المهنة') or ''}")
                else:
                    ok = db.update_person(
                        pid, الاسم=اسم, التولد=تولد, المهنة=مهنة, القضاء=قضاء,
                        العنوان=عنوان, المحل=محل, الهاتف=هاتف,
                        المنطقة=منطقة, الحي=حي, mukhtar_id=mid_sel,
                        الحالة_الزوجية=حالة_ز, الصلة=صلة,
                    )
                    if ok:
                        st.success("✅ تم الحفظ بنجاح")
                        st.rerun()

    family_tab_idx = 2 if has_permission('edit') else 1
    with tabs[family_tab_idx]:
        _family_tab(person)


def _family_tab(person: dict):
    pid = person["id"]
    family_id = person.get("family_id")

    if not family_id:
        st.info("هذا الشخص غير مرتبط بأسرة بعد.")
        if has_permission('edit'):
            if st.button("🏠 إنشاء أسرة جديدة (هذا الشخص رب الأسرة)", key="create_fam", type="primary"):
                fid = db.create_family(pid)
                st.success(f"✅ تم إنشاء الأسرة رقم {fid}")
                st.rerun()
            st.markdown("**أو ربط بأسرة موجودة:**")
            with st.form("link_existing_fam"):
                fid_in = st.number_input("رقم الأسرة", min_value=1, step=1, key="link_fid")
                صلة_in = st.selectbox("الصلة", db.FAMILY_RELATIONS, key="link_sila")
                if st.form_submit_button("ربط"):
                    if db.link_to_family(pid, int(fid_in), صلة_in):
                        st.success(f"✅ تم الربط بالأسرة {fid_in}")
                        st.rerun()
        return

    members = db.get_family_members(family_id)
    head = next((m for m in members if m.get("الصلة") == "رب الأسرة"), None)
    head_name = head["الاسم"] if head else "غير محدد"

    col_title, col_exp = st.columns([5, 2])
    with col_title:
        st.markdown(
            f"<div class='gov-card'>"
            f"<div class='gov-card-title'>🏠 أسرة رقم {family_id} — رب الأسرة: {head_name}</div>"
            f"<div class='gov-card-sub'>{len(members)} فرد</div></div>",
            unsafe_allow_html=True,
        )
    with col_exp:
        fam_excel = db.export_family_excel(family_id)
        st.download_button("📤 تصدير الأسرة", data=fam_excel,
                           file_name=f"أسرة_{family_id}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key=f"dl_fam_{family_id}")

    rel_icons = {"رب الأسرة": "👨", "زوجة": "👩", "ابن": "👦", "ابنة": "👧",
                 "أب": "👴", "أم": "👵", "أخ": "🧑", "أخت": "👩‍🦰"}

    for m in members:
        icon = rel_icons.get(m.get("الصلة") or "", "👤")
        deleted_style = "opacity:.5;" if m["is_deleted"] else ""
        st.markdown(
            f"<div class='fam-member' style='{deleted_style}'>"
            f"<b>{icon} {m['الاسم'] or '—'}</b>  "
            f"<span style='color:var(--text-sec);font-size:.85rem'>"
            f"({m.get('الصلة') or '—'})  ·  {m.get('التولد') or ''}  "
            f"·  {m.get('المهنة') or ''}"
            f"</span></div>",
            unsafe_allow_html=True,
        )
        ca, cb, cc = st.columns([2, 2, 1])
        with ca:
            if st.button("✏️ تفاصيل", key=f"fam_open_{m['id']}", use_container_width=True):
                goto("✏️ تفاصيل / تعديل", m["id"])
        with cb:
            if has_permission('edit'):
                cur_sila = m.get("الصلة") or ""
                صلة_opts = [''] + db.FAMILY_RELATIONS
                new_sila = st.selectbox("الصلة", صلة_opts,
                                        index=صلة_opts.index(cur_sila) if cur_sila in صلة_opts else 0,
                                        key=f"sila_{m['id']}")
                if new_sila != cur_sila:
                    db.link_to_family(m["id"], family_id, new_sila)
                    st.rerun()
        with cc:
            if has_permission('edit') and m["id"] != pid:
                if st.button("✂️", key=f"unlink_{m['id']}", help="إزالة من الأسرة"):
                    db.unlink_from_family(m["id"])
                    st.rerun()

    if has_permission('edit'):
        st.markdown("---")
        with st.expander("➕ إضافة فرد موجود لهذه الأسرة"):
            search_q = st.text_input("ابحث باسم الشخص", key=f"fam_search_{family_id}")
            if search_q.strip():
                results = db.search_persons_for_family(search_q, exclude_family_id=family_id)
                for res in results:
                    ca, cb = st.columns([4, 2])
                    ca.markdown(
                        f"{res['الاسم']}  "
                        f"<span style='color:var(--text-sec);font-size:.82rem'>"
                        f"{res.get('التولد') or ''}  {res.get('المهنة') or ''}</span>",
                        unsafe_allow_html=True,
                    )
                    with cb:
                        صلة_add = st.selectbox("الصلة", db.FAMILY_RELATIONS, key=f"add_sila_{res['id']}")
                        if st.button("إضافة", key=f"add_fam_{res['id']}"):
                            db.link_to_family(res["id"], family_id, صلة_add)
                            st.rerun()
        with st.expander("⚠️ فصل هذا الشخص عن الأسرة"):
            if st.button("✂️ فصل من الأسرة", key="unlink_self", type="secondary"):
                db.unlink_from_family(pid)
                st.rerun()


# ─────────────────────────────────────────────────
# 3. إضافة شخص
# ─────────────────────────────────────────────────

def page_add():
    st.markdown("# ➕ إضافة شخص جديد")

    اسم = st.text_input("الاسم الرباعي واللقب *", key="add_name_pre")
    dups = db.find_duplicate_persons(اسم) if اسم.strip() else []
    show_dup_warning(dups)

    with st.form("add_form"):
        st.text_input("الاسم الرباعي واللقب *", value=اسم, key="add_name_form", disabled=True)
        c1, c2 = st.columns(2)
        with c1:
            تولد = st.text_input("تاريخ الميلاد", key="add_twld")
            قضاء = st.text_input("القضاء (أصلي)", key="add_qdha")
            محل = st.text_input("المحل / الزقاق", key="add_mhl")
            حالة_ز = st.selectbox("الحالة الزوجية", db.MARITAL_STATUS, key="add_hz")
        with c2:
            مهنة = st.text_input("المهنة", key="add_mhna")
            عنوان = st.text_input("عنوان السكن", key="add_adr")
            هاتف = st.text_input("رقم الهاتف", key="add_phn")
            صلة = st.selectbox("الصلة بالأسرة", [''] + db.FAMILY_RELATIONS, key="add_sila")

        st.markdown("---")
        reg_opts = [''] + db.MAIN_REGIONS
        منطقة = st.selectbox("المنطقة الرئيسية", reg_opts, key="add_reg")
        db_h = [n['الاسم'] for n in db.get_neighborhoods(منطقة)] if منطقة else []
        h_opts = ['', '(أدخل حياً جديداً أدناه)'] + db_h
        حي_sel = st.selectbox("الحي (اختر من القائمة)", h_opts, key="add_hay_sel")
        حي_new = st.text_input("أو أدخل حياً جديداً", key="add_hay_new")
        حي = حي_new.strip() if حي_new.strip() else ('' if حي_sel.startswith('(') else حي_sel)
        mid_sel = mukhtar_select("add_muk", region=منطقة)

        if st.form_submit_button("➕ إضافة", type="primary"):
            if not اسم.strip():
                st.error("الاسم حقل مطلوب")
            else:
                dup_check = db.find_duplicate_persons(اسم)
                if dup_check:
                    dup_ids = ' ، '.join(f"التسلسل {d['id']}" for d in dup_check)
                    st.error(f"⛔ لا يمكن الإضافة — يوجد تكرار في الاسم! ({dup_ids})")
                    for d in dup_check:
                        st.warning(f"🔁 مكرر: [{d['id']}] {d['الاسم']} — {d.get('المنطقة') or ''} / {d.get('المهنة') or ''}")
                else:
                    new_id = db.add_person(
                        الاسم=اسم, التولد=تولد, المهنة=مهنة, القضاء=قضاء or منطقة,
                        العنوان=عنوان, المحل=محل, الهاتف=هاتف,
                        الشيت="يدوي", المنطقة=منطقة, الحي=حي,
                        mukhtar_id=mid_sel, الحالة_الزوجية=حالة_ز, الصلة=صلة,
                    )
                    if حي and منطقة:
                        db.add_neighborhood(حي, منطقة)
                    st.success(f"✅ تمت الإضافة بنجاح (التسلسل: {new_id})")
                    goto("✏️ تفاصيل / تعديل", new_id)


# ─────────────────────────────────────────────────
# 4. إحصائيات
# ─────────────────────────────────────────────────

def page_stats():
    try:
        import plotly.express as px
        HAS_PLOTLY = True
    except ImportError:
        HAS_PLOTLY = False

    st.markdown("# 📊 إحصائيات البيانات")
    s = db.get_stats()

    cols = st.columns(4)
    for col, (lbl, val) in zip(cols, [
        ("إجمالي السجلات", s['total']),
        ("النشطة", s['active']),
        ("المحذوفة", s['deleted']),
        ("بأسماء كاملة", s['with_name']),
    ]):
        col.markdown(
            f"<div class='stat-card'>"
            f"<div class='stat-num'>{val:,}</div>"
            f"<div class='stat-lbl'>{lbl}</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    cols2 = st.columns(3)
    for col, (lbl, val) in zip(cols2, [
        ("المختارون", s['mukhtars']),
        ("الأحياء", s['neighborhoods']),
        ("المهن الفريدة", s['mihnas']),
    ]):
        col.markdown(
            f"<div class='stat-card gold'>"
            f"<div class='stat-num'>{val:,}</div>"
            f"<div class='stat-lbl'>{lbl}</div></div>",
            unsafe_allow_html=True,
        )

    st.divider()
    t1, t2, t3, t4 = st.tabs(["🗺 المناطق", "🏘 الأحياء", "💼 المهن", "💑 الحالة الزوجية"])

    def bar_chart(col_name: str, limit: int = 30):
        data = db.get_distribution(col_name, limit)
        if not data:
            st.info("لا توجد بيانات.")
            return
        labels = [d[col_name] for d in data]
        counts = [d["عدد"] for d in data]
        if HAS_PLOTLY:
            import plotly.express as px
            fig = px.bar(x=counts, y=labels, orientation='h',
                         labels={"x": "العدد", "y": col_name},
                         height=max(350, len(labels) * 22),
                         color_discrete_sequence=['#0a3d62'])
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                font=dict(family="Cairo", size=13),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            import pandas as pd
            st.dataframe(pd.DataFrame({"القيمة": labels, "العدد": counts}), use_container_width=True)

    with t1: bar_chart("المنطقة", 5)
    with t2: bar_chart("الحي", 30)
    with t3: bar_chart("المهنة", 30)
    with t4: bar_chart("الحالة_الزوجية", 10)


# ─────────────────────────────────────────────────
# 5. المختارون
# ─────────────────────────────────────────────────

def page_mukhtars():
    st.markdown("# 👑 إدارة المختارين")

    if "editing_mukhtar" not in st.session_state:
        st.session_state["editing_mukhtar"] = None

    tab_g, tab_sh, tab_all, tab_add = st.tabs(
        ["🌍 علي الغربي", "🌏 علي الشرقي", "📋 كل المختارين", "➕ إضافة مختار"]
    )

    def _show_mukhtar_card(m: dict, tab_key: str):
        regions_str = ''
        hayas_str = ''
        if m.get('المناطق'):
            regions_str = ' · '.join(dict.fromkeys(str(m['المناطق']).split(' | ')))
        if m.get('الأحياء'):
            hayas_str = ' · '.join(dict.fromkeys(str(m['الأحياء']).split(' | ')))

        st.markdown(
            f"<div class='gov-card'>"
            f"<div class='gov-card-title'>👑 {m['الاسم']}</div>"
            f"<div class='gov-card-sub'>"
            f"📞 {m['الهاتف'] or '—'}"
            f"{'  |  🗺 ' + regions_str if regions_str else ''}"
            f"{'  |  🏘 ' + hayas_str if hayas_str else ''}"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        if has_permission('edit'):
            ca, cb = st.columns([1, 1])
            with ca:
                if st.button("✏️ تعديل", key=f"btn_edit_{tab_key}_{m['id']}", use_container_width=True):
                    st.session_state["editing_mukhtar"] = (
                        None if st.session_state["editing_mukhtar"] == m['id'] else m['id'])
                    st.rerun()
            with cb:
                if has_permission('delete'):
                    if st.button("🗑 حذف", key=f"btn_del_{tab_key}_{m['id']}",
                                 use_container_width=True, type="secondary"):
                        db.delete_mukhtar(m['id'])
                        st.session_state["editing_mukhtar"] = None
                        st.rerun()

            if st.session_state["editing_mukhtar"] == m['id']:
                _edit_mukhtar_form(m)

        st.markdown("---")

    def _edit_mukhtar_form(m: dict):
        full = db.get_mukhtar(m['id'])
        linked_ids = {n['id'] for n in (full.get('neighborhoods') or [])}
        with st.form(f"edit_muk_{m['id']}"):
            c1, c2 = st.columns(2)
            with c1:
                new_name = st.text_input("الاسم", value=m['الاسم'], key=f"mn_{m['id']}")
            with c2:
                new_phone = st.text_input("الهاتف", value=m['الهاتف'] or '', key=f"mp_{m['id']}")

            all_nb = db.get_neighborhoods()
            sel_ids = []
            if all_nb:
                st.markdown("**الأحياء المرتبطة:**")
                for reg in db.MAIN_REGIONS:
                    reg_nbs = [n for n in all_nb if n['المنطقة'] == reg]
                    if reg_nbs:
                        st.markdown(f"<div class='region-sep'>📍 {reg}</div>", unsafe_allow_html=True)
                        half = (len(reg_nbs) + 1) // 2
                        cl, cr = st.columns(2)
                        for idx, nb in enumerate(reg_nbs):
                            col = cl if idx < half else cr
                            with col:
                                if st.checkbox(nb['الاسم'], value=(nb['id'] in linked_ids),
                                               key=f"nbck_{m['id']}_{nb['id']}"):
                                    sel_ids.append(nb['id'])

            sc1, sc2 = st.columns(2)
            with sc1:
                if st.form_submit_button("💾 حفظ", type="primary"):
                    dup = db.find_duplicate_mukhtar(new_name, exclude_id=m['id'])
                    if dup:
                        st.error(f"⛔ يوجد مختار مكرر بنفس الاسم: [{dup['id']}] {dup['الاسم']}")
                    else:
                        db.update_mukhtar(m['id'], new_name, new_phone)
                        db.set_mukhtar_neighborhoods(m['id'], sel_ids)
                        st.session_state["editing_mukhtar"] = None
                        st.success("✅ تم الحفظ")
                        st.rerun()
            with sc2:
                if st.form_submit_button("❌ إلغاء"):
                    st.session_state["editing_mukhtar"] = None
                    st.rerun()

    grouped = db.get_mukhtars_grouped_by_region()
    all_mkh = db.get_mukhtars()

    with tab_g:
        mkhs_g = grouped.get('علي الغربي', [])
        st.caption(f"{len(mkhs_g)} مختار في منطقة علي الغربي")
        if not mkhs_g:
            st.info("لا يوجد مختارون مرتبطون بمنطقة علي الغربي.")
        for m in mkhs_g:
            _show_mukhtar_card(m, "g")

    with tab_sh:
        mkhs_sh = grouped.get('علي الشرقي', [])
        st.caption(f"{len(mkhs_sh)} مختار في منطقة علي الشرقي")
        if not mkhs_sh:
            st.info("لا يوجد مختارون مرتبطون بمنطقة علي الشرقي.")
        for m in mkhs_sh:
            _show_mukhtar_card(m, "sh")

    with tab_all:
        st.caption(f"إجمالي المختارين: {len(all_mkh)}")
        if not all_mkh:
            st.info("لا يوجد مختارون مضافون بعد.")
        for m in all_mkh:
            _show_mukhtar_card(m, "all")

    with tab_add:
        if not has_permission('edit'):
            st.warning("ليس لديك صلاحية لإضافة مختار.")
        else:
            with st.form("add_mukhtar_form"):
                st.markdown("**بيانات المختار الجديد:**")
                c1, c2 = st.columns(2)
                with c1:
                    mname = st.text_input("اسم المختار *", key="new_m_name")
                with c2:
                    mphone = st.text_input("رقم الهاتف", key="new_m_phone")

                all_nb = db.get_neighborhoods()
                sel_ids = []
                if all_nb:
                    st.markdown("**اختر الأحياء المرتبطة (اختياري):**")
                    for reg in db.MAIN_REGIONS:
                        reg_nbs = [n for n in all_nb if n['المنطقة'] == reg]
                        if reg_nbs:
                            st.markdown(f"<div class='region-sep'>📍 {reg}</div>", unsafe_allow_html=True)
                            half = (len(reg_nbs) + 1) // 2
                            cl, cr = st.columns(2)
                            for idx, nb in enumerate(reg_nbs):
                                with (cl if idx < half else cr):
                                    if st.checkbox(nb['الاسم'], key=f"new_nb_{nb['id']}"):
                                        sel_ids.append(nb['id'])

                if st.form_submit_button("➕ إضافة المختار", type="primary"):
                    if not mname.strip():
                        st.error("الاسم مطلوب")
                    else:
                        dup = db.find_duplicate_mukhtar(mname)
                        if dup:
                            st.error(f"⛔ يوجد مختار مكرر: [{dup['id']}] {dup['الاسم']}")
                        else:
                            mid = db.add_mukhtar(mname, mphone)
                            db.set_mukhtar_neighborhoods(mid, sel_ids)
                            st.success(f"✅ تمت إضافة المختار: {mname}")
                            st.rerun()


# ─────────────────────────────────────────────────
# 6. المناطق والأحياء
# ─────────────────────────────────────────────────

def page_regions():
    st.markdown("# 🗺 المناطق والأحياء")
    tab_g, tab_sh = st.tabs(["🌍 علي الغربي", "🌏 علي الشرقي"])

    def region_tab(region: str):
        nbs = db.get_neighborhoods(region)
        st.markdown(
            f"<div class='gov-card'>"
            f"<div class='gov-card-title'>منطقة: {region}</div>"
            f"<div class='gov-card-sub'>{len(nbs)} حي مسجل</div></div>",
            unsafe_allow_html=True,
        )

        if has_permission('edit'):
            with st.form(f"add_nb_{region}"):
                c1, c2 = st.columns([4, 1])
                with c1:
                    nb_name = st.text_input("اسم الحي الجديد", key=f"nbn_{region}")
                with c2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("➕ إضافة"):
                        if nb_name.strip():
                            dup_nb = db.find_duplicate_neighborhood(nb_name.strip(), region)
                            if dup_nb:
                                st.error(f"⛔ الحي «{nb_name.strip()}» موجود مسبقاً في {region}")
                            else:
                                nid = db.add_neighborhood(nb_name.strip(), region)
                                if nid:
                                    st.success(f"✅ {nb_name}")
                                    st.rerun()
                        else:
                            st.error("أدخل اسم الحي")

        if not nbs:
            st.info("لا توجد أحياء مسجلة لهذه المنطقة بعد.")
            return

        for nb in nbs:
            mkhs = db.get_mukhtars_for_neighborhood(nb['id'])
            mnames = ' · '.join(m['الاسم'] for m in mkhs) if mkhs else '—'
            _, cnt = db.get_persons(haya=nb['الاسم'], region=region, limit=1)
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.markdown(f"<b style='color:var(--primary)'>{nb['الاسم']}</b>", unsafe_allow_html=True)
            c2.markdown(f"<span style='color:var(--text-sec);font-size:.85rem'>{mnames}</span>", unsafe_allow_html=True)
            c3.markdown(f"<span style='color:var(--accent);font-weight:600'>{cnt:,} شخص</span>", unsafe_allow_html=True)
            with c4:
                if has_permission('delete'):
                    if st.button("🗑", key=f"delnb_{region}_{nb['id']}", help="حذف"):
                        db.delete_neighborhood(nb['id'])
                        st.rerun()
            st.markdown("<hr style='margin:3px 0;border-color:#edf0f3'>", unsafe_allow_html=True)

        if has_permission('settings'):
            st.markdown("---")
            with st.expander("🔧 تصحيح أسماء المناطق الخاطئة"):
                bad = db.get_distribution("القضاء", 20)
                for item in bad:
                    raw = item["القضاء"]
                    norm = db.normalize_region(raw)
                    color = "var(--success)" if norm in db.MAIN_REGIONS else "var(--danger)"
                    sym = "✅" if norm == raw else ("🔄" if norm in db.MAIN_REGIONS else "❓")
                    st.markdown(
                        f"<div style='padding:3px 0'>{sym} <b>{raw}</b> → "
                        f"<span style='color:{color}'>{norm}</span> ({item['عدد']:,})</div>",
                        unsafe_allow_html=True,
                    )
                if st.button("🔄 تطبيع جميع المناطق", type="primary", key=f"norm_btn_{region}"):
                    n = db.normalize_all_regions()
                    st.success(f"✅ تم تحديث {n:,} سجل")
                    st.session_state["regions_normalized"] = False
                    st.rerun()

    with tab_g: region_tab("علي الغربي")
    with tab_sh: region_tab("علي الشرقي")


# ─────────────────────────────────────────────────
# 7. الإعداد
# ─────────────────────────────────────────────────

def page_setup():
    import pandas as pd

    st.markdown("# ⚙️ الإعداد والصيانة")

    tab_users, tab_backup, tab_excel, tab_maint = st.tabs(
        ["👥 المستخدمون", "💾 النسخ الاحتياطي", "📊 استيراد البيانات", "🔧 الصيانة"]
    )

    # ─── تبويب المستخدمين ───
    with tab_users:
        st.markdown("### تغيير كلمة المرور")
        with st.form("change_pw"):
            old_pw = st.text_input("كلمة المرور الحالية", type="password", key="old_pw")
            new_pw = st.text_input("كلمة المرور الجديدة", type="password", key="new_pw")
            confirm_pw = st.text_input("تأكيد كلمة المرور الجديدة", type="password", key="confirm_pw")
            if st.form_submit_button("💾 تغيير كلمة المرور", type="primary"):
                if not old_pw or not new_pw:
                    st.error("أدخل كلمة المرور الحالية والجديدة")
                elif new_pw != confirm_pw:
                    st.error("كلمة المرور الجديدة غير متطابقة")
                elif not db.authenticate(USER['username'], old_pw):
                    st.error("كلمة المرور الحالية غير صحيحة")
                else:
                    db.update_password(USER['id'], new_pw)
                    st.success("✅ تم تغيير كلمة المرور بنجاح")

        if has_permission('users'):
            st.markdown("---")
            st.markdown("### إدارة المستخدمين")

            users = db.get_users()
            for u in users:
                role_lbl = db.ROLES.get(u['role'], u['role'])
                c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                c1.markdown(f"<b>{u['display_name']}</b> <span style='color:var(--text-sec);font-size:.82rem'>({u['username']})</span>",
                            unsafe_allow_html=True)
                c2.markdown(f"<span style='font-size:.85rem'>{role_lbl}</span>", unsafe_allow_html=True)
                c3.markdown(f"<span style='font-size:.8rem;color:var(--text-sec)'>{u['created_at']}</span>", unsafe_allow_html=True)
                with c4:
                    if u['username'] != 'admin':
                        if st.button("🗑", key=f"del_user_{u['id']}", help="حذف المستخدم"):
                            db.delete_user(u['id'])
                            st.rerun()
                st.markdown("<hr style='margin:2px 0;border-color:#edf0f3'>", unsafe_allow_html=True)

            st.markdown("### إضافة مستخدم جديد")
            with st.form("add_user_form"):
                c1, c2 = st.columns(2)
                with c1:
                    new_username = st.text_input("اسم المستخدم *", key="new_uname")
                    new_display = st.text_input("الاسم الظاهر *", key="new_dname")
                with c2:
                    new_upw = st.text_input("كلمة المرور *", type="password", key="new_upw")
                    new_role = st.selectbox("الصلاحية", list(db.ROLES.keys()),
                                            format_func=lambda x: db.ROLES[x], key="new_urole")
                if st.form_submit_button("➕ إضافة مستخدم", type="primary"):
                    if not new_username.strip() or not new_upw.strip() or not new_display.strip():
                        st.error("جميع الحقول مطلوبة")
                    else:
                        uid = db.add_user(new_username, new_upw, new_display, new_role)
                        if uid:
                            st.success(f"✅ تمت إضافة المستخدم: {new_display}")
                            st.rerun()
                        else:
                            st.error("اسم المستخدم موجود مسبقاً")

    # ─── تبويب النسخ الاحتياطي ───
    with tab_backup:
        st.markdown(
            "<div class='gov-card'>"
            "<div class='gov-card-title'>💾 النسخ الاحتياطي التلقائي</div>"
            "<div class='gov-card-sub'>يتم إنشاء نسخة احتياطية تلقائياً مرة واحدة يومياً عند فتح النظام. "
            "يتم حذف النسخ الأقدم من 30 يوماً تلقائياً.</div></div>",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📸 إنشاء نسخة احتياطية الآن", type="primary", use_container_width=True):
                bp = db.create_backup()
                if bp:
                    st.success(f"✅ تم إنشاء نسخة: {bp.name}")
                    st.rerun()
                else:
                    st.error("لا توجد قاعدة بيانات للنسخ")
        with c2:
            if st.button("🗑 حذف النسخ الأقدم من 30 يوم", use_container_width=True):
                n = db.cleanup_old_backups(30)
                st.success(f"✅ تم حذف {n} نسخة قديمة")
                st.rerun()

        st.markdown("---")
        backups = db.get_backups()
        if not backups:
            st.info("لا توجد نسخ احتياطية بعد.")
        else:
            st.markdown(f"**النسخ الاحتياطية المتوفرة ({len(backups)}):**")
            for i, bk in enumerate(backups):
                ca, cb, cc, cd = st.columns([3, 2, 1, 1])
                ca.markdown(f"**{bk['name']}**")
                cb.markdown(f"📅 {bk['date']}")
                cc.markdown(f"📦 {bk['size_mb']:.1f} MB")
                with cd:
                    col_r, col_d = st.columns(2)
                    with col_r:
                        if st.button("↩️", key=f"restore_{i}", help="استعادة"):
                            st.session_state[f"confirm_restore_{i}"] = True
                            st.rerun()
                    with col_d:
                        if st.button("🗑", key=f"delbk_{i}", help="حذف"):
                            db.delete_backup(bk['path'])
                            st.rerun()

                if st.session_state.get(f"confirm_restore_{i}"):
                    st.warning(f"⚠️ هل تريد استعادة **{bk['name']}**؟ سيتم استبدال البيانات الحالية!")
                    cr1, cr2 = st.columns(2)
                    with cr1:
                        if st.button("✅ نعم، استعادة", key=f"yes_restore_{i}", type="primary"):
                            db.create_backup()
                            db.restore_backup(bk['path'])
                            st.session_state[f"confirm_restore_{i}"] = False
                            st.success("✅ تم الاستعادة بنجاح")
                            st.rerun()
                    with cr2:
                        if st.button("❌ إلغاء", key=f"no_restore_{i}"):
                            st.session_state[f"confirm_restore_{i}"] = False
                            st.rerun()
                st.markdown("<hr style='margin:3px 0;border-color:#edf0f3'>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**📤 تصدير قاعدة البيانات:**")
        db_path = db.DB_PATH
        if db_path.exists():
            with open(str(db_path), 'rb') as f:
                st.download_button("⬇️ تحميل قاعدة البيانات", data=f.read(),
                                   file_name="ali_gharbi.db", mime="application/octet-stream", key="dl_db")

    # ─── تبويب الاستيراد ───
    with tab_excel:
        default_excel = db.get_excel_path()
        st.info(f"📁 **مكان ملف Excel:** `{default_excel}`\n\n"
                f"ضع ملفك باسم **`{db.EXCEL_FILE_NAME}`** في نفس المجلد.")

        excel_exists = default_excel.exists()
        if excel_exists:
            st.success(f"✅ الملف موجود — {default_excel.stat().st_size // 1024:,} KB")
        else:
            st.warning("⚠️ الملف غير موجود في المسار المتوقع")

        uploaded = st.file_uploader("أو ارفع ملف Excel مختلف", type=["xlsx", "xls"], key="excel_upload")
        clear_opt = st.checkbox("🗑 مسح البيانات الحالية قبل الاستيراد", value=True)

        if st.button("🚀 استيراد من Excel", type="primary", disabled=(not excel_exists and not uploaded)):
            import tempfile, os
            if uploaded:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(uploaded.read())
                    src_path = tmp.name
            else:
                src_path = str(default_excel)
            with st.spinner("جارٍ القراءة والاستيراد..."):
                count, err = db.import_from_excel_file(src_path, clear_first=clear_opt)
            if uploaded:
                try: os.unlink(src_path)
                except: pass
            if err:
                st.error(f"خطأ: {err}")
            else:
                st.success(f"✅ تم استيراد **{count:,}** سجل")
                st.session_state["regions_normalized"] = False
                st.rerun()

        st.markdown("---")
        st.caption("استخدم هذا فقط إذا لم يكن لديك ملف Excel محدّث")
        if st.button("🚀 استيراد من DB القديمة", type="secondary"):
            with st.spinner("جارٍ الاستيراد..."):
                count, err = db.import_from_old_db()
            if err:
                st.error(f"خطأ: {err}")
            else:
                db.normalize_all_regions()
                st.success(f"✅ تم استيراد {count:,} سجل")
                st.rerun()

    # ─── تبويب الصيانة ───
    with tab_maint:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 تطبيع أسماء المناطق", use_container_width=True):
                n = db.normalize_all_regions()
                st.success(f"✅ تم تحديث {n:,} سجل")
        with c2:
            with st.expander("🗑 مسح كل السجلات"):
                confirm = st.text_input("اكتب **نعم** للتأكيد:", key="clear_confirm")
                if st.button("تنفيذ المسح", type="secondary"):
                    if confirm.strip() == "نعم":
                        db.clear_all_persons()
                        st.success("تم المسح.")
                        st.rerun()
                    else:
                        st.error("اكتب 'نعم' بالضبط")

        st.divider()
        st.json(db.get_stats())
        data_dir = Path(__file__).parent / "data"
        files = sorted(data_dir.glob("*.db")) if data_dir.exists() else []
        if files:
            rows_f = [{"الملف": f.name, "MB": f"{f.stat().st_size / 1024 / 1024:.2f}"} for f in files]
            st.dataframe(pd.DataFrame(rows_f), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────
# التوجيه الرئيسي
# ─────────────────────────────────────────────────
page = st.session_state["current_page"]

if   page == "📋 قائمة الأشخاص":   page_list()
elif page == "✏️ تفاصيل / تعديل":  page_details()
elif page == "➕ إضافة شخص":        page_add()
elif page == "📊 إحصائيات":         page_stats()
elif page == "👑 المختارون":        page_mukhtars()
elif page == "🗺 المناطق والأحياء": page_regions()
elif page == "⚙️ الإعداد":          page_setup()
