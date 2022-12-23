.PHONY: wheel start

wheel:
	cd src/py && pip3 wheel -w dist/ .

start: wheel
	cd src && python3 -m http.server 8001

gh-pages:
	./mkpages
