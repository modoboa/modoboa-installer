modoboa-installer
=================

An installer which deploy a complete mail server based on Modoboa.

.. warning::

   This tool is still in beta stage, it has been tested on:

   * Debian Jessie (8)
   * Ubuntu Trusty (14.04) and upper
   * CentOS 7

.. warning::
      
   ``/tmp`` partition must be mounted without the ``noexec`` option.

.. note::

   The server (physical or virtual) running Modoboa needs at least 1GB
   of RAM in order to compile the required dependencies during the
   installation process.

Usage::

  $ git clone https://github.com/modoboa/modoboa-installer
  $ cd modoboa-installer
  $ sudo ./run.py <your domain>

A configuration file will be automatically generated the first time
you run the installer, please don't copy the
``installer.cfg.template`` file manually.

By default, the following components are installed:

* Database server (PostgreSQL or MySQL)
* Nginx and uWSGI
* Postfix
* Dovecot
* Amavis (with SpamAssassin and ClamAV)

If you want to customize configuration before running the installer,
run the following command::

  $ ./run.py --stop-after-configfile-check <your domain>

Make your modifications and run the installer as usual.

If you want more information about the installation process, add the
``--debug`` option to your command line.

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
