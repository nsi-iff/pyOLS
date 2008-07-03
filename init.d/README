Copy the appropriate script to /etc/init.d/pyols

If your system is not listed here, the debian script is
a safe default.

Once the script has been copied, add it to the default
runlevel.

Debian/Ubuntu:
    update-rc.d pyols defaults

Gentoo:
    rc-update add pyols default

Fedora/Redhat:
    /sbin/chkconfig --add pyols

Others:
    ln -s /etc/init.d/pyols /etc/rc0.d/S99pyols # Shutdown
    ln -s /etc/init.d/pyols /etc/rc3.d/S99pyols # No X
    ln -s /etc/init.d/pyols /etc/rc5.d/S99pyols # X
    ln -s /etc/init.d/pyols /etc/rc6.d/S99pyols # Reboot
