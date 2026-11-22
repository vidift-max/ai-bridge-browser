package com.vidiftmax.aibridgebrowser;

import android.app.ActivityManager;
import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Environment;
import android.os.StatFs;

import java.util.Locale;

/** Read-only device diagnostics. Does not scan Wi-Fi or read saved passwords. */
public final class WifiDeviceDiagnostics {
    private WifiDeviceDiagnostics() {}

    public static String summarize(Context context) {
        String wifi = "Wi-Fi: estado indisponível";
        ConnectivityManager manager =
                (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
        if (manager != null) {
            Network active = manager.getActiveNetwork();
            NetworkCapabilities caps = active == null ? null : manager.getNetworkCapabilities(active);
            if (caps != null && caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) {
                boolean internet = caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
                boolean validated = caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED);
                wifi = validated ? "Wi-Fi conectado · internet validada"
                        : internet ? "Wi-Fi conectado · internet ainda não validada"
                        : "Wi-Fi conectado · sem acesso à internet confirmado";
            } else {
                wifi = "Wi-Fi não conectado (ou outra rede está em uso)";
            }
        }

        ActivityManager activityManager =
                (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
        String ram = "RAM: indisponível";
        if (activityManager != null) {
            ActivityManager.MemoryInfo info = new ActivityManager.MemoryInfo();
            activityManager.getMemoryInfo(info);
            ram = String.format(Locale.US, "RAM total: %s · disponível agora: %s",
                    formatBytes(info.totalMem), formatBytes(info.availMem));
        }

        String storage = "Armazenamento: indisponível";
        try {
            StatFs stat = new StatFs(Environment.getDataDirectory().getAbsolutePath());
            storage = String.format(Locale.US, "Armazenamento interno: %s total · %s livre",
                    formatBytes(stat.getTotalBytes()), formatBytes(stat.getAvailableBytes()));
        } catch (IllegalArgumentException ignored) {
            // Keep the safe unavailable label.
        }
        return wifi + "\n" + ram + "\n" + storage
                + "\nConexão automática: o Android reconecta redes salvas e autorizadas.";
    }

    private static String formatBytes(long bytes) {
        if (bytes < 0) return "indisponível";
        double value = bytes;
        String[] units = {"B", "KB", "MB", "GB", "TB"};
        int unit = 0;
        while (value >= 1024 && unit < units.length - 1) {
            value /= 1024;
            unit++;
        }
        return String.format(Locale.US, "%.1f %s", value, units[unit]);
    }
}
