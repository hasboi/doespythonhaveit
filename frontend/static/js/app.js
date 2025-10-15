import { $, fetchAPI, throwError, url, renderCards } from "./utils.js";

$("#searchBtn").addEventListener("click", debounceSearch);
$("#searchInput").addEventListener("keydown", (e) => {
	if (e.key === "Enter") {
		debounceSearch();
	}
});

let timeout;

function debounceSearch() {
	const inputValue = $("#searchInput").value.trim().toLowerCase();
	if (inputValue == "") {
		$("#searchInput").classList.remove("error");
		$("#searchInput").classList.add("error");

		$(".error-empty").style.display = "block";
		$("#loading").style.display = "none";
		return;
	}

	$("#loading").style.display = "flex";
	$("#results").innerHTML = "";
	clearTimeout(timeout);
	timeout = setTimeout(() => {
		searchLib();
	}, 100);
}

$("#searchInput").addEventListener("animationend", () => {
	$("#searchInput").classList.remove("error");
});

async function searchLib() {
	const inputValue = $("#searchInput").value.trim().toLowerCase();
	throwError(false);

	/* {
        "response": "true",
        "results": [
            {
                "name": "numpy",
                "category": "math",
                "desc": "Powerful n-dimensional arrays and math functions."
            }
        ]
    }
    */

	const output = await fetchAPI(`${url}/search?q=${inputValue}`);

	if (output.error) {
		throwError(true, output.error);
		return;
	}

	if (output.response === "true") {
		throwError(false);

		const ro = renderCards(output.results);

		let r;
		for (r of ro) {
			$("#results").appendChild(r);
		}
	} else {
		throwError(
			true,
			"no library found with that keyword. wanna suggest one?",
			true
		);
	}
	$("#loading").style.display = "none";
}

$("#searchInput").addEventListener("input", () => {
	$(".error-empty").style.display = "none";
});
