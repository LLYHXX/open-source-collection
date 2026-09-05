' aififteen Hunter silent watchdog launcher (no window, for autostart)
Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
ws.CurrentDirectory = base
ws.Run """" & base & "\watchdog.bat""", 0, False
