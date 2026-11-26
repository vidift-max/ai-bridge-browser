package com.vidiftmax.aibridgebrowser;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.core.content.FileProvider;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.security.cert.Certificate;
import java.util.Arrays;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * In-app updater. Only published GitHub Releases containing a strict manifest
 * and an APK signed by the already-installed application certificate are eligible.
 */
public final class UpdateCenterActivity extends Activity {
    private static final String RELEASE_API =
            "https://api.github.com/repos/vidift-max/ai-bridge-browser/releases/latest";
    private static final String PACKAGE_NAME = "com.vidiftmax.aibridgebrowser";
    private static final String MANIFEST_ASSET = "ai-bridge-update.json";
    private static final String APK_ASSET = "app-release.apk";
    private static final long MAX_APK_BYTES = 250L * 1024L * 1024L;

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    private TextView status;
    private TextView version;
    private Button checkButton;
    private Button installButton;
    private ProgressBar progress;
    private Candidate candidate;
    private File downloadedApk;

    private static final class Candidate {
        final long versionCode;
        final String versionName;
        final String notes;
        final String apkUrl;
        final String sha256;
        Candidate(long code, String name, String notes, String url, String hash) {
            this.versionCode = code;
            this.versionName = name;
            this.notes = notes;
            this.apkUrl = url;
            this.sha256 = hash;
        }
    }

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(0xFF101827);
        getWindow().setNavigationBarColor(0xFF101827);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(20), dp(24), dp(20), dp(20));
        page.setBackgroundColor(0xFF101827);

        TextView title = text("ATUALIZAÇÕES", 24, 0xFFFFFFFF, true);
        page.addView(title);
        version = text("Versão instalada: " + installedVersion(), 15, 0xFFB5C2D1, false);
        version.setPadding(0, dp(10), 0, dp(18));
        page.addView(version);

        status = text("Verifique se existe uma versão oficial mais recente.", 15, 0xFFFFFFFF, false);
        status.setPadding(0, 0, 0, dp(16));
        page.addView(status);

        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setIndeterminate(true);
        progress.setVisibility(View.GONE);
        page.addView(progress, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(5)));

        checkButton = new Button(this);
        checkButton.setText("Verificar atualizações");
        checkButton.setAllCaps(false);
        checkButton.setOnClickListener(v -> checkForUpdates());
        page.addView(checkButton, fullWidth());

        installButton = new Button(this);
        installButton.setText("Baixar e instalar atualização");
        installButton.setAllCaps(false);
        installButton.setEnabled(false);
        installButton.setOnClickListener(v -> downloadAndInstall());
        page.addView(installButton, fullWidth());

        Button back = new Button(this);
        back.setText("Voltar");
        back.setAllCaps(false);
        back.setOnClickListener(v -> finish());
        page.addView(back, fullWidth());

        TextView safety = text(
                "Somente versões publicadas e assinadas pelo mesmo certificado do aplicativo serão aceitas. " +
                "O Android poderá solicitar confirmação para instalar. Nenhuma versão de teste/debug será oferecida aqui.",
                12, 0xFFB5C2D1, false);
        safety.setPadding(0, dp(20), 0, 0);
        page.addView(safety);
        setContentView(page);
    }

    private void checkForUpdates() {
        setBusy(true, "Consultando o canal oficial de versões…");
        candidate = null;
        installButton.setEnabled(false);
        executor.execute(() -> {
            try {
                JSONObject release = new JSONObject(readUrl(RELEASE_API, 1024 * 1024));
                if (release.optBoolean("draft", true) || release.optBoolean("prerelease", true)) {
                    throw new IllegalStateException("A versão encontrada não é uma publicação estável.");
                }
                JSONArray assets = release.optJSONArray("assets");
                JSONObject manifestAsset = findAsset(assets, MANIFEST_ASSET);
                if (manifestAsset == null) {
                    throw new IllegalStateException("A publicação ainda não contém o manifesto oficial de atualização.");
                }
                String manifestUrl = manifestAsset.getString("browser_download_url");
                JSONObject manifest = new JSONObject(readUrl(manifestUrl, 128 * 1024));
                long remoteCode = manifest.getLong("versionCode");
                String remoteName = manifest.getString("versionName");
                String packageName = manifest.getString("packageName");
                String apkName = manifest.getString("apkAssetName");
                String hash = manifest.getString("sha256").toLowerCase(Locale.ROOT);
                String notes = manifest.optString("notes", release.optString("body", "Atualização oficial."));
                JSONObject apkAsset = findAsset(assets, apkName);
                if (!PACKAGE_NAME.equals(packageName) || !APK_ASSET.equals(apkName)) {
                    throw new IllegalStateException("O manifesto não corresponde a este aplicativo.");
                }
                if (!hash.matches("[a-f0-9]{64}")) {
                    throw new IllegalStateException("Hash SHA-256 ausente ou inválido.");
                }
                if (apkAsset == null) throw new IllegalStateException("APK oficial não encontrado na publicação.");
                String apkUrl = apkAsset.getString("browser_download_url");
                if (!apkUrl.startsWith("https://github.com/vidift-max/ai-bridge-browser/releases/download/")) {
                    throw new IllegalStateException("Origem do APK não permitida.");
                }
                long localCode = getPackageManager().getPackageInfo(getPackageName(), 0)
                        .getLongVersionCode();
                if (remoteCode <= localCode) {
                    main.post(() -> {
                        setBusy(false, "Você já está usando a versão mais recente (" + installedVersion() + ").");
                    });
                    return;
                }
                Candidate found = new Candidate(remoteCode, remoteName, notes, apkUrl, hash);
                main.post(() -> {
                    candidate = found;
                    setBusy(false, "Nova versão disponível: " + found.versionName +
                            " (código " + found.versionCode + ").\n\n" + found.notes);
                    installButton.setEnabled(true);
                });
            } catch (Exception error) {
                main.post(() -> setBusy(false, safeMessage(error)));
            }
        });
    }

    private void downloadAndInstall() {
        Candidate selected = candidate;
        if (selected == null) return;
        installButton.setEnabled(false);
        setBusy(true, "Baixando a atualização oficial…");
        executor.execute(() -> {
            try {
                File folder = new File(getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "updates");
                if (!folder.exists() && !folder.mkdirs()) throw new IllegalStateException("Não foi possível criar a pasta de atualização.");
                File apk = new File(folder, APK_ASSET);
                download(selected.apkUrl, apk);
                String actualHash = sha256(apk);
                if (!selected.sha256.equals(actualHash)) {
                    apk.delete();
                    throw new SecurityException("O hash do APK não confere. Instalação bloqueada.");
                }
                verifyPackageAndCertificate(apk);
                main.post(() -> {
                    downloadedApk = apk;
                    setBusy(false, "Download e verificações concluídos. O APK corresponde ao aplicativo instalado.");
                    installButton.setEnabled(true);
                    installButton.setText("Instalar versão " + selected.versionName);
                    installButton.setOnClickListener(v -> requestInstall(apk));
                });
            } catch (Exception error) {
                main.post(() -> {
                    setBusy(false, safeMessage(error));
                    installButton.setEnabled(candidate != null);
                });
            }
        });
    }

    private void requestInstall(File apk) {
        if (android.os.Build.VERSION.SDK_INT >= 26 && !getPackageManager().canRequestPackageInstalls()) {
            Intent settings = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                    Uri.parse("package:" + getPackageName()));
            startActivity(settings);
            Toast.makeText(this, "Autorize a instalação para este app e volte para concluir.", Toast.LENGTH_LONG).show();
            return;
        }
        try {
            Uri uri = FileProvider.getUriForFile(this, getPackageName() + ".fileprovider", apk);
            Intent install = new Intent(Intent.ACTION_VIEW);
            install.setDataAndType(uri, "application/vnd.android.package-archive");
            install.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(install);
        } catch (Exception error) {
            status.setText("Não foi possível abrir o instalador Android: " + safeMessage(error));
        }
    }

    private void verifyPackageAndCertificate(File apk) throws Exception {
        PackageManager pm = getPackageManager();
        PackageInfo installed = pm.getPackageInfo(getPackageName(), PackageManager.GET_SIGNING_CERTIFICATES);
        PackageInfo downloaded = pm.getPackageArchiveInfo(apk.getAbsolutePath(), PackageManager.GET_SIGNING_CERTIFICATES);
        if (downloaded == null || !PACKAGE_NAME.equals(downloaded.packageName)) {
            throw new SecurityException("O APK não pertence ao AI Bridge Browser.");
        }
        if (installed.signingInfo == null || downloaded.signingInfo == null) {
            throw new SecurityException("Não foi possível verificar a assinatura do APK.");
        }
        Certificate[] current = installed.signingInfo.getApkContentsSigners();
        Certificate[] incoming = downloaded.signingInfo.getApkContentsSigners();
        if (current == null || incoming == null || current.length == 0 ||
                current.length != incoming.length) {
            throw new SecurityException("A assinatura do APK não corresponde à instalação atual.");
        }
        for (int i = 0; i < current.length; i++) {
            if (!Arrays.equals(current[i].getEncoded(), incoming[i].getEncoded())) {
                throw new SecurityException("Certificado diferente. Atualização bloqueada para proteger seus dados.");
            }
        }
    }

    private JSONObject findAsset(JSONArray assets, String name) {
        if (assets == null) return null;
        for (int i = 0; i < assets.length(); i++) {
            JSONObject asset = assets.optJSONObject(i);
            if (asset != null && name.equals(asset.optString("name"))) return asset;
        }
        return null;
    }

    private String readUrl(String address, int maxBytes) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(address).openConnection();
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(20000);
        connection.setInstanceFollowRedirects(true);
        connection.setRequestProperty("Accept", "application/vnd.github+json");
        connection.setRequestProperty("User-Agent", "AI-Bridge-Browser-Updater");
        try {
            int code = connection.getResponseCode();
            if (code != 200) throw new IllegalStateException("Canal de atualizações respondeu HTTP " + code + ".");
            try (InputStream input = connection.getInputStream();
                 ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[8192];
                int count, total = 0;
                while ((count = input.read(buffer)) != -1) {
                    total += count;
                    if (total > maxBytes) throw new IllegalStateException("Resposta do canal excedeu o limite permitido.");
                    output.write(buffer, 0, count);
                }
                return output.toString("UTF-8");
            }
        } finally {
            connection.disconnect();
        }
    }

    private void download(String address, File destination) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(address).openConnection();
        connection.setConnectTimeout(20000);
        connection.setReadTimeout(30000);
        connection.setInstanceFollowRedirects(true);
        connection.setRequestProperty("User-Agent", "AI-Bridge-Browser-Updater");
        try {
            int code = connection.getResponseCode();
            if (code != 200) throw new IllegalStateException("Download respondeu HTTP " + code + ".");
            long declared = connection.getContentLengthLong();
            if (declared > MAX_APK_BYTES) throw new IllegalStateException("APK excede o tamanho máximo permitido.");
            try (InputStream input = new BufferedInputStream(connection.getInputStream());
                 FileOutputStream output = new FileOutputStream(destination)) {
                byte[] buffer = new byte[32768];
                int count;
                long total = 0;
                while ((count = input.read(buffer)) != -1) {
                    total += count;
                    if (total > MAX_APK_BYTES) throw new IllegalStateException("Download excedeu o tamanho máximo permitido.");
                    output.write(buffer, 0, count);
                }
                output.getFD().sync();
                if (declared >= 0 && total != declared) throw new IllegalStateException("Download incompleto.");
            }
        } catch (Exception error) {
            destination.delete();
            throw error;
        } finally {
            connection.disconnect();
        }
    }

    private String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream input = new BufferedInputStream(new java.io.FileInputStream(file))) {
            byte[] buffer = new byte[32768];
            int count;
            while ((count = input.read(buffer)) != -1) digest.update(buffer, 0, count);
        }
        StringBuilder result = new StringBuilder();
        for (byte value : digest.digest()) result.append(String.format(Locale.ROOT, "%02x", value & 0xff));
        return result.toString();
    }

    private String installedVersion() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            return info.versionName + " (" + info.getLongVersionCode() + ")";
        } catch (Exception ignored) { return "desconhecida"; }
    }

    private void setBusy(boolean busy, String message) {
        status.setText(message);
        progress.setVisibility(busy ? View.VISIBLE : View.GONE);
        checkButton.setEnabled(!busy);
        if (busy) installButton.setEnabled(false);
    }

    private String safeMessage(Exception error) {
        String message = error.getMessage();
        if (message == null || message.trim().isEmpty()) return "Não foi possível verificar a atualização. Tente novamente.";
        return message;
    }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        if (bold) view.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
        return view;
    }

    private LinearLayout.LayoutParams fullWidth() {
        return new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    @Override protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }
}
