/* NOCT portfolio — chat widget
   No build step, no dependencies. Loads after DOM via `defer`. */

(function () {
    "use strict";

    const fab      = document.getElementById("chat-fab");
    const panel    = document.getElementById("chat-panel");
    const closeBtn = document.getElementById("chat-close");
    const form     = document.getElementById("chat-form");
    const input    = document.getElementById("chat-input");
    const log      = document.getElementById("chat-log");
    const endpoint = "/api/chat/";

    if (!fab || !panel || !form || !input || !log) return;

    const history = [];
    let isOpen = false;
    let pending = false;

    // ---------- helpers ----------

    function getCookie(name) {
        const match = document.cookie.match(
            new RegExp("(?:^|;\\s*)" + name + "=([^;]*)")
        );
        return match ? decodeURIComponent(match[1]) : "";
    }

    function open() {
        if (isOpen) return;
        panel.hidden = false;
        fab.setAttribute("aria-expanded", "true");
        isOpen = true;
        requestAnimationFrame(() => input.focus());
    }

    function close() {
        if (!isOpen) return;
        panel.hidden = true;
        fab.setAttribute("aria-expanded", "false");
        isOpen = false;
        fab.focus();
    }

    function scrollToBottom() {
        log.scrollTop = log.scrollHeight;
    }

    function autoGrow() {
        input.style.height = "auto";
        input.style.height = Math.min(input.scrollHeight, 120) + "px";
    }

    function appendBubble(role, text) {
        const div = document.createElement("div");
        div.className = "bubble bubble--" + role;
        const p = document.createElement("p");
        p.textContent = text;
        div.appendChild(p);
        log.appendChild(div);
        scrollToBottom();
        return div;
    }

    function appendTyping() {
        const div = document.createElement("div");
        div.className = "bubble bubble--bot bubble--typing";
        div.setAttribute("data-typing", "1");
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement("span");
            div.appendChild(dot);
        }
        log.appendChild(div);
        scrollToBottom();
        return div;
    }

    function replaceTyping(typingEl, role, text) {
        if (!typingEl) return;
        typingEl.classList.remove("bubble--typing");
        typingEl.removeAttribute("data-typing");
        typingEl.querySelectorAll("span").forEach(s => s.remove());
        const p = document.createElement("p");
        p.textContent = text;
        typingEl.appendChild(p);
        scrollToBottom();
    }

    // ---------- submit ----------

    async function sendMessage(message) {
        if (pending) return;
        pending = true;
        form.querySelector(".chat-panel__send").disabled = true;

        appendBubble("user", message);
        history.push({ role: "user", content: message });

        const typing = appendTyping();

        try {
            const response = await fetch(endpoint, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                body: JSON.stringify({
                    message,
                    history: history.slice(-6),
                }),
            });

            let payload = null;
            try {
                payload = await response.json();
            } catch (err) {
                /* fall through to fallback */
            }

            const answer =
                (payload && payload.answer) ||
                "I couldn't reach the assistant just now. Please try again, or use the contact form.";

            replaceTyping(typing, "bot", answer);
            history.push({ role: "assistant", content: answer });
        } catch (err) {
            replaceTyping(
                typing,
                "bot",
                "I'm having trouble reaching the assistant. Please try again in a moment."
            );
        } finally {
            pending = false;
            form.querySelector(".chat-panel__send").disabled = false;
            input.value = "";
            autoGrow();
            input.focus();
        }
    }

    // ---------- wire-up ----------

    fab.addEventListener("click", () => (isOpen ? close() : open()));
    closeBtn.addEventListener("click", close);

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && isOpen) close();
    });

    input.addEventListener("input", autoGrow);
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            form.requestSubmit();
        }
    });

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const value = input.value.trim();
        if (!value || pending) return;
        sendMessage(value);
    });

    // Initial sizing for the textarea.
    autoGrow();
})();