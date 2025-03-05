PYTHON := $$(which python)
PIP := $$(PYTHON) -m pip
SIGN=":"
SEQUENCE := $$(printf "%0.s${SIGN}" $$(seq 1 200))

define headerline
	printf "%*.*s\n" $1 $2 "$(SEQUENCE)"
endef

define header
	printf "%*.*s\n" $1 $2 "::: $3:$4 $(SEQUENCE)"
endef

define format_txt
	printf "%*.*s\n" $1 $2 "::: $3: $4 $$(printf "%0.s#" $$(seq 1 200))"
endef

conda-build:
	@python -m build
	@#python setup.py sdist bdist_wheel

conda-info:
	@PACKAGE_NAME="wattleflow" && \
	if pip list 2>/dev/null | grep -q wattleflow; then \
		pip show $$PACKAGE_NAME 2>/dev/null ;\
		pip show $$PACKAGE_NAME 2>/dev/null | grep -q "Location: .*site-packages" && echo "Library '$$PACKAGE_NAME' IS COMPILED!." || echo "Library '$$PACKAGE_NAME' IS INSTALLED IN EDITABLE MODE." ;\
	fi

conda-install-java:
	@if ! java --version 2>/dev/null; then \
		bash -c "conda activate wattleflow && conda install openjdk -c conda-forge" ;\
	fi

conda-setup-env:
	@found=$$(conda info -e | awk '$$1 ~ "pypi-test" { print $$1 }' | wc -l) && \
	if [ $$found -gt 0 ]; then \
		echo "Environment already exist ..." ;\
	else \
		echo "Will create environement in a moment ..." ;\
		conda create --name pypi-test python=3.8 && sleep 2 ;\
	fi
	@conda deactivate && conda activate pypi-test;\

conda-setup-req: conda-setup-env
	@echo "You should run this proces only once, if you don't have Wattleflow dev environement configured."
	@read -p "Do you want to continue (N/y)" ans && if [ "$$ans" = "y" ]; then \
		pip install setuptools build wheel twine tox flake8 ;\	
	fi

docker:
	@echo "Building docker image ..."
	@cd dockers/sftp && make build 

git-create-key:
	@echo "Genereting key"
	@ssh-keygen -t ed25519 -C "wattleflow@outlook.com"

git-commit:
	@datum=$$(date +%Y%m%d%H)
	@git commit -m "Commit $$datum."
	@git branch -M default
	@git push -u origin default
	@echo "#####git remote set-url origin git@github.com:wattleflow/wattleflow.git" >/dev/null

git-init: 
	@git init
	@git add .
	@git config user.name "wattleflow"
	@git config user.email "wattleflow@outlook.com"
	@git remote add origin https://github.com/wattleflow/wattleflow.git 2>/dev/null
	@git remote -v
	@ssh -T git@github.com

git-ssh-server:
	@echo "SSH: Starting agent and adding key to server ..."
	@pgrep -x ssh-agent | while read pid; do if [ $$pid -gt 0 ]; then kill -9 $$pid 2>/dev/null; sleep 2; fi; done
	@eval "$$(ssh-agent -s)" && sleep 4 && ssh-add $$HOME/.ssh/id_ed25519


### I
install-download-conda:
	@touch /tmp/miniconda.sh
	@if [ ! -f "/tmp/miniconda.sh" ]; then \
		echo "Downloading miniconda ..." ;\
		curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh ;\
	fi

install-conda: download-conda
	@touch /tmp/miniconda.sh
	@sha256sum /tmp/miniconda.sh | cut -d " " -f1 | while read cal; do \
		hash="636b209b00b6673471f846581829d4b96b9c3378679925a59a584257c3fef5a3" ;\
		hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" ;\
		if [ "$$cal" = "$$hash" ]; then \
			echo "Miniconda: OK \n  $$hash\n  $$cal" ;\
			echo "Installation will start in sec ..." && bash /tmp/miniconda.sh 2> /dev/null ;\
			echo "Cleaning up ..." ;\
			rm -rf "/tmp/miniconda.sh" ;\
		else \
			echo "ERROR: hash differs\n   $$cal\n   $$hash" ;\
		fi \
	done

### J
jupyter:
	@echo "Starting jupyter-lab .."
	@pgrep jupyter-lab | while read pid; do if [ $$pid -gt 0 ]; then kill -9 $$pid 2>/dev/null; sleep 3; fi; done
	@conda run -n wattleflow jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --LabApp.token='' &
	@sleep 5 && echo $$(pgrep jupyter-lab)
	@find $$(jupyter --runtime-dir)/* -type f -name "*secret*" | while read n; do cat $$n; done

### P
flake-project:
	@echo "Project analysis ..."
	@flake8 src #--select=F400
flake-tests:
	@echo "Project analysis ..."
	@flake8 tests

project-backup: project-clean
	@tarfile="/mnt/d/projects/.backup/$$(date +%Y%m%d%H)-wattleflow.tar.gz" && \
	tar -czf "$$tarfile" $$(pwd) 2> /dev/null && \
	echo "Backup completed: $$tarfile"

project-build:
	@if ! pip list 2>/dev/null | grep -E "build|setuptools|wheel"; then \
		echo "You may need to install first: build setuptools wheel" ;\
	fi
	@pip install --upgrade pip build setuptools wheel
	@python -m build --no-isolation --skip-dependency-check

project-cache:
	@echo "__pycache__ .ipynb_checkpoints" | tr " " "\n" | while read dir; do \
		find . -type d -name "$$dir" -exec rm -rfv {} +; \
	done
	@echo "Cache cleaned!"

project-clean: project-cache
	@echo "build *.egg-info dist" | tr " " "\n" | while read dir; do find . -name "$$dir" -type d -exec rm -rfv {} +; done
project-compile: project-clean
	@if ! pip list 2>/dev/null | grep -q wattleflow; then \
		echo "Compiling wattleflow ..." ;\
		pip install -v --compile . ;\
	fi

project-distro: project-compile
	@echo "Installing wattleflow distro from wheel .."
	@pip install dist/wattleflow-0.1.0-py3-none-any.whl

project-editable: project-clean
	@echo "Installing editable project ..."
	@if ! pip list 2>/dev/null | grep -q wattleflow; then \
		echo "Installing wattleflow!"; \
		pip install -e . ; \
		pip show wattleflow; \
	else \
		echo "Wattleflow is already installed!"; \
	fi

project-install:
# @pip install -v --use-pep517 .
	@echo "Installing wattleflow distro ..."
	@pip install distro/worfklow

project-pylint: project-clean
	@echo "Generating pylint for wattleflow ..."
	@if ! pip list 2>/dev/null | grep -q pylint; then \
		echo "pylint nije instaliran. Pokrenite: pip install pylint"; \
		pip install pylint ;\
	fi
	@pylint wattleflow | tee /tmp/pylint.txt
	@echo "See details in (/tmp/pylint.txt)."


project-reinstall: project-clean
	@echo "Reinstalling wattleflow ..."
	@echo "pip install --user --upgrade --force-reinstall --ignore-installed --no-binary" 2>/dev/null
	@pip install -v --upgrade --ignore-installed --force-reinstall .

project-upgrade:
	@echo "Upgrading env pip and packages ..."
	@if ! pip list 2>/dev/null | grep -q wattleflow; then \
		python -m pip install --upgrade pip
		echo "Upgrading wattleflow package ..." ;\
		pip install -v --upgrade . ;\
	done

project-uninstall: project-clean
	@echo "Uninstalling wattleflow ..."
	@pip list | grep wattleflow | while read n; do \
		echo "Removing pip package ... " ;\
		pip uninstall wattleflow -y -v ;\
	done

project-vscode:
	@mkdir -p .vscode-test 2> /dev/null
	@echo "{" >  .vscode-test/settings.json
	@echo -n '   "python.envFile": "' >> .vscode-test/settings.json
	@echo -n "$$(pwd)/.env" >> .vscode-test/settings.json
	@echo '",' >> .vscode-test/settings.json
	@echo -n '   "python.analysis.extraPaths": [ "$${workspaceFolder}"' >> .vscode-test/settings.json
	@conda info -e | grep $$(basename $$(pwd)) | awk '{print $$3}' | while read path; do \
		echo -n ', "'; echo -n $$path; echo -n '"'; \
		echo -n ', "'; echo -n $$path/bin/python; echo -n '"'; \
		echo '" ]'; \
	done >> .vscode-test/settings.json
	@echo "}" >> .vscode-test/settings.json
	@ls -la .vscode-test/
	@cat .vscode-test/settings.json

sys-process:
	@echo "Syestem processes: Please wait ... [this is slow process]"
	@sudo netstat -tp | awk 'NR > 2 {split($$4, a, ":"); split($$7, b, "/"); if (length(b[1]) > 3) print a[2], b[1];}' | while read line; do \
		pid=$$(echo $$line | cut -d" " -f2)                  ;\
		port=$$(echo $$line | cut -d" " -f1)                 ;\
		$(call header,1,180,Port,$$port)                     ;\
		echo "::: [ lsof -i :$${port} ] :::\n"               ;\
		sudo lsof -i :$$port && echo                         ;\
		echo "::: [ ps -p $$pid -o pid,user,command ] :::\n" ;\
		ps -p $$pid -o pid,user,command                      ;\
		echo                                                 ;\
	done
	@# sudo fuser -v -a $$port/tcp && echo ;

sys-threads:
	@echo "Syestem threads: Please wait ... [this is slow process]"
	@sudo netstat -tp | awk 'NR > 2 {split($$4, a, ":"); split($$7, b, "/"); if (length(b[1]) > 3) print a[2], b[1];}' | while read line; do \
	{ \
		pid=$$(echo $$line | cut -d" " -f2)                     ;\
		port=$$(echo $$line | cut -d" " -f1)                    ;\
		$(call header,1,180,Pid ,$$pid)                         ;\
		$(call header,1,180,Port,$$port)                        ;\
		echo "::: [ fuser -avu $${port}/tcp ] :::\n"            ;\
		sudo fuser -avu $$port/tcp && echo                      ;\
		echo "::: [ lsof -i :$${port} ] :::\n"                  ;\
		sudo lsof -i :$$port                                    ;\
		echo "::: [ ps -p $${pid} -o pid,user,command ] :::\n"  ;\
		ps -p $$pid -o pid,user,command                         ;\
		echo "\n\n"                                             ;\
	} \
	done

sftp-ssh-clean:
	@echo "SSH: Cleanining up ..."
	@pgrep -x ssh-agent | while read pid; do if [ $$pid -gt 0 ]; then kill -9 $$pid 2>/dev/null; sleep 2; fi; done
	@ssh-keygen -f '/home/micro/.ssh/known_hosts' -R '0.0.0.0:2222' 2>/dev/null
	@ssh-keygen -f '/home/micro/.ssh/known_hosts' -R '127.0.0.1:2222' 2>/dev/null
	@ssh-keygen -f '/home/micro/.ssh/known_hosts' -R '[127.0.0.1]:2222' 2>/dev/null
	@rm -rf ~/.ssh/id_rsa ~/.ssh/id_rsa.pub 2>/dev/null

sftp-ssh-copy:
	@echo "Copying key to server micro@127.0.0.1"
	@ssh-copy-id -p 2222 -t $$HOME/.ssh/id_rsa.pub micro@127.0.0.1
	@cp $$HOME/.ssh/id_rsa.pub ~/projects/wattleflow/dockers/sftp/wattleflow

sftp-ssh-make:
	@echo "Setting up ssh ... micro@127.0.0.1"
	@ssh-keygen -t rsa -C "$$USER" -f $$HOME/.ssh/id_rsa && chmod 600 $$HOME/.ssh/id_rsa && echo

ssh-make-fernet:
	@echo "Setting up ssh ... micro@127.0.0.1"
	@ssh-keygen -t rsa -C "$$USER" -f $$HOME/.ssh/id_rsa && chmod 600 $$HOME/.ssh/id_rsa && echo

ssh-start:
	@echo "SSH: Starting agent and adding key to server ..."
	@pgrep -x ssh-agent | while read pid; do if [ $$pid -gt 0 ]; then kill -9 $$pid 2>/dev/null; sleep 2; fi; done
	@eval "$$(ssh-agent -s)" && sleep 4 && ssh-add $$HOME/.ssh/id_rsa


help:
	@awk '/^(\w+)([:-])/' "$(MAKEFILE_LIST)" | cut -d ":" -f1


## --------------------------------------------------------------
## Toggle Use of Tab Key for Setting Focus
## --------------------------------------------------------------

# pip install --user --upgrade --force-reinstall --ignore-installed --no-binary
# @conda info | awk -F ":" '/active environment/{gsub(/ /,"",$2);print $2}' | while read env; do
# @sudo netstat -tlup
# { 
# } & 
# done; 
# wait

# @echo "See details (/tmp/sys-threads.txt)"

# printf "%10s-" - 10s je padding.
# printf "$(format_text): %*.*s" 1 100 $$SEQUENCE

# CONTAINER ID   IMAGE         COMMAND                  CREATED      STATUS      PORTS                                       NAMES
# ec70d7fbaeb6   server-tika   "/usr/bin/tini -- ja…"   2 days ago   Up 2 days   0.0.0.0:9998->9998/tcp, :::9998->9998/tcp   wattleflow-tika
