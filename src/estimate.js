async function main() {
  const output = document.getElementById("output");
  output.innerHTML = "Running...";

  const constantsUrl =
    "http://florence-tezos.giganode.io/chains/main/blocks/head/context/constants";
  const totalActiveRollsUrl =
    "http://florence-tezos.giganode.io/chains/main/blocks/head/votes/total_voting_power";
  console.log(constantsUrl);
  //const constants = JSON.stringify(await (await fetch(constantsUrl)).json());
  //const activeRolls = await (await fetch(totalActiveRollsUrl)).json();
  const activeRolls = 85000;
  const code = `
      import micropip
      await micropip.install('./py/dist/bakestimator-0.1-py3-none-any.whl')

      from bakestimator import calc, fmt
      fmt.text(calc.compute(${activeRolls}))
    `;

  output.innerHTML = await pyodide.runPythonAsync(code);
}
