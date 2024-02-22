---@type MappingsTable
local M = {}

M.general = {
  n = {
    ["<C-u>"] = { "<C-u>zz", "Move middle up" },
    ["<C-d>"] = { "<C-d>zz", "Move middle down" },
    ["<leader>y"] = { "+y", "Copy to clipboard" },
    ["<leader>Y"] = { "+y", "Copy to clipboard" },

    [";"] = { ":", "enter command mode", opts = { nowait = true } },
    ["<C-f>"] = { "<cmd>silent !tmux neww tmux-sessionizer<CR>", "Run tmux sessionizer. Works only in tmux session" }
  },
  v = {
    [">"] = { ">gv", "indent" },
    ["<leader>p"] = { '"_dP', "Paste vithout saving" },
    ["<leader>y"] = { "+y", "Copy to clipboard" },
    ["y"] = { "ygv<Esc>", "Better yank" },
  },
} -- mo keybinds!

M.harpoon = {
  n = {
    ["<leader>a"] = {
      function()
        local harpoon = require("harpoon")
        harpoon:list():append()
      end,
      "[A]ppend buffer to Harpoon list"
    },
    ["<leader>d"] = {
      function()
        local harpoon = require("harpoon")
        harpoon:list():remove()
      end,
      "[D]elete buffer from Harpoon list"
    },
    ["<C-e>"] = {
      function()
        local harpoon = require("harpoon")
        harpoon.ui:toggle_quick_menu(harpoon:list())
      end,
      "Toggle Harpoon list"
    },
    ["<C-S-P>"] = {
      function()
        local harpoon = require("harpoon")
        harpoon:list():prev()
      end,
      "Toggle previous buffers stored within Harpoon list"
    },
    ["<C-S-N>"] = {
      function()
        local harpoon = require("harpoon")
        harpoon:list():next()
      end,
      "Toggle next buffers stored within Harpoon list"
    },
  },
}

return M
