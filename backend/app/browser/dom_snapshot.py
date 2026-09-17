from typing import Dict, Any, List


EXTRACT_DOM_JS = """
(() => {
    function isVisible(el) {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    }

    function getElementSelector(el) {
        if (el.id) return `#${el.id}`;
        if (el.getAttribute('data-testid')) return `[data-testid="${el.getAttribute('data-testid')}"]`;
        if (el.getAttribute('name')) return `${el.tagName.toLowerCase()}[name="${el.getAttribute('name')}"]`;
        if (el.getAttribute('placeholder')) return `${el.tagName.toLowerCase()}[placeholder="${el.getAttribute('placeholder')}"]`;
        if (el.getAttribute('aria-label')) return `[aria-label="${el.getAttribute('aria-label')}"]`;
        
        let path = el.tagName.toLowerCase();
        if (el.className && typeof el.className === 'string') {
            const classes = el.className.trim().split(/\\s+/).filter(c => !c.includes(':') && c.length < 30).slice(0, 2);
            if (classes.length > 0) path += '.' + classes.join('.');
        }
        return path;
    }

    const interactiveElements = [];
    const elements = document.querySelectorAll('button, a, input, select, textarea, [role="button"], [role="link"], [role="checkbox"], [role="menuitem"], [role="tab"], [role="dialog"], h1, h2, h3, form, [contenteditable="true"]');

    let idx = 1;
    elements.forEach(el => {
        if (!isVisible(el)) return;

        const tag = el.tagName.toLowerCase();
        const role = el.getAttribute('role') || tag;
        const text = (el.innerText || el.textContent || el.getAttribute('placeholder') || el.getAttribute('value') || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ').substring(0, 100);
        const name = el.getAttribute('name') || '';
        const id = el.id || '';
        const placeholder = el.getAttribute('placeholder') || '';
        const type = el.getAttribute('type') || '';
        const href = el.getAttribute('href') || '';
        const value = el.value || '';
        const isChecked = el.checked || false;
        const isDisabled = el.disabled || el.getAttribute('aria-disabled') === 'true';

        const selector = getElementSelector(el);

        // Friendly description
        let label = text;
        if (!label && placeholder) label = placeholder;
        if (!label && name) label = name;
        if (!label && id) label = id;

        interactiveElements.push({
            index: idx++,
            tag,
            role,
            type,
            label,
            value,
            checked: isChecked,
            disabled: isDisabled,
            href,
            selector
        });
    });

    // Detect modals / dialogs / alerts
    const dialogs = [];
    document.querySelectorAll('[role="dialog"], .modal, .dialog, dialog[open], [role="alert"], [role="status"]').forEach(d => {
        if (isVisible(d)) {
            dialogs.push({
                title: d.getAttribute('aria-label') || (d.querySelector('h1, h2, h3, .title, .modal-title')?.innerText || 'Dialog').trim(),
                text: (d.innerText || '').substring(0, 200).replace(/\\s+/g, ' ')
            });
        }
    });

    // Detect navigation links
    const navs = [];
    document.querySelectorAll('nav, header, [role="navigation"]').forEach(nav => {
        const links = Array.from(nav.querySelectorAll('a, button')).map(l => (l.innerText || l.textContent || '').trim()).filter(Boolean);
        if (links.length > 0) {
            navs.push(links.join(' | '));
        }
    });

    // Main visible text content excerpt
    const mainText = (document.body.innerText || '').slice(0, 2000).replace(/\\s+/g, ' ');

    return {
        url: window.location.href,
        title: document.title,
        interactiveElements: interactiveElements.slice(0, 60), // keep top 60 items for compact LLM context
        dialogs,
        navs,
        textExcerpt: mainText
    };
})()
"""


class DOMSnapshot:
    @staticmethod
    def format_for_llm(raw_snapshot: Dict[str, Any]) -> str:
        """
        Formats raw DOM snapshot into compact, highly readable text representation for LLMs.
        """
        lines = []
        lines.append(f"Current URL: {raw_snapshot.get('url', '')}")
        lines.append(f"Page Title: {raw_snapshot.get('title', '')}")

        navs = raw_snapshot.get("navs", [])
        if navs:
            lines.append(f"Navigation: {'; '.join(navs)}")

        dialogs = raw_snapshot.get("dialogs", [])
        if dialogs:
            lines.append("Active Dialogs/Modals/Alerts:")
            for d in dialogs:
                lines.append(f"  - [{d.get('title')}]: {d.get('text')}")

        elements = raw_snapshot.get("interactiveElements", [])
        lines.append(f"Interactive Elements ({len(elements)} items):")
        for el in elements:
            props = []
            if el.get("type"):
                props.append(f"type='{el['type']}'")
            if el.get("value"):
                props.append(f"value='{el['value']}'")
            if el.get("checked"):
                props.append("checked=true")
            if el.get("disabled"):
                props.append("disabled=true")
            if el.get("href"):
                props.append(f"href='{el['href']}'")

            props_str = f" [{', '.join(props)}]" if props else ""
            lines.append(
                f"  [{el.get('index')}] <{el.get('tag')}> role='{el.get('role')}' label='{el.get('label')}' selector='{el.get('selector')}'{props_str}"
            )

        text_excerpt = raw_snapshot.get("textExcerpt", "")
        if text_excerpt:
            lines.append(f"Page Text Summary: {text_excerpt[:300]}...")

        return "\n".join(lines)
