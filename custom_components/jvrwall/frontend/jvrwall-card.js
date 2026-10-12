/* JVRWall wall-tablet card. Tabs: Meals, Shopping, Chores, Calendar. */
const DAYS = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"];
const SLOTS = ["breakfast","lunch","dinner"];
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

class JVRWallCard extends HTMLElement {
  setConfig(config) {
    this._config = {
      meals: "sensor.jvrwall_meal_plan",
      shopping: "sensor.jvrwall_shopping_list",
      chores: "sensor.jvrwall_chores",
      recipes: "sensor.jvrwall_recipes",
      calendars_sensor: "sensor.jvrwall_family_calendars",
      calendars: null,
      ...config,
    };
    this._tab = this._tab || "meals";
    this._events = [];
    this._calKey = "";
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    this._hass = hass;
    const key = ["meals","shopping","chores","recipes"].map((k) => {
      const s = hass.states[this._config[k]]; return s ? s.last_updated : "";
    }).join("|");
    if (key !== this._key) { this._key = key; this._render(); }
    if (this._tab === "calendar") this._loadEvents();
  }

  getCardSize() { return 8; }

  _attrs(k) { const s = this._hass.states[this._config[k]]; return s ? s.attributes : {}; }

  _call(service, data) { return this._hass.callService("jvrwall", service, data); }

  async _loadEvents() {
    const cals = this._config.calendars ||
      (this._hass.states[this._config.calendars_sensor]?.attributes.calendars) || [];
    const now = Date.now();
    if (this._lastLoad && now - this._lastLoad < 60000 && this._calKey === cals.join()) return;
    this._lastLoad = now; this._calKey = cals.join();
    const start = new Date(); start.setHours(0,0,0,0);
    const end = new Date(start.getTime() + 14 * 864e5);
    const all = [];
    for (const cal of cals) {
      try {
        const evs = await this._hass.callApi("GET",
          `calendars/${cal}?start=${start.toISOString()}&end=${end.toISOString()}`);
        evs.forEach((e) => all.push({ ...e, calendar: cal }));
      } catch (err) { console.warn("JVRWall: calendar load failed", cal, err); }
    }
    const t = (e) => new Date(e.start.dateTime || e.start.date || e.start).getTime();
    all.sort((a, b) => t(a) - t(b));
    this._events = all; this._render();
  }

  _fmt(e) {
    const s = e.start.dateTime || e.start.date || e.start;
    const d = new Date(s);
    const day = d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
    return e.start.dateTime ? `${day} ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : day;
  }

  _body() {
    if (this._tab === "meals") {
      const plan = this._attrs("meals").plan || {};
      return `<div class="grid">${DAYS.map((d) => `<div class="card"><h3>${cap(d)}</h3>${SLOTS.map((s) =>
        `<button class="slot" data-act="meal" data-day="${d}" data-slot="${s}"><small>${cap(s)}</small><br>${esc((plan[d] || {})[s] || "＋")}</button>`).join("")}</div>`).join("")}</div>`;
    }
    if (this._tab === "shopping") {
      const items = this._attrs("shopping").items || [];
      return `<div class="bar"><button data-act="addshop">＋ Add item</button><button data-act="clearshop">Clear checked</button></div>` +
        items.map((i) => `<div class="row"><button class="big ${i.checked ? "on" : ""}" data-act="shopcheck" data-id="${i.id}" data-checked="${i.checked}">${i.checked ? "✔" : "○"}</button><span class="${i.checked ? "done" : ""}">${esc(i.name)}</span><button data-act="shopdel" data-id="${i.id}">✕</button></div>`).join("");
    }
    if (this._tab === "chores") {
      const chores = this._attrs("chores").chores || [];
      return `<div class="bar"><button data-act="addchore">＋ Add chore</button></div>` +
        chores.map((c) => `<div class="row"><button class="big ${c.done ? "on" : ""}" data-act="chorecheck" data-id="${c.id}" data-done="${c.done}">${c.done ? "✔" : "○"}</button><span class="${c.done ? "done" : ""}">${esc(c.title)}${c.assignee ? ` <em>· ${esc(c.assignee)}</em>` : ""}${c.due ? ` <small>due ${esc(c.due)}</small>` : ""}</span><button data-act="choredel" data-id="${c.id}">✕</button></div>`).join("");
    }
    if (this._tab === "recipes") {
      const recipes = this._attrs("recipes").recipes || [];
      return `<div class="bar"><button data-act="addrecipe">＋ Add recipe</button></div>` +
        recipes.map((r) => { const safe = /^https?:\/\//i.test(r.url || "") ? r.url : ""; return `<div class="row"><span>${safe ? `<a href="${esc(safe)}" target="_blank" rel="noopener noreferrer">${esc(r.name)}</a>` : esc(r.name)}${r.notes ? ` <small>${esc(r.notes)}</small>` : ""}</span><button data-act="recipedel" data-id="${r.id}">✕</button></div>`; }).join("");
    }
    return this._events.length
      ? this._events.map((e) => `<div class="row"><strong>${esc(this._fmt(e))}</strong><span>${esc(e.summary)}</span></div>`).join("")
      : `<p>No upcoming events. Select calendars in the JVRWall integration options.</p>`;
  }

  _render() {
    if (!this._hass || !this.shadowRoot) return;
    const tabs = [["meals","🍽 Meals"],["shopping","🛒 Shopping"],["chores","✅ Chores"],["recipes","📖 Recipes"],["calendar","📅 Calendar"]];
    this.shadowRoot.innerHTML = `<style>
      :host{display:block}ha-card{padding:16px;font-size:1.3em}
      .tabs{display:flex;gap:8px;margin-bottom:16px}
      button{min-height:56px;min-width:56px;font-size:1em;border-radius:12px;border:none;padding:8px 16px;background:var(--secondary-background-color);color:var(--primary-text-color);cursor:pointer}
      .tabs button{flex:1}.tabs button.active,button.on{background:var(--primary-color);color:var(--text-primary-color,#fff)}
      .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
      .card{background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:12px;padding:8px}
      .slot{width:100%;margin-top:6px;text-align:left}
      .row{display:flex;align-items:center;gap:16px;padding:8px 0;border-bottom:1px solid var(--divider-color)}
      .row span{flex:1}.done{text-decoration:line-through;opacity:.6}.bar{display:flex;gap:8px;margin-bottom:8px}
    </style><ha-card><div class="tabs">${tabs.map(([k,l]) => `<button data-tab="${k}" class="${this._tab===k?"active":""}">${l}</button>`).join("")}</div>${this._body()}</ha-card>`;
    this.shadowRoot.onclick = (ev) => this._click(ev);
  }

  _click(ev) {
    const b = ev.target.closest("button"); if (!b) return;
    const d = b.dataset;
    if (d.tab) { this._tab = d.tab; this._render(); if (d.tab === "calendar") { this._lastLoad = 0; this._loadEvents(); } return; }
    switch (d.act) {
      case "meal": { const m = prompt(`${cap(d.day)} ${d.slot}:`); if (m !== null) this._call("set_meal", { day: d.day, slot: d.slot, meal: m }); break; }
      case "addshop": { const n = prompt("Item:"); if (n) this._call("add_shopping_item", { name: n }); break; }
      case "shopcheck": this._call("check_shopping_item", { id: d.id, checked: d.checked !== "true" }); break;
      case "addrecipe": { const n = prompt("Recipe name:"); if (n) { const u = prompt("Link (optional):"); this._call("add_recipe", { name: n, ...(u ? { url: u } : {}) }); } break; }
      case "recipedel": this._call("remove_recipe", { id: d.id }); break;
      case "shopdel": this._call("remove_shopping_item", { id: d.id }); break;
      case "clearshop": this._call("clear_checked_shopping", {}); break;
      case "addchore": { const t = prompt("Chore:"); if (!t) break; const a = prompt("Assign to (optional):"); this._call("add_chore", a ? { title: t, assignee: a } : { title: t }); break; }
      case "chorecheck": this._call("complete_chore", { id: d.id, done: d.done !== "true" }); break;
      case "choredel": this._call("remove_chore", { id: d.id }); break;
    }
  }
}
customElements.define("jvrwall-card", JVRWallCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "jvrwall-card", name: "JVRWall", description: "Family wall-tablet dashboard" });
