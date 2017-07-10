#
# Script to start a set of apps, switch to recents and fling it back and forth.
# For each iteration, Total frames and janky frames are reported.
#
# Options are described below.
#
# Works for volantis, shamu, and hammerhead. Can be pushed and executed on
# the device.
#

DEVICE=hikey
TIMEOUT=10
EVENT=swipe

# handle args
while [ $# -gt 0 ]
do
	case "$1" in
	(-d) DEVICE=$2; shift;;
	(-t) TIMEOUT=$2; shift;;
	(-e) EVENT=$2; shift;;
	(*)
		echo "Usage: $0 [options]"
		echo "-d: Device type"
		echo "-t: Timeout"
		echo "-e: Event type"
		exit 1;;
	esac
	shift
done

case $DEVICE in
(hikey)
	flingtime=100
	UP="960 720 960 360 $flingtime"
	DOWN="960 360 960 720 $flingtime"
	SELECT="960 540";;
(*)
	echo "Error: No display information available for $DEVICE"
	exit 1;;
esac

function doSwipe {
	input swipe $*
}

function doKeyevent {
	input keyevent $*
}

function swipe {
	doSwipe "$UP"
	sleep 1
	doSwipe "$DOWN"
	sleep 1
}

function click {
	input tap $SELECT
	sleep 1
}

end=$(($SECONDS+$TIMEOUT))

echo $SECONDS
echo $end

while [ $SECONDS -lt $end ]
do
	if [ "$EVENT" = swipe ]; then
		swipe
	elif [ "$EVENT" = click ]; then
		click
	fi
done

#doKeyevent HOME
