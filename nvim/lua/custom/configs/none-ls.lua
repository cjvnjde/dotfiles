local null_ls = require "null-ls"
local utils = require "null-ls/utils"

local b = null_ls.builtins
local augroup = vim.api.nvim_create_augroup("LspFormatting", {})

local function root_files_condition(params)
  return params.conditional_utils.root_has_file(params.files)
end

local function package_json_condition(params)
  if params.conditional_utils.root_has_file { "package.json" } then
    local package_json_path = utils.get_root() .. "/package.json"
    local package_json = vim.json.decode(table.concat(vim.fn.readfile(package_json_path)))
    return package_json[params.field] ~= nil
  end

  return false
end

local sources = {

  -- webdev stuff
  -- b.formatting.deno_fmt, -- choosed deno for ts/js files cuz its very fast!

  -- Lua
  b.formatting.stylua,

  -- cpp
  -- b.formatting.clang_format,

  b.diagnostics.eslint_d.with {
    condition = function(conditional_utils)
      if
        root_files_condition {
          conditional_utils = conditional_utils,
          files = {
            ".eslintrc.js",
            ".eslintrc.cjs",
            ".eslintrc.yaml",
            ".eslintrc.yml",
            ".eslintrc.json",
          },
        }
      then
        return true
      end

      return package_json_condition {
        conditional_utils = conditional_utils,
        field = "eslintConfig",
      }
    end,
  },

  b.formatting.prettierd.with {
    condition = function(conditional_utils)
      if
        root_files_condition {
          conditional_utils = conditional_utils,
          files = {
            ".prettierrc",
            ".prettierrc.json",
            ".prettierrc.yml",
            "prettier.config.js",
            "prettier.config.cjs",
          },
        }
      then
        return true
      end

      -- Check for package.json config entry
      return package_json_condition {
        conditional_utils = conditional_utils,
        field = "prettier",
      }
    end,
  },
}

null_ls.setup {
  debug = true,
  sources = sources,
  on_attach = function(client, bufnr)
    if client.supports_method "textDocument/formatting" then
      vim.api.nvim_clear_autocmds { group = augroup, buffer = bufnr }
      vim.api.nvim_create_autocmd("BufWritePre", {
        group = augroup,
        buffer = bufnr,
        callback = function()
          vim.lsp.buf.format { bufnr = bufnr }
        end,
      })
    end
  end,
}
