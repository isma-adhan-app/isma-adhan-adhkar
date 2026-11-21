; Inno Setup script for اسمع أذان وأذكار (IsmaAdhan)
; Builds IsmaAdhan-Setup.exe from the PyInstaller onedir output.
; Per-user install (no admin required) into %LOCALAPPDATA%\Programs\IsmaAdhan.
; Compile on the CI runner with: iscc build\installer.iss

#define AppName "Isma Adhan wa Adhkar"
#define AppNameAr "اسمع أذان وأذكار"
#define AppVersion "1.6.0"
#define AppExe "IsmaAdhan.exe"

[Setup]
AppName={#AppNameAr}
AppVerName={#AppNameAr} {#AppVersion}
AppVersion={#AppVersion}
AppPublisher=IsmaAdhan
DefaultDirName={autopf}\IsmaAdhan
DefaultGroupName={#AppNameAr}
OutputDir=..\dist\installer
OutputBaseFilename=IsmaAdhan-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\IsmaAdhan.exe
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no
AppMutex=IsmaAdhanAppMutex
VersionInfoVersion={#AppVersion}
VersionInfoCompany=IsmaAdhan
VersionInfoDescription=Isma Adhan wa Adhkar Setup
VersionInfoProductName=Isma Adhan wa Adhkar
VersionInfoProductVersion={#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\IsmaAdhan\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{userdesktop}\{#AppNameAr}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{#AppNameAr}"; Filename: "{app}\{#AppExe}"

[Run]
Filename: "{app}\{#AppExe}"; Description: "تشغيل البرنامج الآن / Run now"; Flags: postinstall nowait skipifsilent unchecked

[Code]
const
  QUIT_MESSAGE_NAME = 'ISMA_ADHAN_REQUEST_QUIT';
  INSTALLER_MUTEX = 'IsmaAdhanAppMutex';

function RegisterWindowMessageW(lpString: String): UINT;
  external 'RegisterWindowMessageW@user32.dll stdcall';
function PostMessageW(hWnd: LongWord; Msg: UINT; wParam: LongWord; lParam: LongInt): Boolean;
  external 'PostMessageW@user32.dll stdcall';

{ Runs right before files are copied (interactive and silent alike).
  A running instance hides to the tray instead of quitting when Windows asks,
  so without this the replace of _internal DLLs fails with DeleteFile code 5. }
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  MsgId: UINT;
  Attempt: Integer;
  KillResult: Integer;
begin
  { 1) polite quit request; this build and newer quit for real on it }
  MsgId := RegisterWindowMessageW(QUIT_MESSAGE_NAME);
  if MsgId <> 0 then
    PostMessageW($FFFF, MsgId, 0, 0); { HWND_BROADCAST }
  for Attempt := 1 to 24 do
  begin
    if not CheckForMutexes(INSTALLER_MUTEX) then
      Break;
    Sleep(250);
  end;
  { 2) older builds never made the mutex or heard the message: force-close
     whatever is still running so the file replace cannot fail. taskkill
     exits 128 when nothing matches, which is fine. }
  Exec('taskkill.exe', '/IM IsmaAdhan.exe /F /T', '', SW_HIDE, ewWaitUntilTerminated, KillResult);
  Sleep(500);
  Result := '';
end;
