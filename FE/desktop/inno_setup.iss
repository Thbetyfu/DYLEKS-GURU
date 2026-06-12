; =========================================================================
; Inno Setup Script - DyLeks Desktop Local-First Platform
; Dikelola Oleh: Tim Pengembang DyLeks (TELULANG)
;
; Alasan Desain ('Why'):
;   1. Memungkinkan guru menginstall seluruh ekosistem DyLeks (FastAPI, 
;      Next.js, SQLite, dan Electron) secara luring dengan sekali klik.
;   2. Mengotomatiskan registrasi Windows Defender Firewall (port 3003 & 3004)
;      agar browser HP siswa dapat terhubung ke laptop guru tanpa diblokir Windows.
; =========================================================================

[Setup]
AppId={{D1A2B3C4-E5F6-7A8B-9C0D-1E2F3A4B5C6D}}
AppName=DyLeks Local AI Platform
AppVersion=2.0
AppPublisher=TELULANG - Universitas Telkom
AppPublisherURL=https://dyleks.id
AppSupportURL=https://dyleks.id
AppUpdatesURL=https://dyleks.id
DefaultDirName={pf}\DyLeks
DefaultGroupName=DyLeks
DisableProgramGroupPage=yes
OutputBaseFilename=DyLeks_Setup_v2.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; SetupIconFile=favicon.ico

[Languages]
Name: "indonesian"; MessagesFile: "compiler:Languages\Indonesian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Salin berkas orkestrator Electron desktop launcher
Source: "main.js"; DestDir: "{app}"; Flags: ignoreversion
Source: "package.json"; DestDir: "{app}"; Flags: ignoreversion

; Salin seluruh direktori Backend FastAPI (termasuk SQLite database)
Source: "..\..\BE\*"; DestDir: "{app}\backend"; Flags: recursesubdirs createallsubdirs ignoreversion

; Salin seluruh direktori Frontend Next.js (exclude folder desktop ini sendiri)
Source: "..\*"; DestDir: "{app}\frontend"; Flags: recursesubdirs createallsubdirs ignoreversion exclude:"\desktop"

[Icons]
Name: "{group}\DyLeks Local AI Platform"; Filename: "{app}\frontend\node_modules\.bin\electron.cmd"; Parameters: "."; WorkingDir: "{app}"
Name: "{userdesktop}\DyLeks Local AI Platform"; Filename: "{app}\frontend\node_modules\.bin\electron.cmd"; Parameters: "."; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Tambahkan pengecualian port firewall Windows secara otomatis agar bisa diakses oleh device dalam satu Wi-Fi kelas (Pilar 2)
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""DyLeks PWA Frontend"" dir=in action=allow protocol=TCP localport=3003"; Flags: runhidden; StatusMsg: "Mengatur aturan firewall untuk port klien (3003)..."
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""DyLeks Backend API"" dir=in action=allow protocol=TCP localport=3004"; Flags: runhidden; StatusMsg: "Mengatur aturan firewall untuk port backend AI (3004)..."

[UninstallRun]
; Hapus aturan firewall saat aplikasi di-uninstall
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""DyLeks PWA Frontend"""; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""DyLeks Backend API"""; Flags: runhidden
