#define debug_package	%{nil}
%define oname Unvanquished

Name:           unvanquished
Version:        0.15.0
Release:        2
Summary:        Sci-fi RTS and FPS game
License:        GPLv3
Group:          Games/Arcade
Url:            http://unvanquished.net/
Source0:        http://unvanquished.net/downloads/sources/bloated/%{name}-%{version}.tar.xz
BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  gmp-devel
BuildRequires:  hicolor-icon-theme
BuildRequires:  libjpeg-devel
BuildRequires:  ncurses-devel
BuildRequires:  pkgconfig(freetype2)
BuildRequires:  pkgconfig(glew)
BuildRequires:  pkgconfig(libcurl)
%if %{mdvver} == 201200
BuildRequires:  pkgconfig(libpng12)
%endif
%if %{mdvver} >= 201210
BuildRequires:  pkgconfig(libpng)
%endif
BuildRequires:  pkgconfig(libwebp)
BuildRequires:  pkgconfig(nettle)
BuildRequires:  pkgconfig(openal)
BuildRequires:  pkgconfig(sdl)
BuildRequires:  pkgconfig(speex)
BuildRequires:  pkgconfig(theora)
BuildRequires:  pkgconfig(vorbis)
BuildRequires:  pkgconfig(glu)
BuildRequires:  pkgconfig(gl)
BuildRequires:  pkgconfig(glut)
Requires:       opengl-games-utils
Requires:       unvanquished-data == %{version}
Suggests:       unvanquished-maps == %{version}


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

%prep
%setup -q 
iconv -f iso8859-1 -t utf-8 GPL.txt > GPL.txt.conv && mv -f GPL.txt.conv GPL.txt

%build
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX="%{_libdir}" \
      -DCMAKE_INSTALL_BINDIR="%{_libdir}/%{oname}" \
      -DCMAKE_INSTALL_LIBDIR="%{_libdir}/%{oname}" \
      -DUSE_CURSES=0 \
      -DUSE_CIN_XVID=0 \
      -DUSE_INTERNAL_SDL=0 \
      -DUSE_INTERNAL_CRYPTO=0 \
      -DUSE_INTERNAL_JPEG=0 \
      -DUSE_INTERNAL_SPEEX=0 \
      -DUSE_INTERNAL_GLEW=0 \
      ..

%make

%install
# icons
mkdir -p  %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/
install -Dm644 debian/unvanquished.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/unvanquished.png

# wrapper game
mkdir -p %{buildroot}%{_bindir}
cat >> %{buildroot}%{_bindir}/unvanquished.sh <<EOF
#!/bin/sh
cd %{_libdir}/%{oname}
exec %{_libdir}/%{oname}/daemon \
	+set fs_libpath "%{_libdir}/%{oname}" \
	+set fs_basepath "%{_datadir}/%{oname}" \
	"$@"
EOF
chmod +x %{buildroot}%{_bindir}/unvanquished.sh

#wrapper server
cat >> %{buildroot}%{_bindir}/unvanquished-server.sh <<EOF
#!/bin/sh
cd %{_libdir}/%{oname}
exec %{_libdir}/%{name}/daemonded \
	+set fs_libpath "%{_libdir}/%{oname}/" \
	+set fs_basepath "%{_datadir}/%{oname}" \
	"$@"
EOF
chmod +x %{buildroot}%{_bindir}/unvanquished-server.sh

# menu entry
mkdir -p %{buildroot}%{_datadir}/applications/
cat >> %{buildroot}%{_datadir}/applications/unvanquished.desktop <<EOF
[Desktop Entry]
Categories=Game;ActionGame;
Name=%{name}
GenericName=sci-fi RTS and FPS mashup
Type=Application
Exec=unvanquished.sh
Icon=unvanquished
StartupNotify=true
EOF

%makeinstall_std -C build

chmod a+x %{buildroot}%{_libdir}/%{oname}/main/game.so
chmod a+x %{buildroot}%{_libdir}/%{oname}/main/cgame.so
chmod a+x %{buildroot}%{_libdir}/%{oname}/main/ui.so


%files
%doc GPL.txt COPYING.txt
%{_bindir}/*
%{_libdir}/%{oname}/
%{_datadir}/applications/unvanquished.desktop
%{_datadir}/icons/hicolor/128x128/apps/unvanquished.png


