# Contributing to QGIS Earth Engine Plugin

Thank you for your interest in contributing to the QGIS Earth Engine Plugin! We appreciate your support and contributions.

## Setting Up for Local Development

Follow these steps to set up the plugin locally for development:

1. Clone the repository:
   ```bash
   git clone https://github.com/gee-community/qgis-earthengine-plugin.git
   cd qgis-earthengine-plugin
   ```

2. Install dependencies and set up the QGIS python environment using [`paver`](https://github.com/paver/paver):
   ```bash
   paver setup
   ```

3. Create a symlink of this project into the QGIS plugin directory:
   ```bash
   paver install
   ```

4. Open QGIS and enable the plugin via the plugin manager. Verify that the custom `about` message is displayed.

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
   paver setup
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
- If possible, add tests to cover your changes and ensure they pass.

## Questions or Help?

If you have any questions or need assistance, feel free to reach out by creating an [issue](https://github.com/gee-community/qgis-earthengine-plugin/issues) or adding a post in the [Discussions](https://github.com/gee-community/qgis-earthengine-plugin/discussions).


## Release Process

When preparing a new release, follow these steps:

1. Update the version number in the `ee_plugin/metadata.txt` file and any other relevant locations.
2. Build the plugin package for distribution, verifying the `ext_libs` don't contain dev dependencies (re-run `paver setup` if you installed dependencies from `dev-requirements.txt`): `paver package`
3. Upload the new release version to the [QGIS Plugin Manager](https://plugins.qgis.org/plugins/ee_plugin/#plugin-versions), ensuring metadata and version compatibility are correctly set in the `metadata.txt` file. Currently, maintainers (@gena or @zacdezgeo) must take this step. If it is a new version, QGIS maintainers must review and approve the upload, which can take several days.
4. Create the new release in GitHub with the ZIP of the plugin section. GitHub will require you add a tag of the version.

> Releases on GitHub can be incremented by 0.0.0.X while the releases on the QGIS plugin repository are incremented by 0.0.X. We can publish release on GitHub and update the underlying ZIP on the plugin repository release as long as it is still an experimental version. This enables us to release more frequently without waiting on QGIS maintainers approval.

Thank you for contributing to the QGIS Earth Engine Plugin!
