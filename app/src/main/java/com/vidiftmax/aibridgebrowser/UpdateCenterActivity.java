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
import android.content.pm.Signature;
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
    private volatile boolean destroyed;

    private static final class Candidate {
        final long versionCode;
        final String versionName;
        final String notes;
        final String apkUrl;
        final String sha256;
        final long apkBytes;
        Candidate(long code, String name, String notes, String url, String hash, long bytes) {
            this.versionCode = code;
            this.versionName = name;
            this.notes = notes;
            this.apkUrl = url;
            this.sha256 = hash;
            this.apkBytes = bytes;
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
        progress.setMax(1000);
        progress.setProgress(0);
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
        clearDownloadedCandidate();
        resetInstallAction();
        installButton.setEnabled(false);
        executor.execute(() -> {
            try {
                JSONObject release = new JSONObject(readUrl(RELEASE_API, 1024 * 1024));
                if (!UpdateReleasePolicy.isStableRelease(release)) {
                    throw new IllegalStateException("A versão encontrada não é uma publicação estável ou possui tag inválida.");
                }
                String releaseTag = release.getString("tag_name");
                JSONArray assets = release.optJSONArray("assets");
                String manifestUrl = UpdateReleasePolicy.findUniqueAssetUrl(
                        assets, MANIFEST_ASSET, releaseTag);
                if (manifestUrl == null) {
                    throw new SecurityException("Manifesto ausente, duplicado ou fora da Release oficial esperada.");
                }
                JSONObject manifest = new JSONObject(readUrl(manifestUrl, 128 * 1024));
                if (!UpdateManifestPolicy.isManifestShapeEligible(manifest)) {
                    throw new SecurityException("Manifesto fora do contrato estrito. Atualização bloqueada.");
                }
                long remoteCode = manifest.getLong("versionCode");
                String remoteName = manifest.getString("versionName");
                if (remoteName.trim().isEmpty()) throw new SecurityException("Nome da versão ausente.");
                String packageName = manifest.getString("packageName");
                String apkName = manifest.getString("apkAssetName");
                String hash = manifest.getString("sha256").toLowerCase(Locale.ROOT);
                String notes = manifest.optString("notes", release.optString("body", "Atualização oficial."));
                UpdateReleasePolicy.AssetMetadata apkAsset = UpdateReleasePolicy.findUniqueAsset(
                        assets, apkName, releaseTag);
                if (apkAsset == null || apkAsset.sizeBytes > MAX_APK_BYTES) {
                    throw new SecurityException("APK ausente, duplicado, excessivo ou fora da Release oficial esperada.");
                }
                String apkUrl = apkAsset.url;
                long localCode = getPackageManager().getPackageInfo(getPackageName(), 0)
                        .getLongVersionCode();
                if (remoteCode <= localCode) {
                    postUi(() -> {
                        setBusy(false, "Você já está usando a versão mais recente (" + installedVersion() + ").");
                    });
                    return;
                }
                if (!UpdateManifestPolicy.isEligible(remoteCode, localCode, packageName,
                        PACKAGE_NAME, apkName, APK_ASSET, hash, apkUrl)) {
                    throw new SecurityException("Manifesto inválido, versão não superior ou origem não permitida.");
                }
                Candidate found = new Candidate(remoteCode, remoteName, notes, apkUrl, hash,
                        apkAsset.sizeBytes);
                postUi(() -> {
                    candidate = found;
                    setBusy(false, "Nova versão disponível: " + found.versionName +
                            " (código " + found.versionCode + ").\n\n" + found.notes);
                    installButton.setEnabled(true);
                    resetInstallAction();
                });
            } catch (Exception error) {
                postUi(() -> setBusy(false, safeMessage(error)));
            }
        });
    }

    private void downloadAndInstall() {
        Candidate selected = candidate;
        if (selected == null) return;
        installButton.setEnabled(false);
        resetInstallAction();
        setBusy(true, "Baixando a atualização oficial…");
        executor.execute(() -> {
            File partial = null;
            try {
                File downloads = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
                if (downloads == null) throw new IllegalStateException("Armazenamento do aplicativo indisponível.");
                File folder = new File(downloads, "updates");
                if (!folder.exists() && !folder.mkdirs()) throw new IllegalStateException("Não foi possível criar a pasta de atualização.");
                File canonicalFolder = folder.getCanonicalFile();
                if (!canonicalFolder.isDirectory()) throw new SecurityException("Pasta privada de atualização inválida.");
                partial = new File(canonicalFolder, APK_ASSET + ".part");
                File apk = new File(canonicalFolder, APK_ASSET);
                if (!partial.getCanonicalFile().getParentFile().equals(canonicalFolder) ||
                        !apk.getCanonicalFile().getParentFile().equals(canonicalFolder)) {
                    throw new SecurityException("Caminho de atualização fora da pasta privada permitida.");
                }
                if (partial.exists() && !partial.delete()) throw new IllegalStateException("Não foi possível remover download parcial anterior.");
                download(selected.apkUrl, partial, selected.apkBytes);
                String actualHash = sha256(partial);
                if (!selected.sha256.equals(actualHash)) {
                    throw new SecurityException("O hash do APK não confere. Instalação bloqueada.");
                }
                verifyPackageAndCertificate(partial, selected);
                if (apk.exists() && !apk.delete()) throw new IllegalStateException("Não foi possível substituir o APK verificado anterior.");
                if (!partial.renameTo(apk)) throw new IllegalStateException("Não foi possível finalizar o APK verificado.");
                partial = null;
                postUi(() -> {
                    downloadedApk = apk;
                    setBusy(false, "Download e verificações concluídos. O APK corresponde ao aplicativo instalado.");
                    installButton.setEnabled(true);
                    installButton.setText("Instalar versão " + selected.versionName);
                    installButton.setOnClickListener(v -> requestInstall(apk));
                });
            } catch (Exception error) {
                if (partial != null && partial.exists()) partial.delete();
                postUi(() -> {
                    clearDownloadedCandidate();
                    resetInstallAction();
                    setBusy(false, safeMessage(error));
                    installButton.setEnabled(candidate != null);
                });
            }
        });
    }

    /** Drop any previously verified file when a new check/download starts. */
    private void clearDownloadedCandidate() {
        File previous = downloadedApk;
        downloadedApk = null;
        if (previous != null && previous.isFile()) {
            previous.setWritable(true, true);
            previous.delete();
        }
    }

    /** Always restore the download action before accepting a new candidate. */
    private void resetInstallAction() {
        installButton.setText("Baixar e instalar atualização");
        installButton.setOnClickListener(v -> downloadAndInstall());
    }

    /** Deliver UI work only while this Activity is still alive. */
    private void postUi(Runnable action) {
        main.post(() -> {
            if (UpdaterUiPolicy.shouldDeliver(destroyed, isFinishing(), isDestroyed())) action.run();
        });
    }

    private void requestInstall(File apk) {
        Candidate expected = candidate;
        File downloads = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
        File allowedDirectory = downloads == null ? null : new File(downloads, "updates");
        try {
            if (expected == null || apk == null || apk != downloadedApk ||
                    !UpdateInstallPolicy.isExpectedVerifiedApk(apk, downloadedApk,
                            allowedDirectory, APK_ASSET, expected.apkBytes, MAX_APK_BYTES)) {
                throw new SecurityException("O arquivo não é o APK verificado desta atualização.");
            }
        } catch (Exception error) {
            clearDownloadedCandidate();
            resetInstallAction();
            installButton.setEnabled(candidate != null);
            status.setText("Instalação bloqueada: " + safeMessage(error));
            return;
        }
        installButton.setEnabled(false);
        setBusy(true, "Revalidando o APK antes de abrir o instalador Android…");
        executor.execute(() -> {
            try {
                if (!UpdateInstallPolicy.isExpectedVerifiedApk(apk, downloadedApk,
                        allowedDirectory, APK_ASSET, expected.apkBytes, MAX_APK_BYTES)) {
                    throw new SecurityException("O tamanho ou caminho do APK mudou antes da instalação. Baixe novamente.");
                }
                if (!expected.sha256.equals(sha256(apk))) {
                    throw new SecurityException("O APK foi alterado depois da verificação. Baixe novamente.");
                }
                verifyPackageAndCertificate(apk, expected);
                if (!UpdateInstallPolicy.lockForInstallerHandoff(apk, downloadedApk,
                        allowedDirectory, APK_ASSET, expected.apkBytes, MAX_APK_BYTES)) {
                    throw new SecurityException("Não foi possível bloquear o APK verificado contra gravação antes da instalação.");
                }
                if (!expected.sha256.equals(sha256(apk))) {
                    throw new SecurityException("O APK mudou durante o bloqueio de escrita. Baixe novamente.");
                }
                postUi(() -> {
                    setBusy(false, "APK verificado novamente. Aguardando confirmação do Android.");
                    installButton.setEnabled(true);
                    openAndroidInstaller(apk);
                });
            } catch (Exception error) {
                postUi(() -> {
                    clearDownloadedCandidate();
                    resetInstallAction();
                    setBusy(false, "Instalação bloqueada: " + safeMessage(error));
                    installButton.setEnabled(candidate != null);
                });
            }
        });
    }

    private void openAndroidInstaller(File apk) {
        try {
            File downloads = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
            File allowedDirectory = downloads == null ? null : new File(downloads, "updates");
            Candidate expected = candidate;
            if (expected == null || apk == null || apk != downloadedApk ||
                    !UpdateInstallPolicy.isLockedInstallerHandoff(apk, downloadedApk,
                            allowedDirectory, APK_ASSET, expected.apkBytes, MAX_APK_BYTES)) {
                throw new SecurityException("O APK não está bloqueado ou não corresponde mais ao arquivo verificado.");
            }
        } catch (Exception error) {
            clearDownloadedCandidate();
            resetInstallAction();
            installButton.setEnabled(candidate != null);
            status.setText("Instalação bloqueada: " + safeMessage(error));
            return;
        }
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
            if (!InstallerIntentPolicy.isSafeHandoff(uri.toString(),
                    getPackageName() + ".fileprovider", install.getType(), install.getFlags())) {
                throw new SecurityException("Permissões ou URI do instalador fora da política permitida.");
            }
            startActivity(install);
        } catch (Exception error) {
            status.setText("Não foi possível abrir o instalador Android: " + safeMessage(error));
        }
    }

    private void verifyPackageAndCertificate(File apk, Candidate expected) throws Exception {
        PackageManager pm = getPackageManager();
        PackageInfo installed = pm.getPackageInfo(getPackageName(), PackageManager.GET_SIGNING_CERTIFICATES);
        PackageInfo downloaded = pm.getPackageArchiveInfo(apk.getAbsolutePath(), PackageManager.GET_SIGNING_CERTIFICATES);
        if (downloaded == null) {
            throw new SecurityException("Não foi possível ler a identidade do APK baixado.");
        }
        if (downloaded.getLongVersionCode() != expected.versionCode ||
                !expected.versionName.equals(downloaded.versionName)) {
            throw new SecurityException("A versão interna do APK não corresponde ao manifesto. Instalação bloqueada.");
        }
        if (installed.signingInfo == null || downloaded.signingInfo == null) {
            throw new SecurityException("Não foi possível verificar a assinatura do APK.");
        }
        Signature[] current = installed.signingInfo.getApkContentsSigners();
        Signature[] incoming = downloaded.signingInfo.getApkContentsSigners();
        if (current == null || incoming == null || current.length == 0 ||
                current.length != incoming.length) {
            throw new SecurityException("A assinatura do APK não corresponde à instalação atual.");
        }
        byte[][] installedSignerBytes = new byte[current.length][];
        byte[][] incomingSignerBytes = new byte[incoming.length][];
        for (int i = 0; i < current.length; i++) {
            if (current[i] == null) throw new SecurityException("Assinatura instalada inválida.");
            installedSignerBytes[i] = current[i].toByteArray();
        }
        for (int i = 0; i < incoming.length; i++) {
            if (incoming[i] == null) throw new SecurityException("Assinatura baixada inválida.");
            incomingSignerBytes[i] = incoming[i].toByteArray();
        }
        boolean allSignersMatched = SigningCertificatePolicy.areSameSignerSets(
                installedSignerBytes, incomingSignerBytes);
        if (!UpdateInstallPolicy.isSameApplicationIdentity(
                PACKAGE_NAME, downloaded.packageName, allSignersMatched)) {
            throw new SecurityException("Pacote ou certificado diferente. Atualização bloqueada para proteger seus dados.");
        }
    }

    private String readUrl(String address, int maxBytes) throws Exception {
        HttpURLConnection connection = openValidatedConnection(address, 15000, 20000,
                "application/vnd.github+json");
        try {
            int code = connection.getResponseCode();
            if (code == 404 && RELEASE_API.equals(address)) {
                throw new IllegalStateException("Ainda não existe uma versão oficial publicada. A área de atualizações já está preparada.");
            }
            if (code != 200) throw new IllegalStateException("Canal de atualizações respondeu HTTP " + code + ".");
            requireHttpsRedirect(connection);
            try (InputStream input = connection.getInputStream();
                 ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[8192];
                int count, total = 0;
                while ((count = input.read(buffer)) != -1) {
                    if (destroyed || Thread.currentThread().isInterrupted())
                        throw new InterruptedException("Atualização cancelada porque a tela foi encerrada.");
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

    private void download(String address, File destination, long expectedAssetBytes) throws Exception {
        if (expectedAssetBytes <= 0 || expectedAssetBytes > MAX_APK_BYTES) {
            throw new SecurityException("Tamanho anunciado do APK fora do limite permitido.");
        }
        HttpURLConnection connection = openValidatedConnection(address, 20000, 30000, null);
        try {
            int code = connection.getResponseCode();
            if (code != 200) throw new IllegalStateException("Download respondeu HTTP " + code + ".");
            requireHttpsRedirect(connection);
            long declared = connection.getContentLengthLong();
            if (declared > MAX_APK_BYTES || (declared != -1 && declared != expectedAssetBytes)) {
                throw new IllegalStateException("Tamanho HTTP não corresponde ao asset oficial da Release.");
            }
            postUi(() -> {
                progress.setIndeterminate(declared <= 0);
                progress.setProgress(0);
                status.setText(declared > 0 ? "Baixando atualização: 0%" : "Baixando atualização…");
            });
            try (InputStream input = new BufferedInputStream(connection.getInputStream());
                 FileOutputStream output = new FileOutputStream(destination)) {
                byte[] buffer = new byte[32768];
                int count;
                long total = 0;
                int lastReported = -1;
                while ((count = input.read(buffer)) != -1) {
                    if (destroyed || Thread.currentThread().isInterrupted())
                        throw new InterruptedException("Download cancelado porque a tela foi encerrada.");
                    total += count;
                    if (total > MAX_APK_BYTES) throw new IllegalStateException("Download excedeu o tamanho máximo permitido.");
                    output.write(buffer, 0, count);
                    if (declared > 0) {
                        int percent = DownloadProgressPolicy.percent(total, declared, MAX_APK_BYTES);
                        if (percent < 0) throw new IllegalStateException("Não foi possível calcular o progresso do download.");
                        if (percent != lastReported) {
                            lastReported = percent;
                            final int completed = percent;
                            postUi(() -> {
                                progress.setProgress(completed * 10);
                                status.setText("Baixando atualização: " + completed + "%");
                            });
                        }
                    }
                }
                output.getFD().sync();
                if (!UpdaterDownloadPolicy.isExpectedAssetLength(
                        declared, total, expectedAssetBytes, MAX_APK_BYTES)) {
                    throw new IllegalStateException("Download incompleto ou diferente do tamanho anunciado pela Release.");
                }
                postUi(() -> {
                    progress.setIndeterminate(false);
                    progress.setProgress(1000);
                    status.setText("Download concluído. Verificando integridade e assinatura…");
                });
            }
        } catch (Exception error) {
            destination.delete();
            throw error;
        } finally {
            connection.disconnect();
        }
    }

    /**
     * Follows redirects manually so every intermediate hop is checked before
     * another network request is made. Only the fixed release API or an exact
     * official release asset may be used as the initial URL.
     */
    private HttpURLConnection openValidatedConnection(String address, int connectTimeout,
            int readTimeout, String accept) throws Exception {
        if (!(RELEASE_API.equals(address) || UpdateUrlPolicy.isOfficialReleaseAssetUrl(address))) {
            throw new SecurityException("URL inicial fora do canal oficial de atualizações.");
        }
        URL current = new URL(address);
        int redirectsFollowed = 0;
        while (true) {
            HttpURLConnection connection = (HttpURLConnection) current.openConnection();
            connection.setConnectTimeout(connectTimeout);
            connection.setReadTimeout(readTimeout);
            connection.setInstanceFollowRedirects(false);
            connection.setRequestProperty("User-Agent", "AI-Bridge-Browser-Updater");
            if (accept != null) connection.setRequestProperty("Accept", accept);
            int code;
            try {
                code = connection.getResponseCode();
            } catch (Exception error) {
                connection.disconnect();
                throw error;
            }
            if (!UpdateRedirectPolicy.isRedirectStatus(code)) return connection;
            String next = UpdateRedirectPolicy.resolveRedirectUrl(current.toString(),
                    connection.getHeaderField("Location"), redirectsFollowed, 5);
            connection.disconnect();
            if (next == null) {
                throw new SecurityException("Redirecionamento ausente, excessivo ou para origem não autorizada.");
            }
            current = new URL(next);
            redirectsFollowed++;
        }
    }

    private void requireHttpsRedirect(HttpURLConnection connection) {
        if (connection == null ||
                !UpdateUrlPolicy.isAllowedRedirectUrl(connection.getURL().toString())) {
            throw new SecurityException("Redirecionamento para origem não autorizada.");
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
        if (busy) {
            progress.setIndeterminate(true);
            progress.setProgress(0);
        }
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
        destroyed = true;
        executor.shutdownNow();
        super.onDestroy();
    }
}
