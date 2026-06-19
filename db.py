# db.py — طبقة قاعدة البيانات SQLite
# مسؤول عن: إنشاء الجداول، CRUD كامل، Soft Delete، Indexes

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

# مسار قاعدة البيانات داخل المشروع
DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "excel_filter.db"


class Database:
    """
    مدير قاعدة البيانات SQLite.
    يُنشئ قاعدة البيانات والجداول تلقائيًا عند أول استخدام.
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ─────────────────────────────────────────────
    # تهيئة قاعدة البيانات
    # ─────────────────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        """إنشاء اتصال جديد بقاعدة البيانات مع دعم UTF-8"""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA encoding='UTF-8'")
        return conn

    def _init_db(self):
        """إنشاء الجداول والفهارس إذا لم تكن موجودة"""
        with self._get_connection() as conn:
            conn.executescript("""
                -- جدول دفعات الاستيراد
                CREATE TABLE IF NOT EXISTS import_batches (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT    NOT NULL,
                    imported_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                    sheets_count INTEGER DEFAULT 0,
                    rows_count  INTEGER DEFAULT 0,
                    status      TEXT    DEFAULT 'completed',
                    notes       TEXT
                );

                -- الجدول الرئيسي للسجلات
                CREATE TABLE IF NOT EXISTS records (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id      INTEGER REFERENCES import_batches(id),
                    source_file   TEXT NOT NULL,
                    source_sheet  TEXT NOT NULL,
                    original_row  INTEGER,
                    original_name TEXT,
                    clean_name    TEXT,
                    row_json      TEXT NOT NULL,
                    created_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    updated_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    is_deleted    INTEGER NOT NULL DEFAULT 0
                );

                -- جدول نتائج المطابقة
                CREATE TABLE IF NOT EXISTS match_results (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_record_id    INTEGER,
                    database_record_id INTEGER REFERENCES records(id),
                    match_type         TEXT,
                    similarity_score   REAL,
                    result             TEXT,
                    created_at         TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                -- الفهارس لتسريع البحث
                CREATE INDEX IF NOT EXISTS idx_records_clean_name
                    ON records(clean_name) WHERE is_deleted = 0;

                CREATE INDEX IF NOT EXISTS idx_records_source_sheet
                    ON records(source_sheet) WHERE is_deleted = 0;

                CREATE INDEX IF NOT EXISTS idx_records_source_file
                    ON records(source_file) WHERE is_deleted = 0;

                CREATE INDEX IF NOT EXISTS idx_records_batch_id
                    ON records(batch_id);

                CREATE INDEX IF NOT EXISTS idx_records_is_deleted
                    ON records(is_deleted);
            """)

    # ─────────────────────────────────────────────
    # import_batches — إدارة دفعات الاستيراد
    # ─────────────────────────────────────────────

    def create_batch(self, source_file: str, sheets_count: int = 0,
                     rows_count: int = 0, notes: str = '') -> int:
        """إنشاء دفعة استيراد جديدة وإرجاع معرّفها"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO import_batches
                   (source_file, sheets_count, rows_count, notes)
                   VALUES (?, ?, ?, ?)""",
                (source_file, sheets_count, rows_count, notes)
            )
            return cursor.lastrowid

    def update_batch(self, batch_id: int, rows_count: int,
                     sheets_count: int, status: str = 'completed'):
        """تحديث معلومات الدفعة بعد اكتمال الاستيراد"""
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE import_batches
                   SET rows_count=?, sheets_count=?, status=?
                   WHERE id=?""",
                (rows_count, sheets_count, status, batch_id)
            )

    def get_batches(self) -> list[dict]:
        """استرجاع كل دفعات الاستيراد"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM import_batches ORDER BY imported_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def find_batch_by_file(self, source_file: str) -> dict | None:
        """البحث عن دفعة سابقة لنفس الملف"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM import_batches WHERE source_file=? ORDER BY imported_at DESC LIMIT 1",
                (source_file,)
            ).fetchone()
            return dict(row) if row else None

    # ─────────────────────────────────────────────
    # records — العمليات الأساسية
    # ─────────────────────────────────────────────

    def insert_record(self, batch_id: int, source_file: str,
                      source_sheet: str, original_row: int,
                      original_name: str, clean_name: str,
                      row_data: dict) -> int:
        """إدراج سجل جديد"""
        row_json = json.dumps(row_data, ensure_ascii=False)
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO records
                   (batch_id, source_file, source_sheet, original_row,
                    original_name, clean_name, row_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (batch_id, source_file, source_sheet, original_row,
                 original_name, clean_name, row_json)
            )
            return cursor.lastrowid

    def insert_records_bulk(self, records: list[dict]) -> int:
        """إدراج مجموعة كبيرة من السجلات دفعة واحدة — أسرع للاستيراد"""
        if not records:
            return 0

        rows = [
            (
                r['batch_id'], r['source_file'], r['source_sheet'],
                r['original_row'], r['original_name'], r['clean_name'],
                json.dumps(r['row_data'], ensure_ascii=False)
            )
            for r in records
        ]

        with self._get_connection() as conn:
            conn.executemany(
                """INSERT INTO records
                   (batch_id, source_file, source_sheet, original_row,
                    original_name, clean_name, row_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                rows
            )
            return len(rows)

    def get_record(self, record_id: int) -> dict | None:
        """استرجاع سجل واحد بمعرّفه"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM records WHERE id=?", (record_id,)
            ).fetchone()
            if not row:
                return None
            result = dict(row)
            result['row_data'] = json.loads(result['row_json'])
            return result

    def update_record(self, record_id: int, new_data: dict) -> bool:
        """
        تحديث سجل موجود.
        new_data يمكن أن يحتوي على:
          - original_name, clean_name, row_data (dict)
        """
        row_json = json.dumps(new_data.get('row_data', {}), ensure_ascii=False) \
            if 'row_data' in new_data else None

        with self._get_connection() as conn:
            if row_json is not None:
                conn.execute(
                    """UPDATE records
                       SET original_name=?, clean_name=?, row_json=?,
                           updated_at=datetime('now','localtime')
                       WHERE id=?""",
                    (
                        new_data.get('original_name'),
                        new_data.get('clean_name'),
                        row_json,
                        record_id
                    )
                )
            else:
                conn.execute(
                    """UPDATE records
                       SET original_name=?, clean_name=?,
                           updated_at=datetime('now','localtime')
                       WHERE id=?""",
                    (
                        new_data.get('original_name'),
                        new_data.get('clean_name'),
                        record_id
                    )
                )
            return conn.total_changes > 0

    def soft_delete_record(self, record_id: int) -> bool:
        """حذف منطقي للسجل (لا يُحذف من قاعدة البيانات)"""
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE records
                   SET is_deleted=1, updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (record_id,)
            )
            return conn.total_changes > 0

    def restore_record(self, record_id: int) -> bool:
        """استعادة سجل محذوف منطقيًا"""
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE records
                   SET is_deleted=0, updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (record_id,)
            )
            return conn.total_changes > 0

    def soft_delete_batch(self, batch_id: int) -> int:
        """حذف منطقي لكل سجلات دفعة معيّنة"""
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE records
                   SET is_deleted=1, updated_at=datetime('now','localtime')
                   WHERE batch_id=?""",
                (batch_id,)
            )
            return conn.total_changes

    def list_records(self, source_file: str = None, source_sheet: str = None,
                     include_deleted: bool = False, limit: int = 1000,
                     offset: int = 0) -> list[dict]:
        """
        سرد السجلات مع فلاتر اختيارية.
        """
        conditions = []
        params = []

        if not include_deleted:
            conditions.append("is_deleted = 0")

        if source_file:
            conditions.append("source_file = ?")
            params.append(source_file)

        if source_sheet:
            conditions.append("source_sheet = ?")
            params.append(source_sheet)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params += [limit, offset]

        with self._get_connection() as conn:
            rows = conn.execute(
                f"""SELECT * FROM records {where}
                    ORDER BY source_file, source_sheet, original_row
                    LIMIT ? OFFSET ?""",
                params
            ).fetchall()

            result = []
            for row in rows:
                r = dict(row)
                try:
                    r['row_data'] = json.loads(r['row_json'])
                except Exception:
                    r['row_data'] = {}
                result.append(r)
            return result

    def count_records(self, source_file: str = None,
                      include_deleted: bool = False) -> int:
        """عدد السجلات"""
        conditions = []
        params = []

        if not include_deleted:
            conditions.append("is_deleted = 0")

        if source_file:
            conditions.append("source_file = ?")
            params.append(source_file)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._get_connection() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM records {where}", params
            ).fetchone()
            return row['cnt']

    def get_stats(self) -> dict:
        """إحصائيات عامة عن قاعدة البيانات"""
        with self._get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) as c FROM records WHERE is_deleted=0"
            ).fetchone()['c']

            deleted = conn.execute(
                "SELECT COUNT(*) as c FROM records WHERE is_deleted=1"
            ).fetchone()['c']

            with_name = conn.execute(
                "SELECT COUNT(*) as c FROM records WHERE is_deleted=0 AND original_name IS NOT NULL AND original_name != ''"
            ).fetchone()['c']

            batches = conn.execute(
                "SELECT COUNT(*) as c FROM import_batches"
            ).fetchone()['c']

            files = conn.execute(
                "SELECT COUNT(DISTINCT source_file) as c FROM records WHERE is_deleted=0"
            ).fetchone()['c']

            sheets = conn.execute(
                "SELECT COUNT(DISTINCT source_sheet) as c FROM records WHERE is_deleted=0"
            ).fetchone()['c']

        return {
            'total_records': total,
            'deleted_records': deleted,
            'records_with_name': with_name,
            'import_batches': batches,
            'unique_files': files,
            'unique_sheets': sheets,
            'db_path': str(self.db_path),
        }

    # ─────────────────────────────────────────────
    # match_results — نتائج المطابقة
    # ─────────────────────────────────────────────

    def save_match_result(self, check_record_id: int | None,
                          database_record_id: int | None,
                          match_type: str, similarity_score: float,
                          result: str) -> int:
        """حفظ نتيجة مطابقة"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO match_results
                   (check_record_id, database_record_id, match_type,
                    similarity_score, result)
                   VALUES (?, ?, ?, ?, ?)""",
                (check_record_id, database_record_id,
                 match_type, similarity_score, result)
            )
            return cursor.lastrowid

    def get_match_results(self, limit: int = 500) -> list[dict]:
        """استرجاع نتائج المطابقة"""
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM match_results
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
