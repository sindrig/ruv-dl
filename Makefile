clean:
	rm -rf .tmp .eggs build dist *.egg-info

test: clean
	python setup.py test

build: clean
	python setup.py sdist bdist_wheel

check:
	twine check dist/*

pypi: build check
	twine upload dist/*

test_pypi: build check
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*