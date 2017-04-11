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

LIBS		= $(DSUPERLULIB) -lptscotchparmetis -lptscotch -lptscotcherr -lmetis -lscotch -lopenblas

#
#  The archiver and the flag(s) to use when building archive (library)
#  If your system has no ranlib, set RANLIB = echo.
#
ARCH         = /usr/bin/ar
ARCHFLAGS    = cr
RANLIB       = /usr/bin/ranlib

CC           = mpicc
CFLAGS 	     += -O3 -DNDEBUG  -DUSE_VENDOR_BLAS -DDEBUGlevel=0 -DPRNTlevel=0 -fopenmp -std=c99 -fPIC -g
# CFLAGS       += -D
# CFLAGS       +=  
NOOPTS       = -O0
FORTRAN	     = mpif90

LOADER       = $(CC) -fopenmp
LOADOPTS     = 
