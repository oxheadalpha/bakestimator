const styles = {
  formRow: { display: "flex", flexDirection: "row", gap: 10, marginBottom: 10 },
};

const rpcConstants = "/chains/main/blocks/head/context/constants";
const rpcVotingPower = "/chains/main/blocks/head/votes/total_voting_power";

const MAINNET = "mainnet";

const defaultNetworks = {
  [MAINNET]: { rpc: "https://mainnet.api.tez.ie", sortOrder: 0 },
};

const fetchJson = async (url) => {
  return await (await fetch(url)).json();
};

const App = () => {
  const [networks, setNetworks] = React.useState(defaultNetworks);
  const [rolls, setRolls] = React.useState("1");
  const [fullBalance, setFullBalance] = React.useState("6000");
  const [delegatedBalance, setDelegatedBalance] = React.useState("0");
  const [tzNetwork, setTzNetwork] = React.useState(MAINNET);
  const [message, setMessage] = React.useState("");
  const [errors, setErrors] = React.useState([]);
  const [calculationResult, setCalculationResult] = React.useState("");
  const [running, setRunning] = React.useState(false);
  const [pyodideLoading, setPyodideLoading] = React.useState(null);
  const [constants, setConstants] = React.useState(null);

  const fetchConstants = async (network) => {
    const { constants } = networks[network];
    if (constants) return constants;
    const url = `${networks[network].rpc}${rpcConstants}`;
    return await fetchJson(url);
  };

  const fetchTotalVotingPower = async (network) => {
    const url = `${networks[network].rpc}${rpcVotingPower}`;
    return await fetchJson(url);
  };

  const networkNameCompare = (a, b) => {
    const na = networks[a];
    const nb = networks[b];
    const sa = na.sortOrder;
    const sb = nb.sortOrder;
    return sa === sb ? -a.localeCompare(b) : sa - sb;
  };

  const addError = (error) => {
    console.error(error);
    setErrors([...errors, error]);
  };

  const deleteError = (index) => {
    const newErrors = [...errors];
    newErrors.splice(index, 1);
    setErrors(newErrors);
  };

  React.useEffect(() => {
    (async () => {
      setConstants(null);
      setRunning(true);
      setMessage("Fetching protocol constants...");
      try {
        const constants = await fetchConstants(tzNetwork);
        setConstants(constants);
        setMessage("");
      } catch (err) {
        console.error(err);
        setMessage("Failed to fetch protocol constants");
        addError(err.getMessage());
      } finally {
        setRunning(false);
      }
    })();
  }, [networks, tzNetwork]);

  React.useEffect(() => {
    const pyodidePromise = loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.18.1/full/",
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

    (async () => {
      try {
        const testNets = await fetchJson("https://teztnets.xyz/teztnets.json");
        console.debug("Got testnet data", testNets);
        const networks = { ...defaultNetworks };
        for (const [networkName, data] of Object.entries(testNets)) {
          if (data.rpc_url) {
            networks[networkName] = {
              rpc: data.rpc_url,
              sortOrder: data.category === "Long-Running Teztnets" ? 1 : 2,
            };
          } else {
            console.warn(
              `Network ${networkName} has no rpc URL, skipping`,
              data
            );
          }
        }
        setNetworks(networks);
      } catch (err) {
        console.error("Failed to fetch test networks info", err);
      }
    })();
  }, []);

  const confidence = 0.9;

  const run = async () => {
    setErrors([]);
    setRunning(true);
    try {
      setMessage("Fetching protocol constants...");
      //const constants = await fetchConstants(tzNetwork);
      setMessage("Getting active roll count...");
      const totalVotingPower = await fetchTotalVotingPower(tzNetwork);
      if (typeof totalVotingPower !== "string") {
        setRunning(false);
        setErrors(["Unexpected total voting power value: " + totalVotingPower]);
        return;
      }
      setMessage("Calculating...");
      console.log("constants", constants);
      const preservedCycles = constants.preserved_cycles;
      const totalActiveStake = totalVotingPower;
      const constantsPyCode = JSON.stringify(constants)
        .replaceAll("true", "True")
        .replaceAll("false", "False")
        .replaceAll("null", "None");

      console.log(constants);

      const loadWheelCode = `
import micropip
await micropip.install('./py/dist/bakestimator-0.4-py3-none-any.whl')
      `;
      let code = null;

      const minimalStake = parseInt(constants.minimal_stake);
      code = `
${loadWheelCode}
from bakestimator import tenderbake
tenderbake.run(
    ${constantsPyCode},
    ${totalActiveStake},
    confidence=${confidence},
    cycles=${preservedCycles},
    full_balance=${fullBalance},
    delegated_balance=${delegatedBalance},
    eligibility_threshold=${minimalStake},
)
      `;
      console.debug(code);
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

  const handleFullBalanceChange = (e) => {
    setFullBalance(e.target.value);
    setCalculationResult("");
  };

  const handleDelegatedBalanceChange = (e) => {
    setDelegatedBalance(e.target.value);
    setCalculationResult("");
  };

  const handleTzNetworkChange = (e) => {
    setTzNetwork(e.target.value);
    setCalculationResult("");
  };

  const isValidBalance = (value, min = 0) =>
    typeof value === "number" && value >= min;

  const rollsAsInt = parseInt(rolls);
  const rollsInputValid = Number.isInteger(rollsAsInt) && rollsAsInt > 0;
  const fullBalanceAsFloat = parseFloat(fullBalance);
  const fullBalanceInputValid = isValidBalance(fullBalanceAsFloat, 6000);

  const delegatedBalanceAsFloat = parseFloat(delegatedBalance);
  const delegatedBalanceInputValid = isValidBalance(delegatedBalanceAsFloat);

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
            href="https://teztnets.xyz/"
            title="Link to Tezos testnets catalog"
          >
            <span className="icon">
              <img src="./lan.svg" alt="Computer Network" />
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
        <div className="field m-2">
          <label className="label">Network</label>
          <div className="control">
            <div className="select">
              <select onChange={handleTzNetworkChange} value={tzNetwork}>
                {Object.keys(networks)
                  .sort(networkNameCompare)
                  .map((n) => (
                    <option key={n}>{n}</option>
                  ))}
              </select>
            </div>
          </div>
        </div>

        <div className="field  m-2">
          <label className="label is-invisible">-</label>
          <div className="control">
            <a
              className={`button is-info ${running ? "is-loading" : ""}`}
              disabled={!rollsInputValid || running || !constants}
              onClick={run}
            >
              Calculate
            </a>
          </div>
        </div>
      </div>

      <div className="field is-grouped">
        <div className="field m-2">
          <label className="label">Full Balance</label>
          <div className="control">
            <input
              className={`input ${fullBalanceInputValid ? "" : "is-danger"}`}
              type="number"
              value={fullBalance}
              maxLength={6}
              style={{ maxWidth: 100 }}
              onChange={handleFullBalanceChange}
            />
          </div>
        </div>

        <div className="field m-2">
          <label className="label">Delegated Balance</label>
          <div className="control">
            <input
              className={`input ${
                delegatedBalanceInputValid ? "" : "is-danger"
              }`}
              type="number"
              value={delegatedBalance}
              maxLength={6}
              style={{ maxWidth: 100 }}
              onChange={handleDelegatedBalanceChange}
            />
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

      {calculationResult && (
        <div>
          <pre>{calculationResult}</pre>
          <div className="is-size-7">
            max values are calculated at {confidence * 100}% confidence
          </div>
        </div>
      )}
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById("app"));
