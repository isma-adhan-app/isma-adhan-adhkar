"""UI strings in Arabic, English and French.

S.<NAME> resolves in the current language (module-level __getattr__), falling
back to Arabic when a translation is missing. Language is chosen at startup
from the settings (or Windows display language on first run) via
set_language(). Adding a language = adding one more table with the same keys.
"""
from __future__ import annotations

_LANG = "ar"

LANGUAGES = {"ar": "العربية", "en": "English", "fr": "Français"}


def set_language(code: str) -> None:
    global _LANG
    if code in LANGUAGES:
        _LANG = code


def current_language() -> str:
    return _LANG


def language_from_langid(langid: int) -> str:
    """Map a Windows LANGID (GetUserDefaultUILanguage) to a supported code."""
    primary = langid & 0x3FF
    return {0x01: "ar", 0x0C: "fr", 0x09: "en"}.get(primary, "ar")


def tr(name: str) -> str:
    table = _TABLES.get(_LANG, _AR)
    return table.get(name, _AR[name])


def __getattr__(name: str):
    # PEP 562: S.APP_NAME etc. resolve dynamically in the current language.
    if name.isupper():
        try:
            return tr(name)
        except KeyError:
            raise AttributeError(name) from None
    raise AttributeError(name)


_AR = {
    "APP_NAME": "اسمع أذان وأذكار",
    "APP_TAGLINE": "أوقات الصلاة والأذان والأذكار",
    "MENU_FILE": "ملف",
    "MENU_EXIT": "خروج",
    "MENU_HIDE": "إخفاء النافذة",
    "MENU_PLAY": "تشغيل",
    "MENU_PLAY_ADHAN": "تشغيل الأذان الآن",
    "MENU_STOP": "إيقاف الصوت",
    "MENU_TOGGLE_ADHKAR": "تشغيل/إيقاف الأذكار",
    "MENU_HELP": "مساعدة",
    "MENU_SHORTCUTS": "اختصارات لوحة المفاتيح",
    "MENU_ABOUT": "حول البرنامج",
    "TAB_HOME": "الرئيسية",
    "TAB_SETTINGS": "الإعدادات",
    "TAB_SOUNDS": "الأصوات",
    "LBL_DATE": "التاريخ",
    "LBL_DATE_GREG_HIJRI": "التاريخ الميلادي والهجري",
    "OPT_RANDOM": "عشوائي",
    "LBL_NEXT_PRAYER": "الصلاة القادمة",
    "LBL_REMAINING": "الوقت المتبقي",
    "LBL_PRAYER_TIMES": "مواقيت الصلاة اليوم",
    "LBL_CONVERT": "تحويل تاريخ (ميلادي إلى هجري أو العكس)",
    "CONVERT_FIELD_NAME": "أدخل تاريخاً مثل 21/11/2026 ميلادي أو 1/9/1447 هجري",
    "CONVERT_RESULT_NAME": "نتيجة التحويل",
    "BTN_CONVERT": "تحويل",
    "BTN_EXPORT_MONTH": "تصدير مواقيت الشهر",
    "MSG_CONVERT_BAD": "لم أفهم التاريخ. اكتبه مثل 21/11/2026 للميلادي أو 1/9/1447 هجري.",
    "MSG_EXPORT_DONE": "تم تصدير مواقيت الشهر إلى مجلد المستندات: {path}",
    "MSG_EXPORT_FAIL": "تعذر تصدير ملف المواقيت.",
    "BTN_PLAY_ADHAN": "تشغيل الأذان الآن",
    "BTN_STOP": "إيقاف الصوت",
    "LBL_LOG": "آخر التنبيهات",
    "SET_LANGUAGE": "اللغة / Language / Langue",
    "OPT_LANG_AUTO": "تلقائي (لغة ويندوز)",
    "MSG_LANGUAGE_RESTART": "تم حفظ اللغة. أعد تشغيل البرنامج لتطبيقها على كل شيء.",
    "SET_CITY": "المدينة",
    "SET_PRE_ADHAN": "تنبيه قبل الأذان",
    "SET_IQAMA": "فترة الإقامة بعد الأذان (دقائق، صفر للإيقاف)",
    "SET_ADHKAR_ON": "تشغيل الأذكار الصوتية",
    "SET_ADHKAR_INTERVAL": "تشغيل ذكر كل (دقائق)",
    "SET_ADHKAR_QUIET": "إيقاف الأذكار أثناء ساعات الهدوء (من 11 مساءً إلى 5 صباحًا)",
    "SET_VOLUME": "مستوى الصوت",
    "SET_ADHAN_SOUND": "صوت الأذان الحالي",
    "SET_SPEAK": "نطق اسم الصلاة عند الأذان والتنبيهات",
    "SET_AUTOSTART": "تشغيل البرنامج مع بدء تشغيل ويندوز",
    "SET_KAHF": "تذكير قراءة سورة الكهف يوم الجمعة",
    "SET_KAHF_TIME": "وقت تذكير سورة الكهف (ساعة:دقيقة)",
    "BTN_SAVE": "حفظ الإعدادات",
    "MSG_SAVED": "تم حفظ الإعدادات",
    "OPT_OFF": "إيقاف",
    "OPT_MIN_5": "٥ دقائق",
    "OPT_MIN_10": "١٠ دقائق",
    "OPT_MIN_15": "١٥ دقيقة",
    "SND_ADHAN_LIB": "مكتبة أصوات الأذان",
    "SND_ADHKAR_LIB": "مكتبة مقاطع الأذكار",
    "BTN_ADD_ADHAN": "إضافة صوت أذان",
    "BTN_ADD_ADHKAR": "إضافة مقطع ذكر",
    "BTN_SET_ADHAN": "تعيين المحدد كصوت الأذان",
    "BTN_PREVIEW": "استماع",
    "MSG_ADDED": "تمت إضافة الملف",
    "MSG_ADHAN_SET": "تم تعيين صوت الأذان",
    "MSG_NO_ADHAN": "لم يتم اختيار صوت أذان. سيُستخدم تنبيه صوتي مع نطق اسم الصلاة.",
    "TRAY_SHOW": "فتح النافذة",
    "TRAY_PLAY": "تشغيل الأذان",
    "TRAY_QUIT": "خروج",
    "SHORTCUTS_HELP": (
        "اختصارات لوحة المفاتيح:\n"
        "Ctrl+A: تشغيل الأذان الآن\n"
        "Ctrl+S: إيقاف الصوت\n"
        "Ctrl+D: تشغيل أو إيقاف الأذكار\n"
        "Ctrl+N: نطق الصلاة القادمة والوقت المتبقي\n"
        "Ctrl+M: إخفاء النافذة إلى منطقة الإشعارات\n"
        "Ctrl+Q: خروج من البرنامج\n"
        "F1: هذه المساعدة\n"
        "التنقل بين كل العناصر يتم بمفتاح Tab."
    ),
    "ABOUT_TEXT": (
        "برنامج مجاني لمواقيت الصلاة والأذان والأذكار الصوتية.\n"
        "يحسب المواقيت بدون اتصال بالإنترنت بطريقة الهيئة المصرية العامة للمساحة.\n"
        "الإصدار {version}."
    ),
    "MSG_KAHF": "تذكير: اليوم الجمعة، لا تنس قراءة سورة الكهف",
    "MSG_ADHKAR_TOGGLED_ON": "تم تشغيل الأذكار",
    "MSG_ADHKAR_TOGGLED_OFF": "تم إيقاف الأذكار",
    "MSG_ADHAN_NOW": "حان الآن وقت صلاة {prayer}",
    "MSG_IQAMA_NOW": "حان الآن وقت إقامة صلاة {prayer}",
    "MSG_PRE_ADHAN": "تبقى {minutes} دقائق على أذان {prayer}",
    "MSG_POST_ADHKAR": "أذكار ما بعد صلاة {prayer}",
    "MSG_MINUTES_COUNT": "{n} دقيقة",
    "MSG_REMAINING_HM": "الوقت المتبقي {h} ساعات و{m} دقيقة.",
    "MSG_NEXT_PRAYER_AT": "الصلاة القادمة صلاة {name} الساعة {time}.",
    "MSG_NEXT_PRAYER_SHORT": "{name} الساعة {time}",
    "MSG_AUDIO_FAIL": "تعذر تشغيل الصوت: {name}",
    "MSG_ADHKAR_EMPTY": "لا توجد مقاطع أذكار في المكتبة بعد. أضف مقاطع من تبويب الأصوات.",
    "MSG_STOPPED": "تم إيقاف الصوت",
    "MSG_BAD_FILE_TYPE": "نوع ملف غير مدعوم: {name}",
    "MSG_CHOOSE_AUDIO": "اختر ملفات صوتية",
    "WILDCARD_AUDIO": "ملفات صوتية (*.mp3;*.wav;*.ogg)|*.mp3;*.wav;*.ogg",
    "MSG_BISMILLAH_LINE": "بسم الله الرحمن الرحيم - {voice}",
    "MSG_LAUNCH_FULL": (
        "برنامج {app} يعمل الآن. "
        "اليوم {weekday}، {gregorian}، الموافق {hijri}. "
        "{notable}"
        "الصلاة القادمة صلاة {name} الساعة {time}."
    ),
    "MSG_LAUNCH_SHORT": "برنامج {app} يعمل الآن.",
    "MSG_STILL_RUNNING": "البرنامج ما زال يعمل في الخلفية بجانب الساعة. للخروج: قائمة ملف ثم خروج.",
    "MSG_CRASH_INCOMPLETE": "آخر محاولة تشغيل توقفت قبل اكتمال فتح البرنامج. التفاصيل محفوظة في ملف app.log.",
    "MSG_AUDIO_DEVICE_FAIL": "تعذر تشغيل الصوت على هذا الجهاز. التنبيهات الصوتية لن تعمل حتى يصلح الصوت.",
    "MSG_CRASH_ERROR": "حدث خطأ في البرنامج. التفاصيل محفوظة في ملف app.log داخل مجلد البرنامج في AppData.\n\n{details}",
    "TITLE_CONFIRM_EXIT": "تأكيد الخروج",
    "MSG_CONFIRM_EXIT": "هل تريد الخروج من البرنامج؟ لن تعمل التنبيهات والأذان حتى تفتحه مرة أخرى.",
    "BTN_YES": "نعم",
    "BTN_NO": "لا",
    "SET_COUNTRY": "الدولة",
    "SET_DETECT": "اكتشاف الموقع تلقائيًا",
    "MSG_DETECTED": "تم اكتشاف موقعك تلقائيًا. راجع الدولة والمدينة ثم احفظ.",
    "MSG_DETECT_FAILED": "تعذر اكتشاف الموقع تلقائيًا، اختر الدولة والمدينة يدويًا.",
    "HDR_PRAYER": "الصلاة",
    "HDR_PRE": "تنبيه قبل الأذان (دقائق)",
    "HDR_IQAMA": "الإقامة بعد (دقائق)",
    "HDR_POST": "أذكار بعد الصلاة (دقائق)",
    "SND_PER_PRAYER": "صوت الأذان لكل صلاة",
    "OPT_DEFAULT": "(نفس الافتراضي)",
    "OPT_RANDOM_ADHAN": "عشوائي - مؤذن مختلف في كل صلاة (المقاطع المدمجة وملفاتي)",
    "OPT_NONE": "(لا شيء)",
    "SND_ALL_PRAYERS": "كل الصلوات (الافتراضي)",
    "MSG_LOCATION_SAVED": "تم حفظ الموقع",
    "SET_BISMILLAH_VOICE": "صوت البسملة عند التشغيل",
    "SND_ALERT_LIB_PRE": "مكتبة أصوات التنبيه قبل الأذان",
    "SND_ALERT_LIB_IQAMA": "مكتبة أصوات الإقامة",
    "SND_ALERT_PER_PRE": "صوت التنبيه قبل الأذان لكل صلاة",
    "SND_ALERT_PER_IQAMA": "صوت الإقامة لكل صلاة",
    "BTN_ADD_ALERT": "إضافة صوت تنبيه",
    "OPT_RANDOM_ALERT": "عشوائي - صوت مختلف كل مرة (الأصوات المدمجة وملفاتي)",
    "MSG_ALERT_SET": "تم تعيين صوت التنبيه",
    "SND_POST_ADHKAR_PER_PRAYER": "صوت الأذكار بعد الصلاة لكل صلاة",
    "SET_UPDATES": "التحديثات",
    "BTN_CHECK_UPDATE": "البحث عن تحديث",
    "BTN_UPDATE_NOW": "تثبيت التحديث الآن",
    "MSG_UPDATE_CHECKING": "يجري البحث عن تحديث...",
    "MSG_UPDATE_NONE": "لا يوجد تحديث جديد. لديك أحدث إصدار.",
    "MSG_UPDATE_AVAILABLE": "يتوفر إصدار جديد: {version}. انتقل إلى الإعدادات ثم زر تثبيت التحديث الآن.",
    "MSG_UPDATE_DOWNLOADING": "يجري تنزيل التحديث...",
    "MSG_UPDATE_STARTING": "اكتمل التنزيل. سيبدأ المثبت الآن ويكمّل التحديث بنفسه.",
    "MSG_UPDATE_FAIL": "تعذر البحث عن تحديث. تحقق من اتصال الإنترنت.",
    "MSG_UPDATE_BAD_HASH": "فشل التحقق من سلامة ملف التحديث. لم يتم تثبيت أي شيء.",
    "MSG_CONVERT_G2H": "{d} {gmonth} {y} م يوافق {hd} {hmonth} {hy} هـ.",
    "MSG_CONVERT_H2G": "{d} {hmonth} {y} هـ يوافق {gd} {gmonth} {gy} م.",
    "MSG_EXPORT_HEADER": "مواقيت الصلاة لشهر {month} {year} م - {city}، {country}",
    "MSG_EXPORT_METHOD": "طريقة الحساب: {method}",
    "EXPORT_FILE_PREFIX": "مواقيت",
    "MSG_DATE_LINE": "{weekday}، {gregorian}  /  {hijri}",
    "MSG_DHIKR_LINE": "ذكر: {label}",
}

_EN = {
    "APP_NAME": "Isma Adhan & Adhkar",
    "APP_TAGLINE": "Prayer times, adhan and adhkar",
    "MENU_FILE": "File",
    "MENU_EXIT": "Exit",
    "MENU_HIDE": "Hide window",
    "MENU_PLAY": "Play",
    "MENU_PLAY_ADHAN": "Play adhan now",
    "MENU_STOP": "Stop sound",
    "MENU_TOGGLE_ADHKAR": "Toggle adhkar",
    "MENU_HELP": "Help",
    "MENU_SHORTCUTS": "Keyboard shortcuts",
    "MENU_ABOUT": "About",
    "TAB_HOME": "Home",
    "TAB_SETTINGS": "Settings",
    "TAB_SOUNDS": "Sounds",
    "LBL_DATE": "Date",
    "LBL_DATE_GREG_HIJRI": "Gregorian and Hijri date",
    "OPT_RANDOM": "Random",
    "LBL_NEXT_PRAYER": "Next prayer",
    "LBL_REMAINING": "Time remaining",
    "LBL_PRAYER_TIMES": "Today's prayer times",
    "LBL_CONVERT": "Convert a date (Gregorian to Hijri or back)",
    "CONVERT_FIELD_NAME": "Enter a date like 21/11/2026 Gregorian or 1/9/1447 Hijri",
    "CONVERT_RESULT_NAME": "Conversion result",
    "BTN_CONVERT": "Convert",
    "BTN_EXPORT_MONTH": "Export this month's times",
    "MSG_CONVERT_BAD": "I could not read that date. Write it like 21/11/2026 for Gregorian or 1/9/1447 for Hijri.",
    "MSG_EXPORT_DONE": "This month's prayer times were exported to your Documents folder: {path}",
    "MSG_EXPORT_FAIL": "Could not export the prayer-times file.",
    "BTN_PLAY_ADHAN": "Play adhan now",
    "BTN_STOP": "Stop sound",
    "LBL_LOG": "Recent alerts",
    "SET_LANGUAGE": "Language / اللغة / Langue",
    "OPT_LANG_AUTO": "Automatic (Windows language)",
    "MSG_LANGUAGE_RESTART": "Language saved. Restart the app to apply it everywhere.",
    "SET_CITY": "City",
    "SET_PRE_ADHAN": "Pre-adhan reminder",
    "SET_IQAMA": "Iqama interval after adhan (minutes, 0 to disable)",
    "SET_ADHKAR_ON": "Play spoken adhkar",
    "SET_ADHKAR_INTERVAL": "Play a dhikr every (minutes)",
    "SET_ADHKAR_QUIET": "Pause adhkar during quiet hours (11 PM to 5 AM)",
    "SET_VOLUME": "Volume",
    "SET_ADHAN_SOUND": "Current adhan sound",
    "SET_SPEAK": "Speak the prayer name at adhan and alerts",
    "SET_AUTOSTART": "Start the app with Windows",
    "SET_KAHF": "Friday reminder to read Surat Al-Kahf",
    "SET_KAHF_TIME": "Al-Kahf reminder time (hour:minute)",
    "BTN_SAVE": "Save settings",
    "MSG_SAVED": "Settings saved",
    "OPT_OFF": "Off",
    "OPT_MIN_5": "5 minutes",
    "OPT_MIN_10": "10 minutes",
    "OPT_MIN_15": "15 minutes",
    "SND_ADHAN_LIB": "Adhan sounds library",
    "SND_ADHKAR_LIB": "Adhkar clips library",
    "BTN_ADD_ADHAN": "Add an adhan sound",
    "BTN_ADD_ADHKAR": "Add an adhkar clip",
    "BTN_SET_ADHAN": "Set selected as the adhan sound",
    "BTN_PREVIEW": "Preview",
    "MSG_ADDED": "File added",
    "MSG_ADHAN_SET": "Adhan sound set",
    "MSG_NO_ADHAN": "No adhan sound chosen. A tone alert with the spoken prayer name will be used.",
    "TRAY_SHOW": "Open window",
    "TRAY_PLAY": "Play adhan",
    "TRAY_QUIT": "Exit",
    "SHORTCUTS_HELP": (
        "Keyboard shortcuts:\n"
        "Ctrl+A: play adhan now\n"
        "Ctrl+S: stop sound\n"
        "Ctrl+D: toggle adhkar\n"
        "Ctrl+N: speak the next prayer and time remaining\n"
        "Ctrl+M: hide the window to the notification area\n"
        "Ctrl+Q: exit the app\n"
        "F1: this help\n"
        "Move between all controls with Tab."
    ),
    "ABOUT_TEXT": (
        "A free app for prayer times, adhan and spoken adhkar.\n"
        "Computes times offline using the Egyptian General Survey Authority method.\n"
        "Version {version}."
    ),
    "MSG_KAHF": "Reminder: today is Friday, don't forget to read Surat Al-Kahf",
    "MSG_ADHKAR_TOGGLED_ON": "Adhkar enabled",
    "MSG_ADHKAR_TOGGLED_OFF": "Adhkar disabled",
    "MSG_ADHAN_NOW": "It is now time for {prayer} prayer",
    "MSG_IQAMA_NOW": "It is now time for the iqama of {prayer} prayer",
    "MSG_PRE_ADHAN": "{minutes} minutes left until the adhan of {prayer}",
    "MSG_POST_ADHKAR": "Post-{prayer} adhkar",
    "MSG_MINUTES_COUNT": "{n} minutes",
    "MSG_REMAINING_HM": "Time remaining: {h} hours and {m} minutes.",
    "MSG_NEXT_PRAYER_AT": "Next prayer is {name} at {time}.",
    "MSG_NEXT_PRAYER_SHORT": "{name} at {time}",
    "MSG_AUDIO_FAIL": "Could not play sound: {name}",
    "MSG_ADHKAR_EMPTY": "No adhkar clips in the library yet. Add clips from the Sounds tab.",
    "MSG_STOPPED": "Sound stopped",
    "MSG_BAD_FILE_TYPE": "Unsupported file type: {name}",
    "MSG_CHOOSE_AUDIO": "Choose audio files",
    "WILDCARD_AUDIO": "Audio files (*.mp3;*.wav;*.ogg)|*.mp3;*.wav;*.ogg",
    "MSG_BISMILLAH_LINE": "In the name of Allah, the Most Gracious, the Most Merciful - {voice}",
    "MSG_LAUNCH_FULL": (
        "{app} is now running. "
        "Today is {weekday}, {gregorian}, corresponding to {hijri}. "
        "{notable}"
        "Next prayer is {name} at {time}."
    ),
    "MSG_LAUNCH_SHORT": "{app} is now running.",
    "MSG_STILL_RUNNING": "The app keeps running in the background next to the clock. To exit: File menu, then Exit.",
    "MSG_CRASH_INCOMPLETE": "The last launch attempt stopped before the app finished opening. Details are saved in app.log.",
    "MSG_AUDIO_DEVICE_FAIL": "Sound could not be initialized on this device. Audio alerts will not work until sound is fixed.",
    "MSG_CRASH_ERROR": "An error occurred in the app. Details are saved in app.log inside the app's AppData folder.\n\n{details}",
    "TITLE_CONFIRM_EXIT": "Confirm exit",
    "MSG_CONFIRM_EXIT": "Do you want to exit the app? Alerts and adhan will not run until you open it again.",
    "BTN_YES": "Yes",
    "BTN_NO": "No",
    "SET_COUNTRY": "Country",
    "SET_DETECT": "Detect my location",
    "MSG_DETECTED": "Your location was detected. Review the country and city, then save.",
    "MSG_DETECT_FAILED": "Could not detect the location automatically; choose the country and city manually.",
    "HDR_PRAYER": "Prayer",
    "HDR_PRE": "Pre-adhan reminder (minutes)",
    "HDR_IQAMA": "Iqama after (minutes)",
    "HDR_POST": "Post-prayer adhkar (minutes)",
    "SND_PER_PRAYER": "Adhan sound per prayer",
    "OPT_DEFAULT": "(same as default)",
    "OPT_RANDOM_ADHAN": "Random - a different reciter each prayer (bundled clips and my files)",
    "OPT_NONE": "(none)",
    "SND_ALL_PRAYERS": "All prayers (default)",
    "MSG_LOCATION_SAVED": "Location saved",
    "SET_BISMILLAH_VOICE": "Bismillah voice at startup",
    "SND_ALERT_LIB_PRE": "Pre-adhan alert sounds library",
    "SND_ALERT_LIB_IQAMA": "Iqama sounds library",
    "SND_ALERT_PER_PRE": "Pre-adhan alert sound per prayer",
    "SND_ALERT_PER_IQAMA": "Iqama sound per prayer",
    "BTN_ADD_ALERT": "Add an alert sound",
    "OPT_RANDOM_ALERT": "Random - a different sound each time (bundled sounds and my files)",
    "MSG_ALERT_SET": "Alert sound set",
    "SND_POST_ADHKAR_PER_PRAYER": "Post-prayer adhkar sound per prayer",
    "SET_UPDATES": "Updates",
    "BTN_CHECK_UPDATE": "Check for updates",
    "BTN_UPDATE_NOW": "Install the update now",
    "MSG_UPDATE_CHECKING": "Checking for updates...",
    "MSG_UPDATE_NONE": "No new update. You have the latest version.",
    "MSG_UPDATE_AVAILABLE": "A new version is available: {version}. Go to Settings, then the Install the update now button.",
    "MSG_UPDATE_DOWNLOADING": "Downloading the update...",
    "MSG_UPDATE_STARTING": "Download complete. The installer will start now and finish the update by itself.",
    "MSG_UPDATE_FAIL": "Could not check for updates. Check your internet connection.",
    "MSG_UPDATE_BAD_HASH": "The update file failed its integrity check. Nothing was installed.",
    "MSG_CONVERT_G2H": "{d} {gmonth} {y} AD corresponds to {hd} {hmonth} {hy} AH.",
    "MSG_CONVERT_H2G": "{d} {hmonth} {y} AH corresponds to {gd} {gmonth} {gy} AD.",
    "MSG_EXPORT_HEADER": "Prayer times for {month} {year} - {city}, {country}",
    "MSG_EXPORT_METHOD": "Calculation method: {method}",
    "EXPORT_FILE_PREFIX": "prayer-times",
    "MSG_DATE_LINE": "{weekday}, {gregorian} / {hijri}",
    "MSG_DHIKR_LINE": "Dhikr: {label}",
}

_FR = {
    "APP_NAME": "Isma Adhan & Adhkar",
    "APP_TAGLINE": "Heures de prière, adhan et adhkar",
    "MENU_FILE": "Fichier",
    "MENU_EXIT": "Quitter",
    "MENU_HIDE": "Masquer la fenêtre",
    "MENU_PLAY": "Lecture",
    "MENU_PLAY_ADHAN": "Jouer l'adhan maintenant",
    "MENU_STOP": "Arrêter le son",
    "MENU_TOGGLE_ADHKAR": "Activer/désactiver les adhkar",
    "MENU_HELP": "Aide",
    "MENU_SHORTCUTS": "Raccourcis clavier",
    "MENU_ABOUT": "À propos",
    "TAB_HOME": "Accueil",
    "TAB_SETTINGS": "Paramètres",
    "TAB_SOUNDS": "Sons",
    "LBL_DATE": "Date",
    "LBL_DATE_GREG_HIJRI": "Date grégorienne et hégirienne",
    "OPT_RANDOM": "Aléatoire",
    "LBL_NEXT_PRAYER": "Prochaine prière",
    "LBL_REMAINING": "Temps restant",
    "LBL_PRAYER_TIMES": "Heures de prière d'aujourd'hui",
    "LBL_CONVERT": "Convertir une date (grégorienne vers hégirienne ou inversement)",
    "CONVERT_FIELD_NAME": "Saisissez une date comme 21/11/2026 grégorienne ou 1/9/1447 hégirienne",
    "CONVERT_RESULT_NAME": "Résultat de la conversion",
    "BTN_CONVERT": "Convertir",
    "BTN_EXPORT_MONTH": "Exporter les heures du mois",
    "MSG_CONVERT_BAD": "Je n'ai pas compris la date. Écrivez-la comme 21/11/2026 pour le grégorien ou 1/9/1447 pour l'hégirien.",
    "MSG_EXPORT_DONE": "Les heures de prière du mois ont été exportées vers le dossier Documents : {path}",
    "MSG_EXPORT_FAIL": "Impossible d'exporter le fichier des horaires.",
    "BTN_PLAY_ADHAN": "Jouer l'adhan maintenant",
    "BTN_STOP": "Arrêter le son",
    "LBL_LOG": "Alertes récentes",
    "SET_LANGUAGE": "Langue / اللغة / Language",
    "OPT_LANG_AUTO": "Automatique (langue de Windows)",
    "MSG_LANGUAGE_RESTART": "Langue enregistrée. Redémarrez l'application pour l'appliquer partout.",
    "SET_CITY": "Ville",
    "SET_PRE_ADHAN": "Rappel avant l'adhan",
    "SET_IQAMA": "Délai de l'iqama après l'adhan (minutes, 0 pour désactiver)",
    "SET_ADHKAR_ON": "Jouer les adhkar audio",
    "SET_ADHKAR_INTERVAL": "Jouer un dhikr toutes les (minutes)",
    "SET_ADHKAR_QUIET": "Suspendre les adhkar pendant les heures calmes (de 23 h à 5 h)",
    "SET_VOLUME": "Volume",
    "SET_ADHAN_SOUND": "Son d'adhan actuel",
    "SET_SPEAK": "Annoncer le nom de la prière à l'adhan et aux alertes",
    "SET_AUTOSTART": "Lancer l'application au démarrage de Windows",
    "SET_KAHF": "Rappel de lecture de sourate Al-Kahf le vendredi",
    "SET_KAHF_TIME": "Heure du rappel Al-Kahf (heure:minute)",
    "BTN_SAVE": "Enregistrer les paramètres",
    "MSG_SAVED": "Paramètres enregistrés",
    "OPT_OFF": "Désactivé",
    "OPT_MIN_5": "5 minutes",
    "OPT_MIN_10": "10 minutes",
    "OPT_MIN_15": "15 minutes",
    "SND_ADHAN_LIB": "Bibliothèque des sons d'adhan",
    "SND_ADHKAR_LIB": "Bibliothèque des clips d'adhkar",
    "BTN_ADD_ADHAN": "Ajouter un son d'adhan",
    "BTN_ADD_ADHKAR": "Ajouter un clip de dhikr",
    "BTN_SET_ADHAN": "Définir la sélection comme son d'adhan",
    "BTN_PREVIEW": "Écouter",
    "MSG_ADDED": "Fichier ajouté",
    "MSG_ADHAN_SET": "Son d'adhan défini",
    "MSG_NO_ADHAN": "Aucun son d'adhan choisi. Une alerte sonore avec le nom de la prière annoncé sera utilisée.",
    "TRAY_SHOW": "Ouvrir la fenêtre",
    "TRAY_PLAY": "Jouer l'adhan",
    "TRAY_QUIT": "Quitter",
    "SHORTCUTS_HELP": (
        "Raccourcis clavier :\n"
        "Ctrl+A : jouer l'adhan maintenant\n"
        "Ctrl+S : arrêter le son\n"
        "Ctrl+D : activer/désactiver les adhkar\n"
        "Ctrl+N : annoncer la prochaine prière et le temps restant\n"
        "Ctrl+M : masquer la fenêtre dans la zone de notification\n"
        "Ctrl+Q : quitter l'application\n"
        "F1 : cette aide\n"
        "Naviguez entre tous les contrôles avec Tab."
    ),
    "ABOUT_TEXT": (
        "Application gratuite pour les heures de prière, l'adhan et les adhkar audio.\n"
        "Calcule les horaires hors ligne selon la méthode de l'Autorité générale égyptienne de topographie.\n"
        "Version {version}."
    ),
    "MSG_KAHF": "Rappel : nous sommes vendredi, n'oubliez pas de lire sourate Al-Kahf",
    "MSG_ADHKAR_TOGGLED_ON": "Adhkar activés",
    "MSG_ADHKAR_TOGGLED_OFF": "Adhkar désactivés",
    "MSG_ADHAN_NOW": "C'est maintenant l'heure de la prière de {prayer}",
    "MSG_IQAMA_NOW": "C'est maintenant l'heure de l'iqama de la prière de {prayer}",
    "MSG_PRE_ADHAN": "Il reste {minutes} minutes avant l'adhan de {prayer}",
    "MSG_POST_ADHKAR": "Adhkar après la prière de {prayer}",
    "MSG_MINUTES_COUNT": "{n} minutes",
    "MSG_REMAINING_HM": "Temps restant : {h} heures et {m} minutes.",
    "MSG_NEXT_PRAYER_AT": "La prochaine prière est {name} à {time}.",
    "MSG_NEXT_PRAYER_SHORT": "{name} à {time}",
    "MSG_AUDIO_FAIL": "Impossible de jouer le son : {name}",
    "MSG_ADHKAR_EMPTY": "Aucun clip d'adhkar dans la bibliothèque pour l'instant. Ajoutez des clips depuis l'onglet Sons.",
    "MSG_STOPPED": "Son arrêté",
    "MSG_BAD_FILE_TYPE": "Type de fichier non pris en charge : {name}",
    "MSG_CHOOSE_AUDIO": "Choisir des fichiers audio",
    "WILDCARD_AUDIO": "Fichiers audio (*.mp3;*.wav;*.ogg)|*.mp3;*.wav;*.ogg",
    "MSG_BISMILLAH_LINE": "Au nom d'Allah, le Tout Miséricordieux, le Très Miséricordieux - {voice}",
    "MSG_LAUNCH_FULL": (
        "{app} est en cours d'exécution. "
        "Nous sommes {weekday} {gregorian}, correspondant au {hijri}. "
        "{notable}"
        "La prochaine prière est {name} à {time}."
    ),
    "MSG_LAUNCH_SHORT": "{app} est en cours d'exécution.",
    "MSG_STILL_RUNNING": "L'application continue de fonctionner en arrière-plan près de l'horloge. Pour quitter : menu Fichier, puis Quitter.",
    "MSG_CRASH_INCOMPLETE": "La dernière tentative de lancement s'est interrompue avant l'ouverture complète de l'application. Les détails sont enregistrés dans app.log.",
    "MSG_AUDIO_DEVICE_FAIL": "Le son n'a pas pu être initialisé sur cet appareil. Les alertes audio ne fonctionneront pas tant que le son n'est pas réparé.",
    "MSG_CRASH_ERROR": "Une erreur s'est produite dans l'application. Les détails sont enregistrés dans app.log dans le dossier AppData de l'application.\n\n{details}",
    "TITLE_CONFIRM_EXIT": "Confirmer la fermeture",
    "MSG_CONFIRM_EXIT": "Voulez-vous quitter l'application ? Les alertes et l'adhan ne fonctionneront pas avant sa réouverture.",
    "BTN_YES": "Oui",
    "BTN_NO": "Non",
    "SET_COUNTRY": "Pays",
    "SET_DETECT": "Détecter ma position",
    "MSG_DETECTED": "Votre position a été détectée. Vérifiez le pays et la ville, puis enregistrez.",
    "MSG_DETECT_FAILED": "Impossible de détecter la position automatiquement ; choisissez le pays et la ville manuellement.",
    "HDR_PRAYER": "Prière",
    "HDR_PRE": "Rappel avant l'adhan (minutes)",
    "HDR_IQAMA": "Iqama après (minutes)",
    "HDR_POST": "Adhkar après la prière (minutes)",
    "SND_PER_PRAYER": "Son d'adhan par prière",
    "OPT_DEFAULT": "(comme par défaut)",
    "OPT_RANDOM_ADHAN": "Aléatoire - un récitateur différent à chaque prière (clips intégrés et mes fichiers)",
    "OPT_NONE": "(aucun)",
    "SND_ALL_PRAYERS": "Toutes les prières (par défaut)",
    "MSG_LOCATION_SAVED": "Position enregistrée",
    "SET_BISMILLAH_VOICE": "Voix de la Bismillah au démarrage",
    "SND_ALERT_LIB_PRE": "Bibliothèque des sons d'alerte avant l'adhan",
    "SND_ALERT_LIB_IQAMA": "Bibliothèque des sons d'iqama",
    "SND_ALERT_PER_PRE": "Son d'alerte avant l'adhan par prière",
    "SND_ALERT_PER_IQAMA": "Son d'iqama par prière",
    "BTN_ADD_ALERT": "Ajouter un son d'alerte",
    "OPT_RANDOM_ALERT": "Aléatoire - un son différent à chaque fois (sons intégrés et mes fichiers)",
    "MSG_ALERT_SET": "Son d'alerte défini",
    "SND_POST_ADHKAR_PER_PRAYER": "Son des adhkar après la prière, par prière",
    "SET_UPDATES": "Mises à jour",
    "BTN_CHECK_UPDATE": "Rechercher une mise à jour",
    "BTN_UPDATE_NOW": "Installer la mise à jour maintenant",
    "MSG_UPDATE_CHECKING": "Recherche de mises à jour...",
    "MSG_UPDATE_NONE": "Pas de nouvelle mise à jour. Vous avez la dernière version.",
    "MSG_UPDATE_AVAILABLE": "Une nouvelle version est disponible : {version}. Allez dans Paramètres, puis sur le bouton Installer la mise à jour maintenant.",
    "MSG_UPDATE_DOWNLOADING": "Téléchargement de la mise à jour...",
    "MSG_UPDATE_STARTING": "Téléchargement terminé. Le programme d'installation va démarrer et terminer la mise à jour tout seul.",
    "MSG_UPDATE_FAIL": "Impossible de rechercher des mises à jour. Vérifiez votre connexion internet.",
    "MSG_UPDATE_BAD_HASH": "Le fichier de mise à jour a échoué à la vérification d'intégrité. Rien n'a été installé.",
    "MSG_CONVERT_G2H": "Le {d} {gmonth} {y} correspond au {hd} {hmonth} {hy} de l'hégire.",
    "MSG_CONVERT_H2G": "Le {d} {hmonth} {y} de l'hégire correspond au {gd} {gmonth} {gy}.",
    "MSG_EXPORT_HEADER": "Heures de prière pour {month} {year} - {city}, {country}",
    "MSG_EXPORT_METHOD": "Méthode de calcul : {method}",
    "EXPORT_FILE_PREFIX": "horaires-prieres",
    "MSG_DATE_LINE": "{weekday} {gregorian} / {hijri}",
    "MSG_DHIKR_LINE": "Dhikr : {label}",
}

_TABLES = {"ar": _AR, "en": _EN, "fr": _FR}

_PRAYER_NAMES = {
    "ar": {"fajr": "الفجر", "sunrise": "الشروق", "dhuhr": "الظهر",
           "asr": "العصر", "maghrib": "المغرب", "isha": "العشاء"},
    "en": {"fajr": "Fajr", "sunrise": "Sunrise", "dhuhr": "Dhuhr",
           "asr": "Asr", "maghrib": "Maghrib", "isha": "Isha"},
    "fr": {"fajr": "Fajr", "sunrise": "Lever du soleil", "dhuhr": "Dhuhr",
           "asr": "Asr", "maghrib": "Maghrib", "isha": "Isha"},
}

_METHOD_LABELS = {
    "egypt": {"ar": "الهيئة المصرية العامة للمساحة",
              "en": "Egyptian General Survey Authority",
              "fr": "Autorité générale égyptienne de topographie"},
    "mwl": {"ar": "رابطة العالم الإسلامي", "en": "Muslim World League",
            "fr": "Ligue islamique mondiale"},
    "isna": {"ar": "ISNA", "en": "ISNA", "fr": "ISNA"},
}


def prayer_name(key: str) -> str:
    names = _PRAYER_NAMES.get(_LANG, _PRAYER_NAMES["ar"])
    return names.get(key, key)


def method_label(key: str) -> str:
    labels = _METHOD_LABELS.get(key)
    if not labels:
        return key
    return labels.get(_LANG, labels["ar"])


def _fmt(name: str, **kw) -> str:
    return tr(name).format(**kw)


def msg_export_done(path: str) -> str:
    return _fmt("MSG_EXPORT_DONE", path=path)


def msg_adhan_now(prayer: str) -> str:
    return _fmt("MSG_ADHAN_NOW", prayer=prayer)


def msg_iqama_now(prayer: str) -> str:
    return _fmt("MSG_IQAMA_NOW", prayer=prayer)


def msg_pre_adhan(prayer: str, minutes: int) -> str:
    return _fmt("MSG_PRE_ADHAN", prayer=prayer, minutes=minutes)


def msg_post_adhkar(prayer: str) -> str:
    return _fmt("MSG_POST_ADHKAR", prayer=prayer)


def msg_next_prayer_at(name: str, time_str: str) -> str:
    return _fmt("MSG_NEXT_PRAYER_AT", name=name, time=time_str)


def msg_remaining(h: int, m: int) -> str:
    return _fmt("MSG_REMAINING_HM", h=h, m=m)


def msg_launch_full(app: str, weekday: str, gregorian: str, hijri: str,
                    notable: str, name: str, time_str: str) -> str:
    return _fmt("MSG_LAUNCH_FULL", app=app, weekday=weekday, gregorian=gregorian,
                hijri=hijri, notable=notable, name=name, time=time_str)


def msg_launch_short(app: str) -> str:
    return _fmt("MSG_LAUNCH_SHORT", app=app)


def msg_update_available(version: str) -> str:
    return _fmt("MSG_UPDATE_AVAILABLE", version=version)


def msg_about(version: str) -> str:
    return tr("APP_NAME") + "\n" + _fmt("ABOUT_TEXT", version=version)
