-- Minimal config: no plugin manager, no LSP, just sane defaults + one theme.
-- To change the theme, replace the name below. Try: habamax, retrobox, unokai,
-- desert, slate, torte, murphy (type :colorscheme <tab> to see all built-ins).
vim.cmd.colorscheme("habamax")

vim.opt.number = true         -- show line numbers
vim.opt.mouse = "a"           -- allow mouse in all modes
vim.opt.ignorecase = true     -- case-insensitive search...
vim.opt.smartcase = true      -- ...unless the search has a capital letter
vim.opt.incsearch = true      -- show matches as you type
vim.opt.expandtab = true      -- spaces instead of tabs
vim.opt.shiftwidth = 2
vim.opt.tabstop = 2
vim.opt.clipboard = "unnamedplus"  -- yank/paste shares the system clipboard
vim.opt.termguicolors = true  -- proper colors in the terminal
