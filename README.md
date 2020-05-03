# vfio

A script for me to start my Windows 10 gaming VM with optional USB and PCI passthrough functions to dynamically generate the arguments for qemu-system_x86-64 and automatically rebind found PCI devices to the vfio_pci driver instead.

Also unbinds PCI devices again when the VM process exits and reprobes the host's nvidia driver before starting lightdm back up removing the need for a reboot when swapping between Linux and the VM.
