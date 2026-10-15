# Build-Skript für eine eigenständige Executable (python setup.py)
import PyInstaller.__main__
import os
import sys

# PyInstaller konfigurieren
args = [
    'main.py',
    '--name=WorkforceScheduling',
    '--onefile',
    '--windowed',
    f'--add-data=database/db_schema.sql{os.pathsep}database',
    '--hidden-import=jpype',
    '--hidden-import=jpype._core',
    '--hidden-import=jpype._jvmfinder',
    '--hidden-import=optapy',
    '--hidden-import=optapy.config',
    '--hidden-import=optapy.config.solver',
    '--hidden-import=optapy.config.solver.termination',
    '--hidden-import=optapy.constraint',
    '--hidden-import=optapy.score',
    '--hidden-import=optapy.types',
    '--collect-all=optapy',
    '--collect-all=jpype',
    '--collect-submodules=jpype',
    '--collect-submodules=optapy',
    '--copy-metadata=optapy',
    '--copy-metadata=JPype1',
    '--clean',
]

if sys.platform == 'win32':
    args.append('--add-binary=%s;.' % os.path.join(sys.prefix, 'Lib', 'site-packages', 'jpype', '_jvm', '*.dll'))

PyInstaller.__main__.run(args)