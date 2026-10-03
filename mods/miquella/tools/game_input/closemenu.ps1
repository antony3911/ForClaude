# Close the REFramework menu (Insert) and the game's voice chat that Insert also opens (right click)
$s = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$s\sendkey.ps1" -vk 0x2D; Start-Sleep -Milliseconds 400
Add-Type @"
using System; using System.Runtime.InteropServices;
public class MSC { [DllImport("user32.dll")] public static extern void mouse_event(uint f, int x, int y, uint d, UIntPtr e); }
"@
[MSC]::mouse_event(0x0008,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 80; [MSC]::mouse_event(0x0010,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 500
