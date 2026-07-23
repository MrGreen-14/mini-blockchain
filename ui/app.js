// ---------------------------------------------------------------- //
//  Pasul 1: bara de stare.  Pasul 2: vizualizatorul de lant.         //
//  Formularul de tranzactie se adauga in pasul urmator.             //
// ---------------------------------------------------------------- //

const REFRESH_INTERVAL_MS = 2000;

// Elemente DOM -- le luam o singura data, nu la fiecare refresh
const elDot = document.getElementById("status-dot");
const elState = document.getElementById("status-state");
const elChainLength = document.getElementById("metric-chain-length");
const elMempoolSize = document.getElementById("metric-mempool-size");
const elPeers = document.getElementById("metric-peers");
const elUpdated = document.getElementById("status-updated");
const elBlocksContainer = document.getElementById("blocks-container");
const elTxForm = document.getElementById("tx-form");
const elTxResponse = document.getElementById("tx-response");
const elTxSender = document.getElementById("tx-sender");
const elPeersContainer = document.getElementById("peers-container");

// COINBASE, in ASCII, codificat hex -- asa arata inceputul lui
// `sender` la o tranzactie coinbase (restul campului e zero-padding).
const COINBASE_HEX_PREFIX = "434f494e42415345";

// Retinem cate blocuri am randat ultima data, ca sa nu reconstruim
// tot DOM-ul la fiecare 2 secunde daca lantul nu s-a schimbat --
// evitam un "flicker" vizual inutil.
let lastRenderedChainLength = -1;

function truncateHex(hex, headChars = 12, tailChars = 6) {
  if (!hex || hex.length <= headChars + tailChars + 3) return hex;
  return `${hex.slice(0, headChars)}...${hex.slice(-tailChars)}`;
}

function renderTransaction(tx) {
  const isCoinbase = tx.sender.toLowerCase().startsWith(COINBASE_HEX_PREFIX.toLowerCase());

  const senderDisplay = isCoinbase
    ? `<span class="tx-coinbase-badge">COINBASE</span>`
    : `<span class="field-value" title="${tx.sender}">${truncateHex(tx.sender, 8, 4)}</span>`;

  return `
    <div class="tx-item">
      ${senderDisplay}
      <span class="tx-arrow">-&gt;</span>
      <span class="field-value" title="${tx.receiver}">${truncateHex(tx.receiver, 8, 4)}</span>
      <span class="tx-amount">${tx.amount}</span>
    </div>
  `;
}

function renderBlock(block) {
  const txHtml = block.transactions.length > 0
    ? block.transactions.map(renderTransaction).join("")
    : `<p class="placeholder" style="margin:0;">fara tranzactii</p>`;

  return `
    <div class="block-card" data-index="${block.index}" data-hash="${block.hash}" data-prev-hash="${block.prev_hash}">
      <div class="block-header">
        <h3>Bloc #${block.index}</h3>
        <span class="block-tx-count">${block.transactions.length} tranzactie(i)</span>
      </div>
      <div class="block-field">
        <span class="field-label">hash</span>
        <span class="field-value" title="${block.hash}">${truncateHex(block.hash)}</span>
      </div>
      <div class="block-field">
        <span class="field-label">prev_hash</span>
        <span class="field-value" title="${block.prev_hash}">${truncateHex(block.prev_hash)}</span>
      </div>
      <div class="block-field">
        <span class="field-label">merkle_root</span>
        <span class="field-value" title="${block.merkle_root}">${truncateHex(block.merkle_root)}</span>
      </div>
      <div class="block-field">
        <span class="field-label">nonce</span>
        <span class="field-value">${block.nonce}</span>
      </div>
      <div class="block-tx-list">
        ${txHtml}
      </div>
    </div>
  `;
}

function renderConnector(prevBlock, nextBlock) {
  // Verificam chiar in JS, vizual, ca prev_hash-ul urmatorului bloc
  // chiar corespunde hash-ului blocului anterior -- exact regula pe
  // care is_chain_valid() o verifica in C, doar ca aici o "vezi".
  const linked = prevBlock.hash === nextBlock.prev_hash;
  const stateClass = linked ? "" : "broken";
  const label = linked ? "legatura verificata" : "LEGATURA RUPTA";

  return `
    <div class="chain-connector ${stateClass}">
      <span class="connector-line"></span>
      <span class="connector-label">${label}:</span>
      <span class="connector-hash">${truncateHex(prevBlock.hash, 8, 4)}</span>
    </div>
  `;
}

async function refreshChain() {
  try {
    const response = await fetch("/chain");
    if (!response.ok) throw new Error(`raspuns HTTP ${response.status}`);

    const data = await response.json();
    // data arata asa: {"length": 2, "blocks": [{index, prev_hash,
    //   merkle_root, nonce, hash, transactions: [{sender, receiver, amount}]}]}

    if (data.length === lastRenderedChainLength) {
      return; // nimic nou -- nu reconstruim DOM-ul degeaba
    }
    lastRenderedChainLength = data.length;

    if (data.blocks.length === 0) {
      elBlocksContainer.innerHTML = `<p class="placeholder">Lantul e gol inca -- niciun bloc minat.</p>`;
      return;
    }

    let html = "";
    data.blocks.forEach((block, i) => {
      html += renderBlock(block);
      if (i < data.blocks.length - 1) {
        html += renderConnector(block, data.blocks[i + 1]);
      }
    });

    elBlocksContainer.innerHTML = `<div class="blocks-stack">${html}</div>`;

  } catch (err) {
    elBlocksContainer.innerHTML = `<p class="placeholder">Eroare la incarcarea lantului: ${err.message}</p>`;
  }
}

async function refreshStatus() {
  try {
    // fetch("/status") -- fara host/port explicit, fiindca pagina asta
    // e servita chiar de Flask-ul nodului: "acelasi origin" ca API-ul.
    const response = await fetch("/status");

    if (!response.ok) {
      throw new Error(`raspuns HTTP ${response.status}`);
    }

    const data = await response.json();
    // data arata asa: {"state": "SYNCED", "chain_length": 4,
    //                  "mempool_size": 0, "peers": ["127.0.0.1:9002", ...]}

    elState.textContent = data.state;
    elChainLength.textContent = data.chain_length;
    elMempoolSize.textContent = data.mempool_size;
    elPeers.textContent = data.peers.length;

    elDot.classList.remove("synced", "syncing", "offline");
    if (data.state === "SYNCED") {
      elDot.classList.add("synced");
    } else if (data.state === "SYNCING") {
      elDot.classList.add("syncing");
    }

    const now = new Date();
    elUpdated.textContent = `actualizat la ${now.toLocaleTimeString("ro-RO")}`;

  } catch (err) {
    // Nodul nu raspunde (oprit, sau inca pornind) -- aratam asta clar,
    // nu lasam bara de stare "inghetata" pe ultima valoare buna.
    elDot.classList.remove("synced", "syncing");
    elDot.classList.add("offline");
    elState.textContent = "NECONECTAT";
    elUpdated.textContent = `eroare: ${err.message}`;
  }
}

// ---------------------------------------------------------------- //
//  Populam dropdown-ul de expeditori cu portofelele gasite local     //
// ---------------------------------------------------------------- //
async function loadWalletNames() {
  try {
    const response = await fetch("/wallet/names");
    const data = await response.json();

    elTxSender.innerHTML = "";
    if (data.names.length === 0) {
      elTxSender.innerHTML = `<option value="">niciun portofel gasit</option>`;
      return;
    }

    data.names.forEach((name) => {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      elTxSender.appendChild(option);
    });
  } catch (err) {
    elTxSender.innerHTML = `<option value="">eroare la incarcare</option>`;
  }
}

// ---------------------------------------------------------------- //
//  Formular tranzactie -- semneaza pe server si trimite, intr-un pas //
// ---------------------------------------------------------------- //
elTxForm.addEventListener("submit", async (event) => {
  event.preventDefault(); // altfel browserul reincarca pagina la submit

  const payload = {
    sender_name: elTxForm.sender_name.value,
    receiver: elTxForm.receiver.value.trim(),
    amount: parseInt(elTxForm.amount.value, 10),
  };

  elTxResponse.className = "tx-response";
  elTxResponse.textContent = "Se semneaza si se trimite...";

  try {
    const response = await fetch("/wallet/sign-and-send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (response.ok) {
      elTxResponse.classList.add("tx-response-ok");
      elTxResponse.textContent = `${data.message} (mempool: ${data.mempool_size})`;
      elTxForm.reset();
    } else {
      elTxResponse.classList.add("tx-response-error");
      elTxResponse.textContent = data.error || `eroare HTTP ${response.status}`;
    }
  } catch (err) {
    elTxResponse.classList.add("tx-response-error");
    elTxResponse.textContent = `eroare de retea: ${err.message}`;
  }
});

loadWalletNames();

// ---------------------------------------------------------------- //
//  Panou peers -- rol (miner/relay) + accesibilitate, prin GET_INFO  //
// ---------------------------------------------------------------- //
const PEERS_REFRESH_INTERVAL_MS = 5000; // interval separat, mai rar --
// fiecare cerere aici asteapta pana la 2 secunde PER peer nereusit
// (vezi timeout-ul din get_peers_info), deci nu vrem sa se suprapuna
// cu bucla rapida de 2 secunde de mai sus (status + lant).

function renderPeer(peer) {
  const reachClass = peer.reachable ? "peer-reachable" : "";
  const roleClass = peer.role === "MINER" ? "peer-role-miner"
    : peer.role === "RELAY" ? "peer-role-relay"
    : "peer-role-unknown";
  const roleLabel = peer.role || "necunoscut";

  return `
    <div class="peer-item ${reachClass}">
      <span class="peer-dot"></span>
      <span class="peer-address">${peer.host}:${peer.p2p_port}</span>
      <span class="peer-role-badge ${roleClass}">${roleLabel}</span>
    </div>
  `;
}

async function refreshPeers() {
  try {
    const response = await fetch("/peers");
    const data = await response.json();

    if (data.peers.length === 0) {
      elPeersContainer.innerHTML = `<p class="placeholder">Niciun peer configurat la pornirea nodului.</p>`;
      return;
    }

    elPeersContainer.innerHTML = data.peers.map(renderPeer).join("");
  } catch (err) {
    elPeersContainer.innerHTML = `<p class="placeholder">Eroare la incarcarea peer-ilor: ${err.message}</p>`;
  }
}

refreshPeers();
setInterval(refreshPeers, PEERS_REFRESH_INTERVAL_MS);

// Prima citire imediat, apoi repetat la fiecare REFRESH_INTERVAL_MS.
function refreshAll() {
  refreshStatus();
  refreshChain();
}

refreshAll();
setInterval(refreshAll, REFRESH_INTERVAL_MS);