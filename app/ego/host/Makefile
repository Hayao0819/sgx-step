# Copyright (c) Edgeless Systems GmbH.
# Licensed under the MIT License.

include ../config.mk

LIBSGXSTEP_DIR=../../../
LIBSGXSTEP=$(LIBSGXSTEP_DIR)/libsgxstep

CFLAGS=$(shell pkg-config oehost-$(COMPILER) --cflags) -I$(LIBSGXSTEP_DIR)
LDFLAGS=$(shell pkg-config oehost-$(COMPILER) --libs) -lsgx-step -pthread -L$(LIBSGXSTEP) -lelf
INCDIR=$(shell pkg-config oehost-$(COMPILER) --variable=includedir)

build:
	@ echo "Compilers used: $(CC), $(CXX)"
	oeedger8r ../emain.edl --untrusted \
		--search-path $(INCDIR) \
		--search-path $(INCDIR)/openenclave/edl \
		--search-path $(INCDIR)/openenclave/edl/sgx
	$(CC) -g -c $(CFLAGS) main.c
	$(CC) -g -c $(CFLAGS) emain_u.c
	# Edgeless RT's liboehost pulls in C++ (EnclaveThreadManager), so link with C++.
	$(CXX) -o ego_host emain_u.o main.o $(LDFLAGS)

clean:
	rm -f ego_host main.o emain_u.o emain_u.c emain_u.h emain_args.h
