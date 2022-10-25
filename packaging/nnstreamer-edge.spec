%define     test_script $(pwd)/packaging/run_unittests.sh

# Default features for Tizen releases
%define     mqtt_support 1
%define     aitt_support 1

# Define features for TV releases
%if "%{?profile}" == "tv"
%define     mqtt_support 0
%define     aitt_support 0
%endif

%bcond_with tizen

Name:       nnstreamer-edge
Summary:    Common library set for nnstreamer-edge
# Synchronize the version of nnstreamer-edge library.
# 1. CMake : ./CMakeLists.txt
# 2. Ubuntu : ./debian/changelog
# 3. Tizen : ./packaging/nnstreamer-edge.spec
Version:    0.2.1
Release:    1
Group:      Machine Learning/ML Framework
Packager:   Sangjung Woo <sangjung.woo@samsung.com>
License:    Apache-2.0
Source0:    %{name}-%{version}.tar.gz
Source1001: nnstreamer-edge.manifest

BuildRequires:  cmake

%if %{with tizen}
BuildRequires:  pkgconfig(dlog)
%endif

%if 0%{?mqtt_support}
BuildRequires:  pkgconfig(libmosquitto)
%endif

%if 0%{?aitt_support}
BuildRequires:  aitt-devel
%endif

%if 0%{?unit_test}
BuildRequires:  gtest-devel
BuildRequires:  procps
BuildRequires:  mosquitto

%if 0%{?testcoverage}
BuildRequires:  lcov
%endif
%endif

%description
nnstreamer-edge provides remote source nodes for NNStreamer pipelines without GStreamer dependencies.
It also contains communicaton library for sharing server node information & status.

%package devel
Summary: development package for nnstreamer-edge
Requires: nnstreamer-edge = %{version}-%{release}
%description devel
It is a development package for nnstreamer-edge.

%if 0%{?unit_test}
%package unittest
Summary: test program for nnstreamer-edge library
%description unittest
It is a test program for nnstreamer-edge library.

%if 0%{?testcoverage}
%package unittest-coverage
Summary: Unittest coverage result for nnstreamer-edge
%description unittest-coverage
HTML pages of lcov results of nnstreamer-edge generated during rpm build
%endif
%endif

%if 0%{?unit_test}
%define enable_unittest -DENABLE_TEST=ON
%else
%define enable_unittest -DENABLE_TEST=OFF
%endif

%if 0%{?mqtt_support}
%define enable_mqtt -DMQTT_SUPPORT=ON
%else
%define enable_mqtt -DMQTT_SUPPORT=OFF
%endif

%if 0%{?aitt_support}
%define enable_aitt -DAITT_SUPPORT=ON
%else
%define enable_aitt -DAITT_SUPPORT=OFF
%endif

%prep
%setup -q
cp %{SOURCE1001} .

%build

%if 0%{?unit_test}
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
%endif # unittest

mkdir -p build
pushd build
%cmake .. \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DVERSION=%{version} \
    %{enable_unittest} %{enable_mqtt} %{enable_aitt}

make %{?jobs:-j%jobs}
popd

%install
rm -rf %{buildroot}
pushd build
%make_install
popd

%if 0%{?unit_test}
LD_LIBRARY_PATH=./src bash %{test_script} ./tests/unittest_nnstreamer-edge

%if 0%{?aitt_support}
LD_LIBRARY_PATH=./src bash %{test_script} ./tests/unittest_nnstreamer-edge-aitt
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
%endif # testcoverage
%endif # unittest

%clean
rm -rf %{buildroot}

%files
%manifest nnstreamer-edge.manifest
%defattr(-,root,root,-)
%license LICENSE
%{_libdir}/libnnstreamer-edge.so*

%files devel
%{_includedir}/nnstreamer-edge.h
%{_libdir}/pkgconfig/nnstreamer-edge.pc

%if 0%{?unit_test}
%files unittest
%manifest nnstreamer-edge.manifest
%defattr(-,root,root,-)
%{_bindir}/unittest_nnstreamer-edge

%if 0%{?aitt_support}
%{_bindir}/unittest_nnstreamer-edge-aitt
%endif

%if 0%{?testcoverage}
%files unittest-coverage
%{_datadir}/nnstreamer-edge/unittest/*
%endif
%endif # unittest

%changelog
* Fri Sep 30 2022 Sangjung Woo <sangjung.woo@samsung.com>
- Start development of 0.2.1 for Tizen 7.5 release (0.2.2)

* Fri Jul 1 2022 Sangjung Woo <sangjung.woo@samsung.com>
- Start development of 0.1.0

* Wed Sep 01 2021 Sangjung Woo <sangjung.woo@samsung.com>
- Start development of 0.0.1
