import { $, $$, fetchAPI, throwError, url, renderCards } from "./utils.js";

let all;
let page = 1;

init();

async function init() {
	try {
		all = await anotherFetch(`${url}/all`);
		putAll();
		updateBtn();
		updateValue();

		document.querySelectorAll(".prev").forEach((p) => {
			p.addEventListener("click", () => previous(p));
		});

		document.querySelectorAll(".next").forEach((p) => {
			p.addEventListener("click", () => next(p));
		});

		$(
			"#listing"
		).innerHTML = `listing <strong>${all.total_results}</strong> libraries`;
	} catch (err) {
		throwError(true, err.message || "Failed to initialize data.");
	}
}

async function anotherFetch(endpoint) {
	try {
		const data = await fetchAPI(endpoint);

		if (!data || data.error) {
			throw new Error(data?.error || "Empty or invalid API response.");
		}

		throwError(false);
		return data;
	} catch (err) {
		console.error("fetch error:", err);
		throwError(true, err.message || "Network error. Please try again later.");
		return { results: [], has_next: false, has_prev: false };
	}
}

function putAll() {
	if (!all || all.error) {
		throwError(true, all?.error || "Invalid data from server.");
		return;
	}

	const ro = renderCards(all.results);
	const container = $("#all");
	container.innerHTML = "";

	for (const r of ro) container.appendChild(r);
}

function updateBtn() {
	const prevs = $$(".prev");
	const nexts = $$(".next");

	prevs.forEach((p) => p.classList.toggle("disabled", !all.has_prev));
	nexts.forEach((n) => n.classList.toggle("disabled", !all.has_next));
}

function updateValue() {
	const pageEls = $$(".page");
	pageEls.forEach((p) => (p.value = all.page || page));
}

async function next(e) {
	if (e.classList.contains("disabled") || !all.has_next) return;

	page++;
	all = await anotherFetch(`${url}/all?page=${page}`);
	putAll();
	updateBtn();
	updateValue();
}

async function previous(e) {
	if (e.classList.contains("disabled") || !all.has_prev) return;

	page--;
	all = await anotherFetch(`${url}/all?page=${page}`);
	putAll();
	updateBtn();
	updateValue();
}
