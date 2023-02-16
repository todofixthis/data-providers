.. image:: https://github.com/todofixthis/data-providers/actions/workflows/build.yml/badge.svg
   :target: https://github.com/todofixthis/data-providers/actions/workflows/build.yml
.. image:: https://readthedocs.org/projects/data-providers/badge/?version=latest
   :target: http://data-providers.readthedocs.io/

Data Providers
==============
Generic implementation of the flywheel pattern.

Data Providers is a great fit for situations where you need to bulk-fetch a lot
of data (e.g., from a database, API query, output from a computationally-
expensive operation, etc.) and then iterate over the results later on.

Requirements
------------
Data Providers is known to be compatible with the following Python versions:

- 3.11
- 3.10
- 3.9

.. note::
   I'm only one person, so to keep from getting overwhelmed, I'm only committing
   to supporting the 3 most recent versions of Python.  Data Providers may work
   in versions not listed here — there just won't be any test coverage to prove
   it 😇

Installation
------------
Install the latest stable version via pip::

    pip install phx-data-providers

.. important::
   Make sure to install `phx-data-providers`, **not** `data-providers`.  I
   created the latter at a previous job years ago, and after I left they never
   touched that project again and stopped responding to my emails — so in the
   end I had to fork it 🤷

Running Unit Tests
------------------
Install the package with the ``test-runner`` extra to set up the necessary
dependencies, and then you can run the tests with the ``tox`` command::

   pip install -e .[test-runner]
   tox -p

To run tests in the current virtualenv::

   python -m unittest

Documentation
-------------
Documentation is available on `ReadTheDocs`_.

If you are installing from source (see above), you can also build the
documentation locally:

#. Install extra dependencies (you only have to do this once)::

      pip install '.[docs-builder]'

#. Switch to the ``docs`` directory::

      cd docs

#. Build the documentation::

      make html


Releases
--------
Steps to build releases are based on `Packaging Python Projects Tutorial`_

.. important::

   Make sure to build releases off of the ``main`` branch, and check that all
   changes from ``develop`` have been merged before creating the release!

1. Build the Project
~~~~~~~~~~~~~~~~~~~~
#. Install extra dependencies (you only have to do this once)::

    pip install -e '.[build-system]'

#. Delete artefacts from previous builds, if applicable::

    rm dist/*

#. Run the build::

    python -m build

#. The build artefacts will be located in the ``dist`` directory at the top
   level of the project.

2. Upload to PyPI
~~~~~~~~~~~~~~~~~
#. `Create a PyPI API token`_ (you only have to do this once).
#. Increment the version number in ``pyproject.toml``.
#. Check that the build artefacts are valid, and fix any errors that it finds::

    python -m twine check dist/*

#. Upload build artefacts to PyPI::

    python -m twine upload dist/*


3. Create GitHub Release
~~~~~~~~~~~~~~~~~~~~~~~~
#. Create a tag and push to GitHub::

    git tag <version>
    git push

   ``<version>`` must match the updated version number in ``pyproject.toml``.

#. Go to the `Releases page for the repo`_.
#. Click ``Draft a new release``.
#. Select the tag that you created in step 1.
#. Specify the title of the release (e.g., ``Data Providers v1.2.3``).
#. Write a description for the release.  Make sure to include:
   - Credit for code contributed by community members.
   - Significant functionality that was added/changed/removed.
   - Any backwards-incompatible changes and/or migration instructions.
   - SHA256 hashes of the build artefacts.
#. GPG-sign the description for the release (ASCII-armoured).
#. Attach the build artefacts to the release.
#. Click ``Publish release``.

.. _Create a PyPI API token: https://pypi.org/manage/account/token/
.. _ReadTheDocs: https://data-providers.readthedocs.io/
.. _Packaging Python Projects Tutorial: https://packaging.python.org/en/latest/tutorials/packaging-projects/
.. _Releases page for the repo: https://github.com/todofixthis/data-providers/releases
