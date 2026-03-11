const { useState, useEffect, useMemo, useCallback, useRef } = React;

// ─── Sport display names & config ──────────────────────────────────────────────
const SPORT_NAMES = {
  mhockey: "Men's Hockey",
  whockey: "Women's Hockey",
  football: "Football",
  mbball: "Men's Basketball",
  wbball: "Women's Basketball",
  baseball: "Baseball",
  softball: "Softball",
  fhockey: "Field Hockey",
  wsoc: "Women's Soccer",
  mswim: "Men's Swimming",
  wswim: "Women's Swimming",
  mcross: "Men's Cross Country",
  wcross: "Women's Cross Country",
  mtrack: "Men's Track & Field",
  wtrack: "Women's Track & Field",
};

const PRIORITY_SPORTS = ["mhockey", "wbball", "mbball", "football"];

const HOCKEY_SPORTS = ["mhockey", "whockey"];

// ─── Date parsing ──────────────────────────────────────────────────────────────
// Dates come as "Oct 3 (Fri)", "Mar 13 (Fri)", etc.
// We need to figure out the year. The academic year spans Aug-Jul.
// Data was generated 2025-2026 season so Oct-Dec = 2025, Jan-Aug = 2026
function parseGameDate(dateStr) {
  if (!dateStr) return null;
  const match = dateStr.match(/^(\w+)\s+(\d+)/);
  if (!match) return null;
  const monthStr = match[1];
  const day = parseInt(match[2], 10);
  const months = {
    Jan: 0, Feb: 1, Mar: 2, Apr: 3, May: 4, Jun: 5,
    Jul: 6, Aug: 7, Sep: 8, Oct: 9, Nov: 10, Dec: 11,
  };
  const month = months[monthStr];
  if (month === undefined) return null;
  // Academic year: Aug-Dec = 2025, Jan-Jul = 2026
  const year = month >= 7 ? 2025 : 2026;
  return new Date(year, month, day);
}

function formatDate(dateStr) {
  const d = parseGameDate(dateStr);
  if (!d) return dateStr;
  return d.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function getToday() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate());
}

function isToday(dateStr) {
  const d = parseGameDate(dateStr);
  if (!d) return false;
  const today = getToday();
  return d.getTime() === today.getTime();
}

function isUpcoming(dateStr) {
  const d = parseGameDate(dateStr);
  if (!d) return false;
  return d.getTime() > getToday().getTime();
}

function isRecent(dateStr) {
  const d = parseGameDate(dateStr);
  if (!d) return false;
  return d.getTime() < getToday().getTime();
}

// ─── Result badge color ────────────────────────────────────────────────────────
function resultColor(result) {
  if (!result) return "bg-gray-100 text-gray-500";
  if (result.startsWith("W")) return "bg-green-100 text-green-800";
  if (result.startsWith("L")) return "bg-red-100 text-red-800";
  return "bg-yellow-100 text-yellow-800"; // Tie
}

// ─── H/A/N badge ──────────────────────────────────────────────────────────────
function haLabel(ha) {
  if (ha === "Home") return { text: "H", cls: "bg-blue-100 text-blue-700" };
  if (ha === "Away") return { text: "A", cls: "bg-orange-100 text-orange-700" };
  return { text: "N", cls: "bg-gray-100 text-gray-600" };
}

// ═══════════════════════════════════════════════════════════════════════════════
// HEADER
// ═══════════════════════════════════════════════════════════════════════════════
function Header() {
  return (
    <header className="bg-bdn-green text-white shadow-lg">
      <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
        <img
          src="https://i0.wp.com/bdn-data.s3.amazonaws.com/uploads/2024/09/Just_BDN_Square-180px.jpg?w=180&ssl=1"
          alt="Bangor Daily News"
          className="w-10 h-10 flex-shrink-0 rounded"
        />
        <div>
          <h1 className="font-heading text-2xl md:text-3xl font-bold tracking-wide">
            Maine Black Bears Sports
          </h1>
          <p className="text-xs text-green-200 tracking-wider uppercase">
            Bangor Daily News
          </p>
        </div>
      </div>
    </header>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// FEATURED GAMES
// ═══════════════════════════════════════════════════════════════════════════════
function FeaturedGames({ schedules }) {
  if (!schedules || !schedules.sports) return null;

  const cards = PRIORITY_SPORTS.map((sport) => {
    const data = schedules.sports[sport];
    if (!data) return null;
    const games = data.games || [];
    const gameIds = data.game_ids || [];

    // Find next upcoming game
    const upcomingIdx = games.findIndex((g) => !g.result);
    // Find most recent completed game
    const completedGames = games.filter((g) => g.result);
    const lastCompleted = completedGames.length > 0 ? completedGames[completedGames.length - 1] : null;

    const featured = upcomingIdx >= 0 ? games[upcomingIdx] : lastCompleted;
    if (!featured) return null;

    const isUpcomingGame = !featured.result;
    const record = data.record;

    return (
      <div
        key={sport}
        className="flex-shrink-0 w-64 bg-white rounded-lg shadow border border-gray-200 p-4 snap-start"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-bdn-green">
            {SPORT_NAMES[sport]}
          </span>
          {record && (
            <span className="text-xs text-gray-500">{record.overall}</span>
          )}
        </div>
        <p className="font-heading text-lg font-semibold text-gray-900 truncate">
          {featured.home_away === "Home" ? "vs" : "@"} {featured.opponent}
        </p>
        <p className="text-sm text-gray-500 mt-1">{formatDate(featured.date)}</p>
        <p className="text-sm text-gray-500">{featured.time}</p>
        <div className="mt-2">
          {isUpcomingGame ? (
            <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-bdn-gold text-bdn-green">
              Upcoming
            </span>
          ) : (
            <span
              className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${resultColor(featured.result)}`}
            >
              {featured.result}
            </span>
          )}
        </div>
      </div>
    );
  }).filter(Boolean);

  if (cards.length === 0) return null;

  return (
    <section className="max-w-6xl mx-auto px-4 py-6">
      <h2 className="font-heading text-lg font-semibold text-gray-800 mb-3 uppercase tracking-wide">
        Featured Games
      </h2>
      <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-thin snap-x">
        {cards}
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// NEWS STRIP
// ═══════════════════════════════════════════════════════════════════════════════
function NewsStrip({ news }) {
  if (!news || !news.articles || news.articles.length === 0) return null;

  return (
    <section className="max-w-6xl mx-auto px-4 py-4">
      <h2 className="font-heading text-lg font-semibold text-gray-800 mb-3 uppercase tracking-wide">
        Latest News
      </h2>
      <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-thin snap-x">
        {news.articles.slice(0, 12).map((article, i) => (
          <a
            key={i}
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 w-72 bg-white rounded-lg shadow border border-gray-200 overflow-hidden hover:shadow-md transition-shadow snap-start group"
          >
            {article.image && (
              <div className="h-36 overflow-hidden bg-gray-100">
                <img
                  src={article.image}
                  alt=""
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              </div>
            )}
            <div className="p-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-bdn-green">
                {article.sport}
              </span>
              <h3 className="font-heading text-sm font-semibold text-gray-900 mt-1 line-clamp-2">
                {article.title}
              </h3>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                {article.summary}
              </p>
            </div>
          </a>
        ))}
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB BAR + SPORT FILTER
// ═══════════════════════════════════════════════════════════════════════════════
const TABS = [
  { id: "scores", label: "Scores & Schedule" },
  { id: "standings", label: "Standings" },
  { id: "boxscores", label: "Box Scores" },
  { id: "rosters", label: "Rosters" },
];

function TabBar({ activeTab, onTabChange, sportFilter, onSportChange, availableSports }) {
  return (
    <div className="max-w-6xl mx-auto px-4">
      <div className="border-b border-gray-200">
        <nav className="flex gap-0 -mb-px overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`px-4 py-3 text-sm font-semibold whitespace-nowrap border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-bdn-green text-bdn-green"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="py-3">
        <select
          value={sportFilter}
          onChange={(e) => onSportChange(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-bdn-green focus:border-bdn-green"
        >
          <option value="all">All Sports</option>
          {availableSports.map((s) => (
            <option key={s} value={s}>
              {SPORT_NAMES[s] || s}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCORES TAB
// ═══════════════════════════════════════════════════════════════════════════════
function ScoresTab({ schedules, boxScores, sportFilter, onOpenBoxScore }) {
  if (!schedules || !schedules.sports) {
    return <div className="text-center py-8 text-gray-500">Loading schedule data...</div>;
  }

  // Build flat list of all games with sport + game_id
  const allGames = useMemo(() => {
    const games = [];
    const sports = sportFilter === "all"
      ? Object.keys(schedules.sports)
      : [sportFilter].filter((s) => schedules.sports[s]);

    sports.forEach((sport) => {
      const data = schedules.sports[sport];
      const gameIds = data.game_ids || [];
      (data.games || []).forEach((g, idx) => {
        games.push({
          ...g,
          sport,
          game_id: gameIds[idx] || null,
        });
      });
    });

    // Sort by date
    games.sort((a, b) => {
      const da = parseGameDate(a.date);
      const db = parseGameDate(b.date);
      if (!da || !db) return 0;
      return da.getTime() - db.getTime();
    });

    return games;
  }, [schedules, sportFilter]);

  // Group into Today, Upcoming, Recent
  const todayGames = allGames.filter((g) => isToday(g.date));
  const upcomingGames = allGames.filter((g) => isUpcoming(g.date));
  const recentGames = allGames
    .filter((g) => isRecent(g.date) && !isToday(g.date))
    .reverse(); // Most recent first

  // Check if a box score exists for a game
  function hasBoxScore(game) {
    if (!boxScores || !boxScores.games || !game.game_id) return false;
    const sportBoxes = boxScores.games[game.sport] || [];
    return sportBoxes.some((bs) => bs.game_id === game.game_id);
  }

  function getBoxScore(game) {
    if (!boxScores || !boxScores.games || !game.game_id) return null;
    const sportBoxes = boxScores.games[game.sport] || [];
    return sportBoxes.find((bs) => bs.game_id === game.game_id) || null;
  }

  function GameCard({ game }) {
    const ha = haLabel(game.home_away);
    const clickable = hasBoxScore(game);

    return (
      <div
        onClick={() => {
          if (clickable) onOpenBoxScore(getBoxScore(game));
        }}
        className={`bg-white rounded-lg border border-gray-200 p-4 ${
          clickable ? "cursor-pointer hover:shadow-md hover:border-bdn-green transition-all" : ""
        }`}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-bdn-green">
            {SPORT_NAMES[game.sport]}
          </span>
          <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${ha.cls}`}>
            {ha.text}
          </span>
        </div>
        <p className="font-heading text-base font-semibold text-gray-900">
          {game.home_away === "Home" ? "vs" : "@"} {game.opponent}
        </p>
        <p className="text-sm text-gray-500 mt-1">{formatDate(game.date)}</p>
        <div className="flex items-center justify-between mt-2">
          {game.result ? (
            <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${resultColor(game.result)}`}>
              {game.result}
            </span>
          ) : (
            <span className="text-sm text-gray-600 font-medium">{game.time}</span>
          )}
          {clickable && (
            <span className="text-xs text-bdn-green font-medium">Box Score &#8250;</span>
          )}
        </div>
        {game.location && (
          <p className="text-xs text-gray-400 mt-1 truncate">{game.location}</p>
        )}
      </div>
    );
  }

  function Section({ title, games, defaultShow = 8 }) {
    const [showAll, setShowAll] = useState(false);
    if (games.length === 0) return null;
    const displayed = showAll ? games : games.slice(0, defaultShow);

    return (
      <div className="mb-8">
        <h3 className="font-heading text-base font-semibold text-gray-700 uppercase tracking-wide mb-3">
          {title}
          <span className="text-gray-400 text-sm ml-2 normal-case">({games.length})</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {displayed.map((g, i) => (
            <GameCard key={`${g.sport}-${g.date}-${g.opponent}-${i}`} game={g} />
          ))}
        </div>
        {games.length > defaultShow && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="mt-3 text-sm text-bdn-green hover:underline font-medium"
          >
            {showAll ? "Show less" : `Show all ${games.length}`}
          </button>
        )}
      </div>
    );
  }

  return (
    <div>
      <Section title="Today" games={todayGames} />
      <Section title="Upcoming" games={upcomingGames} />
      <Section title="Recent Results" games={recentGames} />
      {todayGames.length === 0 && upcomingGames.length === 0 && recentGames.length === 0 && (
        <div className="text-center py-8 text-gray-500">No games found.</div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// STANDINGS TAB
// ═══════════════════════════════════════════════════════════════════════════════
function StandingsTab({ standings, sportFilter }) {
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState("asc");

  if (!standings || !standings.conferences) {
    return <div className="text-center py-8 text-gray-500">Loading standings data...</div>;
  }

  const confs = sportFilter === "all"
    ? Object.keys(standings.conferences)
    : [sportFilter].filter((s) => standings.conferences[s]);

  if (confs.length === 0) {
    return <div className="text-center py-8 text-gray-500">No standings available for this sport.</div>;
  }

  function handleSort(key) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function sortTeams(teams, isHockey) {
    if (!sortKey) return teams;
    return [...teams].sort((a, b) => {
      let va, vb;
      if (sortKey === "school") {
        va = a.school;
        vb = b.school;
        return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
      }
      // For hockey, drill into conference/overall objects
      if (isHockey) {
        if (sortKey === "rank") { va = a.rank; vb = b.rank; }
        else if (sortKey.startsWith("c_")) {
          va = a.conference[sortKey.slice(2)];
          vb = b.conference[sortKey.slice(2)];
        } else if (sortKey.startsWith("o_")) {
          va = a.overall[sortKey.slice(2)];
          vb = b.overall[sortKey.slice(2)];
        } else {
          va = a[sortKey]; vb = b[sortKey];
        }
      } else {
        // America East - flat strings
        if (sortKey === "pct" || sortKey === "conference_pct") {
          va = parseFloat(a[sortKey]) || 0;
          vb = parseFloat(b[sortKey]) || 0;
        } else {
          va = a[sortKey];
          vb = b[sortKey];
        }
      }
      if (typeof va === "number" && typeof vb === "number") {
        return sortDir === "asc" ? va - vb : vb - va;
      }
      if (typeof va === "string" && typeof vb === "string") {
        return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
      }
      return 0;
    });
  }

  function SortHeader({ label, col }) {
    const active = sortKey === col;
    return (
      <th
        onClick={() => handleSort(col)}
        className="px-3 py-2 text-xs font-semibold uppercase tracking-wider cursor-pointer hover:text-bdn-green select-none whitespace-nowrap"
      >
        {label}
        {active && (
          <span className="ml-1">{sortDir === "asc" ? "\u25B2" : "\u25BC"}</span>
        )}
      </th>
    );
  }

  function HockeyTable({ sport, teams }) {
    const sorted = sortTeams(teams, true);
    return (
      <div className="mb-8">
        <h3 className="font-heading text-base font-semibold text-gray-700 uppercase tracking-wide mb-3">
          {SPORT_NAMES[sport]} — Hockey East
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-100 text-gray-600 text-left">
              <tr>
                <SortHeader label="#" col="rank" />
                <SortHeader label="School" col="school" />
                <SortHeader label="GP" col="c_gp" />
                <SortHeader label="PTS" col="c_pts" />
                <SortHeader label="W" col="c_w" />
                <SortHeader label="L" col="c_l" />
                <SortHeader label="T" col="c_t" />
                <SortHeader label="OW" col="c_ow" />
                <SortHeader label="OL" col="c_ol" />
                <SortHeader label="GF" col="c_gf" />
                <SortHeader label="GA" col="c_ga" />
                <th className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-gray-400">|</th>
                <SortHeader label="GP" col="o_gp" />
                <SortHeader label="W" col="o_w" />
                <SortHeader label="L" col="o_l" />
                <SortHeader label="T" col="o_t" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sorted.map((t) => (
                <tr
                  key={t.school}
                  className={t.is_umaine ? "bg-green-50 border-l-4 border-l-bdn-green" : "hover:bg-gray-50"}
                >
                  <td className="px-3 py-2 font-medium">{t.rank}</td>
                  <td className={`px-3 py-2 font-semibold ${t.is_umaine ? "text-bdn-green" : ""}`}>
                    {t.school}
                  </td>
                  <td className="px-3 py-2">{t.conference.gp}</td>
                  <td className="px-3 py-2 font-bold">{t.conference.pts}</td>
                  <td className="px-3 py-2">{t.conference.w}</td>
                  <td className="px-3 py-2">{t.conference.l}</td>
                  <td className="px-3 py-2">{t.conference.t}</td>
                  <td className="px-3 py-2">{t.conference.ow}</td>
                  <td className="px-3 py-2">{t.conference.ol}</td>
                  <td className="px-3 py-2">{t.conference.gf}</td>
                  <td className="px-3 py-2">{t.conference.ga}</td>
                  <td className="px-3 py-2 text-gray-300">|</td>
                  <td className="px-3 py-2">{t.overall.gp}</td>
                  <td className="px-3 py-2">{t.overall.w}</td>
                  <td className="px-3 py-2">{t.overall.l}</td>
                  <td className="px-3 py-2">{t.overall.t}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  function AmericaEastTable({ sport, teams }) {
    const sorted = sortTeams(teams, false);
    return (
      <div className="mb-8">
        <h3 className="font-heading text-base font-semibold text-gray-700 uppercase tracking-wide mb-3">
          {SPORT_NAMES[sport]} — America East
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-100 text-gray-600 text-left">
              <tr>
                <SortHeader label="School" col="school" />
                <SortHeader label="Conference" col="conference" />
                <SortHeader label="Overall" col="overall" />
                <SortHeader label="Win %" col="conference_pct" />
                <SortHeader label="Streak" col="streak" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sorted.map((t) => (
                <tr
                  key={t.school}
                  className={t.is_umaine ? "bg-green-50 border-l-4 border-l-bdn-green" : "hover:bg-gray-50"}
                >
                  <td className={`px-3 py-2 font-semibold ${t.is_umaine ? "text-bdn-green" : ""}`}>
                    {t.school}
                  </td>
                  <td className="px-3 py-2">{t.conference}</td>
                  <td className="px-3 py-2">{t.overall}</td>
                  <td className="px-3 py-2">{t.conference_pct}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-semibold ${
                      t.streak && t.streak.startsWith("W")
                        ? "bg-green-100 text-green-800"
                        : t.streak && t.streak.startsWith("L")
                          ? "bg-red-100 text-red-800"
                          : "bg-gray-100 text-gray-600"
                    }`}>
                      {t.streak}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div>
      {confs.map((sport) => {
        const teams = standings.conferences[sport]?.teams || [];
        if (teams.length === 0) return null;
        const isHockey = HOCKEY_SPORTS.includes(sport);
        return isHockey
          ? <HockeyTable key={sport} sport={sport} teams={teams} />
          : <AmericaEastTable key={sport} sport={sport} teams={teams} />;
      })}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// BOX SCORE DETAIL (shared between tab and modal)
// ═══════════════════════════════════════════════════════════════════════════════
function BoxScoreDetail({ game }) {
  if (!game) return null;

  const home = game.home || {};
  const away = game.away || {};
  const allPeriods = home.periods || away.periods || [];

  return (
    <div>
      {/* Teams + score header */}
      <div className="flex items-center justify-between bg-bdn-green text-white rounded-t-lg px-4 py-3">
        <div className="text-center flex-1">
          <p className="font-heading text-lg font-bold">{away.name || "Away"}</p>
          <p className="text-xs text-green-200">{away.id} {away.record}</p>
        </div>
        <div className="text-center px-4">
          <p className="font-heading text-3xl font-bold">
            {away.score} - {home.score}
          </p>
          <p className="text-xs text-green-200 uppercase">
            {game.result_status === "W" ? "Win" : game.result_status === "L" ? "Loss" : game.result_status === "T" ? "Tie" : "Final"}
          </p>
        </div>
        <div className="text-center flex-1">
          <p className="font-heading text-lg font-bold">{home.name || "Home"}</p>
          <p className="text-xs text-green-200">{home.id} {home.record}</p>
        </div>
      </div>

      {/* Period-by-period */}
      {allPeriods.length > 0 && (
        <div className="overflow-x-auto border-x border-gray-200">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-semibold">Team</th>
                {allPeriods.map((p) => (
                  <th key={p.period} className="px-3 py-2 text-center text-xs font-semibold">
                    {p.period === "OT" || p.period === "OT1" || p.period === "OT2" ? p.period : `P${p.period}`}
                  </th>
                ))}
                <th className="px-3 py-2 text-center text-xs font-bold">T</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <tr>
                <td className="px-3 py-2 font-semibold">{away.name}</td>
                {(away.periods || []).map((p) => (
                  <td key={p.period} className="px-3 py-2 text-center">{p.score}</td>
                ))}
                <td className="px-3 py-2 text-center font-bold">{away.score}</td>
              </tr>
              <tr>
                <td className="px-3 py-2 font-semibold">{home.name}</td>
                {(home.periods || []).map((p) => (
                  <td key={p.period} className="px-3 py-2 text-center">{p.score}</td>
                ))}
                <td className="px-3 py-2 text-center font-bold">{home.score}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Leaders */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 border-x border-gray-200">
        {[away, home].map((team) => (
          <div key={team.name || team.id}>
            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
              {team.name} Leaders
            </h4>
            {(team.leaders || []).length > 0 ? (
              <div className="space-y-1">
                {team.leaders.map((l, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="text-gray-700">{l.name}</span>
                    <span className="text-gray-500">
                      {l.stat}: {l.value}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-400">No leaders data</p>
            )}
          </div>
        ))}
      </div>

      {/* Meta */}
      <div className="px-4 py-3 bg-gray-50 border border-gray-200 rounded-b-lg text-xs text-gray-500 space-y-1">
        {game.location && <p>Location: {game.location}</p>}
        {game.attendance && <p>Attendance: {game.attendance}</p>}
        {game.recap && game.recap.headline && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <p className="font-semibold text-gray-700 text-sm">{game.recap.headline}</p>
            {game.recap.teaser && (
              <p className="text-gray-500 mt-0.5">{game.recap.teaser}</p>
            )}
            {game.recap.url && (
              <a
                href={`https://goblackbears.com${game.recap.url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-bdn-green hover:underline font-medium mt-1 inline-block"
              >
                Read recap &#8250;
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// BOX SCORES TAB
// ═══════════════════════════════════════════════════════════════════════════════
function BoxScoresTab({ boxScores, sportFilter }) {
  const [expanded, setExpanded] = useState(null);

  if (!boxScores || !boxScores.games) {
    return <div className="text-center py-8 text-gray-500">Loading box score data...</div>;
  }

  const sports = sportFilter === "all"
    ? Object.keys(boxScores.games)
    : [sportFilter].filter((s) => boxScores.games[s]);

  // Flatten all box scores
  const allGames = [];
  sports.forEach((sport) => {
    (boxScores.games[sport] || []).forEach((g) => {
      allGames.push({ ...g, sport });
    });
  });

  // Sort by recap date desc, filter out ones without scores
  allGames.sort((a, b) => {
    const da = a.recap?.date ? new Date(a.recap.date) : new Date(0);
    const db = b.recap?.date ? new Date(b.recap.date) : new Date(0);
    return db.getTime() - da.getTime();
  });

  // Filter out games with no team data
  const validGames = allGames.filter((g) => g.home?.name || g.away?.name);

  if (validGames.length === 0) {
    return <div className="text-center py-8 text-gray-500">No box scores available.</div>;
  }

  return (
    <div className="space-y-3">
      {validGames.map((game) => {
        const key = game.game_id || `${game.sport}-${game.home?.name}-${game.away?.name}`;
        const isExpanded = expanded === key;
        const hasScores = game.home?.score && game.away?.score;

        return (
          <div key={key} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {/* Summary row */}
            <button
              onClick={() => setExpanded(isExpanded ? null : key)}
              className="w-full text-left px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-4 flex-1 min-w-0">
                <span className="text-xs font-semibold uppercase tracking-wider text-bdn-green flex-shrink-0">
                  {SPORT_NAMES[game.sport]}
                </span>
                {hasScores ? (
                  <span className="font-heading text-sm font-semibold text-gray-900 truncate">
                    {game.away?.name} {game.away?.score} @ {game.home?.name} {game.home?.score}
                  </span>
                ) : (
                  <span className="font-heading text-sm text-gray-500 truncate">
                    {game.away?.name || "TBD"} @ {game.home?.name || "TBD"}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 flex-shrink-0 ml-2">
                {game.result_status && (
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${resultColor(
                    game.result_status === "W" ? "W" : game.result_status === "L" ? "L" : "T"
                  )}`}>
                    {game.result_status}
                  </span>
                )}
                <svg
                  className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </button>

            {/* Expanded detail */}
            {isExpanded && (
              <div className="border-t border-gray-200">
                <BoxScoreDetail game={game} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// BOX SCORE MODAL
// ═══════════════════════════════════════════════════════════════════════════════
function BoxScoreModal({ game, onClose }) {
  const overlayRef = useRef(null);

  useEffect(() => {
    function handleEsc(e) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [onClose]);

  if (!game) return null;

  return (
    <div
      ref={overlayRef}
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
      className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4 overflow-y-auto"
    >
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Close button */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <h3 className="font-heading text-sm font-semibold uppercase tracking-wide text-gray-500">
            Box Score — {SPORT_NAMES[game.sport] || game.sport}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <BoxScoreDetail game={game} />
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// ROSTERS TAB
// ═══════════════════════════════════════════════════════════════════════════════
function RostersTab({ rosters, sportFilter }) {
  const [sortKey, setSortKey] = useState("number");
  const [sortDir, setSortDir] = useState("asc");

  if (!rosters || !rosters.sports) {
    return <div className="text-center py-8 text-gray-500">Loading roster data...</div>;
  }

  // If "all" is selected, default to first available sport
  const selectedSport = sportFilter === "all"
    ? Object.keys(rosters.sports)[0]
    : sportFilter;

  const players = rosters.sports[selectedSport] || [];

  if (players.length === 0) {
    return <div className="text-center py-8 text-gray-500">No roster available for this sport.</div>;
  }

  function handleSort(key) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  const sorted = useMemo(() => {
    return [...players].sort((a, b) => {
      let va = a[sortKey] || "";
      let vb = b[sortKey] || "";
      if (sortKey === "number") {
        va = parseInt(va, 10) || 9999;
        vb = parseInt(vb, 10) || 9999;
        return sortDir === "asc" ? va - vb : vb - va;
      }
      va = String(va);
      vb = String(vb);
      return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
    });
  }, [players, sortKey, sortDir]);

  function SortButton({ label, col }) {
    const active = sortKey === col;
    return (
      <button
        onClick={() => handleSort(col)}
        className={`text-xs px-2 py-1 rounded font-medium ${
          active
            ? "bg-bdn-green text-white"
            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
        }`}
      >
        {label}
        {active && <span className="ml-1">{sortDir === "asc" ? "\u25B2" : "\u25BC"}</span>}
      </button>
    );
  }

  function PlayerPlaceholder() {
    return (
      <svg viewBox="0 0 80 80" className="w-full h-full bg-gray-200" fill="none">
        <rect width="80" height="80" fill="#e5e7eb"/>
        <circle cx="40" cy="30" r="14" fill="#9ca3af"/>
        <ellipse cx="40" cy="72" rx="24" ry="20" fill="#9ca3af"/>
      </svg>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-heading text-base font-semibold text-gray-700 uppercase tracking-wide">
          {SPORT_NAMES[selectedSport]} Roster
          <span className="text-gray-400 text-sm ml-2 normal-case">({players.length} players)</span>
        </h3>
        <div className="flex gap-1">
          <SortButton label="#" col="number" />
          <SortButton label="Name" col="name" />
          <SortButton label="Pos" col="position" />
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {sorted.map((p) => (
          <div
            key={p.player_id}
            className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
          >
            <div className="aspect-square overflow-hidden bg-gray-100">
              {p.headshot ? (
                <img
                  src={`https://goblackbears.com${p.headshot}`}
                  alt={p.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling && (e.target.nextSibling.style.display = 'block');
                  }}
                />
              ) : null}
              {!p.headshot && <PlayerPlaceholder />}
            </div>
            <div className="p-2">
              <div className="flex items-baseline justify-between">
                <p className="font-heading text-sm font-semibold text-gray-900 truncate">
                  {p.name}
                </p>
                {p.number && (
                  <span className="text-xs font-bold text-bdn-green ml-1 flex-shrink-0">
                    #{p.number}
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-0.5">{p.position}</p>
              <div className="flex items-center justify-between mt-0.5">
                <span className="text-xs text-gray-400">{p.year}</span>
                <span className="text-xs text-gray-400 truncate ml-1">{p.hometown}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// FOOTER
// ═══════════════════════════════════════════════════════════════════════════════
function Footer({ lastUpdated }) {
  let formattedDate = "";
  if (lastUpdated) {
    try {
      const d = new Date(lastUpdated);
      formattedDate = d.toLocaleString("en-US", {
        weekday: "short",
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        timeZoneName: "short",
      });
    } catch (e) {
      formattedDate = lastUpdated;
    }
  }

  return (
    <footer className="border-t border-gray-200 mt-12 py-6 text-center text-xs text-gray-400">
      <p>
        Data via{" "}
        <a
          href="https://goblackbears.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-bdn-green hover:underline"
        >
          GoBlackBears.com
        </a>
        .
      </p>
      {formattedDate && <p className="mt-1">Last updated: {formattedDate}</p>}
    </footer>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// APP
// ═══════════════════════════════════════════════════════════════════════════════
function App() {
  const [schedules, setSchedules] = useState(null);
  const [standings, setStandings] = useState(null);
  const [boxScores, setBoxScores] = useState(null);
  const [news, setNews] = useState(null);
  const [rosters, setRosters] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("scores");
  const [sportFilter, setSportFilter] = useState("all");
  const [modalGame, setModalGame] = useState(null);

  useEffect(() => {
    Promise.allSettled([
      fetch("data/schedules.json").then((r) => r.json()),
      fetch("data/standings.json").then((r) => r.json()),
      fetch("data/box_scores.json").then((r) => r.json()),
      fetch("data/news.json").then((r) => r.json()),
      fetch("data/rosters.json").then((r) => r.json()),
    ]).then(([sched, stand, box, nws, rost]) => {
      if (sched.status === "fulfilled") setSchedules(sched.value);
      if (stand.status === "fulfilled") setStandings(stand.value);
      if (box.status === "fulfilled") setBoxScores(box.value);
      if (nws.status === "fulfilled") setNews(nws.value);
      if (rost.status === "fulfilled") setRosters(rost.value);
      setLoading(false);
    });
  }, []);

  // Build available sports from schedules (most complete list)
  const availableSports = useMemo(() => {
    const sportSet = new Set();
    if (schedules?.sports) Object.keys(schedules.sports).forEach((s) => sportSet.add(s));
    if (standings?.conferences) Object.keys(standings.conferences).forEach((s) => sportSet.add(s));
    if (boxScores?.games) Object.keys(boxScores.games).forEach((s) => sportSet.add(s));
    if (rosters?.sports) Object.keys(rosters.sports).forEach((s) => sportSet.add(s));
    // Order: priority sports first, then alphabetical
    const all = Array.from(sportSet);
    all.sort((a, b) => {
      const ai = PRIORITY_SPORTS.indexOf(a);
      const bi = PRIORITY_SPORTS.indexOf(b);
      if (ai >= 0 && bi >= 0) return ai - bi;
      if (ai >= 0) return -1;
      if (bi >= 0) return 1;
      return (SPORT_NAMES[a] || a).localeCompare(SPORT_NAMES[b] || b);
    });
    return all;
  }, [schedules, standings, boxScores, rosters]);

  const lastUpdated = schedules?.last_updated || standings?.last_updated || "";

  const handleOpenBoxScore = useCallback((game) => {
    if (game) setModalGame(game);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-bdn-green border-t-transparent mx-auto mb-3"></div>
          <p className="text-gray-500 text-sm">Loading Black Bears data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <FeaturedGames schedules={schedules} />
      <NewsStrip news={news} />

      <main className="flex-1 pb-8">
        <TabBar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          sportFilter={sportFilter}
          onSportChange={setSportFilter}
          availableSports={availableSports}
        />

        <div className="max-w-6xl mx-auto px-4 py-4">
          {activeTab === "scores" && (
            <ScoresTab
              schedules={schedules}
              boxScores={boxScores}
              sportFilter={sportFilter}
              onOpenBoxScore={handleOpenBoxScore}
            />
          )}
          {activeTab === "standings" && (
            <StandingsTab standings={standings} sportFilter={sportFilter} />
          )}
          {activeTab === "boxscores" && (
            <BoxScoresTab boxScores={boxScores} sportFilter={sportFilter} />
          )}
          {activeTab === "rosters" && (
            <RostersTab rosters={rosters} sportFilter={sportFilter} />
          )}
        </div>
      </main>

      <Footer lastUpdated={lastUpdated} />

      {modalGame && (
        <BoxScoreModal game={modalGame} onClose={() => setModalGame(null)} />
      )}
    </div>
  );
}

// Mount
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
