# db_ali.py — قاعدة بيانات نظام "المعلومات المدنية للمواطنين"
import sqlite3
import json
import io
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "ali_gharbi.db"

MAIN_REGIONS = ['علي الغربي', 'علي الشرقي']

# تصحيح أخطاء أسماء المناطق الموجودة في البيانات
REGION_NORMALIZE = {
    'علي الغربي':                  'علي الغربي',
    'قضاء علي الغربي':             'علي الغربي',
    'قضاءعلي الغربي':              'علي الغربي',
    'علي الغربيب':                 'علي الغربي',
    'علي الشرقي':                  'علي الشرقي',
    'علي ال شرقي':                 'علي الشرقي',
    'علي الضرقي':                  'علي الشرقي',
    'علي الشقي':                   'علي الشرقي',
    'عتي الشرقي':                  'علي الشرقي',
    'علي الغربي / علي الشرقي':     'علي الغربي',
}

PERSON_FIELDS = ['الاسم', 'التولد', 'المهنة', 'القضاء', 'العنوان', 'المحل', 'الهاتف',
                 'المنطقة', 'الحي', 'mukhtar_id']


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-20000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─────────────────────────────────────────────────
# تهيئة قاعدة البيانات
# ─────────────────────────────────────────────────

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with _conn() as conn:
        # جدول الأشخاص
        conn.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                الاسم       TEXT,
                clean_name  TEXT,
                التولد      TEXT,
                المهنة      TEXT,
                القضاء      TEXT,
                العنوان     TEXT,
                المحل       TEXT,
                الهاتف      TEXT,
                الشيت       TEXT,
                الصف        INTEGER,
                is_deleted  INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                updated_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        # جدول المختارين
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mukhtars (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                الاسم      TEXT NOT NULL,
                الهاتف     TEXT,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        # جدول الأحياء
        conn.execute("""
            CREATE TABLE IF NOT EXISTS neighborhoods (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                الاسم    TEXT NOT NULL,
                المنطقة  TEXT NOT NULL
            )
        """)
        # ربط المختارين بالأحياء (many-to-many)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mukhtar_neighborhoods (
                mukhtar_id      INTEGER NOT NULL REFERENCES mukhtars(id) ON DELETE CASCADE,
                neighborhood_id INTEGER NOT NULL REFERENCES neighborhoods(id) ON DELETE CASCADE,
                PRIMARY KEY (mukhtar_id, neighborhood_id)
            )
        """)

        # جدول المستخدمين
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT NOT NULL UNIQUE,
                password    TEXT NOT NULL,
                display_name TEXT NOT NULL,
                role        TEXT NOT NULL DEFAULT 'viewer',
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        # إنشاء المستخدم الافتراضي admin إذا لم يكن موجوداً
        exists = conn.execute("SELECT 1 FROM users WHERE username='admin'").fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO users (username, password, display_name, role) VALUES (?, ?, ?, ?)",
                ('admin', _hash_pw('admin'), 'المدير', 'admin'),
            )

        # إضافة أعمدة جديدة لـ persons إذا لم تكن موجودة
        existing = {r[1] for r in conn.execute("PRAGMA table_info(persons)").fetchall()}
        new_cols = [
            ('المنطقة',          'TEXT'),
            ('الحي',             'TEXT'),
            ('mukhtar_id',       'INTEGER'),
            ('الحالة_الزوجية',  'TEXT'),
            ('الصلة',            'TEXT'),
            ('family_id',        'INTEGER'),
        ]
        for col, typ in new_cols:
            if col not in existing:
                conn.execute(f"ALTER TABLE persons ADD COLUMN {col} {typ}")

        # جدول المناطق
        conn.execute("""
            CREATE TABLE IF NOT EXISTS regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        # Seed default regions if empty
        if conn.execute("SELECT COUNT(*) FROM regions").fetchone()[0] == 0:
            for r in MAIN_REGIONS:
                conn.execute("INSERT OR IGNORE INTO regions (name) VALUES (?)", (r,))
            # Also add any unique regions from persons table
            existing = conn.execute("SELECT DISTINCT المنطقة FROM persons WHERE المنطقة IS NOT NULL AND المنطقة!=''").fetchall()
            for row in existing:
                conn.execute("INSERT OR IGNORE INTO regions (name) VALUES (?)", (row[0],))

        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_p_name    ON persons(الاسم);
            CREATE INDEX IF NOT EXISTS idx_p_clean   ON persons(clean_name);
            CREATE INDEX IF NOT EXISTS idx_p_deleted ON persons(is_deleted);
            CREATE INDEX IF NOT EXISTS idx_p_sheet   ON persons(الشيت);
            CREATE INDEX IF NOT EXISTS idx_p_qadha   ON persons(القضاء);
            CREATE INDEX IF NOT EXISTS idx_p_mihna   ON persons(المهنة);
            CREATE INDEX IF NOT EXISTS idx_p_region  ON persons(المنطقة);
            CREATE INDEX IF NOT EXISTS idx_p_hay     ON persons(الحي);
            CREATE INDEX IF NOT EXISTS idx_p_family  ON persons(family_id);
            CREATE INDEX IF NOT EXISTS idx_m_name    ON mukhtars(الاسم);
            CREATE INDEX IF NOT EXISTS idx_n_region  ON neighborhoods(المنطقة);
        """)


def db_exists() -> bool:
    if not DB_PATH.exists():
        return False
    try:
        with _conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM persons").fetchone()[0] > 0
    except Exception:
        return False


# ─────────────────────────────────────────────────
# تطبيع أسماء المناطق
# ─────────────────────────────────────────────────

def normalize_region(raw: str) -> str:
    if not raw:
        return ''
    return REGION_NORMALIZE.get(raw.strip(), raw.strip())


def normalize_all_regions() -> int:
    """يعبّئ عمود المنطقة من القضاء لجميع السجلات"""
    with _conn() as conn:
        rows = conn.execute("SELECT id, القضاء FROM persons WHERE المنطقة IS NULL OR المنطقة=''").fetchall()
        batch = [(normalize_region(r['القضاء']), r['id']) for r in rows]
        conn.executemany("UPDATE persons SET المنطقة=? WHERE id=?", batch)
        return len(batch)


# ─────────────────────────────────────────────────
# إحصائيات
# ─────────────────────────────────────────────────

def get_stats() -> dict:
    with _conn() as conn:
        total     = conn.execute("SELECT COUNT(*) FROM persons").fetchone()[0]
        active    = conn.execute("SELECT COUNT(*) FROM persons WHERE is_deleted=0").fetchone()[0]
        deleted   = total - active
        with_name = conn.execute(
            "SELECT COUNT(*) FROM persons WHERE is_deleted=0 AND الاسم IS NOT NULL AND الاسم!=''"
        ).fetchone()[0]
        mukhtars_c  = conn.execute("SELECT COUNT(*) FROM mukhtars").fetchone()[0]
        neighbor_c  = conn.execute("SELECT COUNT(*) FROM neighborhoods").fetchone()[0]
        mihnas      = conn.execute(
            "SELECT COUNT(DISTINCT المهنة) FROM persons WHERE is_deleted=0 AND المهنة IS NOT NULL AND المهنة!=''"
        ).fetchone()[0]
    return dict(total=total, active=active, deleted=deleted, with_name=with_name,
                mukhtars=mukhtars_c, neighborhoods=neighbor_c, mihnas=mihnas)


def get_distribution(col: str, limit: int = 30) -> list:
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT {col}, COUNT(*) AS عدد FROM persons "
            f"WHERE is_deleted=0 AND {col} IS NOT NULL AND {col}!='' "
            f"GROUP BY {col} ORDER BY عدد DESC LIMIT {int(limit)}"
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────
# جلب البيانات مع pagination وفلاتر
# ─────────────────────────────────────────────────

def _build_where(search='', region='', haya='', mihna='', mukhtar_id=None,
                 deleted_filter='active'):
    conditions, params = [], []
    if deleted_filter == 'active':
        conditions.append("p.is_deleted=0")
    elif deleted_filter == 'deleted':
        conditions.append("p.is_deleted=1")

    if region:
        conditions.append("p.المنطقة=?"); params.append(region)
    if haya:
        conditions.append("p.الحي=?"); params.append(haya)
    if mihna:
        conditions.append("p.المهنة LIKE ?"); params.append(f"%{mihna}%")
    if mukhtar_id:
        conditions.append("p.mukhtar_id=?"); params.append(mukhtar_id)
    if search:
        conditions.append(
            "(p.الاسم LIKE ? OR p.clean_name LIKE ? OR p.الهاتف LIKE ? OR p.العنوان LIKE ? OR p.المحل LIKE ?)"
        )
        q = f"%{search}%"
        params.extend([q, q, q, q, q])

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where, params


def get_persons(search='', region='', haya='', mihna='', mukhtar_id=None,
                deleted_filter='active', limit=50, offset=0, include_family=False) -> tuple:
    where, params = _build_where(search, region, haya, mihna, mukhtar_id, deleted_filter)
    with _conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM persons p {where}", params).fetchone()[0]
        rows = conn.execute(
            f"""SELECT p.id, p.الاسم, p.التولد, p.المهنة, p.القضاء, p.العنوان,
                       p.المحل, p.الهاتف, p.الشيت, p.الصف, p.is_deleted,
                       p.المنطقة, p.الحي, p.mukhtar_id,
                       p.الحالة_الزوجية, p.الصلة, p.family_id,
                       m.الاسم AS mukhtar_name,
                       p.created_at, p.updated_at
                FROM persons p
                LEFT JOIN mukhtars m ON p.mukhtar_id = m.id
                {where} ORDER BY p.id LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()
    result = [dict(r) for r in rows]

    if include_family and search and result:
        matched_ids = {r['id'] for r in result}
        family_ids = {r['family_id'] for r in result if r.get('family_id')}
        if family_ids:
            placeholders = ','.join('?' * len(family_ids))
            with _conn() as conn:
                extra = conn.execute(
                    f"""SELECT p.id, p.الاسم, p.التولد, p.المهنة, p.القضاء, p.العنوان,
                               p.المحل, p.الهاتف, p.الشيت, p.الصف, p.is_deleted,
                               p.المنطقة, p.الحي, p.mukhtar_id,
                               p.الحالة_الزوجية, p.الصلة, p.family_id,
                               m.الاسم AS mukhtar_name,
                               p.created_at, p.updated_at
                        FROM persons p
                        LEFT JOIN mukhtars m ON p.mukhtar_id = m.id
                        WHERE p.family_id IN ({placeholders}) AND p.is_deleted=0
                        AND p.id NOT IN ({','.join('?' * len(matched_ids))})""",
                    list(family_ids) + list(matched_ids),
                ).fetchall()
            for r in extra:
                d = dict(r)
                d['included_as_family'] = True
                result.append(d)
        for r in result:
            if 'included_as_family' not in r:
                r['matched_by_search'] = True

    return result, total


def get_person(pid: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            """SELECT p.*, m.الاسم AS mukhtar_name
               FROM persons p LEFT JOIN mukhtars m ON p.mukhtar_id=m.id
               WHERE p.id=?""",
            (pid,),
        ).fetchone()
    return dict(row) if row else None


def get_distinct_values(col: str) -> list:
    with _conn() as conn:
        return [
            r[0] for r in conn.execute(
                f"SELECT DISTINCT {col} FROM persons "
                f"WHERE is_deleted=0 AND {col} IS NOT NULL AND {col}!='' ORDER BY {col}"
            ).fetchall()
        ]


def get_hayas_for_region(region: str) -> list:
    with _conn() as conn:
        return [
            r[0] for r in conn.execute(
                "SELECT DISTINCT الحي FROM persons "
                "WHERE is_deleted=0 AND المنطقة=? AND الحي IS NOT NULL AND الحي!='' ORDER BY الحي",
                (region,),
            ).fetchall()
        ]


# ─────────────────────────────────────────────────
# فحص التكرار
# ─────────────────────────────────────────────────

def find_duplicate_persons(name: str, exclude_id: int = None) -> list:
    """يبحث عن أسماء مشابهة في قاعدة البيانات"""
    from cleaner import clean_arabic_name
    cn = clean_arabic_name(name)
    if not cn:
        return []
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, الاسم, التولد, المهنة, القضاء, المنطقة, الحي FROM persons "
            "WHERE is_deleted=0 AND clean_name=? AND id!=?",
            (cn, exclude_id or -1),
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────
# إدارة المستخدمين والصلاحيات
# ─────────────────────────────────────────────────

ROLES = {'admin': 'مدير النظام', 'editor': 'مدخل بيانات', 'viewer': 'باحث'}


def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def authenticate(username: str, password: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username.strip(), _hash_pw(password)),
        ).fetchone()
    return dict(row) if row else None


def get_users() -> list:
    with _conn() as conn:
        rows = conn.execute("SELECT id, username, display_name, role, created_at FROM users ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def add_user(username: str, password: str, display_name: str, role: str = 'viewer') -> int | None:
    if role not in ROLES:
        return None
    with _conn() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE username=?", (username.strip(),)).fetchone()
        if exists:
            return None
        cur = conn.execute(
            "INSERT INTO users (username, password, display_name, role) VALUES (?, ?, ?, ?)",
            (username.strip(), _hash_pw(password), display_name.strip(), role),
        )
        return cur.lastrowid


def update_password(user_id: int, new_password: str) -> bool:
    with _conn() as conn:
        conn.execute("UPDATE users SET password=? WHERE id=?", (_hash_pw(new_password), user_id))
        return conn.total_changes > 0


def update_user_role(user_id: int, new_role: str) -> bool:
    if new_role not in ROLES:
        return False
    with _conn() as conn:
        conn.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
        return conn.total_changes > 0


def delete_user(user_id: int) -> bool:
    with _conn() as conn:
        user = conn.execute("SELECT username FROM users WHERE id=?", (user_id,)).fetchone()
        if user and user[0] == 'admin':
            return False
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        return conn.total_changes > 0


def find_duplicate_neighborhood(name: str, region: str) -> dict | None:
    """يبحث عن حي بنفس الاسم في نفس المنطقة"""
    if not name.strip() or not region:
        return None
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, الاسم, المنطقة FROM neighborhoods WHERE الاسم=? AND المنطقة=?",
            (name.strip(), region),
        ).fetchone()
    return dict(row) if row else None


def find_duplicate_mukhtar(name: str, exclude_id: int = None) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM mukhtars WHERE الاسم=? AND id!=?",
            (name.strip(), exclude_id or -1),
        ).fetchone()
    return dict(row) if row else None


# ─────────────────────────────────────────────────
# إدارة المناطق
# ─────────────────────────────────────────────────

def get_regions_from_db() -> list:
    """Get all regions from the regions table"""
    with _conn() as conn:
        rows = conn.execute("SELECT id, name, created_at FROM regions ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def add_region(name: str) -> int | None:
    if not name.strip():
        return None
    with _conn() as conn:
        existing = conn.execute("SELECT id FROM regions WHERE name=?", (name.strip(),)).fetchone()
        if existing:
            return None
        cur = conn.execute("INSERT INTO regions (name) VALUES (?)", (name.strip(),))
        return cur.lastrowid


def delete_region(region_id: int) -> bool:
    with _conn() as conn:
        region = conn.execute("SELECT name FROM regions WHERE id=?", (region_id,)).fetchone()
        if not region:
            return False
        name = region[0]
        # Don't delete if persons or neighborhoods use it
        persons_count = conn.execute("SELECT COUNT(*) FROM persons WHERE المنطقة=?", (name,)).fetchone()[0]
        nb_count = conn.execute("SELECT COUNT(*) FROM neighborhoods WHERE المنطقة=?", (name,)).fetchone()[0]
        if persons_count > 0 or nb_count > 0:
            return False
        conn.execute("DELETE FROM regions WHERE id=?", (region_id,))
        return True


# ─────────────────────────────────────────────────
# CRUD الأشخاص
# ─────────────────────────────────────────────────

def _cn(v: str) -> str:
    from cleaner import clean_arabic_name
    return clean_arabic_name(v) if v else ''


MARITAL_STATUS   = ['', 'أعزب', 'متزوج', 'مطلق', 'أرمل', 'مخطوب']
FAMILY_RELATIONS = ['رب الأسرة', 'زوجة', 'ابن', 'ابنة', 'أب', 'أم', 'أخ', 'أخت', 'أخرى']


def update_person(pid: int, الاسم='', التولد='', المهنة='', القضاء='',
                  العنوان='', المحل='', الهاتف='',
                  المنطقة='', الحي='', mukhtar_id=None,
                  الحالة_الزوجية='', الصلة='') -> bool:
    mn = normalize_region(المنطقة) if المنطقة else (normalize_region(القضاء) if القضاء else '')
    with _conn() as conn:
        conn.execute(
            """UPDATE persons
               SET الاسم=?, clean_name=?, التولد=?, المهنة=?, القضاء=?,
                   العنوان=?, المحل=?, الهاتف=?, المنطقة=?, الحي=?, mukhtar_id=?,
                   الحالة_الزوجية=?, الصلة=?,
                   updated_at=datetime('now','localtime')
               WHERE id=?""",
            (الاسم.strip(), _cn(الاسم), التولد.strip(), المهنة.strip(), القضاء.strip(),
             العنوان.strip(), المحل.strip(), الهاتف.strip(),
             mn, الحي.strip() if الحي else '', mukhtar_id,
             الحالة_الزوجية, الصلة, pid),
        )
        return conn.total_changes > 0


def add_person(الاسم='', التولد='', المهنة='', القضاء='', العنوان='',
               المحل='', الهاتف='', الشيت='يدوي', الصف=0,
               المنطقة='', الحي='', mukhtar_id=None,
               الحالة_الزوجية='', الصلة='', family_id=None) -> int:
    mn = normalize_region(المنطقة) if المنطقة else (normalize_region(القضاء) if القضاء else '')
    with _conn() as conn:
        cur = conn.execute(
            """INSERT INTO persons
               (الاسم, clean_name, التولد, المهنة, القضاء, العنوان, المحل, الهاتف,
                الشيت, الصف, المنطقة, الحي, mukhtar_id, الحالة_الزوجية, الصلة, family_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (الاسم.strip(), _cn(الاسم), التولد.strip(), المهنة.strip(), القضاء.strip(),
             العنوان.strip(), المحل.strip(), الهاتف.strip(),
             الشيت, الصف, mn, الحي.strip() if الحي else '', mukhtar_id,
             الحالة_الزوجية, الصلة, family_id),
        )
        return cur.lastrowid


def soft_delete(pid: int) -> bool:
    with _conn() as conn:
        conn.execute(
            "UPDATE persons SET is_deleted=1, updated_at=datetime('now','localtime') WHERE id=?",
            (pid,),
        )
        return conn.total_changes > 0


def restore(pid: int) -> bool:
    with _conn() as conn:
        conn.execute(
            "UPDATE persons SET is_deleted=0, updated_at=datetime('now','localtime') WHERE id=?",
            (pid,),
        )
        return conn.total_changes > 0


def hard_delete_person(pid: int) -> bool:
    """Permanently delete a person from the database"""
    with _conn() as conn:
        row = conn.execute("SELECT id, is_deleted, family_id FROM persons WHERE id=?", (pid,)).fetchone()
        if not row:
            return False
        if row['is_deleted'] != 1:
            raise ValueError("يجب نقل السجل إلى المحذوفات أولاً")
        # Unlink from family
        if row['family_id']:
            conn.execute("UPDATE persons SET family_id=NULL, الصلة=NULL WHERE id=?", (pid,))
        # Permanent delete
        conn.execute("DELETE FROM persons WHERE id=?", (pid,))
        return True


def get_person_with_family(pid: int) -> dict | None:
    """Get person with their family members"""
    person = get_person(pid)
    if not person:
        return None
    result = dict(person)
    if person.get('family_id'):
        result['family_members'] = get_family_members(person['family_id'])
    else:
        result['family_members'] = []
    return result


# ─────────────────────────────────────────────────
# CRUD المختارين
# ─────────────────────────────────────────────────

def get_mukhtars() -> list:
    with _conn() as conn:
        rows = conn.execute(
            """SELECT m.id, m.الاسم, m.الهاتف, m.created_at,
                      GROUP_CONCAT(n.الاسم, ' | ') AS الأحياء,
                      GROUP_CONCAT(n.المنطقة, ' | ') AS المناطق
               FROM mukhtars m
               LEFT JOIN mukhtar_neighborhoods mn ON m.id=mn.mukhtar_id
               LEFT JOIN neighborhoods n ON mn.neighborhood_id=n.id
               GROUP BY m.id ORDER BY m.الاسم"""
        ).fetchall()
    return [dict(r) for r in rows]


def get_mukhtar(mid: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM mukhtars WHERE id=?", (mid,)).fetchone()
        if not row:
            return None
        r = dict(row)
        nb = conn.execute(
            """SELECT n.id, n.الاسم, n.المنطقة FROM neighborhoods n
               JOIN mukhtar_neighborhoods mn ON n.id=mn.neighborhood_id
               WHERE mn.mukhtar_id=?""",
            (mid,),
        ).fetchall()
        r['neighborhoods'] = [dict(x) for x in nb]
    return r


def add_mukhtar(الاسم: str, الهاتف: str = '') -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO mukhtars (الاسم, الهاتف) VALUES (?, ?)",
            (الاسم.strip(), الهاتف.strip()),
        )
        return cur.lastrowid


def update_mukhtar(mid: int, الاسم: str, الهاتف: str = '') -> bool:
    with _conn() as conn:
        conn.execute(
            "UPDATE mukhtars SET الاسم=?, الهاتف=? WHERE id=?",
            (الاسم.strip(), الهاتف.strip(), mid),
        )
        return conn.total_changes > 0


def delete_mukhtar(mid: int) -> bool:
    with _conn() as conn:
        conn.execute("DELETE FROM mukhtar_neighborhoods WHERE mukhtar_id=?", (mid,))
        conn.execute("UPDATE persons SET mukhtar_id=NULL WHERE mukhtar_id=?", (mid,))
        conn.execute("DELETE FROM mukhtars WHERE id=?", (mid,))
        return conn.total_changes > 0


def set_mukhtar_neighborhoods(mid: int, nids: list):
    with _conn() as conn:
        conn.execute("DELETE FROM mukhtar_neighborhoods WHERE mukhtar_id=?", (mid,))
        if nids:
            conn.executemany(
                "INSERT OR IGNORE INTO mukhtar_neighborhoods VALUES (?, ?)",
                [(mid, nid) for nid in nids],
            )


def get_mukhtars_for_region(region: str) -> list:
    with _conn() as conn:
        rows = conn.execute(
            """SELECT DISTINCT m.id, m.الاسم, m.الهاتف FROM mukhtars m
               JOIN mukhtar_neighborhoods mn ON m.id=mn.mukhtar_id
               JOIN neighborhoods n ON mn.neighborhood_id=n.id
               WHERE n.المنطقة=? ORDER BY m.الاسم""",
            (region,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_mukhtars_for_neighborhood(nid: int) -> list:
    with _conn() as conn:
        rows = conn.execute(
            """SELECT m.id, m.الاسم, m.الهاتف FROM mukhtars m
               JOIN mukhtar_neighborhoods mn ON m.id=mn.mukhtar_id
               WHERE mn.neighborhood_id=? ORDER BY m.الاسم""",
            (nid,),
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────
# CRUD الأحياء
# ─────────────────────────────────────────────────

def get_neighborhoods(region: str = '') -> list:
    with _conn() as conn:
        if region:
            rows = conn.execute(
                "SELECT * FROM neighborhoods WHERE المنطقة=? ORDER BY الاسم",
                (region,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM neighborhoods ORDER BY المنطقة, الاسم"
            ).fetchall()
    return [dict(r) for r in rows]


def add_neighborhood(الاسم: str, المنطقة: str) -> int | None:
    if not الاسم.strip() or المنطقة not in MAIN_REGIONS:
        return None
    # منع التكرار
    with _conn() as conn:
        ex = conn.execute(
            "SELECT id FROM neighborhoods WHERE الاسم=? AND المنطقة=?",
            (الاسم.strip(), المنطقة),
        ).fetchone()
        if ex:
            return ex[0]
        cur = conn.execute(
            "INSERT INTO neighborhoods (الاسم, المنطقة) VALUES (?, ?)",
            (الاسم.strip(), المنطقة),
        )
        return cur.lastrowid


def delete_neighborhood(nid: int) -> bool:
    with _conn() as conn:
        conn.execute("DELETE FROM mukhtar_neighborhoods WHERE neighborhood_id=?", (nid,))
        conn.execute("DELETE FROM neighborhoods WHERE id=?", (nid,))
        return conn.total_changes > 0


# ─────────────────────────────────────────────────
# تصدير Excel
# ─────────────────────────────────────────────────

EXPORT_COLS = {
    'id':               'رقم',
    'الاسم':            'الاسم الرباعي واللقب',
    'التولد':           'تاريخ الميلاد',
    'المهنة':           'المهنة',
    'الحالة_الزوجية':  'الحالة الزوجية',
    'الصلة':            'الصلة بالأسرة',
    'المنطقة':          'المنطقة',
    'القضاء':           'القضاء (أصلي)',
    'الحي':             'الحي',
    'العنوان':          'عنوان السكن',
    'المحل':            'المحل / الزقاق',
    'الهاتف':           'رقم الهاتف',
    'mukhtar_name':     'المختار',
    'الشيت':            'المجموعة',
    'الصف':             'الصف الأصلي',
}


def _excel_bytes(df, sheet_name='البيانات') -> bytes:
    import pandas as pd
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        ws = writer.sheets[sheet_name]
        for col_cells in ws.columns:
            w = max((len(str(c.value or '')) for c in col_cells), default=10)
            ws.column_dimensions[col_cells[0].column_letter].width = min(w + 4, 50)
    return buf.getvalue()


def export_to_excel(search='', region='', haya='', mihna='', mukhtar_id=None,
                    deleted_filter='active') -> bytes:
    import pandas as pd
    where, params = _build_where(search, region, haya, mihna, mukhtar_id, deleted_filter)
    with _conn() as conn:
        rows = conn.execute(
            f"""SELECT p.id, p.الاسم, p.التولد, p.المهنة, p.الحالة_الزوجية,
                       p.الصلة, p.المنطقة, p.القضاء, p.الحي, p.العنوان,
                       p.المحل, p.الهاتف, m.الاسم AS mukhtar_name, p.الشيت, p.الصف
                FROM persons p
                LEFT JOIN mukhtars m ON p.mukhtar_id=m.id
                {where} ORDER BY p.المنطقة, p.الحي, p.الاسم""",
            params,
        ).fetchall()

    if not rows:
        return _excel_bytes(pd.DataFrame(columns=list(EXPORT_COLS.values())))
    df = pd.DataFrame([dict(r) for r in rows]).rename(columns=EXPORT_COLS)
    df = df[[c for c in EXPORT_COLS.values() if c in df.columns]]
    return _excel_bytes(df)


# ─────────────────────────────────────────────────
# إدارة الأسرة
# ─────────────────────────────────────────────────

def search_families(query: str, limit: int = 20) -> list:
    """Search families by head name or member name"""
    with _conn() as conn:
        # Find family_ids where any member matches
        rows = conn.execute(
            """SELECT DISTINCT family_id FROM persons
               WHERE family_id IS NOT NULL AND is_deleted=0
               AND (الاسم LIKE ? OR clean_name LIKE ?)
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()

        results = []
        for row in rows:
            fid = row[0]
            members = get_family_members(fid)
            head = next((m for m in members if m.get("الصلة") == "رب الأسرة"), members[0] if members else None)
            results.append({
                'family_id': fid,
                'head_name': head['الاسم'] if head else 'غير محدد',
                'members_count': len(members),
                'region': head.get('المنطقة', '') if head else '',
                'hay': head.get('الحي', '') if head else '',
            })
        return results


def create_family(head_pid: int) -> int:
    """ينشئ عائلة جديدة مع هذا الشخص رباً للأسرة، يُرجع family_id"""
    with _conn() as conn:
        max_fam = conn.execute(
            "SELECT COALESCE(MAX(family_id),0) FROM persons"
        ).fetchone()[0]
        new_fid = max_fam + 1
        conn.execute(
            "UPDATE persons SET family_id=?, الصلة='رب الأسرة', "
            "updated_at=datetime('now','localtime') WHERE id=?",
            (new_fid, head_pid),
        )
    return new_fid


def link_to_family(pid: int, family_id: int, الصلة: str = 'أخرى') -> bool:
    with _conn() as conn:
        conn.execute(
            "UPDATE persons SET family_id=?, الصلة=?, "
            "updated_at=datetime('now','localtime') WHERE id=?",
            (family_id, الصلة, pid),
        )
        return conn.total_changes > 0


def unlink_from_family(pid: int) -> bool:
    with _conn() as conn:
        conn.execute(
            "UPDATE persons SET family_id=NULL, الصلة=NULL, "
            "updated_at=datetime('now','localtime') WHERE id=?",
            (pid,),
        )
        return conn.total_changes > 0


def get_family_members(family_id: int) -> list:
    """جميع أفراد عائلة معينة مرتبين حسب الصلة"""
    with _conn() as conn:
        rows = conn.execute(
            """SELECT id, الاسم, التولد, المهنة, الحالة_الزوجية,
                      الصلة, المنطقة, الحي, العنوان, المحل, الهاتف, is_deleted
               FROM persons WHERE family_id=?
               ORDER BY CASE الصلة
                 WHEN 'رب الأسرة' THEN 1 WHEN 'زوجة' THEN 2
                 WHEN 'ابن' THEN 3 WHEN 'ابنة' THEN 4
                 WHEN 'أب' THEN 5 WHEN 'أم' THEN 6
                 ELSE 9 END, id""",
            (family_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def export_family_excel(family_id: int) -> bytes:
    import pandas as pd
    members = get_family_members(family_id)
    if not members:
        return _excel_bytes(pd.DataFrame())
    FAMILY_COLS = {
        'id': 'رقم', 'الاسم': 'الاسم', 'التولد': 'تاريخ الميلاد',
        'المهنة': 'المهنة', 'الحالة_الزوجية': 'الحالة الزوجية',
        'الصلة': 'الصلة بالأسرة', 'المنطقة': 'المنطقة',
        'الحي': 'الحي', 'العنوان': 'عنوان السكن',
        'المحل': 'المحل', 'الهاتف': 'رقم الهاتف',
    }
    df = pd.DataFrame(members).rename(columns=FAMILY_COLS)
    df = df[[c for c in FAMILY_COLS.values() if c in df.columns]]
    return _excel_bytes(df, sheet_name='أفراد الأسرة')


def search_persons_for_family(query: str, exclude_family_id: int = None,
                               limit: int = 20) -> list:
    """يبحث عن أشخاص لإضافتهم لعائلة"""
    with _conn() as conn:
        if exclude_family_id:
            rows = conn.execute(
                """SELECT id, الاسم, التولد, المهنة FROM persons
                   WHERE is_deleted=0
                     AND (family_id IS NULL OR family_id!=?)
                     AND (الاسم LIKE ? OR clean_name LIKE ?)
                   LIMIT ?""",
                (exclude_family_id, f"%{query}%", f"%{query}%", limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, الاسم, التولد, المهنة FROM persons
                   WHERE is_deleted=0
                     AND (الاسم LIKE ? OR clean_name LIKE ?)
                   LIMIT ?""",
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────
# مختارون مجمّعون حسب المنطقة
# ─────────────────────────────────────────────────

def get_mukhtars_grouped_by_region() -> dict:
    """يُرجع {region: [mukhtars]} للعرض في القوائم المجمّعة"""
    all_mkh = get_mukhtars()
    groups: dict = {r: [] for r in MAIN_REGIONS}
    groups['غير مرتبط'] = []
    seen: dict = {}  # mukhtar_id → set of regions it was added to

    for m in all_mkh:
        regions = []
        if m.get('المناطق'):
            regions = list(dict.fromkeys(str(m['المناطق']).split(' | ')))
            regions = [r for r in regions if r in MAIN_REGIONS]

        if not regions:
            if m['id'] not in seen:
                groups['غير مرتبط'].append(m)
                seen[m['id']] = set()
        else:
            for reg in regions:
                groups.setdefault(reg, []).append(m)

    return {k: v for k, v in groups.items() if v}


# ─────────────────────────────────────────────────
# استيراد من قاعدة البيانات القديمة
# ─────────────────────────────────────────────────

def import_from_old_db() -> tuple:
    from cleaner import clean_arabic_name

    OLD_DB = DB_PATH.parent / "excel_filter.db"
    if not OLD_DB.exists():
        return 0, f"الملف excel_filter.db غير موجود"

    init_db()

    old = sqlite3.connect(str(OLD_DB), timeout=30)
    old.row_factory = sqlite3.Row
    rows = old.execute(
        "SELECT original_name, source_sheet, original_row, row_json "
        "FROM records "
        "WHERE source_file LIKE '%علي الغربي%' AND is_deleted=0 "
        "ORDER BY id",
    ).fetchall()
    old.close()

    if not rows:
        return 0, "لا توجد بيانات في القاعدة القديمة"

    def _v(data: dict, key: str) -> str:
        v = data.get(key, '')
        if v is None or str(v).strip().lower() in ('nan', 'none', ''):
            return ''
        return str(v).strip()

    batch = []
    for row in rows:
        try:
            data = json.loads(row['row_json'] or '{}')
        except Exception:
            data = {}

        الاسم   = row['original_name'] or _v(data, 'الاسم_الرباعي_واللقب')
        التولد  = _v(data, 'التولد')
        المهنة  = _v(data, 'المهنة')
        القضاء  = _v(data, 'القضاء')
        العنوان = _v(data, 'عنوان_السكن')
        المحل   = _v(data, 'محله_زقاق_دار_او_اقرب_نقطه_داله')
        الهاتف  = _v(data, 'رقم_الهاتف')
        clean   = clean_arabic_name(الاسم)
        منطقة   = normalize_region(القضاء)

        batch.append((
            الاسم, clean, التولد, المهنة, القضاء, العنوان, المحل, الهاتف,
            row['source_sheet'] or 'ورقة1',
            row['original_row'] or 0,
            منطقة,
        ))

    with _conn() as conn:
        conn.executemany(
            """INSERT INTO persons
               (الاسم, clean_name, التولد, المهنة, القضاء, العنوان, المحل, الهاتف,
                الشيت, الصف, المنطقة)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            batch,
        )

    return len(batch), None


def clear_all_persons():
    with _conn() as conn:
        conn.execute("DELETE FROM persons")


# ─────────────────────────────────────────────────
# استيراد مباشر من ملف Excel محدّث
# ─────────────────────────────────────────────────

# أعمدة Excel المتوقعة → أعمدة DB
EXCEL_COL_MAP = {
    'الاسم الرباعي واللقب':                   'الاسم',
    'الاسم_الرباعي_واللقب':                   'الاسم',
    'التولد':                                  'التولد',
    'المهنة':                                  'المهنة',
    'القضاء':                                  'القضاء',
    'عنوان السكن':                             'العنوان',
    'عنوان_السكن':                             'العنوان',
    'محله-زقاق-دار او اقرب نقطه داله':        'المحل',
    'محله_زقاق_دار_او_اقرب_نقطه_داله':       'المحل',
    'محله زقاق دار او اقرب نقطه داله':        'المحل',
    'رقم الهاتف':                              'الهاتف',
    'رقم_الهاتف':                              'الهاتف',
    'الحي':                                    'الحي',
    'المنطقة':                                 'المنطقة',
}

EXCEL_FILE_NAME = "المعلومات_المدنية.xlsx"


def get_excel_path() -> Path:
    return Path(__file__).parent / EXCEL_FILE_NAME


def import_from_excel_file(filepath=None, clear_first: bool = False) -> tuple:
    """
    يستورد البيانات مباشرة من ملف Excel.
    filepath: مسار الملف، أو None لاستخدام الملف الافتراضي.
    clear_first: إذا True يمسح البيانات الحالية قبل الاستيراد.
    يُرجع (عدد_المستوردة, رسالة_خطأ_أو_None).
    """
    import pandas as pd
    from cleaner import clean_arabic_name

    path = Path(filepath) if filepath else get_excel_path()
    if not path.exists():
        return 0, f"الملف غير موجود: {path}"

    init_db()

    # قراءة كل أوراق العمل
    try:
        xl = pd.ExcelFile(str(path))
        sheets = xl.sheet_names
    except Exception as e:
        return 0, f"خطأ في فتح الملف: {e}"

    def _v(val) -> str:
        if val is None:
            return ''
        s = str(val).strip()
        return '' if s.lower() in ('nan', 'none', '') else s

    if clear_first:
        clear_all_persons()

    total_inserted = 0
    for sheet_name in sheets:
        try:
            df = pd.read_excel(str(path), sheet_name=sheet_name, dtype=str)
        except Exception:
            continue

        # تعيين أعمدة Excel إلى DB
        col_map = {}
        for excel_col in df.columns:
            mapped = EXCEL_COL_MAP.get(excel_col.strip())
            if mapped:
                col_map[excel_col] = mapped

        batch = []
        for row_idx, row in df.iterrows():
            mapped_row = {db_col: _v(row.get(exc_col)) for exc_col, db_col in col_map.items()}

            اسم     = mapped_row.get('الاسم', '')
            تولد    = mapped_row.get('التولد', '')
            مهنة    = mapped_row.get('المهنة', '')
            قضاء    = mapped_row.get('القضاء', '')
            عنوان   = mapped_row.get('العنوان', '')
            محل     = mapped_row.get('المحل', '')
            هاتف    = mapped_row.get('الهاتف', '')
            حي      = mapped_row.get('الحي', '')
            منطقة   = mapped_row.get('المنطقة', '') or normalize_region(قضاء)
            clean   = clean_arabic_name(اسم)

            batch.append((
                اسم, clean, تولد, مهنة, قضاء, عنوان, محل, هاتف,
                sheet_name, int(row_idx) + 2,
                منطقة, حي,
            ))

        with _conn() as conn:
            conn.executemany(
                """INSERT INTO persons
                   (الاسم, clean_name, التولد, المهنة, القضاء, العنوان, المحل, الهاتف,
                    الشيت, الصف, المنطقة, الحي)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                batch,
            )
        total_inserted += len(batch)

    return total_inserted, None


# ─────────────────────────────────────────────────
# النسخ الاحتياطي
# ─────────────────────────────────────────────────

BACKUP_DIR = DB_PATH.parent / "backups"


def create_backup() -> Path | None:
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    if not DB_PATH.exists():
        return None
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"ali_gharbi_backup_{stamp}.db"
    shutil.copy2(str(DB_PATH), str(dest))
    return dest


def get_backups() -> list:
    """قائمة النسخ الاحتياطية مرتبة من الأحدث"""
    if not BACKUP_DIR.exists():
        return []
    files = sorted(BACKUP_DIR.glob("ali_gharbi_backup_*.db"), reverse=True)
    result = []
    for f in files:
        result.append({
            'path': f,
            'name': f.name,
            'size_mb': f.stat().st_size / 1024 / 1024,
            'date': datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return result


def restore_backup(backup_path: str | Path) -> bool:
    """استعادة قاعدة البيانات من نسخة احتياطية"""
    src = Path(backup_path)
    if not src.exists():
        return False
    shutil.copy2(str(src), str(DB_PATH))
    return True


def delete_backup(backup_path: str | Path) -> bool:
    """حذف نسخة احتياطية"""
    src = Path(backup_path)
    if src.exists():
        src.unlink()
        return True
    return False


def auto_backup_if_needed() -> Path | None:
    """نسخ احتياطي تلقائي يومي — يُنشئ نسخة واحدة يومياً فقط"""
    if not DB_PATH.exists():
        return None
    BACKUP_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    today_backups = list(BACKUP_DIR.glob(f"ali_gharbi_backup_{today}_*.db"))
    if today_backups:
        return None
    return create_backup()


def cleanup_old_backups(keep_days: int = 30):
    """حذف النسخ الاحتياطية الأقدم من عدد أيام محدد"""
    if not BACKUP_DIR.exists():
        return 0
    cutoff = datetime.now() - timedelta(days=keep_days)
    deleted = 0
    for f in BACKUP_DIR.glob("ali_gharbi_backup_*.db"):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            f.unlink()
            deleted += 1
    return deleted
