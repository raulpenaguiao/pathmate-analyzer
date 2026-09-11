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
	var meta = { dialogs: [], groups: [], languages: [] };
	var varFilter = "";

	var el = {
		clock: document.getElementById("sim-clock"),
		transcript: document.getElementById("sim-transcript"),
		pending: document.getElementById("sim-pending"),
		vars: document.querySelector("#sim-vars tbody"),
		launchSelect: document.getElementById("sim-launch-select"),
		chatList: document.getElementById("chat-list"),
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
			.then(function (data) { state = data.state; render(); });
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
			return;
		}
		var c = state.clock;
		el.clock.textContent =
			"day " + c.day + ", " + pad(c.hour) + ":" + pad(c.minute);

		el.transcript.innerHTML = (state.transcript || [])
			.map(function (m) {
				return (
					'<div class="bubble b-' + m.kind + '">' +
					'<span class="b-t">' + escapeHtml(m.t || "") + "</span>" +
					escapeHtml(m.text) +
					"</div>"
				);
			})
			.join("");
		el.transcript.scrollTop = el.transcript.scrollHeight;

		if (state.pending && state.pending.options) {
			el.pending.hidden = false;
			el.pending.innerHTML =
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
					"<tr><td><span class='var'>" + escapeHtml(n) + "</span></td>" +
					'<td><input class="sim-var-in" data-name="' + escapeHtml(n) +
					'" value="' + escapeHtml(state.vars[n]) + '"></td></tr>'
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

	root.addEventListener("change", function (e) {
		var input = e.target.closest(".sim-var-in");
		if (input) post({ type: "set_var", name: input.dataset.name, value: input.value });
	});

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
