// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Controls.Basic as Controls

Controls.Button {
    id: control

    property url iconSource
    property real uiScale: 1

    implicitWidth: 78 * uiScale
    implicitHeight: 76 * uiScale
    padding: 0
    hoverEnabled: true
    activeFocusOnTab: true
    opacity: enabled ? 1 : 0.35
    Accessible.name: text

    background: Item { }
    contentItem: Column {
        spacing: 9 * control.uiScale

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 42 * control.uiScale
            height: width
            radius: width / 2
            color: control.down ? "#65ffffff" : control.hovered ? "#40ffffff" : "#25ffffff"
            border.width: (control.visualFocus ? 2 : 1) * control.uiScale
            border.color: control.visualFocus ? "#c4dfff" : "#20ffffff"
            Behavior on color { ColorAnimation { duration: 120 } }

            Image {
                anchors.centerIn: parent
                width: 21 * control.uiScale
                height: width
                source: control.iconSource
                sourceSize.width: width
                sourceSize.height: height
            }
        }

        Text {
            width: parent.width
            text: control.text
            textFormat: Text.PlainText
            color: "#f5f6ff"
            font: control.font
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
