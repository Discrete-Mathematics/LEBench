# Custom-kernel ablation campaign — status

Status: **attempted, not completed** (documented here so the repository stays truthful).

## What was attempted

After the runtime-toggle experiments, the seven remaining root causes require
kernel rebuilds. A build-and-test pipeline was set up on the recovered guest:

- source: mainline `linux-4.4.210` (mirrors.tuna.tsinghua.edu.cn), Ubuntu
  4.4.0-210 config as the base;
- variants: `stock`, `no-ufd` (CONFIG_USERFAULTFD=n), `no-usercopy`
  (CONFIG_HARDENED_USERCOPY=n), `no-slab` (CONFIG_SLAB_FREELIST_RANDOM=n),
  `no-memcg` (CONFIG_MEMCG=n), `fct-on` (CONFIG_CONTEXT_TRACKING_FORCE=y, to
  reproduce the paper's misconfiguration) and `retpoline` (the paper's Figure 6
  patch: direct calls for `sock_poll`/`pipe_poll`/`timerfd_poll` in
  `fs/select.c`'s `do_select`);
- per variant: three runs of the reduced suite under `results/custom-kernels/`
  plus the environment and the effective `.config`.

## What succeeded

- `stock` and `retpoline` kernels compiled and built (the retpoline patch was
  validated with `git apply --check` and applied cleanly);
- the patch itself is preserved at `D:\work\retpoline.patch` (host) and was
  uploaded to the guest; it is reproducible by anyone with a Linux build box.

## Why it stopped

The host drive filled while the guest was writing, which made the ext4 root go
read-only mid-build and corrupted some directories (`Structure needs
cleaning`). A fsck-from-initramfs recovery was prepared, but the guest then
failed to boot reliably under QEMU/WHPX. The remaining five variants need a
clean Linux environment (a real Ubuntu 16.04/18.04 VM or a server) to finish;
the build script is ready and only needs to be pointed at that environment.

## What this does not change

All committed results stand on their own: 34-kernel sweep, four runtime-toggle
root causes (KPTI, Retpoline, THP, fault-around), the cross-host macrobenchmark,
and the two extensions. The custom-kernel ablation remains listed as a
limitation in the report.
