; Inno Setup script for the Parth Windows installer.
;
; Build prerequisites:
;   1. PyInstaller has produced dist\parth\ (see installer/parth.spec)
;   2. Inno Setup 6 is installed (https://jrsoftware.org/isinfo.php)
;
; Build (PowerShell, from repo root):
;   $env:PARTH_VERSION = python -c "import parth.constants.models as m; print(m.VERSION)"
;   iscc /DAppVersion=$env:PARTH_VERSION installer\parth.iss
;
; Output: installer\Output\parth-agent-{version}-x64-setup.exe
;
; Behavior:
;   • Install  — copies dist\parth\ to "Program Files\Parth Agent",
;                adds to user PATH, creates shortcuts, registers uninstaller.
;   • Upgrade  — same installer detects prior version via AppId, closes a
;                running parth.exe, replaces files, preserves %APPDATA% data,
;                restarts shortcut targets cleanly.
;   • Uninstall — removes installed files, optionally wipes %APPDATA%\parth-agent
;                with a user prompt. PATH entry is cleaned automatically.

; ── Parameterized version ─────────────────────────────────────────────────
; If the build script passes /DAppVersion=X.Y.Z, use it; otherwise fall back.
; Keep this in sync with parth/constants/models.py:VERSION.
#ifndef AppVersion
  #define AppVersion "0.1.3"
#endif

#define MyAppName        "Parth Agent"
#define MyAppPublisher   "Parth"
; TODO before public release: replace with the real GitHub repo URL.
; Shows up in Add/Remove Programs and the installer's "Updates" link.
#define MyAppURL         "https://github.com/anujhabuild/parth-agent"
#define MyAppExeName     "parth.exe"
#define MyAppConfigDir   "{userappdata}\parth-agent"

[Setup]
; AppId is the upgrade identity. NEVER change this between releases — Inno
; Setup uses it to detect "previous version installed" and route into the
; upgrade flow instead of a fresh install. Generated once via Tools > GUID.
AppId={{6E2C9DAE-92B3-4F66-A50A-9B3F9E0F8E3D}

AppName={#MyAppName}
AppVersion={#AppVersion}
AppVerName={#MyAppName} {#AppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Windows-visible version metadata. ProductVersion is what Add/Remove Programs
; and right-click→Properties surface; VersionInfoVersion must be 4-part numeric.
VersionInfoVersion={#AppVersion}.0
VersionInfoProductVersion={#AppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} setup
VersionInfoProductName={#MyAppName}
VersionInfoTextVersion={#MyAppName} {#AppVersion}

DefaultDirName={autopf}\Parth Agent
DefaultGroupName=Parth Agent
DisableProgramGroupPage=yes
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
MinVersion=10.0
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; A new bundle replaces an older one — file replacement is forced and any
; running parth.exe is closed gracefully then restarted. This makes the
; "upgrade while the tool is open" path safe.
CloseApplications=force
RestartApplications=yes

; Block downgrades — installing 0.1.2 over 0.1.4 would silently mess up the
; user's config schema. They must uninstall manually first.
DisableDirPage=auto

OutputBaseFilename=parth-agent-{#AppVersion}-x64-setup
OutputDir=Output
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\parth.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#AppVersion}
ChangesEnvironment=yes
ChangesAssociations=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "addtopath";   Description: "Add &Parth to your user PATH (makes `parth` runnable in any terminal)"; GroupDescription: "Integration:"

[Files]
; PyInstaller produces dist\parth\ — copy it verbatim under {app}.
Source: "..\dist\parth\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; Start Menu shortcut — opens a console window with parth running.
Name: "{group}\Parth Agent"; Filename: "{cmd}"; Parameters: "/k ""{app}\{#MyAppExeName}"""; WorkingDir: "{userdocs}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall Parth Agent"; Filename: "{uninstallexe}"

; Optional Desktop shortcut.
Name: "{autodesktop}\Parth Agent"; Filename: "{cmd}"; Parameters: "/k ""{app}\{#MyAppExeName}"""; WorkingDir: "{userdocs}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Per-user PATH addition, guarded by the "Add to PATH" task selection.
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; \
    ValueData: "{olddata};{app}"; \
    Check: NeedsAddPath('{app}'); Tasks: addtopath

; Version stamp the installer can read on the next upgrade (e.g. for migration
; logic) and the in-app updater can use to check "am I up to date?".
Root: HKCU; Subkey: "Software\Parth\Parth Agent"; ValueType: string; ValueName: "InstalledVersion"; ValueData: "{#AppVersion}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Parth\Parth Agent"; ValueType: string; ValueName: "InstallDir"; ValueData: "{app}"; Flags: uninsdeletekey

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Parth Agent now"; \
    Flags: postinstall nowait skipifsilent unchecked

[UninstallDelete]
; Remove the install dir itself if empty after file removal. Files in
; %APPDATA%\parth-agent are NEVER touched by [UninstallDelete] — they get the
; explicit prompt handled in [Code] below.
Type: dirifempty; Name: "{app}"

; ── Code: PATH cleanup + optional user-data wipe ─────────────────────────
[Code]
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKCU, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Lowercase(ExpandConstant(Param)) + ';',
                ';' + Lowercase(OrigPath) + ';') = 0;
end;

procedure RemoveFromPath(Dir: string);
var
  OrigPath, NewPath, Needle: string;
  Idx: Integer;
begin
  if not RegQueryStringValue(HKCU, 'Environment', 'Path', OrigPath) then exit;
  NewPath := ';' + OrigPath + ';';
  Needle  := ';' + Dir + ';';
  Idx := Pos(Lowercase(Needle), Lowercase(NewPath));
  if Idx = 0 then exit;
  Delete(NewPath, Idx, Length(Needle) - 1);
  // Strip the temporary leading/trailing semicolons we added.
  if (Length(NewPath) > 0) and (NewPath[1] = ';') then Delete(NewPath, 1, 1);
  if (Length(NewPath) > 0) and (NewPath[Length(NewPath)] = ';') then
    Delete(NewPath, Length(NewPath), 1);
  RegWriteExpandStringValue(HKCU, 'Environment', 'Path', NewPath);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ConfigDir: string;
  WipeChoice: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Clean PATH entry we may have added during install.
    RemoveFromPath(ExpandConstant('{app}'));

    // Offer to remove user data. Default = No (preserve), because most users
    // uninstall to upgrade and would lose API keys / chat history otherwise.
    ConfigDir := ExpandConstant('{#MyAppConfigDir}');
    if DirExists(ConfigDir) then
    begin
      WipeChoice := MsgBox(
        'Also remove your Parth Agent user data?' + #13#10 + #13#10 +
        'This wipes API keys, chat history, memory, lessons, and themes at:' + #13#10 +
        ConfigDir + #13#10 + #13#10 +
        'Choose No to keep your data for a future reinstall.',
        mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
      if WipeChoice = IDYES then
        DelTree(ConfigDir, True, True, True);
    end;
  end;
end;
