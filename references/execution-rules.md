# Configure execution rules on another computer

Install this skill and the search tools first. Locate that computer's `es.exe`, `flpsearch.exe`, and Python executable; the paths elsewhere in this skill describe the original installation and may differ. Use those discovered paths for searches and setup.

The skill requests outside-sandbox execution even without persistent rules. The existing rule generator covers the Everything and FileLocator entry points, not the Listary helper. Use the normal outside-sandbox execution mechanism for Listary; adding it as the preferred tool does not change saved approvals. To save approval for those two entry points, use `scripts/configure_execution_rules.py` from the installed skill. Its default mode prints rules without changing files. It derives the preview-helper path from its own installation, validates the supplied files, and quotes paths for the rules format.

For example, after changing the paths to match the new computer:

```powershell
& 'C:\Python\python.exe' -B 'C:\Users\Alice\.codex\skills\local-file-search\scripts\configure_execution_rules.py' --es 'C:\Tools\Everything\es.exe' --flpsearch 'C:\Program Files\Mythicsoft\FileLocator Pro\flpsearch.exe'
```

Review the printed rules. With the user's authorization to save these command exceptions, run the same command with `--install`. It writes only `rules/local-file-search.rules` under `CODEX_HOME`, or `~/.codex` when that variable is unset. Use `--codex-home <directory>` if this Codex installation uses another location. The script refuses to overwrite different existing rules or change `default.rules`.

Restart Codex after installation. If `codex` is available, validate each generated command prefix with `codex execpolicy check --rules <generated-file> -- <command>`. Then test one scoped filename search and one scoped content search outside the sandbox.

The rules allow the fixed Everything client and the fixed Python/helper/FileLocator command sequence. They do not allow a general shell, unrestricted Python, or index-maintenance tools. Search exports still require the corresponding user request. Host or managed policy can override an allow rule; shell wrappers may prevent a match. Importing the skill alone does not activate rules stored inside its folder.

Do not install rules silently during an ordinary search. For Windows setup, follow the execution interface's approval mechanism. Outside-sandbox execution does not require administrator/UAC elevation by itself.

See the [official Codex rules documentation](https://learn.chatgpt.com/docs/agent-configuration/rules) for rule loading and precedence.
