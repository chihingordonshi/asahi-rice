let mapleader = " "
nnoremap <Space> <Nop>

nnoremap <leader>cd :Explore<CR>

nnoremap <leader>w :w<CR>
nnoremap <leader>qa :qa<CR>
nnoremap <leader>so :so<CR>


set number
set mouse=a
set ignorecase
set smartcase
set incsearch
set expandtab
set shiftwidth=4
set tabstop=4
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

highlight LineNr guifg=#9399b2 ctermfg=249
highlight CursorLineNr guifg=#f9e2af gui=bold cterm=bold ctermfg=222
