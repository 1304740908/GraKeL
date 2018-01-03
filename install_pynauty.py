import platform
import pip
import os
import sys
import tarfile
import shutil
import warnings
import argparse
import traceback

parser = argparse.ArgumentParser(description='A program to install pynauty')
parser.add_argument('--venv', help='define if inside a virtual environment', action="store_true")
args = parser.parse_args()
venv = bool(args.venv)

# Define operating system
is_linux, is_windows = False, False
if platform.system() == 'Linux':
    is_linux = True
elif platform.system() == 'Windows':
    # Warning: For a windows operating system MinGW must be installed.
    is_windows = True
else:
    sys.stderr.write('Unsupported os for this library')
    sys.exit(1)

# Dependencies
os.system('python --version')
os.system('pip --version')

# Download library
# for windows curl must be installed
if is_windows:
    os.system('curl https://web.cs.dal.ca/~peter/software/pynauty/pynauty-0.6.0.tar.gz -o pynauty-0.6.0.tar.gz')
elif is_linux:
    os.system('wget https://web.cs.dal.ca/~peter/software/pynauty/pynauty-0.6.0.tar.gz')
    
# Decompress
os.system('tar -xf pynauty-0.6.0.tar.gz')
os.remove('pynauty-0.6.0.tar.gz')

# Move inside pynauty
os.chdir("pynauty-0.6.0")

# Download C library
if is_windows:
    os.system('curl http://users.cecs.anu.edu.au/~bdm/nauty/nauty26r10.tar.gz -o nauty26r10.tar.gz')
elif is_linux:
    os.system('wget http://users.cecs.anu.edu.au/~bdm/nauty/nauty26r10.tar.gz')

# Decompress library
os.system('echo "decompressing: nauty26r10..."')
os.system('tar -xf nauty26r10.tar.gz')

if (is_windows):
    # rename folder
    os.system('echo "rename nauty"')
    os.system('rename nauty26r10 nauty')
    regular_exp = '\"\\\\?\\'+os.path.abspath('nauty')+'\\This_is_nauty26r10.\"'
    # Delete problematic file ending with '.'
    os.system('echo "delete config"')
    os.system('del '+regular_exp)
    # build pynauty
    os.system('make nauty-objects')
    os.system('python setup.py build --compiler=mingw32')
    if venv:
        os.system('pip install --upgrade .')
        try:
            import pynauty
            os.system('echo Succesful import of pynauty!')
        except ImportError as ierr:
            os.system('echo Import-Error: '+str(ierr)+'..')
            os.system('echo '+ str(traceback.print_exc()))
    else:
        os.system('pip install --user --upgrade .')
if (is_linux):
    # rename folder
    os.system('mv nauty26r10 nauty')
    # build pynauty
    os.system('make pynauty')
    if venv:
        os.system('pip install --upgrade .')
    else:
        os.system('pip install --user --upgrade .')

# exit directory and delete
os.chdir("..")
shutil.rmtree('pynauty-0.6.0')
