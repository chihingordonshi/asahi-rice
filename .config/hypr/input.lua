-- Input. kb_layout confirmed against `localectl status` (X11 Layout: us) rather than
-- assumed, since this is exactly the kind of hardware/system-specific value that
-- shouldn't be copied blindly from another machine's config.

hl.config({
    input = {
        kb_layout    = "us",
        follow_mouse = 1,
    },
})
