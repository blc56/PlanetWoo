Dependency Install
===================

Package Dependencies
--------------------

This is a list of Ubuntu 12.04 packages that are needed for PlanetWoo. YMMV depending on your platform. Depending on how ``mapserver`` is built, you may be able to go without some of these.

::

 python 
 python-dev
 python-pip
 swig
 build-essential
 g++
 make 
 autoconf
 automake
 libgeos-dev
 libfreetype6
 libfeetype6-dev
 libpng12-0
 libpng12-dev
 libgif4
 libgif-dev
 libjp3g8
 libjpeg8-dev
 libgd2-noxpm #xpm version is fine too
 libgd2-noxpm-dev
 libxml2
 libxml2-dev
 libexpat1
 libexpat1-dev
 libproj-dev
 libppq-dev
 git
 dtach

Python Dependencies
-------------------

Python packages that should be installed with a python package manager are listed below.

::

 shapely
 PIL
 psycopg2

Non-Package Compiled Dependencies
----------------------------------

Packages which one will probably have/want to compile themselves are listed below.

::

 gdal >= 1.9.0
 mapserver >= 6.0.3

Install Dependencies with Fabric
---------------------------------

This will install all of the dependencies documented on this page.

::

 fab -f planetwoo/fabric/install.py install_deps:<prefix> -H <user>@<host>

