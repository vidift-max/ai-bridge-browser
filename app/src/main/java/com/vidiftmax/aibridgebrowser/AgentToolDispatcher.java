package com.vidiftmax.aibridgebrowser;

import org.json.JSONObject;
import java.util.HashMap;
import java.util.Map;

/**
 * Safe bridge between GPT-6 mission dispatch and the authenticated Tool Hub client.
 * It never invents agent identity: the bound client identity must equal the mission identity.
 */
final class AgentToolDispatcher {
    interface ToolInvoker {
        JSONObject invoke(String toolId, String toolVersion, JSONObject input) throws Exception;
    }

    private static final String[] TOOL_IDS = {
            "duration_timer", "recipe_scaler", "quiz_engine", "svg_chart", "link_card"
    };

    private final AgentCoordinator coordinator;
    private final Map<String, ToolInvoker> invokers = new HashMap<>();

    AgentToolDispatcher(AgentCoordinator coordinator) {
        if (coordinator == null) throw new IllegalArgumentException("coordinator_required");
        this.coordinator = coordinator;
    }

    boolean bindClient(MessengerHttpClient client) {
        if (client == null) return false;
        String aiId = client.getAiId();
        if (!AgentRosterPolicy.isProviderSessionAllowedForCurrentMission(aiId)) return false;
        invokers.put(aiId, client::invokeTool);
        return true;
    }

    boolean bindInvoker(String aiId, ToolInvoker invoker) {
        if (!AgentRosterPolicy.isProviderSessionAllowedForCurrentMission(aiId) || invoker == null)
            return false;
        invokers.put(aiId, invoker);
        return true;
    }

    JSONObject dispatch(String missionId, String toolId, String toolVersion, JSONObject input) throws Exception {
        AgentMissionQueue.Mission mission = findRunningMission(missionId);
        if (mission == null) throw new IllegalStateException("mission_not_running");
        if (!isSupportedTool(toolId)) throw new IllegalArgumentException("unsupported_tool_id");
        if (!"1.0.0".equals(toolVersion)) throw new IllegalArgumentException("unsupported_tool_version");
        ToolInvoker invoker = invokers.get(mission.aiId);
        if (invoker == null) throw new IllegalStateException("agent_tool_client_not_bound");
        return invoker.invoke(toolId, toolVersion, input);
    }

    boolean hasBoundClient(String aiId) { return invokers.containsKey(aiId); }

    private AgentMissionQueue.Mission findRunningMission(String missionId) {
        for (AgentMissionQueue.Mission mission : coordinator.missions()) {
            if (mission.missionId.equals(missionId) && mission.state == AgentMissionQueue.State.RUNNING)
                return mission;
        }
        return null;
    }

    private static boolean isSupportedTool(String toolId) {
        if (toolId == null) return false;
        for (String candidate : TOOL_IDS) if (candidate.equals(toolId)) return true;
        return false;
    }
}
