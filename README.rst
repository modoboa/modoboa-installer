modoboa-installer
=================

|workflow| |codecov|

An installer which deploy a complete mail server based on Modoboa.

.. warning::

   This tool is still in beta stage, it has been tested on:

   * Debian Buster (10) / Bullseye (11)
   * Ubuntu Bionic Beaver (18.04) and upper
   * CentOS 7

.. warning::
      
   ``/tmp`` partition must be mounted without the ``noexec`` option.

.. note::

   The server (physical or virtual) running Modoboa needs at least 2GB
   of RAM in order to compile the required dependencies during the
   installation process. Passwords should not contain any special characters
   as they may cause the installation to fail. It's important to set a FQDN
   before, otherwise the installation will break.

Usage::

  $ git clone https://github.com/modoboa/modoboa-installer
  $ cd modoboa-installer
  $ sudo python3 run.py <your domain>


If ``python3`` is not installed on your system, please install it.

A configuration file will be automatically generated the first time
you run the installer, please don't copy the
``installer.cfg.template`` file manually.

The following components are installed by the installer:

* Database server (PostgreSQL or MySQL)
* Nginx and uWSGI
* Postfix
* Dovecot
* Amavis (with SpamAssassin and ClamAV)
* automx (autoconfiguration service)
* OpenDKIM
* Radicale (CalDAV and CardDAV server)

If you want to customize configuration before running the installer,
run the following command::

  $ ./run.py --stop-after-configfile-check <your domain>

An interactive mode is also available::

  $ ./run.py --interactive <your domain>

Make your modifications and run the installer as usual.

By default, the latest Modoboa version is installed but you can select
a previous one using the ``--version`` option::

  $ sudo ./run.py --version=X.X.X <your domain>

.. note::

   Version selection is available only for Modoboa >= 1.8.1.

You can also install beta releases using the ``--beta`` flag::

  $ sudo ./run.py --beta <your domain>

If you want more information about the installation process, add the
``--debug`` option to your command line.

Upgrade mode
------------

An experimental upgrade mode is available.

.. note::

   You must keep the original configuration file, ie the one used for
   the installation. Otherwise, you won't be able to use this mode.

You can activate it as follows::

  $ sudo ./run.py --upgrade <your domain>

It will automatically install latest versions of modoboa and its plugins.

Backup mode 
------------

An experimental backup mode is available.

.. warning::

   You must keep the original configuration file, i.e. the one used for
   the installation. Otherwise, you will need to recreate it manually with the right information!

You can start the process as follows::

  $ sudo ./run.py --backup <your domain>

Then follow the step on the console.

There is also a non-interactive mode:

1. Silent mode

Command::

  $ sudo ./run.py --silent-backup <your domain>

This mode will run silently. When executed, it will create
/modoboa_backup/ and each time you execute it, it will create a new
backup directory with current date and time.

You can supply a custom path if needed::

  $ sudo ./run.py --silent-backup --backup-path /path/of/backup/directory <your domain>

If you want to disable emails backup, disable dovecot in the
configuration file (set enabled to False).

This can be useful for larger instance.

Restore mode
------------

An experimental restore mode is available.

You can start the process as follows::

  $ sudo ./run.py --restore /path/to/backup/directory/ <your domain>

Then wait for the process to finish.

Change the generated hostname
-----------------------------

By default, the installer will setup your email server using the
following hostname: ``mail.<your domain>``. If you want a different
value, generate the configuration file like this::

  $ ./run.py --stop-after-configfile-check <your domain>

Then edit ``installer.cfg`` and look for the following section::

  [general]
  hostname = mail.%(domain)s

Replace ``mail`` by the value you want to use and save your
modifications.

Finally, run the installer without the
``--stop-after-configfile-check`` option.

Let's Encrypt certificate
-------------------------

.. warning::

   Please note this option requires the hostname you're using to be
   valid (ie. it can be resolved with a DNS query) and to match the
   server you're installing Modoboa on.

If you want to generate a valid certificate using `Let's Encrypt
<https://letsencrypt.org/>`_, edit the ``installer.cfg`` file and
modify the following settings::

  [certificate]
  generate = true
  type = letsencrypt

  [letsencrypt]
  email = admin@example.com

Change the ``email`` setting to a valid value since it will be used
for account recovery.

.. |workflow| image:: https://github.com/modoboa/modoboa-installer/workflows/Modoboa%20installer/badge.svg
.. |codecov| image:: http://codecov.io/github/modoboa/modoboa-installer/coverage.svg?branch=master
   :target: http://codecov.io/github/modoboa/modoboa-installer?branch=master
