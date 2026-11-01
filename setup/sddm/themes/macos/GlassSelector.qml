// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Controls.Basic as Controls

// Shared user/session picker. Explicit styling avoids any platform/KDE style.
Controls.ComboBox {
    id: control

    property real uiScale: 1
    property string labelRole: textRole

    implicitWidth: 244 * uiScale
    implicitHeight: 40 * uiScale
    leftPadding: 14 * uiScale
    rightPadding: 34 * uiScale
    topPadding: 4 * uiScale
    bottomPadding: 4 * uiScale
    hoverEnabled: true
    activeFocusOnTab: true
    opacity: enabled ? 1 : 0.45

    contentItem: Text {
        text: control.displayText
        textFormat: Text.PlainText
        font: control.font
        color: "#f5f6ff"
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    indicator: Image {
        source: "assets/chevron-down.svg"
        width: 16 * control.uiScale
        height: width
        sourceSize.width: width
        sourceSize.height: height
        anchors.right: parent.right
        anchors.rightMargin: 12 * control.uiScale
        anchors.verticalCenter: parent.verticalCenter
        opacity: 0.85
    }

    background: Rectangle {
        radius: 12 * control.uiScale
        color: control.down ? "#443c5391" : control.hovered ? "#363c5391" : "#26233064"
        border.width: (control.visualFocus ? 2 : 1) * control.uiScale
        border.color: control.visualFocus ? "#b9d5ff" : "#30ffffff"
        Behavior on color { ColorAnimation { duration: 120 } }
    }

    delegate: Controls.ItemDelegate {
        id: entry
        required property var model
        required property int index

        width: ListView.view.width
        height: 40 * control.uiScale
        highlighted: control.highlightedIndex === index
        hoverEnabled: true
        padding: 12 * control.uiScale
        font: control.font
        contentItem: Text {
            text: entry.model[control.labelRole] || entry.model[control.textRole] || ""
            textFormat: Text.PlainText
            color: "#ffffff"
            font.family: entry.font.family
            font.pixelSize: entry.font.pixelSize
            font.weight: control.currentIndex === entry.index ? Font.DemiBold : Font.Normal
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 7 * control.uiScale
            color: entry.highlighted || entry.hovered ? "#385e91cb" : "transparent"
        }
    }

    popup: Controls.Popup {
        // The pickers live at the bottom of the screen: menus open upward.
        y: -height - 8 * control.uiScale
        width: control.width
        padding: 6 * control.uiScale
        implicitHeight: Math.min(280 * control.uiScale, contentItem.implicitHeight + topPadding + bottomPadding)
        closePolicy: Controls.Popup.CloseOnEscape | Controls.Popup.CloseOnPressOutsideParent

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            highlightMoveDuration: 0
            boundsBehavior: Flickable.StopAtBounds
            Controls.ScrollIndicator.vertical: Controls.ScrollIndicator { }
        }

        background: Rectangle {
            radius: 14 * control.uiScale
            color: "#f0202c52"
            border.width: 1
            border.color: "#4cffffff"
        }
    }
}
