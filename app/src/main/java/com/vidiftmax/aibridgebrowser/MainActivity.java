package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.net.Uri;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.KeyEvent;
import android.view.inputmethod.EditorInfo;
import android.content.SharedPreferences;
import android.util.Base64;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.SslErrorHandler;
import android.net.http.SslError;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.util.ArrayDeque;
import java.util.Deque;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

public final class MainActivity extends Activity {
    private static final int MAX_TABS = 6;
    private static final String HOME_URL = "https://chatgpt.com/";
    private static final String STATE_URLS = "tab_urls";
    private static final String STATE_ACTIVE = "active_tab";
    private static final String STATE_PAUSED = "automation_paused";
    private static final String PREFS = "ai_bridge_tabs_v1";
    private static final String LIFECYCLE_STATE = "lifecycle_state";
    private static final String LIFECYCLE_RUNNING = "RUNNING";
    private static final String LIFECYCLE_PAUSED = "PAUSED";
    private static final String LIFECYCLE_RECOVERING = "RECOVERING";

    private final List<Tab> tabs = new ArrayList<>();
    private final BrowserState browserState = new BrowserState();
    private LinearLayout tabStrip;
    private FrameHost frameHost;
    private EditText addressBar;
    private TextView audioStatus;
    private TextView automationStatus;
    private Button pauseButton;
    private boolean automationPaused = false;
    private String lifecycleState = LIFECYCLE_RUNNING;
    private SharedPreferences prefs;
    private final Deque<PendingMessage> pendingMessages = new ArrayDeque<>();
    private int activeTab = -1;

    private static final class Tab {
        final WebView webView;
        String title;
        final String tabId;
        final String profileId;
        boolean pageReady = false;
        boolean chatReady = false;
        boolean locked = true;
        String missionState = "WAITING_PAGE";

        Tab(WebView webView, String title) {
            this(webView, title, UUID.randomUUID().toString(), "profile-" + UUID.randomUUID());
        }

        Tab(WebView webView, String title, String tabId, String profileId) {
            this.webView = webView;
            this.title = title;
            this.tabId = tabId;
            this.profileId = profileId;
        }
    }

    private static final class PendingMessage {
        final String tabId;
        final String profileId;
        final String text;
        PendingMessage(String tabId, String profileId, String text) {
            this.tabId = tabId;
            this.profileId = profileId;
            this.text = text;
        }
    }

    private static final class FrameHost extends LinearLayout {
        FrameHost(Activity activity) {
            super(activity);
            setOrientation(VERTICAL);
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        buildChrome();
        if (savedInstanceState != null) automationPaused = savedInstanceState.getBoolean(STATE_PAUSED, false);
        if (restoreDurableTabs()) return;
        if (savedInstanceState != null) {
            ArrayList<String> urls = savedInstanceState.getStringArrayList(STATE_URLS);
            if (urls != null && !urls.isEmpty()) {
                for (String url : urls) addTab(url, false);
                int requested = savedInstanceState.getInt(STATE_ACTIVE, 0);
                selectTab(Math.max(0, Math.min(requested, tabs.size() - 1)));
                return;
            }
        }
        addTab(HOME_URL, true);
    }

    private void buildChrome() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        LinearLayout controls = new LinearLayout(this);
        controls.setGravity(Gravity.CENTER_VERTICAL);
        controls.setPadding(dp(6), dp(4), dp(6), dp(4));

        addressBar = new EditText(this);
        addressBar.setSingleLine(true);
        addressBar.setTextSize(14);
        addressBar.setHint("Endereço HTTPS");
        addressBar.setImeOptions(EditorInfo.IME_ACTION_GO);
        controls.addView(addressBar, new LinearLayout.LayoutParams(0, dp(46), 1));

        Button back = new Button(this);
        back.setText("←");
        back.setContentDescription("Voltar");
        controls.addView(back);
        back.setOnClickListener(v -> navigateBack());

        Button refresh = new Button(this);
        refresh.setText("↻");
        refresh.setContentDescription("Recarregar");
        controls.addView(refresh);
        refresh.setOnClickListener(v -> reloadCurrent());

        Button go = new Button(this);
        go.setText("Ir");
        controls.addView(go);
        go.setOnClickListener(v -> navigateCurrent());

        Button add = new Button(this);
        add.setText("+");
        add.setContentDescription("Nova aba");
        controls.addView(add);
        add.setOnClickListener(v -> addTab(HOME_URL, true));

        addressBar.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO ||
                (event != null && event.getKeyCode() == KeyEvent.KEYCODE_ENTER)) {
                navigateCurrent();
                return true;
            }
            return false;
        });

        tabStrip = new LinearLayout(this);
        tabStrip.setOrientation(LinearLayout.HORIZONTAL);
        HorizontalScrollView tabScroller = new HorizontalScrollView(this);
        tabScroller.setHorizontalScrollBarEnabled(false);
        tabScroller.addView(tabStrip);

        frameHost = new FrameHost(this);
        automationStatus = new TextView(this);
        automationStatus.setTextSize(12);
        automationStatus.setPadding(dp(10), dp(6), dp(10), dp(6));
        automationStatus.setGravity(Gravity.CENTER);
        pauseButton = new Button(this);
        pauseButton.setText(automationPaused ? "▶ Continuar automação" : "⏸ Pausar automação");
        pauseButton.setOnClickListener(v -> setAutomationPaused(!automationPaused));

        audioStatus = new TextView(this);
        audioStatus.setText("Central de áudio: ainda sem captura ou retransmissão.");
        audioStatus.setTextSize(12);
        audioStatus.setPadding(dp(10), dp(10), dp(10), dp(10));
        audioStatus.setGravity(Gravity.CENTER);
        updateAutomationStatus();

        root.addView(controls);
        root.addView(tabScroller);
        root.addView(frameHost, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        root.addView(pauseButton, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(automationStatus, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(audioStatus, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(root);
    }

    private void addTab(String url, boolean select) {
        addTab(url, select, null, null);
    }

    private void addTab(String url, boolean select, String restoredTabId, String restoredProfileId) {
        if (tabs.size() >= MAX_TABS) {
            Toast.makeText(this, "Limite inicial de " + MAX_TABS + " abas.", Toast.LENGTH_SHORT).show();
            return;
        }

        WebView webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setSafeBrowsingEnabled(true);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);

        Tab tab = new Tab(webView, "Nova aba",
                restoredTabId == null ? UUID.randomUUID().toString() : restoredTabId,
                restoredProfileId == null ? "profile-" + UUID.randomUUID() : restoredProfileId);
        tab.locked = true;
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !isAllowedWebUrl(request.getUrl().toString());
            }

            @Override
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                tab.pageReady = false;
                tab.chatReady = false;
                if (tabs.indexOf(tab) == activeTab) addressBar.setText(url);
                updateAutomationStatus();
            }

            @Override
            public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                handler.cancel();
                audioStatus.setText("Navegação bloqueada: certificado TLS inválido.");
            }

            @Override
            public void onReceivedError(WebView view, android.webkit.WebResourceRequest request,
                                        android.webkit.WebResourceError error) {
                if (request.isForMainFrame()) {
                    audioStatus.setText("Falha ao carregar a página. Verifique a conexão e tente novamente.");
                }
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                String pageTitle = view.getTitle();
                tab.title = (pageTitle == null || pageTitle.trim().isEmpty())
                        ? hostLabel(url) : pageTitle.trim();
                tab.pageReady = true;
                tab.chatReady = isChatHost(url);
                renderTabs();
                if (tabs.indexOf(tab) == activeTab) addressBar.setText(url);
                deliverPendingMessages();
            }
        });

        // Camera/microphone access is deliberately denied until a user-consent flow is implemented.
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(android.webkit.PermissionRequest request) {
                request.deny();
            }

            @Override
            public boolean onCreateWindow(WebView view, boolean isDialog,
                                          boolean isUserGesture, android.os.Message resultMsg) {
                return false;
            }
        });

        frameHost.addView(webView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        tabs.add(tab);
        browserState.addTab(tab.tabId);
        webView.loadUrl(normalizeUrl(url));
        renderTabs();
        persistTabs();
        if (select) selectTab(tabs.size() - 1);
        else webView.setVisibility(View.GONE);
    }

    private boolean isChatHost(String url) {
        Uri uri = Uri.parse(url);
        String host = uri.getHost();
        return host != null && (host.equalsIgnoreCase("chatgpt.com") || host.endsWith(".chatgpt.com"));
    }

    private void setAutomationPaused(boolean paused) {
        automationPaused = paused;
        browserState.setPaused(paused);
        lifecycleState = paused ? LIFECYCLE_PAUSED : LIFECYCLE_RUNNING;
        for (Tab tab : tabs) {
            if (paused) tab.missionState = "PAUSED";
            else if (tab.pageReady && tab.chatReady) tab.missionState = "READY";
            else tab.missionState = "WAITING_PAGE";
        }
        if (pauseButton != null) {
            pauseButton.setText(paused ? "▶ Continuar automação" : "⏸ Pausar automação");
        }
        updateAutomationStatus();
        persistTabs();
        if (!paused) deliverPendingMessages();
    }

    private void updateAutomationStatus() {
        if (automationStatus == null) return;
        String state = lifecycleState;
        automationStatus.setText("Automação: " + state + " · fila: " + pendingMessages.size());
    }

    private void queueMessage(int tabIndex, String message) {
        if (tabIndex < 0 || tabIndex >= tabs.size() || message == null || message.trim().isEmpty()) return;
        Tab tab = tabs.get(tabIndex);
        pendingMessages.addLast(new PendingMessage(tab.tabId, tab.profileId, message));
        tab.missionState = "MESSAGE_QUEUED";
        updateAutomationStatus();
        persistTabs();
        deliverPendingMessages();
    }

    private void deliverPendingMessages() {
        if (automationPaused) return;
        while (!pendingMessages.isEmpty()) {
            PendingMessage item = pendingMessages.peekFirst();
            Tab tab = findTab(item.tabId, item.profileId);
            if (tab == null) {
                break;
            }
            if (!tab.pageReady || !tab.chatReady) break;
            // Safe boundary: DOM text injection and auto-submit are not implemented yet.
            break;
        }
        updateAutomationStatus();
    }

    private boolean isAllowedWebUrl(String value) {
        Uri uri = Uri.parse(value);
        String scheme = uri.getScheme();
        return scheme != null &&
                ("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme)) &&
                uri.getHost() != null && uri.getUserInfo() == null;
    }

    private String normalizeUrl(String value) {
        String candidate = value == null ? "" : value.trim();
        if (candidate.isEmpty()) return HOME_URL;
        if (!candidate.contains("://")) candidate = "https://" + candidate;
        return isAllowedWebUrl(candidate) ? candidate : HOME_URL;
    }

    private String hostLabel(String value) {
        Uri uri = Uri.parse(value);
        String host = uri.getHost();
        return host == null ? "Aba" : host.toLowerCase(Locale.ROOT).replaceFirst("^www\\.", "");
    }

    private WebView currentWebView() {
        return activeTab >= 0 && activeTab < tabs.size() ? tabs.get(activeTab).webView : null;
    }

    private void navigateCurrent() {
        WebView current = currentWebView();
        if (current == null) return;
        String url = normalizeUrl(addressBar.getText().toString());
        current.loadUrl(url);
    }

    private void navigateBack() {
        WebView current = currentWebView();
        if (current != null && current.canGoBack()) current.goBack();
    }

    private void reloadCurrent() {
        WebView current = currentWebView();
        if (current != null) current.reload();
    }

    private void renderTabs() {
        tabStrip.removeAllViews();
        for (int i = 0; i < tabs.size(); i++) {
            final int index = i;
            Tab tab = tabs.get(i);
            LinearLayout item = new LinearLayout(this);
            item.setGravity(Gravity.CENTER_VERTICAL);

            Button tabButton = new Button(this);
            String title = tab.title.length() > 14 ? tab.title.substring(0, 14) + "…" : tab.title;
            tabButton.setText((i == activeTab ? "● " : "") + title);
            tabButton.setTextSize(11);
            tabButton.setOnClickListener(v -> selectTab(index));
            item.addView(tabButton);

            Button lock = new Button(this);
            lock.setText(tab.locked ? "🔒" : "🔓");
            lock.setTextSize(11);
            lock.setContentDescription(tab.locked ? "Desbloquear aba " + (index + 1) : "Bloquear aba " + (index + 1));
            lock.setOnClickListener(v -> {
                tab.locked = !tab.locked;
                persistTabs();
                renderTabs();
            });
            item.addView(lock);

            Button close = new Button(this);
            close.setText("×");
            close.setTextSize(12);
            close.setMinWidth(dp(36));
            close.setContentDescription("Fechar aba " + (index + 1));
            close.setOnClickListener(v -> new AlertDialog.Builder(this)
                    .setTitle("Fechar aba?")
                    .setMessage("A aba foi desbloqueada. Deseja realmente fechá-la?")
                    .setNegativeButton("Cancelar", null)
                    .setPositiveButton("Fechar", (dialog, which) -> closeTab(index))
                    .show());
            close.setEnabled(!tab.locked);
            item.addView(close);
            tabStrip.addView(item);
        }
    }

    private void selectTab(int index) {
        if (index < 0 || index >= tabs.size()) return;
        activeTab = index;
        browserState.selectTab(index);
        for (int i = 0; i < tabs.size(); i++) {
            tabs.get(i).webView.setVisibility(i == index ? View.VISIBLE : View.GONE);
        }
        String url = tabs.get(index).webView.getUrl();
        addressBar.setText(url == null ? "" : url);
        renderTabs();
    }

    private void closeTab(int index) {
        if (index < 0 || index >= tabs.size()) return;
        if (tabs.get(index).locked) {
            Toast.makeText(this, "Aba bloqueada 🔒. Desbloqueie antes de fechar.", Toast.LENGTH_SHORT).show();
            return;
        }
        Tab removed = tabs.remove(index);
        browserState.removeTab(removed.tabId);
        removed.webView.stopLoading();
        frameHost.removeView(removed.webView);
        removed.webView.destroy();

        if (tabs.isEmpty()) {
            activeTab = -1;
            addTab(HOME_URL, true);
            return;
        }
        int next = activeTab;
        if (index < activeTab) next--;
        else if (index == activeTab) next = Math.min(index, tabs.size() - 1);
        selectTab(Math.max(0, next));
        persistTabs();
    }

    private Tab findTab(String tabId, String profileId) {
        for (Tab tab : tabs) {
            if (tab.tabId.equals(tabId) && tab.profileId.equals(profileId)) return tab;
        }
        return null;
    }

    private void persistTabs() {
        if (prefs == null) return;
        SharedPreferences.Editor e = prefs.edit();
        e.putInt("count", tabs.size());
        e.putInt("active", Math.max(0, activeTab));
        e.putBoolean("paused", automationPaused);
        e.putInt("queue_count", pendingMessages.size());
        int qi = 0;
        for (PendingMessage pm : pendingMessages) {
            e.putString("queue_tab_id_" + qi, pm.tabId);
            e.putString("queue_profile_id_" + qi, pm.profileId);
            e.putString("queue_text_" + qi, Base64.encodeToString(pm.text.getBytes(java.nio.charset.StandardCharsets.UTF_8), Base64.NO_WRAP));
            qi++;
        }
        for (int i = 0; i < tabs.size(); i++) {
            Tab t = tabs.get(i);
            String url = t.webView.getUrl();
            e.putString("url_" + i, url == null ? HOME_URL : url);
            e.putString("title_" + i, t.title == null ? "Nova aba" : t.title);
            e.putString("tab_id_" + i, t.tabId);
            e.putString("profile_id_" + i, t.profileId);
            e.putBoolean("locked_" + i, t.locked);
            e.putString("mission_state_" + i, t.missionState);
        }
        e.apply();
    }

    private void restorePendingMessages() {
        pendingMessages.clear();
        int count = prefs.getInt("queue_count", 0);
        for (int i = 0; i < count; i++) {
            String tabId = prefs.getString("queue_tab_id_" + i, null);
            String profileId = prefs.getString("queue_profile_id_" + i, null);
            String encoded = prefs.getString("queue_text_" + i, null);
            if (tabId != null && profileId != null && encoded != null) {
                try {
                    String message = new String(Base64.decode(encoded, Base64.NO_WRAP), java.nio.charset.StandardCharsets.UTF_8);
                    pendingMessages.addLast(new PendingMessage(tabId, profileId, message));
                } catch (IllegalArgumentException ignored) { }
            }
        }
    }

    private boolean restoreDurableTabs() {
        if (prefs == null) return false;
        int count = prefs.getInt("count", 0);
        if (count <= 0) return false;
        automationPaused = prefs.getBoolean("paused", false);
        restorePendingMessages();
        for (int i = 0; i < Math.min(count, MAX_TABS); i++) {
            addTab(prefs.getString("url_" + i, HOME_URL), false,
                    prefs.getString("tab_id_" + i, null),
                    prefs.getString("profile_id_" + i, null));
            Tab t = tabs.get(tabs.size() - 1);
            t.title = prefs.getString("title_" + i, "Nova aba");
            t.locked = prefs.getBoolean("locked_" + i, true);
            t.missionState = prefs.getString("mission_state_" + i, "WAITING_PAGE");
        }
        if (tabs.isEmpty()) return false;
        int requested = prefs.getInt("active", 0);
        selectTab(Math.max(0, Math.min(requested, tabs.size() - 1)));
        renderTabs();
        return true;
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    @Override
    protected void onStop() {
        // Leaving the app pauses automation so queued actions cannot run while the user is using the tablet elsewhere.
        if (!isChangingConfigurations()) {
            automationPaused = true;
            browserState.setPaused(true);
            lifecycleState = LIFECYCLE_RECOVERING;
            for (Tab tab : tabs) tab.missionState = "PAUSED";
        }
        persistTabs();
        super.onStop();
    }

    @Override
    protected void onStart() {
        super.onStart();
        if (lifecycleState.equals(LIFECYCLE_RECOVERING)) {
            automationPaused = true;
            browserState.setPaused(true);
            lifecycleState = LIFECYCLE_PAUSED;
            updateAutomationStatus();
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        ArrayList<String> urls = new ArrayList<>();
        for (Tab tab : tabs) {
            String url = tab.webView.getUrl();
            urls.add(url == null ? HOME_URL : url);
        }
        outState.putStringArrayList(STATE_URLS, urls);
        outState.putInt(STATE_ACTIVE, Math.max(0, activeTab));
        outState.putBoolean(STATE_PAUSED, automationPaused);
        persistTabs();
        super.onSaveInstanceState(outState);
    }

    @Override
    public void onBackPressed() {
        if (activeTab >= 0 && activeTab < tabs.size()) {
            WebView current = tabs.get(activeTab).webView;
            if (current.canGoBack()) {
                current.goBack();
                return;
            }
        }
        super.onBackPressed();
    }

    @Override
    protected void onDestroy() {
        persistTabs();
        for (Tab tab : tabs) {
            tab.webView.stopLoading();
            tab.webView.destroy();
        }
        tabs.clear();
        super.onDestroy();
    }
}
