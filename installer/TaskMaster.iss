; Inno Setup скрипт для создания инсталлятора TaskMaster
; Компилируется с помощью Inno Setup Compiler

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName=TaskMaster
AppVersion=1.0.2
AppPublisher=TaskMaster
AppPublisherURL=https://github.com/elementary1997/taskmaster
DefaultDirName={autopf}\TaskMaster
DefaultGroupName=TaskMaster
AllowNoIcons=yes
LicenseFile=
OutputDir=dist
OutputBaseFilename=TaskMaster-Setup-1.0.2
SetupIconFile=..\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes
DisableWelcomePage=no
WizardImageFile=
WizardSmallImageFile=
; Тихая установка
; Тихая установка (можно использовать /SILENT при запуске)
Silent=no
; Автоматически закрывать после установки
CloseApplications=yes
RestartApplications=no
; Не показывать страницу "Готово" при тихой установке
DisableFinishedPage=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "..\dist\TaskMaster\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Включаем иконку если есть
Source: "..\icon.ico"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('{src}\..\icon.ico'))
Source: "..\icon.png"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('{src}\..\icon.png'))

[Icons]
Name: "{group}\TaskMaster"; Filename: "{app}\TaskMaster.exe"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,TaskMaster}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\TaskMaster"; Filename: "{app}\TaskMaster.exe"; Tasks: desktopicon; WorkingDir: "{app}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\TaskMaster"; Filename: "{app}\TaskMaster.exe"; Tasks: quicklaunchicon; WorkingDir: "{app}"

[Run]
Filename: "{app}\TaskMaster.exe"; Description: "{cm:LaunchProgram,TaskMaster}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
