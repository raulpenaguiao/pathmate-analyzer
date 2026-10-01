"use strict";
(function () {
	var root = document.querySelector(".sim");
	if (!root) return;

	var urls = {
		list: root.dataset.listUrl,
		new: root.dataset.newUrl,
		getBase: root.dataset.getUrlBase,
		stepBase: root.dataset.stepUrlBase,
		renameBase: root.dataset.renameUrlBase,
		deleteBase: root.dataset.deleteUrlBase,
	};

	var chats = [];
	var activeId = null;
	var state = null;
	var meta = { dialogs: [], groups: [], languages: [], engine: null };
	var varFilter = "";

	var el = {
		clock: document.getElementById("sim-clock"),
		transcript: document.getElementById("sim-transcript"),
		pending: document.getElementById("sim-pending"),
		vars: document.querySelector("#sim-vars tbody"),
		launchSelect: document.getElementById("sim-launch-select"),
		chatList: document.getElementById("chat-list"),
		legacy: document.getElementById("sim-legacy"),
		stale: document.getElementById("sim-stale"),
		unknown: document.getElementById("sim-unknown"),
		autoPeriodic: document.getElementById("sim-auto-periodic"),
	};

	// Structured engine events (Stage 4): a transcript line may carry
	// `event`; `text` stays the fallback, so this only adds a label.
	var EVENT_LABELS = {
		launch: "launched",
		timeout: "not answered",
		suppressed: "suppressed",
		unresolved_target: "unresolved dialog",
	};

	function urlFor(base, id) {
		return base.replace("__ID__", id);
	}

	function loadChats(selectId) {
		return fetch(urls.list)
			.then(function (r) { return r.json(); })
			.then(function (data) {
				chats = data.chats || [];
				renderChatList();
				var toSelect = selectId || (chats[0] && chats[0].id);
				if (toSelect) return selectChat(toSelect);
				activeId = null;
				state = null;
				render();
			});
	}

	function selectChat(id) {
		activeId = id;
		renderChatList();
		return fetch(urlFor(urls.getBase, id))
			.then(function (r) { return r.json(); })
			.then(function (data) {
				state = data.chat.state;
				meta = {
					dialogs: data.dialogs || [],
					groups: data.groups || [],
					languages: data.languages || ["en-GB"],
					engine: data.engine,
					fingerprint: data.fingerprint || "ok",
				};
				populateLaunch();
				render();
			});
	}

	function post(action) {
		if (!activeId) return Promise.resolve();
		return fetch(urlFor(urls.stepBase, activeId), {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ action: action, lang: meta.languages[0] }),
		})
			.then(function (r) { return r.json(); })
			.then(function (data) {
				if (data.fingerprint === "stale") {  // refused: built on another export
					meta.fingerprint = "stale";
					render();
					return;
				}
				state = data.state;
				if (action.type === "reset") meta.fingerprint = "ok";
				render();
			});
	}

	function populateLaunch() {
		var html = '<optgroup label="Micro dialogs">';
		meta.dialogs.forEach(function (d) {
			html += '<option value="d:' + d.i + '">' + escapeHtml(d.name) + "</option>";
		});
		html += "</optgroup>";
		if (meta.groups.length) {
			html += '<optgroup label="Message groups">';
			meta.groups.forEach(function (g) {
				html += '<option value="g:' + g.i + '">' + escapeHtml(g.name) + "</option>";
			});
			html += "</optgroup>";
		}
		el.launchSelect.innerHTML = html;
	}

	function renderChatList() {
		if (!chats.length) {
			el.chatList.innerHTML = '<li class="muted chat-empty">No chats yet &mdash; start a new one or import a .pmcp.</li>';
			return;
		}
		el.chatList.innerHTML = chats
			.map(function (c) {
				var badge = c.kind === "imported" ? "📥" : "💬";
				var active = c.id === activeId ? " is-active" : "";
				return (
					'<li class="chat-item' + active + '" data-chat-id="' + c.id + '">' +
					'<span class="chat-item-name" title="' + escapeHtml(c.name) + '">' +
					badge + " " + escapeHtml(c.name) + "</span>" +
					'<button type="button" class="chat-item-del" data-del-chat="' + c.id + '" title="Delete this chat">&times;</button>' +
					"</li>"
				);
			})
			.join("");
	}

	function render() {
		if (!state) {
			el.clock.textContent = "…";
			el.transcript.innerHTML = '<p class="muted">Select a chat on the left, start a new one, or import a .pmcp.</p>';
			el.pending.hidden = true;
			el.vars.innerHTML = "";
			el.legacy.hidden = true;
			el.stale.hidden = true;
			el.unknown.hidden = true;
			return;
		}
		el.legacy.hidden = meta.engine !== "html";
		el.stale.hidden = meta.fingerprint !== "stale";
		el.unknown.hidden = meta.fingerprint !== "unknown";
		el.autoPeriodic.checked = !state.settings || state.settings.auto_periodic !== false;
		root.querySelectorAll("[data-setting]").forEach(function (box) {
			var v = (state.settings || {})[box.dataset.setting];
			box.checked = v == null ? box.dataset.default === "true" : !!v;
		});
		var c = state.clock;
		el.clock.textContent =
			"day " + c.day + ", " + pad(c.hour) + ":" + pad(c.minute);

		el.transcript.innerHTML = (state.transcript || [])
			.map(function (m) {
				var ev = m.event && EVENT_LABELS[m.event.type];
				return (
					'<div class="bubble b-' + m.kind + (ev ? " b-ev b-ev-" + m.event.type : "") + '">' +
					'<span class="b-t">' + escapeHtml(m.t || "") +
					(ev ? ' <span class="b-ev-label">' + ev + "</span>" : "") + "</span>" +
					escapeHtml(m.text) +
					"</div>"
				);
			})
			.join("");
		el.transcript.scrollTop = el.transcript.scrollHeight;

		if (state.pending && state.pending.input) {
			el.pending.hidden = false;
			el.pending.innerHTML =
				timeoutLabel(state.pending) +
				'<span class="muted">answer:</span> ' + freeInputForm(state.pending.input);
			var fin = el.pending.querySelector(".free-answer-in");
			if (fin) fin.focus();
		} else if (state.pending && state.pending.options) {
			el.pending.hidden = false;
			el.pending.innerHTML =
				questionnaireNote(state.pending.options) +
				timeoutLabel(state.pending) +
				'<span class="muted">answer:</span> ' +
				state.pending.options
					.map(function (o) {
						return (
							'<button type="button" class="answer" data-answer="' +
							escapeHtml(o.value) + '">' + escapeHtml(o.label) + "</button>"
						);
					})
					.join(" ");
		} else {
			el.pending.hidden = true;
			el.pending.innerHTML = "";
		}

		var names = Object.keys(state.vars || {}).sort();
		el.vars.innerHTML = names
			.filter(function (n) {
				return !varFilter || n.toLowerCase().indexOf(varFilter) !== -1;
			})
			.map(function (n) {
				return (
					// name stacked above its input: long camelCase names get the
					// panel's full width instead of a squeezed column
					"<tr><td><span class='var' title='" + escapeHtml(n) + "'>" + escapeHtml(n) + "</span>" +
					'<input class="sim-var-in" data-name="' + escapeHtml(n) +
					'" aria-label="' + escapeHtml(n) + '" value="' + escapeHtml(state.vars[n]) + '"></td></tr>'
				);
			})
			.join("");
	}

	root.addEventListener("click", function (e) {
		var b = e.target.closest("button");

		if (b && b.id === "chat-new-btn") {
			fetch(urls.new, { method: "POST" })
				.then(function (r) { return r.json(); })
				.then(function (data) { loadChats(data.chat.id); });
			return;
		}

		if (b && b.dataset.delChat) {
			e.stopPropagation();
			if (!confirm("Delete this chat? This can't be undone.")) return;
			var deletedId = b.dataset.delChat;
			fetch(urlFor(urls.deleteBase, deletedId), { method: "POST" })
				.then(function () { loadChats(deletedId === activeId ? null : activeId); });
			return;
		}

		var item = e.target.closest(".chat-item");
		if (item && item.dataset.chatId) {
			selectChat(item.dataset.chatId);
			return;
		}

		if (b && b.dataset.varFilter !== undefined) {
			var vfIn = document.getElementById("sim-var-filter");
			vfIn.value = b.dataset.varFilter;
			varFilter = b.dataset.varFilter.toLowerCase();
			render();
			vfIn.focus();
			return;
		}

		if (!b || !state) return;
		if (b.dataset.tick) post({ type: "tick", minutes: +b.dataset.tick });
		else if (b.dataset.slot) post({ type: "tick", to: "next-slot" });
		else if (b.dataset.periodic) post({ type: "run_periodic" });
		else if (b.dataset.reset) post({ type: "reset" });
		else if (b.dataset.answer !== undefined) post({ type: "answer", value: b.dataset.answer });
		else if (b.id === "sim-launch-btn") {
			var v = el.launchSelect.value || "";
			if (v.indexOf("d:") === 0) post({ type: "launch_dialog", dialog_i: +v.slice(2) });
			else if (v.indexOf("g:") === 0) post({ type: "launch_group", group_i: +v.slice(2) });
		}
	});

	// Free-input answer types (PMCP 6.0 docs, Micro Dialogs: Free Text,
	// Free Numbers, Date, Time). The engine sends `pending.input`
	// {kind, multiline, template, min, max}; "_" in the template marks where
	// the typed value goes. The raw value is posted and stored as-is.
	function freeInputForm(input) {
		var kind = input.kind || "text";
		var tpl = input.template || "";
		var cut = tpl.indexOf("_");
		var before = cut === -1 ? tpl : tpl.slice(0, cut);
		var after = cut === -1 ? "" : tpl.slice(cut + 1);
		var attrs = ' class="free-answer-in" required';
		if (input.placeholder) attrs += ' placeholder="' + escapeHtml(input.placeholder) + '"';
		// only bounds the browser can enforce for this kind (a -99 or unset
		// var would otherwise block every submit)
		var ok = { number: /^-?\d+(\.\d+)?$/, time: /^\d\d:\d\d$/ }[kind];
		["min", "max"].forEach(function (k) {
			var b = input[k] == null ? "" : String(input[k]);
			// the engine sends time bounds as decimal hours ("22.5" = 22:30)
			if (kind === "time" && /^\d+(\.\d+)?$/.test(b) && +b < 24) {
				var mins = Math.round(+b * 60);
				b = ("0" + Math.floor(mins / 60)).slice(-2) + ":" + ("0" + (mins % 60)).slice(-2);
			}
			if (ok && ok.test(b) && !(kind === "number" && b === "-99")) attrs += " " + k + '="' + escapeHtml(b) + '"';
		});
		var field = kind === "text" && input.multiline
			? "<textarea" + attrs + ' rows="2"></textarea>'
			: '<input type="' + ({ number: "number", date: "date", time: "time" }[kind] || "text") + '"' +
				attrs + (kind === "number" ? ' step="any"' : "") + ">";
		return (
			'<form class="free-answer" data-kind="' + escapeHtml(kind) + '">' +
			(before ? '<span class="free-answer-tpl">' + escapeHtml(before) + "</span>" : "") +
			field +
			(after ? '<span class="free-answer-tpl">' + escapeHtml(after) + "</span>" : "") +
			'<button type="submit" class="answer">Send</button></form>'
		);
	}

	root.addEventListener("submit", function (e) {
		var form = e.target.closest(".free-answer");
		if (!form) return;
		e.preventDefault();
		var v = form.querySelector(".free-answer-in").value.trim();
		if (!v) return;
		// <input type=date> gives yyyy-mm-dd; the sim's dates are dd.mm.yyyy
		if (form.dataset.kind === "date") {
			var d = v.split("-");
			if (d.length === 3) v = d[2] + "." + d[1] + "." + d[0];
		}
		post({ type: "answer", value: v });
	});

	root.addEventListener("change", function (e) {
		var input = e.target.closest(".sim-var-in");
		if (input) post({ type: "set_var", name: input.dataset.name, value: input.value });
		else if (e.target.dataset && e.target.dataset.setting) {
			post({ type: "set_setting", name: e.target.dataset.setting, value: e.target.checked });
		} else if (e.target === el.autoPeriodic) {
			post({ type: "set_setting", name: "auto_periodic", value: el.autoPeriodic.checked });
		}
	});

	// An open-component:questionnaire button opens an in-app questionnaire
	// whose answers reach coaching variables through PMCMS bindings that
	// aren't exported, so the sim can't fill them - the user sets them first.
	function questionnaireNote(options) {
		var q = options.filter(function (o) { return o.component === "questionnaire"; })[0];
		if (!q) return "";
		var prefix = String(q.questionnaire_id || "").split("-")[0];
		return (
			'<p class="sim-questionnaire">📋 In the app this opens questionnaire <code>' +
			escapeHtml(q.questionnaire_id || "?") + "</code>. Its answers aren't in the export, so set the " +
			"variables it would write in the inspector before answering." +
			(prefix ? ' <button type="button" class="secondary" data-var-filter="' + escapeHtml(prefix) +
				'">Show $' + escapeHtml(prefix) + "* variables</button>" : "") +
			"</p>"
		);
	}

	// Minutes left before the pending question counts as not answered
	// (`timeout_at` is absolute minutes, same unit as the clock below).
	function timeoutLabel(pending) {
		if (pending.timeout_at == null) return "";
		var c = state.clock;
		var left = pending.timeout_at - (c.day * 1440 + c.hour * 60 + c.minute);
		var txt = left <= 0 ? "timeout due" :
			"times out in " + (left >= 60 ? Math.floor(left / 60) + "h " : "") + (left % 60) + "m";
		return '<span class="sim-timeout">⏳ ' + txt + "</span> ";
	}

	var vf = document.getElementById("sim-var-filter");
	if (vf) vf.addEventListener("input", function () {
		varFilter = vf.value.trim().toLowerCase();
		render();
	});

	function pad(n) { return (n < 10 ? "0" : "") + n; }
	function escapeHtml(s) {
		return String(s).replace(/[&<>"']/g, function (ch) {
			return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
		});
	}

	var started = false;
	function init() {
		if (started) return;
		started = true;
		loadChats();
	}

	document.addEventListener("DOMContentLoaded", init);
	if (document.readyState !== "loading") init();
})();
