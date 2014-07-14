.PHONY: deps develop

all: deps
	PYTHONPATH=.venv ; . .venv/bin/activate

.venv:
	if [ ! -e ".venv/bin/activate_this.py" ] ; then virtualenv --clear .venv ; fi

deps: .venv
	PYTHONPATH=.venv ; . .venv/bin/activate && .venv/bin/pip install -U -r requirements.txt

develop: .venv
	. .venv/bin/activate && .venv/bin/python setup.py develop

test: .venv
	. .venv/bin/activate && .venv/bin/python setup.py test $*

clean:
	rm -rf .venv *.egg-info *.log build
	rm -f `find . -name \*.pyc -print0 | xargs -0`
