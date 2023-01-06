# -*- mode: python ; coding: utf-8 -*-

from gmsh import libpath as gmsh_lib

block_cipher = None

a = Analysis(
    ["stub.py"],
    pathex=[],
    binaries=[(gmsh_lib, ".")],
    datas=[],
    hiddenimports=[
        "gmsh",
        "PySide6.plugins",
        # VTK imports need to be added explicitly
        "vtkmodules",
        "vtkmodules.all",
        "vtkmodules.util",
        "vtkmodules.util.numpy_support",
        "vtkmodules.qt.QVTKRenderWindowInteractor",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
splash = Splash(
    ".\\splash.png",
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    splash,
    splash.binaries,
    [],
    name="Solidity-GUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
