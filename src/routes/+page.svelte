<script>

  /**
     * @type {MediaRecorder}
     */
  let mediaRecorder;
  /**
     * @type {BlobPart[]}
     */
  let audioChunks = [];

  let isRecording = $state(false);
  let isUploading = $state(false);

  let transcript = $state("");
  /**
     * @type {string | any[]}
     */
  let table = $state([]);
  let error = $state("");

  async function startRecording() {
    error = "";
    transcript = "";
    table = [];
    audioChunks = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true
      });

      mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm"
      });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        await sendAudioToBackend();
      };

      mediaRecorder.start();
      isRecording = true;
    } catch (err) {
      if (err instanceof Error) {
        console.error(err);
      } else {
        console.error("Unknown error:", err);
      }
      error = "Microphone permission denied or not available.";
    }
  }

  function stopRecording() {
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
      return;
    }

    isRecording = false;
    mediaRecorder.stop();
  }

  async function sendAudioToBackend() {
    isUploading = true;
    error = "";

    try {
      const audioBlob = new Blob(audioChunks, {
        type: "audio/webm"
      });

      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      const response = await fetch("/api/transcribe", {
        method: "POST",
        body: formData
      });

      const result = await response.json();

      if (!response.ok || result.error) {
        throw new Error(result.error || "Transcription failed.");
      }

      transcript = result.transcript || "";
      table = result.table || [];
    } catch (err) {
      if (err instanceof Error) {
        error = err.message;
        console.error(err);
      } else {
        error = "Something went wrong.";
        console.error("Unknown error:", err);
      }
    } finally {
      isUploading = false;
    }
  }

  const teeth = Array.from({ length: 16 }, (_, i) => i + 1);

  const facialSites = ["MB", "B", "DB"];
  const lingualSites = ["ML", "L", "DL"];

  const rows = [
    "Plaque",
    "Calculus",
    "Probing",
    "Bleed/Supp",
    "Recession",
    "Attachment",
    "Furcation",
    "Mobility"
  ];

    /**
     * @type {Array<{site: number, value: number}>}
     */
  const spokenNumbers = $derived(Array.isArray(table) ? table.map((item, index) => ({
    site: index + 1,
    value: Number(item.number)
  })) : []);

  /**
   * @param {"facial" | "lingual"} surface
   * @param {number} toothIndex
   * @param {number} siteIndex
   */
  function getValue(surface, toothIndex, siteIndex) {
    // facial 16 teeth × 3 sites = first 48 numbers
    // lingual 16 teeth × 3 sites = next 48 numbers
    const surfaceOffset = surface === "facial" ? 0 : 48;
    const index = surfaceOffset + toothIndex * 3 + siteIndex;

    return spokenNumbers[index]?.value ?? "";
  }

  /**
   * @param {number | "" | null | undefined} value
   */
  function getPocketClass(value) {
    if (value === "" || value === null || value === undefined) return "";
    if (value <= 3) return "pocket-normal";
    if (value === 4) return "pocket-warning";
    return "pocket-danger";
  }

  /**
   * @param {"facial" | "lingual"} surface
   */
  function getLinePoints(surface) {
    /** @type {string[]} */
    const points = [];

    teeth.forEach((tooth, toothIndex) => {
      for (let siteIndex = 0; siteIndex < 3; siteIndex++) {
        const value = getValue(surface, toothIndex, siteIndex);

        if (typeof value === "number") {
          const x = toothIndex * 90 + siteIndex * 30 + 15;
          const y = 120 - Number(value) * 12;
          points.push(`${x},${y}`);
        }
      }
    });

    return points.join(" ");
  }
</script>

<svelte:head>
  <title>Persian Number Transcriber</title>
</svelte:head>

<main class="page">
  <section class="card">
    <h1>Persian Number Transcriber</h1>

    <p class="subtitle">
      Record Persian numbers from your microphone and convert them into a table.
    </p>

    <div class="controls">
      <button
        class="start"
        onclick={startRecording}
        disabled={isRecording || isUploading}
      >
        Start Recording
      </button>

      <button
        class="stop"
        onclick={stopRecording}
        disabled={!isRecording}
      >
        Stop & Transcribe
      </button>
    </div>

    {#if isRecording}
      <p class="status recording">Recording...</p>
    {:else if isUploading}
      <p class="status uploading">Uploading and transcribing...</p>
    {:else}
      <p class="status idle">Ready</p>
    {/if}

    {#if error}
      <div class="error">
        {error}
      </div>
    {/if}
  </section>

  <section class="card">
    <h2>Transcript</h2>

    <div class="transcript" dir="rtl">
      {transcript || "هنوز متنی ثبت نشده است"}
    </div>
  </section>

  <section class="card">
    <h2>Detected Numbers</h2>

    <table>
      <thead>
        <tr>
          <th>Row</th>
          <th>Spoken</th>
          <th>Number</th>
        </tr>
      </thead>

      <tbody>
        {#if table.length === 0}
          <tr>
            <td colspan="3">No numbers detected yet</td>
          </tr>
        {:else}
          {#each table as item}
            <tr>
              <td>{item.row}</td>
              <td dir="rtl">{item.spoken}</td>
              <td>{item.number}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </section>
  <section class="card perio-card">
    <h2>Periodontal Chart</h2>

    {#if spokenNumbers.length === 0}
      <p class="empty">No periodontal values yet</p>
    {:else}
      <div class="perio-scroll">
        <div class="perio-grid">

          <div class="side-label top-label">Facial</div>

          <div class="chart-area">
            <div class="tooth-header">
              {#each teeth as tooth}
                <div class="tooth-number">{tooth}</div>
              {/each}
            </div>

            <div class="surface-table">
              {#each rows as row}
                <div class="row-label">{row}</div>

                {#each teeth as tooth, toothIndex}
                  <div class="tooth-cell">
                    {#each facialSites as site, siteIndex}
                      {@const value = row === "Probing" ? getValue("facial", toothIndex, siteIndex) : ""}

                      <div
                        class="site-cell"
                        class:pocket-normal={getPocketClass(value) === "pocket-normal"}
                        class:pocket-warning={getPocketClass(value) === "pocket-warning"}
                        class:pocket-danger={getPocketClass(value) === "pocket-danger"}
                      >
                        {value}
                      </div>
                    {/each}
                  </div>
                {/each}
              {/each}
            </div>

            <div class="graph-box">
              <svg width="1440" height="130" viewBox="0 0 1440 130">
                {#each Array.from({ length: 7 }, (_, i) => i + 1) as level}
                  <line
                    x1="0"
                    x2="1440"
                    y1={120 - level * 12}
                    y2={120 - level * 12}
                    class="grid-line"
                  />
                {/each}

                {#each teeth as tooth, toothIndex}
                  <line
                    x1={toothIndex * 90}
                    x2={toothIndex * 90}
                    y1="0"
                    y2="130"
                    class="tooth-separator"
                  />
                {/each}

                <polyline
                  points={getLinePoints("facial")}
                  fill="none"
                  class="probing-line"
                />

                {#each teeth as tooth, toothIndex}
                  {#each facialSites as site, siteIndex}
                    {@const value = getValue("facial", toothIndex, siteIndex)}

                    {#if typeof(value) === "number"}
                      <circle
                        cx={toothIndex * 90 + siteIndex * 30 + 15}
                        cy={120 - Number(value) * 12}
                        r="4"
                        class="probing-dot"
                      />
                    {/if}
                  {/each}
                {/each}
              </svg>
            </div>
          </div>

          <div class="side-label">Lingual</div>

          <div class="chart-area">
            <div class="surface-table">
              {#each rows as row}
                <div class="row-label">{row}</div>

                {#each teeth as tooth, toothIndex}
                  <div class="tooth-cell">
                    {#each lingualSites as site, siteIndex}
                      {@const value = row === "Probing" ? getValue("lingual", toothIndex, siteIndex) : ""}

                      <div
                        class="site-cell"
                        class:pocket-normal={getPocketClass(value) === "pocket-normal"}
                        class:pocket-warning={getPocketClass(value) === "pocket-warning"}
                        class:pocket-danger={getPocketClass(value) === "pocket-danger"}
                      >
                        {value}
                      </div>
                    {/each}
                  </div>
                {/each}
              {/each}
            </div>

            <div class="graph-box">
              <svg width="1440" height="130" viewBox="0 0 1440 130">
                {#each Array.from({ length: 7 }, (_, i) => i + 1) as level}
                  <line
                    x1="0"
                    x2="1440"
                    y1={120 - level * 12}
                    y2={120 - level * 12}
                    class="grid-line"
                  />
                {/each}

                {#each teeth as tooth, toothIndex}
                  <line
                    x1={toothIndex * 90}
                    x2={toothIndex * 90}
                    y1="0"
                    y2="130"
                    class="tooth-separator"
                  />
                {/each}

                <polyline
                  points={getLinePoints("lingual")}
                  fill="none"
                  class="probing-line"
                />

                {#each teeth as tooth, toothIndex}
                  {#each lingualSites as site, siteIndex}
                    {@const value = getValue("lingual", toothIndex, siteIndex)}

                    {#if typeof(value) === "number"}
                      <circle
                        cx={toothIndex * 90 + siteIndex * 30 + 15}
                        cy={120 - Number(value) * 12}
                        r="4"
                        class="probing-dot"
                      />
                    {/if}
                  {/each}
                {/each}
              </svg>
            </div>
          </div>
        </div>
      </div>

      <p class="hint">
        First 48 spoken numbers fill facial probing depths. Next 48 fill lingual probing depths.
      </p>
    {/if}
  </section>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family:
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      "Segoe UI",
      sans-serif;
    background: #f3f4f6;
    color: #111827;
  }

  .page {
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 20px;
  }

  .card {
    background: white;
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  }

  h1 {
    margin: 0 0 8px;
    font-size: 32px;
  }

  h2 {
    margin-top: 0;
    font-size: 22px;
  }

  .subtitle {
    color: #6b7280;
    margin-bottom: 24px;
  }

  .controls {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  button {
    border: none;
    border-radius: 12px;
    padding: 12px 18px;
    font-size: 16px;
    cursor: pointer;
    color: white;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .start {
    background: #2563eb;
  }

  .stop {
    background: #dc2626;
  }

  .status {
    margin-top: 18px;
    font-weight: 600;
  }

  .recording {
    color: #dc2626;
  }

  .uploading {
    color: #d97706;
  }

  .idle {
    color: #16a34a;
  }

  .error {
    margin-top: 16px;
    background: #fee2e2;
    color: #991b1b;
    padding: 12px;
    border-radius: 12px;
  }

  .transcript {
    min-height: 60px;
    background: #f9fafb;
    border-radius: 12px;
    padding: 16px;
    font-size: 20px;
    text-align: right;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    overflow: hidden;
  }

  th,
  td {
    border: 1px solid #e5e7eb;
    padding: 12px;
    text-align: center;
  }

  th {
    background: #f9fafb;
    font-weight: 700;
  }

  td {
    background: white;
  }

  .perio-card {
    overflow: hidden;
  }

  .perio-scroll {
    overflow-x: auto;
    border: 1px solid #d1d5db;
    border-radius: 14px;
    background: #ffffff;
  }

  .perio-grid {
    min-width: 1540px;
    padding: 12px;
  }

  .side-label {
    width: 80px;
    font-weight: 800;
    font-size: 18px;
    color: #111827;
    margin: 18px 0 8px;
  }

  .top-label {
    margin-top: 0;
  }

  .chart-area {
    margin-bottom: 26px;
  }

  .tooth-header {
    display: grid;
    grid-template-columns: repeat(16, 90px);
    margin-left: 100px;
    border-top: 2px solid #111827;
    border-left: 2px solid #111827;
  }

  .tooth-number {
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-right: 2px solid #111827;
    border-bottom: 2px solid #111827;
    font-weight: 700;
    background: #f3f4f6;
  }

  .surface-table {
    display: grid;
    grid-template-columns: 100px repeat(16, 90px);
    border-left: 2px solid #111827;
    border-top: 2px solid #111827;
  }

  .row-label {
    height: 28px;
    padding-left: 8px;
    display: flex;
    align-items: center;
    border-right: 2px solid #111827;
    border-bottom: 1px solid #9ca3af;
    font-size: 13px;
    font-weight: 600;
    background: #dbeafe;
    color: #1e3a8a;
  }

  .tooth-cell {
    display: grid;
    grid-template-columns: repeat(3, 30px);
    height: 28px;
    border-right: 2px solid #111827;
    border-bottom: 1px solid #9ca3af;
  }

  .site-cell {
    display: flex;
    align-items: center;
    justify-content: center;
    border-right: 1px solid #d1d5db;
    font-size: 13px;
    font-weight: 700;
    color: #111827;
  }

  .site-cell:last-child {
    border-right: none;
  }

  .pocket-normal {
    color: #047857;
  }

  .pocket-warning {
    color: #d97706;
  }

  .pocket-danger {
    color: #dc2626;
  }

  .graph-box {
    margin-left: 100px;
    width: 1440px;
    height: 130px;
    border-left: 2px solid #111827;
    border-right: 2px solid #111827;
    border-bottom: 2px solid #111827;
    background: repeating-linear-gradient(
      to bottom,
      #ffffff 0,
      #ffffff 11px,
      #f3f4f6 12px
    );
  }

  .grid-line {
    stroke: #e5e7eb;
    stroke-width: 1;
  }

  .tooth-separator {
    stroke: #111827;
    stroke-width: 1.5;
    opacity: 0.55;
  }

  .probing-line {
    stroke: #111827;
    stroke-width: 3;
    stroke-linejoin: round;
    stroke-linecap: round;
  }

  .probing-dot {
    fill: #111827;
  }

  .hint {
    margin-top: 12px;
    font-size: 14px;
    color: #6b7280;
  }

  .empty {
    color: #6b7280;
  }
</style>