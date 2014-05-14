ceph-collectd-plugin
====================

A [Ceph](http://ceph.com) plugin for [collectd](http://collectd.org) using collectd's [Python plugin](http://collectd.org/documentation/manpages/collectd-python.5.shtml).

This plugin takes the path to the ceph admin socket as an argument, connects to it and receives the output of ```perf dump```. There is already a [ceph plugin](https://github.com/ceph/collectd-4.10.1) , maintained by the ceph developers. But this is a complete fork of collectd and is not compatible with the upstream version. Also version 4.10.1 of collectd is quite outdated.

This plugin ships with an own types.db (```ceph.types.db```) that is needed for the metrics received from the admin socket. Since they can change during the ceph development, I've included a small script that runs the ```perf schema``` command on the admin socket and creates a corresponding types.db for collectd. 

This Script is tested with collectd version 5.1.0 on Debian wheezy and ceph version 0.72.1 (we will upgrade to firefly soon).

Install
-------
 1. Place ```ceph.py``` in ```${COLLECTD_PLUGINDIR}/python/ceph.py```
 2. Place ```ceph.types.db``` in the same directory (or wherever you like to place it)
 3. Configure the plugin and the new types db (see below).
 4. Restart collectd.

Configuration
-------------
Add the following to your collectd config:

```
    <LoadPlugin python>
      Globals true
    </LoadPlugin>

    <Plugin python>
      ModulePath "/usr/lib/collectd/python"
      Import "ceph"

      <Module ceph>
        AdminSocket "/var/run/ceph/ceph-*.asok"
      </Module>
    </Plugin>
```

The plugin will find all admin sockets matching the shell expression and query them. The results will be tagged with the name of the corresponding daemon (ex.: ```osd.12```) in the plugin_instance field.

Contribution
------------

If you experience any errors, please open an issue on github!
