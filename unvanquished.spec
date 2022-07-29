%define debug_package	%{nil}
%define _service %{name}-server
%define _service_user %{name}
%define _service_home /var/lib/%{_service}
# need this to avoid stripping 
# witch causes failure at runtime with an IPC error.
%global __os_install_post %{nil}
%global __strip /bin/true

Summary:	Sci-fi RTS and FPS game
Name:		unvanquished
Version:	0.52.0
Release:	1
License:	GPLv3
Group:		Games/Arcade
Url:		http://unvanquished.net/
Source:		https://github.com/Unvanquished/Unvanquished/archive/Unvanquished-%{version}.tar.gz
# We should package google-NaCl separately ? Symbianflo
Source1:	http://dl.unvanquished.net/deps/linux32-4.tar.bz2
Source2:	http://dl.unvanquished.net/deps/linux64-4.tar.bz2
#
Source3:	http://dl.unvanquished.net/deps/pnacl-3.zip
# cbse required but not included in tarball
Source4:	CBSE-Toolchain-1d62124.zip
Source10:	%{name}-service.sh
Source11:	server.cfg
Source12:	maprotation.cfg
Source13:	NOTES.txt
Source100:	unvanquished.rpmlintrc

BuildRequires:	cmake
BuildRequires:	desktop-file-utils
BuildRequires:	xz
BuildRequires:	gmp-devel
BuildRequires:	hicolor-icon-theme
BuildRequires:	pkgconfig(geoip)
BuildRequires:	pkgconfig(libjpeg)
BuildRequires:	tinyxml-devel
BuildRequires:	pkgconfig(ncurses)
BuildRequires:	bzip2-devel
BuildRequires:	unzip
BuildRequires:	pkgconfig(freetype2)
BuildRequires:	pkgconfig(glew)
BuildRequires:	pkgconfig(libcurl)
BuildRequires:	pkgconfig(libpng)
BuildRequires:	pkgconfig(libwebp)
BuildRequires:	pkgconfig(nettle)
BuildRequires:	pkgconfig(openal)
BuildRequires:	pkgconfig(opus)
BuildRequires:	pkgconfig(opusfile)
BuildRequires:	pkgconfig(sdl2)
BuildRequires:	pkgconfig(speex)
BuildRequires:	pkgconfig(theora)
BuildRequires:	pkgconfig(vorbis)
BuildRequires:	python
BuildRequires:	python-yaml
BuildRequires:	python-jinja2

Requires:	opengl-games-utils
# those are circular , and suggested on the spec files
# just because I'm not good in chain-build on abf.Symbianflo.
Requires:	%{name}-data = %{version}
Requires:	%{name}-maps
Requires:	%{name}-service

%description
Players fight online in team based combat in a war of aliens against humans.

While the humans are equipped with weapons that they use to exterminate 
the alien presence, the aliens have only their pincers and a few special 
attacks, such as poison gas, and ranged electrical and projectile attacks. 
Players do not spawn at random points in the map; instead, each map has 
default spawn points and both teams are capable of moving 
them wherever they please. 
Both teams have other buildings that round out their base, 
such as machinegun turrets for the humans and barricades for the aliens. 
Either team wins by destroying the opposing team's spawn points 
and killing any remaining members of that team before they 
are able to build any more spawn points or the game timer ends.
This package only contains the game engine.

%files
%doc GPL.txt COPYING.txt NOTES.txt
%{_bindir}/*
%{_libdir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/128x128/apps/%{name}.png
#--------------------------------------------------------------
# Service

%package service
Summary:	Run game server as a service
Group:		Games/Arcade
Requires:	%{name} >= %{version}

%description service
This package installs the files and config 
to run a unvanquished server as a systemd service.

** THIS IS A WORK IN PROGRESS - EXPERIMENTAL**
 - Service control and monitoring still experimental.
 - Connection to server instance's console not telnet'esque yet.

%files service
%doc NOTES.txt
%config(noreplace)  /var/adm/fillup-templates/sysconfig.%{_service}
%{_unitdir}/%{_service}.service
%attr(750,%{_service_user},%{_service_user}) %dir %{_service_home}/
%attr(750,%{_service_user},%{_service_user}) %dir %{_service_home}/config/
%attr(750,%{_service_user},%{_service_user}) %dir %{_service_home}/game/
%attr(750,%{_service_user},%{_service_user}) %dir %{_service_home}/pkg/
%attr(0750,%{_service_user},%{_service_user}) %{_service_home}/%{name}-service.sh
%attr(0750,%{_service_user},%{_service_user}) %{_service_home}/%{_service}-cmd
%attr(0640,%{_service_user},%{_service_user}) %config(noreplace) %{_service_home}/config/server.cfg
%attr(0640,%{_service_user},%{_service_user}) %config(noreplace) %{_service_home}/game/maprotation.cfg
#--------------------------------------------------------------

%prep
%setup -qn Unvanquished-%{version}
#iconv -f iso8859-1 -t utf-8 GPL.txt > GPL.txt.conv && mv -f GPL.txt.conv GPL.txt
# Google Native Client (NaCl)
pushd daemon/external_deps
%ifarch i586
tar -xjvf %{SOURCE1}
%endif
%ifarch x86_64
tar -xjvf %{SOURCE2}
%endif
unzip -o %{SOURCE3}
popd

pushd src/utils/cbse/
unzip %{SOURCE4}
mv CBSE-Toolchain-*/* .
popd

mkdir -p build

%build
%cmake \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_SKIP_RPATH=ON \
      -DBUILD_GAME_NATIVE_DLL=OFF \
      -DBUILD_GAME_NATIVE_EXE=OFF \
      -DBUILD_GAME_NACL=OFF

%make_build

%install
# doc
cp -a %{SOURCE13} ./

# Icons
install -Dm644 debian/%{name}.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/%{name}.png

# CLI
mkdir command-ui
pushd command-ui

# game client wrapper
# ----------------------
cat >> %{name} <<EOF
#!/bin/sh

app_args=''
uri=''

while [ \$# -gt 0 ]; do
case "\$1" in
    # handle URI unv:// passed in
    unv://*)
    	uri=\$(echo "\$1" | grep -o '^unv://[^[:space:]+;]*')
    	app_args="\${app_args} +connect \${uri}"
        ;;
    *)
    	app_args="\${app_args} \$1"
        ;;
esac
shift
done

# Note: argument stucture changed in alpha 37: 
#   -set <variable> <value> is now the preferred way to set a configuration variable.
# 	+set <variable> <value> and +<command> are only applied after engine initialization.
exec %{_libdir}/%{name}/daemon -libpath %{_libdir}/%{name} -pakpath %{_datadir}/%{name}/pkg \${app_args}
EOF
# ----------------------

# game server wrapper
# ----------------------
cat >> %{name}-server <<EOF
#!/bin/sh

# Note: argument stucture changed in alpha 37: 
#   -set <variable> <value> is now the preferred way to set a configuration variable.
# 	+set <variable> <value> and +<command> are only applied after engine initialization.
exec %{_libdir}/%{name}/daemonded -libpath %{_libdir}/%{name}/ -pakpath %{_datadir}/%{name}/pkg -curses "\$@"
EOF
# ----------------------
# binary
mkdir -p %{buildroot}%{_bindir}/
install -m 755 %{name} %{name}-server %{buildroot}%{_bindir}/
# ----------------------
# menu entry
cat >> %{name}.desktop <<EOF
[Desktop Entry]
Categories=Game;ActionGame;
Name=Unvanquished
GenericName=sci-fi RTS and FPS mashup
Type=Application
Exec=%{name}
Icon=%{name}
MimeType=x-scheme-handler/unv;
EOF
# ----------------------
install -Dm 644 %{name}.desktop %{buildroot}%{_datadir}/applications/%{name}.desktop


# Server service
# ----------------------
cat >> %{_service}.conf <<EOF
# Unvanquished Dedicated Server - Environment Config

# Daemonded lib directory
LIBPATH=%{_libdir}/%{name}

# Server Store
HOMEPATH=%{_service_home}

# .pk3 Package Store - for installed game data and maps
PAKPATH=%{_datadir}/%{name}/pkg

# Startup Server Configuration
EXEC=server.cfg
EOF
# ----------------------

# For /etc/sysconfig/
install -Dm 644 %{_service}.conf %{buildroot}/var/adm/fillup-templates/sysconfig.%{_service}

install -Dm 750 %{SOURCE10} %{buildroot}%{_service_home}/%{name}-service.sh

# Systemd service file
# ----------------------
cat >> %{_service}.service <<EOF
[Unit]
Description=Unvanquished Dedicated Server
After=network.target

[Service]
EnvironmentFile=/etc/sysconfig/%{_service}
User=%{_service_user}
Group=%{_service_user}
ExecStart=%{_service_home}/%{name}-service.sh +exec \$EXEC
ExecStop=%{_service_home}/%{name}-service.sh stop

[Install]
WantedBy=multi-user.target
EOF
# ----------------------
install -Dm 644 %{_service}.service %{buildroot}%{_unitdir}/%{_service}.service

# Administer the running service instance
# ----------------------
cat >> %{_service}-cmd <<EOF
#!/bin/sh
# Send command(s) to running daemonded instance started as a service
#
test -s /etc/sysconfig/%{_service} && . /etc/sysconfig/%{_service}

service_state=\$(systemctl is-active %{_service}.service)
if [ "\${service_state}" != "active" ]; then
	echo "No active instance of %{_service}, Exiting."
    exit 1
fi

# Administer running service instance - To send it commands.
#   -homepath must be same as running instance
exec %{_libdir}/%{name}/daemonded -libpath \$LIBPATH -pakpath \$PAKPATH -homepath \$HOMEPATH "\$@"

EOF
# ----------------------
install -Dm 750 %{_service}-cmd %{buildroot}%{_service_home}/%{_service}-cmd

#
popd # command-ui

# Service Home
install -Dm 640 %{SOURCE11} %{buildroot}%{_service_home}/config/server.cfg
install -Dm 640 %{SOURCE12} %{buildroot}%{_service_home}/game/maprotation.cfg
install -d %{buildroot}%{_service_home}/pkg


# == Binary Assets ==
mkdir -p %{buildroot}%{_libdir}/%{name}/

cd build

# Application
install -m 755 daemon daemonded daemon-tty %{buildroot}%{_libdir}/%{name}/

# Helpers
install -m 755 nacl_helper_bootstrap nacl_loader %{buildroot}%{_libdir}/%{name}/

%ifarch i586
install -m 755 irt_core-x86.nexe %{buildroot}%{_libdir}/%{name}/
%endif
%ifarch x86_64
install -m 755 irt_core-x86_64.nexe %{buildroot}%{_libdir}/%{name}/
%endif

%pre service
# Server Setup of User / Group
getent group %{_service_user} >/dev/null || groupadd -r %{_service_user}
getent passwd %{_service_user} >/dev/null || useradd -r -g %{_service_user} \
	-d %{_service_home} -s /bin/false -c "Unvanquished Dedicated Server" %{_service_user}
