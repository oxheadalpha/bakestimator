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
    <div>
      <div style={styles.formRow}>
        <label>Rolls:</label>
        <input
          type="number"
          value={rolls}
          onChange={(e) => {
            setRolls(e.target.value.toUpperCase());
          }}
        />
      </div>
      <div style={styles.formRow}>
        <label>Network:</label>
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
      <button onClick={run}>Calculate</button>
      <div>{message}</div>
      <pre>{calculationResult}</pre>
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById("app"));
