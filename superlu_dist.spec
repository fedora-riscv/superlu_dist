# Copyright (c) 2016 Dave Love, Liverpool University
# MIT licence, per Fedora policy.

# Following scalapack
%{!?openblas_arches:%global openblas_arches x86_64 %{ix86} armv7hl %{power64} aarch64}
%ifarch %{openblas_arches}
%bcond_without openblas
%else
%bcond_with openblas
%endif

Name:          superlu_dist
Version:       5.1.3
Release:       6%{?dist}
Summary:       Solution of large, sparse, nonsymmetric systems of linear equations
License:       BSD
URL:           http://crd-legacy.lbl.gov/~xiaoye/SuperLU/
Source0:       http://crd-legacy.lbl.gov/~xiaoye/SuperLU/superlu_dist_%version.tar.gz
Source1:       superlu_dist-make.inc
# Make the parmetis support work with Scotch
Patch1:        superlu_dist-parmetis.patch
# Zap diagnostics, recommended in
# <https://math.berkeley.edu/~linlin/pexsi/page_dependency.html>
Patch2:        superlu_dist-output.patch
Patch3:	       superlu_dist-cblas.patch
BuildRequires: scotch-devel gcc-gfortran
%if %{with openblas}
BuildRequires: openblas-devel
# Probably not worth a bundled provides for the bundled partial cblas.
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

%ifarch s390 s390x
%if 0%{?fedora} >= 25
%bcond_without openmpi
%else
%bcond_with openmpi
%endif
%else
%bcond_without openmpi
%endif

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
%global minor 0
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
BuildRequires: openmpi-devel ptscotch-openmpi-devel-parmetis
BuildRequires: ptscotch-openmpi-devel
Requires: openmpi-devel%{?_isa}
Requires: %name-openmpi%{?_isa} = %version-%release

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
# https://bugzilla.redhat.com/show_bug.cgi?id=1397192 (fixed in RHEL 7.4 beta)
Requires: mpich-devel%{!?el7:%{?_isa}}
Requires: %name-mpich%{?_isa} = %version-%release

%description mpich-devel
Development files for %name-mpich
%endif


%prep
%setup -q -n SuperLU_DIST_%version
%patch1 -p1
%patch2 -p1
%patch3 -p1
cp %SOURCE1 make.inc

%build
# This order to leave openmpi version in place for %%check
for m in %mpich %openmpi; do
case $m in
openmpi) %_openmpi_load ;;
mpich) %_mpich_load ;;
esac
find -name \*.[oa] | xargs rm 2>/dev/null || true # no clean target
pwd
export CFLAGS="%optflags"
%if %{with openblas}
make SuperLUroot=$(pwd)
%else
make blaslib HEADER=. BLASLIB='../libblas.a'
make SuperLUroot=$(pwd) BLASDEF= BLASLIB='../libblas.a'
%endif
mkdir -p tmp $m
pushd tmp
ar x ../SRC/libsuperlu_dist.a
mpicc -shared -Wl,-soname=libsuperlu_dist.so.%major -Wl,--as-needed \
      -o ../$m/libsuperlu_dist.so.%sover *.o -fopenmp -lptscotchparmetis \
      -lptscotch -lptscotcherr -lscotch -lmetis \
%if %{with openblas}
      -lopenblas \
%endif
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

pushd EXAMPLE
# There are SEGVs on koji ppc64le which are probably due to limited stack
%ifnarch %power64
%if %{with openmpi}
# just check that it runs
%_openmpi_load
mpirun -n 4 ../pddrive -r 2 -c 2 g20.rua
%endif
%endif
make clean

%{!?_licensedir:%global license %doc}
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
