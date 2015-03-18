clean:
	find . -name *.pyc -delete

db-create:
	python db_create.py

run:
	python run.py

test:
	py.test --cov-report term-missing --cov app

install:
	pip install -r requirements.txt

freeze:
	pip freeze > requirements.txt
