# -*- mode: python ; coding: utf-8 -*-
# Build: pyinstaller desktop/narna-desktop.spec
# Output: dist/NARNA-Desktop/NARNA-Desktop.exe

block_cipher = None

a = Analysis(
    ['run_desktop.py'],
    pathex=['..', '../src'],
    binaries=[],
    datas=[
        ('../src/uap/desktop_static', 'uap/desktop_static'),
        ('../src/uap/_packages', 'uap/_packages'),
        ('../specs/examples/packages', 'specs/examples/packages'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'pydantic',
        'uap',
        'uap.desktop_app',
        'uap.desktop_server',
        'uap.narna_agent',
        'uap.model_router',
        'uap.adqa',
        'uap.agent_tools',
        'yaml',
        'jsonschema',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'torch'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NARNA-Desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NARNA-Desktop',
)
