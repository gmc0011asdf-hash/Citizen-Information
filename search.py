# search.py — دوال البحث والفلترة والمطابقة

import json
from rapidfuzz import fuzz, process as fuzz_process
from db import Database
from cleaner import clean_arabic_name

# ─────────────────────────────────────────────────
# حدود نسب التشابه
# ─────────────────────────────────────────────────
SCORE_EXACT     = 100
SCORE_HIGH_MIN  = 95
SCORE_REVIEW_MIN = 90

# ─────────────────────────────────────────────────
# دوال البحث الأساسية
# ─────────────────────────────────────────────────

def search_by_name(db: Database, name: str,
                   include_deleted: bool = False) -> list[dict]:
    """البحث بالاسم الأصلي (partial match)"""
    with db._get_connection() as conn:
        del_cond = "" if include_deleted else "AND is_deleted = 0"
        rows = conn.execute(
            f"""SELECT * FROM records
                WHERE original_name LIKE ? {del_cond}
                ORDER BY source_file, source_sheet, original_row
                LIMIT 500""",
            (f'%{name}%',)
        ).fetchall()
        return _parse_rows(rows)


def search_by_clean_name(db: Database, name: str,
                         include_deleted: bool = False) -> list[dict]:
    """البحث بالاسم المنظّف (بعد التطبيع العربي)"""
    clean = clean_arabic_name(name)
    with db._get_connection() as conn:
        del_cond = "" if include_deleted else "AND is_deleted = 0"
        rows = conn.execute(
            f"""SELECT * FROM records
                WHERE clean_name LIKE ? {del_cond}
                ORDER BY source_file, source_sheet, original_row
                LIMIT 500""",
            (f'%{clean}%',)
        ).fetchall()
        return _parse_rows(rows)


def search_by_sheet(db: Database, sheet_name: str,
                    include_deleted: bool = False) -> list[dict]:
    """البحث حسب اسم الشيت"""
    with db._get_connection() as conn:
        del_cond = "" if include_deleted else "AND is_deleted = 0"
        rows = conn.execute(
            f"""SELECT * FROM records
                WHERE source_sheet = ? {del_cond}
                ORDER BY original_row
                LIMIT 1000""",
            (sheet_name,)
        ).fetchall()
        return _parse_rows(rows)


def search_by_file(db: Database, file_name: str,
                   include_deleted: bool = False) -> list[dict]:
    """البحث حسب اسم الملف"""
    with db._get_connection() as conn:
        del_cond = "" if include_deleted else "AND is_deleted = 0"
        rows = conn.execute(
            f"""SELECT * FROM records
                WHERE source_file LIKE ? {del_cond}
                ORDER BY source_sheet, original_row
                LIMIT 1000""",
            (f'%{file_name}%',)
        ).fetchall()
        return _parse_rows(rows)


def list_deleted(db: Database) -> list[dict]:
    """سرد السجلات المحذوفة منطقيًا"""
    with db._get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM records WHERE is_deleted = 1
               ORDER BY updated_at DESC LIMIT 1000"""
        ).fetchall()
        return _parse_rows(rows)


def list_active(db: Database, limit: int = 1000,
                offset: int = 0) -> list[dict]:
    """سرد السجلات النشطة غير المحذوفة"""
    with db._get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM records WHERE is_deleted = 0
               ORDER BY source_file, source_sheet, original_row
               LIMIT ? OFFSET ?""",
            (limit, offset)
        ).fetchall()
        return _parse_rows(rows)


# ─────────────────────────────────────────────────
# المطابقة
# ─────────────────────────────────────────────────

def match_single_name(db: Database, query_name: str,
                      limit: int = 10) -> dict:
    """
    مطابقة اسم واحد مع قاعدة البيانات.

    المراحل:
    1. مطابقة مباشرة (exact) بعد التنظيف
    2. مطابقة تقريبية (fuzzy) بـ rapidfuzz

    يُرجع:
        {
          'query': الاسم الأصلي,
          'query_clean': الاسم المنظف,
          'result': 'موجود' | 'محتمل موجود' | 'يحتاج مراجعة' | 'غير موجود',
          'best_score': أعلى نسبة تشابه,
          'matches': [قائمة المطابقات],
        }
    """
    query_clean = clean_arabic_name(query_name)

    if not query_clean:
        return {
            'query': query_name,
            'query_clean': '',
            'result': 'اسم فارغ',
            'best_score': 0,
            'matches': [],
        }

    # جلب كل الأسماء النظيفة من قاعدة البيانات
    with db._get_connection() as conn:
        rows = conn.execute(
            """SELECT id, original_name, clean_name, source_file,
                      source_sheet, original_row
               FROM records
               WHERE is_deleted = 0 AND clean_name IS NOT NULL
               AND clean_name != ''"""
        ).fetchall()

    if not rows:
        return {
            'query': query_name,
            'query_clean': query_clean,
            'result': 'قاعدة البيانات فارغة',
            'best_score': 0,
            'matches': [],
        }

    # بناء قاموس: {clean_name: record_info}
    db_names = {r['clean_name']: dict(r) for r in rows}
    choices = list(db_names.keys())

    # المرحلة 1: مطابقة مباشرة
    if query_clean in db_names:
        rec = db_names[query_clean]
        return {
            'query': query_name,
            'query_clean': query_clean,
            'result': 'موجود',
            'best_score': 100,
            'matches': [_format_match(rec, 100, 'exact')],
        }

    # المرحلة 2: مطابقة تقريبية
    fuzzy_results = fuzz_process.extract(
        query_clean,
        choices,
        scorer=fuzz.token_sort_ratio,
        limit=limit,
    )

    matches = []
    best_score = 0

    for match_name, score, _ in fuzzy_results:
        if score < 60:
            continue
        rec = db_names[match_name]
        matches.append(_format_match(rec, score, 'fuzzy'))
        if score > best_score:
            best_score = score

    # تحديد النتيجة
    result_label = _score_to_label(best_score)

    return {
        'query': query_name,
        'query_clean': query_clean,
        'result': result_label,
        'best_score': best_score,
        'matches': matches,
    }


def match_excel_against_db(db: Database, check_file_path: str,
                            name_column: str | None = None) -> list[dict]:
    """
    مطابقة ملف Excel صغير بالكامل ضد قاعدة البيانات.

    المعاملات:
        check_file_path: مسار ملف Excel للمقارنة
        name_column: اسم عمود الاسم (اختياري — يُكتشف تلقائيًا)

    يُرجع:
        قائمة بنتائج المطابقة لكل صف
    """
    import pandas as pd
    from cleaner import detect_name_column, prepare_columns

    df = pd.read_excel(check_file_path, dtype=str, header=0)
    clean_cols, _ = prepare_columns(df.columns.tolist())
    df.columns = clean_cols

    detected_col = name_column or detect_name_column(clean_cols)
    if not detected_col:
        raise ValueError(
            "لم يُعثر على عمود الاسم. حدّد اسم العمود يدويًا."
        )

    results = []
    for i, row in df.iterrows():
        name = str(row.get(detected_col, '') or '').strip()
        if not name or name.lower() == 'nan':
            continue
        match_result = match_single_name(db, name)
        match_result['source_row'] = i + 2  # رقم الصف في Excel
        results.append(match_result)

    return results


# ─────────────────────────────────────────────────
# دوال مساعدة
# ─────────────────────────────────────────────────

def _parse_rows(rows) -> list[dict]:
    """تحويل صفوف SQLite إلى قواميس مع فك JSON"""
    result = []
    for row in rows:
        r = dict(row)
        try:
            r['row_data'] = json.loads(r.get('row_json', '{}'))
        except Exception:
            r['row_data'] = {}
        result.append(r)
    return result


def _format_match(rec: dict, score: float, match_type: str) -> dict:
    """تنسيق نتيجة مطابقة واحدة"""
    return {
        'record_id': rec['id'],
        'original_name': rec['original_name'],
        'clean_name': rec['clean_name'],
        'source_file': rec['source_file'],
        'source_sheet': rec['source_sheet'],
        'original_row': rec['original_row'],
        'similarity_score': score,
        'match_type': match_type,
        'label': _score_to_label(score),
    }


def _score_to_label(score: float) -> str:
    """تحويل نسبة التشابه إلى تسمية نصية"""
    if score >= SCORE_EXACT:
        return 'موجود'
    elif score >= SCORE_HIGH_MIN:
        return 'محتمل موجود بدرجة عالية'
    elif score >= SCORE_REVIEW_MIN:
        return 'يحتاج مراجعة'
    else:
        return 'غير موجود'


def print_match_result(result: dict):
    """طباعة نتيجة مطابقة اسم واحد"""
    print(f"\n  الاسم       : {result['query']}")
    print(f"  المنظّف     : {result['query_clean']}")
    print(f"  النتيجة     : {result['result']}")
    print(f"  أعلى تشابه  : {result['best_score']}%")
    if result['matches']:
        print(f"  أفضل مطابقات:")
        for m in result['matches'][:5]:
            print(f"    - {m['original_name']} ({m['source_sheet']}) "
                  f"— {m['similarity_score']:.1f}% [{m['label']}]")
