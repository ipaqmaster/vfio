# vfio

A script for me to start a gaming VM with a single GPU; Leaving the host headless until the VM shuts down, returning me to lightdm's login screen.

Takes optional USB and PCI passthrough arguments to dynamically generate arguments for 'qemu-system_x86-64'. rebind's all matched PCI devices to the vfio-pci driver for run time.

Unbinds unbinds PCI devices again when the VM process exits then reprobes the host's nvidia driver before starting lightdm back up removing the need for a reboot when swapping between Linux and the VM.


Had this working on my beloved Sabertooth X79 motherboard with a 3930k Intel CPU. And now also on my new build with an Aorus x570 Motherboard and a Ryzen 9 3900X AMD CPU.

An example run:
  sudo ./main -image /root/windows.img,format=raw -bridge br0,enp4s0,tap0 -usb 'SteelSeries|Audio-Technica|Holtek|Xbox' -pci 'NVIDIA' 

  Builds arguments for USB and PCI devices found in their regular expression's. 
  The script automatically unbinds all PCI matches from their drivers before rebinding them to vfio-pci.

  The guest gets all CPU Cores and 2 threads each and 50% of the host's total memory when option -memory is omitted.

  Upon the guest shutting down (qemu-system-x86_64 exiting) it will attempt to unbind the NVIDIA card again, reprobe the nvidia drivers on the host before starting lightdm and taking me back to the login screen.

It's not perfect yet and I hope to continue improving on this as time goes, but hopefully someone finds it useful for now.
