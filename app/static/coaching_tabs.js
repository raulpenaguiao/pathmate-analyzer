"use strict";
(function () {
	function activateTab(name) {
		document.querySelectorAll(".coaching-tabs .tab").forEach(function (t) {
			t.classList.toggle("is-active", t.dataset.tab === name);
		});
		document.querySelectorAll(".coaching-tabs .tab-panel").forEach(function (p) {
			p.classList.toggle("is-active", p.dataset.tab === name);
		});
		if (name === "dialogs") loadMicroDialogs();
	}

	var mdPromise = null;
	function loadMicroDialogs() {
		var host = document.getElementById("md-lazy");
		if (!host) return Promise.resolve();
		if (host.dataset.loaded) return Promise.resolve();
		if (mdPromise) return mdPromise;
		mdPromise = fetch(host.dataset.url)
			.then(function (r) { return r.text(); })
			.then(function (html) {
				host.innerHTML = html;
				host.dataset.loaded = "1";
				wireMicroDialogs();
			})
			.catch(function () {
				host.innerHTML = '<p class="muted">Failed to load micro dialogs.</p>';
				mdPromise = null;
			});
		return mdPromise;
	}

	function wireMicroDialogs() {
		var f = document.getElementById("dlg-filter");
		if (f) f.addEventListener("input", function () {
			filterRows(f.value, ".dlg", "name");
		});
		var langSel = document.getElementById("md-lang");
		var panel = document.querySelector(".md-panel");
		if (langSel && panel) langSel.addEventListener("change", function () {
			panel.dataset.lang = langSel.value;
		});
	}

	function filterRows(q, selector, key) {
		q = q.trim().toLowerCase();
		document.querySelectorAll(selector).forEach(function (el) {
			var hay = (el.dataset[key] || "").toLowerCase();
			el.style.display = !q || hay.indexOf(q) !== -1 ? "" : "none";
		});
	}

	function jumpTo(id) {
		if (!id) return;
		var el = document.getElementById(id);
		var go = function () {
			var target = document.getElementById(id);
			if (!target) return;
			var panel = target.closest(".tab-panel");
			if (panel) activateTab(panel.dataset.tab);
			var d = target.closest("details");
			while (d) {
				d.open = true;
				d = d.parentElement ? d.parentElement.closest("details") : null;
			}
			if (target.tagName === "DETAILS") target.open = true;
			requestAnimationFrame(function () {
				target.scrollIntoView({ block: "center", behavior: "smooth" });
				target.classList.add("is-target");
				setTimeout(function () { target.classList.remove("is-target"); }, 1800);
			});
			history.replaceState(null, "", "#" + id);
		};
		if (!el && id.indexOf("dlg-") === 0) {
			activateTab("dialogs");
			loadMicroDialogs().then(go);
			return;
		}
		go();
	}

	function toggleRulesTree() {
		var box = document.getElementById("rules-tree");
		var btn = document.getElementById("rules-tree-btn");
		if (!box.dataset.loaded) {
			fetch(btn.dataset.url)
				.then(function (r) { return r.text(); })
				.then(function (html) {
					box.innerHTML = html;
					box.dataset.loaded = "1";
					box.hidden = false;
				});
		} else {
			box.hidden = !box.hidden;
		}
	}

	document.addEventListener("click", function (e) {
		var a = e.target.closest("a[data-jump]");
		if (!a) return;
		e.preventDefault();
		jumpTo(a.getAttribute("href").slice(1));
	});

	document.addEventListener("DOMContentLoaded", function () {
		document.querySelectorAll(".coaching-tabs .tab").forEach(function (t) {
			t.addEventListener("click", function () {
				activateTab(t.dataset.tab);
				history.replaceState(null, "", "#tab-" + t.dataset.tab);
			});
		});

		var rf = document.getElementById("rule-filter");
		if (rf) rf.addEventListener("input", function () {
			filterRows(rf.value, ".rule-row", "search");
		});
		var vf = document.getElementById("var-filter");
		if (vf) vf.addEventListener("input", function () {
			filterRows(vf.value, "#var-table tbody tr", "name");
		});
		var rtb = document.getElementById("rules-tree-btn");
		if (rtb) rtb.addEventListener("click", toggleRulesTree);

		var h = decodeURIComponent(location.hash.slice(1));
		if (h.indexOf("tab-") === 0) activateTab(h.slice(4));
		else if (h) jumpTo(h);
	});
})();
