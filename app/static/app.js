"use strict";

const $ = (id) => document.getElementById(id);
const moodFields = ["energy", "valence", "tension", "density", "closure"];
const state = { songs: [], selected: new Set(), presets: [], editing: null, playlist: null,
  conversationId: null, activeSongId: null, initialized: false, catalog: null, profiles: new Map() };
const descriptions = {
  gentle_rise: "낮은 에너지에서 시작해 끝까지 완만하게 상승합니다.",
  mid_peak: "중반에 절정에 도달하고 후반에는 자연스럽게 내려옵니다.",
  late_explosion: "에너지를 서서히 쌓아 마지막 구간에서 폭발합니다.",
  calm_afterglow: "초중반에 고조된 뒤 잔잔한 여운으로 마무리합니다.",
  auto: "선택한 곡의 에너지 분포에 맞춰 목표 범위를 조정합니다. 아래 사전 미리보기는 보관함 전체 기준입니다."
};

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function notify(message, error = false) {
  $("notice").textContent = message;
  $("notice").classList.toggle("error", error);
}

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) {
    let detail = `요청 실패 (HTTP ${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
      if (body.errors) detail += " " + body.errors.map(e => `${e.field}: ${e.message}`).join(" / ");
    } catch { /* A non-JSON HTTP error is shown using its status. */ }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

async function action(button, work) {
  if (button.disabled) return;
  button.disabled = true;
  try { await work(); }
  catch (error) { notify(error.message || "요청을 처리할 수 없습니다.", true); }
  finally { button.disabled = false; }
}

async function refreshSongs() {
  const oldIds = new Set(state.songs.map(s => s.id));
  state.songs = await api("/api/songs");
  const newIds = new Set(state.songs.map(s => s.id));
  state.selected = new Set([...state.selected].filter(id => newIds.has(id)));
  for (const song of state.songs) if (!state.initialized || !oldIds.has(song.id)) state.selected.add(song.id);
  state.initialized = true;
  if (state.activeSongId && !newIds.has(state.activeSongId)) state.activeSongId = null;
  renderSongs();
  state.presets = await api("/api/presets");
  updateContext();
}

function renderSongs() {
  $("song-rows").replaceChildren();
  for (const song of state.songs) {
    const row = node("tr");
    const chooseCell = node("td");
    const checkbox = node("input"); checkbox.type = "checkbox"; checkbox.checked = state.selected.has(song.id);
    checkbox.setAttribute("aria-label", `${song.title} 선택`);
    checkbox.addEventListener("change", () => { if (checkbox.checked) state.selected.add(song.id); else state.selected.delete(song.id); updateSelection(); });
    chooseCell.append(checkbox); row.append(chooseCell);
    const titleCell = node("td", "song-name");
    titleCell.append(node("strong", "", song.title), node("small", "", `#${song.id} · ${song.artist}`)); row.append(titleCell);
    const playback = musicPlaybackLink(song);
    if (playback) { playback.className = "song-media-link"; titleCell.append(playback); }
    const findLink = node("button", "research-toggle", "링크 찾기"); findLink.type = "button";
    findLink.setAttribute("aria-label", `${song.title} 링크 찾기`); findLink.addEventListener("click", () => findSongLink(song)); titleCell.append(findLink);
    for (const field of moodFields) row.append(node("td", field === "energy" ? "energy-value" : "", song[field]));
    const controls = node("td");
    const edit = node("button", "manage", "편집"); edit.type = "button"; edit.setAttribute("aria-label", `${song.title} 편집`);
    edit.addEventListener("click", () => editSong(song));
    const remove = node("button", "manage", "삭제"); remove.type = "button"; remove.setAttribute("aria-label", `${song.title} 삭제`);
    remove.addEventListener("click", () => action(remove, async () => {
      if (!window.confirm(`‘${song.title}’을 보관함에서 삭제할까요? 기존 Playlist는 보존됩니다.`)) return;
      await api(`/api/songs/${song.id}`, { method: "DELETE" });
      if (state.editing === song.id) resetForm();
      await refreshSongs(); notify("곡을 삭제했습니다.");
    }));
    controls.append(edit, remove); row.append(controls); $("song-rows").append(row);
    const profile = song.artist === "King Gnu" ? state.profiles.get(song.title) : null;
    if (profile) {
      const detailRow = node("tr", "research-row"); detailRow.hidden = true; detailRow.id = `research-${song.id}`;
      const cell = node("td"); cell.colSpan = 8; cell.append(renderResearch(song, profile)); detailRow.append(cell);
      const toggle = node("button", "research-toggle", "장르·악기·근거"); toggle.type = "button";
      toggle.setAttribute("aria-label", `${song.title} 장르·악기·근거`);
      toggle.setAttribute("aria-expanded", "false"); toggle.setAttribute("aria-controls", detailRow.id);
      toggle.addEventListener("click", () => { detailRow.hidden = !detailRow.hidden; toggle.setAttribute("aria-expanded", String(!detailRow.hidden)); });
      titleCell.append(toggle); $("song-rows").append(detailRow);
    }
  }
  $("song-count").textContent = state.songs.length;
  $("empty-library").hidden = state.songs.length > 0;
  updateSelection();
}

function sourceLink(source, label = source.label) {
  const link = node("a", "", label);
  if (/^https:\/\//.test(source.url)) { link.href = source.url; link.target = "_blank"; link.rel = "noopener noreferrer"; }
  return link;
}

function renderResearch(song, profile) {
  const box = node("div", "research-content");
  box.append(node("strong", "", `${song.title} · 초깃값 근거`));
  box.append(node("p", "", `장르·스타일: ${profile.genre_tags.join(" · ")} (자료를 해석한 태그)`));
  box.append(node("p", "", `확인된 악기·음색: ${profile.instruments.join(" · ") || "곡 단위로 확인한 악기 자료 없음"}`));
  box.append(node("p", "muted", profile.instrument_scope));
  box.append(node("p", "", profile.evidence_note));
  const stats = profile.stats;
  box.append(node("p", "", `수집한 공연 중 ${stats.concert_count}개에 등장 · 오프닝 ${stats.opening_count}회 · 본편 마지막 ${stats.main_closing_count}회 · 공연 마지막 ${stats.show_closing_count}회 · 앙코르 ${stats.encore_count}회`));
  box.append(node("p", "", `배치 반영 초깃값 (에너지 / 밝기 / 긴장 / 밀도 / 마무리): ${moodFields.map(f => profile.ratings[f]).join(" / ")}`));
  box.append(node("p", "muted", `음악 자료 기반 수작업 값: ${moodFields.map(f => profile.base_ratings[f]).join(" / ")} → 에너지는 음악 85% + 배치 15%, 마무리는 음악 55% + 종료 배치 45%로 보정합니다.`));
  if (moodFields.some(f => song[f] !== profile.ratings[f])) box.append(node("p", "research-edited", "현재 보관함 수치는 초깃값에서 수정된 상태입니다. 위 자료는 원래 초깃값의 근거입니다."));
  const links = node("div", "research-sources");
  for (const id of profile.source_ids) links.append(sourceLink(state.catalog.sources[id]));
  box.append(links);
  const positions = node("details"); positions.append(node("summary", "", "공연별 배치와 세트리스트 출처"));
  const list = node("ul");
  for (const visit of profile.occurrences) {
    const show = state.catalog.concerts.find(c => c.id === visit.concert_id);
    const section = { main: "본편", encore: "앙코르", double_encore: "더블 앙코르" }[visit.section];
    const item = node("li");
    item.append(sourceLink(show.sources[0], `${show.date} · ${show.name}`));
    item.append(node("span", "", ` — ${section} ${visit.section_position}/${visit.section_song_count} · 전체 ${visit.position}/${visit.song_count}`));
    list.append(item);
  }
  positions.append(list, node("p", "muted", "순번은 연결 트랙·게스트 곡을 제외한 선정 곡 기준입니다. 공연별 종료는 본편·앙코르를 구분합니다."));
  box.append(positions);
  return box;
}

function updateSelection() {
  $("selection-count").textContent = `${state.selected.size}곡 선택 · 최대 50곡`;
  $("select-all").checked = state.songs.length > 0 && state.selected.size === state.songs.length;
  $("select-all").indeterminate = state.selected.size > 0 && state.selected.size < state.songs.length;
}

function editSong(song) {
  $("selected-music-help").hidden = true;
  state.editing = song.id; state.activeSongId = song.id;
  $("song-form").hidden = false; $("toggle-form").setAttribute("aria-expanded", "true");
  for (const key of ["title", "artist", ...moodFields, "media_uri"]) $("song-form").elements.namedItem(key).value = song[key] ?? "";
  $("form-title").textContent = `곡 #${song.id} 편집`; $("save-song").textContent = "수정 저장"; $("cancel-edit").hidden = false;
  updateContext(); $("song-form").scrollIntoView({ behavior: "smooth", block: "center" });
}

function resetForm() {
  $("selected-music-help").hidden = true;
  state.editing = null; $("song-form").reset(); $("form-title").textContent = "새 곡 등록";
  $("save-song").textContent = "곡 등록"; $("cancel-edit").hidden = true;
}

function svgNode(tag, attrs, text) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attrs)) element.setAttribute(key, String(value));
  if (text !== undefined) element.textContent = text;
  return element;
}

function drawCurve(targets, actual = []) {
  const svg = $("curve-chart"); svg.replaceChildren();
  const x = (i, n) => 38 + (n > 1 ? i / (n - 1) : .5) * 420;
  const y = (v) => 180 - v * 1.5;
  for (const tick of [0, 25, 50, 75, 100]) {
    svg.append(svgNode("line", { x1: 38, y1: y(tick), x2: 458, y2: y(tick), stroke: "#dce5df", "stroke-dasharray": "3 5" }));
    svg.append(svgNode("text", { x: 28, y: y(tick) + 4, "text-anchor": "end", fill: "#78877e", "font-size": 10 }, tick));
  }
  svg.append(svgNode("text", { x: 38, y: 205, fill: "#78877e", "font-size": 11 }, "시작"), svgNode("text", { x: 458, y: 205, "text-anchor": "end", fill: "#78877e", "font-size": 11 }, "마무리"));
  for (const [values, color, dashed] of [[targets, "#167e7c", true], [actual, "#ec754c", false]]) {
    if (!values.length) continue;
    const points = values.map((v, i) => `${x(i, values.length)},${y(v)}`).join(" ");
    svg.append(svgNode("polyline", { points, fill: "none", stroke: color, "stroke-width": 2.7, "stroke-linejoin": "round", "stroke-dasharray": dashed ? "5 4" : "none" }));
    if (!dashed || values.length === 1) values.forEach((value, index) => {
      const circle = svgNode("circle", { cx: x(index, values.length), cy: y(value), r: 4, fill: color, stroke: "white", "stroke-width": 1.5 });
      circle.append(svgNode("title", {}, `${index + 1}번째 · 에너지 ${value}`)); svg.append(circle);
    });
  }
}

function previewPreset() {
  const preset = $("preset").value;
  $("preset-description").textContent = descriptions[preset];
  $("chart-title").textContent = "목표 에너지 미리보기";
  drawCurve(state.presets.find(p => p.id === preset)?.targets || []);
}

function renderPlaylist(playlist) {
  state.playlist = playlist;
  $("playlist-title").textContent = playlist.name;
  $("playlist-meta").textContent = `#${playlist.id} · ${playlist.preset} · ${playlist.items.length}곡`;
  $("chart-title").textContent = "생성 결과 · 목표와 실제 에너지";
  drawCurve(playlist.items.map(i => i.target_energy), playlist.items.map(i => i.actual_energy));
  $("playlist-summary").replaceChildren(node("strong", "score-number", `${playlist.fit_score}`), node("span", "", `적합도 / 100 · 비용 ${playlist.cost.toFixed(2)}\n${playlist.summary}`));
  $("playlist-items").replaceChildren();
  for (const item of playlist.items) {
    const row = node("li", "playlist-item"); row.append(node("span", "track-number", String(item.position).padStart(2, "0")));
    const content = node("div", "track-content"); const heading = node("div", "track-heading");
    heading.append(node("strong", "", item.song.title), node("span", `role ${item.role === "절정" ? "peak" : ""}`, item.role));
    content.append(heading, node("p", "track-meta", `${item.song.artist} · 목표 ${item.target_energy.toFixed(1)} / 실제 ${item.actual_energy}`), node("p", "track-reason", item.transition_reason));
    const playback = musicPlaybackLink(item.song);
    if (playback) { playback.className = "song-media-link"; content.append(playback); }
    const details = node("details", "penalties"); details.append(node("summary", "", "점수 구성 확인"), node("pre", "", JSON.stringify(item.penalties, null, 2)));
    content.append(details); row.append(content); $("playlist-items").append(row);
  }
  $("export-json").disabled = false; $("export-m3u").disabled = false;
  $("saved-playlists").value = String(playlist.id);
  updateContext();
}

async function refreshPlaylists() {
  const playlists = await api("/api/playlists");
  $("saved-playlists").replaceChildren(node("option", "", "저장된 결과 선택")); $("saved-playlists").firstChild.value = "";
  for (const playlist of playlists) { const option = node("option", "", `#${playlist.id} ${playlist.name} · ${playlist.preset}`); option.value = playlist.id; $("saved-playlists").append(option); }
  if (state.playlist) $("saved-playlists").value = state.playlist.id;
}

function traceCard(trace, expanded = false) {
  const card = node("div", `tool-card ${trace.success ? "" : "tool-failed"}`);
  const head = node("div", "tool-head"); head.append(node("span", "tool-name", trace.tool_name), node("span", "muted", `${trace.success ? "성공" : "실패"} · ${new Date(trace.created_at).toLocaleTimeString("ko-KR")}`));
  card.append(head, node("p", "", trace.result_summary));
  const details = node("details"); details.open = expanded;
  details.append(node("summary", "", "Arguments와 요청 보기"), node("p", "muted", trace.user_request), node("pre", "", JSON.stringify(trace.arguments, null, 2)));
  card.append(details); return card;
}

async function refreshLogs() {
  const logs = await api("/api/tool-logs?limit=30"); $("tool-logs").replaceChildren();
  if (!logs.length) $("tool-logs").append(node("p", "empty", "아직 Agent Tool 실행 기록이 없습니다."));
  for (const trace of logs) $("tool-logs").append(traceCard(trace));
}

function addMessage(role, message) {
  $("chat-messages").querySelector(".empty")?.remove();
  const element = node("div", `message ${role}`);
  element.append(node("span", "speaker", role === "user" ? "YOU" : "SETFLOW AGENT"), document.createTextNode(message));
  $("chat-messages").append(element); $("chat-messages").scrollTop = $("chat-messages").scrollHeight;
}

function updateContext() {
  $("chat-context").textContent = `대화 대상 · 곡 ${state.activeSongId ? "#" + state.activeSongId : "미지정"} / Playlist ${state.playlist ? "#" + state.playlist.id : "미지정"} · 자연어 생성에서 곡 ID를 생략하면 보관함 전체를 사용합니다.`;
}

async function download(format) {
  if (!state.playlist) return;
  const response = await fetch(`/api/playlists/${state.playlist.id}/export`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ format }) });
  if (!response.ok) throw new Error("Export에 실패했습니다.");
  await response.arrayBuffer();
  const link = node("a"); link.href = `/api/playlists/${state.playlist.id}/download?format=${format}`;
  link.download = `playlist-${state.playlist.id}.${format}`; document.body.append(link); link.click(); link.remove();
  notify(response.headers.get("X-SetFlow-Missing-Media") === "true" ? "M3U 다운로드를 요청했습니다. 재생 위치가 없는 곡은 주석으로 기록되며 재생되지 않습니다. media_uri를 입력한 뒤 Playlist를 다시 생성하세요." : `${format.toUpperCase()} 다운로드를 요청했습니다.`);
  if (response.headers.get("X-SetFlow-Webpage-Links") === "true") notify(`${$("notice").textContent} YouTube 링크는 웹페이지이므로 일반 M3U 플레이어에서 재생되지 않을 수 있으며, 계정 재생목록에는 자동 저장되지 않습니다.`);
}

$("toggle-form").addEventListener("click", () => { $("song-form").hidden = !$("song-form").hidden; $("toggle-form").setAttribute("aria-expanded", String(!$("song-form").hidden)); });
setupMusicSearch();
const searchPrompt = node("button", "", "YouTube 곡 찾기"); searchPrompt.type = "button";
searchPrompt.dataset.prompt = "유튜브에서 King Gnu 白日 검색해줘.";
document.querySelector(".example-prompts").append(searchPrompt);
$("cancel-edit").addEventListener("click", resetForm);
$("select-all").addEventListener("change", () => { state.selected = $("select-all").checked ? new Set(state.songs.map(s => s.id)) : new Set(); renderSongs(); });
$("preset").addEventListener("change", previewPreset);
$("seed-button").addEventListener("click", () => action($("seed-button"), async () => { const result = await api("/api/sample-data", { method: "POST" }); await refreshSongs(); previewPreset(); notify(`${result.added}곡 추가 · ${result.notice}`); }));
$("song-form").addEventListener("submit", (event) => { event.preventDefault(); action($("save-song"), async () => {
  const data = Object.fromEntries(new FormData(event.target));
  for (const field of moodFields) data[field] = Number(data[field]);
  if (!state.editing && !data.media_uri) data.media_uri = null;
  const result = await api(state.editing ? `/api/songs/${state.editing}` : "/api/songs", { method: state.editing ? "PATCH" : "POST", body: JSON.stringify(data) });
  state.activeSongId = result.id; resetForm(); await refreshSongs(); notify(`곡 #${result.id} ‘${result.title}’을 저장했습니다.`);
}); });
$("playlist-form").addEventListener("submit", (event) => { event.preventDefault(); action($("generate-button"), async () => {
  if (!state.selected.size) throw new Error("곡을 하나 이상 선택하세요.");
  const result = await api("/api/playlists/generate", { method: "POST", body: JSON.stringify({ song_ids: [...state.selected], preset: $("preset").value, name: $("playlist-name").value }) });
  await refreshPlaylists(); renderPlaylist(result); notify("Playlist를 생성했습니다. 각 곡의 역할과 전환 이유를 확인하세요.");
}); });
$("saved-playlists").addEventListener("change", () => { if (!$("saved-playlists").value) return; action($("saved-playlists"), async () => renderPlaylist(await api(`/api/playlists/${$("saved-playlists").value}`))); });
$("export-json").addEventListener("click", () => action($("export-json"), () => download("json")));
$("export-m3u").addEventListener("click", () => action($("export-m3u"), () => download("m3u")));
$("refresh-logs").addEventListener("click", () => action($("refresh-logs"), refreshLogs));
document.querySelectorAll("[data-prompt]").forEach(button => button.addEventListener("click", () => { $("chat-input").value = button.dataset.prompt; $("chat-input").focus(); }));
$("new-chat").addEventListener("click", () => { state.conversationId = null; state.activeSongId = null; $("chat-messages").replaceChildren(); $("selected-tools").replaceChildren(); updateContext(); notify("새 대화를 시작합니다. 화면에 열린 Playlist는 대화 대상으로 유지됩니다."); });
$("chat-form").addEventListener("submit", (event) => { event.preventDefault(); action($("chat-send"), async () => {
  const message = $("chat-input").value.trim(); if (!message) return;
  addMessage("user", message); $("chat-input").value = "";
  let reply;
  try { reply = await api("/api/agent/chat", { method: "POST", body: JSON.stringify({ message, conversation_id: state.conversationId, playlist_id: state.playlist?.id ?? null, song_id: state.activeSongId }) }); }
  catch (error) { addMessage("assistant", error.message); throw error; }
  state.conversationId = reply.conversation_id; state.activeSongId = reply.song_id;
  addMessage("assistant", reply.message); $("selected-tools").replaceChildren();
  for (const trace of reply.tool_calls) {
    $("selected-tools").append(traceCard(trace, true));
    if (trace.tool_name === "search_music" && trace.success) {
      state.searchTarget = null; $("music-query").value = trace.result.query;
      renderMusicResults(trace.result); $("music-search-results").scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }
  if (reply.download_url && /^\/api\/playlists\/\d+\/download\?format=(json|m3u)$/.test(reply.download_url)) {
    const link = node("a", "download-link", "생성된 파일 다운로드 ↓"); link.href = reply.download_url; link.download = ""; $("selected-tools").append(link);
  }
  await refreshSongs(); await refreshPlaylists(); await refreshLogs();
  if (reply.playlist_id) renderPlaylist(await api(`/api/playlists/${reply.playlist_id}`));
  notify(reply.needs_input ? "Agent가 추가 입력 또는 설정 확인을 요청했습니다." : "Agent 요청을 처리했습니다. 선택된 Tool과 Arguments를 확인하세요.");
}); });

async function initialize() {
  try {
    const health = await api("/health"); $("server-status").textContent = "● 서버 정상";
    $("public-demo-notice").hidden = !health.public_demo;
    $("mode").textContent = health.mode === "demo" ? "Demo Mode" : "OpenAI Mode";
    $("mode").classList.toggle("demo", health.mode === "demo");
    if (!health.agent_ready) notify("OPENAI_MODEL이 비어 있습니다. 일반 기능은 사용 가능하며, Agent를 사용하려면 .env 설정 후 재시작하세요.", true);
    try {
      state.catalog = await api("/api/catalog/king-gnu");
      state.profiles = new Map(state.catalog.profiles.map(p => [p.title, p]));
    } catch { notify("곡별 근거 자료를 불러오지 못했습니다. 보관함 기능은 계속 사용할 수 있습니다.", true); }
    await refreshSongs(); await refreshPlaylists(); await refreshLogs(); previewPreset();
  } catch (error) { $("server-status").textContent = "서버 연결 실패"; $("server-status").classList.add("error"); notify(error.message, true); }
}
initialize();
