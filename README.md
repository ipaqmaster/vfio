# vfio

## What is this

I made this bash script to start my Win10 VM with automatically generated qemu arguments based on the guidelines I pass in.

It saves me loads of time swapping between Linux and VM for gaming and I hope it can help someone else.

## But what does it do

It starts a VM using qemu-system-x86_64 directly but it also:

  Takes a regular expression of PCI and USB devices to pass to the VM when starting it.

  Automatically unbinds specified PCI devices from any driver attached to vfio-pci without having to put blacklists or early binds in the boot options.

  Optionally makes a network bridge on the host during VM runtime; Giving the VM its own IP, MAC and DHCP entry in your router. a 'real' [Layer 2] presence on your LAN.
  (Useful if the default NAT adapter doesn't your VM networking needs)

  It can optionally pin the VM's qemu process to specific host CPU threads
    (Useful if I've set up core isolation in the host's boot parameters or have a cpu-set defined for improved VM performance)

  When qemu exits (VM shutsdown) the script reprobes the nvidia drivers and brings the display-manager back to a login screen with no reboot.

## What hosts and installs are supported?

This is an ongoing discovery. This script has worked for me this year using Archlinux.
I play Overwatch on it a lot and as for performance: If the game were presented to me without context I wouldn't be able to tell it's a VM. The fps and input latency has seriously been great.

On Archlinux, it's worked on my two below hardware configurations however I'm certain other distros and hardware configurations will work too.

  - My now-retired Sabertooth X79 Motherboard (Intel i7 x3930K CPU)
  
  - My current     Aorus x570 Motherboard     (AMD Ryzen 9 3900X CPU)

While the VM runs and my host goes headless.. I can still SSH into it, mount steamapps over NFS, X11 forward programs and more. So it's been good.

# Why

WINE and Proton have gotten me far for the past few years but sometimes I don't have the time to get a stubborn Title running or worse:
  1. A title is known to nor work with Proton or WINE regardless.
  2. A title employs a driver-level Anti-Cheat solution (which you cannot just throw at WINE) which leaves a VM as the next best option.

Modern IOMMU Support has made playing incompatible titles with ease.


With a second GPU present the Looking Glass project could be implemented; leaving the VM headless instead. (This flag is being worked on)

# The script, arguments, and examples

## Arguments this script will take [and script Gotchas]

### Arguments

#### Minimum argument requirements

`-image /dev/zvol/zpoolName/windows,format=raw`

   If set - attaches a flatfile, partition, wholedisk or zvol to the VM with QEMU's -drive parameter.

#### Optional

`-iso /path/to/a/diskimage.iso`

   If set - attaches an ISO with QEMU's -cdrom parameter.

`-bridge br0,enp4s0,tap0`

   Takes a bridge name, interface and tap interface name as arguments.
   Using this example it:
     1. Creates br0 + tap0.
     2. Slaves tap0 to br0 with enp4s0.
     3. Copies the mac from enp4s0 to the br0 (To preserve any DHCP Reservation in a network)
     4. Removes any lingering IPs from enp4s0. (flush)
     5. Brings all 3 ints up.
     6. And finally runs dhclient on br0.

   If NetworkManager is found to be running it gets stopped during bridging and started back up after the bridge is destroyed once the VM shuts down.
   
   If this argument isn't specified the default qemu NAT adapter will be used
    (NAT may be desirable for some setups)
     
`-memory 8192M` / `-memory 8G` / `-mem 8G`

   Set how much memory the VM gets for this run. Argument assumes megabytes unless you explicitly use a suffix like K, M, or G.
     If this argument isn't specified the default value is HALF of the host total.

`-bios '/path/to/that.fd'`
   An optional bios path.
     If not set, the script tries to use '/usr/share/ovmf/x64/OVMF_CODE.fd' if available.

`-USB 'AT2020USB|SteelSeries|Ducky|Xbox|1425:5769'`

   If set, the script enumerates lsusb with this regex and generates qemu arguments for them to run with.
     This example would catch any attached:
       Any Audio Techinica AT2020 (USB Microphone+headphone DAC)
       Any SteelSeries mouse,
       Any Xbox Controllers,
       Any Ducky brand keyboard.
       And an example explicitly defined device with ID 1425:5769.

`-PCI 'Realtek|NVIDIA|10ec:8168'`
   If set, the script enumerates lspci with this regex not only generating qemu arguments the matched PCI devices, but also rebinding them to the vfio-pci driver for you.
     This example would catch any attached:
       Any PCI devices by Realtek
       Any NVIDIA cards (Including children of the GPU like the audio card and USB-C controller)
       And an example expicitly defined device with ID 10ec:8168.

`-taskset 0,1,2,3,4,5,6`  / `-taskset 0,2,4,8`
   This taskset argument takes a comma delimited list of host threads and only lets the VM run on those.
   If you've configured core isolation on the host you'll want to specify this argument in conjunction."
     This also calculates the cores/threads for the guest during a session.
       e.g.
       The argument: 0,1,2,3 would give the guest 2 cores of 2 threads each (4 total) only executing on those 4 specified threads of the host."
       However     : 0,2,4   would give the guest 3 cores of 1 thread  each (3 total) only executing on those 3 specified threads of the host."

`-run`
  Actually run. The script dry-runs without -run.
    This is good for looking at what your USB/PCI regex argument will find.
    Requiring this flag is also good for general safety.

### Useful Notes and Gotchas

  - The absolute minimum requirement to get started is the `-image` and `iso` arguments. While OVMF is installed.
    This starts the VM in a regular window where you can install Windows, VirtIO and NVIDIA drivers without worrying about PCI passthrough just yet.
  - The default QEMU user-mode networking will also be used (NAT through desktop). This is fine but if you want to talk to the guest from the outside you'll want to try the `-bridge` flag.
  - This script makes use of VirtIO devices, you may wish to install the drivers into the guest ahead of time unless you're passing through a USB/PCI network adapter.
  - If you don't pass in any -usb or -pci arguments the VM will run in a window on your Linux desktop. Useful for initial installation.
  - The CPU topology is 'host' by default, so the VM will copy your host's cpu model.
      This script also passes through ALL host cores and threads by default, giving your VM all the host cores/threads to work with.
      You can use -taskset to limit and set what threads the guest is given and permitted to run on.
        This is very useful if the host has enough load to interupt the VM during normal operation.
        If your host doesn't have the headroom for a gaming guestor the VM stutters; Consider using taskset for core isolation.
        
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
