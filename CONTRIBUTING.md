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

5. Follow along the README example!

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

If you have any questions or need assistance, feel free to reach out by creating an issue in the repository or contacting the original author: [gennadiy.donchyts@gmail.com](mailto:gennadiy.donchyts@gmail.com).

Thank you for contributing to the QGIS Earth Engine Plugin!
