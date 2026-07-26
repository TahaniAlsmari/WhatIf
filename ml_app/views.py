
from difflib import SequenceMatcher
from django.http import JsonResponse
from django.shortcuts import render
import logging
import os
from .models import DecisionRecord

import re
import pandas as pd

from .model_loader import model, decision_encoder, explainer
from .gemini_service import analyze_decision

logger = logging.getLogger(__name__)

DEBUG_AI_PIPELINE = (
    os.getenv(
        "DEBUG_AI_PIPELINE",
        "false"
    ).lower() == "true"
)

FEATURE_ORDER = [
    "الإيرادات_السنوية",
    "المصاريف_التشغيلية",
    "صافي_الربح",
    "هامش_الربح_%",
    "عدد_الموظفين",
    "إجمالي_الأصول",
    "إجمالي_الديون",
    "نسبة_الدين_للأصول_%",
    "التدفق_النقدي",
    "نوع_القرار",
    "تكلفة_القرار",
]


FEATURE_LABELS = {
    "الإيرادات_السنوية": "الإيرادات السنوية",
    "المصاريف_التشغيلية": "المصاريف التشغيلية",
    "صافي_الربح": "صافي الربح",
    "هامش_الربح_%": "هامش الربح",
    "عدد_الموظفين": "عدد الموظفين",
    "إجمالي_الأصول": "إجمالي الأصول",
    "إجمالي_الديون": "إجمالي الديون",
    "نسبة_الدين_للأصول_%": "نسبة الدين إلى الأصول",
    "التدفق_النقدي": "التدفق النقدي",
    "نوع_القرار": "نوع القرار",
    "تكلفة_القرار": "تكلفة القرار",
}


COMPANY_DATA = {
    "الإيرادات_السنوية": 7223228,
    "المصاريف_التشغيلية": 5501786,
    "صافي_الربح": 1721442,
    "هامش_الربح_%": 23.8,
    "عدد_الموظفين": 60,
    "إجمالي_الأصول": 10623613,
    "إجمالي_الديون": 6391165,
    "نسبة_الدين_للأصول_%": 60.2,
    "التدفق_النقدي": 2117514,
}


DECISION_NORMALIZATION = {
    "شراء معدات جديدة": "شراء معدات",
    "شراء معدات جديده": "شراء معدات",
    "شراء معدات": "شراء معدات",

    "افتتاح فرع": "افتتاح فرع جديد",
    "فتح فرع": "افتتاح فرع جديد",
    "فتح فرع جديد": "افتتاح فرع جديد",

    "تطوير النظام": "تطوير نظام تقني",
    "تطوير النظام التقني": "تطوير نظام تقني",
    "تطوير نظام": "تطوير نظام تقني",

    "توظيف موظفين جدد": "توظيف موظفين",
    "توظيف موظفين": "توظيف موظفين",

    "حملة تسويقية جديدة": "حملة تسويقية",
    "حملة تسويقية": "حملة تسويقية",


    "التوسع في سوق جديد": "دخول سوق جديد",
    "دخول سوق جديد": "دخول سوق جديد",
}


RISK_MAPPING = {
    0: "منخفض",
    1: "متوسط",
    2: "مرتفع",
}
ARABIC_DIGITS_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)

def normalize_digits(text):

    if text is None:
        return ""

    return str(text).translate(
        ARABIC_DIGITS_TRANSLATION
    )

def landing_view(request):

    records = DecisionRecord.objects.filter(user=request.user)

    total_decisions = records.count()

    low_count = records.filter(
        risk_level="منخفض"
    ).count()

    medium_count = records.filter(
        risk_level="متوسط"
    ).count()

    high_count = records.filter(
        risk_level="مرتفع"
    ).count()

    return render(
        request,
        "ml_app/landing.html",
        {
            "active_page": "home",
            "total_decisions": total_decisions,
            "low_count": low_count,
            "medium_high_count": (
                medium_count + high_count
            ),
        }
    )
def home_view(request):

    records = DecisionRecord.objects.filter(user=request.user)

    total_decisions = records.count()

    low_count = records.filter(
        risk_level="منخفض"
    ).count()

    medium_count = records.filter(
        risk_level="متوسط"
    ).count()

    high_count = records.filter(
        risk_level="مرتفع"
    ).count()

    return render(
        request,
        "ml_app/home.html",
        {
            "active_page": "dashboard",
            "records": records,
            "total_decisions": total_decisions,
            "low_count": low_count,
            "medium_count": medium_count,
            "high_count": high_count,
        }
    )
def normalize_arabic_text(text):

    if not text:
        return ""

    text = normalize_digits(str(text).lower().strip())

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ؤ": "و",
        "ئ": "ي",
        "ى": "ي",
        "ة": "ه",
        "ـ": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)


    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text,
    )


    text = re.sub(
        r"[^\u0600-\u06FFa-zA-Z0-9\s]",
        " ",
        text,
    )


    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def similarity_score(text1, text2):

    return SequenceMatcher(
        None,
        normalize_arabic_text(text1),
        normalize_arabic_text(text2),
    ).ratio()

def normalize_decision(decision_text):

    if not decision_text:
        return None

    known_decisions = list(
        decision_encoder.classes_
    )

    normalized_text = normalize_arabic_text(
        decision_text
    )



    decision_aliases = {
        "توظيف موظفين": [
            "توظيف موظفين",
            "توظيف موظف",
            "توظيف اشخاص",
            "تعيين موظفين",
            "تعيين موظف",
            "استخدام موظفين",
            "زياده الموظفين",
            "زياده عدد الموظفين",
            "نوظف",
            "اوظف",
            "ابي اوظف",
            "نبي نوظف",
            "نحتاج نوظف",
            "نرغب في التوظيف",
            "توظف",
            "وظف",
            "نعين",
            "ابي اعين",
            "تعيين كفاءات",
            "استقطاب موظفين",
            "استقطاب كفاءات",
        ],

        "إطلاق منتج جديد": [
            "اطلاق منتج جديد",
            "اطلاق منتج",
            "طرح منتج جديد",
            "طرح منتج",
            "منتج جديد",
            "تطوير منتج جديد",
            "اصدار منتج",
            "تقديم منتج جديد",
            "ندشن منتج",
            "نطلق منتج",
            "ابي اطلق منتج",
        ],

        "افتتاح فرع جديد": [
            "افتتاح فرع جديد",
            "فتح فرع جديد",
            "افتتاح فرع",
            "فتح فرع",
            "انشاء فرع",
            "تاسيس فرع",
            "فرع جديد",
            "نفتح فرع",
            "ابي افتح فرع",
            "التوسع بفرع جديد",
        ],

        "شراء معدات": [
            "شراء معدات",
            "شراء معدات جديده",
            "شراء اجهزه",
            "شراء جهاز",
            "شراء الات",
            "شراء ماكينات",
            "تحديث المعدات",
            "استبدال المعدات",
            "توفير معدات",
            "اقتناء معدات",
            "نشتري معدات",
            "ابي اشتري معدات",
        ],

        "حملة تسويقية": [
            "حمله تسويقيه",
            "حمله اعلانيه",
            "حمله تسويق",
            "اعلان",
            "اعلانات",
            "تسويق",
            "تسويق المنتج",
            "اطلاق حمله",
            "حمله دعائيه",
            "ميزانيه تسويق",
            "نبي نسوق",
            "ابي اسوي حمله",
        ],

        "دخول سوق جديد": [
            "دخول سوق جديد",
            "التوسع في السوق",
            "توسع في السوق",
            "التوسع في سوق جديد",
            "دخول اسواق جديده",
            "التوسع الجغرافي",
            "دخول منطقه جديده",
            "دخول دوله جديده",
            "التوسع خارجيا",
            "فتح سوق جديد",
            "ندخل سوق",
            "نوسع السوق",
        ],

        "تطوير نظام تقني": [
            "تطوير نظام تقني",
            "تطوير نظام",
            "تطوير النظام",
            "تطوير التقنيه",
            "تطوير تقني",
            "تحديث النظام",
            "انشاء نظام",
            "بناء نظام",
            "نظام جديد",
            "برنامج جديد",
            "تطوير برنامج",
            "منصه تقنيه",
            "بناء منصه",
            "حل تقني",
            "التحول الرقمي",
            "رقمنه",
            "تطوير الموقع",
            "تطوير التطبيق",
            "انشاء تطبيق",
            "تطوير تطبيق",
        ],
    }



    for known_decision in known_decisions:
        if (
            normalize_arabic_text(
                known_decision
            ) == normalized_text
        ):
            return known_decision



    for target_decision, aliases in decision_aliases.items():

        if target_decision not in known_decisions:
            continue

        for alias in aliases:

            normalized_alias = normalize_arabic_text(
                alias
            )

            if normalized_alias in normalized_text:
                return target_decision



    token_groups = {
        "توظيف موظفين": [
            "وظف",
            "توظيف",
            "موظف",
            "موظفين",
            "تعيين",
            "نعين",
            "استقطاب",
            "كفاءات",
        ],

        "إطلاق منتج جديد": [
            "منتج",
            "اطلاق",
            "طرح",
            "تدشين",
        ],

        "افتتاح فرع جديد": [
            "فرع",
            "افتتاح",
            "فتح",
            "تاسيس",
        ],

        "شراء معدات": [
            "معدات",
            "اجهزه",
            "جهاز",
            "الات",
            "ماكينات",
        ],

        "حملة تسويقية": [
            "تسويق",
            "تسويقيه",
            "حمله",
            "اعلان",
            "دعائيه",
        ],

        "دخول سوق جديد": [
            "سوق",
            "اسواق",
            "توسع",
            "التوسع",
            "جغرافي",
        ],

        "تطوير نظام تقني": [
            "نظام",
            "تقني",
            "تقنيه",
            "برنامج",
            "منصه",
            "تطبيق",
            "رقمي",
            "رقمنه",
        ],
    }

    scores = {}

    for target_decision, keywords in token_groups.items():

        if target_decision not in known_decisions:
            continue

        score = 0

        for keyword in keywords:
            if keyword in normalized_text:
                score += 1

        scores[target_decision] = score

    if scores:
        best_decision = max(
            scores,
            key=scores.get,
        )

        if scores[best_decision] > 0:
            return best_decision



    best_match = None
    best_score = 0

    for target_decision, aliases in decision_aliases.items():

        if target_decision not in known_decisions:
            continue

        for alias in aliases:

            score = similarity_score(
                normalized_text,
                alias,
            )

            if score > best_score:
                best_score = score
                best_match = target_decision


    if best_score >= 0.62:
        return best_match

    return None


def number_with_multiplier(
    number_text,
    unit_text="",
):

    number_text = (
        number_text
        .replace(",", "")
        .replace("٬", "")
        .strip()
    )

    value = float(number_text)

    unit_text = unit_text or ""

    if "مليار" in unit_text:
        value *= 1_000_000_000

    elif "مليون" in unit_text:
        value *= 1_000_000

    elif (
        "ألف" in unit_text
        or "الف" in unit_text
    ):
        value *= 1_000

    return int(round(value))
ARABIC_NUMBER_WORDS = {
    "صفر": 0,

    "واحد": 1,
    "واحده": 1,
    "واحدة": 1,
    "احد": 1,
    "إحدى": 1,

    "اثنين": 2,
    "اثنان": 2,
    "اثنتين": 2,
    "اثنتان": 2,
    "اثنينه": 2,

    "ثلاث": 3,
    "ثلاثه": 3,
    "ثلاثة": 3,

    "اربع": 4,
    "اربعه": 4,
    "أربع": 4,
    "أربعة": 4,

    "خمس": 5,
    "خمسه": 5,
    "خمسة": 5,

    "ست": 6,
    "سته": 6,
    "ستة": 6,

    "سبع": 7,
    "سبعه": 7,
    "سبعة": 7,

    "ثمان": 8,
    "ثمانيه": 8,
    "ثمانية": 8,
    "ثماني": 8,

    "تسع": 9,
    "تسعه": 9,
    "تسعة": 9,

    "عشر": 10,
    "عشره": 10,
    "عشرة": 10,

    "احدعشر": 11,
    "احدى عشر": 11,
    "احد عشر": 11,

    "اثناعشر": 12,
    "اثنا عشر": 12,
    "اثني عشر": 12,

    "عشرين": 20,
    "عشرون": 20,

    "ثلاثين": 30,
    "ثلاثون": 30,

    "اربعين": 40,
    "أربعين": 40,

    "خمسين": 50,
    "ستين": 60,
    "سبعين": 70,
    "ثمانين": 80,
    "تسعين": 90,

    "مئه": 100,
    "مئة": 100,
    "مائه": 100,
    "مائة": 100,

    "مئتين": 200,
    "مئتان": 200,
    "مائتين": 200,
    "مائتان": 200,

    "ثلاثمئه": 300,
    "ثلاثمئة": 300,
    "اربعمئه": 400,
    "اربعمئة": 400,
    "خمسمئه": 500,
    "خمسمئة": 500,
    "ستمئه": 600,
    "ستمئة": 600,
    "سبعمئه": 700,
    "سبعمئة": 700,
    "ثمانمئه": 800,
    "ثمانمئة": 800,
    "تسعمئه": 900,
    "تسعمئة": 900,
}


def normalize_number_words_text(text):

    if not text:
        return ""

    text = normalize_digits(str(text).lower())

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ـ": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text,
    )

    text = text.replace("،", " ")
    text = re.sub(r"\s+", " ", text).strip()

    return text


def parse_small_arabic_number(words):

    if not words:
        return None

    cleaned_words = []

    for word in words:
        word = word.strip()

        if not word:
            continue



        if word.startswith("و") and len(word) > 1:
            word = word[1:]

        cleaned_words.append(word)

    phrase = " ".join(cleaned_words)

    if phrase in ARABIC_NUMBER_WORDS:
        return ARABIC_NUMBER_WORDS[phrase]

    total = 0
    found = False

    for word in cleaned_words:
        if word in ARABIC_NUMBER_WORDS:
            total += ARABIC_NUMBER_WORDS[word]
            found = True

    if not found:
        return None

    return total


def extract_textual_cost(text):

    normalized_text = normalize_number_words_text(text)


    special_patterns = [
        (
            r"\bمليون\s+ونصف\b",
            1_500_000,
        ),
        (
            r"\bمليون\s+و\s+نصف\b",
            1_500_000,
        ),
        (
            r"\bنصف\s+مليون\b",
            500_000,
        ),
        (
            r"\bربع\s+مليون\b",
            250_000,
        ),
        (
            r"\bنصف\s+مليار\b",
            500_000_000,
        ),
    ]

    for pattern, value in special_patterns:
        if re.search(pattern, normalized_text):
            return value

    unit_multipliers = {
        "الف": 1_000,
        "الاف": 1_000,
        "مليون": 1_000_000,
        "ملايين": 1_000_000,
        "مليار": 1_000_000_000,
        "مليارات": 1_000_000_000,
    }


    pattern = re.compile(
        r"((?:[\u0600-\u06FF]+\s+){0,4})"
        r"(الف|الاف|مليون|ملايين|مليار|مليارات)"
    )

    candidates = []

    count_words = [
        "موظف",
        "موظفين",
        "شخص",
        "اشخاص",
        "جهاز",
        "اجهزه",
        "فرع",
        "فروع",
        "منتج",
        "منتجات",
        "سنه",
        "سنوات",
        "شهر",
        "اشهر",
    ]

    for match in pattern.finditer(normalized_text):
        number_phrase = match.group(1).strip()
        unit = match.group(2)

        start, end = match.span()

        after_context = normalized_text[
            end:min(len(normalized_text), end + 20)
        ]


        if any(
            word in after_context
            for word in count_words
        ):
            continue

        multiplier = unit_multipliers[unit]

        if not number_phrase:
            base_number = 1
        else:
            words = number_phrase.split()


            numeric_words = [
                word
                for word in words
                if (
                    word in ARABIC_NUMBER_WORDS
                    or (
                        word.startswith("و")
                        and word[1:] in ARABIC_NUMBER_WORDS
                    )
                )
            ]

            base_number = parse_small_arabic_number(
                numeric_words
            )

        if base_number is None:
            continue

        value = int(base_number * multiplier)

        candidates.append(
            {
                "position": start,
                "value": value,
            }
        )

    if not candidates:
        return 0


    candidates.sort(
        key=lambda item: item["position"],
        reverse=True,
    )

    return candidates[0]["value"]

def extract_cost(text):

    if not text:
        return 0
    textual_cost = extract_textual_cost(text)

    normalized_text = normalize_digits(text)

    normalized_text = (
        normalized_text
        .replace("،", " ")
        .replace(",", "")
        .replace("٬", "")
    )


    financial_signals = [
        "تكلفة",
        "التكلفة",
        "بتكلفة",
        "تكلفته",
        "تكلفتها",
        "تكلف",
        "قيمة",
        "القيمة",
        "بقيمة",
        "قيمته",
        "قيمتها",
        "مبلغ",
        "المبلغ",
        "بمبلغ",
        "ميزانية",
        "الميزانية",
        "بميزانية",
        "ميزانيته",
        "ميزانيتها",
        "قدرها",
        "قدره",
        "إجمالي",
        "اجمالي",
        "استثمار",
        "استثماره",
        "استثمارها",
        "مخصص",
        "خصصنا",
        "رصدنا",
        "تمويل",
        "ميزانية مخصصة",
        "رواتب إجمالية",
        "اجمالي الرواتب",
        "إجمالي الرواتب",
        "برواتب",
    ]


    count_words = [
        "موظف",
        "موظفين",
        "شخص",
        "أشخاص",
        "اشخاص",
        "جهاز",
        "أجهزة",
        "اجهزة",
        "فرع",
        "فروع",
        "منتج",
        "منتجات",
        "آلة",
        "آلات",
        "اله",
        "الات",
        "سنة",
        "سنوات",
        "شهر",
        "أشهر",
        "اشهر",
        "يوم",
        "أيام",
        "ايام",
        "%",
        "نسبة",
    ]

    pattern = re.compile(
        r"(\d+(?:\.\d+)?)"
        r"\s*"
        r"(مليار|مليون|ألف|الف)?"
    )

    candidates = []

    for match in pattern.finditer(normalized_text):
        raw_number = match.group(1)
        unit = match.group(2) or ""

        start, end = match.span()

        before_context = normalized_text[
            max(0, start - 50):start
        ]

        after_context = normalized_text[
            end:min(len(normalized_text), end + 25)
        ]

        full_context = normalized_text[
            max(0, start - 50):
            min(len(normalized_text), end + 25)
        ]


        if any(
            word in after_context[:18]
            for word in count_words
        ):
            continue

        try:
            value = number_with_multiplier(
                raw_number,
                unit,
            )
        except (TypeError, ValueError):
            continue

        score = 0


        if any(
            signal in before_context
            for signal in financial_signals
        ):
            score += 10


        if (
            "ريال" in full_context
            or "ر.س" in full_context
        ):
            score += 8


        if unit:
            score += 4


        if score == 0:
            continue

        candidates.append(
            {
                "score": score,
                "position": start,
                "value": value,
            }
        )

    if not candidates:
        return textual_cost

    candidates.sort(
        key=lambda item: (
            item["score"],
            item["position"],
        ),
        reverse=True,
    )

    numeric_cost = candidates[0]["value"]



    if numeric_cost > 0:
        return numeric_cost

    return textual_cost


def reconcile_extracted_cost(
    text,
    gemini_cost,
):

    local_cost = extract_cost(text)

    try:
        gemini_cost = float(
            gemini_cost or 0
        )

    except (TypeError, ValueError):
        gemini_cost = 0

    if local_cost > 0:

        if gemini_cost <= 0:
            return float(local_cost)

        difference_ratio = (
            abs(gemini_cost - local_cost)
            / max(local_cost, 1)
        )

        if difference_ratio > 0.01:

            logger.warning(
                (
                    "Cost mismatch: "
                    "Gemini=%s, local=%s, text=%r"
                ),
                gemini_cost,
                local_cost,
                text,
            )

            return float(local_cost)

    return float(gemini_cost)


def build_financial_metrics(features):

    cost = float(
        features.get(
            "تكلفة_القرار",
            0
        ) or 0
    )

    cashflow = float(
        features.get(
            "التدفق_النقدي",
            0
        ) or 0
    )

    profit = float(
        features.get(
            "صافي_الربح",
            0
        ) or 0
    )

    revenue = float(
        features.get(
            "الإيرادات_السنوية",
            0
        ) or 0
    )

    assets = float(
        features.get(
            "إجمالي_الأصول",
            0
        ) or 0
    )

    debt = float(
        features.get(
            "إجمالي_الديون",
            0
        ) or 0
    )

    if assets:
        debt_to_assets = round(
            (debt / assets) * 100,
            2
        )
    else:
        debt_to_assets = None

    if cashflow:
        cost_to_cashflow = round(
            (cost / cashflow) * 100,
            2
        )
    else:
        cost_to_cashflow = None

    if profit > 0:
        cost_to_profit = round(
            (cost / profit) * 100,
            2
        )
    else:
        cost_to_profit = None

    if revenue:
        cost_to_revenue = round(
            (cost / revenue) * 100,
            2
        )
    else:
        cost_to_revenue = None

    return {
        "تكلفة_القرار": cost,

        "التدفق_النقدي": cashflow,

        "صافي_الربح": profit,

        "الإيرادات_السنوية": revenue,

        "إجمالي_الأصول": assets,

        "إجمالي_الديون": debt,

        "نسبة_الدين_للأصول_%": (
            debt_to_assets
        ),

        "نسبة_التكلفة_إلى_التدفق_النقدي_%": (
            cost_to_cashflow
        ),

        "نسبة_التكلفة_إلى_صافي_الربح_%": (
            cost_to_profit
        ),

        "نسبة_التكلفة_إلى_الإيرادات_%": (
            cost_to_revenue
        ),

        "هل_التدفق_النقدي_يغطي_التكلفة": (
            cashflow >= cost
            if cost > 0
            else None
        ),

        "الفائض_أو_العجز_بعد_التكلفة": round(
            cashflow - cost,
            2
        ),

        "هل_صافي_الربح_يغطي_التكلفة": (
            profit >= cost
            if cost > 0
            else None
        ),
    }
def fallback_extract_decision(text):

    normalized_decision = normalize_decision(
        text
    )

    if normalized_decision is None:
        return {
            "status": "unsupported",
            "نوع_القرار": "",
            "تكلفة_القرار": 0,
            "message": (
                "خدماتنا حاليًا تدعم تحليل قرارات "
                "التوظيف، إطلاق المنتجات، افتتاح الفروع، "
                "شراء المعدات، الحملات التسويقية، "
                "التوسع في الأسواق، وتطوير الأنظمة "
                "والحلول التقنية. "
                "ويجري العمل على دعم أنواع إضافية "
                "ضمن مراحل توسع البرنامج مستقبلًا."
            ),
        }

    cost = extract_cost(text)

    if cost <= 0:
        return {
            "status": "missing_cost",
            "نوع_القرار": normalized_decision,
            "تكلفة_القرار": 0,
            "message": (
                "تم التعرف على نوع القرار، لكن لم يتم "
                "العثور على تكلفة إجمالية واضحة. "
                "يرجى إعادة كتابة القرار مع تحديد "
                "التكلفة الإجمالية، ثم إعادة التحليل."
            ),
        }

    return {
        "status": "ok",
        "نوع_القرار": normalized_decision,
        "تكلفة_القرار": cost,
        "message": "",
    }

def fallback_explanation(
    risk,
    metrics=None,
    features=None,
    shap=None,
):

    metrics = metrics or {}
    features = features or {}
    shap = shap or {}

    if risk == "منخفض":
        return {
            "message": (
                "القرار منخفض الخطورة وفق تقييم نموذج "
                "CatBoost وبيانات الشركة الحالية."
            )
        }

    cost = float(
        metrics.get(
            "تكلفة_القرار",
            features.get(
                "تكلفة_القرار",
                0,
            ),
        ) or 0
    )

    cashflow = float(
        metrics.get(
            "التدفق_النقدي",
            features.get(
                "التدفق_النقدي",
                0,
            ),
        ) or 0
    )

    profit = float(
        metrics.get(
            "صافي_الربح",
            features.get(
                "صافي_الربح",
                0,
            ),
        ) or 0
    )

    debt_ratio = metrics.get(
        "نسبة_الدين_للأصول_%",
        features.get(
            "نسبة_الدين_للأصول_%",
        ),
    )

    cost_to_cashflow = metrics.get(
        "نسبة_التكلفة_إلى_التدفق_النقدي_%"
    )

    cost_to_profit = metrics.get(
        "نسبة_التكلفة_إلى_صافي_الربح_%"
    )

    remaining_cash = metrics.get(
        "الفائض_أو_العجز_بعد_التكلفة"
    )

    cash_covers_cost = metrics.get(
        "هل_التدفق_النقدي_يغطي_التكلفة"
    )

    reasons = []


    if (
        cost_to_cashflow is not None
        and remaining_cash is not None
    ):
        if cash_covers_cost is True:
            reasons.append(
                (
                    f"تبلغ تكلفة القرار {cost:,.0f} ريال، "
                    f"وتمثل {cost_to_cashflow:.1f}% من "
                    f"التدفق النقدي البالغ {cashflow:,.0f} ريال. "
                    f"وبعد تغطية التكلفة يتبقى "
                    f"{remaining_cash:,.0f} ريال من السيولة."
                )
            )

        elif cash_covers_cost is False:
            reasons.append(
                (
                    f"تبلغ تكلفة القرار {cost:,.0f} ريال، "
                    f"بينما يبلغ التدفق النقدي "
                    f"{cashflow:,.0f} ريال، وينتج عن ذلك "
                    f"عجز قدره {abs(remaining_cash):,.0f} ريال."
                )
            )


    if debt_ratio is not None:
        reasons.append(
            (
                f"تبلغ نسبة الدين إلى الأصول "
                f"{float(debt_ratio):.1f}%، لذلك يجب مراعاة "
                f"الالتزامات الحالية عند تخصيص جزء كبير "
                f"من السيولة للقرار."
            )
        )

    elif cost_to_profit is not None:
        reasons.append(
            (
                f"تمثل تكلفة القرار "
                f"{float(cost_to_profit):.1f}% من صافي الربح "
                f"البالغ {profit:,.0f} ريال، ما يوضح أن القرار "
                f"ذو حجم مالي ملموس مقارنة بأرباح الشركة."
            )
        )


    if shap:
        sorted_shap = sorted(
            shap.items(),
            key=lambda item: abs(
                float(item[1])
            ),
            reverse=True,
        )

        if sorted_shap:
            feature, shap_value = sorted_shap[0]

            feature_name = FEATURE_LABELS.get(
                feature,
                feature,
            )

            if float(shap_value) > 0:
                direction = (
                    "دفع تنبؤ النموذج نحو مستوى خطورة أعلى"
                )
            else:
                direction = (
                    "دفع تنبؤ النموذج نحو مستوى خطورة أقل"
                )

            reasons.append(
                (
                    f"أظهر تحليل SHAP أن عامل "
                    f"{feature_name} كان من أكثر العوامل "
                    f"تأثيرًا، وقد {direction}."
                )
            )


    if not reasons:
        reasons.append(
            (
                "يعكس مستوى الخطورة نتيجة مشتركة لتكلفة "
                "القرار ووضع السيولة والالتزامات المالية "
                "الحالية للشركة."
            )
        )

    return {
        "message": (
            "صنف نموذج CatBoost القرار ضمن مستوى "
            f"خطورة {risk} بناءً على بيانات الشركة "
            "وحجم القرار."
        ),

        "reasons": reasons[:3],

        "recommendation": (
            "يُنصح بتخفيض تكلفة القرار ومقارنة عروض "
            "متعددة، مع الحفاظ على رصيد نقدي كافٍ "
            "للالتزامات التشغيلية الحالية."
        ),

        "alternative_decision": "",
    }
def clean_reason_text(text):
    if not isinstance(text, str):
        return text

    return (
        text.replace("*", "")
        .replace("•", "")
        .replace("-", "")
        .strip()
    )


def clean_explanation(explanation):
    if not isinstance(explanation, dict):
        return {}

    if "message" in explanation:
        explanation["message"] = clean_reason_text(
            explanation["message"]
        )

    if "reasons" in explanation:
        explanation["reasons"] = [
            clean_reason_text(reason)
            for reason in explanation["reasons"]
        ]

    if "recommendation" in explanation:
        explanation["recommendation"] = clean_reason_text(
            explanation["recommendation"]
        )

    if "alternative_decision" in explanation:
        explanation["alternative_decision"] = clean_reason_text(
            explanation["alternative_decision"]
        )



    explanation.pop("alternative_risk", None)

    return explanation


def prepare_model_input(decision_text, decision_cost):

    normalized_decision = normalize_decision(decision_text)

    try:
        decision_cost = float(decision_cost)
    except (TypeError, ValueError):
        decision_cost = 0

    features = COMPANY_DATA.copy()
    features["نوع_القرار"] = normalized_decision
    features["تكلفة_القرار"] = decision_cost

    display_features = features.copy()

    encoded_features = features.copy()

    encoded_features["نوع_القرار"] = decision_encoder.transform(
        [normalized_decision]
    )[0]
    print("="*50)
    print("Display Features")

    print(display_features)
    input_data = pd.DataFrame([encoded_features])
    input_data = input_data[FEATURE_ORDER]

    return input_data, display_features, normalized_decision


def predict_with_catboost(decision_text, decision_cost):

    input_data, display_features, normalized_decision = (
        prepare_model_input(
            decision_text=decision_text,
            decision_cost=decision_cost,
        )
    )

    prediction = model.predict(input_data)[0]


    if hasattr(prediction, "__len__") and not isinstance(
        prediction,
        (str, bytes),
    ):
        prediction = prediction[0]

    prediction_number = int(prediction)

    risk = RISK_MAPPING.get(
        prediction_number,
        "غير معروف",
    )

    return {
        "risk": risk,
        "prediction": prediction_number,
        "input_data": input_data,
        "display_features": display_features,
        "decision_text": normalized_decision,
        "decision_cost": decision_cost,
    }


def calculate_shap(input_data, prediction_number):

    shap_result = explainer(input_data)
    shap_values = shap_result.values

    if len(shap_values.shape) == 3:
        shap_values = shap_values[0][:, prediction_number]
    else:
        shap_values = shap_values[0]

    shap_importance = {}

    for feature, value in zip(input_data.columns, shap_values):
        shap_importance[feature] = float(value)

    top_shap = sorted(
        shap_importance.items(),
        key=lambda item: abs(item[1]),
        reverse=True,
    )[:5]

    shap_chart = [
        {
            "feature": FEATURE_LABELS.get(feature, feature),
            "value": round(value, 4),
        }
        for feature, value in top_shap
    ]

    return shap_importance, shap_chart

def extract_decision_using_gemini(text):

    try:
        result = analyze_decision(text)

        if not isinstance(result, dict):
            raise ValueError(
                "Gemini response is not a dictionary"
            )

        status = result.get("status", "ok")


        if status != "ok":
            return {
                "status": status,
                "نوع_القرار": result.get(
                    "نوع_القرار",
                    "",
                ),
                "تكلفة_القرار": 0,
                "message": result.get(
                    "message",
                    "",
                ),
            }

        gemini_decision = result.get(
            "نوع_القرار",
            "",
        )

        normalized_decision = normalize_decision(
            gemini_decision
        )

        if normalized_decision is None:
            return {
                "status": "unsupported",
                "نوع_القرار": "",
                "تكلفة_القرار": 0,
                "message": (
                    "خدماتنا حاليًا تدعم تحليل قرارات: "
                    "التوظيف، إطلاق منتج جديد، افتتاح فرع جديد، "
                    "شراء المعدات، الحملات التسويقية، "
                    "التوسع أو الدخول في سوق جديد، "
                    "وتطوير الأنظمة أو الحلول التقنية. "
                    "ويجري العمل على دعم أنواع إضافية مستقبلًا."
                ),
            }

        gemini_cost = result.get(
            "تكلفة_القرار",
            0,
        )

        validated_cost = reconcile_extracted_cost(
            text=text,
            gemini_cost=gemini_cost,
        )

        if validated_cost <= 0:
            return {
                "status": "missing_cost",
                "نوع_القرار": normalized_decision,
                "تكلفة_القرار": 0,
                "message": (
                    "لم يتم العثور على تكلفة واضحة للقرار. "
                    "يرجى إعادة كتابة القرار مع تحديد "
                    "التكلفة الإجمالية بوضوح، ثم إعادة التحليل."
                ),
            }

        return {
            "status": "ok",
            "نوع_القرار": normalized_decision,
            "تكلفة_القرار": validated_cost,
            "message": "",
        }

    except Exception:
        logger.exception(
            "Gemini extraction failed; using safe fallback"
        )


        return fallback_extract_decision(text)
def evaluate_alternative_decision(alternative_text):

    if not alternative_text:
        return {
            "decision": "",
            "decision_type": "",
            "decision_cost": 0,
            "risk": "",
        }

    alternative_features = extract_decision_using_gemini(
        alternative_text
    )

    alternative_type = alternative_features.get(
        "نوع_القرار",
        "",
    )

    alternative_cost = alternative_features.get(
        "تكلفة_القرار",
        0,
    )

    alternative_result = predict_with_catboost(
        decision_text=alternative_type,
        decision_cost=alternative_cost,
    )

    return {
        "decision": alternative_text,
        "decision_type": alternative_result["decision_text"],
        "decision_cost": alternative_cost,
        "risk": alternative_result["risk"],
    }
def build_fallback_alternative(decision_text, decision_cost):

    try:
        original_cost = float(decision_cost)
    except (TypeError, ValueError):
        original_cost = 0

    if original_cost > 0:
        safer_cost = max(
            int(original_cost * 0.20),
            1000
        )
    else:
        safer_cost = 1000

    return (
        f"{decision_text} بتكلفة مخفضة قدرها "
        f"{safer_cost} ريال"
    )
def find_low_risk_alternative(
    decision_type,
    original_cost,
):

    try:
        original_cost = float(original_cost)

    except (TypeError, ValueError):
        return None

    if original_cost <= 0:
        return None

    low_risk_candidates = []



    ratios = [
        ratio / 100
        for ratio in range(99, 0, -1)
    ]

    for ratio in ratios:

        candidate_cost = max(
            int(original_cost * ratio),
            1000,
        )

        result = predict_with_catboost(
            decision_text=decision_type,
            decision_cost=candidate_cost,
        )

        if DEBUG_AI_PIPELINE:
            logger.info(
                (
                    "Alternative search | "
                    "ratio=%s | "
                    "cost=%s | "
                    "risk=%s"
                ),
                ratio,
                candidate_cost,
                result["risk"],
            )

        if result["risk"] == "منخفض":

            low_risk_candidates.append(
                {
                    "decision": (
                        f"{decision_type} بتكلفة "
                        f"{candidate_cost} ريال"
                    ),
                    "decision_type": result[
                        "decision_text"
                    ],
                    "decision_cost": candidate_cost,
                    "risk": result["risk"],
                }
            )

    if not low_risk_candidates:
        return None



    return max(
        low_risk_candidates,
        key=lambda item: item["decision_cost"],
    )

def predict_risk(request):

    if request.method == "GET":
        return render(
            request,
            "ml_app/decision.html",
            {
                "active_page": "decision",
            },
        )

    text = request.POST.get(
        "text",
        "",
    ).strip()

    if not text:
        return JsonResponse(
            {
                "error": "لم يتم إدخال قرار.",
            },
            status=400,
        )



    decision_features = extract_decision_using_gemini(
        text
    )

    extraction_status = decision_features.get(
        "status",
        "ok",
    )


    if extraction_status != "ok":
        return render(
            request,
            "ml_app/decision.html",
            {
                "active_page": "decision",
                "input_error": decision_features.get(
                    "message",
                    "يرجى التحقق من نوع القرار وتكلفته.",
                ),
                "entered_text": text,
            },
        )


    decision_text = decision_features.get(
        "نوع_القرار",
        "",
    )

    decision_cost = decision_features.get(
        "تكلفة_القرار",
        0,
    )

    original_result = predict_with_catboost(
        decision_text=decision_text,
        decision_cost=decision_cost,
    )

    normalized_decision = original_result[
        "decision_text"
    ]

    risk = original_result[
        "risk"
    ]

    prediction_number = original_result[
        "prediction"
    ]

    input_data = original_result[
        "input_data"
    ]

    display_features = original_result[
        "display_features"
    ]



    shap_importance, shap_chart = calculate_shap(
        input_data=input_data,
        prediction_number=prediction_number,
    )



    financial_metrics = build_financial_metrics(
        display_features
    )



    try:
        explanation = analyze_decision(
            text=text,
            risk=risk,
            features=display_features,
            shap=shap_importance,
            derived_metrics=financial_metrics,
        )

    except Exception:
        logger.exception(
            "Gemini explanation failed"
        )

        explanation = fallback_explanation(
            risk=risk,
            metrics=financial_metrics,
            features=display_features,
            shap=shap_importance,
        )

    explanation = clean_explanation(
        explanation
    )

    if DEBUG_AI_PIPELINE:
        logger.info(
            (
                "AI PIPELINE | "
                "user_text=%r | "
                "extracted=%s | "
                "normalized_decision=%s | "
                "risk=%s | "
                "financial_metrics=%s | "
                "gemini_explanation=%s"
            ),
            text,
            decision_features,
            normalized_decision,
            risk,
            financial_metrics,
            explanation,
        )



    alternative_text = str(
        explanation.get(
            "alternative_decision",
            "",
        )
    ).strip()

    if (
        risk in ["متوسط", "مرتفع"]
        and not alternative_text
    ):
        alternative_text = build_fallback_alternative(
            decision_text=normalized_decision,
            decision_cost=decision_cost,
        )

        explanation[
            "alternative_decision"
        ] = alternative_text

    alternative_result = {
        "decision": "",
        "decision_type": "",
        "decision_cost": 0,
        "risk": "",
    }



    if alternative_text:
        try:
            alternative_result = (
                evaluate_alternative_decision(
                    alternative_text
                )
            )

            explanation[
                "alternative_risk"
            ] = alternative_result[
                "risk"
            ]

            explanation[
                "alternative_cost"
            ] = alternative_result[
                "decision_cost"
            ]

            explanation[
                "alternative_type"
            ] = alternative_result[
                "decision_type"
            ]

        except Exception:
            logger.exception(
                "Alternative evaluation failed"
            )

            explanation[
                "alternative_risk"
            ] = "تعذر تقييم القرار البديل"
    if (
        alternative_result["risk"] != "منخفض"
        and risk in ["متوسط", "مرتفع"]
    ):
        safer_alternative = find_low_risk_alternative(
            decision_type=normalized_decision,
            original_cost=decision_cost,
        )

        if safer_alternative:
            alternative_result = safer_alternative

            alternative_text = safer_alternative[
                "decision"
            ]

            explanation[
                "alternative_decision"
            ] = alternative_text

            explanation[
                "alternative_risk"
            ] = safer_alternative["risk"]

            explanation[
                "alternative_cost"
            ] = safer_alternative[
                "decision_cost"
            ]

            explanation[
                "alternative_type"
            ] = safer_alternative[
                "decision_type"
            ]


    DecisionRecord.objects.create(
        user=request.user,
        decision_text=normalized_decision,
        risk_level=risk,
        alternative_decision=alternative_text,
        alternative_risk=explanation.get(
            "alternative_risk",
            "",
        ),
    )



    return render(
        request,
        "ml_app/decision.html",
        {
            "active_page": "decision",
            "entered_text": text,
            "decision": normalized_decision,
            "decision_cost": decision_cost,
            "risk": risk,
            "shap_chart": shap_chart,
            "gemini": explanation,
            "alternative": alternative_result,
            "financial_metrics": financial_metrics,
        },
    )
