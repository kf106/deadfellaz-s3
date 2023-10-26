# deadfellaz-s3
Firmware and code for building a DeadFellaz T-Display-S3 display device. Note that this repository also provides general information for anyone wanting to code in micropython for the Lilygo T-Display-S3 and then compile and flash functioning firmware to the device.

Almost all the information to do this was available on the Internet, but it was scattered all over the place, and a few key pieces were missing.

I aim to make my repositories as understandable as possible, so if you find yourself confused please open an issue explaining your problem and I'll try to resolve it.

## Setting up a docker firmware building image

Please note that I like my repositories to document the journey, rather than just the end result.

### Configure a container from scratch
One approach is to start a Ubuntu docker container, and run the setup.sh script to configure it correctly, although this takes quite some time if you want to run the container again and again. It is, however, a useful tutorial.

1. Install docker if you don't have it already. See [the docker install guide](https://docs.docker.com/engine/install/ubuntu/)

2. Run the following command from this repository's main folder to start an interactive bash terminal, with the current folder mapped to /deadfellaz-s3:

`docker run -v "$(pwd)":/deadfellaz-s3/ -it ubuntu:22.04 /bin/bash`

3. Change to the mapping of this repository:

`cd /deadfellaz-s3/`

4. Run the setup script, which should clone and build all the required tools for you:

`./setup.sh`

If everything went according to plan, your terminal should now show the following lines:

```
Project build complete. To flash, run this command:
/root/.espressif/python_env/idf4.4_py3.10_env/bin/python ../../../esp-idf/components/esptool_py/esptool/esptool.py -p (PORT) -b 460800 --before default_reset --after no_reset --chip esp32s3  write_flash --flash_mode dio --flash_size detect --flash_freq 80m 0x0 build-GENERIC_S3_SPIRAM_OCT/bootloader/bootloader.bin 0x8000 build-GENERIC_S3_SPIRAM_OCT/partition_table/partition-table.bin 0x10000 build-GENERIC_S3_SPIRAM_OCT/micropython.bin
or run 'idf.py -p (PORT) flash'
bootloader  @0x000000    18784  (   13984 remaining)
partitions  @0x008000     3072  (    1024 remaining)
application @0x010000  1502112  (  529504 remaining)
total                  1567648
```
### Build an image for your build container using the Dockerfile

A better long-term solution is to build an image that is configured correctly to make board builds correctly.

`docker build -f Dockerfile -t s3lcd-build --compress .`

Once you have the build image, you can start it immediately using:

`docker run -it s3lcd-build`

To make a build, run `cd /tmp/micropython/ports/esp32` and then execute:

`make USER_C_MODULES=/tmp/s3lcd/src/micropython.cmake FROZEN_MANIFEST="" FROZEN_MPY_DIR=$UPYDIR/modules BOARD=GENERIC_S3_SPIRAM_OCT`

