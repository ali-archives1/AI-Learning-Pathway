"""Visual system for the engineering-manual workspace."""

STYLES = """
* { font-family: 'Segoe UI'; font-size: 13px; color: #E9EEF7; }
QWidget { background: transparent; }
QMainWindow, QWidget#Root { background: #0C1019; }
QFrame#Rail { background: #101621; border-right: 1px solid #253043; }
QFrame#Topbar { background: #0F1520; border-bottom: 1px solid #253043; }
QFrame#EvidencePane { background: #101621; border-left: 1px solid #253043; }
QFrame#Surface { background: #161F2D; border: 1px solid #29374B; border-radius: 12px; }
QFrame#AnswerCard { background: #141F2B; border: 1px solid #31534F; border-radius: 14px; }
QFrame#QuoteCard { background: #101A25; border: 1px solid #27433F; border-radius: 10px; }
QFrame#EvidenceCard { background: #151E2B; border: 1px solid #29364A; border-radius: 11px; }
QFrame#ErrorCard { background: #34232A; border: 1px solid #87505C; border-radius: 10px; }
QLabel#Brand { font-size: 18px; font-weight: 750; letter-spacing: 2px; }
QLabel#Overline { color: #8292AA; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; }
QLabel#Heading { font-size: 28px; font-weight: 700; letter-spacing: -0.7px; }
QLabel#Hero { font-size: 31px; font-weight: 700; letter-spacing: -0.8px; }
QLabel#Subheading { font-size: 17px; font-weight: 650; }
QLabel#Body { font-size: 15px; }
QLabel#Muted { color: #9AA9BD; }
QLabel#Small { color: #91A0B7; font-size: 11px; }
QLabel#Teal { color: #7DE2CF; font-weight: 650; }
QLabel#Badge { color: #8BE6D5; background: #153B36; border: 1px solid #28594E; border-radius: 9px; padding: 5px 10px; font-size: 11px; }
QLabel#Step { color: #B4BEE5; font-size: 11px; background: #1D2539; border-radius: 8px; padding: 7px 10px; }
QLabel#Warning { color: #EFC68B; }
QPushButton { background: #192334; border: 1px solid #2D3A50; border-radius: 8px; padding: 9px 13px; font-weight: 600; min-height: 18px; }
QPushButton:hover { background: #233148; border-color: #576C8A; }
QPushButton:pressed { background: #101825; }
QPushButton:focus { border: 1px solid #A9F0E1; }
QPushButton:disabled { color: #778397; background: #171D29; border-color: #283143; }
QPushButton#Primary { background: #7DE2CF; color: #0B2724; border: 1px solid #7DE2CF; }
QPushButton#Primary:hover { background: #A0EDDF; }
QPushButton#Primary:disabled { background: #29453F; color: #849E97; border-color: #29453F; }
QPushButton#Nav { text-align: left; background: transparent; border: none; padding: 13px 14px; color: #9BAAC0; }
QPushButton#Nav:checked { color: #9CE9DC; background: #1B3533; }
QPushButton#Nav:hover { background: #1B2836; }
QPushButton#Ghost { background: transparent; border-color: #304056; color: #B2C3D7; }
QPushButton#Citation { background: #193D37; border-color: #326458; color: #A0ECDD; padding: 5px 10px; font-size: 11px; }
QPushButton#Example { text-align: left; background: #151E2B; color: #BBC9DC; font-weight: 400; padding: 12px; }
QPlainTextEdit { background: #101824; border: 1px solid #34435B; border-radius: 10px; padding: 12px; font-size: 15px; selection-background-color: #315964; }
QPlainTextEdit:focus { border-color: #7DE2CF; }
QComboBox { background: #182233; border: 1px solid #344159; border-radius: 7px; padding: 8px; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView { background: #182233; color: #EDF2F7; selection-background-color: #29483F; }
QSpinBox { background: #182233; border: 1px solid #344159; border-radius: 6px; padding: 5px; min-width: 48px; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: #3A485D; border-radius: 3px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSplitter::handle { background: #29374A; width: 2px; }
QProgressBar { background: #1D2839; border: none; border-radius: 3px; min-height: 5px; max-height: 5px; }
QProgressBar::chunk { background: #7DE2CF; border-radius: 3px; }
QTableWidget { background: #121B28; border: 1px solid #2C3A4F; border-radius: 8px; gridline-color: #263349; selection-background-color: #254840; }
QTableWidget::item { padding: 9px; }
QHeaderView::section { background: #1B2739; color: #AFBED3; border: none; padding: 11px 7px; font-size: 11px; font-weight: 650; }
QToolTip { color: #EDF2F8; background: #202C3F; border: 1px solid #51627A; padding: 7px; }
"""
