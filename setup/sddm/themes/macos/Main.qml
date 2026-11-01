// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Controls.Basic as Controls
import SddmComponents 2.0 as SDDM

Rectangle {
    id: root
    width: 1280
    height: 800
    color: "#0b153e"

    // Qt already handles display DPI. This only keeps the composition on small
    // screens, without transforms that would mis-scale popup menus.
    readonly property real uiScale: Math.min(1.25, width / 1100, height / 850)
    readonly property string uiFont: Qt.fontFamilies().indexOf("Inter") >= 0 ? "Inter" : "Sans Serif"
    property date now: new Date()
    property bool authenticating: false
    property bool loginError: false
    property string statusMessage: ""
    property bool initialized: false
    readonly property string accountName: userSelector.currentIndex >= 0 ? userSelector.currentText : ""
    readonly property string displayName: userSelector.currentValue || accountName
    readonly property bool canSubmit: initialized && !authenticating && accountName.length > 0
                                      && userSelector.currentIndex >= 0 && userSelector.count > 0
                                      && sessionSelector.currentIndex >= 0 && sessionSelector.count > 0

    SDDM.TextConstants { id: strings }

    function validIndex(index, count) {
        return index >= 0 && index < count;
    }

    function restoreSelections() {
        // Honor SDDM's persisted state, including hyprland-uwsm.desktop seeded
        // by the host setup. Never guess a session by its translated label.
        var rememberedUser = userSelector.find(userModel.lastUser, Qt.MatchExactly);
        userSelector.currentIndex = validIndex(rememberedUser, userSelector.count) ? rememberedUser
                                  : validIndex(userModel.lastIndex, userSelector.count) ? userModel.lastIndex
                                  : userSelector.count > 0 ? 0 : -1;
        sessionSelector.currentIndex = validIndex(sessionModel.lastIndex, sessionSelector.count)
                                     ? sessionModel.lastIndex : sessionSelector.count > 0 ? 0 : -1;
        initialized = true;
        if (userSelector.count === 0)
            userSelector.forceActiveFocus();
        else if (sessionSelector.count === 0)
            sessionSelector.forceActiveFocus();
        else
            password.forceActiveFocus();
    }

    function resetPrompt() {
        password.clear();
        statusMessage = "";
        loginError = false;
    }

    function submit() {
        // Both Enter and the arrow use this guard. Keep the lock until SDDM
        // reports failure/success; informational PAM messages are not completion.
        if (!canSubmit)
            return;
        authenticating = true;
        loginError = false;
        statusMessage = qsTr("Signing in…");
        sddm.login(accountName, password.text, sessionSelector.currentIndex);
    }

    Connections {
        target: sddm

        function onLoginFailed() {
            root.authenticating = false;
            password.clear();
            root.loginError = true;
            root.statusMessage = qsTr("Sign-in failed. Please try again.");
            Qt.callLater(function() { password.forceActiveFocus(); });
        }

        function onLoginSucceeded() {
            // Do not permit a second attempt while the greeter hands off.
            root.authenticating = true;
            password.clear();
            root.loginError = false;
            root.statusMessage = qsTr("Signing in…");
        }

        function onInformationMessage(message) {
            root.statusMessage = message;
        }
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: root.now = new Date()
    }

    Image {
        anchors.fill: parent
        source: "assets/blue-hour.svg"
        fillMode: Image.PreserveAspectCrop
        // Rasterize at the actual output size rather than the SVG's intrinsic
        // resolution; no GPU shaders, blur modules, or external wallpaper.
        sourceSize.width: root.width
        sourceSize.height: root.height
    }

    // A gentle veil makes the clock and controls readable on all crop ratios.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0; color: "#20040820" }
            GradientStop { position: 0.6; color: "#00040820" }
            GradientStop { position: 1; color: "#68040820" }
        }
    }

    Row {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 25 * root.uiScale
        anchors.rightMargin: 30 * root.uiScale
        spacing: 7 * root.uiScale
        opacity: 0.72

        Image {
            source: "assets/lock.svg"
            width: 13 * root.uiScale
            height: width
            sourceSize.width: width
            sourceSize.height: height
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: sddm.hostName
            textFormat: Text.PlainText
            color: "#ffffff"
            font.family: root.uiFont
            font.pixelSize: 11 * root.uiScale
            elide: Text.ElideRight
            width: Math.min(implicitWidth, 220 * root.uiScale)
        }
    }

    Column {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 64 * root.uiScale
        spacing: 0

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatDateTime(root.now, config.dateFormat || "dddd, MMMM d")
            textFormat: Text.PlainText
            color: "#eef2ff"
            font.family: root.uiFont
            font.pixelSize: 21 * root.uiScale
            font.weight: Font.Medium
        }
        Text {
            objectName: "clock"
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatTime(root.now, config.clockFormat || "hh:mm")
            textFormat: Text.PlainText
            color: "#f2f4ff"
            font.family: root.uiFont
            font.pixelSize: 100 * root.uiScale
            font.weight: Font.DemiBold
            font.letterSpacing: -4 * root.uiScale
        }
    }

    Column {
        id: loginForm
        width: 360 * root.uiScale
        anchors.horizontalCenter: parent.horizontalCenter
        y: root.height * 0.425
        spacing: 16 * root.uiScale

        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 104 * root.uiScale
            height: width
            source: "assets/avatar.svg"
            sourceSize.width: width
            sourceSize.height: height
            Accessible.ignored: true
        }

        Text {
            width: parent.width
            text: root.displayName || qsTr("No users available")
            textFormat: Text.PlainText
            color: "#ffffff"
            font.family: root.uiFont
            font.pixelSize: 21 * root.uiScale
            font.weight: Font.DemiBold
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }

        Item {
            width: 300 * root.uiScale
            height: 44 * root.uiScale
            anchors.horizontalCenter: parent.horizontalCenter

            Controls.TextField {
                id: password
                objectName: "password"
                anchors.fill: parent
                enabled: !root.authenticating && userSelector.count > 0 && sessionSelector.count > 0
                opacity: enabled || root.authenticating ? 1 : 0.45
                leftPadding: 16 * root.uiScale
                rightPadding: 50 * root.uiScale
                topPadding: 0
                bottomPadding: 0
                placeholderText: strings.password
                placeholderTextColor: "#d5dcf2"
                color: "#ffffff"
                selectionColor: "#7999cf"
                selectedTextColor: "#ffffff"
                font.family: root.uiFont
                font.pixelSize: 14 * root.uiScale
                echoMode: TextInput.Password
                passwordCharacter: "•"
                selectByMouse: true
                activeFocusOnTab: true
                inputMethodHints: Qt.ImhHiddenText | Qt.ImhSensitiveData | Qt.ImhNoPredictiveText
                Accessible.name: strings.password
                onAccepted: root.submit()
                onTextEdited: {
                    root.loginError = false;
                    root.statusMessage = "";
                }
                Keys.onEscapePressed: {
                    if (!root.authenticating)
                        root.resetPrompt();
                }
                KeyNavigation.tab: submitButton
                KeyNavigation.backtab: sessionSelector

                background: Rectangle {
                    radius: 22 * root.uiScale
                    color: "#37ffffff"
                    border.width: (password.activeFocus ? 2 : 1) * root.uiScale
                    border.color: root.loginError ? "#f0c1cb" : password.activeFocus ? "#abd1ff" : "#45ffffff"
                    Behavior on border.color { ColorAnimation { duration: 140 } }
                }
            }

            Controls.Button {
                id: submitButton
                objectName: "submitButton"
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.rightMargin: 6 * root.uiScale
                width: 32 * root.uiScale
                height: width
                enabled: root.canSubmit
                hoverEnabled: true
                activeFocusOnTab: true
                text: strings.login
                Accessible.name: strings.login
                onClicked: root.submit()
                KeyNavigation.tab: userSelector
                KeyNavigation.backtab: password
                padding: 0
                background: Rectangle {
                    radius: width / 2
                    color: submitButton.down ? "#85ffffff" : submitButton.hovered ? "#60ffffff" : "#36ffffff"
                    border.width: submitButton.visualFocus ? 2 * root.uiScale : 0
                    border.color: "#d1e5ff"
                }
                contentItem: Image {
                    source: "assets/arrow-right.svg"
                    sourceSize.width: 24 * root.uiScale
                    sourceSize.height: 24 * root.uiScale
                    fillMode: Image.PreserveAspectFit
                    opacity: root.authenticating ? 0 : submitButton.enabled ? 1 : 0.35
                }

                Controls.BusyIndicator {
                    anchors.centerIn: parent
                    width: 24 * root.uiScale
                    height: width
                    padding: 2 * root.uiScale
                    running: root.authenticating
                    visible: running
                    palette.dark: "#ffffff"
                }
            }
        }

        Column {
            width: parent.width
            height: 54 * root.uiScale
            spacing: 6 * root.uiScale

            Text {
                width: parent.width
                text: root.statusMessage || (userSelector.count === 0 ? qsTr("No users are available. Check SDDM configuration.")
                       : sessionSelector.count === 0 ? qsTr("No desktop sessions are installed.")
                       : qsTr("Enter your password to sign in"))
                textFormat: Text.PlainText
                color: root.loginError ? "#ffdae1" : "#dce4ff"
                opacity: root.statusMessage || !root.canSubmit ? 1 : 0.75
                font.family: root.uiFont
                font.pixelSize: 11 * root.uiScale
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                maximumLineCount: 3
                elide: Text.ElideRight
                Accessible.name: text
            }
            Text {
                width: parent.width
                text: qsTr("Caps Lock is on")
                visible: keyboard.capsLock
                textFormat: Text.PlainText
                color: "#fff0c7"
                font.family: root.uiFont
                font.pixelSize: 11 * root.uiScale
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    // Wide-screen layout keeps the secondary choices away from the login form.
    // All dimensions share uiScale, so the three groups also fit at 640 × 480.
    Column {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.leftMargin: 32 * root.uiScale
        anchors.bottomMargin: 38 * root.uiScale
        spacing: 8 * root.uiScale

        Text {
            text: qsTr("User")
            color: "#d2dbf8"
            font.family: root.uiFont
            font.pixelSize: 10 * root.uiScale
            leftPadding: 12 * root.uiScale
        }
        GlassSelector {
            id: userSelector
            objectName: "userSelector"
            uiScale: root.uiScale
            model: userModel
            textRole: "name"
            valueRole: "realName"
            labelRole: "realName"
            displayText: count > 0 ? root.displayName : qsTr("No users available")
            font.family: root.uiFont
            font.pixelSize: 11 * root.uiScale
            enabled: !root.authenticating && count > 0
            Accessible.name: qsTr("User")
            Accessible.description: qsTr("Choose the account to sign in to")
            onCurrentIndexChanged: {
                if (root.initialized)
                    root.resetPrompt();
            }
            onActivated: password.forceActiveFocus()
            KeyNavigation.tab: sleepButton.visible ? sleepButton : restartButton.visible ? restartButton : shutdownButton.visible ? shutdownButton : sessionSelector
            KeyNavigation.backtab: submitButton
        }
    }

    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 25 * root.uiScale
        spacing: 18 * root.uiScale

        PowerAction {
            id: sleepButton
            uiScale: root.uiScale
            iconSource: "assets/sleep.svg"
            text: qsTr("Sleep")
            font.family: root.uiFont
            font.pixelSize: 11 * root.uiScale
            visible: sddm.canSuspend
            enabled: !root.authenticating
            onClicked: sddm.suspend()
            KeyNavigation.tab: restartButton.visible ? restartButton : shutdownButton.visible ? shutdownButton : sessionSelector
            KeyNavigation.backtab: userSelector
        }
        PowerAction {
            id: restartButton
            uiScale: root.uiScale
            iconSource: "assets/restart.svg"
            text: qsTr("Restart")
            font.family: root.uiFont
            font.pixelSize: 11 * root.uiScale
            visible: sddm.canReboot
            enabled: !root.authenticating
            onClicked: sddm.reboot()
            KeyNavigation.tab: shutdownButton.visible ? shutdownButton : sessionSelector
            KeyNavigation.backtab: sleepButton.visible ? sleepButton : userSelector
        }
        PowerAction {
            id: shutdownButton
            uiScale: root.uiScale
            iconSource: "assets/shutdown.svg"
            text: qsTr("Shut Down")
            font.family: root.uiFont
            font.pixelSize: 11 * root.uiScale
            visible: sddm.canPowerOff
            enabled: !root.authenticating
            onClicked: sddm.powerOff()
            KeyNavigation.tab: sessionSelector
            KeyNavigation.backtab: restartButton.visible ? restartButton : sleepButton.visible ? sleepButton : userSelector
        }
    }

    Column {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: 32 * root.uiScale
        anchors.bottomMargin: 38 * root.uiScale
        spacing: 8 * root.uiScale

        Text {
            text: strings.session
            color: "#d2dbf8"
            font.family: root.uiFont
            font.pixelSize: 10 * root.uiScale
            leftPadding: 12 * root.uiScale
        }
        GlassSelector {
            id: sessionSelector
            objectName: "sessionSelector"
            uiScale: root.uiScale
            model: sessionModel
            textRole: "name"
            displayText: count > 0 ? currentText : qsTr("No sessions available")
            font.family: root.uiFont
            font.pixelSize: 11 * root.uiScale
            enabled: !root.authenticating && count > 0
            Accessible.name: strings.session
            Accessible.description: qsTr("Choose the desktop session")
            onActivated: password.forceActiveFocus()
            KeyNavigation.tab: password
            KeyNavigation.backtab: shutdownButton.visible ? shutdownButton : restartButton.visible ? restartButton : sleepButton.visible ? sleepButton : userSelector
        }
    }

    Component.onCompleted: Qt.callLater(restoreSelections)
}
