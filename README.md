`bakestimator` is a utility to estimate Tezos baking
rewards and deposits based on selected network's current protocol
constants and active roll count.

`bakestimator` is available as a command line utility and a web
applcation.

Web application is up at
<https://oxheadalpha.github.io/bakestimator/>.
This web application runs the same Python code to perform the
calculations as the command line version, in the browser, via
[Pyodide](https://github.com/pyodide/pyodide.) WebAssembly is [well
supported in modern browsers](https://caniuse.com/wasm) but there are
plenty of rough edges and `bakestimator` page [may crash with "out of
memory"](https://github.com/pyodide/pyodide/issues/1513) or other
errors. If that happens, try another browser or use command line
version.

Command line version can be installed via pip:

```
pip install git+https://github.com/oxheadalpha/bakestimator.git#subdirectory=src/py
```

and then just run

```
bakestimator
```

to get estimates for a single roll on the `mainnet` or

```
bakestimator --help
```

to see usage/available options.
