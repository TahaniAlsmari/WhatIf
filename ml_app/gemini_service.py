import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai




load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "لم يتم العثور على GEMINI_API_KEY داخل ملف .env"
    )

client = genai.Client(
    api_key=GEMINI_API_KEY
)




SUPPORTED_DECISIONS = [
    "توظيف موظفين",
    "إطلاق منتج جديد",
    "افتتاح فرع جديد",
    "شراء معدات",
    "حملة تسويقية",
    "دخول سوق جديد",
    "تطوير نظام تقني",
]


SUPPORTED_DECISIONS_MESSAGE = (
    "خدماتنا حاليًا تدعم تحليل القرارات التالية: "
    "التوظيف، إطلاق منتج جديد، افتتاح فرع جديد، شراء المعدات، "
    "الحملات التسويقية، التوسع أو الدخول في سوق جديد، "
    "وتطوير الأنظمة أو الحلول التقنية. "
    "ويجري العمل على دعم أنواع إضافية من القرارات "
    "ضمن مراحل توسع البرنامج مستقبلًا."
)


MISSING_COST_MESSAGE = (
    "لم يتم العثور على تكلفة واضحة للقرار. "
    "يرجى إعادة كتابة القرار مع تحديد التكلفة الإجمالية بوضوح، "
    "ثم إعادة التحليل. "
    "مثال: توظيف 70 موظفًا بتكلفة إجمالية 900000 ريال سنويًا."
)




def clean_json(text: str) -> dict[str, Any]:

    if not text:
        raise ValueError("Gemini returned an empty response")

    cleaned_text = str(text).strip()

    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text.replace(
            "```json",
            "",
            1,
        )
        cleaned_text = cleaned_text.replace(
            "```JSON",
            "",
            1,
        )
        cleaned_text = cleaned_text.replace(
            "```",
            "",
        )

    start = cleaned_text.find("{")
    end = cleaned_text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError(
            "Gemini response does not contain valid JSON"
        )

    json_text = cleaned_text[start:end + 1]

    try:
        result = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Gemini returned invalid JSON: {json_text}"
        ) from error

    if not isinstance(result, dict):
        raise ValueError(
            "Gemini response must be a JSON object"
        )

    return result




def normalize_cost(value: Any) -> int:

    if value is None:
        return 0

    if isinstance(value, bool):
        return 0

    if isinstance(value, (int, float)):
        return max(int(value), 0)

    value_text = str(value).strip()

    value_text = value_text.replace(",", "")
    value_text = value_text.replace("٬", "")
    value_text = value_text.replace("،", "")
    value_text = value_text.replace("ريال", "")
    value_text = value_text.strip()

    try:
        return max(int(float(value_text)), 0)
    except (TypeError, ValueError):
        return 0




def validate_extraction(
    result: dict[str, Any]
) -> dict[str, Any]:

    status = str(
        result.get("status", "")
    ).strip().lower()

    decision_type = str(
        result.get("نوع_القرار", "")
    ).strip()

    decision_cost = normalize_cost(
        result.get("تكلفة_القرار", 0)
    )


    if (
        status == "unsupported"
        or decision_type not in SUPPORTED_DECISIONS
    ):
        return {
            "status": "unsupported",
            "نوع_القرار": "",
            "تكلفة_القرار": 0,
            "message": SUPPORTED_DECISIONS_MESSAGE,
        }


    if (
        status == "missing_cost"
        or decision_cost <= 0
    ):
        return {
            "status": "missing_cost",
            "نوع_القرار": decision_type,
            "تكلفة_القرار": 0,
            "message": MISSING_COST_MESSAGE,
        }



    return {
        "status": "ok",
        "نوع_القرار": decision_type,
        "تكلفة_القرار": decision_cost,
        "message": "",
    }




def analyze_decision(
    text,
    risk=None,
    features=None,
    shap=None,
    derived_metrics=None,
):



    if risk is None:

        prompt = f"""
أنت مكوّن لاستخراج بيانات قرارات الشركات.

مهمتك ليست تقييم الخطورة ولا تقديم نصائح.

استخرج من نص المستخدم:

1. نوع القرار من التصنيفات المدعومة فقط.
2. التكلفة المالية الفعلية للقرار بالريال.

النص:

{text}

التصنيفات المدعومة فقط:

- توظيف موظفين
- إطلاق منتج جديد
- افتتاح فرع جديد
- شراء معدات
- حملة تسويقية
- دخول سوق جديد
- تطوير نظام تقني

التطبيع الإلزامي:

- "تعيين موظفين" أو "توظيف أشخاص" أو "زيادة الموظفين"
  => "توظيف موظفين"

- "طرح منتج" أو "منتج جديد"
  => "إطلاق منتج جديد"

- "فتح فرع" أو "إنشاء فرع"
  => "افتتاح فرع جديد"

- "شراء أجهزة" أو "شراء آلات" أو "تحديث المعدات"
  => "شراء معدات"

- "إعلان" أو "حملة إعلانية" أو "تسويق"
  => "حملة تسويقية"

- "التوسع في السوق" أو "دخول سوق" أو "التوسع الجغرافي"
  => "دخول سوق جديد"

- "تطوير برنامج" أو "نظام إلكتروني" أو "تطوير التقنية"
  أو "التحول الرقمي"
  => "تطوير نظام تقني"

أعد JSON فقط بهذا الشكل:

{{
    "status": "ok",
    "نوع_القرار": "أحد التصنيفات المدعومة فقط",
    "تكلفة_القرار": 0,
    "message": ""
}}

القواعد الإلزامية للتكلفة:

1. افهم الأرقام المكتوبة بالأرقام أو بالكلمات العربية.

2. حوّل الكلمات العددية إلى رقم كامل، ومن أمثلتها:

- "ثلاثة ملايين" = 3000000
- "ثلاث مليون" = 3000000
- "مليون ونصف" = 1500000
- "مليون وخمسمائة ألف" = 1500000
- "تسعمائة ألف" = 900000
- "مئتان وخمسون ألفًا" = 250000
- "خمسة وأربعون ألف" = 45000
- "تسعة آلاف شهريًا" = 9000

3. افهم أيضًا:

- ألف = 1000
- مليون = 1000000
- مليار = 1000000000
- نصف مليون = 500000
- ربع مليون = 250000

4. التكلفة هي المبلغ المرتبط بكلمات مالية مثل:

- تكلفة
- بتكلفة
- إجمالي التكلفة
- بميزانية
- ميزانية
- بقيمة
- بمبلغ
- راتب إجمالي
- رواتب سنوية
- رواتب شهرية
- تكلفة شهرية
- تكلفة سنوية
- استثمار بقيمة
- ريال

5. لا تعتبر الأرقام التالية تكلفة:

- عدد الموظفين.
- عدد الأجهزة.
- عدد الفروع.
- عدد المنتجات.
- عدد السنوات أو الأشهر.
- النسب المئوية.
- رقم الفرع.
- كمية المعدات.

مثال:

"نريد توظيف 6 موظفين"

الرقم 6 عدد موظفين وليس تكلفة.

الناتج:

{{
    "status": "missing_cost",
    "نوع_القرار": "توظيف موظفين",
    "تكلفة_القرار": 0,
    "message": "يرجى كتابة التكلفة الإجمالية أو الشهرية أو السنوية لتوظيف الموظفين."
}}

مثال:

"نريد توظيف 6 موظفين بتكلفة ثلاثة ملايين ريال سنويًا"

الناتج:

{{
    "status": "ok",
    "نوع_القرار": "توظيف موظفين",
    "تكلفة_القرار": 3000000,
    "message": ""
}}

مثال:

"شراء 10 أجهزة بمبلغ مئتين وخمسين ألف ريال"

الناتج:

{{
    "status": "ok",
    "نوع_القرار": "شراء معدات",
    "تكلفة_القرار": 250000,
    "message": ""
}}

مثال:

"نريد توظيف 6 موظفين يحصل كل موظف على 9000 ريال شهريًا"

هذا النص لا يحتوي على إجمالي تكلفة القرار بشكل صريح.
لا تضرب العدد في الراتب من نفسك.

الناتج:

{{
    "status": "missing_cost",
    "نوع_القرار": "توظيف موظفين",
    "تكلفة_القرار": 0,
    "message": "يرجى كتابة إجمالي تكلفة التوظيف الشهرية أو السنوية بوضوح."
}}

إذا كان القرار خارج التصنيفات المدعومة، مثل:

- الحصول على قرض.
- الاندماج.
- الاستحواذ.
- إغلاق فرع.
- توزيع أرباح.
- شراء مصنع.
- منح تمويل.
- سداد ديون.

أعد:

{{
    "status": "unsupported",
    "نوع_القرار": "",
    "تكلفة_القرار": 0,
    "message": "هذا النوع من القرارات غير مدعوم حاليًا. النظام مدرب حاليًا على: توظيف موظفين، إطلاق منتج جديد، افتتاح فرع جديد، شراء معدات، حملة تسويقية، التوسع أو الدخول في سوق جديد، وتطوير نظام تقني. سيتم دعم أنواع إضافية من القرارات قريبًا."
}}

إذا كان نوع القرار مدعومًا لكن لا توجد تكلفة مالية إجمالية واضحة:

{{
    "status": "missing_cost",
    "نوع_القرار": "التصنيف المدعوم",
    "تكلفة_القرار": 0,
    "message": "يرجى كتابة تكلفة القرار بوضوح حتى يتمكن النظام من تحليله."
}}

ممنوع:

- اختيار أقرب تصنيف لقرار غير مدعوم.
- اختراع تكلفة.
- استخدام عدد الموظفين باعتباره تكلفة.
- استخدام عدد المعدات باعتباره تكلفة.
- حساب إجمالي التكلفة من الراتب وعدد الموظفين.
- إضافة تصنيف غير موجود في القائمة.
- كتابة شرح خارج JSON.
- استخدام Markdown.

أعد JSON صالحًا فقط.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        extracted_result = clean_json(
            response.text
        )

        return validate_extraction(
            extracted_result
        )



    features_json = json.dumps(
        features or {},
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    shap_json = json.dumps(
        shap or {},
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    metrics_json = json.dumps(
        derived_metrics or {},
        ensure_ascii=False,
        indent=2,
        default=str,
    )



    prompt = f"""
أنت محلل مالي متخصص في تفسير نتائج نماذج تقييم المخاطر.

لا تحدد مستوى الخطورة ولا تغيره.
المستوى تم تحديده بواسطة CatBoost.

القرار:
{text}

مستوى الخطورة:
{risk}

بيانات الشركة والقرار:
{features_json}

حقائق مالية محسوبة مسبقًا بواسطة Python:
{metrics_json}

قيم SHAP:
{shap_json}

قواعد إلزامية:

1. لا تغير مستوى الخطورة.

2. لا تخترع أرقامًا أو التزامات أو أرباحًا مستقبلية.

3. لا تعِد حساب الأرقام المالية من نفسك.

4. استخدم الحقائق المحسوبة مسبقًا كما هي.

5. استخدم SHAP لتحديد العوامل المؤثرة:
   - القيمة الموجبة دفعت التنبؤ نحو خطورة أعلى.
   - القيمة السالبة دفعت التنبؤ نحو خطورة أقل.
   - قيمة SHAP ليست نسبة مئوية.

6. لا تقل إن القرار سيزيد الديون إلا إذا كان التمويل بالدين
   مذكورًا صراحة.

7. لا تخلط بين صافي الربح والتدفق النقدي.

8. استخدم عبارات احتمالية مثل:
   - قد يضغط على السيولة.
   - يحتاج إلى مراجعة.
   - قد يؤثر على المرونة المالية.

9. إذا كانت الخطورة متوسطة أو مرتفعة:
   - اكتب ثلاثة أسباب مختلفة.
   - اربط الأسباب بالأرقام والحقائق وSHAP.
   - اقترح قرارًا بديلًا واحدًا من النوع نفسه.
   - اجعل تكلفة البديل أقل من تكلفة القرار الأصلي.
   - اكتب التكلفة بوضوح داخل القرار البديل.
   - لا تحدد خطورة البديل.
   - لا تكتب alternative_risk.

10. إذا كانت الخطورة منخفضة:
    اكتب رسالة قصيرة تؤكد أن النتيجة منخفضة وفق CatBoost
    مع ذكر حقيقة مالية داعمة واحدة فقط.

إذا كانت الخطورة منخفضة أعد:

{{
    "message": "رسالة قصيرة مبنية على حقيقة مالية موجودة"
}}

إذا كانت الخطورة متوسطة أو مرتفعة أعد:

{{
    "message": "شرح مختصر لمعنى النتيجة",

    "reasons": [
        "سبب رقمي متعلق بالتكلفة والتدفق النقدي",
        "سبب رقمي متعلق بعامل مالي مختلف",
        "سبب يشرح اتجاه أحد أهم عوامل SHAP"
    ],

    "recommendation": "توصية عملية ومحددة",

    "alternative_decision": "قرار بديل من النوع نفسه بتكلفة رقمية واضحة بالريال"
}}

قواعد الإخراج:

- JSON صالح فقط.
- لا تستخدم Markdown.
- لا تكتب قبل JSON أو بعده.
- لا تضف مفاتيح أخرى.
- استخدم علامات اقتباس مزدوجة.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return clean_json(
        response.text
    )
