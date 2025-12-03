# -*- mode: python ; coding: utf-8 -*-

from gmsh import libpath as gmsh_lib
import logging
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

docker_env_hook = Path.cwd() / "solidity_docker_env_hook.py"
runtime_hooks = []
if docker_env_hook.exists():
    logging.warn("solidity_docker_env_hook.py found. Adding Docker image env variables to program.")
    runtime_hooks.append(str(docker_env_hook))
extra_hiddenimports = os.getenv("PLUGIN_IMPORT_PATHS", "")
extra_hiddenimports = extra_hiddenimports.strip().split(",")
extra_hiddenimports = [extra for extra in extra_hiddenimports if extra]

if extra_hiddenimports:
    logging.warn(
        "Adding hiddenimports from environment variable: {}".format(
            "".join(extra_hiddenimports)
        )
    )

a = Analysis(
    ["stub.py"],
    pathex=[],
    binaries=[(gmsh_lib, ".")],
    datas=[("solidity_gui/templates/BST.Y3D.jinja", "solidity_gui/templates"),
            ("solidity_gui/templates/mat.txt.jinja", "solidity_gui/templates")],
    hiddenimports=[
        "gmsh",
        "PySide6.plugins",
    ] + collect_submodules("vtkmodules") + extra_hiddenimports,

    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Solidity-GUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
