
-- Default curves and animations, see https://wiki.hypr.land/Configuring/Advanced-and-Cool/Animations/
hl.curve("easeOutQuint",   { type = "bezier", points = { {0.23, 1},    {0.32, 1}    } })
hl.curve("easeInOutCubic", { type = "bezier", points = { {0.65, 0.05}, {0.36, 1}    } })
hl.curve("easeOutCubic",   { type = "bezier", points = { {0.33, 1},    {0.68, 1}    } })
hl.curve("linear",         { type = "bezier", points = { {0, 0},       {1, 1}       } })
hl.curve("almostLinear",   { type = "bezier", points = { {0.5, 0.5},   {0.75, 1}    } })
hl.curve("quick",          { type = "bezier", points = { {0.15, 0},    {0.1, 1}     } })
hl.curve("swift",          { type = 'bezier', points = { {0.55, 0},    {0.1, 1}     } })
hl.curve("springIn",       { type = "bezier", points = { {0.66, 0.13}, {0.27, 1.61} } })

-- Default springs
hl.curve("easy",           { type = "spring", mass = 1, stiffness = 900, dampening = 60 })
hl.curve("poppin",         { type = "spring", mass = 1, stiffness = 200, dampening = 25 })
hl.curve("wiggle",         { type = "spring", mass = 1, stiffness = 100, dampening = 10})

hl.animation({ leaf = "global",        enabled = true,  speed = 3,    bezier = "default" })
hl.animation({ leaf = "border",        enabled = true,  speed = 3,    bezier = "easeOutQuint" })
hl.animation({ leaf = "fade",          enabled = true,  speed = 3.03, bezier = "quick" })
hl.animation({ leaf = "layers",        enabled = true,  speed = 3.81, bezier = "easeOutQuint" })
hl.animation({ leaf = "workspaces",    enabled = true,  speed = 1.94, bezier = "almostLinear",  style = "fade" })
hl.animation({ leaf = "zoomFactor",    enabled = true,  speed = 7,    bezier = "quick" })
