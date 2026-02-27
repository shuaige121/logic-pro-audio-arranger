let currentComposition = null;

function setOutput(obj) {
  const el = document.getElementById("output");
  el.textContent = typeof obj === "string" ? obj : JSON.stringify(obj, null, 2);
}

async function digitize() {
  const file = document.getElementById("inputFile").files[0];
  if (!file) {
    setOutput("Please choose an input file first.");
    return;
  }

  const form = new FormData();
  form.append("file", file);
  form.append("style", document.getElementById("style").value);

  const bars = document.getElementById("bars").value.trim();
  const tempo = document.getElementById("tempo").value.trim();
  const beats = document.getElementById("beats").value.trim();
  if (bars) form.append("bars", bars);
  if (tempo) form.append("tempo", tempo);
  if (beats) form.append("beats_per_bar", beats);

  setOutput("Digitizing...");
  const response = await fetch("/api/digitize", {
    method: "POST",
    body: form,
  });
  const payload = await response.json();
  if (!response.ok) {
    setOutput(payload);
    return;
  }

  currentComposition = payload.composition;
  document.getElementById("arrangeBtn").disabled = false;
  document.getElementById("packBtn").disabled = false;
  setOutput(payload);
}

async function arrange() {
  if (!currentComposition) {
    setOutput("Please digitize first.");
    return;
  }

  const body = {
    composition: currentComposition,
    project_name: document.getElementById("projectName").value || "Studio Arrangement",
    complexity: document.getElementById("complexity").value,
    arrangement_bars: Number(document.getElementById("arrBars").value || 32),
    loop_melody: document.getElementById("loopMelody").value === "true",
  };

  setOutput("Generating Logic kit...");
  const response = await fetch("/api/arrange", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  setOutput(payload);
}

async function midiPack() {
  if (!currentComposition) {
    setOutput("Please digitize first.");
    return;
  }
  const body = {
    composition: currentComposition,
    project_prefix: document.getElementById("projectName").value || "Studio Pack",
    styles: ["pop", "modal", "jazz"],
    bars: [32, 64],
    complexity: document.getElementById("complexity").value,
  };

  setOutput("Generating MIDI pack...");
  const response = await fetch("/api/midi-pack", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  setOutput(payload);
}

document.getElementById("digitizeBtn").addEventListener("click", digitize);
document.getElementById("arrangeBtn").addEventListener("click", arrange);
document.getElementById("packBtn").addEventListener("click", midiPack);
