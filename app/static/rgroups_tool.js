"use strict";
(function () {
	function downloadLink(url, label) {
		return '<a class="button secondary" href="' + url + '">&#8681; ' + label + '</a>';
	}

	function wireRgroupsPanel(root) {
		if (!root || root.dataset.wired) return;
		root.dataset.wired = "1";

		var reportUrl = root.dataset.reportUrl;
		var prepareUrl = root.dataset.prepareUrl;
		var expandStartUrl = root.dataset.expandStartUrl;
		var expandStatusTpl = root.dataset.expandStatusUrl; // .../JOBID
		var downloadTpl = root.dataset.downloadUrl; // .../KIND

		function dlUrl(kind) { return downloadTpl.replace("KIND", kind); }

		var btn1 = root.querySelector("#rgroups-step1-btn");
		var result1 = root.querySelector("#rgroups-step1-result");
		if (btn1) btn1.addEventListener("click", function () {
			btn1.disabled = true;
			result1.textContent = "Running…";
			fetch(reportUrl, { method: "POST" })
				.then(function (r) { return r.json(); })
				.then(function (data) {
					btn1.disabled = false;
					if (!data.ok) { result1.textContent = data.error || "Failed."; return; }
					result1.innerHTML =
						data.groups + " groups, " + data.messages + " messages, " +
						data.pools + " pools (" + data.thinPools + " thin) &mdash; " +
						downloadLink(dlUrl("table"), "rgroups_table.csv");
				})
				.catch(function () { btn1.disabled = false; result1.textContent = "Request failed."; });
		});

		var btn2 = root.querySelector("#rgroups-step2-btn");
		var result2 = root.querySelector("#rgroups-step2-result");
		var limitInput = root.querySelector('#rgroups-expand-form [name=limit]');
		if (btn2) btn2.addEventListener("click", function () {
			btn2.disabled = true;
			result2.textContent = "Running…";
			fetch(prepareUrl, { method: "POST" })
				.then(function (r) { return r.json(); })
				.then(function (data) {
					btn2.disabled = false;
					if (!data.ok) { result2.textContent = data.error || "Failed."; return; }
					result2.innerHTML =
						data.pools + " thin pools, " + data.variants + " variants to generate &mdash; " +
						downloadLink(dlUrl("requests"), "rgroups_requests.csv");
					if (limitInput) limitInput.max = String(data.pools);
				})
				.catch(function () { btn2.disabled = false; result2.textContent = "Request failed."; });
		});

		var form = root.querySelector("#rgroups-expand-form");
		var result3 = root.querySelector("#rgroups-step3-result");
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
						submitBtn.disabled = false;
						if (job.error) {
							result3.textContent = "Error: " + job.error;
						} else {
							result3.innerHTML =
								job.okCount + "/" + job.totalVariants + " variants generated &mdash; " +
								downloadLink(dlUrl("generated"), "rgroups_generated.csv");
						}
						return;
					}
					setTimeout(tick, 1500);
				}).catch(function () { setTimeout(tick, 3000); });
			};
			tick();
		}

		if (form) form.addEventListener("submit", function (e) {
			e.preventDefault();
			var fd = new FormData(form);
			var submitBtn = form.querySelector("button[type=submit]");
			submitBtn.disabled = true;
			result3.textContent = "";
			fill.style.width = "0%";
			label.textContent = "";
			fetch(expandStartUrl, { method: "POST", body: fd })
				.then(function (r) { return r.json(); })
				.then(function (data) {
					var keyField = form.querySelector('[name=api_key]');
					if (keyField) keyField.value = "";
					if (!data.ok) {
						submitBtn.disabled = false;
						result3.textContent = data.error || "Failed to start.";
						return;
					}
					poll(data.jobId, submitBtn);
				})
				.catch(function () {
					submitBtn.disabled = false;
					result3.textContent = "Request failed.";
				});
		});
	}

	window.wireRgroupsPanel = wireRgroupsPanel;
})();
