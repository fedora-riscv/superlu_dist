# Copyright (c) 2016 Dave Love, Liverpool University
# Copyright (c) 2018 Dave Love, University of Manchester
# MIT licence, per Fedora policy.

# This flag prevents the linkage to libptscotch.so
%undefine _ld_as_needed

# Choose the build method
%bcond_without cmake
%bcond_with manual

# Choose if using 64-bit integers for indexing sparse matrices
%if %{?__isa_bits:%{__isa_bits}}%{!?__isa_bits:32} == 64
%bcond_with index64
%endif

%bcond_without mpich
%bcond_without openmpi

%if %{with openmpi}
%global openmpi openmpi
%else
%global openmpi %nil
%endif
%if %{with mpich}
%global mpich mpich
%else
%global mpich %nil
%endif

# For library soname.  Start at one in case we need the incompatible
# v4 packaged separately.
%if %{with manual}
%global major 1
%global minor 4
%global miner 0
%global sover %major.%minor.%miner
%endif

# Following scalapack
%bcond_without optimized_blas

%if 0%{?fedora} || 0%{?rhel} >= 9
%global blaslib flexiblas
%if %{with index64}
%global OPENBLASLINK -lflexiblas64
%global OPENBLASLIB /libflexiblas64.so
%else
%global OPENBLASLINK -lflexiblas
%global OPENBLASLIB /libflexiblas.so
%endif
%else
%global blaslib openblas
%if %{with index64}
%global OPENBLASLINK -lopenblaso64
%global OPENBLASLIB /libopenblaso64.so
%else
%global OPENBLASLINK -lopenblaso
%global OPENBLASLIB /libopenblaso.so
%endif
%endif

# Tests failed on riscv64, disable it for default.
%ifarch riscv64
%bcond_with check
%else
%bcond_without check
%endif

%if %{with cmake}
# Enable CombBLAS support
%bcond_with CombBLAS
%endif

# RHEL8 does not provide Metis64
%if %{with index64}
BuildRequires: metis64-devel
%global METISLINK -lmetis64
%global METISLIB %{_libdir}/libmetis64.so
%global METISINC %{_includedir}/metis64.h
%else
BuildRequires: metis-devel
%global METISLINK -lmetis
%global METISLIB %{_libdir}/libmetis.so
%global METISINC %{_includedir}/metis.h
%endif

%if 0%{?el7}
# For good enough C++
%global dts devtoolset-7-
%endif

Name: superlu_dist
Version: 8.1.0
Release: 2.rv64%{?dist}
Epoch:   1

Summary: Solution of large, sparse, nonsymmetric systems of linear equations
License: BSD
URL: http://crd-legacy.lbl.gov/~xiaoye/SuperLU/
Source0: https://github.com/xiaoyeli/superlu_dist/archive/v%version/%name-%version.tar.gz
Source1: %name-make.inc

# Use CFLAGS in INSTALL/Makefile (was only failing on some targets)
Patch0: %name-inst.patch
Patch1: %name-fix_pkgconfig_creation.patch

Patch3: %name-scotch_parmetis.patch

# Longer tests take 1000 sec or timeout, so don't run them
Patch4: %name-only_short_tests.patch

BuildRequires: scotch-devel
BuildRequires: %{?dts}gcc-c++, dos2unix, chrpath
%if %{with cmake}
BuildRequires: cmake3
%endif
%if %{with optimized_blas}
BuildRequires: %{blaslib}-devel
%endif


%global desc \
SuperLU is a general purpose library for the direct solution of large,\
sparse, nonsymmetric systems of linear equations.  The library is\
written in C and is callable from either C or Fortran program.  It\
uses MPI, OpenMP and CUDA to support various forms of parallelism.  It\
supports both real and complex datatypes, both single and double\
precision, and 64-bit integer indexing.  The library routines performs\
an LU decomposition with partial pivoting and triangular system solves\
through forward and back substitution.  The LU factorization routines\
can handle non-square matrices but the triangular solves are performed\
only for square matrices.  The matrix columns may be preordered\
(before factorization) either through library or user supplied\
routines.  This preordering for sparsity is completely separate from\
the factorization.  Working precision iterative refinement subroutines\
are provided for improved backward stability.  Routines are also\
provided to equilibrate the system, estimate the condition number,\
calculate the relative backward error, and estimate error bounds for\
the refined solutions.\
\
This version uses MPI and OpenMP.


%description
%desc

%if %{with openmpi}
%package openmpi
Summary:       Solution of large, sparse, nonsymmetric systems of linear equations - openmpi
BuildRequires: openmpi-devel
# ptscotch-openmpi-devel-parmetis unavailable on rhel8 ??
BuildRequires: ptscotch-openmpi-devel >= 6.0.5 %{!?el8:ptscotch-openmpi-devel-parmetis >= 6.0.5}
%if %{with CombBLAS}
BuildRequires: combblas-openmpi-devel
%endif
Requires:      gcc-gfortran%{?_isa}

%description openmpi
%desc

This is the openmpi version.

%package openmpi-devel
Summary: Development files for %name-openmpi
Requires: openmpi-devel%{?_isa}
Requires: %name-openmpi%{?_isa} = %{epoch}:%version-%release
Provides: %name-openmpi-static = %{epoch}:%version-%release

%description openmpi-devel
Development files for %name-openmpi
%endif

%package doc
Summary: Documentation for %name
BuildArch: noarch

%description doc
Documentation for %name

%if %{with mpich}
%package mpich
Summary:       Solution of large, sparse, nonsymmetric systems of linear equations - mpich
BuildRequires: mpich-devel
BuildRequires: ptscotch-mpich-devel  >= 6.0.5
BuildRequires: ptscotch-mpich-devel-parmetis  >= 6.0.5
%if %{with CombBLAS}
BuildRequires: combblas-mpich-devel
%endif
Requires:      gcc-gfortran%{?_isa}

%description mpich
%desc

This is the mpich version.

%package mpich-devel
Summary: Development files for %name-mpich
Requires: mpich-devel%{?_isa}
Requires: ptscotch-mpich-devel%{?_isa} ptscotch-mpich-devel-parmetis%{?_isa}
Requires: %name-mpich%{?_isa} = %{epoch}:%version-%release
Provides: %name-mpich-static = %{epoch}:%version-%release

%description mpich-devel
Development files for %name-mpich
%endif


%prep
%autosetup -n superlu_dist-%version -N

%if %{with manual}
cp %SOURCE1 make.inc
%patch0 -p1 -b .orig
%endif

%if %{with cmake}
dos2unix CMakeLists.txt
%patch1 -p1 -b .fix_pkgconfig_creation
%endif
%patch4 -p1 -b .only_short_tests

%build
%if %{with manual}
%{?dts:source /opt/rh/devtoolset-7/enable}
export CFLAGS="%build_cflags" LDFLAGS="%build_ldflags" CXXFLAGS="%build_cxxflags"
# This order to leave openmpi version in place for %%check
for m in %mpich %openmpi; do
case $m in
openmpi) %_openmpi_load ;;
mpich) %_mpich_load ;;
esac
find -name \*.[oa] | xargs rm 2>/dev/null || true # no "clean" target
%if %{with optimized_blas}
make SuperLUroot=$(pwd) BLASLIB=%{OPENBLASLINK} INCLUDEDIR=$(pwd)/SRC V=1
%else
make blaslib HEADER=. BLASLIB='../libblas.a' INCLUDEDIR=%_includedir V=1
make SuperLUroot=$(pwd) BLASDEF= BLASLIB='../libblas.a' INCLUDEDIR=$(pwd)/SRC V=1
%endif
mkdir -p tmp $m
pushd tmp
ar x ../SRC/libsuperlu_dist.a
mpicxx -shared -Wl,-soname=libsuperlu_dist.so.%major \
      -o ../$m/libsuperlu_dist.so.%sover *.o -fopenmp \
      -lptscotchparmetis -lscotchmetis -lscotch -lptscotch \
      -lptscotcherr -lptscotcherrexit \
      %{?with_optimized_blas:%OPENBLASLINK} \
      %{?__global_ldflags}
popd
case $m in
openmpi)
  cp -a EXAMPLE/pddrive .
  %_openmpi_unload ;;
mpich)
  make -C EXAMPLE clean
  %_mpich_unload ;;
esac
done
%endif
# Manual build method

%if %{with cmake}
%if 0%{?el7}
%{?dts:source /opt/rh/devtoolset-7/enable}
%endif

%if %{with openmpi}
%{_openmpi_load}
mkdir -p build/openmpi
%if 0%{?rhel} == 7
. /opt/rh/devtoolset-7/enable
%endif
export CC=$MPI_BIN/mpicc
export CXX=$MPI_BIN/mpic++
export CXXFLAGS="%optflags -I$MPI_INCLUDE"
export LDFLAGS="%build_ldflags -L$MPI_LIB -lptscotch"
%cmake3 -B build/openmpi -DCMAKE_BUILD_TYPE:STRING=Release \
 -DBUILD_STATIC_LIBS:BOOL=FALSE \
 -DCMAKE_Fortran_COMPILER:FILEPATH=$MPI_BIN/mpifort \
 -DMPIEXEC_EXECUTABLE:FILEPATH=$MPI_BIN/mpiexec \
%if %{with CombBLAS}
 -DTPL_COMBBLAS_INCLUDE_DIRS:PATH="$MPI_INCLUDE/CombBLAS;$MPI_INCLUDE/CombBLAS/3DSpGEMM;$MPI_INCLUDE/CombBLAS/Applications;$MPI_INCLUDE/CombBLAS/BipartiteMatchings" \
 -DTPL_COMBBLAS_LIBRARIES:STRING=$MPI_LIB/libCombBLAS.so -DTPL_ENABLE_COMBBLASLIB:BOOL=ON \
%endif
 -DTPL_BLAS_LIBRARIES:FILEPATH=%{_libdir}%{OPENBLASLIB} -DTPL_ENABLE_LAPACKLIB:BOOL=OFF -DTPL_LAPACK_LIBRARIES:BOOL=OFF \
 -DMPI_C_HEADER_DIR:PATH="$MPI_INCLUDE -I%{METISINC}" \
 -DMPI_C_LINK_FLAGS:STRING="-L$MPI_LIB -lptscotch -lptscotcherr -lptscotcherrexit -L%{_libdir} %{METISLINK} -lscotch" \
 -DMPI_CXX_LINK_FLAGS:STRING="-L$MPI_LIB -lptscotch -lptscotcherr -lptscotcherrexit -L%{_libdir} %{METISLINK} -lscotch -fopenmp" \
%if 0%{?fedora} || 0%{?rhel} < 8
 -DTPL_PARMETIS_INCLUDE_DIRS:PATH=$MPI_INCLUDE \
 -DTPL_PARMETIS_LIBRARIES:STRING="$MPI_LIB/libptscotchparmetis.so;%{METISLIB}" \
%endif
%if %{with index64}
 -DXSDK_INDEX_SIZE=64 \
%else
 -DXSDK_INDEX_SIZE=32 \
%endif
%if 0%{?rhel} && 0%{?rhel} >= 8
 -DTPL_ENABLE_PARMETISLIB:BOOL=OFF \
%endif
 -Denable_double:BOOL=ON -Denable_complex16:BOOL=ON \
 -Denable_examples:BOOL=ON -Denable_tests:BOOL=ON -DBUILD_TESTING:BOOL=ON \
 -DCMAKE_INSTALL_PREFIX:PATH=%{_prefix} -DCMAKE_INSTALL_BINDIR:PATH=$MPI_BIN -DCMAKE_INSTALL_INCLUDEDIR:PATH=$MPI_INCLUDE/%{name} \
 -DCMAKE_INSTALL_LIBDIR:PATH=$MPI_LIB

%make_build V=1 -C build/openmpi
%{_openmpi_unload}
%endif

%if %{with mpich}
%{_mpich_load}
mkdir -p build/mpich
%if 0%{?rhel} == 7
. /opt/rh/devtoolset-7/enable
%endif
export CC=$MPI_BIN/mpicc
export CXX=$MPI_BIN/mpic++
export CFLAGS="%optflags -DPRNTlevel=0 -DDEBUGlevel=0"
export CXXFLAGS="%optflags -I$MPI_INCLUDE"
export LDFLAGS="%build_ldflags -L$MPI_LIB -lptscotch"
%cmake3 -B build/mpich -DCMAKE_BUILD_TYPE:STRING=Release \
 -DBUILD_STATIC_LIBS:BOOL=FALSE \
 -DCMAKE_Fortran_COMPILER:FILEPATH=$MPI_BIN/mpifort \
 -DMPIEXEC_EXECUTABLE:FILEPATH=$MPI_BIN/mpiexec \
%if %{with CombBLAS}
 -DTPL_COMBBLAS_INCLUDE_DIRS:PATH="$MPI_INCLUDE/CombBLAS;$MPI_INCLUDE/CombBLAS/3DSpGEMM;$MPI_INCLUDE/CombBLAS/Applications;$MPI_INCLUDE/CombBLAS/BipartiteMatchings" \
 -DTPL_COMBBLAS_LIBRARIES:STRING=$MPI_LIB/libCombBLAS.so -DTPL_ENABLE_COMBBLASLIB:BOOL=ON \
%endif
 -DTPL_BLAS_LIBRARIES:FILEPATH=%{_libdir}%{OPENBLASLIB} -DTPL_ENABLE_LAPACKLIB:BOOL=OFF -DTPL_LAPACK_LIBRARIES:BOOL=OFF \
 -DMPI_C_HEADER_DIR:PATH="$MPI_INCLUDE -I%{METISINC}" \
 -DMPI_C_LINK_FLAGS:STRING="-L$MPI_LIB -lptscotch -lptscotcherr -lptscotcherrexit -L%{_libdir} %{METISLINK} -lscotch -fopenmp" \
 -DMPI_CXX_LINK_FLAGS:STRING="-L$MPI_LIB -lptscotch -lptscotcherr -lptscotcherrexit -L%{_libdir} %{METISLINK} -lscotch" \
%if 0%{?fedora} || 0%{?rhel} < 8
 -DTPL_PARMETIS_INCLUDE_DIRS:PATH=$MPI_INCLUDE \
 -DTPL_PARMETIS_LIBRARIES:STRING="$MPI_LIB/libptscotchparmetis.so;%{METISLIB}" \
%endif
%if %{with index64}
 -DXSDK_INDEX_SIZE=64 \
%else
 -DXSDK_INDEX_SIZE=32 \
%endif
%if 0%{?rhel} && 0%{?rhel} >= 8
 -DTPL_ENABLE_PARMETISLIB:BOOL=OFF \
%endif
 -Denable_double:BOOL=ON -Denable_complex16:BOOL=ON \
 -Denable_examples:BOOL=ON -Denable_tests:BOOL=ON -DBUILD_TESTING:BOOL=ON \
 -DCMAKE_INSTALL_PREFIX:PATH=%{_prefix} -DCMAKE_INSTALL_BINDIR:PATH=$MPI_BIN -DCMAKE_INSTALL_INCLUDEDIR:PATH=$MPI_INCLUDE/%{name} \
 -DCMAKE_INSTALL_LIBDIR:PATH=$MPI_LIB

%make_build -C build/mpich
%{_mpich_unload}
%endif
%endif
# CMake build method


%install
%if %{with manual}
for m in %mpich %openmpi; do
case $m in
openmpi) %_openmpi_load ;;
mpich) %_mpich_load ;;
esac
mkdir -p %buildroot$MPI_LIB %buildroot$MPI_INCLUDE/superlu_dist
install -m644 SRC/*.h %buildroot$MPI_INCLUDE/superlu_dist

install -m 755 $m/libsuperlu_dist.so* %buildroot$MPI_LIB
pushd %buildroot$MPI_LIB
ln -s libsuperlu_dist.so.%sover libsuperlu_dist.so
ln -s libsuperlu_dist.so.%sover libsuperlu_dist.so.%major
ln -s libsuperlu_dist.so.%sover libsuperlu_dist.so.%major.%minor
popd
case $m in
openmpi) %_openmpi_unload ;;
mpich) %_mpich_unload ;;
esac
done
%endif
# Manual build method

%if %{with cmake}
%if %{with openmpi}
%{_openmpi_load}
%make_install -C build/openmpi
# Make sure all header files are installed
install -m644 SRC/*.h %buildroot$MPI_INCLUDE/superlu_dist/
rm -rf %buildroot$MPI_LIB/EXAMPLE
rm -rf %buildroot$MPI_LIB/superlu_dist/FORTRAN/CMakeFiles
chrpath -r $MPI_LIB %buildroot$MPI_LIB/libsuperlu_dist*.so*
%{_openmpi_unload}
%endif

%if %{with mpich}
%{_mpich_load}
%make_install -C build/mpich
# Make sure all header files are installed
install -m644 SRC/*.h %buildroot$MPI_INCLUDE/superlu_dist/

rm -rf %buildroot$MPI_LIB/EXAMPLE
rm -rf %buildroot$MPI_LIB/superlu_dist/FORTRAN/CMakeFiles
chrpath -r $MPI_LIB %buildroot$MPI_LIB/libsuperlu_dist*.so*
%{_mpich_unload}
%endif
%endif
# CMake build method


# This is hanging inconsistently in koji, normally on i686 and arm.  I
# can't debug it, so let's hope it doesn't deadlock in realistic
# situations.
%if %{with check}

%check
%if %{with manual}
%{?dts:source /opt/rh/devtoolset-7/enable}
pushd EXAMPLE
%if %{with openmpi}
# just check that it runs
%_openmpi_load
# Allow for more processes than cores
export OMPI_MCA_rmaps_base_oversubscribe=1
mpirun -n 4 ../pddrive -r 2 -c 2 g20.rua
%endif
make clean
%endif
# Manual build method

%if %{with cmake}
%if %{with openmpi}
%{_openmpi_load}
pushd EXAMPLE
# Do not perform on rhel8
# rhbz#1744780
%if 0%{?fedora}
export OMPI_MCA_rmaps_base_oversubscribe=1
mpirun -n 4 -v ../build/openmpi/EXAMPLE/pddrive -r 2 -c 2 g20.rua
%endif
popd
%{_openmpi_unload}
%endif

%if %{with mpich}
%{_mpich_load}
pushd EXAMPLE
export OMPI_MCA_rmaps_base_oversubscribe=1
mpirun -n 4 -v ../build/mpich/EXAMPLE/pddrive -r 2 -c 2 g20.rua
popd
%{_mpich_unload}
%endif
%endif
# CMake build method
%endif
# Check

%if %{with openmpi}
%files openmpi
%license License.txt
%_libdir/openmpi/lib/*.so.*

%files openmpi-devel
%_libdir/openmpi/lib/*.so
%_libdir/openmpi/lib/*.a
%if %{with cmake}
%_libdir/openmpi/lib/pkgconfig/*.pc
%endif
%_includedir/openmpi-%_arch/superlu_dist/
%endif

%files doc
%license License.txt
%doc DOC/ug.pdf EXAMPLE

%if %{with mpich}
%files mpich
%license License.txt
%_libdir/mpich/lib/*.so.*

%files mpich-devel
%_libdir/mpich/lib/*.so
%_libdir/mpich/lib/*.a
%if %{with cmake}
%_libdir/mpich/lib/pkgconfig/*.pc
%endif
%_includedir/mpich-%_arch/superlu_dist/
%endif


%changelog
* Mon Jan 02 2023 Liu Yang <Yang.Liu.sn@gmail.com> - 1:8.1.0-2.rv64
- Disable failed tests by default on riscv64.

* Sat Jul 23 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1:8.1.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Thu Jul 07 2022 Antonio Trande <sagitter@fedoraproject.org> - 1:8.1.0-1
- Release 8.1.0
- Remove obsolete conditional macros

* Sun May 29 2022 Antonio Trande <sagitter@fedoraproject.org> - 1:8.0.0-1
- Release 8.0.0
- Provide static libraries

* Sat Apr 16 2022 Antonio Trande <sagitter@fedoraproject.org> - 1:7.2.0-3
- Enable complex16 libraries

* Fri Apr 15 2022 Antonio Trande <sagitter@fedoraproject.org> - 1:7.2.0-2
- Make sure installing all header libraries

* Sat Apr 02 2022 Antonio Trande <sagitter@fedoraproject.org> - 1:7.2.0-1
- Release 7.2.0
- Enable CombBLAS support
- Add CMake build method
- Specific index_size

* Sat Jan 22 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1:6.1.1-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Fri Jul 23 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1:6.1.1-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1:6.1.1-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Fri Aug 28 2020 Iñaki Úcar <iucar@fedoraproject.org> - 1:6.1.1-6
- https://fedoraproject.org/wiki/Changes/FlexiBLAS_as_BLAS/LAPACK_manager

* Sat Aug 01 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1:6.1.1-5
- Second attempt - Rebuilt for
  https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1:6.1.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Mon Apr 13 2020 Dave Love <loveshack@fedoraproject.org> - 1:6.1.1-3
- Introduce epoch and revert incompatible change to 6.3.1

* Thu Apr  9 2020 Dave Love <loveshack@fedoraproject.org> - 6.3.1-1
- New version

* Fri Jan 31 2020 Fedora Release Engineering <releng@fedoraproject.org> - 6.1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Sep 12 2019 Dave Love <loveshack@fedoraproject.org> - 6.1.1-1
- New version

* Sat Jul 27 2019 Fedora Release Engineering <releng@fedoraproject.org> - 6.1.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Thu Feb 14 2019 Orion Poplawski <orion@nwra.com> - 6.1.0-2
- Rebuild for openmpi 3.1.3

* Sun Feb 03 2019 Antonio Trande <sagitter@fedoraproject.org> - 6.1.0-1
- Release 6.1.0

* Sun Feb 03 2019 Fedora Release Engineering <releng@fedoraproject.org> - 6.0.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Sun Dec 16 2018 Orion Poplawski <orion@cora.nwra.com> - 6.0.0-3
- libsuperlu_dist is a C++ library, link with mpicxx
- Allow oversubscription with openmpi in tests

* Thu Nov 29 2018 Orion Poplawski <orion@cora.nwra.com> - 6.0.0-2
- Re-enable tests - seem to be working with openmpi 2.1.6rc1

* Wed Nov 21 2018 Dave Love <loveshack@fedoraproject.org> - 6.0.0-1
- New version
- Avoid tests

* Thu Jul 19 2018 Sandro Mani <manisandro@gmail.com> - 5.4.0-3
- Rebuild (scotch)

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 5.4.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jul 10 2018 Dave Love <loveshack@fedoraproject.org> - 5.4.0-1
- New version

* Thu Apr 26 2018 Dave Love <loveshack@fedoraproject.org> - 5.3.0-3
- Require ptscotch-mpich-devel-parmetis

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 5.3.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Jan 30 2018 Dave Love <loveshack@fedoraproject.org> - 5.3.0-1
- New version
- Update sovar
- Drop patch

* Sun Nov  5 2017 Dave Love <loveshack@fedoraproject.org> - 5.2.2-2
- Link againt ptscothmetis et al

* Tue Oct 31 2017 Dave Love <loveshack@fedoraproject.org> - 5.2.2-1
- New version
- Drop output and cmake patches
- Update soname minor version (added function)

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 5.1.3-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 5.1.3-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jun  9 2017 Dave Love <loveshack@fedoraproject.org> - 5.1.3-6
- Maybe use openblas_arches instead

* Thu Jun  8 2017 Dave Love <loveshack@fedoraproject.org> - 5.1.3-5
- Fix up mpich-devel requirement for el7 7.3
- Avoid openblas on s3909(x)

* Sat Jun  3 2017 Dave Love <loveshack@fedoraproject.org> - 5.1.3-4
- Fix mpich conditional
- Build for openmpi on s390 f25+

* Tue Apr 18 2017 Dave Love <loveshack@fedoraproject.org> - 5.1.3-3
- Rebuild for fix to rhbz #1435690

* Wed Apr 12 2017 Dave Love <loveshack@fedoraproject.org> - 5.1.3-2
- Fix EXAMPLES clean up

* Wed Apr 12 2017 Dave Love <loveshack@fedoraproject.org> - 5.1.3-1
- Exclude check on power64 and fix the mpich conditional

* Wed Mar  8 2017 Dave Love <loveshack@fedoraproject.org> - 5.1.3-1
- New version

* Fri Nov 25 2016 Dave Love <loveshack@fedoraproject.org> - 5.1.2-3
- Use optflags, __global_ldflags

* Thu Nov 17 2016 Dave Love <loveshack@fedoraproject.org> - 5.1.2-2
- Patch to avoid large diagnostic output

* Thu Oct 27 2016 Dave Love <loveshack@fedoraproject.org> - 5.1.2-1
- New version
- Drop the OpenMP patch

* Sat Oct 22 2016 Dave Love <loveshack@fedoraproject.org> - 5.1.1-3
- Fix soname

* Wed Oct 19 2016 Dave Love <loveshack@fedoraproject.org> - 5.1.1-2
- Conditionalize openmpi

* Mon Oct 17 2016 Dave Love <loveshack@fedoraproject.org> - 5.1.1-1
- New version
- Drop some patches and use ptscotch to replace parmetis
- Add mpich version
- Make -doc package

* Fri Nov 20 2015 Dave Love <loveshack@fedoraproject.org> - 4.2-1
- Initial version
