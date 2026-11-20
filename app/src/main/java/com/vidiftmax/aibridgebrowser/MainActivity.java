package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.KeyEvent;
import android.view.inputmethod.EditorInfo;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
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

public final class MainActivity extends Activity {
    private static final int MAX_TABS = 5;
    private static final String HOME_URL = "https://chatgpt.com/";

    private final List<Tab> tabs = new ArrayList<>();
    private LinearLayout root;
    private LinearLayout tabStrip;
    private FrameHost frameHost;
    private EditText addressBar;
    private int activeTab = -1;

    private static final class Tab {
        final WebView webView;
        final String label;

        Tab(WebView webView, String label) {
            this.webView = webView;
            this.label = label;
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
        addTab(HOME_URL);
    }

    private void buildChrome() {
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        LinearLayout controls = new LinearLayout(this);
        controls.setGravity(Gravity.CENTER_VERTICAL);
        controls.setPadding(8, 8, 8, 8);

        addressBar = new EditText(this);
        addressBar.setSingleLine(true);
        addressBar.setHint("Digite um endereço HTTPS");
        addressBar.setImeOptions(EditorInfo.IME_ACTION_GO);
        controls.addView(addressBar, new LinearLayout.LayoutParams(0, dp(48), 1));

        Button go = new Button(this);
        go.setText("Abrir");
        controls.addView(go);
        go.setOnClickListener(v -> navigateCurrent());

        Button add = new Button(this);
        add.setText("+");
        controls.addView(add);
        add.setOnClickListener(v -> addTab(HOME_URL));

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
        root.addView(controls);
        root.addView(tabScroller);
        root.addView(frameHost, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

        setContentView(root);
    }

    private void addTab(String url) {
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

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String scheme = request.getUrl().getScheme();
                return !("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme));
            }
        });
        // Microphone/camera permissions remain denied until an explicit permission flow is implemented.
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(android.webkit.PermissionRequest request) {
                request.deny();
            }
        });

        frameHost.addView(webView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        tabs.add(new Tab(webView, "Aba " + tabs.size()));
        webView.loadUrl(normalizeUrl(url));
        renderTabs();
        selectTab(tabs.size() - 1);
    }

    private String normalizeUrl(String value) {
        String trimmed = value == null ? "" : value.trim();
        if (trimmed.isEmpty()) return HOME_URL;
        if (!trimmed.contains("://")) trimmed = "https://" + trimmed;
        if (!trimmed.startsWith("https://") && !trimmed.startsWith("http://")) return HOME_URL;
        return trimmed;
    }

    private void navigateCurrent() {
        if (activeTab < 0 || activeTab >= tabs.size()) return;
        String url = normalizeUrl(addressBar.getText().toString());
        tabs.get(activeTab).webView.loadUrl(url);
    }

    private void renderTabs() {
        tabStrip.removeAllViews();
        for (int i = 0; i < tabs.size(); i++) {
            final int index = i;
            Button tabButton = new Button(this);
            tabButton.setText((i == activeTab ? "● " : "") + "Aba " + (i + 1));
            tabButton.setOnClickListener(v -> selectTab(index));
            tabStrip.addView(tabButton);
        }
    }

    private void selectTab(int index) {
        if (index < 0 || index >= tabs.size()) return;
        activeTab = index;
        for (int i = 0; i < tabs.size(); i++) {
            tabs.get(i).webView.setVisibility(i == index ? View.VISIBLE : View.GONE);
        }
        addressBar.setText(tabs.get(index).webView.getUrl());
        renderTabs();
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    @Override
    public void onBackPressed() {
        if (activeTab >= 0) {
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
