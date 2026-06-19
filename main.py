# main.py — نقطة الدخول الرئيسية للبرنامج
# التشغيل: python main.py

import sys
import os

# ضمان دعم UTF-8 في الطرفية على Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import tkinter as tk
from tkinter import filedialog, messagebox

from db import Database
from importer import ExcelImporter


def choose_excel_file() -> str | None:
    """
    فتح نافذة اختيار ملف Excel.
    يُرجع المسار الكامل للملف أو None إذا ألغى المستخدم.
    """
    root = tk.Tk()
    root.withdraw()          # إخفاء النافذة الرئيسية
    root.attributes('-topmost', True)   # تظهر في المقدمة

    file_path = filedialog.askopenfilename(
        title='اختر ملف Excel للاستيراد',
        filetypes=[
            ('ملفات Excel', '*.xlsx *.xls *.xlsm *.xlsb'),
            ('كل الملفات', '*.*'),
        ],
    )
    root.destroy()
    return file_path if file_path else None


def ask_reimport_choice(file_name: str, prev_batch: dict) -> str:
    """
    عرض خيارات إعادة الاستيراد عند وجود دفعة سابقة.

    يُرجع: 'new' | 'update' | 'cancel'
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    msg = (
        f"الملف '{file_name}' تم استيراده مسبقًا.\n\n"
        f"آخر استيراد: {prev_batch.get('imported_at', 'غير معروف')}\n"
        f"عدد السجلات السابقة: {prev_batch.get('rows_count', 0)}\n\n"
        f"ماذا تريد أن تفعل؟"
    )

    choice = {'value': 'cancel'}

    dialog = tk.Toplevel(root)
    dialog.title('تحذير: ملف مستورد مسبقًا')
    dialog.geometry('420x220')
    dialog.resizable(False, False)
    dialog.attributes('-topmost', True)

    tk.Label(
        dialog, text=msg, justify='right', wraplength=390, pady=10
    ).pack(padx=10, pady=10)

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=10)

    def on_new():
        choice['value'] = 'new'
        dialog.destroy()

    def on_cancel():
        choice['value'] = 'cancel'
        dialog.destroy()

    tk.Button(
        btn_frame, text='استيراد كدفعة جديدة',
        command=on_new, bg='#1F4E79', fg='white', width=20, pady=5
    ).pack(side='left', padx=5)

    tk.Button(
        btn_frame, text='إلغاء العملية',
        command=on_cancel, bg='#C00000', fg='white', width=15, pady=5
    ).pack(side='left', padx=5)

    root.wait_window(dialog)
    root.destroy()
    return choice['value']


def show_report_dialog(report: dict):
    """عرض نافذة تقرير الاستيراد"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    sheets_detail = '\n'.join(
        f"  • {s['sheet']}: {s['rows']} صف ({s['with_name']} باسم)"
        for s in report.get('sheets_detail', [])
    )

    msg = (
        f"تم الاستيراد بنجاح!\n\n"
        f"الملف: {report['source_file']}\n"
        f"عدد الشيتات: {report['sheets_count']}\n"
        f"إجمالي الصفوف: {report['total_rows']}\n"
        f"صفوف بأسماء: {report['rows_with_name']}\n\n"
        f"تفاصيل الشيتات:\n{sheets_detail}\n\n"
        f"قاعدة البيانات:\n{report['db_path']}"
    )

    messagebox.showinfo('تقرير الاستيراد', msg)
    root.destroy()


def main():
    print("=" * 60)
    print("  نظام استيراد Excel إلى SQLite")
    print("  Excel → SQLite Importer")
    print("=" * 60)

    # تهيئة قاعدة البيانات
    db = Database()
    importer = ExcelImporter(db=db)

    # اختيار ملف Excel
    print("\n  [*] يرجى اختيار ملف Excel من نافذة الاختيار...")
    file_path = choose_excel_file()

    if not file_path:
        print("  [!] لم يتم اختيار أي ملف. تم إلغاء العملية.")
        return

    print(f"  [*] الملف المختار: {file_path}")

    # فحص الاستيراد السابق
    prev_batch = importer.check_previous_import(file_path)

    if prev_batch:
        import os
        file_name = os.path.basename(file_path)
        choice = ask_reimport_choice(file_name, prev_batch)

        if choice == 'cancel':
            print("  [!] تم إلغاء العملية.")
            return
        elif choice == 'new':
            print("  [*] سيتم الاستيراد كدفعة جديدة.")
            # الدفعة الجديدة تُضاف تلقائيًا في import_file
    else:
        print("  [*] ملف جديد — جارٍ الاستيراد...")

    # تنفيذ الاستيراد
    try:
        report = importer.import_file(file_path, force_new_batch=True)
        show_report_dialog(report)
        print("  [✓] اكتمل الاستيراد بنجاح.")

    except ValueError as e:
        print(f"\n  [!] خطأ في البيانات: {e}")
        _show_error(str(e))

    except RuntimeError as e:
        print(f"\n  [!] خطأ في قراءة الملف: {e}")
        _show_error(str(e))

    except Exception as e:
        print(f"\n  [!] خطأ غير متوقع: {e}")
        _show_error(str(e))


def _show_error(msg: str):
    """عرض رسالة خطأ للمستخدم"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        messagebox.showerror('خطأ', msg)
        root.destroy()
    except Exception:
        pass


if __name__ == '__main__':
    main()
