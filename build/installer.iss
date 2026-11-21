; Inno Setup script for اسمع أذان وأذكار (IsmaAdhan)
; Builds IsmaAdhan-Setup.exe from the PyInstaller onedir output.
; Per-user install (no admin required) into %LOCALAPPDATA%\Programs\IsmaAdhan.
; Compile on the CI runner with: iscc build\installer.iss

#define AppName "Isma Adhan wa Adhkar"
#define AppNameAr "اسمع أذان وأذكار"
#define AppVersion "1.7.0"
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
DirExistsWarning=no
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

; The default uninstaller only removes files it installed; app-created
; leftovers (logs, cached data) kept the folder behind, which made the next
; install show the "folder already exists" prompt. Purge them. User
; settings live in %APPDATA%\IsmaAdhan and are deliberately kept.
[UninstallDelete]
Type: filesandordirs; Name: "{app}\*"
Type: dirifempty; Name: "{app}"

[Code]
const
  QUIT_MESSAGE_NAME = 'ISMA_ADHAN_REQUEST_QUIT';
  INSTALLER_MUTEX = 'IsmaAdhanAppMutex';

function RegisterWindowMessageW(lpString: String): UINT;
  external 'RegisterWindowMessageW@user32.dll stdcall';
function PostMessageW(hWnd: LongWord; Msg: UINT; wParam: LongWord; lParam: LongInt): Boolean;
  external 'PostMessageW@user32.dll stdcall';

{ Close any running instance: politely first (this build and newer answer
  the broadcast quit message with a real quit), then forcefully (covers
  older builds that have neither hook). Safe to call repeatedly. }
procedure CloseRunningIsmaAdhan;
var
  MsgId: UINT;
  Attempt: Integer;
  KillResult: Integer;
begin
  MsgId := RegisterWindowMessageW(QUIT_MESSAGE_NAME);
  if MsgId <> 0 then
    PostMessageW($FFFF, MsgId, 0, 0); { HWND_BROADCAST }
  for Attempt := 1 to 24 do
  begin
    if not CheckForMutexes(INSTALLER_MUTEX) then
      Break;
    Sleep(250);
  end;
  { taskkill exits 128 when nothing matches, which is fine }
  Exec('taskkill.exe', '/IM IsmaAdhan.exe /F /T', '', SW_HIDE, ewWaitUntilTerminated, KillResult);
  Sleep(500);
end;

{ MUST run in InitializeSetup: Inno's own AppMutex check ("Setup has
  detected that ... is currently running") fires right after this function
  and BEFORE PrepareToInstall, and in silent mode that prompt aborts the
  whole install. Kill the app here so the check finds nothing. }
function InitializeSetup(): Boolean;
begin
  CloseRunningIsmaAdhan;
  Result := True;
end;

{ Belt and braces: the user could relaunch the app while the wizard is open. }
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  CloseRunningIsmaAdhan;
  Result := '';
end;

function InitializeUninstall(): Boolean;
begin
  CloseRunningIsmaAdhan;
  Result := True;
end;
