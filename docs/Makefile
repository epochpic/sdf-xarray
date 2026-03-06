# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
SOURCECODEDIR = ../src/sdf_xarray
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

livehtml:
	@sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" \
		--builder html \
		--watch "$(SOURCECODEDIR)" \
		--watch "../CONTRIBUTING.md" \
		--quiet \
		--ignore "$(SOURCEDIR)/generated" \
		--ignore "$(BUILDDIR)/jupyter_execute" \
		--ignore "$(SOURCECODEDIR)/__pycache__"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
