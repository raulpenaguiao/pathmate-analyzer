"use strict";
(function () {
	function setError(root, id, msg) {
		var el = root.querySelector("#" + id);
		if (!el) return;
		el.textContent = msg || "";
		el.hidden = !msg;
	}

	// Refetches the whole tab fragment from the server (the source of truth
	// for what CSVs exist) and re-renders in place, so the next step's
	// button/preview reflects what's actually on disk -- not just what this
	// one browser tab remembers doing.
	function reload(root) {
		var url = root.dataset.selfUrl;
		return fetch(url)
			.then(function (r) { return r.text(); })
			.then(function (html) {
				var tmp = document.createElement("div");
				tmp.innerHTML = html;
				var fresh = tmp.querySelector(".rgroups-panel");
				if (!fresh) return;
				root.innerHTML = fresh.innerHTML;
				wireInner(root);
			});
	}

	function wireInner(root) {
		var reportUrl = root.dataset.reportUrl;
		var prepareUrl = root.dataset.prepareUrl;
		var expandStartUrl = root.dataset.expandStartUrl;
		var expandStatusTpl = root.dataset.expandStatusUrl; // .../JOBID

		var btn1 = root.querySelector("#rgroups-step1-btn");
		if (btn1) btn1.addEventListener("click", function () {
			btn1.disabled = true;
			setError(root, "rgroups-step1-error", "");
			fetch(reportUrl, { method: "POST" })
				.then(function (r) { return r.json(); })
				.then(function (data) {
					if (!data.ok) { btn1.disabled = false; setError(root, "rgroups-step1-error", data.error || "Failed."); return; }
					reload(root);
				})
				.catch(function () { btn1.disabled = false; setError(root, "rgroups-step1-error", "Request failed."); });
		});

		var btn2 = root.querySelector("#rgroups-step2-btn");
		if (btn2 && !btn2.disabled) btn2.addEventListener("click", function () {
			btn2.disabled = true;
			setError(root, "rgroups-step2-error", "");
			fetch(prepareUrl, { method: "POST" })
				.then(function (r) { return r.json(); })
				.then(function (data) {
					if (!data.ok) { btn2.disabled = false; setError(root, "rgroups-step2-error", data.error || "Failed."); return; }
					reload(root);
				})
				.catch(function () { btn2.disabled = false; setError(root, "rgroups-step2-error", "Request failed."); });
		});

		var form = root.querySelector("#rgroups-expand-form");
		var bar = root.querySelector("#rgroups-progress");
		var fill = root.querySelector("#rgroups-progress-fill");
		var label = root.querySelector("#rgroups-progress-label");

		function poll(jobId, submitBtn) {
			bar.hidden = false;
			var url = expandStatusTpl.replace("JOBID", jobId);
			var tick = function () {
				fetch(url).then(function (r) { return r.json(); }).then(function (job) {
					if (!job.ok) {
						submitBtn.disabled = false;
						label.textContent = job.error || "Lost track of the job.";
						return;
					}
					var total = job.total || 1;
					var done = job.done || 0;
					var pct = Math.round((done / total) * 100);
					fill.style.width = pct + "%";
					label.textContent = "pool " + (job.current || 0) + "/" + total +
						(job.pool ? " — " + job.pool : "") +
						(job.lastStatus ? " (" + job.lastStatus + ")" : "");
					if (job.finished) {
						if (job.error) {
							submitBtn.disabled = false;
							setError(root, "rgroups-step3-error", "Error: " + job.error);
							return;
						}
						label.textContent += " — done, " + job.okCount + "/" + job.totalVariants + " variants generated";
						reload(root);
						return;
					}
					setTimeout(tick, 1500);
				}).catch(function () { setTimeout(tick, 3000); });
			};
			tick();
		}

		if (form && !form.querySelector("[name=api_key]").disabled) form.addEventListener("submit", function (e) {
			e.preventDefault();
			var fd = new FormData(form);
			var submitBtn = form.querySelector("button[type=submit]");
			submitBtn.disabled = true;
			setError(root, "rgroups-step3-error", "");
			fill.style.width = "0%";
			label.textContent = "";
			fetch(expandStartUrl, { method: "POST", body: fd })
				.then(function (r) { return r.json(); })
				.then(function (data) {
					var keyField = form.querySelector('[name=api_key]');
					if (keyField) keyField.value = "";
					if (!data.ok) {
						submitBtn.disabled = false;
						setError(root, "rgroups-step3-error", data.error || "Failed to start.");
						return;
					}
					poll(data.jobId, submitBtn);
				})
				.catch(function () {
					submitBtn.disabled = false;
					setError(root, "rgroups-step3-error", "Request failed.");
				});
		});
	}

	function wireRgroupsPanel(root) {
		if (!root) return;
		wireInner(root);
	}

	window.wireRgroupsPanel = wireRgroupsPanel;
})();
