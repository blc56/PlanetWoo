##\file install.py Fabric script for installing planetwoo
from fabric.api import serial, parallel, task, local, settings, abort, run, cd, env, get, put, execute
from fabric.operations import sudo
import os.path
import boto
import sys
from time import sleep
import StringIO

def out(s):
	sys.stdout.write(s)
	sys.stdout.flush()

#
# Method: create_server
# Launches a server in the EC2 returns an Boto EC2 Instances if successful. Defaults to an Ubuntu 12.04 Instance
#
@task
def create_server(ec2_conn, ssh_key, ami='ami-82fa58eb', size='m1.small', security_group='Basic HTTP(S) Setup', region='us-east-1d' ,sudo_user='ubuntu'):
	request = ec2_conn.run_instances(ami, key_name=ssh_key, instance_type=size, security_groups=[security_group,],placement=region)

	instance = request.instances[0]
	instance.update()
	current_state = instance.state
	out('Waiting on server to start...')
	while(current_state != 'running'):
		# wait on amazon
		sleep(2)
		# update the status
		instance.update()
		current_state = instance.state
		if(current_state == 'pending'):
			out('.')
		elif(current_state == 'running'):
			# the done message will popup next
			# so, we'll do nothing.
			pass
		else:
			# something odd happened...
			out(current_state+'..')
	out("Got Server: %s\n" % instance.public_dns_name)

	return instance
#
# Method: wait_for_server
# Waits for the server to pass all of the status checks.  This generally
# ensures that the server is booted and ready to accept further commands.
#
@task
def wait_for_server(ec2_conn, instance):
	out('Waiting for SSH...')
	waiting_secs = 0
	status = ''
	while(status != 'Status:ok'):
		# we can sleep a little longer as we are waiting for the kernel to boot.
		sleep(10)
		# check the status
		status = str(ec2_conn.get_all_instance_status(instance_ids=[instance.id])[0].instance_status)
		# make the user feel more comfortable
		out('.')
		# increment our total wait time
		waiting_secs+=10
		# this shit really should come up in < 2 minutes.  Bail if it didn't.
		if(waiting_secs > 120 and status != 'Status:ok'):
			print 'Ack, there is something wrong, giving up...'
			return -1
#
# Method: launch_server
# Creates a Server from an image.
#
@task
def launch_server(ssh_key, ami='ami-82fa58eb', size='m1.small', security_group='Basic HTTP(S) Setup', region='us-east-1d',sudo_user='ubuntu'):
	ec2_conn = boto.connect_ec2()	
	instance = create_server(ec2_conn, ssh_key, ami, size=size, security_group=security_group, region=region)

	env.hosts = [instance.public_dns_name]
	env.instance = instance
	env.user = sudo_user
	wait_for_server(ec2_conn, instance)
	execute(install_deps, hosts=env.hosts)
	execute(install_user_env, hosts=env.hosts)
	execute(install_planetwoo, hosts=env.hosts)

	print "\n* Created Server: %s" % instance.public_dns_name

@task
def install_user_env(prefix="/opt/planetwoo/"):
	env_sh = \
"""
echo '
PYTHONPATH="%(prefix)s/lib/python2.7/site-packages/:%(prefix)s/PlanetWoo/:${PYTHONPATH}"
LD_LIBRARY_PATH="%(prefix)s/lib/:${LD_LIBRARY_PATH}"
' > %(prefix)s/user_env.sh
export PYTHONPATH
export LD_LIBRARY_PATH
""" % {'prefix': prefix}

	#put(env_sh, os.path.join(prefix, 'user_env.sh'))
	sudo(env_sh)

@task
#for ubuntu 12.04 machines
def install_deps(prefix="/opt/planetwoo/"):
	#stuff from packages
	sudo('apt-get update')
	sudo('apt-get -y upgrade')
	sudo('apt-get -y install python python-dev python-pip')
	sudo('apt-get -y install swig')
	sudo('apt-get -y install build-essential g++ make autoconf automake')
	sudo('apt-get -y install libgeos-dev')
	sudo('apt-get -y install libfreetype6 libfreetype6-dev')
	sudo('apt-get -y install libpng12-0 libpng12-dev')
	sudo('apt-get -y install libgif4 libgif-dev')
	sudo('apt-get -y install libjpeg8 libjpeg8-dev')
	sudo('apt-get -y install libgd2-noxpm libgd2-noxpm-dev')
	sudo('apt-get -y install libcurl4-openssl-dev')
	sudo('apt-get -y install libxml2 libxml2-dev')
	sudo('apt-get -y install libexpat1 libexpat1-dev')
	sudo('apt-get -y install libproj-dev')
	sudo('apt-get -y install s3cmd')
	sudo('apt-get -y install libpq-dev')
	sudo('apt-get -y install git')
	sudo('pip install shapely')
	sudo('pip install PIL')
	sudo('pip install psycopg2')

	sudo('mkdir -p %s' % os.path.join(prefix,'src'))

	#TODO:FIXME: lots of unnecessary sudo action in here...

	with cd(os.path.join(prefix,'src')):
		#gdal
		sudo('wget http://download.osgeo.org/gdal/gdal-1.9.0.tar.gz')
		sudo('tar -xf gdal-1.9.0.tar.gz')
		with cd('gdal-1.9.0'):
			sudo('./configure --prefix=%s --with-pg --with-python --with-pic --with-xml --with-expat' % prefix)
			sudo('make')
			#NOTE: the prefix seems to be ignored when installing the python modules
			#annoying...
			sudo('make install')

		#mapserver
		sudo('wget http://download.osgeo.org/mapserver/mapserver-6.0.3.tar.gz')
		sudo('tar -xf mapserver-6.0.3.tar.gz')
		with cd('mapserver-6.0.3'):
			#hack to fix mapserver compilation?
			sudo('rm -f /usr/lib/libgd.so')
			sudo('ln -s /usr/lib/x86_64-linux-gnu/libgd.so /usr/lib/')
			sudo('./configure --with-xml --with-wfs --with-wmsclient --with-wfsclient --with-postgis --with-freetype --with-proj --with-gdal=%(prefix)s/bin/gdal-config --with-ogr=%(prefix)s/bin/gdal-config --prefix=%(prefix)s' % {'prefix': prefix})
			sudo('make')
			sudo('make install')

			sudo('mkdir -p %s/lib/python2.7/site-packages/' % prefix)
			with cd('mapscript/python'):
				sudo('export PYTHONPATH=%(prefix)s/lib/python2.7/site-packages/ ; python setup.py install --prefix %(prefix)s' % {'prefix': prefix})

@task
def install_planetwoo(prefix="/opt/planetwoo"):
	sudo('mkdir -p %s' % prefix)
	with cd('%s' % prefix):
		sudo('git clone https://github.com/blc56/PlanetWoo.git')

