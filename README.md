# vfio

## What is this

A bash script that starts my Win10 VM directly with `qemu-system-x86_64` but automatically handles optional network bridging, hugepage allocation, USB passthrough arguments and PCI device rebinding + arguments (+ rebinding back to drivers when done) for minimizing my headaches.

It makes starting the Win10 vm quick and easy then sends me back to the lightdm login screen once it shuts down.
Hoping the script can be helpful to others as I continiously tinker with it. Plan to add dual GPU support (one for host, one for guest) once I dust my old PC off.

## What does it do

It starts a VM using qemu-system-x86_64 directly but it also:

  Takes a regular expression of PCI and USB devices to pass to the VM when starting it. Generates qemu arguments for both.

  Automatically unbinds specified PCI devices from their current driver and attaches them to the vfio-pci driver. (without any need for driver blocking or early vfio binds in the boot options)
  Then rebinds them to the driver they were originally used by after VM shutdown.

  Optionally makes a network bridge on the host during VM runtime; Giving the VM its own Layer 2 mac-address presence on the existing home LAN.
  (Useful for setting a DHCP reservation, connecting to services running on the VM such as RDP, avoiding host-NAT nightmares)
  
  It can optionally pin the VM's qemu process to specific host CPU threads
    (Useful if core isolation is configured in the host's boot parameters or have a cpu-set defined for improved VM performance)
    
  On VM exit it rebinds PCI devices back to their original drivers and starts your display-manager back up if it were running.

## What hosts and installs are supported?

This is an ongoing discovery but typically today's modern boards are going to be fine. As long as your motherboard has virtualization support and preferrably IOMMU on the motherboard for best performance it seems to work.

This script has worked for me this year using Archlinux.
I play Overwatch on it a lot and as for performance: If the game were presented to me without context I wouldn't be able to tell it's a VM. The fps and input latency has seriously been great.

On Archlinux, it's worked on my two below hardware configurations however I'm certain other distros and hardware configurations will work too.

# Why

WINE and Proton have gotten me far for the past few years but sometimes:
  1. Lacking the time to help a stubborn title run,
  2. A title is known not to work despite the efforts of Proton or Wine,
  3. A title employs a driver-level Anti-Cheat solution (which you cannot just throw at WINE) which leaves a VM as the next best option.

Modern IOMMU Support has made playing incompatible titles with ease.


With a second GPU present the Looking Glass project could be implemented; leaving the VM headless instead. (This flag is being worked on)

# The script, arguments, examples and an installation example

## General usage arguments

`-image /dev/zvol/zpoolName/windows -imageformat raw`

   If set - attaches a flatfile, partition, whole-disk or zvol to the VM with QEMU's -drive parameter.
   -imageformat is optional and will apply to the most recent -image argument specified.
   -image and -imageformat can be used multiple times to add more disks.

`-iso /path/to/a/diskimage.iso`

   If set attaches an ISO to qemu with an incrementing index id. Can be specified as many times needed for multiple CDs. Good for liveCDs or installing an OS with an optional driver-cd.

`-bridge br0,tap0	(Attach vm's tap0 to existing br0)`

`-bridge br0,tap0,eth0	(Create br0, attach vm's tap0 and host's eth0 to br0, use dhclient for a host IP.)`

   Takes a bridge name, interface and tap interface name as arguments.
   
   Using example 1:
   
1. Checks br0 exists first.
     
2. Creates tap0 for the vm as usual and attaches it to the pre-existing br0 (No dhclient, assumes pre-existing bridge is configured)
     
3. During cleanup unslaves and deletes tap0.
     
Using example 2:
   
1. Creates br0 + tap0.
     
2. Slaves tap0 and eth0 to br0.
     
3. Copies the mac from eth0 to the br0 (To preserve any DHCP Reservation in a network)
     
4. Removes any lingering IPs from eth0. (flush)
     
5. Brings all 3 up and runs dhclient on br0
     
6. During cleanup, unslaves the interface and deletes br0+tap0. Restores NetworkManager if it were found to be running.
     
   If this argument isn't specified the default qemu NAT adapter will be used
    (NAT may be desirable for some setups)
     
`-memory 8192M` / `-memory 8G` / `-mem 8G`

   Set how much memory the VM gets for this run. Argument assumes megabytes unless you explicitly use a suffix like K, M, or G.
     If this argument isn't specified the default value is HALF of the host total.

`-hugepages / -huge`

   Try to mount (if not already) and allocate some hugepages based on the VM's total memory defined with -memory (or default).
   If successful, qemu is given the arguments to use it. Gets unallocated after VM exit in the cleanup routine.

`-hyperv`

   Enable hyper-v enlightenments for nested virtualization. For some cases this may help convince more invasive Anti-cheats to play along. You will need to enable (tick) the HyperV Windows Feature and reboot when it asks before this will work though.

`-bios '/path/to/that.fd'`

   An optional bios path. If not set the script will try `/usr/share/ovmf/x64/OVMF_CODE.fd` if available.

`-usb 'AT2020USB|SteelSeries|Ducky|Xbox|1425:5769'`

   If set, the script enumerates `lsusb` with this regex and generates qemu arguments for passing them through when the VM starts.

This example would catch any:
     
1. Audio-Techinica AT2020 (USB Microphone+headphone DAC)

2. SteelSeries mouse,

3. Xbox Controllers,

4. Ducky brand keyboard.

5. A USB device with ID `1425:5769`, whatever that may be.

`-pci 'Realtek|NVIDIA|10ec:8168'`

   If set, the script enumerates `lspci` and generates arguments like the above. But also unbinds them from their current drivers (If any) and binds them to vfio-pci. Remembers what they were beforehand for rebinding after the VM shuts down.
   
This example would catch any:
     
1. PCI devices by Realtek
       
2. NVIDIA cards (Including children of the GPU like the audio card and USB-C controller)
       
3. A PCI device with ID `10ec:8168`.

`-taskset 0,1,2,3,4,5` / `-taskset 0,2,4,8`

   The taskset argument will take the threads you give it and only lets the VM execute on those threads. It also creates only that many threads on the VM. (6 and 4 in the examples respectively)
   This can significantly reduce latency if the guestis having trouble, even if you haven't configured any host pinning.

`-colortest`

  A quick terminal color test then exits.

`-iommugroups` / `-iommugrouping`

  Prints IOMMU groupings if available then exists.

`-extras '-device xyz -device abc -device ac97 -display gtk -curses'`

   If set adds extra arbitrary commands to the cmdline of qemu (Once invoked)
   Useful for `-device ac97` to get some quick and easy audio support if the host is running pulseaudio.
   
`-run`

  Actually run. The script runs dry by default and outputs qemu arguments and environment information without this flag.
  Especially useful for testing PCI regexes without unbinding things first try, but good for general safety.

## Notes and Gotchas.
  - If you don't set any `-usb` or `-pci` arguments the VM will run in a window on your desktop as is normal for Qemu. Useful for testing the VM actually boots, installing OSes or using liveCDs.
    - If you don't have $DISPLAY set the guest will run headless but the terminal will attach to the guest's serial. Make sure you put something like console=ttyS0 in the guest boot arguments if you actually want to interact with it while headless.
  - The absolute minimum requirement to get started is the `-image` and `-iso` arguments with OVMF available. You can install an OS, VirtIO+Nvidia drivers if needed, and have it ready for a passthrough on the next boot.
  - The default networking mode is QEMU's user-mode networking (NAT through host IP).
    - It's fine but if you want to talk to the guest from the outside you'll want to consider using `-bridge`.
  - This script makes use of VirtIO for networking. Unless you're passing through a USB/PCI network adapter, you'll want to install the VirtIO drivers into the guest. (e.g. Boot into the Windows ISO to install, then reboot the VM this time with the VirtIO driver iso attached)
    - The CPU topology is 'host' by default. The VM will think it has the host's CPU model.
  - By default the VM's CPU topology uses ALL host cores and HALF the host's total memory
      You can use -taskset to cherrypick host threads for the VM to execute on, it will also set the VM's threadcount appropriately to match.
        This is very useful if the host has enough load to interupt the VM during normal operation.
        If your host doesn't have the cpu load headroom for a gaming guest or the VM experiences stuttering, Consider using -taskset to isolate guest cores.
        
## Getting started with a fresh Win10 install

I recommend starting the install as an X window then doing passthrough once the guest is ready, however some GPU setups aren't phased by the guest having no drivers in certain scenarios allowing you to pass through your devices from the beginning and install all the drivers from inside the VM *during* GPU Passthrough if desired.

The below instructions will just use an X window in your display-manager for setting things up.

1. Get the latest virtio ISO as drivers for the VM: https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/archive-virtio/

2. Get the latest Win10 ISO from Microsoft: https://www.microsoft.com/en-au/software-download/windows10ISO

3. Create storage for your VM, this may involve commands like the below:

     `qemu-img create -f qcow2 myWin10VM.qcow2 100G # classic sparse qcow2`

     `dd if=/dev/zero of=myvm.img bs=1G count=100   # Preallocated raw example with DD`

     `zfs create -V100G myPool/myVMDisk             # zfs backed virtual block-device (ZVOL)`

4. Start the script following something like the below example:

     `./main -image /dev/zvol/myPool/myVMDisk -imageformat raw -iso ~/Downloads/Win10_20H2_v2_English_x64.iso -iso /nas/common/ISOs/virtio-win-0.1.189.iso`

5. Have your serial key ready to install Windows and if it can't see the virtual drive you specified with -image just load the drivers from the virtio ISO you also passed through.

6. Once at your Windows VM's desktop, Install VirtIO so features like networking can kick in. Also install the video drivers for your card (Such as Nvidia), and any others you might need.

7. Shut the VM down and try again without the ISOs and try using -pci to pass through some devices from the host (and optional -usb arguments if you aren't already passing the entire pci usb controller too)

## Examples

Note: I've omitted `-run` from these so they remain a dry-run.

If you aren't ready to do any passthrough and just want to start the VM in a regular window (Installation, Drivers, etc.):
  `./main -image /root/windows.img,format=raw -cdrom /root/Win10Latest.iso`

If a host has been booted with isolated cores you can tell the script to pin the guest to those only:
  `./main -image /root/windows.img,format=raw -taskset 0,1,2,3,4,5`
  
  This example starts the VM with only host threads 0 to 5 (The first 3 cores on a multi-threaded host)
  Very useful if a VM experiences stuttering from host load.

An example run with passthrough could look like:
  `./main -image /dev/zvol/poolName/windows,format=raw -bridge br0,eth0,tap0 -usb 'SteelSeries|Audio-Technica|Holtek|Xbox' -pci 'NVIDIA'`
  
  This example would  would (if seen) pass all regex-matching USB and PCI devices and rebind the PCI devices if applicable.
It would also provision network bridge br0 and attach tap0 to the bridge with your host interface. Then give tap0 to the VM.
