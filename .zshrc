# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ "$TERM" == "xterm-kitty" ]] && [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Lines configured by zsh-newuser-install
HISTFILE=~/.histfile
HISTSIZE=100
SAVEHIST=1000
bindkey -e
# End of lines configured by zsh-newuser-install
# The following lines were added by compinstall
# zstyle :compinstall filename '/home/chihin/.zshrc'

alias ls='eza --icons --group-directories-first'
alias ll='eza -lah --icons --group-directories-first --git'
alias la='eza -a --icons --group-directories-first'
alias lt='eza --tree --icons --group-directories-first'
alias cat='bat --paging=never'
alias grep='rg'
alias find='fd'
alias du='dust'
alias df='duf'
alias ps='procs'
alias ping='gping'
alias ..='cd ..'
alias top='btop'
alias lg='lazygit'
alias vim='nvim'

alias dotbackup='/usr/bin/git --git-dir=$HOME/.dotfiles --work-tree=$HOME'
alias gitlogin='git config --global user.email chihin.gordon.shi@gmail.com \
    && git config --global user.name chihingordonshi'

source /usr/share/zsh/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh
source ~/.zsh_functions

# Must run before zoxide's `cd` override below: nvm.sh detects NVM_DIR via
# `\cd -q ...`, which skips aliases but not shell functions, so zoxide's `cd`
# would otherwise intercept it and leave NVM_DIR unset.
source /usr/share/nvm/nvm.sh

eval "$(direnv hook zsh)"
eval "$(navi widget zsh)"
eval "$(mcfly init zsh)"
eval "$(zoxide init zsh --cmd cd)"
source <(fzf --zsh)

# End of lines added by compinstall
export PATH="$HOME/.local/bin:$HOME/go/bin:$PATH"
source /usr/share/zsh-theme-powerlevel10k/powerlevel10k.zsh-theme

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.


[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

if [[ $TERM == "xterm-kitty" ]]; then
  typeset -g POWERLEVEL9K_INSTANT_PROMPT=off
  pokemon-colorscripts -r --no-title
fi

# >>> juliaup initialize >>>

# !! Contents within this block are managed by juliaup !!

path=('/home/chihin/.juliaup/bin' $path)
export PATH
# Tab completion for juliaup and julia channel selection
[ -f "/home/chihin/.julia/juliaup/completions/zsh.zsh" ] && source "/home/chihin/.julia/juliaup/completions/zsh.zsh"

# <<< juliaup initialize <<<

alias music='mocp'
