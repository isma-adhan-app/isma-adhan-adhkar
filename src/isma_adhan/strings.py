"""All Arabic UI strings in one place."""

APP_NAME = "اسمع أذان وأذكار"
APP_TAGLINE = "أوقات الصلاة والأذان والأذكار"

MENU_FILE = "ملف"
MENU_EXIT = "خروج"
MENU_PLAY = "تشغيل"
MENU_PLAY_ADHAN = "تشغيل الأذان الآن"
MENU_STOP = "إيقاف الصوت"
MENU_TOGGLE_ADHKAR = "تشغيل/إيقاف الأذكار"
MENU_HELP = "مساعدة"
MENU_SHORTCUTS = "اختصارات لوحة المفاتيح"
MENU_ABOUT = "حول البرنامج"

TAB_HOME = "الرئيسية"
TAB_SETTINGS = "الإعدادات"
TAB_SOUNDS = "الأصوات"

LBL_DATE = "التاريخ"
LBL_NEXT_PRAYER = "الصلاة القادمة"
LBL_REMAINING = "الوقت المتبقي"
LBL_PRAYER_TIMES = "مواقيت الصلاة اليوم"
BTN_PLAY_ADHAN = "تشغيل الأذان الآن"
BTN_STOP = "إيقاف الصوت"
LBL_LOG = "آخر التنبيهات"

SET_CITY = "المدينة"
SET_PRE_ADHAN = "تنبيه قبل الأذان"
SET_IQAMA = "فترة الإقامة بعد الأذان (دقائق، صفر للإيقاف)"
SET_ADHKAR_ON = "تشغيل الأذكار الصوتية"
SET_ADHKAR_INTERVAL = "تشغيل ذكر كل (دقائق)"
SET_ADHKAR_QUIET = "إيقاف الأذكار أثناء ساعات الهدوء (من 11 مساءً إلى 5 صباحًا)"
SET_VOLUME = "مستوى الصوت"
SET_ADHAN_SOUND = "صوت الأذان الحالي"
SET_SPEAK = "نطق اسم الصلاة عند الأذان والتنبيهات"
SET_AUTOSTART = "تشغيل البرنامج مع بدء تشغيل ويندوز"
SET_KAHF = "تذكير قراءة سورة الكهف يوم الجمعة"
SET_KAHF_TIME = "وقت تذكير سورة الكهف (ساعة:دقيقة)"
BTN_SAVE = "حفظ الإعدادات"
MSG_SAVED = "تم حفظ الإعدادات"

OPT_OFF = "إيقاف"
OPT_MIN_5 = "٥ دقائق"
OPT_MIN_10 = "١٠ دقائق"
OPT_MIN_15 = "١٥ دقيقة"

SND_ADHAN_LIB = "مكتبة أصوات الأذان"
SND_ADHKAR_LIB = "مكتبة مقاطع الأذكار"
BTN_ADD_ADHAN = "إضافة صوت أذان"
BTN_ADD_ADHKAR = "إضافة مقطع ذكر"
BTN_SET_ADHAN = "تعيين المحدد كصوت الأذان"
BTN_PREVIEW = "استماع"
MSG_ADDED = "تمت إضافة الملف"
MSG_ADHAN_SET = "تم تعيين صوت الأذان"
MSG_NO_ADHAN = "لم يتم اختيار صوت أذان. سيُستخدم تنبيه صوتي مع نطق اسم الصلاة."

TRAY_TOOLTIP = APP_NAME
TRAY_SHOW = "فتح النافذة"
TRAY_PLAY = "تشغيل الأذان"
TRAY_QUIT = "خروج"

SHORTCUTS_HELP = (
    "اختصارات لوحة المفاتيح:\n"
    "Ctrl+A: تشغيل الأذان الآن\n"
    "Ctrl+S: إيقاف الصوت\n"
    "Ctrl+D: تشغيل أو إيقاف الأذكار\n"
    "Ctrl+N: نطق الصلاة القادمة والوقت المتبقي\n"
    "Ctrl+M: إخفاء النافذة إلى منطقة الإشعارات\n"
    "Ctrl+Q: خروج من البرنامج\n"
    "F1: هذه المساعدة\n"
    "التنقل بين كل العناصر يتم بمفتاح Tab."
)

ABOUT_TEXT = (
    f"{APP_NAME}\n"
    "برنامج مجاني لمواقيت الصلاة والأذان والأذكار الصوتية.\n"
    "يحسب المواقيت بدون اتصال بالإنترنت بطريقة الهيئة المصرية العامة للمساحة.\n"
    "الإصدار الأول."
)

# spoken / notification messages
def msg_adhan_now(prayer_ar: str) -> str:
    return f"حان الآن وقت صلاة {prayer_ar}"


def msg_iqama_now(prayer_ar: str) -> str:
    return f"حان الآن وقت إقامة صلاة {prayer_ar}"


def msg_pre_adhan(prayer_ar: str, minutes: int) -> str:
    return f"تبقى {minutes} دقائق على أذان {prayer_ar}"


MSG_KAHF = "تذكير: اليوم الجمعة، لا تنس قراءة سورة الكهف"
MSG_ADHKAR_TOGGLED_ON = "تم تشغيل الأذكار"
MSG_ADHKAR_TOGGLED_OFF = "تم إيقاف الأذكار"
