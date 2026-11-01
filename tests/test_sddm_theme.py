"""Exercise the QML login flow with fake SDDM models, never real authentication."""

import os
from pathlib import Path
import tempfile
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ.pop("QT_QPA_PLATFORMTHEME", None)
os.environ.pop("QT_IM_MODULE", None)

try:
    from PySide6.QtCore import QAbstractListModel, QModelIndex, QMetaObject, QObject, Property, QSettings, Qt, QUrl, Signal, Slot
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlPropertyMap
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest
except ImportError:
    QGuiApplication = None

ROOT = Path(__file__).resolve().parents[1]
UWSM_SESSION = "/usr/share/wayland-sessions/hyprland-uwsm.desktop"

if QGuiApplication is not None:
    class Model(QAbstractListModel):
        def __init__(self, rows, last_index=0, last_user="alice"):
            super().__init__()
            self.rows = rows
            self.last_index = last_index
            self.last_user = last_user

        lastIndex = Property(int, lambda self: self.last_index, constant=True)
        lastUser = Property(str, lambda self: self.last_user, constant=True)

        def rowCount(self, parent=QModelIndex()):
            return 0 if parent.isValid() else len(self.rows)

        def roleNames(self):
            return {Qt.UserRole + 1: b"name", Qt.UserRole + 2: b"realName", Qt.UserRole + 3: b"file"}

        def data(self, index, role):
            if not index.isValid() or not 0 <= index.row() < len(self.rows):
                return None
            key = self.roleNames().get(role, b"").decode()
            return self.rows[index.row()].get(key, "")

    class LoginManager(QObject):
        loginFailed = Signal()
        loginSucceeded = Signal()
        informationMessage = Signal(str)
        hostName = Property(str, lambda self: "test-host", constant=True)
        canSuspend = Property(bool, lambda self: True, constant=True)
        canReboot = Property(bool, lambda self: True, constant=True)
        canPowerOff = Property(bool, lambda self: True, constant=True)

        def __init__(self):
            super().__init__()
            self.attempts = []

        @Slot(str, str, int)
        def login(self, user, password, session):
            self.attempts.append((user, password, session))

        @Slot()
        def suspend(self):
            pass

        @Slot()
        def reboot(self):
            pass

        @Slot()
        def powerOff(self):
            pass


@unittest.skipIf(QGuiApplication is None, "QML behavior tests require python3-pyside6")
class SddmThemeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        artifacts = ROOT / ".test-artifacts"
        artifacts.mkdir(exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(prefix="sddm-qml-", dir=artifacts)
        # SDDM embeds this module in its binary. Only its static translated
        # labels are mocked; QtQuick/Controls and all theme QML remain real.
        module = Path(cls.temporary.name) / "SddmComponents"
        module.mkdir()
        (module / "qmldir").write_text("module SddmComponents\nTextConstants 2.0 TextConstants.qml\n")
        (module / "TextConstants.qml").write_text(
            'import QtQml\nQtObject { property string password: "Password"; '
            'property string login: "Log In"; property string session: "Session" }\n'
        )

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.engine = QQmlEngine()
        self.engine.addImportPath(self.temporary.name)
        self.manager = LoginManager()
        self.keyboard = QQmlPropertyMap.create()
        self.keyboard.insert("capsLock", False)
        self.config = QQmlPropertyMap.create()
        self.config.insert("clockFormat", "hh:mm")
        self.config.insert("dateFormat", "dddd, MMMM d")
        self.config.insert("sessionFile", UWSM_SESSION)
        self.root = None

    def tearDown(self):
        if self.root is not None:
            self.root.deleteLater()
        self.engine.deleteLater()
        self.app.processEvents()

    def create_theme(self, users=True, sessions=True, uwsm=True, last_session=1):
        self.users = Model([{"name": "bob", "realName": "Bob"},
                            {"name": "alice", "realName": "Alice"}] if users else [])
        session_rows = [{"name": "Hyprland", "file": "/usr/share/wayland-sessions/hyprland.desktop"}]
        if uwsm:
            session_rows.append({"name": "Hyprland (uwsm-managed)", "file": UWSM_SESSION})
        self.sessions = Model(session_rows if sessions else [], last_index=last_session)
        for key, value in {"sddm": self.manager, "keyboard": self.keyboard,
                           "config": self.config, "userModel": self.users,
                           "sessionModel": self.sessions}.items():
            self.engine.rootContext().setContextProperty(key, value)
        self.component = QQmlComponent(self.engine, QUrl.fromLocalFile(
            str(ROOT / "setup/sddm/themes/macos/Main.qml")))
        self.assertTrue(self.component.isReady(), "\n".join(error.toString() for error in self.component.errors()))
        self.root = self.component.create()
        self.assertIsNotNone(self.root, "\n".join(error.toString() for error in self.component.errors()))
        for _ in range(3):
            self.app.processEvents()
        return self.root

    def submit(self):
        self.assertTrue(QMetaObject.invokeMethod(self.root, "submit"))
        self.app.processEvents()

    def test_date_format_is_one_string_not_an_ini_comma_list(self):
        settings = QSettings(str(ROOT / "setup/sddm/themes/macos/theme.conf"), QSettings.IniFormat)
        self.assertEqual(settings.value("dateFormat"), "dddd, MMMM d")

    def test_smaller_typography_keeps_control_dimensions_and_screen_scaling(self):
        root = self.create_theme()
        clock = root.findChild(QObject, "clock")
        password = root.findChild(QObject, "password")
        for width, height in ((1280, 800), (640, 480)):
            with self.subTest(width=width, height=height):
                root.setProperty("width", width)
                root.setProperty("height", height)
                self.app.processEvents()
                scale = root.property("uiScale")
                self.assertEqual(clock.property("font").pixelSize(), round(100 * scale))
                self.assertEqual(password.property("font").pixelSize(), round(14 * scale))
                self.assertAlmostEqual(password.property("width"), 300 * scale)
                self.assertAlmostEqual(password.property("height"), 44 * scale)

    def test_restores_account_and_pins_uwsm_even_if_plain_hyprland_was_remembered(self):
        root = self.create_theme(last_session=0)
        self.assertEqual(root.property("accountName"), "alice")
        self.assertEqual(root.property("displayName"), "Alice")
        session = root.findChild(QObject, "sessionSelector")
        self.assertEqual(session.property("currentValue"), UWSM_SESSION)
        self.assertEqual(session.property("currentIndex"), 1)
        self.assertTrue(root.property("canSubmit"))
        self.assertEqual(self.manager.attempts, [])

    def test_user_and_session_selectors_are_hidden_and_not_focusable(self):
        root = self.create_theme()
        for name in ("userSelector", "sessionSelector"):
            with self.subTest(name=name):
                selector = root.findChild(QObject, name)
                self.assertFalse(selector.property("visible"))
                self.assertFalse(selector.property("enabled"))
                self.assertFalse(selector.property("activeFocusOnTab"))

    def test_keyboard_navigation_skips_hidden_selectors_and_unavailable_power_actions(self):
        root = self.create_theme()
        window = QQuickWindow()
        root.setParentItem(window.contentItem())
        window.resize(1280, 800)
        window.show()
        window.requestActivate()
        self.app.processEvents()
        password = root.findChild(QObject, "password")
        power_names = ("sleepButton", "restartButton", "shutdownButton")
        try:
            for unavailable in ((), power_names, ("sleepButton", "shutdownButton")):
                with self.subTest(unavailable=unavailable):
                    for name in power_names:
                        root.findChild(QObject, name).setProperty("visible", name not in unavailable)
                    password.forceActiveFocus()
                    self.app.processEvents()
                    forward = ["submitButton"] + [name for name in power_names if name not in unavailable] + ["password"]
                    for name in forward:
                        QTest.keyClick(window, Qt.Key_Tab)
                        self.assertEqual(window.activeFocusItem().objectName(), name)
                    for name in reversed(forward[:-1]):
                        QTest.keyClick(window, Qt.Key_Backtab, Qt.ShiftModifier)
                        self.assertEqual(window.activeFocusItem().objectName(), name)
                    QTest.keyClick(window, Qt.Key_Backtab, Qt.ShiftModifier)
                    self.assertEqual(window.activeFocusItem().objectName(), "password")
        finally:
            window.close()
            root.setParentItem(None)

    def test_missing_uwsm_never_falls_back_to_plain_hyprland(self):
        root = self.create_theme(uwsm=False, last_session=0)
        self.submit()
        self.assertFalse(root.property("canSubmit"))
        self.assertFalse(root.findChild(QObject, "password").property("enabled"))
        self.assertEqual(root.findChild(QObject, "sessionSelector").property("currentIndex"), -1)
        self.assertEqual(self.manager.attempts, [])

    def test_duplicate_submit_blocked_until_failure_and_password_cleared(self):
        root = self.create_theme()
        password = root.findChild(QObject, "password")
        password.setProperty("text", "test-only-password")
        self.submit()
        self.submit()
        self.assertEqual(self.manager.attempts, [("alice", "test-only-password", 1)])
        self.manager.informationMessage.emit("Checking credentials")
        self.app.processEvents()
        self.assertTrue(root.property("authenticating"))
        self.submit()
        self.assertEqual(len(self.manager.attempts), 1)
        self.manager.loginFailed.emit()
        self.app.processEvents()
        self.assertFalse(root.property("authenticating"))
        self.assertTrue(root.property("loginError"))
        self.assertEqual(password.property("text"), "")
        self.assertTrue(root.property("canSubmit"))

    def test_success_keeps_handoff_locked_and_clears_password(self):
        root = self.create_theme()
        password = root.findChild(QObject, "password")
        password.setProperty("text", "test-only-password")
        self.submit()
        self.manager.loginSucceeded.emit()
        self.app.processEvents()
        self.assertTrue(root.property("authenticating"))
        self.assertEqual(password.property("text"), "")
        self.submit()
        self.assertEqual(len(self.manager.attempts), 1)

    def test_switching_accounts_clears_the_password(self):
        root = self.create_theme()
        password = root.findChild(QObject, "password")
        password.setProperty("text", "test-only-password")
        root.findChild(QObject, "userSelector").setProperty("currentIndex", 0)
        self.app.processEvents()
        self.assertEqual(root.property("accountName"), "bob")
        self.assertEqual(password.property("text"), "")
        self.assertEqual(self.manager.attempts, [])

    def test_missing_users_cannot_submit(self):
        self.create_theme(users=False)
        self.submit()
        self.assertFalse(self.root.property("canSubmit"))
        self.assertEqual(self.manager.attempts, [])

    def test_missing_sessions_cannot_submit(self):
        self.create_theme(sessions=False)
        self.submit()
        self.assertFalse(self.root.property("canSubmit"))
        self.assertEqual(self.manager.attempts, [])


if __name__ == "__main__":
    unittest.main()
