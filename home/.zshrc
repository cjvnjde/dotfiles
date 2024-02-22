export XDG_CONFIG_HOME="$HOME/.config"
export ZSH="$HOME/.oh-my-zsh"

path+=("$HOME/.local/scripts")

ZSH_THEME="bira"

plugins=(git autojump asdf npm docker tmux fzf node-bin)

alias vim="nvim"
bindkey -s ^f "tmux-sessionizer\n"

source $ZSH/oh-my-zsh.sh

if [ -f "$HOME/.zshrc_local" ]; then
    source "$HOME/.zshrc_local"
fi

