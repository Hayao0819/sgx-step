# Copyright (c) Edgeless Systems GmbH.
# Licensed under the MIT License.

.PHONY: all build clean run simulate

all: build

build:
	$(MAKE) -C enclave
	$(MAKE) -C host

clean:
	$(MAKE) -C enclave clean
	$(MAKE) -C host clean

run: build
	host/ego_host ./enclave/hello

simulate: build
	OE_SIMULATION=1 host/ego_host ./enclave/hello
