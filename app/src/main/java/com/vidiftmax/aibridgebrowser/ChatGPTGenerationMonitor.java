package com.vidiftmax.aibridgebrowser;

/**
 * Read-only state machine for observing ChatGPT's visible stop-generation control.
 * It never clicks the control and never treats an initial missing control as completion.
 */
final class ChatGPTGenerationMonitor {
    enum Observation { GENERATING, NOT_GENERATING, UNKNOWN }
    enum State { UNKNOWN, RESPONDING, RESPONSE_COMPLETE }

    private State state = State.UNKNOWN;
    private boolean generationObserved;
    private int consecutiveAbsent;

    State state() { return state; }

    State observe(Observation observation) {
        if (observation == null || observation == Observation.UNKNOWN) {
            consecutiveAbsent = 0;
            return state;
        }
        if (observation == Observation.GENERATING) {
            generationObserved = true;
            consecutiveAbsent = 0;
            state = State.RESPONDING;
            return state;
        }
        if (!generationObserved) {
            state = State.UNKNOWN;
            return state;
        }
        consecutiveAbsent++;
        if (consecutiveAbsent >= 2) state = State.RESPONSE_COMPLETE;
        return state;
    }

    /** JavaScript returns GENERATING, NOT_GENERATING, or UNKNOWN; observation only. */
    static String observationScript() {
        return "(function(){try{" +
            "const visible=e=>{if(!e)return false;const r=e.getBoundingClientRect();const s=getComputedStyle(e);" +
            "return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none';};" +
            "const buttons=Array.from(document.querySelectorAll('button'));" +
            "const stop=buttons.some(b=>{const a=(b.getAttribute('aria-label')||'').toLowerCase();" +
            "const title=(b.getAttribute('title')||'').toLowerCase();" +
            "const t=(b.getAttribute('data-testid')||'').toLowerCase();" +
            "return visible(b)&&(t.includes('stop')||a.includes('stop generating')||" +
            "a.includes('stop streaming')||a==='stop'||title.includes('stop'));});" +
            "if(stop)return 'GENERATING';" +
            "const send=buttons.some(b=>{const a=(b.getAttribute('aria-label')||'').toLowerCase();" +
            "const title=(b.getAttribute('title')||'').toLowerCase();" +
            "const t=(b.getAttribute('data-testid')||'').toLowerCase();" +
            "return visible(b)&&(t.includes('send')||a.includes('send')||title.includes('send'));});" +
            "if(send)return 'NOT_GENERATING';" +
            "return 'UNKNOWN';" +
            "}catch(e){return 'UNKNOWN';}})();";
    }

    static Observation parse(String value) {
        if ("GENERATING".equals(value)) return Observation.GENERATING;
        if ("NOT_GENERATING".equals(value)) return Observation.NOT_GENERATING;
        return Observation.UNKNOWN;
    }
}
