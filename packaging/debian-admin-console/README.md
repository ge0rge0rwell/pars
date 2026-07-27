Build layout this package expects:

```
<build-root>/
  debian/            <- this directory's debian/ subtree
  admin-console/      <- copy or symlink of repo's admin-console/
  shared/              <- copy or symlink of repo's shared/
```

`debian/rules`' `override_dh_auto_build` stages `pars_admin` and
`pars_shared` plus the systemd unit files from those sibling
directories before `dh_install` runs — there's no `setup.py` in this
repo (a plain module tree, not a pip package), so pybuild doesn't
apply here.

Build with `dpkg-buildpackage -us -uc` from `<build-root>`.

Not verified end-to-end: no `dpkg-buildpackage`/`dpkg-deb` available in
this dev sandbox (macOS, no Debian toolchain) — deferred to E5 along
with the actual `dpkg -i` install-on-clean-VM check, same pattern as
every other VM-only task in TASKS.md.
