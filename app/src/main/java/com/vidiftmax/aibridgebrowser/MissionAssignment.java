package com.vidiftmax.aibridgebrowser;

final class MissionAssignment {
    enum Status { PENDING, RUNNING, BLOCKED, DONE }

    final String missionId;
    final String aiId;
    final int round;
    final int totalRounds;
    final String missionUrl;
    final String reportUrl;
    Status status;

    MissionAssignment(String missionId, String aiId, int round, int totalRounds,
                      String missionUrl, String reportUrl) {
        if (missionId == null || missionId.trim().isEmpty()) throw new IllegalArgumentException("missionId");
        if (aiId == null || aiId.trim().isEmpty()) throw new IllegalArgumentException("aiId");
        if (round < 1 || totalRounds < round) throw new IllegalArgumentException("round");
        if (missionUrl == null || missionUrl.trim().isEmpty()) throw new IllegalArgumentException("missionUrl");
        this.missionId = missionId;
        this.aiId = aiId;
        this.round = round;
        this.totalRounds = totalRounds;
        this.missionUrl = missionUrl;
        this.reportUrl = reportUrl == null ? "" : reportUrl;
        this.status = Status.PENDING;
    }

    String roundLabel() {
        return round + "/" + totalRounds;
    }

    boolean isComplete() {
        return status == Status.DONE;
    }
}
