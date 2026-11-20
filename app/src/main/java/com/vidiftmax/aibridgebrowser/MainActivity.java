package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.os.Bundle;
import android.net.Uri;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.KeyEvent;
import android.view.inputmethod.EditorInfo;
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

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final int MAX_TABS = 5;
    private static final String HOME_URL = "https://chatgpt.com/";
    private static final String STATE_URLS = "tab_urls";
    private static final String STATE_ACTIVE = "active_tab";

    private final List<Tab> tabs = new ArrayList<>();
    private LinearLayout tabStrip;
    private FrameHost frameHost;
    private EditText addressBar;
    private TextView audioStatus;
    private int activeTab = -1;

    private static final class Tab {
        final WebView webView;
        String title;

        Tab(WebView webView, String title) {
            this.webView = webView;
            this.title = title;
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
        buildChrome();
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
        audioStatus = new TextView(this);
        audioStatus.setText("Central de áudio: ainda sem captura ou retransmissão.");
        audioStatus.setTextSize(12);
        audioStatus.setPadding(dp(10), dp(10), dp(10), dp(10));
        audioStatus.setGravity(Gravity.CENTER);

        root.addView(controls);
        root.addView(tabScroller);
        root.addView(frameHost, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        root.addView(audioStatus, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(root);
    }

    private void addTab(String url, boolean select) {
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

        Tab tab = new Tab(webView, "Nova aba");
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !isAllowedWebUrl(request.getUrl().toString());
            }

            @Override
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                if (tabs.indexOf(tab) == activeTab) addressBar.setText(url);
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
                renderTabs();
                if (tabs.indexOf(tab) == activeTab) addressBar.setText(url);
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
        webView.loadUrl(normalizeUrl(url));
        renderTabs();
        if (select) selectTab(tabs.size() - 1);
        else webView.setVisibility(View.GONE);
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

            Button close = new Button(this);
            close.setText("×");
            close.setTextSize(12);
            close.setMinWidth(dp(36));
            close.setContentDescription("Fechar aba " + (index + 1));
            close.setOnClickListener(v -> closeTab(index));
            item.addView(close);
            tabStrip.addView(item);
        }
    }

    private void selectTab(int index) {
        if (index < 0 || index >= tabs.size()) return;
        activeTab = index;
        for (int i = 0; i < tabs.size(); i++) {
            tabs.get(i).webView.setVisibility(i == index ? View.VISIBLE : View.GONE);
        }
        String url = tabs.get(index).webView.getUrl();
        addressBar.setText(url == null ? "" : url);
        renderTabs();
    }

    private void closeTab(int index) {
        if (index < 0 || index >= tabs.size()) return;
        Tab removed = tabs.remove(index);
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
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
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
        for (Tab tab : tabs) {
            tab.webView.stopLoading();
            tab.webView.destroy();
        }
        tabs.clear();
        super.onDestroy();
    }
}
