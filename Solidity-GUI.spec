# -*- mode: python ; coding: utf-8 -*-

from gmsh import libpath as gmsh_lib
import logging
import os
from pathlib import Path

block_cipher = None

mac_address_verification_hook = Path.cwd() / "setup_mac_address_verification.py"
runtime_hooks = []
if mac_address_verification_hook.exists():
    logging.warn("setup_mac_address_verification.py found. Adding MAC verification to program.")
    runtime_hooks.append(str(mac_address_verification_hook))

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
    datas=[("solidity_gui/templates/BST.Y3D.jinja", "solidity_gui/templates")],
    hiddenimports=[
        "gmsh",
        "PySide6.plugins",
        # VTK imports need to be added explicitly
        "vtkmodules",
        "vtkmodules.all",
        "vtkmodules.util",
        "vtkmodules.util.numpy_support",
        "vtkmodules.qt.QVTKRenderWindowInteractor",
    ]
    + extra_hiddenimports,
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
