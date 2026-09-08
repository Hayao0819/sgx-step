# Copyright (c) Edgeless Systems GmbH.
# Licensed under the MIT License.

# Build and sign a Go enclave with EGo (ego-go + ego sign); ../host/ego_host loads it.

all: sign

build:
	ego-go build -o hello .

sign: build
	ego sign hello

clean:
	rm -f hello public.pem private.pem enclave.json
