NANOCAT := $(shell which nanocat 2> /dev/null)
nanomsg:
ifndef NANOCAT
		cd /tmp && \
		wget https://github.com/nanomsg/nanomsg/archive/0.4-beta.tar.gz && \
		tar -xzf 0.4-beta.tar.gz && \
		cd nanomsg-0.4-beta && \
		./autogen.sh && \
		./configure && \
		make && \
		sudo make install && \
		sudo ldconfig
endif

devenv: nanomsg
	test -d devenv || (mkdir devenv && virtualenv devenv)
	(. devenv/bin/activate && \
	pip install -r requirements.txt -r requirements-dev.txt)

.PHONY: devenv nanomsg
