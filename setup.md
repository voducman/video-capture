# This is a tutorial for compiling GsStreamer into Opencv library

## Step 1. 
    sudo apt update && sudo apt install cmake
## Step 2. 
    conda activate YOUR_ENV_HERE (discard if not need)
## Step 3. 
    pip install numpy
## Step 4 [install GsStreamer]. 
    sudo apt-get install libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good\
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools gstreamer1.0-x \
    gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio

## Step 5. 
    git clone https://github.com/opencv/opencv.git \
    cd opencv/ \
    git checkout YOUR_VERSION_YOU_WANT 
** example: git checkout 4.5.1 **

## Step 6. 
    mkdir build
    cd build
    cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D INSTALL_PYTHON_EXAMPLES=ON \
    -D INSTALL_C_EXAMPLES=OFF \
    -D PYTHON_EXECUTABLE=$(which python) \
    -D BUILD_opencv_python2=OFF \
    -D CMAKE_INSTALL_PREFIX=$(python -c "import sys; print(sys.prefix)") \
    -D PYTHON3_INCLUDE_DIR_EXECUTABLE=$(which python) \
    -D PYTHON3_INCLUDE_DIR=$(python -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
    -D PYTHON3_PACKAGES_PATH=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())”) \
    -D WITH_GSTREAMER=ON \
    -D BUILD_EXAMPLES=ON ..

## Step 7 [building - take a minutes depend on your hardware]. 
    sudo make -j$(nproc)
## Step 8 [install package]. 
    sudo make install && sudo ldconfig  





#This is a tutorial for compiling FFmpeg with GPU support

## Step 1. 
    git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git
## Step 2. 
    cd nv-codec-headers && sudo make install && cd ..
## Step 3. 
    git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg/
## Step 4. 
    sudo apt-get install build-essential yasm cmake libtool libc6 libc6-dev unzip wget libnuma1 libnuma-dev
## Step 5. 
    cd ffmpeg 
## Step 6. 
    sudo apt install -y libx264-dev libx265-dev 
## Step 7. 
    ./configure \
    --enable-cuda --enable-cuvid --enable-nvdec --enable-nvenc --enable-nonfree --enable-libnpp \
    --extra-cflags=-I/usr/local/cuda/include  --extra-ldflags=-L/usr/local/cuda/lib64 \
    --enable-libx264  --enable-libx265 --enable-gpl --pkg-config="pkg-config --static"

## Step 8. 
    make -j 8
## Step 9. 
    sudo make install


