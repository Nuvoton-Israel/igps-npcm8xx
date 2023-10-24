
Get-Process -Name ttermpro | Stop-Process -Force


$serialPorts = Get-WmiObject Win32_PnPEntity | Where-Object { $_.Manufacturer -eq 'FTDI' -and $_.PNPClass -eq 'Ports' -and $_.PNPDeviceID -like "*VID_0403*" }
$serialPorts = $serialPorts[($serialPorts.Count-1)..1]
foreach ($port in $serialPorts) {
    echo $($port.Name)
    $com = ($($port.Name) -split '\(|\)')[1]
	$portNumber = [regex]::Replace($com, "[^0-9]", "")
	echo    Start-Process "C:\Program Files (x86)\teraterm\ttermpro.exe" -ArgumentList "/C=$portNumber /BAUD=115200"
    Start-Process "C:\Program Files (x86)\teraterm\ttermpro.exe" -ArgumentList "/C=$portNumber /BAUD=115200"
	$portNumber = ""
}

