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
  const [initializing, setInitializing] = React.useState(true);
  const [message, setMessage] = React.useState("");
  const [calculationResult, setCalculationResult] = React.useState("");

  React.useEffect(() => {
    languagePluginLoader
      .then(
        () => {
          return pyodide.loadPackage(["scipy", "micropip"]);
        },
        (err) => {
          console.error(err);
        }
      )
      .then(() => {
        setInitializing(false);
      });
  }, []);

  if (initializing) {
    return <div>Initializing...</div>;
  }

  const run = async () => {
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

    const result = await pyodide.runPythonAsync(code);
    setMessage("");
    setCalculationResult(result);
  };

  return (
    <div className="m-4">
      <div className="field is-grouped">
        <div className="field is-horizontal m-2">
          <div className="field-label is-normal">
            <label className="label">Network</label>
          </div>
          <div className="control">
            <div className="select">
              <select
                onChange={(e) => {
                  console.log(tzNetwork, e.target.value);
                  setTzNetwork(e.target.value);
                }}
                value={tzNetwork}
              >
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
              className="input"
              type="number"
              value={rolls}
              maxLength={6}
              style={{ maxWidth: 100 }}
              onChange={(e) => {
                setRolls(e.target.value.toUpperCase());
              }}
            />
          </div>
        </div>

        <div className="field is-horizontal m-2">
          <div className="field-label is-normal">
            <label className="label is-invisible">-</label>
          </div>
          <div className="control">
            <a className="button is-info" onClick={run}>
              Calculate
            </a>
          </div>
        </div>
      </div>
      <div className="mb-2">
        <span className="is-invisible">-</span>
        {message}
      </div>
      <pre>{calculationResult}</pre>
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById("app"));
