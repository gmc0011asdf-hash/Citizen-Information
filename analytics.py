# analytics.py — استعلامات الإحصائيات والرسوم البيانية

import pandas as pd
from crud import _conn


def records_by_file() -> pd.DataFrame:
    """عدد السجلات النشطة حسب الملف"""
    with _conn() as conn:
        return pd.read_sql(
            """SELECT source_file AS الملف, COUNT(*) AS عدد_السجلات
               FROM records WHERE is_deleted=0
               GROUP BY source_file
               ORDER BY عدد_السجلات DESC""",
            conn,
        )


def records_by_sheet(source_file: str = '') -> pd.DataFrame:
    """عدد السجلات حسب الشيت، مع خيار فلترة بالملف"""
    with _conn() as conn:
        if source_file:
            return pd.read_sql(
                """SELECT source_sheet AS الشيت, COUNT(*) AS عدد_السجلات
                   FROM records WHERE is_deleted=0 AND source_file=?
                   GROUP BY source_sheet ORDER BY عدد_السجلات DESC""",
                conn, params=[source_file],
            )
        return pd.read_sql(
            """SELECT source_sheet AS الشيت, COUNT(*) AS عدد_السجلات
               FROM records WHERE is_deleted=0
               GROUP BY source_sheet ORDER BY عدد_السجلات DESC""",
            conn,
        )


def name_vs_no_name() -> pd.DataFrame:
    """مقارنة السجلات التي لديها أسماء مقابل التي بدون أسماء"""
    with _conn() as conn:
        return pd.read_sql(
            """SELECT
               CASE WHEN original_name IS NOT NULL AND original_name != ''
                    THEN 'لديه اسم' ELSE 'بدون اسم' END AS الفئة,
               COUNT(*) AS عدد_السجلات
               FROM records WHERE is_deleted=0
               GROUP BY الفئة""",
            conn,
        )


def active_vs_deleted() -> pd.DataFrame:
    """نشط مقابل محذوف"""
    with _conn() as conn:
        return pd.read_sql(
            """SELECT
               CASE WHEN is_deleted=0 THEN 'نشط' ELSE 'محذوف' END AS الحالة,
               COUNT(*) AS عدد_السجلات
               FROM records GROUP BY is_deleted""",
            conn,
        )


def top_sheets(n: int = 20) -> pd.DataFrame:
    """أكبر N شيت حسب عدد السجلات"""
    with _conn() as conn:
        return pd.read_sql(
            f"""SELECT source_file AS الملف, source_sheet AS الشيت,
                COUNT(*) AS عدد_السجلات
                FROM records WHERE is_deleted=0
                GROUP BY source_file, source_sheet
                ORDER BY عدد_السجلات DESC
                LIMIT {int(n)}""",
            conn,
        )


def records_by_batch() -> pd.DataFrame:
    """توزيع السجلات على دفعات الاستيراد"""
    with _conn() as conn:
        return pd.read_sql(
            """SELECT b.id AS رقم_الدفعة, b.source_file AS الملف,
               b.imported_at AS وقت_الاستيراد,
               COUNT(r.id) AS عدد_السجلات
               FROM import_batches b
               LEFT JOIN records r ON r.batch_id=b.id AND r.is_deleted=0
               GROUP BY b.id ORDER BY b.imported_at DESC""",
            conn,
        )


def monthly_imports() -> pd.DataFrame:
    """الاستيرادات حسب الشهر"""
    with _conn() as conn:
        return pd.read_sql(
            """SELECT substr(imported_at, 1, 7) AS الشهر,
               COUNT(*) AS عدد_الدفعات,
               SUM(rows_count) AS إجمالي_السجلات
               FROM import_batches
               GROUP BY الشهر ORDER BY الشهر""",
            conn,
        )
