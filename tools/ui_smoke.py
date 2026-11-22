"""Real wx smoke test and screenshots with isolated settings and fake audio.
Does not verify NVDA or the user's installed speech synthesizer.
"""
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
os.environ['APPDATA'] = tempfile.mkdtemp(prefix='isma-ui-profile-')
os.environ['XDG_CONFIG_HOME'] = os.environ['APPDATA']
import wx
from isma_adhan import strings as S
from isma_adhan import main_window as ui
from isma_adhan.config import Settings
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else 'ui-evidence')
OUT.mkdir(parents=True, exist_ok=True)

class Player:
    def set_volume(self, n): pass
    def play(self, p): pass
    def stop(self): self.stopped = True
class Speaker:
    def __init__(self): self.lines = []
    def speak(self, text): self.lines.append(text)

app = wx.App(False)
app.SetExitOnFrameDelete(False)
errors = []
state = {}

def step(fn, *args):
    def guarded():
        try: fn(*args)
        except Exception as exc:
            import traceback
            errors.append(str(exc))
            traceback.print_exc()
            app.ExitMainLoop()
    wx.CallLater(350, guarded)

def snap(frame, name):
    from PIL import ImageGrab
    rect = frame.GetScreenRect()
    image = ImageGrab.grab(bbox=(rect.x, rect.y, rect.x+rect.width, rect.y+rect.height))
    image.save(OUT / (name + '.png'))

def snd_default_label():
    from isma_adhan import sounds
    return S.tr('SND_BUNDLED_DEFAULT').format(name=sounds.adhan_voice_name(sounds.ADHAN_DEFAULT_VOICE))

def begin(lang_index):
    if lang_index == 3:
        print('PASS UI smoke complete')
        app.ExitMainLoop()
        return
    lang = ('ar','en','fr')[lang_index]
    S.set_language(lang)
    ui.load_settings = lambda: Settings(language=lang)
    p,s = Player(),Speaker()
    f = ui.MainFrame(p,s)
    state.update(frame=f,lang=lang,index=lang_index)
    f.Show()
    f.Raise()
    step(tab,0)

def tab(index):
    f=state['frame']
    f.notebook.SetSelection(index)
    step(capture,index)

def capture(index):
    f=state['frame']
    lang=state['lang']
    assert f.GetTitle() == S.APP_NAME
    assert S.MSG_NO_ADHAN not in f.log_box.GetValue()
    assert snd_default_label() == f.adhan_assign["all"].GetStringSelection()
    assert f.country_choice.GetStringSelection() == ('مصر' if lang=='ar' else 'Egypt')
    snap(f,lang+'-'+('home','settings','sounds')[index])
    if index<2:
        if index == 1:
            f.btn_check_update.SetFocus()
            step(bottom)
        else:
            step(tab,index+1)
    else:
        step(exercise)

def bottom():
    f=state['frame']
    snap(f,state['lang']+'-settings-bottom')
    step(tab,2)

def inspect_dialog():
    try:
        dialogs=[w for w in wx.GetTopLevelWindows() if isinstance(w,wx.Dialog) and w.IsModal()]
        assert len(dialogs)==1
        dlg=dialogs[0]
        assert dlg.FindWindow(wx.ID_YES).GetLabel()==S.BTN_YES
        assert dlg.FindWindow(wx.ID_NO).GetLabel()==S.BTN_NO
        snap(dlg,state['lang']+'-exit')
        dlg.EndModal(wx.ID_NO)
    except Exception as exc:
        errors.append(str(exc))
        app.ExitMainLoop()

def exercise():
    f=state['frame']
    assert f.timer.IsRunning()
    f.stop_audio()
    assert f.timer.IsRunning()
    assert f.player.stopped and f.speaker.lines[-1] == S.MSG_STOPPED
    assert not f._really_quit
    wx.CallLater(350,inspect_dialog)
    assert f._confirm_exit() is False
    from isma_adhan import updater
    launched, downloaded = [], []
    old_launch, old_download = updater.launch_installer, updater.download_async
    updater.launch_installer = lambda path: launched.append(path)
    def fake_download(info, callback):
        downloaded.append(info)
        callback(Path('test-only-installer.exe'),None)
    updater.download_async = fake_download
    try:
        f._on_update_checked(updater.UpdateInfo('9.9.9','', 'a'*64,True),None,False)
        assert f.btn_update_now.IsEnabled() and not launched and not downloaded
        event=wx.CommandEvent(wx.EVT_BUTTON.typeId,f.btn_update_now.GetId())
        f.btn_update_now.GetEventHandler().ProcessEvent(event)
        assert len(downloaded)==1
        wx.Yield()
        assert len(launched)==1
    finally:
        updater.launch_installer, updater.download_async = old_launch, old_download
    f.settings.adhan_sounds['all'] = 'missing-test-only.mp3'
    f.refresh_sound_lists()
    assert S.MSG_NO_ADHAN in f.current_adhan_label.GetLabel()
    assert f.adhan_assign['all'].GetStringSelection().startswith(S.tr('SND_UNAVAILABLE').split('{')[0])
    f.settings.adhan_sounds.pop('all')
    f.refresh_sound_lists()
    f._confirm_exit=lambda:False
    f.Close()
    assert not f._really_quit and not f.IsBeingDeleted()
    f._confirm_exit=lambda:True
    f.Close()
    print('PASS language, stop preserves scheduler, close-No, close-Yes:',state['lang'])
    step(begin,state['index']+1)

sentinel=wx.Frame(None)
sentinel.Show()
step(begin,0)
app.MainLoop()
if errors: raise SystemExit(1)
