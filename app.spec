# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['workflow_test_desktop/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('workflow_test_desktop/config/themes.py', 'workflow_test_desktop/config/'),
    ],
    hiddenimports=[
        'PySide6', 'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui',
        'qasync',
        'httpx', 'aiosqlite',
        'workflow_test_desktop.config.themes',
        'workflow_test_desktop.core.config.environment',
        'workflow_test_desktop.core.config.secrets',
        'workflow_test_desktop.core.storage.database',
        'workflow_test_desktop.core.storage.recorder',
        'workflow_test_desktop.core.session.manager',
        'workflow_test_desktop.core.session.lease',
        'workflow_test_desktop.core.flow.catalog',
        'workflow_test_desktop.core.flow.inspector',
        'workflow_test_desktop.core.assignment.engine',
        'workflow_test_desktop.core.assignment.models',
        'workflow_test_desktop.core.execution.run_plan',
        'workflow_test_desktop.core.execution.scheduler',
        'workflow_test_desktop.core.execution.executor',
        'workflow_test_desktop.core.execution.controller',
        'workflow_test_desktop.core.export.exporter',
        'workflow_test_desktop.core.export.templates',
        'workflow_test_desktop.ui.main_window',
        'workflow_test_desktop.ui.wizard_navigator',
        'workflow_test_desktop.ui.steps.step_account',
        'workflow_test_desktop.ui.steps.step_flow',
        'workflow_test_desktop.ui.steps.step_form',
        'workflow_test_desktop.ui.steps.step_nodes',
        'workflow_test_desktop.ui.steps.step_run',
        'workflow_test_desktop.ui.steps.step_report',
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='workflow_test_desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
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
    upx=False,
    upx_exclude=[],
    name='workflow_test_desktop',
)
