precommit
=========

### hooks
#### `check-codeowners`

Ensures that for any given file, either it or one of its parent module initializer's has a value for the given variable 
name, e.g. `__owner__ = "@Org/team"`. An empty string can be provided for the value to bypass enforcement. If a module 
initializer has a defined owner (empty string excluded) then all of it's descendants will not require code owner 
attribution.

Flags
- `--auto-fix` If the variable is missing, automatically add attribution using the team defined in 
`git --config user.team` erring if the config value is not defined.
- `--variable-name` TODO: this could be updated to be a regex expression?

#### `create-codeowners`

Updates an existing `CODEOWNERS` file by scanning **all** files in the current branch in the order they appear in 
`git ls-files`. For a given file the first match made by the regular expression will be written to the `CODEOWNERS` 
file as `file/path @Owner`. A file can be manually added to `CODEOWNERS` by including above the delimiter `# END`. If 
there is no delimiter in the file, `create-codeowners` will fail. 

Flags
- `--codeowners-path` Path to an existing `CODEOWNERS` file. 
- `--regex-pattern` Regex with single capture group used to get a file's owner(s) from an attribution. You'll likely be 
providing this value in a YAML file so be aware of YAMLs behavior around double and single quote escape sequences.

Example configuration file:

 ```yaml
-   repo: git://github.com/Patreon/precommit
    rev: v1.0.2
    hooks:
    -   id: check-codeowners
        exclude: ^test/
        args:
            - --variable-name=__owner__
            - --auto-fix
    -   id: create-codeowners
#       Always run in the case files are deleted, see https://github.com/pre-commit/pre-commit/issues/749
        always_run: true
        pass_filenames: false
        args:
            - --codeowners-path=CODEOWNERS
            - '--regex-pattern=__owner__\s*=\s*[''"]([\S\s]+)[''"]'
```