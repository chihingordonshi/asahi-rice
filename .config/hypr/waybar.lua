local waybarAutohide = os.getenv("HOME") .. "/.config/hypr/scripts/waybar-autohide"

function ToggleWaybarVisibility()
    hl.exec_cmd(waybarAutohide .. " --toggle-visibility")
end
