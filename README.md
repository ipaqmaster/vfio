# vfio

## About this script

This is a bash script I've put a lot of love into trying to avoid defining VMs in libvirt with hardcoded host PCI addresses, among other virtualization test cases which it helps make very quick for me.

It starts a VM by calling `qemu-system-x86_64` directly but can automatically handle extra arguments all with the convenience of a terminal with history and the ability to just backspace something out if you don't want it in the guest.

It also happens to make Windows VM gaming a pinch on my single-gpu 2080Ti host and older dual-gpu host with Looking Glass. Now if only NVIDIA would *officially* support vGPUs onafaf  their consumer hardware...

## What does it actually do

It's a good question. On the surface it's just a qemu wrapper... But I swear by it for any VM/VFIO screwery because it also:

  * Gives a good rundown of all the extra things it's been asked to do in default 'Dry' mode so it doesn't wreak havoc without saying go(`-run`) first.

    While also providing the exact QEMU arguments it's about to use if you plan to dive in manually yourself.

  * Takes as many virtual disks or iso's as you want to pass in with an iothread on the host for each virtual disk.

    Or if you're passing in an entire disk array, save the overhead and pass the entire HBA controller with (`-PCI 'SATA'`)

    (Assuming that doesn't include your host disk!)

  * Takes an optional regular expression of PCI and USB devices to pass to the VM when starting it.
  * 
    (My favorite is `-PCI 'NVIDIA|USB'` to give it my card with all host USB controllers)

  * *Automatically unbinds all specified PCI devices from their driver's onto vfio-pci if they're not already on it.

    (No need for early host driver blocking or early PCI device vfio binds)

  * ***Automatically REBINDS all PCI devices back to their originating driver*** on guest exit (When applicable)

  * Automatically kills the display-manager if the GPU is stuck unbinding for a guest to use (Unavoidable in single GPU scenarios)

    But also rebinds the card back to its driver on guest exit and restarts the DM back to the login screen.
    
    Almost seamless...

  * Makes network bridges automatically or attaches the VM to an existing bridge with a tap adapter (Standard VM stuff) giving your VM a true Layer 2 network presence on your LAN, DHCP, direct port exposure for RDP, SSH, and all.


    (Useful to avoid the default "One way trip" nat adapter)
  
  * Takes optional vcpuPinning arguments if you've isolated cores on your host to help avoid stutter.

  * Can describe your host's IOMMU Groups and CPU thread to core pairs so you know the true CPU topology to isolate and pin with appropriately.
    
    *(For now core isolation must be handled outside the script. Sorry! it annoys me too. But the best time to isolate is in the kernel arguments, of which I've provided some powerful examples lower down.)*

  * Dynamically allocate hugepages for the VM *on the fly* if host memory isn't too fragmented, otherwise it will notice existing hugepages and use them if there's enough free from earlier/boot time allocation.

  * Optionally enables Looking Glass support if you have a second i/dGPU on the host to continue graphically with while the guest runs.

  * Takes an optional romfile argument for any GPU devices being passed through if needed for your setup.

  * Optionally includes key hyperv enlightenments for Windows guest performance.

  * And sometimes more! (*There's most likely many more arguments below*)

## What hosts and installs are supported?

Put short, it's designed for Archlinux but confirmed working in Ubuntu 20.04 and 18.04 as well.

It seems any distribution running a modern Linux kernel and the latest QEMU will do. The host will need to support either Intel's VT-d or AMD-Vi (May just be labelled IOMMU in bios) While even my older PC from the early 2010s supports these modern boards do a much better job for latency and performance.
Also don't forget to add the relevant AMD or Intel VFIO arguments to your kernel's boot arguments. On some distros straying enough from the rolling lifestyle, you may need to specify the OVMF path using `-bios`, but that should be the worst of it. 

Even my partially retired desktop from 2011 with a 3930K CPU and x79 motherboard can run this script using a Looking Glass window into the guest through X via a second GPU for the host.

On my 2020 PC build (3900x, DDR4@3600, single 2080Ti, M.2 SSD in the back slot *just for the guest*) I play Overwatch, Mortal Kombat, Battlefield and more in a VM on this machine with ease. As for performance I'm glad to be able to say I genuinely can't tell I'm in a VM (without checking Device Manager of course). There's no stutters or any other telltale signs that its not a real computer in gameplay when pinning and isolation are done correctly; which I find to be particularly important in multiplayer titles.


# Why make this
The #0 reason is "fun", I love my field and the 'edutainment' I've always gained from it fuels the fire; but while WINE and Proton have gotten me far over the past few years:
  1. It lets me do a lot of "scratch pad" debugging/testing/kernel patching/hacking and other test which can be entirely forgotten in a blink.
     (Or by hitting ^a^x in QEMU's terminal window which might be faster)
  2. A game title may employ a driver-level Anti-Cheat solution, completely borking the multiplayer experience in Linux (Which you can't just throw at WINE).
  3. Overall, a title may be known not to work in Linux despite best efforts and time commitment.

Furthermore, instead of hardcoding a VM in libvirtd this script lets me take on less of a "set and forget" attitude, only to come back once a bios update or setting change causes PCI addresses to change (Common online complaint I see)
I figured I'd write my own all-in-one manager for the job and editing what I want to send to a VM is a easy as pressing the up arrow in my Bash history and just changing the line calling this script with no troubles.
In general this script has been very useful in my tinkering even outside VFIO gaming and at this point I swear by it for quick and easy screwing around just on the desktop.

# The script, arguments, examples and an installation example

## General usage arguments

`-avoidVirtio` / `-noVirtio`

  If set, tries to pick more traditional QEMU devices for the best compatibility with a booting guest.
  Likely to be useful during new Windows installs if you don't have the virtio iso to pass in with the installer iso.
  Also useful in other departments such as testing kernels and initramfs combinations where virtio isn't a kernel inbuilt or initramfs as a late module.

`-iommugroups` / `-iommugrouping`

  Prints IOMMU groupings if available then exists.

 `-cputhreads` / `-showpairs` / `-showthreads` / `-showcpu`

  Prints host core count and shares which threads belong to which core
  Useful knowledge for setting up isolation in kernel arguments and when pinning the guest with -pinvcpus

`-ignorevtcon` / `-ignoreframebuffer` / `-leavefb` / `-leaveframebuffer` / `leavevtcon`
    Intentionally leave the vtcon and efi-framebuffer bindings alone 
    Primarily added to [work around kernel bug 216475](https://bugzilla.kernel.org/show_bug.cgi?id=216475)
    Prevents restoring vtcon's at a cost of as many GPU swaps from host to guest as desired.

`-image /dev/zvol/zpoolName/windows -imageformat raw`

   If set, attaches a flatfile, partition, whole-disk or zvol to the VM with QEMU's -drive parameter.
   -imageformat is optional and will apply to the most recent -image argument specified.
   -image and -imageformat can be used multiple times to add more disks.

`-iso /path/to/a/diskimage.iso`

   If set, attaches an ISO to QEMU with an incrementing index id. Can be specified as many times needed for multiple CDs. Good for liveCDs or installing an OS with an optional driver-cd.

`-bridge tap0,br0       (Attach vm's tap0 to existing br0)`

`-bridge tap0,br0,eth0  (Create br0, attach vm's tap0 and host's eth0 to br0, use dhclient for a host IP.)`

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
     
6. During cleanup, frees the interface from the bridge and deletes the bridge and tap interface. Restores NetworkManager if it were found to be running.
     
   If this argument isn't specified the default QEMU NAT adapter will be used
    (NAT may be desirable for some setups)

`-memory 8192M` / `-m 8G` / `-mem 8G`

   Set how much memory the VM gets for this run. Argument assumes megabytes unless you explicitly use a suffix like K, M, or G.
     If this argument isn't specified the default value is HALF of the host total.

`-hugepages` / `-huge` / `-hugepages /optional/mountpoint/to/custom/hugepage`

   Tries to allocate hugepages for the VM dynamically based on how much memory it will be given (defined with -memory). Hugepages for a VM with frequent random memory access such as in gaming can be much snappier than your regular process accessing regular memory.
   If no argument is given it'll use /dev/hugepages which is often 2MB per page. The script drops host memory cache and then runs compact_memory before allocating with the aim of less fragmentation in hugepages. Using this argument will also clean up after itself by setting pages back to 0, reclaiming memory for the host. But only if it wasn't already preallocated before running the script.

   This flag also supports preallocation, so if you reserved some 1GB pages at boot time and mounted a pagesize=1G hugetlbfs to some directory, specifying that will skip the dynamic hugepgae allocation step above if there's enough free for the VM to use. Allocating hugepages at boot time sacrifices a lot of memory but doing it so early prevents fragmentation. Can be a lifesaver for performance.

`-hyperv`

   Enable hyper-v enlightenments for nested virtualization. For some cases this may help convince more invasive Anti-cheats to play along. You will need to enable (tick) the HyperV Windows Feature and reboot when it asks before this will work though.

`-hostaudio`

   Try to use the host's audio server for guest audio and also tries to start it.

`-cmdline` / `-append` & `-initrd`  / `-initramfs` & `-kernel`  / `-k`

Optionally pass a kernel file either self compiled or straight out of /boot to tinker with. Pass useful arguments to it with -cmdline such as console=ttyS0 and root=/dev/vda1. -initrd typically only required if kernel image built without relevant drivers or if there's licensing issues.

`-quiet` / `-q `/ `-silence` / `-s`

   Try to be quiet, only printing any errors we run into. Useful after your 1786th run.

`-bios '/path/to/that.fd'`

   An optional bios path. If not set the script will try `/usr/share/ovmf/x64/OVMF_CODE.fd` if available.

`-usb 'AT2020USB|SteelSeries|Ducky|Xbox|1425:5769'`

   If set, the script enumerates `lsusb` with this regex and generates QEMU arguments for passing them through when the VM starts.

This example would catch any:
     
1. Audio-Techinica AT2020 (USB Microphone+headphone DAC)

2. SteelSeries mouse,

3. Xbox Controllers,

4. Ducky brand keyboard.

5. A USB device with ID `1425:5769`, whatever that may be.

`-pci 'Realtek|NVIDIA|10ec:8168'`

   If set, the script enumerates `lspci` for the set regex and generates qemu arguments as it does for `-usb`. In `-run` mode, it also unbinds them from their current drivers (If any) and binds them to vfio-pci.
   It remembers what they were bound to beforehand for rebinding once the VM shuts down.
   
This example would catch any:
     
1. PCI devices by Realtek
       
2. NVIDIA cards (Including children of the GPU like the audio card and USB-C controller)
       
3. A PCI device with ID `10ec:8168`.

`-pinvcpus 0,1,2,3,4,5` / `-pinvcpus 0,2,4,8`

   The taskset argument will take the threads you give it and only lets the VM execute on those threads. It also creates only that many threads on the VM. (6 and 4 in the examples respectively)
   This can significantly reduce latency if the guestis having trouble, even if you haven't configured any host pinning.

`-portforward tcp:2222:22` + `-portforward tcp:33389,3389`
    A comma separated argument taking a comma delimited argument in the format of protocol,hostport,guestport for guest portforwarding.
    Can be specified multiple times.
    Only applicable with default user-mode NAT networking (Pointless when bridging)

`-colortest`

  A quick terminal color test then exits.

`-looking-glass` / `-lookingglass` / `-lg`

  Adds a 64MB shared memory module for the Looking Glass project and a spice server onto the guest for input from host during Looking Glass usage.
  You will still need to go into your VM add the VirtIO IVSHMEM driver to the "PCI standard RAM Controller" which appears in Device Manager under System Devices before Looking Glass will function.

`-romfile` / `-vbios /path/to/vbios.bin`
   Accepts a file path to a rom file to use on any detected GPU during -pci argument processing.
   Some host configurations will need this even with a modern GPU. Older NVIDIA gpus need this too if not isolated from boot time.
   
   If you're on a single-dGPU host passthrough to a guest on an older NVIDIA card, you will likely require this.
   If you experience "black screen" issues on guest startup it's often a problem solvable with a vbios.
   My 2080Ti has days where it can just fire up in a guest and others where it needs a vbios to light up the screen during passthrough. Probably bios setting dependant in my case.
   
   If you're going to use a vbios dump, you should confirm it's safe before using it on a GPU the rom-parser github project is good to check this.
   Otherwise you can usually just find a preexisting dump for your model's vbios on TechPowerup and patch it with say, NVIDIA-vBIOS-VFIO-Patcher.
   
`-extras '-device xyz -device abc -device ac97 -display gtk -curses'`

   If set adds extra arbitrary commands to the cmdline of QEMU (Once invoked)
   Useful for `-device ac97` to get some quick and easy audio support if the host is running pulseaudio.

`-run`

  Actually run. The script runs dry by default and outputs QEMU arguments and environment information without this flag.
  Especially useful for testing PCI regexes without unbinding things first try, but good for general safety.

## Notes and Gotchas.
  - If you don't pass through a graphics card while your $DISPLAY variable is set (e.g. launching this script in a terminal in your current graphical session)
    The script will give the VM a virtual screen and pop up like any other window so you can *see*.
    You can prepend DISPLAY='' to the script command line to force the guest to have no virtual VGA screen. This is useful if you're using a NIX based OS which can take an argument such as console=ttyS0 to be accessible from the ter minal you launched from .
  - The absolute minimum requirement to do anything useful is the `-image` and/or `-iso` arguments with OVMF installed. You can install an OS, extra drivers can always wait until later.
  - The default networking mode is QEMU's user-mode networking (NAT through host IP).This is fine for most people but if you expect to be able to initiate outside connections to the guest, consider using `-bridge`
  - This script makes use of VirtIO for networking. Unless you're passing through a USB/PCI network adapter and use `-nonet`, you'll want to install the VirtIO drivers into the guest before expecting virtual-networking to work.
    If you can't use virtio drivers for whatever reason, you can specify -noVirtio, but the performance penalty will be noticible.
  - The CPU topology this sets is 'host'. So the VM will think it has the host's CPU model. This is usually a good idea.
  - Without specifying - The VM will use ALL host cores and HALF the host memory.
      You can use -pinvcpus to cherry pick some host cpu threads for the VM to execute on and this will also set the VM's vcpu count appropriately to match.
        This is very useful if the host produces enough load to cause stuttering in the VM during normal operation.
        If your host doesn't have the cpu load headroom for a gaming guest or the VM experiences stuttering, Consider using -pinvcpus and isolateing the cores you pick for the guest.
        
## The VM and Getting started with a fresh install of something (Windows? Linux? Direct kernel booting?)

Right out the gate, if you're "feeling lucky" (Have prepared accordingly) you can start the script with your GPU, some usb input device like a keyboard so you can actually configure it, an installer ISO, an optional vbios if you're having initialization issues and just do it all in one take.

Try to include the virtio ISO too and use virtio hardware instead of setting -noVirtio, virtio devices perform much better than a lot of the traditional stuff (Theoretical 10Gbe link between host and guest for example) and this script creates an ioThread for the guest's disk activity when using virtio.

Otherwise, feel free to start the script just specifying your -iso of choice with QEMU's default virtual GPU will pop up a window for you to get started in. Once you've installed everything you need you can shut the guest down and try GPU passthrough (With peripherals!)

If you've already isolated a GPU for the guest (Explicitly isolated from boot, often also involves telling the bios which GPU to use/ignore) or have a patched vbios ready to specify with -vbios so the guest can re-initialize the card for itself then you too can start the install process with the card included from install. You'll want to passthrough at least a keyboard with -usb, or you can specify 'USB' in the -PCI argument regex to capture ALL of your hosts USB card inputs with your GPU too. Passing through entire USB/SATA/NVME controllers is ideal; much better performance than having the guest access the same devices through virtual hardware.

### In depth installation steps for a Windows VM

1. You *should* use virtio hardware with your VM, it performs better than the legacy-supporting virtual hardware and [you can get the virtio driver disc ISO to pass with your installer ISO here](https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/archive-virtio): 

*Don't want to use virtio drivers for your guest or can't fetch the ISO? You can launch this script with -novirtio to use legacy devices like e1000e for networking which should be compatible with most barebones OSes

2. [Get the latest Win ISO you wish to install from Microsoft's site here](https://www.microsoft.com/en-au/software-download/)

3. Create storage for your VM; It has to live somewhere. Example commands below.

     `QEMU-img create -f qcow2 myWin10VM.qcow2 100G # A classic sparse qcow2`

     `dd if=/dev/zero of=myvm.img bs=1G count=100   # A preallocated raw example with DD, will probably perform better if you're not on a QoW Filesystem`

     `zfs create -V100G myPool/myVMDisk             # zfs backed virtual block-device (ZVOL), doesn't perform as well as I'd like but very tidy`

4. Start the script following something like the below example:

     `./main -image /dev/zvol/myPool/myVMDisk -imageformat raw -iso /tmp/Win10_20H2_v2_English_x64.iso -iso /nas/common/ISOs/virtio-win-0.1.189.iso`
* Or if you can't provide the guest with virtio drivers yet:
     `./main -image /dev/zvol/myPool/myVMDisk -imageformat raw -iso /tmp/Win10_20H2_v2_English_x64.iso -novirtio`

* For veterans, an example including the GPU and all USB controllers thus devices from VM first boot and on a new on the fly host bridge interface:
     `qemu-img create -f raw /tmp/win.qcow2 50G`
     `~/vfio/main -mem 12G -image /tmp/win.qcow2 -imageformat qcow2 -bridge tap0,br0,eth0 -pci 'NVIDIA|USB' -pinvcpus 0,12,1,13,2,14,3,15 -ignorevtcon -run`

5. Eventually windows will ask you to partition disks, if you're using VIRTIO (default) then you'll need to install the storage driver here before it'll see its disk.
   If you used `-novirtio` there should be no issue continuing over classic IDE.

6. Once at the VM's desktop:

* If you passed your GPU in from the beginning you're set, go ahead and install the official drivers for your card, do your updates and grab Steam or something.

* If you haven't passed your card in yet, you can shutdown the VM and pass it in now. As a Plan B for Win guests you can do your Windows Updates so it knows to grab the driver and initialize the card. In case something else goes wrong.

* It's worth going through Device Manager for any missing drivers. If you used virtio the iso will likely take care of them shortly if you don't click in and specify.

### Passthrough gotchas

1. If you're on a NVIDIA card including 2000,3000 and 4000 generations but are experiencing a blank screen or monitors just going into standby at VM boot, ensure you have isolated correctly, or if you already know your GPU isn't isolated then consider using a patched VBIOS file so the guest can just reinitialize the card itself.

2. If your guest has the NVIDIA driver installed, you may find your screen starts black (And you visually miss the TianoCore UEFI boot process)
but eventually gets a video signal once the guest reaches the login screen and the NVIDIA driver kicks in to resuscitate the card itself. This isn't ideal but it can also save the day like that.


### Performance woes?

For best VM performance in any scenario:

1. If you're virtualizing Windows, you can pass `-hyperv` to enable some HyperV enlightenments courtesy of QEMU.

2. Consider hugepages (`-hugepages`) with your `-memory` argument. If your host memory is too fragmented for them to allocate on the fly, consider using `hugepagesz=1G` and `hugepages=12` in your kernel boot arguments; replacing '12' with the number of GB you wish to reserve for your VM. Don't forget to specify all of it with `-m xG -hugepages` when starting your VM.

3. If you opted out of virtio devices with -novirtio and this isn't just a testbed; consider installing the drivers and using virtio devices. The virtual network interface alone is capable of 10Gbps which likely isn't your LAN speed, but means the host<>guest communication will be as fast as the CPU can deliver. This could be useful things such as reading a Steam library from the host over NFS, fast host to guest network shares in general and other cases for example if somebody wanted to use projects such as Steam's Streaming option or software such as Parsec, both of which would love a large low latency pipe to speak through.


4. Pinning the vcpus of your guest to cpu threads of your host. QEMU spawns a child vcpu thread for each cpu you give it. They act as the actual "cpu" threads of your guest OS. You can check `-cputhreads` and use -pinvcpus to pin host cores to your guest. Pinning QEMU vcpu threads avoids it getting thrown about at the mercy of your host scheduler and can help significantly, especially on single GPU scenarios where your host load is negligible.


5. Isolating the cores on the host that you pinned the guest to. I use the below to squeeze every last drop of low latency responsiveness on my VM:

* isolcpus= thread,range,to-isolate  # Tell the kernel to not schedule work onto these, as they will be the ones we pin QEMU to
* nohz_full=thread,range,to-isolate  # Tell the kernel to NOT send timer ticks to these cores, their only job will be QEMU so no need to check in. "Adaptive Ticks"
* rcu_nocbs=thread,range,to-isolate  # Tell the kernel to handle RCU callbacks for these on any other CPU but themselves.
* irqaffinity=remaining,host,threads # Use these remaining host cores to handle all host IRQ/RCU
* rcu_nocb_poll                      # Enforce the above by polling only ever so often rather than having cores handle it themselves
* systemd.unified_cgroup_hierarchy=0 # Enables systemd v1 cgroups

6. Passing in a real disk to your guest to boot from such as a dedicated NVME controller with the -pci argument will always perform much better than any QEMU disk method, even though this script creates an iothread per guest disk, you can't go wrong with raw NVME passthrough.
   The next closest contender would be a raw partition on the host passed as a virtio disk, or a raw.img file on a lightweight host FS such as ext4 (with a goal of minimizing overhead)

## Saving your Display Manager from being killed to unbind the guest card (Xorg) / General guest GPU pre-prep

Informing Xorg via xorg.conf (or a .d/file.conf) to ignore other GPUs on your system is a good way to keep your second GPU on the driver (So it can still be used for CUDA operations) while allowing it to be unbound from the driver on the fly for a guest to use without killing your host's graphical session. 

Isolating the second card like this allows your second card to stick around for CUDA-powered computations on the host and if there's no other processes other than Xorg using your guest card, you can unbind it for vfio-pci usage at any time without hanging (Waiting for processes to exit)

Naturally, this is only applicable in scenarios where you have a second GPU. Single GPU passthrough users only have the one card to draw to, which means X needs to be stopped before the guest can have that card. Sorry. However, if you aren't running anything graphically intensive, you could use XPRA on your host and run your programs through that. Then re-attach to it when you make it back to the host graphically. Or even better, you could attach to XPRA *from inside the guest* and continue accessing your host applications from inside the guest.

### An Xorg.conf example to only use one GPU (On a system with more)

This can be put right into /etc/X11/xorg.conf but be sure to replace any existing Device declarations you have so that X doesn't error. -- Some distros

    Section "ServerFlags"
        # Do not scan for GPUs
      Option "AutoAddGPU" "0"
      Option "AutoBindGPU"  "0"
        # It's OK to scan and add peripherals however.
      Option "AutoAddDevices" "1"
      Option "AutoEnableDevices"  "1"
    EndSection
    
    # Define the host GPU here, no others
    Section "Device"
        Identifier     "Device0"
          # Pick the right driver for your host GPU vendor.
        Driver         "nvidia"
          # And the correct bus ID (lspci -D)
        BusID          "PCI:1:0:0"
          # Do not probe for others.
        Option "ProbeAllGpus" "0" 
    EndSection
    
### Checking what's using your GPU's at a glance.
Here's a quick and dirty one-liner which this VFIO script also uses to check what processes are using a GPU. Just substitute the path with the PCI address of your guest-intended GPU:
1. `xrandr --listproviders` will reveal how many GPUs it thinks it's allowed to use in your Graphical Session. **This honors your xorg.conf**.
2. `ps $(fuser /dev/dri/by-path/pci-0000:03:00.0* 2>/dev/null)` will reveal exactly which processes are using a GPU no matter what. Any that aren't following your xorg.conf will be listed here too. The script uses this for killing when required. Don't forget to replace this example `pci-0000:03:00.0` with the PCI path of the GPU you wish to check.

### Some processes that get in the way even with a perfectly isolating xorg.conf
I've spent plenty of time going over every relevant flag to try and demystify why xorg.conf isolation is so inconsistent so this README.md can be a good VFIO general reference but in my experience even with a perfect gpu-isolating xorg.conf, some Window Managers still spawn processes which latch onto the card I just tried to isolate.

I use Cinnamon and Xfce4. It turns out Cinnamon spawns `xdg-desktop-portal-gnome` (I assume nay Gnome-based WM will) and Xfce4 spawns `xdg-desktop-portal` both of which latch onto the second GPU despite being isolated in xorg.conf.

This is really annoying, but is easily thwarted by simply kill/pkill'ing those processes.
In the case of both Window Managers, I was able to kill those portal processes and my graphical session continued to function just fine. But also, my second GPU could be unbound and used for VFIO without killing my graphical session.

Armed with this knowledge, the script now supports xorg.conf isolation and will try to unbind a card without killing X first, only resorting to killing it in a last resort scenario / flag.

## Guest GPU "selective" isolation use-cases

For general guest GPU pre-prep or if you're desperate to not kill your existing Xorg session; there's many ways to prepare, though the methods available drastically change depending on your use case.

### Use case 1: Dedicated GPU for the guest which is a different model and driver than your host's GPU
This is the best case scenario to deal with easiest scenario to deal with as you can simply [bind vfio-pci at boot time](https://wiki.archlinux.org/title/PCI_passthrough_via_OVMF#Binding_vfio-pci_via_device_ID) by adding `vfio-pci.ids=` to your host's kernel arguments. This will bind the guest card to vfio-pci immediately and to undo it you can either remove that kernel argument and reboot or manually unbind your gust GPU from vfio-pci and bind it back onto the vendor GPU driver.
### Use case 2: Dedicated GPU for the guest, but you want to use it on the host when the guest isn't in use (e.g. Host Cuda while guest is powered down)
As long as you aren't locking your guest's card into an Xorg session, you can let this vfio script dynamically unbind your guest card from the nvidia/radeon/amdgpu driver on the fly. Just make sure you aren't using the GPU elsewhere such as a CUDA operation or other gpu-accelerated CLI task.
### Use case 3: The guest GPU and host GPU are identical [vendor:class] IDs
This ends up being a similar case as #2, as you cannot target your guest's card using vfio-pci.ids because that will catch your host's GPU as well.
You can use the same xorg.conf isolation method to tell X to only use your primary GPU by targeting its PCI address. This script will automatically unbind your second GPU of the same model if it is not in use by anything else.

## Script usage examples

Note: `-run` is omitted for obvious reasons.



If you aren't ready to do any passthrough and just want to start the VM in a regular window (Installation, Drivers, etc.):

`./main -image /root/windows.img -imageformat raw -iso /tmp/Installer.iso`

If a host has been booted with isolated cores you can tell the script to pin the guest to those only:

`./main -image /root/windows.img -imageformat raw -pinvcpus 0,1,2,3,4,5`
  
  This example starts the VM with only host threads 0 to 5 (The first 3 cores on some multi-threaded hosts, check -cputhreads to see your true host thread to core topology)
  Useful if a VM experiences stuttering from host load.

An example run with passthrough could look like:

`./main -image /dev/zvol/poolName/windows,format=raw -bridge tap0,br0,eth0 -usb 'SteelSeries|Audio-Technica|Holtek|Xbox' -pci 'NVIDIA'`
  
  This example would (if seen) pass all regex-matching USB and PCI devices and rebind the PCI devices if applicable.
  It would also provision network bridge br0 and attach tap0 to the bridge with your host interface. Then give tap0 to the VM.

An advanced example giving a guest 8G of memory and booting the host's kernel with arguments to boot from the first partition of a provided virtual disk.
Includes an initramfs for the ext4 driver, which will be needed to read the ext4 rootfs partition of the virtua disk provided.
Also doesn't use VirtIO becuase nor the kernel or initramfs have the virtio_scsi driver as a built-in:

  `./main -m 8G -kernel /boot/vmlinuz-linux -append 'root=/dev/sda1 rw ' -initramfs /boot/initramfs-linux.img -image /zfstmp/kernelbuild/test.ext4.qcow2 -imageformat qcow2 -novirtio -run`

