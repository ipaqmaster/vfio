# vfio

## What is this

I made this bash script to start my Win10 VM with automatically generated qemu arguments based on the guidelines I pass in.

It saves me loads of time swapping between Linux and VM for gaming and I hope it can help someone else!

## But what does it do

It starts a VM.. but:

  It supports an optional regular expression of USB and PCI devices as arguments and will generate arguments for qemu and pass them in when starting it.

  It rebinds found PCI devices from an optionally provided regex while also generating their qemu arguments.

  It can make a network bridge on the host during VM runtime. Giving the VM a real [Layer 2] presence on your LAN.
    (Useful if the default NAT adapter doesn't satisfy networking needs)

  It can optionally pin the VM's qemu process to specific host CPU threads
    (Useful if I've set up core isolation in the host's boot parameters for improved VM performance)

  When the VM shuts down (qemu exits) the script reprobes my nvidia drivers and brings my display-manager back to my login screen like the VM never happened. All without rebooting!

## What hosts and installs are supported?

This is an ongoing discovery. This script has worked for me this year using Archlinux.

On Archlinux, it's worked on my two below hardware configurations:

  - My now-retired Sabertooth X79 Motherboard (Intel i7 x3930K CPU)
  
  - My current     Aorus x570 Motherboard     (AMD Ryzen 9 3900X CPU)
    
I'm sure it will work on many others however I worry a user's Distribution of Choice™ could easily affect the script's behavior. I'll keep testing this on other installs.

# Why

WINE and Proton have gotten me far for the past few years but sometimes I don't have the time to get a stubborn Title running,
  or worse, a title is known to nor work with Proton or WINE regardless.
  or WORSE, a title employs a driver-level Anti-Cheat solution (which you cannot just throw at WINE) which leaves a VM as the only option.

Modern IOMMU Support has made playing incompatible titles plausible and with ease.

While the VM runs and my host goes headless.. I can still SSH into it, mount steamapps over NFS, X11 forward programs and more.

With a second GPU present the Looking Glass project could be implemented, leaving the VM headless instead. (This flag is being worked on)

# The script, arguments, and examples

## Arguments this script will take [and script Gotchas]

### Arguments

#### Always Required

`-image /dev/zvol/zpoolName/windows,format=raw`

   If set - attaches it with the QEMU -drive parameter.

#### Optional

`-iso /path/to/a/diskimage.iso`

   If set - attaches it with the QEMU -cdrom parameter.

`-bridge br0,enp4s0,tap0`

   Takes a bridge name, interface and tap interface name as arguments.
   In this example it:
     Creates br0 + tap0.
     Slaves tap0 + enp4s0 to br0
     Copies the mac from enp4s0 to the br0 (To preserve the DHCP Reservation in my network)
     Removes any lingering IPs from enp4s0.
     Sets all three to UP..
     Then finally runs dhclient on br0.

   If NetworkManager is found to be running it is stopped during bridging and restored after the bridge is destroyed at the end.
   
   If this argument isn't specified the default qemu NAT adapter will be used
    NAT may be enough for most people.
     
`-memory 8192M` / `-memory 8G`

   Set how much memory the VM gets for this run. Assumes you meanmegabytes unless you explicitly use a suffix like K, M, or G.
     If this argument isn't specified the default value is HALF of the host total.

`-bios '/path/to/that.fd'`
   An optional bios path.
     If not set, the script uses '/usr/share/ovmf/x64/OVMF_CODE.fd' if available.

`-USB 'AT2020USB|SteelSeries|Holtek|Xbox|1425:5769'`

   If set, the script enumerates the regex for USB devices and generates qemu arguments for them.
     This example would catch any attached:
       Any AT2020 Microphone/DAC,
       Any SteelSeries mouse,
       Any Xbox Controllers,
       And an explicitly defined device with ID 1425:5769.

`-PCI 'Realtek|NVIDIA|10ec:8168'`
   If set, the script enumerates the regex for PCI devices and generates qemu arguments for them... but also rebinds them to the vfio-pci driver.
   Then generates arguments for the VM's runtime.
     This example would catch any attached:
       Any Realtek PCI devices
       Any NVIDIA devices (Including children of the GPU like the audio card and USB-C controller)
       And an explicitly mentioned PCI Device with ID 10ec:8168.

`-taskset 0,1,2,3,4,5,6`  / `-taskset 0,2,4,8`
   This taskset argument takes a comma delimited list of host threads and only lets the VM run on those.
   If you've configured core isolation on the host you'll want to specify this argument in conjunction."
     This also calculates the cores/threads for the guest during a session.
       e.g.
       The argument: 0,1,2,3 would give the guest 2 cores of 2 threads each (4 total) only executing on those 4 specified threads of the host."
       However     : 0,2,4   would give the guest 3 cores of 1 thread  each (3 total) only executing on those 3 specified threads of the host."

`-run`
  Actually run. The script always dry-runs without -run.
    Without -run the script shows all matched USB/PCI devices and it's finished QEMU arguments.
    Requiring this flag makes for a good safety net to test my REGEXs before rebinding PCI devices and actually starting the VM.

### Script Notes and Gotchas

  - The absolute minimum requirement to get started is the `-image` and `iso` arguments.
    If OVMF is automatically detected this will start the VM in a regular window with no passthrough. 
  - The default QEMU user-mode networking will also be used (which will NAT through your desktop's existing IP).
  - This script also makes use of VirtIO, you may wish to install the drivers into the guest ahead of time.
  - If you do not pass in any -usb or -pci arguments the VM will run in a window on your Linux desktop.
      This is useful for installing the OS, drivers or general debugging without without GPU acceleration.
  - The CPU topology is 'host' by default, so the VM will copy your host's cpu model.
      This script also passes through ALL host cores and threads by default, giving your VM all the host cores/threads to work with.
      You can use -taskset to limit and set what threads the guest is allowed to execute on.
        If your host doesn't have the headroom for a gaming guest making the VM stutter; Consider Core Isolation by
        adding the isolcpus=w,x,y,z option to the host's boot parameters.
        After adding it and rebooting it one can specify the `-taskset w,x,y,z` argument so the VM will only execute on those threads too.
        This is very useful if the host has enough load to interupt the VM during normal operation.

## Got any example runs?

Note: I have omitted `-run` from all of these. Running without -run is a dry-run

If you aren't ready to do any passthrough and just want to start the VM in a regular window (Installation, Drivers, etc.):
  `sudo ./main -image /root/windows.img,format=raw -cdrom /data/Win10Latest.iso`

If a host has been booted with isolated cores you can tell the script to pin the guest to those only:
  `sudo ./main -image /root/windows.img,format=raw -taskset 0,1,2,3,4,5`
  This example starts the VM with only host threads 0 to 5 (The first 3 cores on a multi-threaded host)
  Very useful if a VM experiences stuttering from host load.

An example run with passthrough could look like:
  `sudo ./main -image /dev/zvol/poolName/windows,format=raw -bridge br0,enp4s0,tap0 -usb 'SteelSeries|Audio-Technica|Holtek|Xbox' -pci 'NVIDIA'`
  This example would  would (if seen) pass all regex-matching USB and PCI devices and rebind the PCI devices if applicable.
It would also provision network bridge br0 and attach tap0 to the bridge with your host interface. Then give tap0 to the VM.
