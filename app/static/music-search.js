"use strict";

function musicKey(value) { return String(value || "").normalize("NFKC").trim().toLocaleLowerCase().replace(/\s+/g, " "); }

function musicDraft(result, songs, profiles, targetId = null) {
  const matches = songs.filter(song => targetId ? song.id === targetId :
    (musicKey(song.title) === musicKey(result.title) && musicKey(song.artist) === musicKey(result.artist)) ||
    (!result.artist && musicKey(`${song.artist} - ${song.title}`) === musicKey(result.title)) ||
    (Boolean(result.media_uri) && song.media_uri === result.media_uri));
  const existing = matches.length === 1 ? matches[0] : null;
  if (targetId && !existing) throw new Error("연결할 곡이 보관함에서 사라졌습니다. 다시 검색하세요.");
  if (matches.length > 1) throw new Error("같은 곡이 여러 개 있습니다. 보관함에서 원하는 곡의 ‘링크 찾기’를 누르세요.");
  if (existing) return { existing, values: { ...existing, media_uri: result.media_uri }, profile: false };
  const profile = musicKey(result.artist) === "king gnu" ? profiles.get(result.title) : null;
  return { existing: null, profile: Boolean(profile), values: {
    title: result.title, artist: profile ? "King Gnu" : result.artist, media_uri: result.media_uri,
    ...(profile ? profile.ratings : {})
  } };
}

function isYouTubeUrl(value) {
  return /^https:\/\/(?:www\.youtube\.com|music\.youtube\.com)\/watch\?v=[A-Za-z0-9_-]{11}$/.test(value || "");
}

function musicPlaybackLink(song) {
  if (!isYouTubeUrl(song.media_uri)) return null;
  return sourceLink({ url: song.media_uri }, song.media_uri.includes("music.youtube.com") ? "YouTube Music 열기 ↗" : "YouTube 열기 ↗");
}

function updateMusicSearchLinks(query) {
  const encoded = encodeURIComponent(query.trim());
  $("open-youtube-search").href = `https://www.youtube.com/results?search_query=${encoded}`;
  $("open-music-search").href = `https://music.youtube.com/search?q=${encoded}`;
}

async function chooseMusic(result, button, targetId) {
  await action(button, async () => {
    await refreshSongs();
    const draft = musicDraft(result, state.songs, state.profiles, targetId);
    if (draft.existing) editSong(draft.existing);
    else {
      resetForm(); $("song-form").hidden = false; $("toggle-form").setAttribute("aria-expanded", "true");
    }
    for (const key of ["title", "artist", ...moodFields, "media_uri"]) {
      $("song-form").elements.namedItem(key).value = draft.values[key] ?? "";
    }
    const help = draft.existing ? `보관함의 ‘${draft.existing.title}’에 링크를 연결합니다. 기존 분위기 수치는 유지됩니다. 확인 후 ‘수정 저장’을 누르세요.` :
      draft.profile ? "King Gnu 조사 초깃값을 채웠습니다. 곡과 수치를 확인한 뒤 ‘곡 등록’을 누르세요." :
      "곡 제목과 아티스트를 확인하고 다섯 분위기 수치를 입력하세요. 영상의 업로더는 아티스트와 다를 수 있어 자동 입력하지 않습니다.";
    $("selected-music-help").textContent = `${help} 선택한 영상: ${result.title}. 웹페이지 링크는 계정 재생목록에 자동 저장되지 않습니다.`;
    $("selected-music-help").hidden = false;
    notify(help); $("song-form").scrollIntoView({ behavior: "smooth", block: "center" });
    $("song-form").elements.namedItem(draft.existing ? "media_uri" : "title").focus({ preventScroll: true });
  });
}

function renderMusicResults(response, targetId = null) {
  const container = $("music-search-results"); container.replaceChildren();
  const results = Array.isArray(response.results) ? response.results : [];
  updateMusicSearchLinks(response.query || $("music-query").value);
  $("music-search-status").textContent = results.length ?
    `${response.source} · ${results.length}개 결과${targetId ? " · 기존 곡에 연결할 영상을 선택하세요." : " · 제목과 버전을 확인하고 선택하세요."}` :
    "검색 결과가 없습니다. 다른 곡명으로 검색하거나 아래의 YouTube 검색을 여세요.";
  for (const result of results) {
    const row = node("article", "music-result");
    if (/^[A-Za-z0-9_-]{11}$/.test(result.video_id)) {
      const thumbnail = node("img"); thumbnail.src = `https://i.ytimg.com/vi/${result.video_id}/default.jpg`;
      thumbnail.alt = ""; thumbnail.loading = "lazy"; thumbnail.referrerPolicy = "no-referrer"; row.append(thumbnail);
    }
    const content = node("div", "music-result-info"); content.append(node("strong", "", result.title));
    content.append(node("p", "", [result.artist || `채널: ${result.channel || "정보 없음"}`, result.album, result.duration].filter(Boolean).join(" · ")));
    const controls = node("div", "music-result-actions");
    const select = node("button", "secondary", targetId ? "이 영상 연결" : "이 곡 선택"); select.type = "button";
    select.setAttribute("aria-label", `${result.title} 선택`); select.disabled = !isYouTubeUrl(result.media_uri);
    select.addEventListener("click", () => chooseMusic(result, select, targetId)); controls.append(select);
    if (isYouTubeUrl(result.youtube_url)) controls.append(sourceLink({ url: result.youtube_url }, "YouTube 열기 ↗"));
    if (isYouTubeUrl(result.media_uri) && result.source === "YouTube Music") controls.append(sourceLink({ url: result.media_uri }, "YouTube Music 열기 ↗"));
    content.append(controls); row.append(content); container.append(row);
  }
}

function setupMusicSearch() {
  state.searchTarget = null;
  $("music-query").addEventListener("input", () => { state.searchTarget = null; updateMusicSearchLinks($("music-query").value); });
  $("music-search-form").addEventListener("submit", event => {
    event.preventDefault();
    action($("music-search-button"), async () => {
      const query = $("music-query").value.trim(); if (!query) throw new Error("검색어를 입력하세요.");
      const targetId = state.searchTarget;
      updateMusicSearchLinks(query); $("music-search-results").replaceChildren();
      $("music-search-status").textContent = "YouTube에서 검색 중입니다…";
      $("music-search-results").setAttribute("aria-busy", "true");
      try {
        const response = await api(`/api/music/search?query=${encodeURIComponent(query)}&kind=${$("music-kind").value}&limit=8`);
        renderMusicResults(response, targetId);
      } catch (error) { $("music-search-status").textContent = error.message; throw error; }
      finally { $("music-search-results").setAttribute("aria-busy", "false"); }
    });
  });
}

function findSongLink(song) {
  if ($("music-search-button").disabled) { notify("현재 검색이 끝난 뒤 다시 눌러주세요."); return; }
  state.searchTarget = song.id; $("music-query").value = `${song.artist} ${song.title}`;
  $("music-search-form").requestSubmit();
  $("music-search-form").scrollIntoView({ behavior: "smooth", block: "center" });
}
