# Build the engineering extension without replacing the historical study binary.
from pathlib import Path

root = Path(SPECPATH)
data = [
    (str(root / "data" / "sources.json"), "data"),
    (str(root / "data" / "manuals" / "arduino-uno-r3.pdf"), "data/manuals"),
    (str(root / "evaluation" / "questions.json"), "evaluation"),
    (str(root / "evaluation" / "run_evaluation.py"), "evaluation"),
    (str(root / "evaluation" / "__init__.py"), "evaluation"),
]
verified = root / "evaluation" / "verified_results.json"
if verified.is_file():
    data.append((str(verified), "evaluation"))
a = Analysis([str(root / "src" / "manual_app.py")], pathex=[str(root / "src"),str(root)],
             binaries=[], datas=data, hiddenimports=["evaluation.run_evaluation"],
             excludes=["tkinter","matplotlib","PySide6.QtWebEngineCore","PySide6.QtWebEngineWidgets",
                       "PySide6.QtQml","PySide6.QtQuick","PySide6.QtMultimedia"], optimize=1)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="Engineering Manual QA",
          debug=False, strip=False, upx=False, console=False,
          icon=str(root / "assets" / "manual-icon.ico"))
