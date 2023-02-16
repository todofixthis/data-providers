Contents
========
.. toctree::
   :maxdepth: 1

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
