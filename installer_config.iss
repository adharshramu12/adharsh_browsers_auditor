[Setup]
AppName=Adharsh Browser Auditor
AppVersion=1.0
DefaultDirName={localappdata}\AdharshBrowserAuditor
DisableDirPage=yes
DefaultGroupName=Adharsh Browser Auditor
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=Adharsh_Auditor_Setup_Windows
SetupIconFile=app_logo.ico
UninstallDisplayIcon={app}\Adharsh_Browser_Auditor.exe
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\Adharsh_Browser_Auditor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Adharsh Browser Auditor"; Filename: "{app}\Adharsh_Browser_Auditor.exe"; IconFilename: "{app}\app_logo.ico"
Name: "{autodesktop}\Adharsh Browser Auditor"; Filename: "{app}\Adharsh_Browser_Auditor.exe"; IconFilename: "{app}\app_logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\Adharsh_Browser_Auditor.exe"; Description: "{cm:LaunchProgram,Adharsh Browser Auditor}"; Flags: nowait postinstall skipifsilent
