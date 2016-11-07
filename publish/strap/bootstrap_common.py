#!/usr/bin/python
import os
import os.path
import platform
from stat import *
import subprocess
import sys
import zipfile
import shutil
from urllib2 import urlopen, URLError, HTTPError
from optparse import (OptionParser,BadOptionError,AmbiguousOptionError)

parser = OptionParser()
parser.add_option('--version', dest='version', default='gcc44', action="store", help="override compiler version")
parser.add_option('--premake_args', type='string', default=[], dest='premake_args', action="append", help="arguments for premake")
parser.add_option('--premake_action', default='gmake', dest='premake_action', action="store", help="premake action")

options = None
_optino_parsed = False

build_tools_version = "${PREMAKE_VERSION}"
build_package_version = "BGS_May2014"
build_output_path = "build"
package_server = "http://package.battle.net/"
action_override = False

toolchain = 'gcc'
arch = 'x86_64'
if 'Platform' in os.environ and os.environ['Platform'] == 'x32':
    arch = 'i386'

def parse_options():
    global _optino_parsed
    if _optino_parsed:
        return
    global parser
    global options
    options, unknown = parser.parse_args()
    _optino_parsed = True
    return options

def check_premake():
    currentpremake = ('"'+build_tools_version+'"')
    latestpremake = urlopen("http://packageserver.corp.blizzard.net/premakeversion").read()
    if currentpremake != latestpremake:
        print '\n**WARNING: Latest version of premake is %s, you are running %s.\n' % (latestpremake, currentpremake)

def build_tool_url():
    build_tools_prefix = package_server + "Battle.net%20Build%20Tools/" + build_tools_version
    if platform.system() == 'Windows':
        return build_tools_prefix + "/win32-x86_64.zip"
    elif platform.system() == 'Linux':
        return build_tools_prefix + "/linux-x86_64.zip"
    else:
        return build_tools_prefix + "/darwin-x86_64.zip"

def build_package_url():
    return package_server + "Python%20Package/" + build_package_version + "/package.zip"

def build_scripts_url():
    return package_server + "Battle.net%20Build%20Tools/" + build_tools_version + "/noarch.zip"

def build_tools_directory():
    return os.path.abspath(os.path.join(build_output_path, "build_tools_" + build_tools_version, sys.platform))

def dlfile(url, outfile):
    # Open the url
    #print "Downloading " + url
    f = urlopen(url)
    # Open our local file for writing
    with open(outfile, "wb") as local_file:
        local_file.write(f.read())

def extractzip(zip, outfolder):
    fh = open(zip, 'rb')
    z = zipfile.ZipFile(fh)
    for name in z.namelist():
        z.extract(name, outfolder)
    fh.close()

def chmod(file):
    st = os.stat(file)
    os.chmod(file, st.st_mode | S_IEXEC | S_IXGRP)

def getsetupcompiler():
    version_map = {'gcc44' : '4.4.7-libc2.5', 'gcc47' : '4.7.2-bnet0', 'gcc48' : '4.8.3-bnet0'}
    version = version_map[options.version]
    return [
        "echo \"$$(python %s/%s/build_setup.py --buildTool=make --toolchain=%s --version=%s --targetArch=%s --targetOS=linux --package=True)\"\n" % (build_tools_directory(), build_output_path, toolchain, version, arch),
    ]

def run_bootstrap(premakeArgs):
    check_premake()
    build_tools_dir = build_tools_directory()
    premake = os.path.join(build_tools_dir, "bin", "premake5")

    if not os.path.isdir(build_tools_dir):
        os.makedirs(build_tools_dir)
        dlfile(build_tool_url(), "build_tools.zip")
        extractzip("build_tools.zip", build_tools_dir)
        os.remove("build_tools.zip")

        if platform.system() != 'Windows':
            chmod(premake)
            # This is no longer needed with premake 5, so the targeted scripts are
            # no longer provided ont he package server.  Nothing to see here, move along...
            # dlfile(build_scripts_url(), "build_scripts.zip")
            # extractzip("build_scripts.zip", build_tools_dir)
            # os.remove("build_scripts.zip")

    default_platform = action_override
    if default_platform is False or options.premake_action is not 'gmake':
      default_platform = options.premake_action
    if platform.system() == 'Windows':
        if default_platform == 'gmake':
           default_platform = "vs2010"

    cmdline = '"%s" %s' % (premake, default_platform)
    if premakeArgs:
        for arg in premakeArgs:
            cmdline += ' %s' % arg

    # Windows has special command line needs. It is sufficient to invoke
    # the subprocess with only single quotes around each arg (in a python list)
    if platform.system() == 'Windows':
        c = cmdline.replace('"', '').split(" ")
    else:
        c = cmdline
    #print "Executing", c
    res = subprocess.call(c, shell=True)
    if res != 0:
      sys.exit(res)

    if platform.system() != 'Windows':
        with open("./%s/setup_compiler.sh" % build_output_path, 'w') as fh:
            fh.writelines(getsetupcompiler())
        chmod("./%s/setup_compiler.sh" % build_output_path)
        dlfile(build_package_url(), "%s/package.zip" % build_output_path)

def main(build_path=None, premake_ver=None, action=None, premake_flags=None):
    if premake_ver:
        global build_tools_version
        build_tools_version = premake_ver

    if build_path:
        global  build_output_path
        build_output_path = build_path

    # Handle pre-defined actions
    if action:
        global action_override
        action_override = action

    parse_options()

    premakeArgs = premake_flags if premake_flags is not None else []
    premakeArgs += options.premake_args if options.premake_args is not None else []
    premakeArgs = None if premakeArgs == [] else premakeArgs

    run_bootstrap(premakeArgs)

if __name__ == '__main__':
    main()
