"""Main window (wxPython). Arabic, right-to-left, NVDA-friendly.

Accessibility rules followed here:
- every control is a native Windows control reachable with Tab alone
- every input has a visible wx.StaticText label so screen readers announce it
- every action exists in the menu bar and on a keyboard shortcut;
  nothing requires a mouse
- each alert is delivered three ways: a sound, a spoken announcement (SAPI),
  and a Windows notification, and it is appended to the on-screen log
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
from .cities import city_names
from .config import ensure_dirs, load_settings, save_settings, sound_dirs
from .hijri import hijri_label, weekday_label
from .prayer_times import ARABIC_NAMES, PRAYERS, PrayerTimeCalculator
from .scheduler import ADHAN, ADHKAR, IQAMA, KAHF, PRE_ADHAN, SchedulerEngine

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
    return S.OPT_OFF if minutes == 0 else f"{minutes} دقيقة"


class MainFrame(wx.Frame):
    def __init__(self, player, speaker):
        super().__init__(None, title=S.APP_NAME, size=(620, 700))
        self.SetLayoutDirection(wx.Layout_RightToLeft)

        self.settings = load_settings()
        ensure_dirs()
        self.dirs = sound_dirs()
        self.player = player
        self.player.set_volume(self.settings.volume)
        self.speaker = speaker
        self._really_quit = False
        self._current_day = None

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
        if not self.settings.adhan_sound:
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
        file_menu.Append(int(ID_HIDE), "إخفاء النافذة")
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
        self.Bind(wx.EVT_MENU, lambda e: wx.MessageBox(S.ABOUT_TEXT, S.MENU_ABOUT, parent=self), id=int(ID_ABOUT))

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
        panel.SetLayoutDirection(wx.Layout_RightToLeft)
        root = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(panel)
        self.notebook.SetLayoutDirection(wx.Layout_RightToLeft)
        root.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 8)
        panel.SetSizer(root)

        self._build_home_tab()
        self._build_settings_tab()
        self._build_sounds_tab()

    def _build_home_tab(self):
        page = wx.Panel(self.notebook)
        page.SetLayoutDirection(wx.Layout_RightToLeft)
        box = wx.BoxSizer(wx.VERTICAL)

        big = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.date_label = wx.StaticText(page, label="")
        self.date_label.SetFont(big)
        box.Add(self.date_label, 0, wx.ALL, 8)

        self.next_label = wx.StaticText(page, label="")
        self.next_label.SetFont(big)
        box.Add(self.next_label, 0, wx.ALL, 8)

        self.remaining_label = wx.StaticText(page, label="")
        box.Add(self.remaining_label, 0, wx.ALL, 8)

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
        box.Add(btn_row, 0, wx.ALL, 4)

        box.Add(wx.StaticText(page, label=S.LBL_LOG), 0, wx.LEFT | wx.TOP, 8)
        self.log_box = wx.TextCtrl(page, style=wx.TE_MULTILINE | wx.TE_READONLY)
        box.Add(self.log_box, 1, wx.EXPAND | wx.ALL, 8)

        page.SetSizer(box)
        self.notebook.AddPage(page, S.TAB_HOME)

    def _build_settings_tab(self):
        page = wx.Panel(self.notebook)
        page.SetLayoutDirection(wx.Layout_RightToLeft)
        box = wx.BoxSizer(wx.VERTICAL)
        s = self.settings

        def add_row(label_text, control):
            row = wx.BoxSizer(wx.HORIZONTAL)
            lbl = wx.StaticText(page, label=label_text)
            row.Add(lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 6)
            row.Add(control, 1, wx.ALL | wx.EXPAND, 6)
            box.Add(row, 0, wx.EXPAND)
            return control

        self.city_choice = add_row(S.SET_CITY, wx.Choice(page, choices=city_names()))
        names = city_names()
        self.city_choice.SetSelection(names.index(s.city) if s.city in names else 0)

        self.pre_choice = add_row(
            S.SET_PRE_ADHAN,
            wx.Choice(page, choices=[_minutes_label(m) for m in PRE_ADHAN_CHOICES]),
        )
        self.pre_choice.SetSelection(
            PRE_ADHAN_CHOICES.index(s.pre_adhan_minutes) if s.pre_adhan_minutes in PRE_ADHAN_CHOICES else 1
        )

        self.iqama_spin = add_row(S.SET_IQAMA, wx.SpinCtrl(page, min=0, max=60, initial=s.iqama_minutes))

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

        page.SetSizer(box)
        self.notebook.AddPage(page, S.TAB_SETTINGS)

    def _build_sounds_tab(self):
        page = wx.Panel(self.notebook)
        page.SetLayoutDirection(wx.Layout_RightToLeft)
        box = wx.BoxSizer(wx.VERTICAL)

        box.Add(wx.StaticText(page, label=S.SND_ADHAN_LIB), 0, wx.LEFT | wx.TOP, 8)
        self.adhan_list = wx.ListBox(page, choices=[])
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

        box.Add(wx.StaticText(page, label=S.SND_ADHKAR_LIB), 0, wx.LEFT | wx.TOP, 8)
        self.adhkar_list = wx.ListBox(page, choices=[])
        box.Add(self.adhkar_list, 1, wx.EXPAND | wx.ALL, 8)

        row2 = wx.BoxSizer(wx.HORIZONTAL)
        add_adhkar_btn = wx.Button(page, label=S.BTN_ADD_ADHKAR)
        add_adhkar_btn.Bind(wx.EVT_BUTTON, self.on_add_adhkar)
        preview_adhkar_btn = wx.Button(page, label=S.BTN_PREVIEW)
        preview_adhkar_btn.Bind(wx.EVT_BUTTON, lambda e: self._preview(self.adhkar_list, self.dirs["adhkar"]))
        row2.Add(add_adhkar_btn, 0, wx.ALL, 4)
        row2.Add(preview_adhkar_btn, 0, wx.ALL, 4)
        box.Add(row2, 0)

        page.SetSizer(box)
        self.notebook.AddPage(page, S.TAB_SOUNDS)
        self.refresh_sound_lists()

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
        self.date_label.SetLabel(
            f"{weekday_label(d)}، {d.strftime('%Y-%m-%d')} م  /  {hijri_label(d)}"
        )
        day_times = self.calc.for_date(d)
        self._day_times = day_times
        self.prayer_list.Set(
            [f"{ARABIC_NAMES[p]}: {day_times.times[p].strftime('%H:%M')}" for p in PRAYERS]
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
        self.next_label.SetLabel(f"{S.LBL_NEXT_PRAYER}: {ARABIC_NAMES[name]} الساعة {at.strftime('%H:%M')}")
        self.remaining_label.SetLabel(f"{S.LBL_REMAINING}: {h:02d}:{m:02d}:{sec:02d}")

    # --------------------------------------------------------------- events
    def handle_event(self, ev):
        ar = ARABIC_NAMES.get(ev.prayer or "", "")
        if ev.kind == PRE_ADHAN:
            msg = S.msg_pre_adhan(ar, self.settings.pre_adhan_minutes)
            self._safe_play(snd.default_tone("pre_adhan"))
            self.notify(msg)
            self.speak(msg)
            self.log(msg)
        elif ev.kind == ADHAN:
            msg = S.msg_adhan_now(ar)
            path = Path(self.settings.adhan_sound) if self.settings.adhan_sound else None
            if path and path.exists():
                self._safe_play(path)
            else:
                self._safe_play(snd.default_tone("fallback_adhan"))
            self.notify(msg)
            self.speak(msg)
            self.log(msg)
        elif ev.kind == IQAMA:
            msg = S.msg_iqama_now(ar)
            self._safe_play(snd.default_tone("iqama"))
            self.notify(msg)
            self.speak(msg)
            self.log(msg)
        elif ev.kind == ADHKAR:
            clips = snd.list_sounds(self.dirs["adhkar"])
            clip = self.adhkar_rotation.next(clips)
            if clip:
                self._safe_play(clip)
                self.log(f"ذكر: {snd.display_name(clip)}")
            else:
                self.log("لا توجد مقاطع أذكار في المكتبة بعد. أضف مقاطع من تبويب الأصوات.")
        elif ev.kind == KAHF:
            self._safe_play(snd.default_tone("kahf"))
            self.notify(S.MSG_KAHF)
            self.speak(S.MSG_KAHF)
            self.log(S.MSG_KAHF)

    def _safe_play(self, path):
        try:
            self.player.play(path)
        except Exception as exc:
            self.log(f"تعذر تشغيل الصوت: {Path(path).name}")

    # --------------------------------------------------------------- actions
    def play_adhan_now(self):
        path = Path(self.settings.adhan_sound) if self.settings.adhan_sound else None
        if path and path.exists():
            self._safe_play(path)
        else:
            self._safe_play(snd.default_tone("fallback_adhan"))
            self.log(S.MSG_NO_ADHAN)

    def stop_audio(self):
        self.player.stop()
        self.log("تم إيقاف الصوت")

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
        text = (
            f"الصلاة القادمة صلاة {ARABIC_NAMES[name]} الساعة {at.strftime('%H:%M')}. "
            f"الوقت المتبقي {h} ساعات و{m} دقيقة."
        )
        self.speaker.speak(text)
        self.log(text)

    def apply_settings(self):
        s = self.settings
        names = city_names()
        sel = self.city_choice.GetSelection()
        s.city = names[sel] if 0 <= sel < len(names) else names[0]
        s.pre_adhan_minutes = PRE_ADHAN_CHOICES[max(0, self.pre_choice.GetSelection())]
        s.iqama_minutes = self.iqama_spin.GetValue()
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

    # ------------------------------------------------------------- sounds tab
    def refresh_sound_lists(self):
        adhan_files = snd.list_sounds(self.dirs["adhan"])
        self._adhan_files = adhan_files
        self.adhan_list.Set([snd.display_name(p) for p in adhan_files])
        adhkar_files = snd.list_sounds(self.dirs["adhkar"])
        self._adhkar_files = adhkar_files
        self.adhkar_list.Set([snd.display_name(p) for p in adhkar_files])
        current = Path(self.settings.adhan_sound).stem if self.settings.adhan_sound else S.OPT_OFF
        self.current_adhan_label.SetLabel(f"{S.SET_ADHAN_SOUND}: {current}")

    def _add_files(self, directory):
        dlg = wx.FileDialog(
            self,
            message="اختر ملفات صوتية",
            wildcard="ملفات صوتية (*.mp3;*.wav;*.ogg)|*.mp3;*.wav;*.ogg",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            for path in dlg.GetPaths():
                try:
                    snd.add_sound(Path(path), directory)
                    self.log(f"{S.MSG_ADDED}: {Path(path).name}")
                except ValueError:
                    self.log(f"نوع ملف غير مدعوم: {Path(path).name}")
            self.refresh_sound_lists()
        dlg.Destroy()

    def on_add_adhan(self, _event):
        self._add_files(self.dirs["adhan"])

    def on_add_adhkar(self, _event):
        self._add_files(self.dirs["adhkar"])

    def on_set_adhan(self, _event):
        sel = self.adhan_list.GetSelection()
        if 0 <= sel < len(self._adhan_files):
            self.settings.adhan_sound = str(self._adhan_files[sel])
            save_settings(self.settings)
            self.refresh_sound_lists()
            self.log(S.MSG_ADHAN_SET)
            self.speak(S.MSG_ADHAN_SET)

    def _preview(self, listbox, directory):
        sel = listbox.GetSelection()
        files = self._adhan_files if directory == self.dirs["adhan"] else self._adhkar_files
        if 0 <= sel < len(files):
            self._safe_play(files[sel])

    # ---------------------------------------------------------------- close
    def show_window(self):
        self.Show()
        self.Iconize(False)
        self.Raise()

    def on_close(self, event):
        if self._really_quit:
            self.timer.Stop()
            self.player.stop()
            self.Destroy()
        else:
            self.Hide()
            self.notify("البرنامج ما زال يعمل في الخلفية بجانب الساعة. للخروج: قائمة ملف ثم خروج.")

    def on_quit(self, _event):
        self._really_quit = True
        self.Close()
