# vfio

## About it

This is a bash script I've made to start virtual machines by calling `qemu-system-x86_64` directly but it automatically handles optional network bridging, hugepage allocation, USB passthrough arguments, PCI passthrough arguments complete with automatic driver rebinding and other scenarios useful for gaming or other tinkering. It's been great for minimizing my headaches.

It makes starting a Win10 vm for gaming quick and easy then sends me back to the lightdm login screen once the VM shuts down after returning all devices back to their driver. I'm Hoping the script can be helpful to others as I continue to tinker with it. I've even pulled out the old PC with two GPUs just to play with and add Looking Glass support to the script.

## What does it do

This script starts a VM using qemu-system-x86_64 directly but it can optionally:

  * Give you a good rundown of what it's about to do in dry mode (Default) without -run, also printing the QEMU arguments it would've used.

  * Include virtual disks and any ISOs you may wish to boot with

  * Take a regular expression of PCI and USB devices to pass to the VM when starting it.

  * Automatically generate qemu arguments for PCI and USB matches while automatically unbinding matched PCI devices from their current driver and attaching them to the vfio-pci driver if not already done, without any need for driver blocking or early vfio binding at boot time.
  
  * Rebind PCI devices back to the driver they came from after the VM shuts down like it never happened and restart your display-manager if it were running.

  * Make a network bridge on the host during VM runtime or attach the VM to an existing network bridge; Giving the VM its own Layer 2 mac-address presence on the existing home LAN.
  (Useful for setting a DHCP reservation, connecting to services running on the VM such as RDP, avoiding host-NAT nightmares)
  
  * Pin the VM's vcpu qemu threads to specific host CPU threads to help avoid stutter.
    (Useful if core isolation is configured in the host's boot parameters or if it has an isolating cpu-set defined for improved VM performance)

  * Dynamically allocate hugepages for the VM, or use existing pages if enough are free and preallocated (such as, at boot time in kernel arguments)

  * Enable Looking Glass shared memory + spice keyboard/mouse input for when you have more than one GPU on the host and want to stay in your Linux environment.

  * Pass a romfile for any GPU pci devices being passed through

  * Include common HyperV enlightenments to either aid with performance in some scenarios or to help kernel-based Anti-Cheat agents play along.

  * And sometimes more.

## What hosts and installs are supported?

It seems any distribution running a modern Linux kernel, the latest qemu and all on a host with either Intel's VT-d or AMD-Vi (May just be labelled IOMMU in bios) appears suitable. And of course, don't forget to add the iommu arguments kernel's boot arguments. If you are not using Archlinux, you may have to manually specify the OVMF path using `-bios`, but that would be the worst of it. Confirmed working in Ubuntu 20.04 and 18.04 as well.

Even my partially retired desktop from 2011 with a 3930K CPU and x79 motherboard can run this script using a Looking Glass window into the guest in X with a GPU for the host.

On my latest May 2020 desktop upgrade (3900x, DDR4@3600, single 2080Ti, M.2 SSD) I play Overwatch, MK11, Battlefield 4 and more in a VM on this machine frequently. As for performance I genuinely cannot tell it's a VM (unless I verify in Device Manager of course). There's no stutters or any other telltale signs that its not a real computer; which I find to be particularly important in multiplayer titles.


# Why make this
The #0 reason is "fun" but while WINE and Proton have gotten me far over the past few years sometimes:
  1. I may lack the time to help a stubborn title run,
  2. A title may be known not to work in Linux despite best efforts,
  3. A title may employ a driver-level Anti-Cheat solution, completely borking the multiplayer experience in Linux (Which you can't just throw at WINE).

Furthermore, instead of using libvirtd and defining a Windows VM in a more "set and forget" attitude, I figured I'd write my own all-in-one manager so the addition, exclusion and modification of what I'm passing through is as easy as a quick argument change in my terminal to influence the next VM boot. In general, this script has been very useful in my tinkering even outside VFIO gaming and at this point I swear by it for quick and easy screwing around with vfio and more even just on the desktop.

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

`-hugepages / -huge / -hugepages /optional/mountpoint/to/custom/hugepage`

   Tries to allocate hugepages for the VM dynamically based on how much memory it will be given (defined with -memory). Hugepages for a VM with frequent random memory access such as in gaming can be much snappier than your regular process accessing regular memory.
   If no argument is given it'll use /dev/hugepages which is often 2MB per page. The script drops host memory cache and then compact_memory before allocating to aim for less fragmentation and will clean up after itself by setting pages back to 0 to reclaim memory for the host to use later if they weren't preallocated earlier.
   
   This flag also supports preallocation, so if you reserved some 1GB pages at boot time and mounted a pagesize=1G hugetlbfs to some directory, specifying that will skip the dynamic hugepgae allocation step above if there's enough free for the VM to use. Allocating hugepages at boot time sacrifices a lot of memory but doing it so early prevents fragmentation. Can be a lifesaver for performance.

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

`-pinvcpus 0,1,2,3,4,5` / `-pinvcpus 0,2,4,8`

   The taskset argument will take the threads you give it and only lets the VM execute on those threads. It also creates only that many threads on the VM. (6 and 4 in the examples respectively)
   This can significantly reduce latency if the guestis having trouble, even if you haven't configured any host pinning.

`-colortest`

  A quick terminal color test then exits.

`-iommugroups` / `-iommugrouping`

  Prints IOMMU groupings if available then exists.

`-looking-glass` / `-lookingglass` / `-lg`

  Adds a 64MB shared memory module for the Looking Glass project and a spice server onto the guest for input from host during Looking Glass usage.
  You will still need to go into your VM add the VirtIO IVSHMEM driver to the "PCI standard RAM Controller" which appears in Device Manager under System Devices before Looking Glass will function.

`-extras '-device xyz -device abc -device ac97 -display gtk -curses'`

   If set adds extra arbitrary commands to the cmdline of qemu (Once invoked)
   Useful for `-device ac97` to get some quick and easy audio support if the host is running pulseaudio.

`-romfile/-vbios /path/to/vbios.bin`
   Accepts a file path to a rom file to use on any detected GPU during -pci argument processing.
   You should check the vbios dump you're about to use is safe before using it on a GPU, rom-parser is a good project for this.
   Otherwise you can often download your model's vbios from TechPowerup and patch it with a project like NVIDIA-vBIOS-VFIO-Patcher before using it.
   
`-run`

  Actually run. The script runs dry by default and outputs qemu arguments and environment information without this flag.
  Especially useful for testing PCI regexes without unbinding things first try, but good for general safety.

## Notes and Gotchas.
  - If you don't pass through a graphics card and your $DISPLAY variable is set (The script looks for a VGA device to make a decision) the script will give the VM a virtual screen so you can actually see, just in a normal qemu popup window like any other on your desktop. This is useful for testing the VM actually boots before passing through hardware or to test OSes, liveCDs, other hardware configurations and so on.
  - The absolute minimum requirement to do anything useful started is the `-image` and/or `-iso` arguments with OVMF installed. You can install an OS, the VirtIO and Nvidia drivers if needed and have it ready for a passthrough on the next boot.
  - The default networking mode is QEMU's user-mode networking (NAT through host IP).
    - This is usually fine but if you want to talk to the guest from the outside, such as your local network you'll want to consider using `-bridge`.
  - This script makes use of VirtIO for networking. Unless you're passing through a USB/PCI network adapter and use `-nonet`, you'll want to install the VirtIO drivers into the guest before expecting virtual-networking to work.
  - The CPU topology is 'host' by default. The VM will think it has the host's CPU model.
  - By default the VM's CPU topology uses ALL host cores and HALF the host's total memory
      You can use -pinvcpus to cherry pick some host cpu threads for the VM to execute on and this will also set the VM's vcpu count appropriately to match.
        This is very useful if the host has enough load to interupt the VM during normal operation.
        If your host doesn't have the cpu load headroom for a gaming guest or the VM experiences stuttering, Consider using -pinvcpus to isolate guest cores.
        
## Getting started with a fresh Win10 install

I recommend starting the install as an X window then doing GPU passthrough once the guest is prepared. If your GPU of choice is already completely isolated since boot or your have a romfile to pass through with the GPU you could pass it through and include -romfile to do the VM's OS and driver installation with the GPU already passed through.

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
  `./main -image /root/windows.img,format=raw -pinvcpus 0,1,2,3,4,5`
  
  This example starts the VM with only host threads 0 to 5 (The first 3 cores on a multi-threaded host)
  Very useful if a VM experiences stuttering from host load.

An example run with passthrough could look like:
  `./main -image /dev/zvol/poolName/windows,format=raw -bridge br0,eth0,tap0 -usb 'SteelSeries|Audio-Technica|Holtek|Xbox' -pci 'NVIDIA'`
  
  This example would (if seen) pass all regex-matching USB and PCI devices and rebind the PCI devices if applicable.
It would also provision network bridge br0 and attach tap0 to the bridge with your host interface. Then give tap0 to the VM.
