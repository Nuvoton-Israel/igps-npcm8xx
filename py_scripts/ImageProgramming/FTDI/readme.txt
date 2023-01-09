 This tool control FTDI device using Asynchronous Bit-Bang mode.
 
 Usage: 
 Arbel_EVB_Automation -help 
 Arbel_EVB_Automation -list 
 Arbel_EVB_Automation -open-desc  <description>   [commands ...] 
 Arbel_EVB_Automation -open-sn    <serial-number> [commands ...] 
 Arbel_EVB_Automation -open-locid <locid>         [commands ...] 


 Mandatory:
 ----------
 -help : Print this usage manual.
 -list : List FTDI devices. FT4232H devices with "NPCM8mnx_Evaluation_Board A" description are mark in green.
 -open-desc <description>: Open device by description string. Use '-list' to get description of connected devices.
 -open-sn <serial-number>: Open device by serial-number string. Use '-list' to get serial-number of connected devices.
 -open-locid <locid>:      Open device by location ID in hex value. Use '-list' to get location ID of connected devices.
 
 Commands:
 ---------
 Commands are executed in the order in which they appear in command-line arguments.
 
 -port-set <mask> <dir> <out>: Set local variable port state, not yet update the port
    <mask>: Bit mask for <dir> and <out> setting. 0:skip, 1:use
    <dir>:  Port direction in hex value. 0:input tristate, 1:output
    <out>:  Port data output in hex value
    Example: -port-set 0xF0 0xF0 0x80
             This will set pin 7 to output high, pins 4-6 to output low while pins 0-3 are unchanged

 -port-read: Read the actual port input value. Useful for pins that was set to input
    Note: only last -port-read command or -pin-read will be the return value
    Example: -port-set 0xF0 0xF0 0x80 -update -port-read
             This will set the port output and then read the port input

 -pin-set <num> <direction> <output>: Set local variable pin state, not yet update the port
    <num>:     Pin number 0 to 7
    <direction>:  Pin direction. 0:input tristate, 1:output
    <output>:     Pin output value
    Example: -pin-set 5 1 0 -update
             This will set pin 5 to output low

 -pin-read <num>: Read the actual pin input value. Useful for pins that was set to input
    <num>: Pin number 0 to 7.
    Note: only last -port-read command or -pin-read will be the return value
    Example: -pin-set 0 1 1 -update -pin-read 0
             This will set pin 0 high and then read pin 0 input

 -update: Update entire port direction and data output according to local variables
 -reset: Reset the entire port and exit Asynchronous Bit-Bang mode

 -delay <msec>: add delay according to <msec>
    Example: -delay 2000; delay 2 sec
	
 -s: Silent mode, no prints to console

 Example: -open-desc "Quad RS232-HS A" -pin-set 6 1 0 -pin-set 5 1 0 -update -delay 1000 -pin-set 6 0 0 -update
           open device by description, set pins 5 and 6 low (all others are tristate), wait 1 sec, set pin 6 input.
 Note: on tool start, port direction local variable initial value is set to input tristate.
 