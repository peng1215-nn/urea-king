/**
 * overflow_tooltip.js
 * 给所有 .detail-value 和 .invite-meta > span 等截断元素
 * 加点击显示完整内容的 tooltip
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

        // 先让它渲染出来获取实际尺寸
        tooltip.style.left = '0px';
        tooltip.style.top = '0px';
        tooltip.style.transform = '';

        const rect = target.getBoundingClientRect();
        const tipW = tooltip.offsetWidth || 280;
        const tipH = tooltip.offsetHeight || 60;

        let left = rect.left;
        let top = rect.bottom + 8;

        // 不超出右边
        if (left + tipW > window.innerWidth - 8) {
            left = window.innerWidth - tipW - 8;
        }
        if (left < 8) left = 8;

        // 不超出下边，则显示在上方
        if (top + tipH > window.innerHeight - 8) {
            top = rect.top - tipH - 8;
        }
        if (top < 8) top = 8;

        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    }

    function hideTooltip() {
        if (!tooltip) return;
        tooltip.classList.remove('visible');
    }

    function isOverflowing(el) {
        return el.scrollWidth > el.clientWidth + 1;
    }

    function attachTooltip(el) {
        // 防止重复绑定
        if (el._tooltipBound) return;
        el._tooltipBound = true;

        // 检查溢出并标记
        function checkOverflow() {
            if (isOverflowing(el)) {
                el.setAttribute('data-overflowing', 'true');
            } else {
                el.removeAttribute('data-overflowing');
            }
        }
        checkOverflow();

        el.addEventListener('click', function (e) {
            if (!isOverflowing(el)) return;
            e.stopPropagation();
            showTooltip(el, el.textContent.trim());
        });
    }

    function initOverflowTooltips() {
        // .detail-value 元素
        document.querySelectorAll('.detail-value').forEach(attachTooltip);

        // .invite-meta 里的 span（邀请码页面）
        document.querySelectorAll('.invite-meta > span').forEach(attachTooltip);

        // .stats-row-sub（game_log统计页面）
        document.querySelectorAll('.stats-row-sub').forEach(attachTooltip);

        // .player-rate-stats 里的 span（玩家水上/水下率）
        document.querySelectorAll('.player-rate-stats > span, .rate-games, .rate-win, .rate-lose').forEach(attachTooltip);

        // 点击其他地方关闭
        if (!document._tooltipClickBound) {
            document._tooltipClickBound = true;
            document.addEventListener('click', function () {
                hideTooltip();
            });
        }
    }

    // 初始化 + 内容更新后重新检测（MutationObserver）
    function setup() {
        initOverflowTooltips();

        // 监听任何可能动态加载的内容容器
        const containers = [
            document.getElementById('detail-panel'),
            document.querySelector('.detail-panel'),
            document.getElementById('invite-list'),
            document.querySelector('.stats-list'),
            document.querySelector('.player-rates-list'),
        ].filter(Boolean);

        containers.forEach(function(panel) {
            const observer = new MutationObserver(function () {
                setTimeout(function () {
                    initOverflowTooltips();
                }, 50);
            });
            observer.observe(panel, { childList: true, subtree: true, characterData: true });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();
