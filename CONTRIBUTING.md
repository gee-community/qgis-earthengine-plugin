# Contributing to QGIS Earth Engine Plugin

Thank you for your interest in contributing to the QGIS Earth Engine Plugin! We appreciate your support and contributions.

## Setting Up for Local Development

To contribute locally, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/gee-community/qgis-earthengine-plugin.git
   cd qgis-earthengine-plugin
   ```

2. Create a virtual environment and install development dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. Create a symlink to your plugin directory so it can be loaded directly into QGIS:
   ```bash
   # macOS/Linux
   ln -sf "$(pwd)/ee_plugin" "$HOME/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/ee_plugin"
   ```

   ```powershell
   # Windows PowerShell (as Administrator)
   $src = "$(pwd)\ee_plugin"
   $dst = "$env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins\ee_plugin"
   New-Item -ItemType SymbolicLink -Path $dst -Target $src
   ```

4. Restart QGIS and enable the plugin via the Plugin Manager. Use the [Plugin Reloader](https://plugins.qgis.org/plugins/plugin_reloader/) for a faster development loop.

## Debugging within VSCode

The plugin can be debugged within [Visual Studio Code](https://code.visualstudio.com/) with the help of the [debugvs QGIS plugin](https://plugins.qgis.org/plugins/debug_vs).

> [!NOTE]
> At time of writing, an [outstanding PR](https://github.com/lmotta/debug_vs_plugin/pull/18) is required to successfully debug QGIS. This fix can manually be applied by copying the `__init__.py` file to your local installation of the `debugvs` plugin.
>
> Example MacOSX:
>
> ```
> curl https://raw.githubusercontent.com/lmotta/debug_vs_plugin/f1f28d72eb0221581b51c7dd1e4d0435db991eb8/__init__.py >> ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/debug_vs/__init__.py
> ```

### Workflow

1. Within QGIS:
   - Start “Enable Debug for Visual Studio Code” plugin.
2. Within the `qgis-earthengine-plugin` codebase opened within VSCode:
   - In Debug tools, launch the Run and Debug for “Python: Remote Attach”
   - In the codebase, add breakpoints where desired.
3. Within QGIS:
   - Run EarthEngine QGIS plugin to trigger code at desired breakpoints.

## Code Contribution Process

1. Ensure your contribution addresses an existing issue or discussion topic in the repository. If it does not, please open an issue to discuss your idea before starting.

2. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make your changes and ensure they follow the project’s coding standards.

4. Test your changes locally including reinstalling new dependencies for the QGIS environment with:
   ```bash
   pip install -r requirements.txt -t ee_plugin/extlibs  
   ```

5. Commit your changes with a clear and descriptive message:
   ```bash
   git commit -m "Add a clear description of your changes"
   ```

6. Push your changes to your forked repository:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Open a Pull Request (PR) against the main repository. Ensure your PR description includes the problem it solves, a summary of changes, and any additional notes.

## Coding Standards

- Follow Python’s [PEP 8](https://pep8.org/) guidelines for code style.
- Ensure that your code is well-documented with comments and docstrings.
- Use descriptive variable and function names.

## Testing

- Test your changes thoroughly before submitting a PR.

- Run unit tests using pytest from your virtual environment:

  ```bash
  pytest
  ```

- If possible, add tests to cover your changes and ensure they pass.

## Questions or Help?

If you have any questions or need assistance, feel free to reach out by creating an [issue](https://github.com/gee-community/qgis-earthengine-plugin/issues) or adding a post in the [Discussions](https://github.com/gee-community/qgis-earthengine-plugin/discussions).


## Building and Releasing with qgis-plugin-ci

We now use [`qgis-plugin-ci`](https://github.com/opengisch/qgis-plugin-ci) to manage packaging and release. Here’s how:

1. Build `extlibs`:
   ```bash
   pip install -r requirements.txt -t ee_plugin/extlibs  
   ```

2. Package plugin (including `extlibs`) and verify size:
   ```bash
   qgis-plugin-ci package <version> --asset-path ee_plugin/extlibs
   ```

   Replace `<version>` with your desired version tag (e.g., `1.3.0`). This will produce a zip under `dist/`.

3. Optionally publish to GitHub:
   ```bash
   git tag <version>
   git push origin <version>
   qgis-plugin-ci release <version>
   ```

   Make sure the changelog is up to date and version is bumped in `metadata.txt`.

Thank you for contributing to the QGIS Earth Engine Plugin!
