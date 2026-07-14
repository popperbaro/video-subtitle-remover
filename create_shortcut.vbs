Set WshShell = WScript.CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
strCurDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Create Desktop shortcut
Set oShortcut = WshShell.CreateShortcut(strDesktop & "\Video Subtitle Remover.lnk")
oShortcut.TargetPath = strCurDir & "\Video Subtitle Remover.bat"
oShortcut.WorkingDirectory = strCurDir
oShortcut.IconLocation = strCurDir & "\design\vsr.ico, 0"
oShortcut.Description = "AI-powered Video Subtitle Remover"
oShortcut.WindowStyle = 7
oShortcut.Save

' Create shortcut in app folder too
Set oShortcut2 = WshShell.CreateShortcut(strCurDir & "\Video Subtitle Remover.lnk")
oShortcut2.TargetPath = strCurDir & "\Video Subtitle Remover.bat"
oShortcut2.WorkingDirectory = strCurDir
oShortcut2.IconLocation = strCurDir & "\design\vsr.ico, 0"
oShortcut2.Description = "AI-powered Video Subtitle Remover"
oShortcut2.WindowStyle = 7
oShortcut2.Save

WScript.Echo "Shortcut created on Desktop and in app folder!"
