// selector
export const $ = (id) => document.querySelector(id);
export const $$ = (selector) => document.querySelectorAll(selector);

// utils: fetch API
export async function fetchAPI(url) {
	if (!navigator.onLine) {
		return {
			error:
				"looks like you're offline, please check your internet connection.",
		};
	}

	try {
		const response = await fetch(url);

		if (!response.ok) {
			if (response.status >= 500) {
				return { error: "our server seems to be sleeping, try again later." };
			} else if (response.status >= 400) {
				return { error: "we couldn't find anything matching your request." };
			} else {
				return { error: `unexpected server response (${response.status}).` };
			}
		}

		try {
			const data = await response.json();
			return data;
		} catch {
			return {
				error:
					"hmm, we got something strange from the server, please try again.",
			};
		}
	} catch (err) {
		return {
			error: "we couldn't reach the server. maybe it's taking a nap?",
		};
	}
}

// utils: error
export function throwError(show = true, message = "", showButton = false) {
	$("#loading").style.display = "none";
	const errorBox = document.getElementById("error");
	const paragraph = errorBox.querySelector("p");
	const button = document.getElementById("suggest");

	if (show) {
		errorBox.style.display = "flex";
		paragraph.innerText = message || "oops, something went wrong.";
		button.style.display = showButton ? "inline-block" : "none";
	} else {
		errorBox.style.display = "none";
	}
}

// url
export const url = "http://127.0.0.1:8000";

export function renderCards(output) {
	let results = [];
	const resultDict = output;
	let r;

	for (r of resultDict) {
		const result = document.createElement("a");
		/* 
            <a href="about:blank" class="result-card">
                        <h3>numpy</h3>
                        <p>Powerful n-dimensional arrays and math functions.</p>
                    </a>*/
		result.href = r.link;
		result.classList.add("result-card");
		result.target = "_blank";

		result.innerHTML = `
            <h3>${r.name}</h3>
            <p>${r.desc || r.user_desc}</p>
            `;
		results.push(result);
	}

	return results;
}
