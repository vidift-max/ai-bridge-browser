import java.io.File

plugins {
    id("com.android.application")
}

android {
    namespace = "com.vidiftmax.aibridgebrowser"
    compileSdk = 37

    val releaseKeystorePath = System.getenv("AI_PHONE_RELEASE_KEYSTORE_PATH")
    val releaseStorePassword = System.getenv("AI_PHONE_RELEASE_STORE_PASSWORD")
    val releaseKeyAlias = System.getenv("AI_PHONE_RELEASE_KEY_ALIAS")
    val releaseKeyPassword = System.getenv("AI_PHONE_RELEASE_KEY_PASSWORD")
    val releaseSigningReady = !releaseKeystorePath.isNullOrBlank()
        && File(releaseKeystorePath).isFile
        && !releaseStorePassword.isNullOrBlank()
        && !releaseKeyAlias.isNullOrBlank()
        && !releaseKeyPassword.isNullOrBlank()

    signingConfigs {
        create("release") {
            if (releaseSigningReady) {
                storeFile = File(releaseKeystorePath!!)
                storePassword = releaseStorePassword
                keyAlias = releaseKeyAlias
                keyPassword = releaseKeyPassword
            }
        }
    }

    defaultConfig {
        applicationId = "com.vidiftmax.aibridgebrowser"
        minSdk = 29
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation("androidx.core:core:1.17.0")
    implementation("androidx.webkit:webkit:1.18.0")
    testImplementation("junit:junit:4.13.2")
}
