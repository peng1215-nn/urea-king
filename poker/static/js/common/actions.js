/*
 * 全站统一的事件分发。
 *
 * 页面里不再写 onclick="..." 这类内联脚本（安全策略禁止内联脚本），改成：
 *   <button data-on-click="saveNickname">                     点击时调用 saveNickname()
 *   <button data-on-click="switchView" data-args="[&quot;logs&quot;]">  调用 switchView("logs")
 *   <input  data-on-change="toggleSelectAll" data-args="[&quot;$checked&quot;]">
 *   <div    data-href="/admin-dashboard">                       点击时跳转
 *   <button data-back>                                          点击时返回上一页
 *   <button data-on-click="exportGameCard" data-args="[12]" data-stop>  调用后不再触发外层元素
 *
 * data-args 是 JSON 数组，其中这几个特殊值会被替换：
 *   "$this" 当前元素   "$checked" 当前元素的 checked   "$value" 当前元素的 value   "$event" 事件对象
 *
 * 行为与原来的内联写法一致：从被点击的元素开始逐层往外，凡是带对应 data-on-* 的元素都会执行，
 * 遇到 data-stop 就停止（相当于原来的 event.stopPropagation()）。
 */
(function () {
    if (window.__actionsInstalled) {
        return;
    }
    window.__actionsInstalled = true;

    var EVENTS = ["click", "change", "input"];

    function resolveArg(arg, el, event) {
        if (arg === "$this") return el;
        if (arg === "$checked") return el.checked;
        if (arg === "$value") return el.value;
        if (arg === "$event") return event;
        return arg;
    }

    function parseArgs(el) {
        var raw = el.getAttribute("data-args");
        if (!raw) return [];
        try {
            var parsed = JSON.parse(raw);
            return Array.isArray(parsed) ? parsed : [parsed];
        } catch (error) {
            console.error("[actions] invalid data-args", raw, el);
            return [];
        }
    }

    function run(el, type, event) {
        var name = el.getAttribute("data-on-" + type);
        var fn = window[name];

        if (typeof fn !== "function") {
            console.error("[actions] function not found:", name, el);
            return;
        }

        var args = parseArgs(el).map(function (arg) {
            return resolveArg(arg, el, event);
        });

        // 和原来的内联写法一样，函数里的 this 不是被点击的元素（需要元素时用 "$this" 传入）
        fn.apply(window, args);
    }

    EVENTS.forEach(function (type) {
        var attr = "data-on-" + type;

        document.addEventListener(type, function (event) {
            var el = event.target instanceof Element ? event.target : event.target.parentElement;

            while (el && el !== document) {
                if (el.hasAttribute(attr)) {
                    run(el, type, event);
                    if (el.hasAttribute("data-stop")) {
                        event.stopPropagation();
                        return;
                    }
                }

                if (type === "click" && el.hasAttribute("data-back")) {
                    window.history.back();
                    return;
                }

                if (type === "click" && el.hasAttribute("data-href")) {
                    window.location.href = el.getAttribute("data-href");
                    return;
                }

                el = el.parentElement;
            }
        });
    });
})();
