let mapleader = " "
nnoremap <Space> <Nop>

nnoremap <leader>cd :Explore<CR>

nnoremap <leader>w :w<CR>
nnoremap <leader>qa :qa<CR>
nnoremap <leader>so :so<CR>

" Save, rebuild, and run the current standalone C++ file.
function! s:RunCpp() abort
    if &buftype !=# '' || empty(expand('%'))
        echoerr 'Run: open a C++ file first.'
        return
    endif
    if &filetype !=# 'cpp' && index(['cpp', 'cc', 'cxx', 'c++', 'C'], expand('%:e')) < 0
        echoerr 'Run: the current file is not C++.'
        return
    endif
    let l:compiler = executable('g++') ? 'g++' : executable('clang++') ? 'clang++' : ''
    if empty(l:compiler)
        echoerr 'Run: install g++ or clang++ first.'
        return
    endif
    update
    let l:binary = tempname()
    try
        execute '!' . l:compiler . ' -std=c++17 -Wall -Wextra '
            \ . shellescape(expand('%:p'), 1) . ' -o ' . shellescape(l:binary, 1)
            \ . ' && ' . shellescape(l:binary, 1)
    finally
        call delete(l:binary)
    endtry
endfunction

command! Run call <SID>RunCpp()
" Vim user commands must start uppercase; expand only the exact :run command.
cnoreabbrev <expr> run getcmdtype() ==# ':' && getcmdline() ==# 'run' ? 'Run' : 'run'

set number
set mouse=a
set ignorecase
set smartcase
set incsearch
set expandtab
set shiftwidth=4
set tabstop=4

" Use wl-clipboard as Vim's clipboard provider on Wayland.  This Vim build
" has +clipboard_provider, but was compiled without native +clipboard.
if has('clipboard_provider') && executable('wl-copy') && executable('wl-paste')
    function! ChihinWlClipboardCopy(reg, type, lines) abort
        let l:args = a:reg ==# '*' ? 'wl-copy --primary' : 'wl-copy'
        call system(l:args, a:lines)
    endfunction

    function! ChihinWlClipboardPaste(reg) abort
        let l:args = 'wl-paste --no-newline'
        if a:reg ==# '*'
            let l:args .= ' --primary'
        endif
        return ['', systemlist(l:args)]
    endfunction

    let v:clipproviders['wl_clipboard'] = {
        \ 'available': {-> v:true},
        \ 'copy': {'+': function('ChihinWlClipboardCopy'), '*': function('ChihinWlClipboardCopy')},
        \ 'paste': {'+': function('ChihinWlClipboardPaste'), '*': function('ChihinWlClipboardPaste')}
        \ }
    set clipmethod=wl_clipboard
endif
set clipboard=unnamedplus
set termguicolors
set cursorline
set encoding=utf-8
set relativenumber
set smartindent
set autoindent
syntax on
set hidden
set scrolloff=8
set backspace=indent,eol,start
set showcmd
set ruler
set background=dark
set wrap

call plug#begin('~/.vim/plugged')
Plug 'junegunn/fzf.vim'
Plug 'tpope/vim-surround'
Plug 'tpope/vim-fugitive'
Plug 'vim-airline/vim-airline'
call plug#end()

colorscheme catppuccin

" Let Kitty's background opacity and blur show through Vim's main editing
" areas. Reapply after every colorscheme change, since themes reset these.
function! s:EnableKittyTransparency() abort
    highlight Normal       guibg=NONE ctermbg=NONE
    highlight NormalNC     guibg=NONE ctermbg=NONE
    highlight SignColumn   guibg=NONE ctermbg=NONE
    highlight FoldColumn   guibg=NONE ctermbg=NONE
    highlight EndOfBuffer  guibg=NONE ctermbg=NONE
endfunction

augroup kitty_transparency
    autocmd!
    autocmd ColorScheme * call <SID>EnableKittyTransparency()
augroup END
call <SID>EnableKittyTransparency()

highlight LineNr guifg=#9399b2 ctermfg=249
highlight CursorLineNr guifg=#f9e2af gui=bold cterm=bold ctermfg=222
