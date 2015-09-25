import os
import platform
import sys
import urllib
import httplib
import zipfile
import string
import argparse

# -----------------------------------------------------------------------------

def PublishFile(server, archive, name, version):
	args = urllib.urlencode({'archive': archive, 'name': name, 'version': version})
	f = open(archive, 'rb')
	connection = httplib.HTTPConnection(server)
	connection.request('PUT', '/upload?' + args, f.read())
	result = connection.getresponse()
	f.close()

	if result.status != 200:
		print 'FAILED TO UPLOAD!'
		print result.status, result.reason
		print result.read()

# -----------------------------------------------------------------------------

# get the release tag from AutoCI
releaseTag = os.getenv('AUTOCI-RELEASE_TAG')
if releaseTag == None:
	exit()

# get the script path.
publish_path = os.path.dirname(__file__)

# change the working folder to the path of this script.
oldworkingfolder = os.getcwd()
os.chdir(publish_path)

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--platform', dest='platform')
commandlineArgs = parser.parse_args()

if commandlineArgs.platform == None:
	print "no platform specified."
	exit()

# -----------------------------------------------------------------------------
# publish premake binary.
binary_name   = "premake5"
platform_name = commandlineArgs.platform

if platform_name == 'win32':
	binary_name = "premake5.exe"

# zip up the binary.
archive = platform_name + '-x86_64.zip'
z = zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED)
z.write("../bin/release/" + binary_name, "bin/" + binary_name)
z.close()

# publish to Package Server.
print "Publishing '%s' binaries." % (platform_name)
PublishFile('packageserver.corp.blizzard.net', archive, 'Premake', releaseTag)
PublishFile('package.battle.net', archive, 'Battle.net Build Tools', releaseTag)

# done publishing.
os.remove(archive)

# -----------------------------------------------------------------------------
# Publish Premake Bootstrap package (we only do this once, pick a platform)
if platform_name == 'win32':
	filein = open('strap/bootstrap_common.py')
	src = string.Template( filein.read() )
	filein.close()

	z = zipfile.ZipFile('noarch.zip', 'w', zipfile.ZIP_DEFLATED)
	z.writestr('bootstrap_common.py', src.substitute({'PREMAKE_VERSION':releaseTag}))
	z.close()

	# publish to Package Server.
	print "Publishing Strap package."
	PublishFile('package.battle.net', 'noarch.zip', 'Strap', releaseTag)

	# done publishing.
	os.remove('noarch.zip')

# restore the working folder.
os.chdir(oldworkingfolder)

