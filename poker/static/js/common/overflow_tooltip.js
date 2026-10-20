/**
 * overflow_tooltip.js
 * 给所有 .detail-value 元素加点击显示完整内容的 tooltip
 * 当文字被截断（scrollWidth > clientWidth）时才生效
 */
(function () {
    let tooltip = null;
    let hideTimer = null;

    function createTooltip() {
        const el = document.createElement('div');
        el.className = 'detail-value-tooltip';
        document.body.appendChild(el);
        return el;
    }

    function showTooltip(target, text) {
        if (!tooltip) tooltip = createTooltip();
        clearTimeout(hideTimer);

        tooltip.textContent = text;
        tooltip.classList.add('visible');

        // 定位在元素下方
        const rect = target.getBoundingClientRect();
        const tipWidth = 280;
        let left = rect.left;
        let top = rect.bottom + 8;

        // 不超出右边
        if (left + tipWidth > window.innerWidth - 8) {
            left = window.innerWidth - tipWidth - 8;
        }
        // 不超出下边，则显示在上方
        if (top + 60 > window.innerHeight) {
            top = rect.top - 8;
            tooltip.style.transform = 'translateY(-100%)';
        } else {
            tooltip.style.transform = 'translateY(0)';
        }

        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    }

    function hideTooltip() {
        if (!tooltip) return;
        tooltip.classList.remove('visible');
    }

    function initOverflowTooltips() {
        document.querySelectorAll('.detail-value').forEach(function (el) {
            // 检查是否溢出
            if (el.scrollWidth > el.clientWidth + 1) {
                el.setAttribute('data-overflowing', 'true');
            }

            el.addEventListener('click', function (e) {
                if (el.scrollWidth <= el.clientWidth + 1) return;
                e.stopPropagation();
                showTooltip(el, el.textContent.trim());
            });
        });

        // 点击其他地方关闭
        document.addEventListener('click', function () {
            hideTooltip();
        });
    }

    // 初始化 + 内容更新后重新检测（MutationObserver）
    function setup() {
        initOverflowTooltips();

        const panel = document.getElementById('detail-panel') || document.querySelector('.detail-panel');
        if (!panel) return;

        const observer = new MutationObserver(function () {
            // 内容变化后延迟重新检测溢出状态
            setTimeout(function () {
                panel.querySelectorAll('.detail-value').forEach(function (el) {
                    if (el.scrollWidth > el.clientWidth + 1) {
                        el.setAttribute('data-overflowing', 'true');
                    } else {
                        el.removeAttribute('data-overflowing');
                    }
                });
            }, 50);
        });
        observer.observe(panel, { childList: true, subtree: true, characterData: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();
