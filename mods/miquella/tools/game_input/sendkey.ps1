# Send one key to the foreground window at system level (keybd_event): the game takes these
# where computer-use key names fail (Insert). Usage: sendkey.ps1 -vk 0x2D [-holdMs 60]
# (0x2D Insert, 0x1B Esc, 0x46 F, 0x57 W)
param([int]$vk = 0x2D, [int]$holdMs = 60)
Add-Type @"
using System; using System.Runtime.InteropServices;
public class KB { [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
[DllImport("user32.dll")] public static extern uint MapVirtualKey(uint code, uint type); }
"@
$scan = [byte][KB]::MapVirtualKey([uint32]$vk, 0)
$ext = 0; if (@(0x2D,0x2E,0x24,0x23,0x21,0x22,0x25,0x26,0x27,0x28) -contains $vk) { $ext = 1 }
[KB]::keybd_event([byte]$vk, $scan, [uint32]$ext, [UIntPtr]::Zero)
Start-Sleep -Milliseconds $holdMs
[KB]::keybd_event([byte]$vk, $scan, [uint32](2 -bor $ext), [UIntPtr]::Zero)
