export CORES=6

travis: travis-install travis-doc build-cpp tests-cpp

travis-install:
	pip install -e .
	pip install -r requirements.txt
	pip install -r docs/requirements.txt
	pip install -r tests/requirements.txt

travis-doc: build-doc

rm-doc:
	rm -rf docs/api
	rm -rf _build

build-doc:
	sphinx-build -W --color -c docs/ -b html docs/ _build/html

serve-doc:
	sphinx-serve

update-doc: build-doc serve-doc

yolo: rm-doc build-doc serve-doc

build-cpp:
	mkdir -p build
	cd build
	CXX=g++-8 CC=gcc-8 cmake ..
	make -j $CORES

tests-cpp: build-cpp
	make coverage


