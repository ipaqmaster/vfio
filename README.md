# vfio

## What is this
This bash script (Among other small things) takes optional USB and PCI passthrough arguments to dynamically generate arguments for 'qemu-system_x86-64'. rebind's all matched PCI devices to the vfio-pci driver for run time. Then undoes it and returns me to lightdm's login screen after VM shutdown. It isn't perfect but I hope to continue improving on it over time.

I made this script so I can start a gaming VM for the few stubborn titles out there. It leaves my host headless during runtime and reprobes the nvidia drivers after the VM shuts down so I get sent back to my login screen. With a second GPU present, using the Looking Glass project would be easily possible.

Got this working on my beloved Sabertooth X79 with a 3930k Intel CPU. And now also on my new build with an Aorus x570 Motherboard and a Ryzen 9 3900X AMD CPU.

## Why

Short: Modern VFIO/IOMMU Support have made using both sides of the gaming coin easy; And even better supported on this generation's motherboards, I've found.

Moderate:
Linux systems, networks and administration of both are a large part of my occupation and maybe even a hobby. I've opted for an Archlinux (root on ZFS) install for a while now and is today the setup of choice for any desktop environment I use.

WINE and Proton have gotten me far for many great titles the past few years but sometimes I'm too busy to spend the time.. or worse encounter a title which definitely cannot run on Linux.

Let alone some titles (while amazing!) which employ third party Anti-Cheat services. And while that's fine.. Driver level anti-cheats like BattlEye and Easy Anti-Cheat aren't something you can justthrow at WINE; leaving you stuck in Single Player experiences for those titles or the worst case, not running at all.

Shortest: iommu go brr

## The script, arguments and examples

### About using it

The absolute minimum requirement is the `-image` argument. This will only start the VM just on your desktop in the current X session. The default QEMU user-mode networking will also be used (which will NAT through your desktop's existing IP). This is typically what you'd run during the installation stage with the -iso flag, too.

If you specify any USB devices their arguments will be generated for the qemu-system-x86_64 command. They're a lot easier to throw around than PCI devices.

If you specify any PCI devices they will be unbound from their drivers and re-bound to 'vfio-pci' first, then will have their qemu-system arguments generated.

### The full argument list [and examples] (For now)

  -iso /path/to/a/diskimage.iso
     If set, we will attach it with qemu's -cdrom parameter.

  -image /dev/zvol/zpoolName/windows,format=raw
     If set, we will attach this disk qemu's -drive parameter.

  -bridge br0,enp4s0,tap0
     Creates bridge br0 and interface tap0 then attaches tap0 and enp4s0 to br0.
     Clones mac of real interface enp4s0 onto br0 and uses dhclient to get an IP on br0. (I do this to keep my linux dhcp reservation at home)
     Stops/starts networkmanager if found to be running
     if argument not specified, the default qemu nat adapter will be used.
     
  -memory 8192
     Sets the memory in megabytes for this guest. If unspecified the default is half of the host total.

  -USB 'AT2020|SteelSeries|Holtek|Xbox'
     If set enumerates through the specified regex for usb devices using 'lsusb' and generates qemu arguments for them.

### Any examples to get a quick idea?

An example run could look like:
  sudo ./main -image /root/windows.img,format=raw -bridge br0,enp4s0,tap0 -usb 'SteelSeries|Audio-Technica|Holtek|Xbox' -pci 'NVIDIA'
  
  This would create br0, create and attach tap0, slave enp4s0 (Host network card) to the bridge, copy the mac of enp4s0 to br0 and dhcp. Then make usb and PCI arguments while rebinding the PCI devices to vfio. Then start the machine with half of your host's memory and all of the CPU threads.
  
  This example regex sees my SteelSeries mouse, AT2020 USB Microphone/DAC, My Ducky usb keyboard (Holtek chipset) and any attached Xbox controllers/receivers it sees during this run. They all go to the Windows guest during runtime.
