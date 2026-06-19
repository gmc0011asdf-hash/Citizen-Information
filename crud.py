# crud.py — عمليات قاعدة البيانات للواجهة الرسومية
# يستخدم sqlite3 مباشرةً مع LIMIT/OFFSET لضمان الأداء مع 55k+ سجل

import sqlite3
import json
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "data" / "excel_filter.db"

# ── الملف الأساسي — يُستخدم كاختيار افتراضي في كل الصفحات ──
BASE_FILE_NAME = "المعلومات_المدنية.xlsx"


def _conn() -> sqlite3.Connection:
    """فتح اتصال بقاعدة البيانات مع دعم UTF-8 والقراءة المتزامنة"""
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA encoding='UTF-8'")
    conn.execute("PRAGMA cache_size=10000")
    return conn


def db_exists() -> bool:
    return DB_PATH.exists()


def ensure_indexes():
    """إضافة فهارس إضافية لتسريع واجهة المستخدم (لا تُكرَّر)"""
    with _conn() as conn:
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_records_name_search
                ON records(original_name);
            CREATE INDEX IF NOT EXISTS idx_records_original_row
                ON records(original_row);
            CREATE INDEX IF NOT EXISTS idx_records_batch_deleted
                ON records(batch_id, is_deleted);
            CREATE INDEX IF NOT EXISTS idx_records_created
                ON records(created_at);
        """)


# ─────────────────────────────────────────────────
# الإحصائيات العامة
# ─────────────────────────────────────────────────

def get_stats() -> dict:
    """إحصائيات لوحة التحكم"""
    with _conn() as conn:
        total     = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        active    = conn.execute("SELECT COUNT(*) FROM records WHERE is_deleted=0").fetchone()[0]
        deleted   = conn.execute("SELECT COUNT(*) FROM records WHERE is_deleted=1").fetchone()[0]
        with_name = conn.execute(
            "SELECT COUNT(*) FROM records WHERE is_deleted=0 AND original_name IS NOT NULL AND original_name != ''"
        ).fetchone()[0]
        files   = conn.execute("SELECT COUNT(DISTINCT source_file) FROM records WHERE is_deleted=0").fetchone()[0]
        sheets  = conn.execute("SELECT COUNT(DISTINCT source_sheet) FROM records WHERE is_deleted=0").fetchone()[0]
        batches = conn.execute("SELECT COUNT(*) FROM import_batches").fetchone()[0]
        last = conn.execute(
            "SELECT source_file, imported_at FROM import_batches ORDER BY imported_at DESC LIMIT 1"
        ).fetchone()
    return {
        'total':       total,
        'active':      active,
        'deleted':     deleted,
        'with_name':   with_name,
        'files':       files,
        'sheets':      sheets,
        'batches':     batches,
        'last_file':   last['source_file'] if last else '—',
        'last_import': last['imported_at'] if last else '—',
    }


# ─────────────────────────────────────────────────
# بناء شرط WHERE ديناميكي
# ─────────────────────────────────────────────────

def _build_where(
    source_file='', source_sheet='', deleted_filter='active',
    name_search='', clean_name_search='', json_search='',
    row_from=0, row_to=0, batch_id=None,
    unified_search='',
):
    conditions, params = [], []

    if deleted_filter == 'active':
        conditions.append("is_deleted = 0")
    elif deleted_filter == 'deleted':
        conditions.append("is_deleted = 1")

    if source_file:
        conditions.append("source_file = ?")
        params.append(source_file)

    if source_sheet:
        conditions.append("source_sheet = ?")
        params.append(source_sheet)

    if batch_id is not None:
        conditions.append("batch_id = ?")
        params.append(int(batch_id))

    if unified_search:
        # بحث موحد: original_name أو clean_name أو row_json
        conditions.append("(original_name LIKE ? OR clean_name LIKE ? OR row_json LIKE ?)")
        q = f"%{unified_search}%"
        params.extend([q, q, q])
    else:
        if name_search:
            conditions.append("original_name LIKE ?")
            params.append(f"%{name_search}%")

        if clean_name_search:
            conditions.append("clean_name LIKE ?")
            params.append(f"%{clean_name_search}%")

        if json_search:
            conditions.append("row_json LIKE ?")
            params.append(f"%{json_search}%")

    if row_from and row_from > 0:
        conditions.append("original_row >= ?")
        params.append(int(row_from))

    if row_to and row_to > 0:
        conditions.append("original_row <= ?")
        params.append(int(row_to))

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where, params


# ─────────────────────────────────────────────────
# جلب السجلات مع Pagination
# ─────────────────────────────────────────────────

def get_records(
    source_file='', source_sheet='', deleted_filter='active',
    name_search='', clean_name_search='', json_search='',
    row_from=0, row_to=0, batch_id=None,
    limit=50, offset=0,
    unified_search='',
) -> tuple:
    """يُرجع (قائمة السجلات, العدد الكلي)"""
    where, params = _build_where(
        source_file, source_sheet, deleted_filter,
        name_search, clean_name_search, json_search,
        row_from, row_to, batch_id,
        unified_search,
    )
    with _conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM records {where}", params).fetchone()[0]
        rows = conn.execute(
            f"""SELECT id, batch_id, source_file, source_sheet, original_row,
                       original_name, clean_name, row_json,
                       created_at, updated_at, is_deleted
                FROM records {where}
                ORDER BY id
                LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()
    return [dict(r) for r in rows], total


def get_record_by_id(record_id: int) -> Optional[dict]:
    """جلب سجل واحد بمعرّفه مع فك JSON"""
    with _conn() as conn:
        row = conn.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone()
        if not row:
            return None
        r = dict(row)
        try:
            r['row_data'] = json.loads(r.get('row_json') or '{}')
        except Exception:
            r['row_data'] = {}
        return r


# ─────────────────────────────────────────────────
# عمليات CRUD
# ─────────────────────────────────────────────────

def update_record(record_id: int, original_name: str,
                  clean_name: str, row_json_str: str) -> bool:
    try:
        json.loads(row_json_str)
    except Exception:
        raise ValueError("صيغة JSON غير صحيحة — تحقق من الأقواس والمسافات")

    with _conn() as conn:
        conn.execute(
            """UPDATE records SET original_name=?, clean_name=?, row_json=?,
               updated_at=datetime('now','localtime') WHERE id=?""",
            (original_name.strip(), clean_name.strip(), row_json_str, record_id),
        )
        return conn.total_changes > 0


def soft_delete(record_id: int) -> bool:
    """حذف منطقي فقط — is_deleted=1"""
    with _conn() as conn:
        conn.execute(
            "UPDATE records SET is_deleted=1, updated_at=datetime('now','localtime') WHERE id=?",
            (record_id,),
        )
        return conn.total_changes > 0


def restore(record_id: int) -> bool:
    """استعادة سجل محذوف — is_deleted=0"""
    with _conn() as conn:
        conn.execute(
            "UPDATE records SET is_deleted=0, updated_at=datetime('now','localtime') WHERE id=?",
            (record_id,),
        )
        return conn.total_changes > 0


def add_record(source_file: str, source_sheet: str, original_row: int,
               original_name: str, clean_name: str,
               row_json_str: str, batch_id=None) -> int:
    try:
        json.loads(row_json_str)
    except Exception:
        raise ValueError("صيغة JSON غير صحيحة")

    with _conn() as conn:
        cursor = conn.execute(
            """INSERT INTO records
               (batch_id, source_file, source_sheet, original_row,
                original_name, clean_name, row_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (batch_id, source_file.strip(), source_sheet.strip(),
             int(original_row), original_name.strip(),
             clean_name.strip(), row_json_str),
        )
        return cursor.lastrowid


# ─────────────────────────────────────────────────
# قوائم منسدلة
# ─────────────────────────────────────────────────

def get_distinct_files() -> list:
    with _conn() as conn:
        return [r[0] for r in conn.execute(
            "SELECT DISTINCT source_file FROM records ORDER BY source_file"
        ).fetchall()]


def get_distinct_sheets(source_file='') -> list:
    with _conn() as conn:
        if source_file:
            return [r[0] for r in conn.execute(
                "SELECT DISTINCT source_sheet FROM records WHERE source_file=? ORDER BY source_sheet",
                (source_file,),
            ).fetchall()]
        return [r[0] for r in conn.execute(
            "SELECT DISTINCT source_sheet FROM records ORDER BY source_sheet"
        ).fetchall()]


# ─────────────────────────────────────────────────
# الدفعات
# ─────────────────────────────────────────────────

def get_batches() -> list:
    with _conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM import_batches ORDER BY imported_at DESC"
        ).fetchall()]


def get_batch_detail(batch_id: int) -> dict:
    with _conn() as conn:
        total     = conn.execute("SELECT COUNT(*) FROM records WHERE batch_id=?", (batch_id,)).fetchone()[0]
        active    = conn.execute("SELECT COUNT(*) FROM records WHERE batch_id=? AND is_deleted=0", (batch_id,)).fetchone()[0]
        with_name = conn.execute(
            "SELECT COUNT(*) FROM records WHERE batch_id=? AND original_name IS NOT NULL AND original_name!=''",
            (batch_id,)
        ).fetchone()[0]
        sheets    = conn.execute(
            "SELECT COUNT(DISTINCT source_sheet) FROM records WHERE batch_id=?", (batch_id,)
        ).fetchone()[0]
    return {
        'total':     total,
        'active':    active,
        'deleted':   total - active,
        'with_name': with_name,
        'sheets':    sheets,
    }


# ─────────────────────────────────────────────────
# إحصائيات الملف الواحد
# ─────────────────────────────────────────────────

def get_file_stats(source_file: str) -> dict:
    """إحصائيات شاملة لملف Excel واحد"""
    with _conn() as conn:
        total     = conn.execute("SELECT COUNT(*) FROM records WHERE source_file=?",     (source_file,)).fetchone()[0]
        active    = conn.execute("SELECT COUNT(*) FROM records WHERE source_file=? AND is_deleted=0", (source_file,)).fetchone()[0]
        deleted   = conn.execute("SELECT COUNT(*) FROM records WHERE source_file=? AND is_deleted=1", (source_file,)).fetchone()[0]
        with_name = conn.execute(
            "SELECT COUNT(*) FROM records WHERE source_file=? AND is_deleted=0 AND original_name IS NOT NULL AND original_name!=''",
            (source_file,)
        ).fetchone()[0]
        sheets    = conn.execute(
            "SELECT COUNT(DISTINCT source_sheet) FROM records WHERE source_file=?", (source_file,)
        ).fetchone()[0]
        batches   = conn.execute(
            "SELECT COUNT(*) FROM import_batches WHERE source_file=?", (source_file,)
        ).fetchone()[0]
        last_row  = conn.execute(
            "SELECT imported_at FROM import_batches WHERE source_file=? ORDER BY imported_at DESC LIMIT 1",
            (source_file,)
        ).fetchone()
    return {
        'source_file': source_file,
        'total':       total,
        'active':      active,
        'deleted':     deleted,
        'with_name':   with_name,
        'sheets':      sheets,
        'batches':     batches,
        'last_import': last_row[0] if last_row else '—',
    }


def get_files_summary() -> list:
    """ملخص كل ملفات Excel المستوردة مع إحصائياتها"""
    with _conn() as conn:
        rows = conn.execute("""
            SELECT
                r.source_file,
                COUNT(*)                                                                 AS total_records,
                SUM(CASE WHEN r.is_deleted=0 THEN 1 ELSE 0 END)                        AS active_records,
                SUM(CASE WHEN r.is_deleted=1 THEN 1 ELSE 0 END)                        AS deleted_records,
                SUM(CASE WHEN r.is_deleted=0
                          AND r.original_name IS NOT NULL
                          AND r.original_name != '' THEN 1 ELSE 0 END)                  AS records_with_name,
                COUNT(DISTINCT r.source_sheet)                                           AS sheets_count,
                MAX(b.imported_at)                                                       AS last_import,
                COUNT(DISTINCT b.id)                                                     AS batches_count
            FROM records r
            LEFT JOIN import_batches b ON b.source_file = r.source_file
            GROUP BY r.source_file
            ORDER BY total_records DESC
        """).fetchall()
    return [dict(r) for r in rows]


def get_default_file() -> str:
    """يُرجع الملف الأساسي إذا كان موجودًا، وإلا أول ملف متاح"""
    files = get_distinct_files()
    if not files:
        return ''
    if BASE_FILE_NAME in files:
        return BASE_FILE_NAME
    return files[0]


def get_batches_for_file(source_file: str = '') -> list:
    """جلب دفعات الاستيراد مع خيار فلترة حسب الملف"""
    with _conn() as conn:
        if source_file:
            rows = conn.execute(
                "SELECT * FROM import_batches WHERE source_file=? ORDER BY imported_at DESC",
                (source_file,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM import_batches ORDER BY imported_at DESC"
            ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────
# إعادة بناء أسماء من row_json
# ─────────────────────────────────────────────────

def rebuild_names_from_row_json(source_file: str = None) -> int:
    """يعيد بناء original_name وclean_name من row_json للسجلات الفارغة الاسم"""
    from cleaner import clean_arabic_name, NAME_COLUMN_PATTERNS

    with _conn() as conn:
        base_q = (
            "SELECT id, row_json FROM records "
            "WHERE (original_name IS NULL OR original_name = '') AND is_deleted = 0"
        )
        params: list = []
        if source_file:
            base_q += " AND source_file = ?"
            params.append(source_file)

        rows = conn.execute(base_q, params).fetchall()
        updated = 0

        for row in rows:
            try:
                data = json.loads(row['row_json'] or '{}')
            except Exception:
                continue

            name_val = None
            for key in data:
                key_str = str(key).strip()
                # مطابقة مباشرة بالأنماط
                matched = any(pat in key_str for pat in NAME_COLUMN_PATTERNS)
                if not matched:
                    matched = 'اسم' in key_str or 'name' in key_str.lower()
                if matched:
                    val = str(data[key]).strip()
                    if val and val.lower() not in ('none', 'nan', ''):
                        name_val = val
                        break

            if name_val:
                clean = clean_arabic_name(name_val)
                conn.execute(
                    "UPDATE records SET original_name=?, clean_name=?, "
                    "updated_at=datetime('now','localtime') WHERE id=?",
                    (name_val, clean, row['id']),
                )
                updated += 1

    return updated


def get_sample_columns(source_file: str) -> list:
    """جلب أسماء أعمدة row_json من أول سجل في الملف المحدد"""
    with _conn() as conn:
        row = conn.execute(
            "SELECT row_json FROM records WHERE source_file=? AND row_json IS NOT NULL AND row_json != '{}' LIMIT 1",
            (source_file,)
        ).fetchone()
    if not row:
        return []
    try:
        return list(json.loads(row['row_json']).keys())
    except Exception:
        return []


def get_records_for_matching(source_file: str) -> list:
    """جلب السجلات من الملف المحدد للمطابقة والمقارنة"""
    with _conn() as conn:
        rows = conn.execute(
            """SELECT source_file AS check_file, source_sheet AS check_sheet,
                      original_row AS check_row, original_name, clean_name
               FROM records
               WHERE source_file = ? AND is_deleted = 0
               AND original_name IS NOT NULL AND original_name != ''""",
            (source_file,)
        ).fetchall()
    return [dict(r) for r in rows]
