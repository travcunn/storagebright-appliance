clean:
	find . -name *.pyc -delete

db-create:
	python db_create.py

run:
	python run.py

test:
	py.test tests.py

install:
	pip install -r requirements.txt
