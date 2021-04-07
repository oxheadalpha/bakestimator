.PHONY: wheel start

wheel:
	cd src/py && pip wheel -w dist/ .

start: wheel
	cd src && python3 -m http.server
