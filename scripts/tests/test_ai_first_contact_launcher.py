from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MAIN = (ROOT / "app/src/main/java/com/vidiftmax/aibridgebrowser/MainActivity.java").read_text()
POLICY = (ROOT / "app/src/main/java/com/vidiftmax/aibridgebrowser/AiConversationLaunchPolicy.java").read_text()
ORCHESTRATOR = (ROOT / "app/src/main/java/com/vidiftmax/aibridgebrowser/TwoAiChatOrchestrator.java").read_text()
DOM_BRIDGE = (ROOT / "app/src/main/assets/ai_bridge_chatgpt_dom_bridge.js").read_text()
EVIDENCE = (ROOT / "app/src/main/java/com/vidiftmax/aibridgebrowser/AiBridgeEvidence.java").read_text()
ORCHESTRATOR = (ROOT / "app/src/main/java/com/vidiftmax/aibridgebrowser/TwoAiChatOrchestrator.java").read_text()


class FirstContactLauncherContractTest(unittest.TestCase):
    def test_launcher_button_is_visible_enabled_and_user_started(self):
        self.assertIn('aiConversationButton.setText("AI ↔ AI · Começar")', MAIN)
        self.assertIn("aiConversationButton.setEnabled(true)", MAIN)
        self.assertIn("aiConversationButton.setVisibility(View.VISIBLE)", MAIN)
        self.assertIn("v -> startAiConversationDialog()", MAIN)

    def test_launch_requires_two_distinct_verified_profiles(self):
        self.assertIn("AiConversationLaunchPolicy.blockingReason(", MAIN)
        self.assertIn("!tab01.tabId.equals(tab02.tabId)", MAIN)
        self.assertIn("!tab01.profileId.equals(tab02.profileId)", MAIN)
        self.assertIn("tab01.sessionIsolationSupported && tab02.sessionIsolationSupported", MAIN)

    def test_preflight_requires_real_chat_composers_and_send_buttons(self):
        self.assertIn("chatGptDomBridge.inspect(tab01.webView", MAIN)
        self.assertIn("chatGptDomBridge.inspect(tab02.webView", MAIN)
        self.assertIn('state.optBoolean("composer", false)', MAIN)
        self.assertIn('state.optBoolean("sendButton", false)', MAIN)
        self.assertIn('!state.optBoolean("generating", true)', MAIN)

    def test_preflight_accepts_present_but_initially_disabled_send_control(self):
        self.assertIn("function sendButtonElement(doc)", DOM_BRIDGE)
        self.assertIn("sendButton:!!sendButtonElement(doc)", DOM_BRIDGE)
        self.assertIn("sendButtonEnabled:!!button", DOM_BRIDGE)
        self.assertIn("const button=sendButton(doc);", DOM_BRIDGE)
        self.assertIn("if(!button)return {ok:false,code:\"SEND_BUTTON_NOT_FOUND\"};", DOM_BRIDGE)

    def test_user_must_confirm_the_two_account_assignments(self):
        self.assertIn("Confirmei que AI-01 está na conta ChatGPT correta.", MAIN)
        self.assertIn("Confirmei que AI-02 está em outra conta ChatGPT.", MAIN)
        self.assertIn("confirm01.isChecked() && confirm02.isChecked()", MAIN)

    def test_first_contact_is_exactly_ten_user_authorized_turns(self):
        self.assertIn("private static final int AI_BRIDGE_TURNS = 10", MAIN)
        self.assertIn("first, AI_BRIDGE_TURNS", MAIN)
        self.assertIn('setPositiveButton("Começar 10 turnos", null)', MAIN)
        self.assertIn('this.nextAiId = "AI-01"', ORCHESTRATOR)

    def test_launch_gate_fails_closed_for_each_missing_precondition(self):
        for reason in (
            "AI_IDENTITIES_NOT_ASSIGNED", "TABS_NOT_DISTINCT",
            "PROFILES_NOT_DISTINCT", "PROFILE_ISOLATION_UNVERIFIED",
            "PAGES_NOT_READY", "CHATGPT_NOT_OPEN",
        ):
            self.assertIn(reason, POLICY)

    def test_no_login_credentials_are_collected_by_launcher(self):
        self.assertNotIn("getPassword(", MAIN)
        self.assertNotIn('name="password"', MAIN)
        self.assertNotIn("passwordInput", MAIN)


    def test_turn_evidence_is_sequential_alternating_and_privacy_preserving(self):
        self.assertIn("turn != events.size() + 1", EVIDENCE)
        self.assertIn('turn % 2 == 1) ? "AI-01" : "AI-02"', EVIDENCE)
        self.assertIn('MessageDigest.getInstance("SHA-256")', EVIDENCE)
        self.assertIn("responseSha256", EVIDENCE)
        self.assertNotIn("final String response;", EVIDENCE)
        self.assertIn("Collections.unmodifiableList(events)", EVIDENCE)

    def test_orchestrator_requires_complete_valid_evidence_before_success(self):
        self.assertIn("evidence.turnCount() != maxTurns", ORCHESTRATOR)
        self.assertIn("!evidence.isAlternatingPair()", ORCHESTRATOR)
        self.assertIn("FINAL_EVIDENCE_VALIDATION_FAILED", ORCHESTRATOR)


if __name__ == "__main__":
    unittest.main()
