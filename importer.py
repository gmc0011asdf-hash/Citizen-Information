# importer.py — قراءة ملفات Excel واستيراد بياناتها إلى SQLite

import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# ضمان دعم UTF-8 في الطباعة على Windows
def _safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = ' '.join(str(a) for a in args)
        print(text.encode('ascii', errors='replace').decode('ascii'), **kwargs)

from cleaner import (
    clean_arabic_name,
    detect_name_column,
    prepare_columns,
)
from db import Database


class ExcelImporter:
    """
    يقرأ ملف Excel (xlsx أو xls)، يعالج كل الشيتات،
    ويستورد البيانات إلى قاعدة البيانات.
    """

    def __init__(self, db: Database | None = None):
        self.db = db or Database()

    # ─────────────────────────────────────────────
    # القراءة
    # ─────────────────────────────────────────────

    def read_excel(self, file_path: str) -> dict[str, pd.DataFrame]:
        """
        قراءة كل الشيتات من ملف Excel.
        يُرجع قاموسًا: {sheet_name: DataFrame}
        """
        file_path = str(file_path)
        ext = Path(file_path).suffix.lower()

        if ext not in ('.xlsx', '.xls', '.xlsm', '.xlsb'):
            raise ValueError(f"صيغة الملف غير مدعومة: {ext}")

        try:
            # قراءة كل الشيتات
            sheets = pd.read_excel(
                file_path,
                sheet_name=None,
                dtype=str,        # نقرأ كل شيء نصًا لتجنب تحويل الأرقام
                header=0,
                engine='openpyxl' if ext in ('.xlsx', '.xlsm', '.xlsb') else None,
            )
        except Exception as e:
            raise RuntimeError(f"فشل قراءة الملف: {e}")

        if not sheets:
            raise ValueError("الملف لا يحتوي على أي شيت")

        return sheets

    # ─────────────────────────────────────────────
    # المعالجة
    # ─────────────────────────────────────────────

    def process_sheet(self, df: pd.DataFrame, sheet_name: str,
                      source_file: str, batch_id: int,
                      original_row_offset: int = 2) -> list[dict]:
        """
        تحويل DataFrame واحد إلى قائمة من السجلات الجاهزة للإدراج.
        original_row_offset=2 لأن الصف الأول في Excel هو العنوان (رقم 1)
        والبيانات تبدأ من صف 2.
        """
        if df.empty:
            return []

        # تنظيف أسماء الأعمدة
        clean_cols, _ = prepare_columns(df.columns.tolist())
        df.columns = clean_cols

        # حذف الصفوف الفارغة كليًا
        df = df.dropna(how='all')

        # الكشف عن عمود الاسم
        name_col = detect_name_column(clean_cols)

        records = []
        for idx, (excel_row_idx, row) in enumerate(df.iterrows()):
            # الصف الأصلي في Excel (يبدأ من 2)
            original_row = excel_row_idx + original_row_offset

            # بناء بيانات الصف كـ dict نظيف
            row_data = {}
            for col in clean_cols:
                val = row.get(col)
                if pd.isna(val) if isinstance(val, float) else (
                    val is None or str(val).strip().lower() == 'nan'
                ):
                    row_data[col] = None
                else:
                    row_data[col] = str(val).strip()

            # استخراج الاسم إذا وُجد عمود اسم
            original_name = ''
            clean_name_val = ''
            if name_col and name_col in row_data and row_data[name_col]:
                original_name = str(row_data[name_col]).strip()
                clean_name_val = clean_arabic_name(original_name)

            records.append({
                'batch_id': batch_id,
                'source_file': source_file,
                'source_sheet': sheet_name,
                'original_row': original_row,
                'original_name': original_name,
                'clean_name': clean_name_val,
                'row_data': row_data,
            })

        return records

    # ─────────────────────────────────────────────
    # الاستيراد الرئيسي
    # ─────────────────────────────────────────────

    def import_file(self, file_path: str,
                    force_new_batch: bool = True) -> dict:
        """
        الدالة الرئيسية: تستورد ملف Excel كاملًا إلى قاعدة البيانات.

        المعاملات:
            file_path: مسار ملف Excel
            force_new_batch: True = دفعة جديدة دائمًا

        يُرجع:
            dict يحتوي على إحصائيات الاستيراد
        """
        file_path = str(file_path)
        source_file = Path(file_path).name  # اسم الملف فقط بدون المسار الكامل

        print(f"\n{'='*60}")
        print(f"  بدء استيراد: {source_file}")
        print(f"{'='*60}")

        # قراءة الملف
        print("  [1/4] قراءة ملف Excel...")
        sheets = self.read_excel(file_path)
        sheets_count = len(sheets)
        print(f"        وُجد {sheets_count} شيت: {list(sheets.keys())}")

        # إنشاء دفعة استيراد
        batch_id = self.db.create_batch(
            source_file=source_file,
            sheets_count=sheets_count,
            notes=f"استيراد من: {file_path}"
        )
        print(f"  [2/4] تم إنشاء دفعة الاستيراد رقم: {batch_id}")

        # معالجة كل شيت
        print("  [3/4] معالجة الشيتات...")
        all_records = []
        sheets_report = []

        for sheet_name, df in sheets.items():
            sheet_records = self.process_sheet(
                df=df,
                sheet_name=str(sheet_name),
                source_file=source_file,
                batch_id=batch_id,
            )

            records_with_name = sum(
                1 for r in sheet_records if r['original_name']
            )

            sheets_report.append({
                'sheet': sheet_name,
                'rows': len(sheet_records),
                'with_name': records_with_name,
            })

            print(f"        شيت [{sheet_name}]: {len(sheet_records)} صف، "
                  f"{records_with_name} باسم")

            all_records.extend(sheet_records)

        # الإدراج الجماعي
        print(f"  [4/4] حفظ {len(all_records)} سجل في قاعدة البيانات...")
        inserted = self.db.insert_records_bulk(all_records)

        # تحديث الدفعة
        total_with_name = sum(r['with_name'] for r in sheets_report)
        self.db.update_batch(
            batch_id=batch_id,
            rows_count=inserted,
            sheets_count=sheets_count,
            status='completed'
        )

        report = {
            'batch_id': batch_id,
            'source_file': source_file,
            'source_path': file_path,
            'sheets_count': sheets_count,
            'total_rows': inserted,
            'rows_with_name': total_with_name,
            'sheets_detail': sheets_report,
            'db_path': str(self.db.db_path),
            'imported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        self._print_report(report)
        return report

    # ─────────────────────────────────────────────
    # التقرير
    # ─────────────────────────────────────────────

    def _print_report(self, report: dict):
        """طباعة تقرير الاستيراد بشكل منسّق"""
        print(f"\n{'='*60}")
        print("  تقرير الاستيراد")
        print(f"{'='*60}")
        print(f"  الملف         : {report['source_file']}")
        print(f"  عدد الشيتات   : {report['sheets_count']}")
        print(f"  إجمالي الصفوف : {report['total_rows']}")
        print(f"  صفوف بأسماء   : {report['rows_with_name']}")
        print(f"  رقم الدفعة    : {report['batch_id']}")
        print(f"  قاعدة البيانات: {report['db_path']}")
        print(f"  وقت الاستيراد : {report['imported_at']}")
        print(f"{'='*60}\n")

    # ─────────────────────────────────────────────
    # فحص الاستيراد السابق
    # ─────────────────────────────────────────────

    def check_previous_import(self, file_path: str) -> dict | None:
        """
        التحقق من وجود استيراد سابق لنفس الملف.
        يُرجع معلومات الدفعة السابقة أو None.
        """
        source_file = Path(file_path).name
        return self.db.find_batch_by_file(source_file)
