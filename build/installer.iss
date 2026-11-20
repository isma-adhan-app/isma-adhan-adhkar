; Inno Setup script for اسمع أذان وأذكار (IsmaAdhan)
; Builds IsmaAdhan-Setup.exe from the PyInstaller onedir output.
; Per-user install (no admin required) into %LOCALAPPDATA%\Programs\IsmaAdhan.
; Compile on the CI runner with: iscc build\installer.iss

#define AppName "Isma Adhan wa Adhkar"
#define AppNameAr "اسمع أذان وأذكار"
#define AppVersion "1.1.0"
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

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\IsmaAdhan\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{userdesktop}\{#AppNameAr}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{#AppNameAr}"; Filename: "{app}\{#AppExe}"

[Run]
Filename: "{app}\{#AppExe}"; Description: "تشغيل البرنامج الآن / Run now"; Flags: postinstall nowait skipifsilent unchecked
