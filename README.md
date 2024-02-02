# pydoit-nb

<!---
Can use start-after and end-before directives in docs, see
https://myst-parser.readthedocs.io/en/latest/syntax/organising_content.html#inserting-other-documents-directly-into-the-current-document
-->

<!--- sec-begin-description -->

Library to support combining jupyter notebooks and pydoit.



[![CI](https://github.com/climate-resource/pydoit-nb/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/climate-resource/pydoit-nb/actions/workflows/ci.yaml)
[![Coverage](https://codecov.io/gh/climate-resource/pydoit-nb/branch/main/graph/badge.svg)](https://codecov.io/gh/climate-resource/pydoit-nb)
[![Docs](https://readthedocs.org/projects/pydoit-nb/badge/?version=latest)](https://pydoit-nb.readthedocs.io)

**PyPI :**
[![PyPI](https://img.shields.io/pypi/v/pydoit-nb.svg)](https://pypi.org/project/pydoit-nb/)
[![PyPI: Supported Python versions](https://img.shields.io/pypi/pyversions/pydoit-nb.svg)](https://pypi.org/project/pydoit-nb/)
[![PyPI install](https://github.com/climate-resource/pydoit-nb/actions/workflows/install.yaml/badge.svg?branch=main)](https://github.com/climate-resource/pydoit-nb/actions/workflows/install.yaml)

**Other info :**
[![License](https://img.shields.io/github/license/climate-resource/pydoit-nb.svg)](https://github.com/climate-resource/pydoit-nb/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/climate-resource/pydoit-nb.svg)](https://github.com/climate-resource/pydoit-nb/commits/main)
[![Contributors](https://img.shields.io/github/contributors/climate-resource/pydoit-nb.svg)](https://github.com/climate-resource/pydoit-nb/graphs/contributors)


<!--- sec-end-description -->

Full documentation can be found at:
[pydoit-nb.readthedocs.io](https://pydoit-nb.readthedocs.io/en/latest/).
We recommend reading the docs there because the internal documentation links
don't render correctly on GitHub's viewer.

## Installation

<!--- sec-begin-installation -->

pydoit-nb can be installed with conda or pip:

```bash
pip install pydoit-nb
conda install -c conda-forge pydoit-nb
```

Additional dependencies can be installed using

```bash
# To add notebook dependencies
pip install pydoit-nb[notebooks]

# If you are installing with conda, we recommend
# installing the extras by hand because there is no stable
# solution yet (issue here: https://github.com/conda/conda/issues/7502)
```

<!--- sec-end-installation -->

### For developers

<!--- sec-begin-installation-dev -->

For development, we rely on [poetry](https://python-poetry.org) for all our
dependency management. To get started, you will need to make sure that poetry
is installed
([instructions here](https://python-poetry.org/docs/#installing-with-the-official-installer),
we found that pipx and pip worked better to install on a Mac).

For all of work, we use our `Makefile`.
You can read the instructions out and run the commands by hand if you wish,
but we generally discourage this because it can be error prone.
In order to create your environment, run `make virtual-environment`.

If there are any issues, the messages from the `Makefile` should guide you
through. If not, please raise an issue in the [issue tracker][issue_tracker].

For the rest of our developer docs, please see [](development-reference).

[issue_tracker]: https://github.com/climate-resource/pydoit-nb/issues

<!--- sec-end-installation-dev -->
