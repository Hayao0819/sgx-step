#!/usr/bin/python3

import argparse
import os
import re
import statistics
import subprocess
import sys

from elftools.elf.elffile import ELFFile

ENCLAVE_FILE = 'Enclave/encl.so'
INST_SLIDE_SYM = 'asm_microbenchmark'
OUT_FILE = 'out.txt'
APP = './app'
CONFIG_H = '../../libsgxstep/config.h'

RIP_RE = re.compile(r'RIP=0x([0-9A-Fa-f]+); ACCESSED=([0-9])')

MAX_IRQ = None


def slide_start():
    with open(ENCLAVE_FILE, 'rb') as f:
        elf = ELFFile(f)
        sym = elf.get_section_by_name('.symtab').get_symbol_by_name(INST_SLIDE_SYM)
        return sym[0]['st_value']


def count_steps(start, slide_len):
    end = start + slide_len
    tot = one = zero = plus = 0
    prev = 0
    with open(OUT_FILE) as fi:
        for line in fi:
            m = RIP_RE.search(line)
            if not m:
                continue
            cur = int(m.group(1), 16)
            if start <= cur <= end:
                diff = cur - prev
                if prev:
                    if diff == 0:
                        zero += 1
                    elif diff == 1:
                        one += 1
                    else:
                        plus += 1
                prev = cur
                tot += 1
    return {'tot': tot, 'one': one, 'zero': zero, 'plus': plus}


def run_app(interval):
    cmd = ['sudo', APP, '-t', str(interval)]
    if MAX_IRQ is not None:
        cmd += ['-m', str(MAX_IRQ)]
    with open(OUT_FILE, 'w') as out:
        subprocess.run(cmd, stdout=out, stderr=subprocess.STDOUT, check=False)


def measure(interval, start, slide_len, repeats):
    runs = []
    for _ in range(repeats):
        run_app(interval)
        runs.append(count_steps(start, slide_len))
    agg = {
        'plus_max': max(r['plus'] for r in runs),
        'one_med': int(statistics.median(r['one'] for r in runs)),
        'zero_med': int(statistics.median(r['zero'] for r in runs)),
        'tot_med': int(statistics.median(r['tot'] for r in runs)),
    }
    return agg, runs


def fmt(interval, agg):
    tot = agg['tot_med'] or 1
    return ('interval=%3d | single=%3d zero=%3d plus(multi)=%2d | '
            'single_ratio=%.2f' % (interval, agg['one_med'], agg['zero_med'],
                                   agg['plus_max'], agg['one_med'] / tot))


def apply_config(value):
    with open(CONFIG_H) as f:
        src = f.read()
    new = re.sub(r'(#define\s+SGX_STEP_TIMER_INTERVAL\s+)\d+',
                 r'\g<1>%d' % value, src, count=1)
    if new == src:
        print('calibrate.py: could not find SGX_STEP_TIMER_INTERVAL define; not written')
        return
    with open(CONFIG_H, 'w') as f:
        f.write(new)
    print('calibrate.py: wrote SGX_STEP_TIMER_INTERVAL=%d to %s' % (value, CONFIG_H))


def main():
    p = argparse.ArgumentParser(
        description='Auto-tune SGX_STEP_TIMER_INTERVAL by sweeping a NOP slide.')
    p.add_argument('--min', type=int, default=1, help='lower bound of sweep')
    p.add_argument('--max', type=int, default=300, help='upper bound of sweep')
    p.add_argument('--step', type=int, default=1, help='sweep granularity')
    p.add_argument('--slide-len', type=int, default=100,
                   help='NOP slide length; must match the built NUM (default 100)')
    p.add_argument('--repeats', type=int, default=3,
                   help='runs per candidate (all must be multi-step-free)')
    p.add_argument('--max-irq', type=int, default=None,
                   help='app -m: abort a stuck zero-stepping run after N interrupts')
    p.add_argument('--apply', action='store_true',
                   help='write the recommended value into libsgxstep/config.h')
    args = p.parse_args()

    global MAX_IRQ
    MAX_IRQ = args.max_irq

    if not os.path.exists(APP):
        print('calibrate.py: %s not found; run `make all` first' % APP)
        sys.exit(1)

    start = slide_start()
    print('calibrate.py: NOP slide at %s (len=%d), sweep [%d, %d] step %d, repeats=%d'
          % (hex(start), args.slide_len, args.min, args.max, args.step, args.repeats))

    # "no multi-step" is not monotonic (holds below and above the good band),
    # so sweep and pick the interval with the most single-steps.
    results = []
    for interval in range(args.min, args.max + 1, args.step):
        agg, _ = measure(interval, start, args.slide_len, args.repeats)
        print('  ' + fmt(interval, agg))
        results.append((interval, agg))

    safe = [(iv, agg) for iv, agg in results
            if agg['plus_max'] == 0 and agg['one_med'] > 0]
    if not safe:
        print()
        print('calibrate.py: no single-stepping interval in [%d, %d]; widen the '
              'range or the landing window.' % (args.min, args.max))
        sys.exit(2)

    # most single-steps; lower interval wins ties
    best_iv, best_agg = max(safe, key=lambda r: (r[1]['one_med'], -r[0]))

    print()
    print('calibrate.py: best single-stepping interval = %d (%s)'
          % (best_iv, fmt(best_iv, best_agg).split('| ', 1)[1]))
    tot = best_agg['tot_med'] or 1
    if best_agg['one_med'] / tot < 0.9:
        print('calibrate.py: note: single-step ratio %.2f; zero-steps are '
              'filtered via the code PTE accessed bit.' % (best_agg['one_med'] / tot))

    print()
    print('RECOMMENDED SGX_STEP_TIMER_INTERVAL=%d' % best_iv)
    if args.apply:
        apply_config(best_iv)
    else:
        print('(re-run with --apply to write this into libsgxstep/config.h)')


if __name__ == '__main__':
    main()
