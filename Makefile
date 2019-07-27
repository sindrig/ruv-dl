clean:
	rm -rf .tmp .eggs build dist *.egg-info

test: clean
	python setup.py test

build: clean
	python setup.py sdist bdist_wheel

check:
	twine check dist/*

upload: build check
	env
	twine upload dist/*

test_upload: build check
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*