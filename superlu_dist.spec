# Copyright (c) 2016 Dave Love, Liverpool University
# Copyright (c) 2018 Dave Love, University of Manchester
# MIT licence, per Fedora policy.

# Following scalapack
%bcond_without optimized_blas

%if 0%{?fedora} >= 33 || 0%{?rhel} >= 9
%global blaslib flexiblas
%else
%global blaslib openblas
%endif

%bcond_without check

%if 0%{?el6}%{?el7}
# For good enough C++
%global dts devtoolset-7-
%endif

Name:          superlu_dist
# 6.2.0 fails with
# superlu_defs.h:94:10: fatal error: superlu_FortranCInterface.h: No such file or directory
# 6.3.1 has API/ABI change
Version:       6.1.1
Release:       7%{?dist}
Epoch:	       1
Summary:       Solution of large, sparse, nonsymmetric systems of linear equations
License:       BSD
URL:           http://crd-legacy.lbl.gov/~xiaoye/SuperLU/
Source0:       http://crd-legacy.lbl.gov/~xiaoye/SuperLU/superlu_dist_%version.tar.gz
Source1:       superlu_dist-make.inc
# Use CFLAGS in INSTALL/Makefile (was only failing on some targets)
Patch1:	       superlu_dist-inst.patch
BuildRequires: make
BuildRequires: scotch-devel
BuildRequires: %{?dts}gcc-c++
%if %{with optimized_blas}
BuildRequires: %{blaslib}-devel
# [else] Probably not worth a bundled provides for the bundled partial cblas.
%endif
# The test program runs if we link with -lmetis but crashes if linked with
# -lscotchmetis.
BuildRequires: metis-devel

%ifarch %power64
%if 0%{?el6}
%bcond_with mpich
%else
%bcond_without mpich
%endif
%else
%bcond_without mpich
%endif

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
%global major 1
%global minor 4
%global miner 0
%global sover %major.%minor.%miner


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
Requires:      openmpi%{?_isa}

%description openmpi
%desc

This is the openmpi version.

%package openmpi-devel
Summary: Development files for %name-openmpi
# ptscotch-openmpi-devel-parmetis is missing from RHEL8 for some reason
# https://bugzilla.redhat.com/show_bug.cgi?id=1750180
BuildRequires: openmpi-devel %{!?el8:ptscotch-openmpi-devel-parmetis}
BuildRequires: ptscotch-openmpi-devel
Requires: openmpi-devel%{?_isa}
Requires: %name-openmpi%{?_isa} = %epoch:%version-%release

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
BuildRequires: mpich-devel ptscotch-mpich-devel ptscotch-mpich-devel-parmetis
Requires:      mpich%{?_isa}

%description mpich
%desc

This is the mpich version.

%package mpich-devel
Summary: Development files for %name-mpich
Requires: mpich-devel%{?_isa}
Requires: ptscotch-mpich-devel%{?_isa} ptscotch-mpich-devel-parmetis%{?_isa}
Requires: %name-mpich%{?_isa} = %epoch:%version-%release

%description mpich-devel
Development files for %name-mpich
%endif


%prep
%setup -q -n SuperLU_DIST_%version
cp %SOURCE1 make.inc
%patch1 -p1 -b .orig


%build
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
make SuperLUroot=$(pwd) BLASLIB=-l%{blaslib} INCLUDEDIR=$(pwd)/SRC V=1
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
      %{?with_optimized_blas:-l%{blaslib}} \
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


%install

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

%check
# This is hanging inconsistently in koji, normally on i686 and arm.  I
# can't debug it, so let's hope it doesn't deadlock in realistic
# situations.
%if %{with check}
%{?dts:source /opt/rh/devtoolset-7/enable}
pushd EXAMPLE
%if %{with openmpi}
# just check that it runs
%_openmpi_load
# Allow for more processes than cores
export OMPI_MCA_rmaps_base_oversubscribe=1
mpirun -n 4 ../pddrive -r 2 -c 2 g20.rua
%endif
%endif
make clean

%if %{with openmpi}
%files openmpi
%license License.txt
%_libdir/openmpi/lib/*.so.*

%files openmpi-devel
%_libdir/openmpi/lib/*.so
%_includedir/openmpi-%_arch/superlu_dist
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
%_includedir/mpich-%_arch/superlu_dist
%endif


%changelog
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
