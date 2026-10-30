/**
 * pagination.js — 紧凑分页：首页、上一页、当前页前后各 1 页、下一页、末页，中间用省略号。
 * 页数多时不会把所有页码都排出来（手机上会撑破一行）。
 * 用法：renderCompactPagination(container, page, totalPages, gotoPage)
 */
function compactPageList(page, totalPages) {
    const pages = new Set([1, totalPages, page - 1, page, page + 1]);
    const sorted = [...pages].filter(p => p >= 1 && p <= totalPages).sort((a, b) => a - b);
    const result = [];
    sorted.forEach((p, i) => {
        if (i > 0 && p - sorted[i - 1] > 1) {
            // 只差一页时直接显示那一页，比显示省略号更省地方
            if (p - sorted[i - 1] === 2) result.push(p - 1);
            else result.push("…");
        }
        result.push(p);
    });
    return result;
}

function renderCompactPagination(container, page, totalPages, gotoPage) {
    if (!container) return;
    container.innerHTML = "";
    if (totalPages <= 1) return;

    function addButton(label, target, extraClass, ariaLabel) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "page-btn" + (extraClass ? " " + extraClass : "");
        btn.innerText = label;
        if (ariaLabel) btn.setAttribute("aria-label", ariaLabel);
        if (target === null) {
            btn.disabled = true;
        } else {
            btn.addEventListener("click", () => gotoPage(target));
        }
        container.appendChild(btn);
    }

    addButton("←", page > 1 ? page - 1 : null, page <= 1 ? "disabled" : "", "previous");
    compactPageList(page, totalPages).forEach(item => {
        if (item === "…") {
            const gap = document.createElement("span");
            gap.className = "page-ellipsis";
            gap.innerText = "…";
            container.appendChild(gap);
        } else if (item === page) {
            const current = document.createElement("button");
            current.type = "button";
            current.className = "page-btn active";
            current.innerText = item;
            current.setAttribute("aria-current", "page");
            container.appendChild(current);
        } else {
            addButton(String(item), item, "", null);
        }
    });
    addButton("→", page < totalPages ? page + 1 : null, page >= totalPages ? "disabled" : "", "next");
}
