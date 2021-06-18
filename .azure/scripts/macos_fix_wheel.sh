#!/bin/bash
set -e -x

DESTINATION=$1
WHEEL=$2
CYCLONEDDS_HOME=$3
DELOCATE_ARCHS=$4

# Unpack the wheel
wheel unpack -d temp $WHEEL

# Get the wheel directory
files=(temp/*)
UNWHEEL="${files[0]}"
files=($UNWHEEL/cyclonedds/_clayer*)
DYLIB="${files[0]}"


# Strip out the rpath

echo $(otool -L $DYLIB)
install_name_tool -change @rpath/libddsc.0.dylib $CYCLONEDDS_HOME/lib/libddsc.dylib $DYLIB
echo $(otool -L $DYLIB)

rm $WHEEL
wheel pack -d $(dirname $WHEEL) $UNWHEEL
rm -rf temp

delocate-listdeps $WHEEL
delocate-wheel -v --require-archs $DELOCATE_ARCHS -w $DESTINATION $WHEEL
