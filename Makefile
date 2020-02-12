clean:
	rm -rf .tmp .eggs build dist *.egg-info

lint:
	black ruv_dl tests --check

test: clean
	tox

build: clean lint
	python setup.py sdist bdist_wheel

check:
	twine check dist/*

pypi: build check
	twine upload dist/*

test_pypi: build check
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*