# joyhome-knx-kernel

Linux 6.18 LTS for the **JoyHome "KNX HOME SERVER"**: an Orange Pi CM4 v1.4 (Rockchip RK3566) on JoyHome's carrier board, running Debian with Home Assistant Supervised, knxd and a TP-UART KNX interface.

The box shipped with Orange Pi's 5.10.160 kernel (a 2022 base that no longer gets fixes). Orange Pi has nothing newer for this board, and ready-made kernels such as Armbian's can't boot it. This repo builds a current long-term kernel that can, and rebuilds it every month as new 6.18 fixes come out.

## Why a ready-made kernel won't boot

JoyHome's carrier board has an **external hardware watchdog** on GPIO4_C3. It resets the whole board unless that pin is toggled about every second, starting from the first moments of boot. JoyHome's own kernel has the GPIO watchdog driver built in at the earliest boot stage (`CONFIG_GPIO_WATCHDOG=y`, `CONFIG_GPIO_WATCHDOG_ARCH_INITCALL=y`). Armbian's kernels either don't have it or load it as a module, which is seconds too late. So the board resets before the kernel gets anywhere.

## What's here

| Path | What it is |
|---|---|
| `dts/rk3566-joyhome-knx.dts` | Device tree for the box: Orange Pi's CM4 v1.4 tree plus JoyHome's additions (watchdog, three front buttons, second fan, fan table) and the settings JoyHome's overlays turned on (KNX on ttyS3, Zigbee on ttyS7, I2C2 for the OLED and DS1307 RTC, I2C4, PWM11). Ethernet keeps the name `end1`. Checked pin by pin against the running 5.10 system. |
| `dts/rk3566-orangepi-cm4-v1.4-opi66.dtsi` | Orange Pi's CM4 v1.4 board file (from their 6.6 branch), which matches this board: VCCIO5 at 1.8 V, Ethernet PHY reset on GPIO4_C4. |
| `config/base-armbian-rockchip64-6.18.config` | Armbian's rockchip64 6.18 kernel config, the starting point. |
| `config/joyhome.config` | The changes on top: watchdog built in, DS1307 RTC, 10 serial ports, no debug info. |
| `config/trim-drivers.py` | Turns off driver modules this box can never use, to keep builds quick. |
| `.github/workflows/build.yml` | Builds the latest 6.18.y on the 3rd of each month (or by hand) and publishes the `.deb` as a release. |
| `box/` | Files installed on the box (see below). |

## On the box

| File on the box | From `box/` | What it does |
|---|---|---|
| `/boot/boot.cmd`, `/boot/boot.scr` | `boot.cmd`, `boot.scr` | u-boot script: picks 6.18 or 5.10 (see trial boots), keeps JoyHome's hardware check (`adc_read 3`). |
| `/etc/kernel/postinst.d/zz-joyhome-boot` | `zz-joyhome-boot` | After a `*-joyhome` kernel installs: copies it to `/boot/Image`, its device tree to `/boot/joyhome/`, and arms a trial boot. |
| `/etc/initramfs/post-update.d/99-uboot` | `99-uboot` | Makes `/boot/uInitrd` for the new kernel; a 5.10 rebuild goes to `/boot/k510/uInitrd`. |
| `/usr/local/sbin/kernel-trial-confirm` + `.service` | same | On a trial boot, waits for Ethernet, `/dev/knx`, Docker and the RTC, then confirms the kernel or reboots back to 5.10. |
| `/usr/local/sbin/joyhome-kernel-update` | same | Installs the latest release from this repo. |
| `/etc/initramfs-tools/scripts/init-{premount,bottom}/k618diag` | `k618diag-*` | During a trial only, saves the kernel log to `/boot` (for diagnosis). |
| `/etc/systemd/system/ap6256-bluetooth.service.d/only-on-5.10.conf` | `ap6256-only-on-5.10.conf` | 6.18 drives the Bluetooth itself; JoyHome's script only runs on 5.10. |

5.10 stays on the box in `/boot/k510/` (kernel, initrd, device trees) as the fallback.

### Trial boots

Flags in `/boot` decide what u-boot boots:

| Flag | Meaning |
|---|---|
| none | 5.10 (safe default) |
| `karmed.txt` | Try the new kernel once: u-boot writes `ktrial.txt` and boots it. |
| `ktrial.txt` | A trial boot started but didn't confirm: u-boot writes `kold.txt` and boots 5.10. |
| `knew.txt` | The new kernel passed its trial: boot it. |
| `kold.txt` | Boot 5.10 whatever else is there. |

A kernel that crashes reboots itself after 10 seconds (`panic=10`), and the hardware watchdog resets the board if it hangs, so a bad kernel always ends up back on 5.10 within a couple of minutes.

### Updating

```bash
sudo joyhome-kernel-update            # install the latest build, reboot when it suits
sudo joyhome-kernel-update --reboot   # install and reboot now
sudo joyhome-kernel-update --check    # just check
```

The first boot of a new kernel is always a trial.

### Going back to 5.10

```bash
echo x | sudo tee /boot/kold.txt && sudo reboot
```

Delete `/boot/kold.txt` and create `/boot/karmed.txt` to try the new kernel again.

## Building by hand

Actions → **Build kernel** → Run workflow. Leave the version blank for the latest 6.18.y, or enter one (e.g. `6.18.63`).
