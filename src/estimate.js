const styles = {
  formRow: { display: "flex", flexDirection: "row", gap: 10, marginBottom: 10 },
};

const rpcConstants = "/chains/main/blocks/head/context/constants";
const rpcVotingPower = "/chains/main/blocks/head/votes/total_voting_power";

const networks = {
  main: "https://mainnet-tezos.giganode.io",
  florence: "https://florence-tezos.giganode.io",
};

const fetchJson = async (url) => {
  return await (await fetch(url)).json();
};

const fetchConstants = async (network) => {
  const url = `${networks[network]}${rpcConstants}`;
  return await fetchJson(url);
};

const fetchActiveRolls = async (network) => {
  const url = `${networks[network]}${rpcVotingPower}`;
  return await fetchJson(url);
};

const App = () => {
  const [rolls, setRolls] = React.useState("1");
  const [tzNetwork, setTzNetwork] = React.useState("main");
  const [message, setMessage] = React.useState("");
  const [errors, setErrors] = React.useState([]);
  const [calculationResult, setCalculationResult] = React.useState("");
  const [running, setRunning] = React.useState(false);
  const [pyodideLoading, setPyodideLoading] = React.useState(null);

  const addError = (error) => {
    setErrors([...errors, error]);
  };

  const deleteError = (index) => {
    const newErrors = [...errors];
    newErrors.splice(index, 1);
    setErrors(newErrors);
  };

  React.useEffect(() => {
    const pyodidePromise = loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.17.0/full/",
    });
    pyodidePromise.then(
      (pyodide) => {
        pyodide.loadPackage(["scipy", "micropip"]);
        return pyodide;
      },
      (err) => {
        console.error(err);
        addError(err);
      }
    );
    setPyodideLoading(pyodidePromise);
  }, []);

  const run = async () => {
    setErrors([]);
    setRunning(true);
    try {
      setMessage("Fetching protocol constants...");
      const constants = await fetchConstants(tzNetwork);
      setMessage("Getting active roll count...");
      const activeRolls = await fetchActiveRolls(tzNetwork);
      setMessage("Calculating...");
      console.log("constants", constants);
      const preservedCycles = constants.preserved_cycles;

      const code = `
import micropip
await micropip.install('./py/dist/bakestimator-0.1-py3-none-any.whl')

from bakestimator import calc, fmt
fmt.text(calc.compute(${activeRolls}, 
         baking_rolls=${rolls}, 
         cycles=${preservedCycles},
         **calc.args_from_constants(${JSON.stringify(constants)})))
`;

      const pyodide = await pyodideLoading;
      const result = await pyodide.runPythonAsync(code);
      setCalculationResult(result);
    } catch (err) {
      addError(err);
    } finally {
      setMessage("");
      setRunning(false);
    }
  };

  const handleRollsChange = (e) => {
    setRolls(e.target.value);
    setCalculationResult("");
  };

  const handleTzNetworkChange = (e) => {
    setTzNetwork(e.target.value);
    setCalculationResult("");
  };

  const rollsAsInt = parseInt(rolls);
  const rollsInputValid = Number.isInteger(rollsAsInt) && rollsAsInt > 0;

  return (
    <div className="m-4">
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h1 className="title">Baking Estimator</h1>
          <h2 className="subtitle">
            Estimate Tezos baking rewards and deposits
          </h2>
        </div>
        <div className="is-flex is-flex-justify-content-end is-flex-wrap-wrap">
          <a
            href="https://tezos.gitlab.io/introduction/howtorun.html#deposits-and-over-delegation"
            title="Link to Tezos documentation on over-delegation"
          >
            <span className="icon">
              <img src="./school.svg" alt="Oxford cap" />
            </span>
          </a>
          <div className="mr-2" />
          <a
            href="https://github.com/tqtezos/bakestimator"
            title="Link to source code respository"
          >
            <span className="icon">
              <img src="./github.svg" alt="Github Octocat" />
            </span>
          </a>
        </div>
      </div>
      <hr />
      <div className="field is-grouped">
        <div className="field is-horizontal m-2">
          <div className="field-label is-normal">
            <label className="label">Network</label>
          </div>
          <div className="control">
            <div className="select">
              <select onChange={handleTzNetworkChange} value={tzNetwork}>
                <option>main</option>
                <option>florence</option>
              </select>
            </div>
          </div>
        </div>

        <div className="field is-horizontal m-2">
          <div className="field-label is-normal">
            <label className="label">Rolls</label>
          </div>
          <div className="control">
            <input
              className={`input ${rollsInputValid ? "" : "is-danger"}`}
              type="number"
              value={rolls}
              maxLength={6}
              style={{ maxWidth: 100 }}
              onChange={handleRollsChange}
            />
          </div>
        </div>

        <div className="field is-horizontal m-2">
          <div className="field-label is-normal">
            <label className="label is-invisible">-</label>
          </div>
          <div className="control">
            <a
              className={`button is-info ${running ? "is-loading" : ""}`}
              disabled={!rollsInputValid || running}
              onClick={run}
            >
              Calculate
            </a>
          </div>
        </div>
      </div>
      <div className="mb-2">
        <span className="is-invisible">-</span>
        {message}
      </div>
      {errors.map((error, i) => {
        return (
          <article className="message is-danger">
            <div className="message-header">
              <p>Error</p>
              <button
                className="delete"
                aria-label="delete"
                onClick={() => deleteError(i)}
              ></button>
            </div>
            <div className="message-body">{error}</div>
          </article>
        );
      })}

      {calculationResult && <pre>{calculationResult}</pre>}
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById("app"));
