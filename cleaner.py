# cleaner.py — تنظيف الأسماء العربية وأسماء الأعمدة
# يعمل بترميز UTF-8 ويدعم اللغة العربية بالكامل

import re
import unicodedata

# أنماط عمود الاسم المحتملة بالعربية والإنجليزية
NAME_COLUMN_PATTERNS = [
    'الاسم', 'اسم', 'الاسم الكامل', 'الاسم الكاملة', 'الإسم', 'الاسم الرباعي',
    'full_name', 'fullname', 'name', 'Name', 'NAME', 'employee_name',
    'اسم الموظف', 'اسم الطالب', 'اسم العميل', 'اسم الشخص', 'الاسم واللقب',
]


def clean_arabic_name(text) -> str:
    """
    تنظيف الاسم العربي وإعداده للمطابقة:
    - توحيد أشكال الألف (أ إ آ ٱ) إلى (ا)
    - تحويل (ى) إلى (ي)
    - تحويل (ة) إلى (ه)
    - تحويل (ؤ) إلى (و)
    - تحويل (ئ) إلى (ي)
    - حذف التشكيل والحركات
    - حذف المدّة (ـ)
    - توحيد المسافات
    - حذف الرموز غير المهمة
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ''

    text = text.strip()

    if not text or text.lower() == 'nan':
        return ''

    # حذف التشكيل (الحركات الإعرابية)
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

    # توحيد أشكال الألف المختلفة
    text = re.sub(r'[أإآٱ]', 'ا', text)

    # تحويل الألف المقصورة إلى ياء
    text = text.replace('ى', 'ي')

    # تحويل التاء المربوطة إلى هاء
    text = text.replace('ة', 'ه')

    # تحويل الواو مع الهمزة
    text = text.replace('ؤ', 'و')

    # تحويل الياء مع الهمزة
    text = text.replace('ئ', 'ي')

    # حذف المد
    text = text.replace('ـ', '')

    # حذف الرموز غير الأبجدية (الاحتفاظ بالحروف العربية والإنجليزية والمسافات)
    text = re.sub(r'[^؀-ۿa-zA-Z0-9\s]', '', text)

    # توحيد المسافات المتعددة
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def detect_name_column(columns: list) -> str | None:
    """
    البحث عن عمود الاسم من بين أعمدة الـ DataFrame.
    يُرجع اسم العمود إذا وُجد، وإلا None.
    """
    for col in columns:
        col_str = str(col).strip()

        # مطابقة مباشرة بالأنماط المعرّفة
        if col_str in NAME_COLUMN_PATTERNS:
            return col_str

        # مطابقة بتجاهل حالة الأحرف الإنجليزية
        col_lower = col_str.lower()
        patterns_lower = [p.lower() for p in NAME_COLUMN_PATTERNS]
        if col_lower in patterns_lower:
            return col_str

        # إذا احتوى اسم العمود على كلمة "اسم"
        if 'اسم' in col_str or 'الاسم' in col_str:
            return col_str

        # إذا احتوى على name بأي شكل
        if 'name' in col_lower and col_lower not in ('unnamed', 'nan'):
            return col_str

    return None


def clean_column_name(col) -> str:
    """
    تنظيف اسم العمود لجعله صالحًا لقواعد البيانات والـ DataFrame.
    """
    col_str = str(col).strip()

    if not col_str or col_str.lower() == 'nan':
        return 'unnamed_col'

    # استبدال المسافات بـ underscore
    col_str = re.sub(r'\s+', '_', col_str)

    # الاحتفاظ فقط بالحروف العربية والإنجليزية والأرقام والشرطة السفلية
    col_str = re.sub(r'[^؀-ۿa-zA-Z0-9_]', '_', col_str)

    # دمج الشرطات المتعددة
    col_str = re.sub(r'_+', '_', col_str).strip('_')

    return col_str if col_str else 'unnamed_col'


def deduplicate_columns(columns: list) -> list:
    """
    معالجة أسماء الأعمدة المكررة بإضافة رقم تسلسلي.
    """
    seen: dict[str, int] = {}
    result = []

    for col in columns:
        if col in seen:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            result.append(col)

    return result


def prepare_columns(raw_columns) -> tuple:
    """
    تنظيف كل أسماء الأعمدة ومعالجة الفراغات والتكرار.

    يُرجع:
        (قائمة الأعمدة النظيفة، خريطة من الأصلي إلى النظيف)
    """
    cleaned = [clean_column_name(c) for c in raw_columns]
    cleaned = deduplicate_columns(cleaned)
    mapping = {str(raw): clean for raw, clean in zip(raw_columns, cleaned)}
    return cleaned, mapping
