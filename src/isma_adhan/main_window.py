"""Main window (wxPython). Multilingual (Arabic RTL, English, French),
NVDA-friendly.

Accessibility rules followed here:
- every control is a native Windows control reachable with Tab alone
- every input has a visible wx.StaticText label so screen readers announce it
- every action exists in the menu bar and on a keyboard shortcut;
  nothing requires a mouse
- each alert is delivered three ways: a sound, a spoken announcement (NVDA
  first, SAPI fallback), and a Windows notification, and it is appended to
  the on-screen log
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import wx
import wx.adv

from . import autostart
from . import sounds as snd
from . import strings as S
from . import updater
from . import world
from . import __version__
from .config import ensure_dirs, load_settings, save_settings, sound_dirs
from .hijri import gregorian_label, hijri_label, notable_announcement, weekday_label
from .date_tools import convert_date_text, month_export_lines
from .prayer_times import ADHAN_PRAYERS, PRAYERS, PrayerTimeCalculator
from .scheduler import ADHAN, ADHKAR, IQAMA, KAHF, POST_ADHKAR, PRE_ADHAN, SchedulerEngine

PRE_ADHAN_CHOICES = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
ADHKAR_INTERVAL_CHOICES = [10, 15, 20, 30]

ID_PLAY_ADHAN = wx.NewIdRef()
ID_STOP = wx.NewIdRef()
ID_TOGGLE_ADHKAR = wx.NewIdRef()
ID_SAY_NEXT = wx.NewIdRef()
ID_HIDE = wx.NewIdRef()
ID_SHORTCUTS = wx.NewIdRef()
ID_ABOUT = wx.NewIdRef()
ID_QUIT = wx.NewIdRef()


def _minutes_label(minutes: int) -> str:
    return S.OPT_OFF if minutes == 0 else S.tr("MSG_MINUTES_COUNT").format(n=minutes)


# v1.7 alert-sound sections map each kind to its strings key
_ALERT_LIB_KEYS = {"pre_adhan": "SND_ALERT_LIB_PRE", "iqama": "SND_ALERT_LIB_IQAMA"}
_ALERT_PER_KEYS = {"pre_adhan": "SND_ALERT_PER_PRE", "iqama": "SND_ALERT_PER_IQAMA"}


def _layout_dir():
    return wx.Layout_RightToLeft if S.current_language() == "ar" else wx.Layout_LeftToRight


class MainFrame(wx.Frame):
    def __init__(self, player, speaker):
        area = wx.Display(0).GetClientArea()
        initial_size = (min(900, area.width - 20), min(820, area.height - 20))
        super().__init__(None, title=S.APP_NAME, size=initial_size)
        self.SetPosition((area.x + (area.width - initial_size[0]) // 2,
                          area.y + (area.height - initial_size[1]) // 2))
        self.SetLayoutDirection(_layout_dir())

        self.settings = load_settings()
        ensure_dirs()
        self.dirs = sound_dirs()
        self.player = player
        self.player.set_volume(self.settings.volume)
        self.speaker = speaker
        self._really_quit = False
        self._current_day = None
        self._pending_update = None
        self._update_busy = False

        self.calc = self._make_calculator()
        self.engine = SchedulerEngine(
            self.settings, lambda d: self.calc.for_date(d).times
        )
        self.adhkar_rotation = snd.ShuffledRotation()

        self._build_menu()
        self._build_ui()
        self._build_accelerators()
        self.CreateStatusBar()
        self.SetStatusText(S.APP_TAGLINE)

        icon_path = snd.resource_path("assets", "icon.ico")
        if icon_path.exists():
            self.SetIcon(wx.Icon(str(icon_path), wx.BITMAP_TYPE_ICO))

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(1000)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self._refresh_day()
        if snd.resolve_adhan(self.settings.adhan_sounds.get("all"), self.dirs["adhan"]) is None:
            self.log(S.MSG_NO_ADHAN)

    # ------------------------------------------------------------------ UI
    def _build_menu(self):
        menubar = wx.MenuBar()

        play_menu = wx.Menu()
        play_menu.Append(int(ID_PLAY_ADHAN), S.MENU_PLAY_ADHAN)
        play_menu.Append(int(ID_STOP), S.MENU_STOP)
        play_menu.Append(int(ID_TOGGLE_ADHKAR), S.MENU_TOGGLE_ADHKAR)
        menubar.Append(play_menu, S.MENU_PLAY)

        file_menu = wx.Menu()
        file_menu.Append(int(ID_HIDE), S.MENU_HIDE)
        file_menu.Append(int(ID_QUIT), S.MENU_EXIT)
        menubar.Append(file_menu, S.MENU_FILE)

        help_menu = wx.Menu()
        help_menu.Append(int(ID_SHORTCUTS), S.MENU_SHORTCUTS)
        help_menu.Append(int(ID_ABOUT), S.MENU_ABOUT)
        menubar.Append(help_menu, S.MENU_HELP)

        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, lambda e: self.play_adhan_now(), id=int(ID_PLAY_ADHAN))
        self.Bind(wx.EVT_MENU, lambda e: self.stop_audio(), id=int(ID_STOP))
        self.Bind(wx.EVT_MENU, lambda e: self.toggle_adhkar(), id=int(ID_TOGGLE_ADHKAR))
        self.Bind(wx.EVT_MENU, lambda e: self.say_next_prayer(), id=int(ID_SAY_NEXT))
        self.Bind(wx.EVT_MENU, lambda e: self.Hide(), id=int(ID_HIDE))
        self.Bind(wx.EVT_MENU, self.on_quit, id=int(ID_QUIT))
        self.Bind(wx.EVT_MENU, lambda e: wx.MessageBox(S.SHORTCUTS_HELP, S.MENU_SHORTCUTS, parent=self), id=int(ID_SHORTCUTS))
        self.Bind(wx.EVT_MENU, lambda e: wx.MessageBox(S.msg_about(__version__), S.MENU_ABOUT, parent=self), id=int(ID_ABOUT))

    def _build_accelerators(self):
        entries = [
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("A"), int(ID_PLAY_ADHAN)),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("S"), int(ID_STOP)),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("D"), int(ID_TOGGLE_ADHKAR)),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("N"), int(ID_SAY_NEXT)),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("M"), int(ID_HIDE)),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("Q"), int(ID_QUIT)),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F1, int(ID_SHORTCUTS)),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

    def _build_ui(self):
        panel = wx.Panel(self)
        panel.SetLayoutDirection(_layout_dir())
        root = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(panel)
        self.notebook.SetLayoutDirection(_layout_dir())
        root.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 8)
        panel.SetSizer(root)

        self._build_home_tab()
        self._build_settings_tab()
        self._build_sounds_tab()

    def _build_home_tab(self):
        page = wx.Panel(self.notebook)
        page.SetLayoutDirection(_layout_dir())
        box = wx.BoxSizer(wx.VERTICAL)

        big = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.next_label = wx.StaticText(page, label="")
        self.next_label.SetFont(big)
        box.Add(self.next_label, 0, wx.ALL, 8)

        self.remaining_label = wx.StaticText(page, label="")
        box.Add(self.remaining_label, 0, wx.ALL, 8)

        # date line: prominent, right before the prayer-times list, and a
        # read-only text control (not a StaticText) so the date is in the tab
        # order and NVDA announces it like any other field
        box.Add(wx.StaticText(page, label=S.LBL_DATE), 0, wx.LEFT | wx.TOP, 8)
        self.date_label = wx.TextCtrl(
            page, style=wx.TE_READONLY | wx.TE_CENTER | wx.BORDER_SIMPLE
        )
        self.date_label.SetName(S.LBL_DATE_GREG_HIJRI)
        self.date_label.SetFont(big)
        box.Add(self.date_label, 0, wx.ALL | wx.EXPAND, 8)

        # date converter: type a date, hear/see it in the other calendar
        box.Add(wx.StaticText(page, label=S.LBL_CONVERT), 0, wx.LEFT | wx.TOP, 8)
        conv_row = wx.BoxSizer(wx.HORIZONTAL)
        self.convert_input = wx.TextCtrl(page)
        self.convert_input.SetName(S.CONVERT_FIELD_NAME)
        self.btn_convert = wx.Button(page, label=S.BTN_CONVERT)
        self.btn_convert.Bind(wx.EVT_BUTTON, lambda e: self.convert_date())
        conv_row.Add(self.convert_input, 1, wx.ALL | wx.EXPAND, 4)
        conv_row.Add(self.btn_convert, 0, wx.ALL, 4)
        box.Add(conv_row, 0, wx.EXPAND | wx.ALL, 4)
        self.convert_result = wx.TextCtrl(
            page, style=wx.TE_READONLY | wx.TE_CENTER | wx.BORDER_SIMPLE
        )
        self.convert_result.SetName(S.CONVERT_RESULT_NAME)
        box.Add(self.convert_result, 0, wx.ALL | wx.EXPAND, 4)

        box.Add(wx.StaticText(page, label=S.LBL_PRAYER_TIMES), 0, wx.LEFT | wx.TOP, 8)
        self.prayer_list = wx.ListBox(page, choices=[])
        box.Add(self.prayer_list, 0, wx.EXPAND | wx.ALL, 8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_play = wx.Button(page, label=S.BTN_PLAY_ADHAN)
        self.btn_stop = wx.Button(page, label=S.BTN_STOP)
        self.btn_play.Bind(wx.EVT_BUTTON, lambda e: self.play_adhan_now())
        self.btn_stop.Bind(wx.EVT_BUTTON, lambda e: self.stop_audio())
        btn_row.Add(self.btn_play, 0, wx.ALL, 4)
        btn_row.Add(self.btn_stop, 0, wx.ALL, 4)
        self.btn_export = wx.Button(page, label=S.BTN_EXPORT_MONTH)
        self.btn_export.Bind(wx.EVT_BUTTON, lambda e: self.export_month())
        btn_row.Add(self.btn_export, 0, wx.ALL, 4)
        box.Add(btn_row, 0, wx.ALL, 4)

        box.Add(wx.StaticText(page, label=S.LBL_LOG), 0, wx.LEFT | wx.TOP, 8)
        self.log_box = wx.TextCtrl(page, style=wx.TE_MULTILINE | wx.TE_READONLY)
        box.Add(self.log_box, 1, wx.EXPAND | wx.ALL, 8)

        page.SetSizer(box)
        self.notebook.AddPage(page, S.TAB_HOME)

    def _on_scrolled_focus(self, event, page):
        child = event.GetWindow()
        event.Skip()

        def reveal():
            if not page or not child:
                return
            origin = page.ClientToScreen((0, 0))
            rect = child.GetScreenRect()
            top = rect.y - origin.y
            bottom = top + rect.height
            height = page.GetClientSize().height
            delta = bottom - height + 8 if bottom > height - 8 else (top - 8 if top < 8 else 0)
            if delta:
                unit = page.GetScrollPixelsPerUnit()[1] or 20
                steps = (delta + unit - 1) // unit if delta > 0 else delta // unit
                page.Scroll(-1, max(0, page.GetViewStart()[1] + steps))
        wx.CallAfter(reveal)

    def _build_settings_tab(self):
        page = wx.ScrolledWindow(self.notebook)
        page.SetScrollRate(0, 20)
        page.Bind(wx.EVT_CHILD_FOCUS, lambda e, p=page: self._on_scrolled_focus(e, p))
        page.SetLayoutDirection(_layout_dir())
        box = wx.BoxSizer(wx.VERTICAL)
        s = self.settings

        def add_row(label_text, control):
            row = wx.BoxSizer(wx.HORIZONTAL)
            lbl = wx.StaticText(page, label=label_text)
            lbl.Wrap(340)
            row.Add(lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 6)
            row.Add(control, 1, wx.ALL | wx.EXPAND, 6)
            box.Add(row, 0, wx.EXPAND)
            control.SetName(label_text)
            return control

        # --- language first, "like any program": auto follows Windows,
        # manual override here; applies fully on restart
        self._lang_codes = ["auto", "ar", "en", "fr"]
        lang_choices = [S.OPT_LANG_AUTO] + [S.LANGUAGES[c] for c in ("ar", "en", "fr")]
        self.language_choice = add_row(S.SET_LANGUAGE, wx.Choice(page, choices=lang_choices))
        cur = s.language if s.language in self._lang_codes else "auto"
        self.language_choice.SetSelection(self._lang_codes.index(cur))

        # --- location: country -> city, plus auto-detect
        country_names = [d for _, d in world.countries()]
        self._country_isos = [iso for iso, _ in world.countries()]
        self.country_choice = add_row(S.SET_COUNTRY, wx.Choice(page, choices=country_names))
        self.city_choice = add_row(S.SET_CITY, wx.Choice(page, choices=[]))
        self._cities = []
        self.country_choice.Bind(wx.EVT_CHOICE, lambda e: self._fill_cities())
        self._select_country_by_display(s.country)
        detect_btn = wx.Button(page, label=S.SET_DETECT)
        detect_btn.Bind(wx.EVT_BUTTON, lambda e: self.on_detect_location())
        box.Add(detect_btn, 0, wx.ALL, 6)

        # --- startup bismillah reciter
        self.bismillah_choice = add_row(
            S.SET_BISMILLAH_VOICE,
            wx.Choice(page, choices=[snd.bismillah_voice_name(k) for k, *_ in snd.BISMILLAH_VOICES] + [S.OPT_RANDOM]),
        )
        keys = [k for k, *_ in snd.BISMILLAH_VOICES] + ["random"]
        self.bismillah_choice.SetSelection(
            keys.index(s.bismillah_voice) if s.bismillah_voice in keys else 0
        )

        # --- per-prayer alerts: pre-adhan / iqama / post-prayer adhkar
        grid = wx.FlexGridSizer(rows=len(ADHAN_PRAYERS) + 1, cols=4, vgap=4, hgap=6)
        for head in (S.HDR_PRAYER, S.HDR_PRE, S.HDR_IQAMA, S.HDR_POST):
            heading = wx.StaticText(page, label=head)
            heading.Wrap(170)
            grid.Add(heading, 0, wx.ALL, 4)
        for col in (1, 2, 3):
            grid.AddGrowableCol(col)
        self.pre_choices = {}
        self.iqama_spins = {}
        self.post_choices = {}
        for prayer in ADHAN_PRAYERS:
            pname = S.prayer_name(prayer)
            grid.Add(wx.StaticText(page, label=pname), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
            pre = wx.Choice(page, choices=[_minutes_label(m) for m in PRE_ADHAN_CHOICES])
            pre.SetName(f"{S.HDR_PRE} - {pname}")
            v = s.pre_adhan_for(prayer)
            pre.SetSelection(PRE_ADHAN_CHOICES.index(v) if v in PRE_ADHAN_CHOICES else 1)
            grid.Add(pre, 1, wx.ALL | wx.EXPAND, 4)
            self.pre_choices[prayer] = pre
            spin = wx.SpinCtrl(page, min=0, max=60, initial=s.iqama_for(prayer))
            spin.SetName(f"{S.HDR_IQAMA} - {pname}")
            grid.Add(spin, 1, wx.ALL | wx.EXPAND, 4)
            self.iqama_spins[prayer] = spin
            post = wx.Choice(page, choices=[_minutes_label(m) for m in PRE_ADHAN_CHOICES])
            post.SetName(f"{S.HDR_POST} - {pname}")
            v = s.post_adhkar_for(prayer)
            post.SetSelection(PRE_ADHAN_CHOICES.index(v) if v in PRE_ADHAN_CHOICES else 0)
            grid.Add(post, 1, wx.ALL | wx.EXPAND, 4)
            self.post_choices[prayer] = post
        box.Add(grid, 0, wx.EXPAND | wx.ALL, 4)

        self.adhkar_check = wx.CheckBox(page, label=S.SET_ADHKAR_ON)
        self.adhkar_check.SetValue(s.adhkar_enabled)
        box.Add(self.adhkar_check, 0, wx.ALL, 6)

        self.adhkar_interval_choice = add_row(
            S.SET_ADHKAR_INTERVAL,
            wx.Choice(page, choices=[_minutes_label(m) for m in ADHKAR_INTERVAL_CHOICES]),
        )
        self.adhkar_interval_choice.SetSelection(
            ADHKAR_INTERVAL_CHOICES.index(s.adhkar_interval_minutes)
            if s.adhkar_interval_minutes in ADHKAR_INTERVAL_CHOICES
            else 1
        )

        self.quiet_check = wx.CheckBox(page, label=S.SET_ADHKAR_QUIET)
        self.quiet_check.SetValue(s.adhkar_quiet_hours)
        box.Add(self.quiet_check, 0, wx.ALL, 6)

        self.volume_slider = add_row(
            S.SET_VOLUME, wx.Slider(page, value=s.volume, minValue=0, maxValue=100)
        )

        self.speak_check = wx.CheckBox(page, label=S.SET_SPEAK)
        self.speak_check.SetValue(s.speak_prayer_name)
        box.Add(self.speak_check, 0, wx.ALL, 6)

        self.autostart_check = wx.CheckBox(page, label=S.SET_AUTOSTART)
        self.autostart_check.SetValue(s.autostart and autostart.is_supported())
        box.Add(self.autostart_check, 0, wx.ALL, 6)

        self.kahf_check = wx.CheckBox(page, label=S.SET_KAHF)
        self.kahf_check.SetValue(s.kahf_enabled)
        box.Add(self.kahf_check, 0, wx.ALL, 6)

        self.kahf_time_text = add_row(S.SET_KAHF_TIME, wx.TextCtrl(page, value=s.kahf_time))

        save_btn = wx.Button(page, label=S.BTN_SAVE)
        save_btn.Bind(wx.EVT_BUTTON, lambda e: self.apply_settings())
        box.Add(save_btn, 0, wx.ALL, 8)

        # --- updates: manual check + an Update button that only arms after a
        # newer version was found; the installer never runs on its own
        box.Add(wx.StaticText(page, label=S.SET_UPDATES), 0, wx.LEFT | wx.TOP, 8)
        upd_row = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_check_update = wx.Button(page, label=S.BTN_CHECK_UPDATE)
        self.btn_check_update.Bind(wx.EVT_BUTTON, lambda e: self.on_check_update(manual=True))
        self.btn_update_now = wx.Button(page, label=S.BTN_UPDATE_NOW)
        self.btn_update_now.Bind(wx.EVT_BUTTON, lambda e: self.on_update_now())
        self.btn_update_now.Enable(False)
        upd_row.Add(self.btn_check_update, 0, wx.ALL, 4)
        upd_row.Add(self.btn_update_now, 0, wx.ALL, 4)
        box.Add(upd_row, 0, wx.ALL, 4)

        page.SetSizer(box)
        page.FitInside()
        self.notebook.AddPage(page, S.TAB_SETTINGS)

    def _select_country_by_display(self, display):
        for i, (iso, disp) in enumerate(world.countries()):
            if disp == display or iso == world.country_iso(display):
                self.country_choice.SetSelection(i)
                self._fill_cities()
                return
        if self.country_choice.GetCount():
            self.country_choice.SetSelection(0)
        self._fill_cities()

    def _fill_cities(self):
        sel = self.country_choice.GetSelection()
        iso = self._country_isos[sel] if 0 <= sel < len(self._country_isos) else "EG"
        self._cities = world.cities_of(iso)
        self.city_choice.Set([world.city_display(c) for c in self._cities])
        for i, c in enumerate(self._cities):
            if self.settings.city in (c.get("ar"), c["en"]) or (
                c["lat"] == self.settings.lat and c["lng"] == self.settings.lng
            ):
                self.city_choice.SetSelection(i)
                return
        if self._cities:
            self.city_choice.SetSelection(0)

    def on_detect_location(self):
        found = world.detect_location()
        if not found:
            self.log(S.MSG_DETECT_FAILED)
            self.speak(S.MSG_DETECT_FAILED)
            return
        self._select_country_by_display(world.country_display(found["iso"]))
        disp = world.city_display(found["city"])
        for i, c in enumerate(self._cities):
            if world.city_display(c) == disp:
                self.city_choice.SetSelection(i)
                break
        self.log(S.MSG_DETECTED)
        self.speak(S.MSG_DETECTED)

    def _build_sounds_tab(self):
        page = wx.ScrolledWindow(self.notebook)
        page.SetScrollRate(0, 20)
        page.Bind(wx.EVT_CHILD_FOCUS, lambda e, p=page: self._on_scrolled_focus(e, p))
        page.SetLayoutDirection(_layout_dir())
        box = wx.BoxSizer(wx.VERTICAL)

        box.Add(wx.StaticText(page, label=S.SND_ADHAN_LIB), 0, wx.LEFT | wx.TOP, 8)
        self.adhan_list = wx.ListBox(page, choices=[], size=(-1, 100))
        box.Add(self.adhan_list, 1, wx.EXPAND | wx.ALL, 8)

        row = wx.BoxSizer(wx.HORIZONTAL)
        for label, handler in (
            (S.BTN_ADD_ADHAN, self.on_add_adhan),
            (S.BTN_SET_ADHAN, self.on_set_adhan),
            (S.BTN_PREVIEW, lambda e: self._preview(self.adhan_list, self.dirs["adhan"])),
            (S.BTN_STOP, lambda e: self.stop_audio()),
        ):
            b = wx.Button(page, label=label)
            b.Bind(wx.EVT_BUTTON, handler)
            row.Add(b, 0, wx.ALL, 4)
        box.Add(row, 0)

        self.current_adhan_label = wx.StaticText(page, label="")
        box.Add(self.current_adhan_label, 0, wx.ALL, 8)

        box.Add(wx.StaticText(page, label=S.SND_PER_PRAYER), 0, wx.LEFT | wx.TOP, 8)
        self.adhan_assign = {}
        assign_rows = [("all", S.SND_ALL_PRAYERS)] + [(p, S.prayer_name(p)) for p in ADHAN_PRAYERS]
        for key, label in assign_rows:
            arow = wx.BoxSizer(wx.HORIZONTAL)
            arow.Add(wx.StaticText(page, label=label), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 6)
            achoice = wx.Choice(page, choices=[])
            achoice.SetName(f"{S.SND_PER_PRAYER} - {label}")
            arow.Add(achoice, 1, wx.ALL | wx.EXPAND, 6)
            box.Add(arow, 0, wx.EXPAND)
            achoice.Bind(wx.EVT_CHOICE, lambda e, k=key: self.on_assign_adhan(k))
            self.adhan_assign[key] = achoice

        # v1.7: custom alert sounds (pre-adhan reminder + iqama), per prayer,
        # same shape as the adhan section above
        self._alert_ui = {}
        self._build_alert_section(page, box, "pre_adhan")
        self._build_alert_section(page, box, "iqama")

        box.Add(wx.StaticText(page, label=S.SND_ADHKAR_LIB), 0, wx.LEFT | wx.TOP, 8)
        self.adhkar_list = wx.ListBox(page, choices=[], size=(-1, 100))
        box.Add(self.adhkar_list, 1, wx.EXPAND | wx.ALL, 8)

        row2 = wx.BoxSizer(wx.HORIZONTAL)
        add_adhkar_btn = wx.Button(page, label=S.BTN_ADD_ADHKAR)
        add_adhkar_btn.Bind(wx.EVT_BUTTON, self.on_add_adhkar)
        preview_adhkar_btn = wx.Button(page, label=S.BTN_PREVIEW)
        preview_adhkar_btn.Bind(wx.EVT_BUTTON, lambda e: self._preview(self.adhkar_list, self.dirs["adhkar"]))
        row2.Add(add_adhkar_btn, 0, wx.ALL, 4)
        row2.Add(preview_adhkar_btn, 0, wx.ALL, 4)
        box.Add(row2, 0)

        # v1.7: per-prayer picker for the post-prayer adhkar sound; the
        # library above IS this kind's list (bundled clips + his files)
        box.Add(wx.StaticText(page, label=S.SND_POST_ADHKAR_PER_PRAYER), 0, wx.LEFT | wx.TOP, 8)
        assign = {}
        assign_rows = [("all", S.SND_ALL_PRAYERS)] + [(p, S.prayer_name(p)) for p in ADHAN_PRAYERS]
        for key, label in assign_rows:
            arow = wx.BoxSizer(wx.HORIZONTAL)
            arow.Add(wx.StaticText(page, label=label), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 6)
            achoice = wx.Choice(page, choices=[])
            achoice.SetName(f"{S.SND_POST_ADHKAR_PER_PRAYER} - {label}")
            arow.Add(achoice, 1, wx.ALL | wx.EXPAND, 6)
            box.Add(arow, 0, wx.EXPAND)
            achoice.Bind(wx.EVT_CHOICE, lambda e, kk=key: self.on_assign_alert("post_adhkar", kk))
            assign[key] = achoice
        self._alert_ui["post_adhkar"] = {"list": None, "assign": assign, "files": []}

        page.SetSizer(box)
        page.FitInside()
        self.notebook.AddPage(page, S.TAB_SOUNDS)
        self.refresh_sound_lists()

    def _build_alert_section(self, page, box, kind):
        """One alert-sound section of the sounds tab (v1.7): library list
        (bundled tones + the user's own files), add/preview/stop buttons,
        and per-prayer assignment - the same shape as the adhan section."""
        lib_label = S.tr(_ALERT_LIB_KEYS[kind])
        per_label = S.tr(_ALERT_PER_KEYS[kind])
        box.Add(wx.StaticText(page, label=lib_label), 0, wx.LEFT | wx.TOP, 8)
        lst = wx.ListBox(page, choices=[], size=(-1, 100))
        lst.SetName(lib_label)
        box.Add(lst, 1, wx.EXPAND | wx.ALL, 8)

        row = wx.BoxSizer(wx.HORIZONTAL)
        add_btn = wx.Button(page, label=S.BTN_ADD_ALERT)
        add_btn.Bind(wx.EVT_BUTTON, lambda e, k=kind: self._add_files(self.dirs[k]))
        prev_btn = wx.Button(page, label=S.BTN_PREVIEW)
        prev_btn.Bind(wx.EVT_BUTTON, lambda e, k=kind: self._preview_alert(k))
        stop_btn = wx.Button(page, label=S.BTN_STOP)
        stop_btn.Bind(wx.EVT_BUTTON, lambda e: self.stop_audio())
        for b in (add_btn, prev_btn, stop_btn):
            row.Add(b, 0, wx.ALL, 4)
        box.Add(row, 0)

        box.Add(wx.StaticText(page, label=per_label), 0, wx.LEFT | wx.TOP, 8)
        assign = {}
        assign_rows = [("all", S.SND_ALL_PRAYERS)] + [(p, S.prayer_name(p)) for p in ADHAN_PRAYERS]
        for key, label in assign_rows:
            arow = wx.BoxSizer(wx.HORIZONTAL)
            arow.Add(wx.StaticText(page, label=label), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 6)
            achoice = wx.Choice(page, choices=[])
            achoice.SetName(f"{per_label} - {label}")
            arow.Add(achoice, 1, wx.ALL | wx.EXPAND, 6)
            box.Add(arow, 0, wx.EXPAND)
            achoice.Bind(wx.EVT_CHOICE, lambda e, k=kind, kk=key: self.on_assign_alert(k, kk))
            assign[key] = achoice
        self._alert_ui[kind] = {"list": lst, "assign": assign, "files": []}

    def _alert_settings_dict(self, kind):
        return {
            "pre_adhan": self.settings.pre_adhan_sounds,
            "iqama": self.settings.iqama_sounds,
            "post_adhkar": self.settings.post_adhkar_sounds,
        }[kind]

    def on_assign_alert(self, kind, key):
        ui = self._alert_ui[kind]
        sel = ui["assign"][key].GetSelection()
        target = self._alert_settings_dict(kind)
        if sel == 0:
            target.pop(key, None)
        elif sel == 1:
            target[key] = snd.ALERT_RANDOM_TOKEN
        elif 2 <= sel <= len(ui["files"]) + 1:
            target[key] = str(ui["files"][sel - 2])
        save_settings(self.settings)
        self.refresh_sound_lists()
        self.log(S.MSG_ALERT_SET)
        self.speak(S.MSG_ALERT_SET)

    def _preview_alert(self, kind):
        ui = self._alert_ui[kind]
        sel = ui["list"].GetSelection()
        if sel == 0:
            path = snd.resolve_alert(kind, snd.ALERT_RANDOM_TOKEN, self.dirs[kind])
            if path is not None:
                self._safe_play(path)
        elif 1 <= sel <= len(ui["files"]):
            self._safe_play(ui["files"][sel - 1])

    def _refresh_alert_lists(self):
        for kind in ("pre_adhan", "iqama", "post_adhkar"):
            ui = getattr(self, "_alert_ui", {}).get(kind)
            if not ui:
                continue
            user_dir = self.dirs["adhkar"] if kind == "post_adhkar" else self.dirs[kind]
            bundled = snd.bundled_alerts(kind)
            user_files = snd.list_sounds(user_dir)
            ui["files"] = [p for p, _ in bundled] + user_files
            names = [label for _, label in bundled] + [snd.display_name(p) for p in user_files]
            if ui["list"] is not None:
                ui["list"].Set([S.OPT_RANDOM_ALERT] + names)
            target = self._alert_settings_dict(kind)
            for key, choice in ui["assign"].items():
                if key != "all":
                    default_label = S.OPT_DEFAULT
                elif kind == "post_adhkar":
                    default_label = S.SND_ROTATION
                else:
                    default_label = S.tr("SND_BUNDLED_DEFAULT").format(name=snd.alert_clip_name(kind, snd.alert_default_key(kind)))
                choice.Set([default_label, S.OPT_RANDOM_ALERT] + names)
                current = target.get(key, "")
                idx = 0
                if current == snd.ALERT_RANDOM_TOKEN:
                    idx = 1
                elif current:
                    for i, pth in enumerate(ui["files"]):
                        if str(pth) == current:
                            idx = i + 2
                            break
                choice.SetSelection(idx)

    # ------------------------------------------------------------- helpers
    def _make_calculator(self) -> PrayerTimeCalculator:
        lat, lng = self.settings.lat_lng()
        return PrayerTimeCalculator(lat, lng, self.settings.timezone_name, self.settings.method)

    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.settings.timezone_name)

    def now(self) -> datetime:
        return datetime.now(self.tz())

    def log(self, message: str):
        stamp = self.now().strftime("%H:%M:%S")
        self.log_box.AppendText(f"[{stamp}] {message}\n")
        self.SetStatusText(message)

    def notify(self, message: str):
        notif = wx.adv.NotificationMessage(S.APP_NAME, message, parent=self)
        notif.Show(timeout=wx.adv.NotificationMessage.Timeout_Auto)
        self._last_notif = notif  # keep alive

    def speak(self, message: str):
        if self.settings.speak_prayer_name:
            self.speaker.speak(message)

    # --------------------------------------------------------------- timer
    def on_timer(self, _event):
        now = self.now()
        if self._current_day != now.date():
            self._refresh_day()
        for ev in self.engine.tick(now):
            self.handle_event(ev)
        self._update_countdown(now)

    def _refresh_day(self):
        now = self.now()
        self._current_day = now.date()
        d = now.date()
        self.date_label.SetValue(
            S.tr("MSG_DATE_LINE").format(
                weekday=weekday_label(d), gregorian=gregorian_label(d), hijri=hijri_label(d))
        )
        day_times = self.calc.for_date(d)
        self._day_times = day_times
        self.prayer_list.Set(
            [f"{S.prayer_name(p)}: {day_times.times[p].strftime('%H:%M')}" for p in PRAYERS]
        )
        self._update_countdown(now)

    def _update_countdown(self, now: datetime):
        try:
            name, at = self.calc.next_prayer(now)
        except Exception:
            return
        remaining = at - now
        total_seconds = max(0, int(remaining.total_seconds()))
        h, rem = divmod(total_seconds, 3600)
        m, sec = divmod(rem, 60)
        self.next_label.SetLabel(
            f"{S.LBL_NEXT_PRAYER}: "
            + S.tr("MSG_NEXT_PRAYER_SHORT").format(
                name=S.prayer_name(name), time=at.strftime('%H:%M')))
        self.remaining_label.SetLabel(f"{S.LBL_REMAINING}: {h:02d}:{m:02d}:{sec:02d}")

    # --------------------------------------------------------------- events
    def handle_event(self, ev):
        ar = S.prayer_name(ev.prayer or "")
        if ev.kind == PRE_ADHAN:
            msg = S.msg_pre_adhan(ar, self.settings.pre_adhan_for(ev.prayer))
            path = snd.resolve_alert(
                "pre_adhan", self.settings.pre_adhan_sound_for(ev.prayer), self.dirs["pre_adhan"]
            )
            self._safe_play(path if path is not None else snd.default_tone("pre_adhan"))
            self.notify(msg)
            self.speak(msg)
            self.log(msg)
        elif ev.kind == ADHAN:
            msg = S.msg_adhan_now(ar)
            path = snd.resolve_adhan(self.settings.adhan_sound_for(ev.prayer), self.dirs["adhan"])
            if path is not None:
                self._safe_play(path)
            else:
                self._safe_play(snd.default_tone("fallback_adhan"))
            self.notify(msg)
            self.speak(msg)
            self.log(msg)
        elif ev.kind == IQAMA:
            msg = S.msg_iqama_now(ar)
            path = snd.resolve_alert(
                "iqama", self.settings.iqama_sound_for(ev.prayer), self.dirs["iqama"]
            )
            self._safe_play(path if path is not None else snd.default_tone("iqama"))
            self.notify(msg)
            self.speak(msg)
            self.log(msg)
        elif ev.kind == POST_ADHKAR:
            msg = S.msg_post_adhkar(ar)
            self.log(msg)
            self.speak(msg)
            choice = self.settings.post_adhkar_sound_for(ev.prayer)
            path = snd.resolve_alert("post_adhkar", choice, self.dirs["adhkar"]) if choice else None
            if path is not None:
                self._safe_play(path)
            else:
                self._play_next_adhkar_clip()
        elif ev.kind == ADHKAR:
            self._play_next_adhkar_clip()
        elif ev.kind == KAHF:
            self._safe_play(snd.default_tone("kahf"))
            self.notify(S.MSG_KAHF)
            self.speak(S.MSG_KAHF)
            self.log(S.MSG_KAHF)

    def on_assign_adhan(self, key):
        choice = self.adhan_assign[key]
        sel = choice.GetSelection()
        if sel == 0:
            self.settings.adhan_sounds.pop(key, None)
        elif sel == 1:
            self.settings.adhan_sounds[key] = snd.ADHAN_RANDOM_TOKEN
        elif 2 <= sel <= len(self._adhan_files) + 1:
            self.settings.adhan_sounds[key] = str(self._adhan_files[sel - 2])
        save_settings(self.settings)
        self.refresh_sound_lists()
        self.log(S.MSG_ADHAN_SET)

    def _safe_play(self, path):
        try:
            self.player.play(path)
        except Exception as exc:
            self.log(S.tr("MSG_AUDIO_FAIL").format(name=Path(path).name))

    def _play_next_adhkar_clip(self):
        clips = snd.all_adhkar(self.dirs["adhkar"])
        labels = {str(p): label for p, label in clips}
        clip = self.adhkar_rotation.next([p for p, _ in clips])
        if clip:
            self._safe_play(clip)
            self.log(S.tr("MSG_DHIKR_LINE").format(label=labels.get(str(clip), snd.display_name(clip))))
        else:
            self.log(S.MSG_ADHKAR_EMPTY)

    # --------------------------------------------------------------- actions
    def play_adhan_now(self):
        path = snd.resolve_adhan(self.settings.adhan_sounds.get("all", ""), self.dirs["adhan"])
        if path is not None:
            self._safe_play(path)
        else:
            self._safe_play(snd.default_tone("fallback_adhan"))
            self.log(S.MSG_NO_ADHAN)

    def convert_date(self):
        result = convert_date_text(self.convert_input.GetValue())
        self.convert_result.SetValue(result)
        self.log(result)
        self.speak(result)

    def export_month(self):
        try:
            now = self.now()
            lines = month_export_lines(
                self.calc,
                now.year,
                now.month,
                self.settings.city,
                self.settings.country,
                self.settings.method,
            )
            docs = Path.home() / "Documents"
            docs.mkdir(parents=True, exist_ok=True)
            out = docs / f"{S.EXPORT_FILE_PREFIX}-{now.year}-{now.month:02d}.txt"
            # utf-8-sig so Windows Notepad shows the arabic correctly
            out.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
            msg = S.msg_export_done(out.name)
            self.log(msg)
            self.speak(msg)
        except Exception:
            self.log(S.MSG_EXPORT_FAIL)
            self.speak(S.MSG_EXPORT_FAIL)

    def stop_audio(self):
        self.player.stop()
        self.log(S.MSG_STOPPED)
        self.speaker.speak(S.MSG_STOPPED)

    def toggle_adhkar(self):
        self.settings.adhkar_enabled = not self.settings.adhkar_enabled
        self.adhkar_check.SetValue(self.settings.adhkar_enabled)
        save_settings(self.settings)
        msg = S.MSG_ADHKAR_TOGGLED_ON if self.settings.adhkar_enabled else S.MSG_ADHKAR_TOGGLED_OFF
        self.speak(msg)
        self.log(msg)

    def say_next_prayer(self):
        now = self.now()
        name, at = self.calc.next_prayer(now)
        remaining = at - now
        total = max(0, int(remaining.total_seconds()))
        h, rem = divmod(total, 3600)
        m = rem // 60
        text = S.msg_next_prayer_at(S.prayer_name(name), at.strftime('%H:%M')) + " " + S.msg_remaining(h, m)
        self.speaker.speak(text)
        self.log(text)

    def apply_settings(self):
        s = self.settings
        li = self.language_choice.GetSelection()
        old_language = s.language
        if 0 <= li < len(self._lang_codes):
            s.language = self._lang_codes[li]
        ci = self.country_choice.GetSelection()
        countries = world.countries()
        if 0 <= ci < len(countries):
            s.country = countries[ci][1]
        sel = self.city_choice.GetSelection()
        if 0 <= sel < len(self._cities):
            c = self._cities[sel]
            s.city = world.city_display(c)
            s.lat, s.lng, s.timezone_name = c["lat"], c["lng"], c["tz"]
        for prayer in ADHAN_PRAYERS:
            s.pre_adhan_per[prayer] = PRE_ADHAN_CHOICES[max(0, self.pre_choices[prayer].GetSelection())]
            s.iqama_per[prayer] = self.iqama_spins[prayer].GetValue()
            s.post_adhkar_per[prayer] = PRE_ADHAN_CHOICES[max(0, self.post_choices[prayer].GetSelection())]
        keys = [k for k, *_ in snd.BISMILLAH_VOICES] + ["random"]
        bi = self.bismillah_choice.GetSelection()
        if 0 <= bi < len(keys):
            s.bismillah_voice = keys[bi]
        s.adhkar_enabled = self.adhkar_check.GetValue()
        s.adhkar_interval_minutes = ADHKAR_INTERVAL_CHOICES[
            max(0, self.adhkar_interval_choice.GetSelection())
        ]
        s.adhkar_quiet_hours = self.quiet_check.GetValue()
        s.volume = self.volume_slider.GetValue()
        s.speak_prayer_name = self.speak_check.GetValue()
        s.kahf_enabled = self.kahf_check.GetValue()
        kahf_time = self.kahf_time_text.GetValue().strip()
        if len(kahf_time.split(":")) == 2:
            s.kahf_time = kahf_time
        s.autostart = self.autostart_check.GetValue()

        if autostart.is_supported():
            if s.autostart:
                autostart.enable(sys.executable)
            else:
                autostart.disable()

        save_settings(s)
        self.player.set_volume(s.volume)
        self.calc = self._make_calculator()
        self.engine = SchedulerEngine(s, lambda d: self.calc.for_date(d).times)
        self._refresh_day()
        self.log(S.MSG_SAVED)
        self.speak(S.MSG_SAVED)
        if s.language != old_language:
            # applies fully on restart; announced in the current language
            self.speak(S.MSG_LANGUAGE_RESTART)
            self.log(S.MSG_LANGUAGE_RESTART)

    # ------------------------------------------------------------- sounds tab
    def refresh_sound_lists(self):
        bundled_a = snd.bundled_adhan()
        user_files = snd.list_sounds(self.dirs["adhan"])
        self._adhan_files = [p for p, _ in bundled_a] + user_files
        names = [label for _, label in bundled_a] + [snd.display_name(p) for p in user_files]
        self.adhan_list.Set([S.OPT_RANDOM_ADHAN] + names)
        for key, choice in getattr(self, "adhan_assign", {}).items():
            default_label = S.tr("SND_BUNDLED_DEFAULT").format(name=snd.adhan_voice_name(snd.ADHAN_DEFAULT_VOICE)) if key == "all" else S.OPT_DEFAULT
            choice.Set([default_label, S.OPT_RANDOM_ADHAN] + names)
            current = self.settings.adhan_sounds.get(key, "")
            idx = 0
            if current == snd.ADHAN_RANDOM_TOKEN:
                idx = 1
            elif current:
                for i, p in enumerate(self._adhan_files):
                    if str(p) == current or snd.resolve_adhan(current, self.dirs["adhan"]) == p:
                        idx = i + 2
                        break
            if current and idx == 0:
                choice.Append(S.tr("SND_UNAVAILABLE").format(name=snd.adhan_display(current)))
                idx = choice.GetCount() - 1
            choice.SetSelection(idx)
        bundled = snd.bundled_adhkar()
        user_files = snd.list_sounds(self.dirs["adhkar"])
        self._adhkar_files = [p for p, _ in bundled] + user_files
        self.adhkar_list.Set([label for _, label in bundled] + [snd.display_name(p) for p in user_files])
        value = self.settings.adhan_sounds.get("all", "")
        current = snd.adhan_display(value)
        if snd.resolve_adhan(value, self.dirs["adhan"]) is None:
            current = S.MSG_NO_ADHAN
        self.current_adhan_label.SetLabel(f"{S.SET_ADHAN_SOUND}: {current}")
        self._refresh_alert_lists()

    def _add_files(self, directory):
        dlg = wx.FileDialog(
            self,
            message=S.MSG_CHOOSE_AUDIO,
            wildcard=S.WILDCARD_AUDIO,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            for path in dlg.GetPaths():
                try:
                    snd.add_sound(Path(path), directory)
                    self.log(f"{S.MSG_ADDED}: {Path(path).name}")
                except ValueError:
                    self.log(S.tr("MSG_BAD_FILE_TYPE").format(name=Path(path).name))
            self.refresh_sound_lists()
        dlg.Destroy()

    def on_add_adhan(self, _event):
        self._add_files(self.dirs["adhan"])

    def on_add_adhkar(self, _event):
        self._add_files(self.dirs["adhkar"])

    def on_set_adhan(self, _event):
        sel = self.adhan_list.GetSelection()
        if sel == 0:
            self.settings.adhan_sounds["all"] = snd.ADHAN_RANDOM_TOKEN
        elif 1 <= sel <= len(self._adhan_files):
            self.settings.adhan_sounds["all"] = str(self._adhan_files[sel - 1])
        else:
            return
        save_settings(self.settings)
        self.refresh_sound_lists()
        self.log(S.MSG_ADHAN_SET)
        self.speak(S.MSG_ADHAN_SET)

    def _preview(self, listbox, directory):
        sel = listbox.GetSelection()
        files = self._adhan_files if directory == self.dirs["adhan"] else self._adhkar_files
        if directory == self.dirs["adhan"] and sel == 0:
            path = snd.resolve_adhan(snd.ADHAN_RANDOM_TOKEN, self.dirs["adhan"])
            if path is not None:
                self._safe_play(path)
        elif directory == self.dirs["adhan"] and 1 <= sel <= len(files):
            self._safe_play(files[sel - 1])
        elif directory != self.dirs["adhan"] and 0 <= sel < len(files):
            self._safe_play(files[sel])

    # ---------------------------------------------------------------- close
    def play_bismillah(self) -> float:
        """Play the bundled Bismillah (first sound at launch, before the chime
        and the spoken announcement). Returns its length in seconds, or 0 when
        it cannot play so the caller falls back to the chime."""
        voice = snd.resolve_bismillah_voice(self.settings.bismillah_voice)
        path = snd.bismillah_path(voice)
        if path is None:
            path = snd.resource_path("assets", "sounds", "bismillah.wav")
        if not path.exists():
            return 0.0
        try:
            if path.suffix.lower() == ".wav":
                import wave

                with wave.open(str(path), "rb") as w:
                    secs = w.getnframes() / w.getframerate()
            else:
                secs = snd.bismillah_voice_seconds(voice)
        except Exception:
            secs = 6.0
        try:
            self.player.play(path)
            self.log(S.tr("MSG_BISMILLAH_LINE").format(voice=snd.bismillah_voice_name(voice)))
            return secs
        except Exception:
            return 0.0

    def announce_startup(self):
        """Spoken confirmation that the app started - key feedback for a blind
        user who cannot otherwise tell the window opened. Independent of the
        speak_prayer_name setting so first run always says something."""
        try:
            now = self.now()
            d = now.date()
            name, at = self.calc.next_prayer(now)
            note = notable_announcement(d)
            text = S.msg_launch_full(
                app=S.APP_NAME,
                weekday=weekday_label(d),
                gregorian=gregorian_label(d),
                hijri=hijri_label(d),
                notable=(note + " ") if note else "",
                name=S.prayer_name(name),
                time_str=at.strftime('%H:%M'),
            )
        except Exception:
            text = S.msg_launch_short(S.APP_NAME)
        self.speaker.speak(text)
        self.log(text)

    def show_window(self):
        self.Show()
        self.Iconize(False)
        self.Raise()

    def _confirm_exit(self) -> bool:
        """Accessible spoken Yes/No before any real exit (v1.8, his request:
        Alt+F4 asks first). No cancels the close and keeps everything running."""
        self.speaker.speak(S.MSG_CONFIRM_EXIT)
        dlg = wx.GenericMessageDialog(
            self, S.MSG_CONFIRM_EXIT, S.TITLE_CONFIRM_EXIT,
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        dlg.SetYesNoLabels(S.BTN_YES, S.BTN_NO)
        try:
            return dlg.ShowModal() == wx.ID_YES
        finally:
            dlg.Destroy()

    def on_close(self, event):
        # _really_quit is set by the installer hook, the end-session handlers
        # and the confirm path below: those close without asking again.
        if self._really_quit:
            self.timer.Stop()
            self.player.stop()
            self.Destroy()
            return
        if event.CanVeto() and not self._confirm_exit():
            event.Veto()
            return
        self._really_quit = True
        self.timer.Stop()
        self.player.stop()
        self.Destroy()

    def on_quit(self, _event):
        self.Close()

    # ------------------------------------------------------------- updates
    def on_check_update(self, manual: bool):
        """Silent launch check (manual=False) or the Settings button. Only
        ever REPORTS; installing always needs the Update button (his rule,
        the installer never runs on its own)."""
        if self._update_busy or getattr(self, "_update_checking", False):
            return
        self._update_checking = True
        if manual:
            self.btn_check_update.Enable(False)
            self.log(S.MSG_UPDATE_CHECKING)
            self.speak(S.MSG_UPDATE_CHECKING)
        updater.check_async(
            lambda info, error: wx.CallAfter(self._on_update_checked, info, error, manual)
        )

    def _on_update_checked(self, info, error, manual):
        if not self or self.IsBeingDeleted():
            return
        self._update_checking = False
        self.btn_check_update.Enable(True)
        if error or info is None:
            if manual:
                self.log(S.MSG_UPDATE_FAIL)
                self.speak(S.MSG_UPDATE_FAIL)
            return
        if not info.newer:
            if manual:
                self.log(S.MSG_UPDATE_NONE)
                self.speak(S.MSG_UPDATE_NONE)
            return
        self._pending_update = info
        self.btn_update_now.Enable(True)
        msg = S.msg_update_available(info.version)
        self.log(msg)
        self.speak(msg)
        self.notify(msg)

    def on_update_now(self):
        info = self._pending_update
        if info is None:
            self.on_check_update(manual=True)
            return
        if self._update_busy:
            return
        self._update_busy = True
        self.btn_update_now.Enable(False)
        self.btn_check_update.Enable(False)
        self.log(S.MSG_UPDATE_DOWNLOADING)
        self.speak(S.MSG_UPDATE_DOWNLOADING)
        updater.download_async(
            info,
            lambda path, error: wx.CallAfter(self._on_update_downloaded, path, error),
        )

    def _on_update_downloaded(self, path, error):
        if not self or self.IsBeingDeleted():
            return
        self._update_busy = False
        self.btn_check_update.Enable(True)
        if error is not None or path is None:
            self.btn_update_now.Enable(True)
            msg = S.MSG_UPDATE_BAD_HASH if error == "hash" else S.MSG_UPDATE_FAIL
            self.log(msg)
            self.speak(msg)
            return
        self.log(S.MSG_UPDATE_STARTING)
        self.speak(S.MSG_UPDATE_STARTING)
        try:
            updater.launch_installer(path)
        except OSError:
            self.btn_update_now.Enable(True)
            self.log(S.MSG_UPDATE_FAIL)
            self.speaker.speak(S.MSG_UPDATE_FAIL)
