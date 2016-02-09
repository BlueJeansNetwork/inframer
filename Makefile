.PHONY: deps dummy run test

## so we can parse args to 'make test'
ifeq (test,$(firstword $(MAKECMDGOALS)))
  ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(ARGS):;@:)
endif

deps:
	sudo pip install -r requirements.txt

dummy:
	python helpers/dummy-data/load_dummy_data.py

run:
	python api.py

test:
	./create-test.sh && ./test.sh 2>/dev/null
