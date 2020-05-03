# What is this
This bash script starts a VM.

You can optionally specify a regex of USB and PCI devices. It will generate qemu arguments for them and automatically unbind/rebind the PCI devices to vfio-pci where it can. When the VM exits it attempts to reprobe the nvidia drivers start lightdm for a login screen. It can also make a network bridge on the host making the VM LAN accessible with it's own presence.

I made this so I could participate in the few stubborn titles out there. During PCI passthrough on my machine it leaves the host headless. Once the VM shuts down (exits) the script reprobes the nvidia drivers and starts lightdm back up.

With a second GPU present; using the Looking Glass project would be very achievable.

It isn't perfect but I hope to continue improving on it over time.

# Why

Short: Modern VFIO/IOMMU Support have made using both sides of the gaming coin easy; And even better supported on this generation's motherboards, I've found.

Moderate:
Linux systems, networks and administration of both are a large part of my occupation and maybe even a hobby. I've opted for an Archlinux (root on ZFS) install for a while now and is today the setup of choice for any desktop environment I use.

WINE and Proton have gotten me far for many great titles the past few years but sometimes I'm too busy to spend the time.. or worse encounter a title which definitely cannot run on Linux.

Let alone some titles (while amazing!) which employ third party Anti-Cheat services. And while that's fine.. Driver level anti-cheats like BattlEye and Easy Anti-Cheat aren't something you can justthrow at WINE; leaving you stuck in Single Player experiences for those titles or the worst case, not running at all.

Shortest: iommu go brr

# The script, arguments and examples

## About using it

The absolute minimum requirement to get started is the `-image` and `iso` arguments. This will only start the VM with it's own little window in your X session. The default QEMU user-mode networking will also be used (which will NAT through your desktop's existing IP).

Because this script makes use of some virtio features you may need to download the VirtIO drivers for the guest to make use of the network interface.

If you specify any USB devices their arguments will be generated for the qemu-system-x86_64 command. They're a lot easier to throw around than PCI devices.

If you specify any PCI devices they will be unbound from their drivers and re-bound to 'vfio-pci' first, then will have their qemu-system arguments generated.

## Currently accepted arguments [and examples]

`-iso /path/to/a/diskimage.iso`

   If set, attaches it with qemu's -cdrom parameter.

`-image /dev/zvol/zpoolName/windows,format=raw`

   If set, attaches it disk qemu's -drive parameter.

`-bridge br0,enp4s0,tap0`

   Creates bridge br0 and tap0 then attaches both tap0 with enp4s0 to br0.
   
   Clones mac of real interface enp4s0 onto br0 and uses dhclient to get an IP on br0.
   (I do this to keep my linux dhcp reservation at home)
   
   Stops/restarts networkmanager if found to be running during VM operation.
   
   if argument not specified, the default qemu NAT adapter will be used.
     
`-memory 8192`

   Sets the memory for this guest in megabytes (Unless explicitly specified with suffixes K,M or G).
   If unspecified the default value is half of the host total.

`-USB 'AT2020|SteelSeries|Holtek|Xbox|1425:5769'`

   If set enumerates through the specified regex for usb devices using 'lsusb' and generates qemu arguments for them.

## Any examples to get a quick idea?

An example run could look like:
  `sudo ./main -image /root/windows.img,format=raw -bridge br0,enp4s0,tap0 -usb 'SteelSeries|Audio-Technica|Holtek|Xbox' -pci 'NVIDIA'`
  
  This would make and configure the bridge interface. Make usb and PCI arguments while rebinding the PCI devices to vfio. Then start the machine with half of your host's memory and all of the CPU threads.
  
  The USB regex is capable of finding a SteelSeries mouse, AT2020 USB Microphone/DAC, My Ducky usb keyboard (Holtek chipset) and any attached Xbox controllers/receivers it sees during this run. They all go to the Windows guest during runtime.
  
  The PCI one only has 'NVIDIA'. When running `lspci` this will see the GPU itself and (If the model has them) three children devices such as the Audio Controller, USB3.1 Host Controller and the parent Type-C UCSI Controller, passing all of them to the guest in one regex specification.
  
 ## Key Notes
  - This is only capable of starting `lightdm` at the moment. Anyone using a different display manager will need to manually do so in their ctrl+alt+f2 tab after the reprobe happens. I will add better automatic DM management soon.
  - The CPU topology is 'host' by default, so the VM will copy your host's cpu model.
  - If '-memory 12345' is omitted it'll just give half of what the host has. (32G host = 16G guest)
  - If '-bios /path/to/that.fd' is omitted the script defaults to '/usr/share/ovmf/x64/OVMF_CODE.fd'
  - This script passes through all host cores and threads=2 so a VM will get 12 cores with 2 threads each (24 total) on a run.
      If your host doesn't have the headroom with few cores to spare performance may take a hit. People in this situation should consider core isolation.
  - If you do not pass in any -usb and -pci arguments, the final command will run in a window in your display manager.
      This is good for debugging VM problems, provisioning or just installing the OS for the first time.

# Anything else?

I got this working on my beloved Sabertooth X79 with a 3930k Intel CPU and have since upgaded to an Aorus x570 Motherboard and a Ryzen 9 3900X AMD CPU. Even though it's not perfect yet, I'm glad I put the time into it to automate most of the annoying steps and make it dynamic enough to handle hardware changes easily.
