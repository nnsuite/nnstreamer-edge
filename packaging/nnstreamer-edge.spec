%define     test_script $(pwd)/packaging/run_unittests.sh

Name:       nnstreamer-edge
Summary:    Common library set for nnstreamer-edge
Version:    0.0.1
Release:    1
Group:      Machine Learning/ML Framework
Packager:   Sangjung Woo <sangjung.woo@samsung.com>
License:    Apache-2.0
Source0:    %{name}-%{version}.tar.gz
Source1001: nnstreamer-edge.manifest

BuildRequires:  cmake
BuildRequires:  pkgconfig(paho-mqtt-c)
%if 0%{?sensor_test}
BuildRequires:  gtest-devel
%endif

%if 0%{?testcoverage}
BuildRequires:	lcov
%endif

%description
nnstreamer-edge provides remote source nodes for NNStreamer pipelines without GStreamer dependencies.
It also contains communicaton library for sharing server node information & status

%package sensor
Summary: communication library for edge sensor
%description sensor
It is a communication library for edge sensor devices.
This library supports publishing the sensor data to the GStreamer pipeline without GStreamer / Glib dependency.

%package sensor-test
Summary: test program for nnstreamer-edge-sensor library
%description sensor-test
It is a test program for nnstreamer-edge-sensor library.
It read the jpeg data and publishes it as "TestTopic" topic name 10 times.
If data is successfully received, then the image is shown on the server-side.

%package sensor-devel
Summary: development package for nnstreamer-edge-sensor
Requires: nnstreamer-edge = %{version}-%{release}
%description sensor-devel
It is a development package for nnstreamer-edge-sensor.

%if 0%{?testcoverage}
%package unittest-coverage
Summary: Unittest coverage result for nnstreamer-edge
%description unittest-coverage
HTML pages of lcov results of nnstreamer-edge generated during rpm build
%endif

%define enable_sensor_test -DENABLE_TEST=OFF
%if 0%{?sensor_test}
%define enable_sensor_test -DENABLE_TEST=ON
%endif

%prep
%setup -q
cp %{SOURCE1001} .

%build

%if 0%{?testcoverage}
# To test coverage, disable optimizations (and should unset _FORTIFY_SOURCE to use -O0)
CFLAGS=`echo $CFLAGS | sed -e "s|-O[1-9]|-O0|g"`
CFLAGS=`echo $CFLAGS | sed -e "s|-Wp,-D_FORTIFY_SOURCE=[1-9]||g"`
CXXFLAGS=`echo $CXXFLAGS | sed -e "s|-O[1-9]|-O0|g"`
CXXFLAGS=`echo $CXXFLAGS | sed -e "s|-Wp,-D_FORTIFY_SOURCE=[1-9]||g"`

export CFLAGS+=" -fprofile-arcs -ftest-coverage -g"
export CXXFLAGS+=" -fprofile-arcs -ftest-coverage -g"
export FFLAGS+=" -fprofile-arcs -ftest-coverage -g"
export LDFLAGS+=" -lgcov"
%endif

mkdir -p build
pushd build
%cmake .. \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DVERSION=%{version} %{enable_sensor_test}

make %{?jobs:-j%jobs}
popd

%install
rm -rf %{buildroot}
pushd build
%make_install
popd

%if 0%{?sensor_test}
LD_LIBRARY_PATH=./src bash %{test_script} ./tests/unittest_edge_sensor
%endif

%if 0%{?testcoverage}
# 'lcov' generates the date format with UTC time zone by default. Let's replace UTC with KST.
# If you can get a root privilege, run ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
TZ='Asia/Seoul'; export TZ

# Get commit info
VCS=`cat ${RPM_SOURCE_DIR}/nnstreamer-edge.spec | grep "^VCS:" | sed "s|VCS:\\W*\\(.*\\)|\\1|"`

# Create human readable coverage report web page.
# Create null gcda files if gcov didn't create it because there is completely no unit test for them.
find . -name "*.gcno" -exec sh -c 'touch -a "${1%.gcno}.gcda"' _ {} \;
# Remove gcda for meaningless file (CMake's autogenerated)
find . -name "CMakeCCompilerId*.gcda" -delete
find . -name "CMakeCXXCompilerId*.gcda" -delete
# Generate report
lcov -t 'NNStreamer-edge unittest coverage' -o unittest.info -c -d . -b $(pwd) --no-external
# Exclude test files.
lcov -r unittest.info "*/tests/*" -o unittest-filtered.info
# Visualize the report
genhtml -o result unittest-filtered.info -t "NNStreamer-edge %{version}-%{release} ${VCS}" --ignore-errors source -p ${RPM_BUILD_DIR}

mkdir -p %{buildroot}%{_datadir}/nnstreamer-edge/unittest/
cp -r result %{buildroot}%{_datadir}/nnstreamer-edge/unittest/
%endif # test coverage

%clean
rm -rf %{buildroot}

%files sensor
%manifest nnstreamer-edge.manifest
%defattr(-,root,root,-)
%{_libdir}/libedge-sensor.so*

%if 0%{?sensor_test}
%files sensor-test
%manifest nnstreamer-edge.manifest
%defattr(-,root,root,-)
%{_bindir}/test_edge_sensor
%endif

%files sensor-devel
%{_includedir}/edge_sensor.h
%{_libdir}/pkgconfig/nnstreamer-edge-sensor.pc

%if 0%{?testcoverage}
%files unittest-coverage
%{_datadir}/nnstreamer-edge/unittest/*
%endif
