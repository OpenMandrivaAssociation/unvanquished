#!/bin/sh
# Unvanquished Server as a Service
# By harland.coles@energy-x.com
# Copyright 2015 under http://opensource.org/licenses/ISC
#
thisName=$(basename $0)
usage(){
	echo "Usage: ${thisName} [--help] [ quit | cmd <command(s)> ] | [con [<commands>]]"
	echo "   Wrapper to run Unvanquished daemonded as a service,"
	echo "     with console pipe interaction."
	echo ""
	echo "   cmd <commands>:  Pipes commands into running instance."
	echo "   con:    Start in console mode (curses)."
	echo "           from commandline only, not systemd"
}
case "$1" in
	"--help"|"-h")
		usage
		exit 0
		;;
esac
logThis(){
	echo -e "#$(date +%Y%m%d-%H%M%S)] $1" >> "$2"
}

# NOTES:
#===============
# One path where systemd starts, and stops
#  another, where pipe or IPC command stops
# Also can start,stop without systemd

Service=unvanquished-server

config=/etc/sysconfig/${Service}
if [ -s ${config} ]; then
	. ${config}
else
	echo "#!# Error: Config not found: ${config}"
	exit 1
fi

srv_log="$HOMEPATH/unv_srv.log"
fifo_pipe="$HOMEPATH/unv_in.pipe"

flag_console=0
console_mode_sentinel="$HOMEPATH/mode_console"
[ -e "$console_mode_sentinel" ] && flag_console=1

IPC_send(){
	if [ -e "$HOMEPATH/lock-server" ]; then
		${LIBPATH}/daemonded -libpath $LIBPATH -pakpath $PAKPATH -homepath $HOMEPATH "$@" >> ${srv_log} 2>&1 &
	fi
}
pipe_cmd(){
	if [ $flag_console == 1 ]; then
		IPC_send "$@"
	else
		[ -p "${fifo_pipe}" ] && echo "$@" > ${fifo_pipe}
	fi
}

case "$1" in
	"stop"|"quit"|"exit")
		pipe_cmd "quit"
		sleep 5s # systemd stop: wait for cleanup by script
		exit 0
		;;
	"cmd"|"command"|"send")
		shift
		pipe_cmd "$@"
		exit 0
		;;
	"con"|"console"|"curses")
		shift
		flag_console=1
		;;
esac


# SERVICE START
#==================
service_pid=0

if [ -e "$HOMEPATH/lock-server" ]; then
	echo "#!# Service all ready running. Use $thisName cmd <commands>."
	exit 1
fi

mk_fifo(){
        [ ! -e "${1}" ] && mkfifo -m660 "${1}" >> ${srv_log} 2>&1
}
rm_fifo(){
        [ -p "${1}" ] && rm "${1}" >> ${srv_log} 2>&1
}

logThis "-*-*- $Service Start -*-*-" "${srv_log}"

if [ $flag_console == 1 ]; then
	logThis "In console mode: Arguments: $@" "${srv_log}"
    
	touch "$console_mode_sentinel" >> ${srv_log} 2>&1  # file sentinel
    
	${LIBPATH}/daemonded -libpath $LIBPATH -pakpath $PAKPATH -homepath $HOMEPATH -curses "$@"
    
	[ -e "$console_mode_sentinel" ] && rm "$console_mode_sentinel" >> ${srv_log} 2>&1
else
	# Need a second named pipe, for proper handling of 'tail -f'
	tmp_fifo="$HOMEPATH/._${Service}.fifo"

	mk_fifo "${fifo_pipe}"
	mk_fifo "${tmp_fifo}"

	# Open and hold tmp fifo
	$(3>$tmp_fifo) &

	# Start daemon engine
	${LIBPATH}/daemonded -libpath $LIBPATH -pakpath $PAKPATH -homepath $HOMEPATH "$@" < ${tmp_fifo} >> ${srv_log} 2>&1 &
	service_pid=$!

	# Keep fifo pipe open for direct writes, no buffering - tail dies on daemonded exit
	# Script execution spins here
	tail --pid ${service_pid} -f "${fifo_pipe}" > "${tmp_fifo}" 2>> ${srv_log}

	rm_fifo "${tmp_fifo}"
	rm_fifo "${fifo_pipe}"

fi #flag_console

logThis "-*-*- $Service Complete -*-*-" "${srv_log}"

exit 0
#eof