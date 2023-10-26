# ensure image has latest packages and is up to date
apt-get -y update
apt-get -y upgrade

# install required packages
apt-get -y install build-essential libffi-dev git pkg-config cmake virtualenv python3-pip python3-virtualenv python3-libusb1

# clone repositories in tmp folder
cd /tmp
git clone https://github.com/micropython/micropython.git
git clone https://github.com/russhughes/s3lcd.git
git clone --recursive https://github.com/espressif/esp-idf.git

# build correct version of esp-idf, the build environment
cd esp-idf
git checkout v4.4.4
git submodule update --init --recursive

# and install it
./install.sh

# finally ensure that the required environment is exported
source export.sh

# build correct version of micropython
cd ..
cd micropython/
git checkout v1.20.0
git submodule update --init
cd mpy-cross/
make
cd ..
cd ports/esp32

# update the board definition for the T-Display-3 which has a 16MB octal SPIRAM 
sed -i 's/8MB=y/8MB=/' ./boards/GENERIC_S3_SPIRAM_OCT/sdkconfig.board
sed -i 's/16MB=/16MB=y/' ./boards/GENERIC_S3_SPIRAM_OCT/sdkconfig.board
sed -i 's/8MiB/16MiB/' ./boards/GENERIC_S3_SPIRAM_OCT/sdkconfig.board

# perform a test build with the current configuration
make USER_C_MODULES=/tmp/s3lcd/src/micropython.cmake FROZEN_MANIFEST="" FROZEN_MPY_DIR=$UPYDIR/modules BOARD=GENERIC_S3_SPIRAM_OCT

# if everything went well, you should now see the following lines:

# Project build complete. To flash, run this command:
# /root/.espressif/python_env/idf4.4_py3.10_env/bin/python ../../../esp-idf/components/esptool_py/esptool/esptool.py -p (PORT) -b 460800 --before default_reset --after no_reset --chip esp32s3  write_flash --flash_mode dio --flash_size detect --flash_freq 80m 0x0 build-GENERIC_S3_SPIRAM_OCT/bootloader/bootloader.bin 0x8000 build-GENERIC_S3_SPIRAM_OCT/partition_table/partition-table.bin 0x10000 build-GENERIC_S3_SPIRAM_OCT/micropython.bin
# or run 'idf.py -p (PORT) flash'
# bootloader  @0x000000    18784  (   13984 remaining)
# partitions  @0x008000     3072  (    1024 remaining)
# application @0x010000  1502112  (  529504 remaining)
# total                  1567648
