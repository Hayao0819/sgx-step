> :warning: SGX-Step integration for EGo is experimental.

### Building the patched EGo

EGo builds on Edgeless RT, which vendors upstream Open Enclave and applies its own `ert.patch` at build time. We reuse the SGX-Step AEP/TCS bindings from `sdk/oe/0001-Minimal-SGX-Step-bindings.patch` and layer them on top of `ert.patch`, following Edgeless RT's [`OEDEV` workflow](edgelessrt/3rdparty/openenclave/HACKING.md).

0. Build and install the patched Edgeless RT and EGo (on Ubuntu 20.04/22.04):

```bash
$ ./install_ego_sdk.sh
```

This initializes the Edgeless RT and EGo submodules, applies `ert.patch` followed by our bindings (`patch_sdk.sh`) to the vendored Open Enclave, builds and installs Edgeless RT to `/opt/edgelessrt`, then builds EGo against it.

1. Validate that the bindings were applied to the patched `liboehost`:

```bash
$ nm /opt/edgelessrt/lib/openenclave/host/liboehost.a | grep -E "sgx_(get|set)_aep|sgx_get_tcs"
0000000000001c90 T sgx_get_aep
0000000000001d00 T sgx_get_tcs
0000000000001cd0 T sgx_set_aep
```

The bindings apply with only line offsets (verified against Edgeless RT v0.5.3, Open Enclave submodule `cbd6450`). Unlike vanilla Open Enclave, Edgeless RT's `liboehost` pulls in C++ (its `EnclaveThreadManager`), so the host links with the C++ driver.

### Single-stepping an EGo enclave

`app/ego` provides a small SGX-Step host that stands in for `ego-host` (Edgeless RT's `erthost`): it loads the signed EGo enclave through `oe_create_emain_enclave`, registers an AEP callback, and single-steps it with the APIC one-shot timer. EGo loads the runtime enclave `ego-enclave` with the signed Go binary as its payload, so pass both as `<ego-enclave>:<payload>`.

```bash
$ cd ../../app/ego
$ make
$ sudo taskset -c 1 ./host/ego_host -t 60 /opt/ego/share/ego-enclave:./enclave/hello > out
```

Go's runtime multiplexes goroutines over the enclave's TCS-bound OS threads, so which goroutine a given TCS observes still needs empirical work; use a debug build (release builds are `-trimpath`ed) for source correlation.
