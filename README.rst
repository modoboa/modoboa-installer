modoboa-installer
=================

An installer which deploy a complete mail server based on Modoboa.

.. warning::

   This tool is still in beta stage, it has been tested on Debian
   Jessie (8) only.

.. warning::
      
   ``/tmp`` partition must be mounted without the ``noexec`` option.

Usage::

  $ git clone https://github.com/modoboa/modoboa-installer
  $ cd modoboa-installer
  $ sudo ./run.py <mail server hostname>

To customize the installation, look at the ``installer.cfg`` file.

By default, the following components are installed:

* Database server (PostgreSQL or MySQL)
* Nginx and uWSGI
* Postfix
* Dovecot
* Amavis (with SpamAssassin and ClamAV)  

If you want more information about the installation process, add the
``--debug`` option to your command line.

At the end of the process, you should consider updating virus databases
with this command::

  $ freshclam
  $ service clamav-daemon restart
