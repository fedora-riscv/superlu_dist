############################################################################
#
#  Program:         SuperLU_DIST
#
#  Module:          make.inc
#
#  Purpose:         Top-level Definitions
#
#  Creation date:   March 1, 2016	version 5.0.0
#
#  Modified:	    
#		    
#
############################################################################
#
#  The name of the libraries to be created/linked to
#
SuperLUroot	=
DSUPERLULIB   	= $(SuperLUroot)/SRC/libsuperlu_dist.a
BLASDEF		= -DUSE_VENDOR_BLAS
BLASLIB		= $(BLASLIB)

LIBS		= $(DSUPERLULIB) -lptscotchparmetis -lmetis64 -lscotch \
-lptscotch -lptscotcherr -lptscotcherrexit $(BLASLIB)

#
#  The archiver and the flag(s) to use when building archive (library)
#  If your system has no ranlib, set RANLIB = echo.
#
ARCH         = /usr/bin/ar
ARCHFLAGS    = cr
RANLIB       = /usr/bin/ranlib

CC           = mpicc
CFLAGS 	     += -O3 -DNDEBUG $(BLASDEF) -DDEBUGlevel=0 -DPRNTlevel=0 -fopenmp -std=c99 -DUSE_VENDOR_BLAS -fPIC
# CFLAGS       += -D
# CFLAGS       +=  
CXX          = mpicxx
CXXFLAGS     += -O3 -DNDEBUG $(BLASDEF) -DDEBUGlevel=0 -DPRNTlevel=0 -fopenmp -std=gnu++11 -DUSE_VENDOR_BLAS -fPIC
HAVE_LAPACK=1
HAVE_PARMETIS=1
HAVE_COMBBLAS=0
NOOPTS       = -O0
FORTRAN	     = mpif90

LOADER       = $(CXX)
LOADOPTS     = $(LDFLAGS) -fopenmp
