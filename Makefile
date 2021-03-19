.PHONY: tests
default: tests


clean:
	find . -name \*.pyc -delete
	find . -name __pycache__ -delete
	rm -rf .mypy_cache
	rm -rf *.egg-info
	rm -rf .pytest_cache .benchmarks
	rm -rf htmlcov .coverage
	rm -rf build dist

build.pypi: clean
	python setup.py sdist bdist_wheel

build.docker: clean
	docker build -t tesarekjakub/trickster:${PACKAGE_VERSION} .

publish.pypi:
	twine upload dist/*

publish.docker:
	docker push tesarekjakub/trickster:${PACKAGE_VERSION}

run.local:
	flask run

run.docker:
	docker run -p 5000:5000 tesarekjakub/trickster:${PACKAGE_VERSION}

check.lint: clean
	flake8 .

check.typing:
	mypy trickster app.py

check.tests: clean
	py.test tests/* -s \
		--cov trickster \
		--cov-report html \
		--cov-report term

check.all: clean check.lint check.typing check.tests