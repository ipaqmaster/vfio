# vfio

##What is this
This bash script starts a VM but takes care of generating arguments for qemu-system-x86_64 beforehand. Among other steps.

## What does it change
It supports an optional regular expression of USB and PCI devices as arguments to generate qemu arguments inclusively.

It Automatically rebinds PCI devices to the vfio-pci driver based on what it finds with your regular expression.

It can make a network bridge for VM runtime to give it a real presence on the LAN if the default NAT adapter doesn't satisfy your networking needs.

When the VM shuts down and the qemu process ends.. the script reprobes the nvidia drivers and restores the host's virtual-console's, then re-launches your display-manager of choice.

## What's supported?
This script has worked for me day to day for the past few months with Archlinux on the below hardware configurations:
  - My now-retired Sabertooth X79 Motherboard (Intel i7 x3930K CPU)
  - My current     Aorus x570 Motherboard     (AMD Ryzen 9 3900X CPU)

# Why
WINE and Proton have gotten me far for many great titles the past few years but sometimes I'm too busy to spend the time.. or worse encounter a title which definitely cannot run on Linux.

Modern VFIO/IOMMU Support has made using both sides of the gaming coin plausible and with improved performance on the current generation's motherboards.

I made this so I could participate in the few stubborn titles out there with ease. It leaves my host running, SSHable, pingable and headless; then returns me to my display manager's login screen once the VM shuts down. All that rebinding and SSHing in from the laptop to restore X inspired me to make this management script so any future passthrough changes become a breeze.

With a second GPU present using the Looking Glass project is possible, leaving the VM headless instead.

This script isn't perfect but I hope to continue improving on it.


Let alone some titles (while amazing!) which employ third party Anti-Cheat services. And while that's fine... Driver level anti-cheats like BattlEye and Easy Anti-Cheat aren't something you can throw at WINE; leaving you stuck in Single Player experiences for those titles or the worst case, not running at all.

# The script, arguments, and examples

## About using it

The absolute minimum requirement to get started is the `-image` and `iso` arguments. This will only start the VM with a new window in your X session.
The default QEMU user-mode networking will also be used (which will NAT through your desktop's existing IP).

This script makes use of some virtio features you may need to download the VirtIO drivers for the guest to make use of the network interface.

## Arguments this script will take [and examples]

`-iso /path/to/a/diskimage.iso`

   If set - attaches it with qemu's -cdrom parameter.

`-image /dev/zvol/zpoolName/windows,format=raw`

   If set - attaches it with qemu's -drive parameter.

`-bridge br0,enp4s0,tap0`

   Takes three arguments; A bridge, a real interface, and a tap interface to bind to the Guest.
   Creates the bridge and the tap then slaves both the tap and the real interface to the bridge. Turns them all on and runs dhclient on the bridge.
   
   It also clones the MAC Address of the real interface onto br0. I do this to keep my Linux DHCP reservation at home.
   
   If NetworkManager is found to be running it is stopped during runtime and restored after the bridge is destroyed at the end.
   
   If this argument isn't specified the default qemu NAT adapter will be used.
     
`-memory 8192`

   Sets the memory for this guest in megabytes (Unless explicitly specified with suffixes K, M, or G).
   If this argument isn't specified the default value is half of the host total.

`-bios '/path/to/that.fd'`
   An optional bios path. The default path is '/usr/share/ovmf/x64/OVMF_CODE.fd'

`-USB 'AT2020USB|SteelSeries|Holtek|Xbox|1425:5769'`

   If set enumerates through the specified regex for USB devices using 'lsusb' and generates qemu arguments for them.

`-PCI 'Realtek|NVIDIA|10ec:8168'`
   A regex for lspci parsing. Same idea as the -USB flag but 
   This example will unbind any Nvidia, Realtek cards, and any matching device with ID '10ec:8168' from their drivers and rebind them to vfio-pci.
   Then generates arguments for the VM's runtime.

## Some example runs

An example run could look like:
  `sudo ./main -image /root/windows.img,format=raw -bridge br0,enp4s0,tap0 -usb 'SteelSeries|Audio-Technica|Holtek|Xbox' -pci 'NVIDIA'`
  
  This would create and configure the bridge; Make USB and PCI arguments while rebinding the PCI devices to vfio.. and then start the machine with half of your host's memory and all of the CPU cores attached.
  
  This USB regex example will find any SteelSeries mouse, The model AT2020USB Microphone/Headset unit, My Ducky usb keyboard (Holtek chipset) and any attached Xbox controllers/receivers it sees during this startup phase. They all go to the Windows guest during runtime.
  
  The PCI one only has 'NVIDIA'. When checking `lspci`, this will see the GPU itself and (If the model has them) any extra child devices on the card such as the Audio Controller, USB3.1 Host Controller, passing all of them to the guest with that one regex search.
  
## Key Notes
  - The CPU topology is 'host' by default, so the VM will copy your host's cpu model.
  - This script passes through all host cores and threads=2 so a VM will get all 12 cores with 2 threads each showing 24 total when running,
      If your host doesn't have the CPU Load headroom with very few cores to spare -- performance may take a hit.
      Anyone in this situation should consider a core-isolation approach.
  - If you do not pass in any -usb and -pci arguments, the final command will run in a window in your display manager.
      This is good for debugging VM problems, provisioning or just installing the OS for the first time.
  - This uses some VirtIO devices so it would be best to install those drivers on your VM ahead of time.
