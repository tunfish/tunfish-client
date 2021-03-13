# -------------
# Configuration
# -------------

$(eval venv        := .venv)
$(eval pip         := $(venv)/bin/pip)
$(eval python      := $(venv)/bin/python)
$(eval pytest      := $(venv)/bin/pytest)


# -------------------------------------
# https://backdoor-collective.org/docs/
# -------------------------------------

# Setup Python virtualenv
setup-virtualenv:
	@test -e $(python) || python3 -m venv $(venv)

test: setup-virtualenv
	@test -e $(pytest) || $(pip) install --requirement requirements-test.txt
	$(pytest) tests -vvv
