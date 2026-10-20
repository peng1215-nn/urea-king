/**
 * overflow_tooltip.js
 * 给截断元素加点击显示完整内容的 tooltip
 * 支持: .detail-value, .invite-meta > span, .stats-row-sub, .stats-row-value,
 *       .rate-games, .rate-win, .rate-lose
 */
(function () {
    let tooltip = null;

    function createTooltip() {
        const el = document.createElement('div');
        el.className = 'detail-value-tooltip';
        document.body.appendChild(el);
        return el;
    }

    function showTooltip(target, text) {
        if (!tooltip) tooltip = createTooltip();

        tooltip.textContent = text;
        tooltip.style.opacity = '0';
        tooltip.style.left = '0px';
        tooltip.style.top = '0px';
        tooltip.style.transform = '';
        tooltip.classList.add('visible');

        // 等浏览器渲染后获取实际尺寸
        requestAnimationFrame(function () {
            const rect = target.getBoundingClientRect();
            const tipW = tooltip.offsetWidth;
            const tipH = tooltip.offsetHeight;

            let left = rect.left;
            let top = rect.bottom + 8;

            if (left + tipW > window.innerWidth - 8) {
                left = window.innerWidth - tipW - 8;
            }
            if (left < 8) left = 8;

            if (top + tipH > window.innerHeight - 8) {
                top = rect.top - tipH - 8;
            }
            if (top < 8) top = 8;

            tooltip.style.left = left + 'px';
            tooltip.style.top = top + 'px';
            tooltip.style.opacity = '';
        });
    }

    function hideTooltip() {
        if (!tooltip) return;
        tooltip.classList.remove('visible');
    }

    function isOverflowing(el) {
        return el.scrollWidth > el.clientWidth + 1;
    }

    function attachTooltip(el) {
        if (el._tooltipBound) return;
        el._tooltipBound = true;

        el.addEventListener('click', function (e) {
            if (!isOverflowing(el)) return;
            e.stopPropagation();
            showTooltip(el, el.textContent.trim());
        });
    }

    // 更新所有可截断元素的 data-overflowing 标记（用于 CSS cursor/underline）
    function updateOverflowMarks(root) {
        var scope = root || document;
        scope.querySelectorAll(
            '.detail-value, .invite-meta > span, .stats-row-sub, .stats-row-value, ' +
            '.rate-games, .rate-win, .rate-lose'
        ).forEach(function (el) {
            attachTooltip(el);
            if (isOverflowing(el)) {
                el.setAttribute('data-overflowing', 'true');
            } else {
                el.removeAttribute('data-overflowing');
            }
        });
    }

    function setup() {
        updateOverflowMarks();

        // 点击其他地方关闭
        document.addEventListener('click', function () {
            hideTooltip();
        });

        // 监听动态内容变化
        var containers = [
            document.querySelector('.detail-panel'),
            document.getElementById('invite-list'),
            document.querySelector('.stats-list'),
            document.querySelector('.player-rates-list'),
        ].filter(Boolean);

        containers.forEach(function (panel) {
            var observer = new MutationObserver(function () {
                setTimeout(function () { updateOverflowMarks(panel); }, 80);
            });
            observer.observe(panel, { childList: true, subtree: true, characterData: true });
        });

        // 窗口resize后重新检测溢出标记
        window.addEventListener('resize', function () {
            updateOverflowMarks();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();
