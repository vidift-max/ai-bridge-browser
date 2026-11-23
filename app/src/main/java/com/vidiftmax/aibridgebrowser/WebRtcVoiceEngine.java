package com.vidiftmax.aibridgebrowser;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;

import org.webrtc.AudioSource;
import org.webrtc.AudioTrack;
import org.webrtc.DataChannel;
import org.webrtc.IceCandidate;
import org.webrtc.MediaConstraints;
import org.webrtc.MediaStream;
import org.webrtc.PeerConnection;
import org.webrtc.PeerConnectionFactory;
import org.webrtc.RtpReceiver;
import org.webrtc.RtpTransceiver;
import org.webrtc.SdpObserver;
import org.webrtc.SessionDescription;
import org.webrtc.SurfaceTextureHelper;
import org.webrtc.VideoTrack;
import org.webrtc.JavaAudioDeviceModule;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * One-to-one, audio-only WebRTC peer engine.
 *
 * Signaling transport, call authorization, microphone permission prompts and ICE server
 * provisioning remain owned by the application. No default public STUN/TURN server is used.
 */
public final class WebRtcVoiceEngine implements AutoCloseable {
    public interface Listener {
        void onLocalDescription(String type, String sdp);
        void onLocalIceCandidate(IceCandidate candidate);
        void onIceState(String state);
        void onRemoteAudioTrack(AudioTrack track);
        void onError(String code);
    }

    private final Context appContext;
    private final Listener listener;
    private final PeerConnectionFactory factory;
    private final JavaAudioDeviceModule audioDeviceModule;
    private final AudioSource audioSource;
    private final AudioTrack localAudioTrack;
    private final PeerConnection peer;
    private volatile boolean closed;

    public WebRtcVoiceEngine(Context context, List<PeerConnection.IceServer> iceServers,
                             Listener listener) {
        if (context == null || listener == null) throw new IllegalArgumentException("context_and_listener_required");
        appContext = context.getApplicationContext();
        this.listener = listener;
        if (appContext.checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED)
            throw new SecurityException("record_audio_permission_required");

        PeerConnectionFactory.initialize(
                PeerConnectionFactory.InitializationOptions.builder(appContext)
                        .createInitializationOptions());
        audioDeviceModule = JavaAudioDeviceModule.builder(appContext).createAudioDeviceModule();
        factory = PeerConnectionFactory.builder()
                .setAudioDeviceModule(audioDeviceModule)
                .createPeerConnectionFactory();

        audioSource = factory.createAudioSource(new MediaConstraints());
        localAudioTrack = factory.createAudioTrack("ai-phone-microphone", audioSource);
        localAudioTrack.setEnabled(true);

        List<PeerConnection.IceServer> configuredServers = iceServers == null
                ? Collections.emptyList() : new ArrayList<>(iceServers);
        PeerConnection.RTCConfiguration configuration =
                new PeerConnection.RTCConfiguration(configuredServers);
        configuration.sdpSemantics = PeerConnection.SdpSemantics.UNIFIED_PLAN;
        peer = factory.createPeerConnection(configuration, new PeerConnection.Observer() {
            @Override public void onSignalingChange(PeerConnection.SignalingState state) { }
            @Override public void onIceConnectionChange(PeerConnection.IceConnectionState state) {
                if (closed) return;
                listener.onIceState(state.name());
            }
            @Override public void onIceConnectionReceivingChange(boolean receiving) { }
            @Override public void onIceGatheringChange(PeerConnection.IceGatheringState state) { }
            @Override public void onIceCandidate(IceCandidate candidate) {
                if (!closed) listener.onLocalIceCandidate(candidate);
            }
            @Override public void onIceCandidatesRemoved(IceCandidate[] candidates) { }
            @Override public void onAddStream(MediaStream stream) {
                if (closed || stream == null) return;
                for (AudioTrack track : stream.audioTracks) exposeRemoteAudio(track);
            }
            @Override public void onRemoveStream(MediaStream stream) { }
            @Override public void onDataChannel(DataChannel channel) { }
            @Override public void onRenegotiationNeeded() { }
            @Override public void onAddTrack(RtpReceiver receiver, MediaStream[] streams) {
                if (receiver != null && receiver.track() instanceof AudioTrack)
                    exposeRemoteAudio((AudioTrack) receiver.track());
            }
            @Override public void onTrack(RtpTransceiver transceiver) {
                if (transceiver != null && transceiver.getReceiver() != null
                        && transceiver.getReceiver().track() instanceof AudioTrack)
                    exposeRemoteAudio((AudioTrack) transceiver.getReceiver().track());
            }
        });
        if (peer == null) {
            localAudioTrack.dispose();
            audioSource.dispose();
            factory.dispose();
            audioDeviceModule.release();
            throw new IllegalStateException("webrtc_peer_connection_unavailable");
        }
        peer.addTrack(localAudioTrack, Collections.singletonList("ai-phone-audio-stream"));
    }

    public void createOffer() {
        ensureOpen();
        peer.createOffer(new DescriptionObserver(true), audioConstraints());
    }

    public void createAnswer() {
        ensureOpen();
        peer.createAnswer(new DescriptionObserver(true), audioConstraints());
    }

    public void setRemoteDescription(String type, String sdp) {
        ensureOpen();
        SessionDescription.Type descriptionType;
        try {
            descriptionType = SessionDescription.Type.fromCanonicalForm(type);
        } catch (RuntimeException invalid) {
            listener.onError("invalid_remote_sdp_type");
            return;
        }
        if (sdp == null || sdp.trim().isEmpty() || sdp.length() > VoiceSignalPayload.MAX_SDP_CHARS) {
            listener.onError("invalid_remote_sdp");
            return;
        }
        peer.setRemoteDescription(new SdpObserver() {
            @Override public void onCreateSuccess(SessionDescription value) { }
            @Override public void onSetSuccess() { }
            @Override public void onCreateFailure(String error) { listener.onError("remote_sdp_create_failed"); }
            @Override public void onSetFailure(String error) { listener.onError("remote_sdp_rejected"); }
        }, new SessionDescription(descriptionType, sdp));
    }

    public boolean addRemoteIceCandidate(VoiceSignalPayload.IceCandidateData data) {
        ensureOpen();
        if (data == null) return false;
        return peer.addIceCandidate(new IceCandidate(
                data.sdpMid, data.sdpMLineIndex, data.candidate));
    }

    public void setMicrophoneEnabled(boolean enabled) {
        ensureOpen();
        localAudioTrack.setEnabled(enabled);
    }

    public boolean isMicrophoneEnabled() {
        return !closed && localAudioTrack.enabled();
    }

    private void exposeRemoteAudio(AudioTrack track) {
        if (track == null || closed) return;
        track.setEnabled(true);
        listener.onRemoteAudioTrack(track);
    }

    private static MediaConstraints audioConstraints() {
        MediaConstraints constraints = new MediaConstraints();
        constraints.mandatory.add(new MediaConstraints.KeyValuePair("OfferToReceiveAudio", "true"));
        constraints.mandatory.add(new MediaConstraints.KeyValuePair("OfferToReceiveVideo", "false"));
        return constraints;
    }

    private void ensureOpen() {
        if (closed) throw new IllegalStateException("webrtc_engine_closed");
    }

    @Override public synchronized void close() {
        if (closed) return;
        closed = true;
        peer.close();
        peer.dispose();
        localAudioTrack.setEnabled(false);
        localAudioTrack.dispose();
        audioSource.dispose();
        factory.dispose();
        audioDeviceModule.release();
    }

    private final class DescriptionObserver implements SdpObserver {
        private final boolean setLocal;
        DescriptionObserver(boolean setLocal) { this.setLocal = setLocal; }
        @Override public void onCreateSuccess(SessionDescription description) {
            if (closed || description == null) return;
            if (!setLocal) {
                listener.onLocalDescription(description.type.canonicalForm(), description.description);
                return;
            }
            peer.setLocalDescription(new SdpObserver() {
                @Override public void onCreateSuccess(SessionDescription ignored) { }
                @Override public void onSetSuccess() {
                    if (!closed) listener.onLocalDescription(
                            description.type.canonicalForm(), description.description);
                }
                @Override public void onCreateFailure(String error) { listener.onError("local_sdp_create_failed"); }
                @Override public void onSetFailure(String error) { listener.onError("local_sdp_rejected"); }
            }, description);
        }
        @Override public void onSetSuccess() { }
        @Override public void onCreateFailure(String error) { listener.onError("local_sdp_create_failed"); }
        @Override public void onSetFailure(String error) { listener.onError("local_sdp_rejected"); }
    }
}
