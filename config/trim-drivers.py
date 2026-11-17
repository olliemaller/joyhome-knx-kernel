#!/usr/bin/env python3
# Turns off modules under drivers/ that this box can never use (PCIe NICs,
# other SoCs, industrial buses...), keeping whole families it could use.
# Usage: trim-drivers.py <kernel source dir>   (edits .config; run olddefconfig after)
import os,re,sys
L=sys.argv[1]
# map config symbol -> Kconfig file
sym={}
for root,dirs,files in os.walk(L):
    if "/.git" in root: continue
    for f in files:
        if f.startswith("Kconfig"):
            p=os.path.join(root,f)
            try:
                for ln in open(p,errors="ignore"):
                    m=re.match(r"^\s*(?:menu)?config\s+(\w+)",ln)
                    if m: sym.setdefault(m.group(1),os.path.relpath(p,L))
            except: pass
keep_drivers=["drivers/usb","drivers/hid","drivers/input","drivers/bluetooth","drivers/rtc","drivers/hwmon",
 "drivers/iio","drivers/i2c","drivers/spi","drivers/leds","drivers/watchdog","drivers/thermal","drivers/phy",
 "drivers/pwm","drivers/char","drivers/block","drivers/md","drivers/mmc","drivers/tty","drivers/gpio",
 "drivers/regulator","drivers/power","drivers/scsi","drivers/crypto","drivers/clk","drivers/pinctrl","drivers/soc",
 "drivers/net/wireless/broadcom","drivers/net/wireless/Kconfig","drivers/net/usb","drivers/net/phy","drivers/net/Kconfig",
 "drivers/net/wireguard","drivers/net/team","drivers/net/bonding","drivers/net/vxlan","drivers/net/ipvlan","drivers/net/mdio",
 "drivers/net/pcs","drivers/net/ethernet/stmicro","drivers/net/ethernet/Kconfig","drivers/gpu/drm/Kconfig","drivers/gpu/drm/rockchip",
 "drivers/gpu/drm/bridge","drivers/gpu/drm/display","drivers/gpu/drm/panfrost","drivers/gpu/Kconfig","drivers/dma","drivers/mfd",
 "drivers/nvmem","drivers/reset","drivers/misc","drivers/staging/Kconfig","drivers/firmware","drivers/devfreq","drivers/cpufreq",
 "drivers/video","drivers/base","drivers/virtio","drivers/vhost","drivers/remoteproc","drivers/mailbox","drivers/extcon",
 "drivers/net/wireless/realtek","drivers/net/wireless/mediatek","drivers/net/wireless/ralink","drivers/net/wireless/atheros"]
cfg=open(os.path.join(L,".config")).read().split("\n")
out=[];dropped=0;kept=0;unknown=0
for ln in cfg:
    m=re.match(r"^CONFIG_(\w+)=m$",ln)
    if m:
        k=sym.get(m.group(1))
        if k is None: unknown+=1; out.append(ln); continue
        if k.startswith("drivers/") and not any(k==d or k.startswith(d+"/") or k.startswith(d) and d.endswith("Kconfig") and k==d for d in keep_drivers):
            out.append(f"# CONFIG_{m.group(1)} is not set"); dropped+=1; continue
        kept+=1
    out.append(ln)
open(os.path.join(L,".config"),"w").write("\n".join(out))
print(f"dropped {dropped}, kept {kept}, unknown {unknown}")
