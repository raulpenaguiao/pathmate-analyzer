"use strict";
(function () {
	var root = document.querySelector(".sim");
	if (!root) return;

	var stepUrl = root.dataset.stepUrl;
	var state = null;
	var meta = { dialogs: [], groups: [], languages: [] };
	var varFilter = "";

	var el = {
		clock: document.getElementById("sim-clock"),
		transcript: document.getElementById("sim-transcript"),
		pending: document.getElementById("sim-pending"),
		vars: document.querySelector("#sim-vars tbody"),
		launchSelect: document.getElementById("sim-launch-select"),
	};

	function post(action) {
		return fetch(stepUrl, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ state: state, action: action, lang: meta.languages[0] }),
		})
			.then(function (r) { return r.json(); })
			.then(function (data) { state = data.state; render(); });
	}

	var started = false;
	function init() {
		if (started) return;
		started = true;
		fetch(root.dataset.initUrl)
			.then(function (r) { return r.json(); })
			.then(function (data) {
				state = data.state;
				meta = {
					dialogs: data.dialogs || [],
					groups: data.groups || [],
					languages: data.languages || ["en-GB"],
				};
				populateLaunch();
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

	function render() {
		if (!state) return;
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
		if (!b) return;
		if (b.dataset.tick) post({ type: "tick", minutes: +b.dataset.tick });
		else if (b.dataset.slot) post({ type: "tick", to: "next-slot" });
		else if (b.dataset.periodic) post({ type: "run_periodic" });
		else if (b.dataset.reset) post({ type: "reset" });
		else if (b.dataset.startImport) post({ type: "start_from_import" });
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

	document.addEventListener("DOMContentLoaded", init);
	if (document.readyState !== "loading") init();
})();
