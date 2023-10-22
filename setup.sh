1  git clone https://github.com/espressif/esp-idf.git
    2  sudo apt-get -y update
    3  apt-get -y update
    4  apt-get -y upgrade
    5  sudo apt-get -y install build-essential libffi-dev git pkg-config cmake virtualenv python3-pip python3-virtualenv
    6  apt-get -y install build-essential libffi-dev git pkg-config cmake virtualenv python3-pip python3-virtualenv
    7  cd esp-id
    8  ls
    9  cd tmp
   10  git clone -b v4.4.4 --recursive https://github.com/espressif/esp-idf.git
   11  cd esp-idf
   12  git pull
   13  git status
   14  cd ..
   15  ls
   16  cd esp-idf/
   17  git checkout v4.4.4
   18  git status
   19  git pull
   20  git submodule update --init --recursive
   21  ./install.
   22  ./install.sh
   23  source export.sh
   24  cd ..
   25  cd esp-idf/
   26  ./install.
   27  ./install.sh
   28  source export.sh
   29  pip3 install python3-libusb1
   30  apt-get install python3-libusb1
   31  source export.sh
   32  cd ..
   33  ls
   34  git clone https://github.com/micropython/micropython.git
   35  cd micropython/
   36  git checkout v1.20.0
   37  git submodule update --init
   38  cd ..
   39  git clone https://github.com/russhughes/s3lcd.git
   40  cd micropython/
   41  git submodule update --init
   42  cd mpy-cross/
   43  make
   44  cd ..
   45  cd ports/esp32
   46  ls
   47  nano boards/GENERIC_s3_SPIRAM_OCT
   48  ls
   49  cd boards/
   50  ls
   51  cd GENERIC_S3_SPIRAM_OCT/
   52  ls
   53  nano sdkconfig.board 
   54  apt-get install nano
   55  nano sdkconfig.board 
   56  cd ..
   57  ls
   58  make USER_C_MODULES=/tmp/s3lcd/src/micropython.cmake FROZEN_MANIFEST="" FROZEN_MPY_DIR=$UPYDIR/modules BOARD=GENERIC_S3_SPIRAM_OCT

