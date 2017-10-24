# Contributing &amp; Support

## Overview

Sublime Versions | Description
-----------------|------------
ST2\ <=\ version\ <\ ST3 | Supported on a separate branch, but not actively.  Any further fixes or enhancements must come from the community.  Issues for versions less than ST3 will not be addressed moving forward by me.  Pull requests are welcome for back-porting features, enhancements, or fixes to the old branch, but the content of the pull **must** already exist on the main, actively developed branch.  I will not allow an older branch to exceed the main branch in regards to functionality. |
ST3 | Fully supported and actively maintained.

Contributions from the community are encouraged and can be done in a variety of ways:

- Bug reports
- Code reviewing
- Code patches via pull requests
- Documentation improvements via pull requests

## Bug Reports

1. Please **read the documentation** and **search the issue tracker** to try to find the answer to your question **before** posting an issue.

2. When an issue is created, a [template][template] will be shown, please fill out the appropriate sections. If the template is not followed, the issue will be marked `Invalid` and closed.

3. When creating an issue on the repository, please provide as much info as possible:

    - Provide environment information by running `Preferences->Package Settings->RegReplace->Support Info`.  The information will be copied to the clipboard; paste the info in issue.
    - Errors in console.
    - Detailed description of the problem.
    - Examples for reproducing the error.  You can post pictures, but if specific text or code is required to reproduce the issue, please provide the text in a plain text format for easy copy/paste.

    The more info provided, the greater the chance someone will take the time to answer, implement, or fix the issue.

4. Be prepared to answer questions and provide additional information if required.  Issues in which the creator refuses to respond to follow up questions will be marked as stale and closed.

## Reviewing Code

Take part in reviewing pull requests and/or reviewing direct commits.  Make suggestions to improve the code and discuss solutions to overcome weakness in the algorithm.

## Pull Requests

Pull requests are welcome, and if you plan on contributing directly to the code, there are a couple of things you should bare in mind.

Continuous integration tests are run on all pull requests and commits via [Travis CI][travis].  When making a pull request, the tests will be automatically run, and the request must pass to be accepted.  You can (and should) run these tests locally before pull requesting.  If it's not possible to run them locally, they will be run when the pull request is made, but it's strongly recommended that requesters make an effort to verify before requesting to allow for a quick, smooth merge.

Feel free to use a virtual environment if you are concerned about installing any of the Python packages.  In the future, I may use [tox][tox], but as I currently only test on Python 3.3, I wanted to keep things simple.

### Running Validation Tests

!!! tip "Tip"
    If you are using Sublime on a OSX or Linux/Unix system, and your installed environment meets all the requirements listed below, you can run all tests by executing the shell script:

    ```
    chmod +x run_tests.sh
    ./run_tests.sh
    ```

There are a couple of dependencies that must be present before running the tests.

1. As ST3 is the only current, actively supported version, Python 3.3 must be used to validate the tests.

2. Unit tests are run with `pytest`.  You can install [pytest][pytest] via:

    ```
    pip install pytest
    ```

    The tests should be run from the root folder of the plugin by using the following command:

    ```
    py.test .
    ```

3. Linting is performed on the entire project with `flake8`, `flake8-docstrings`, and `pep8-naming`.  These can be installed via:

    ```
    pip install flake8
    pip install flake8-docstrings
    pip install pep8-naming
    ```

    Linting is performed with the following command:

    ```
    flake8 .
    ```

## Documentation Improvements

A huge amount of time has been spent not only creating and supporting this plugin, but also writing this documentation.  If you feel it's still lacking, show your appreciation for the plugin by helping to improve the documentation.  Help with documentation is always appreciated and can be done via pull requests.  There shouldn't be any need to run validation tests when updating just the documentation.

You don't have to render the docs locally before pull requesting, but if you wish to, I currently use a combination of [mkdocs][mkdocs] with my own custom Python Markdown [extensions][pymdown-extensions] to render the docs.  You can preview the docs if you install these two packages.  The command for previewing the docs is `mkdocs serve` from the root directory.

--8<-- "refs.md"
