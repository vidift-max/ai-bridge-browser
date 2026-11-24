/* AI Bridge local voice controls.
 * Dictation is enabled only when the browser explicitly confirms local processing.
 * No install/download fallback and no automatic microphone activation.
 */
(function (root) {
  "use strict";

  var LANG = "pt-BR";

  function recognitionConstructor() {
    return root.SpeechRecognition || root.webkitSpeechRecognition || null;
  }

  async function inspect() {
    var Recognition = recognitionConstructor();
    var localRecognitionAvailable = false;
    var reason = "LOCAL_SPEECH_RECOGNITION_UNAVAILABLE";
    if (Recognition && typeof Recognition.available === "function") {
      try {
        var availability = await Recognition.available({
          langs: [LANG],
          processLocally: true
        });
        localRecognitionAvailable = availability === true || availability === "available";
        reason = localRecognitionAvailable ? null : "LOCAL_LANGUAGE_PACK_NOT_AVAILABLE";
      } catch (_) {
        reason = "LOCAL_RECOGNITION_CHECK_FAILED";
      }
    }
    var synthesisAvailable = !!(root.speechSynthesis &&
      typeof root.speechSynthesis.speak === "function" &&
      typeof root.SpeechSynthesisUtterance === "function");
    return Object.freeze({
      dictationAvailable: localRecognitionAvailable,
      recognitionApiAvailable: !!Recognition,
      synthesisAvailable: synthesisAvailable,
      dictationReason: reason,
      language: LANG
    });
  }

  function createController(onStatus) {
    var activeRecognition = null;
    var activeUtterance = null;
    var stoppedByUser = false;

    function status(message) {
      if (typeof onStatus === "function") onStatus(message);
    }

    async function startDictation(textarea) {
      if (!textarea || typeof textarea.value !== "string") {
        throw new Error("DICTATION_TARGET_REQUIRED");
      }
      if (activeRecognition) throw new Error("DICTATION_ALREADY_ACTIVE");
      var capability = await inspect();
      if (!capability.dictationAvailable) {
        throw new Error(capability.dictationReason || "LOCAL_DICTATION_UNAVAILABLE");
      }
      var Recognition = recognitionConstructor();
      var recognition = new Recognition();
      if (!("processLocally" in recognition)) {
        throw new Error("LOCAL_PROCESSING_FLAG_UNSUPPORTED");
      }
      recognition.lang = LANG;
      recognition.processLocally = true;
      recognition.continuous = false;
      recognition.interimResults = true;
      stoppedByUser = false;
      activeRecognition = recognition;
      recognition.onstart = function () { status("Ditado local ativo. Fale agora."); };
      recognition.onresult = function (event) {
        var finalText = "";
        var interimText = "";
        for (var i = event.resultIndex || 0; i < event.results.length; i += 1) {
          var result = event.results[i];
          var transcript = result && result[0] ? result[0].transcript : "";
          if (result.isFinal) finalText += transcript;
          else interimText += transcript;
        }
        if (finalText) {
          var separator = textarea.value && !/\\s$/.test(textarea.value) ? " " : "";
          textarea.value += separator + finalText.trim();
          textarea.dispatchEvent(new Event("input", { bubbles: true }));
        }
        if (interimText) status("Ouvindo: " + interimText);
      };
      recognition.onerror = function (event) {
        activeRecognition = null;
        status("Ditado interrompido: " + (event.error || "erro do navegador"));
      };
      recognition.onend = function () {
        activeRecognition = null;
        if (!stoppedByUser) status("Ditado encerrado.");
      };
      try {
        recognition.start();
      } catch (error) {
        activeRecognition = null;
        throw error;
      }
      return true;
    }

    function stopDictation() {
      if (!activeRecognition) return false;
      stoppedByUser = true;
      var current = activeRecognition;
      activeRecognition = null;
      try { current.stop(); } catch (_) {}
      status("Ditado parado.");
      return true;
    }

    function speak(text) {
      var cleanText = typeof text === "string" ? text.trim() : "";
      if (!cleanText) throw new Error("SPEECH_TEXT_REQUIRED");
      if (!root.speechSynthesis || typeof root.speechSynthesis.speak !== "function" ||
          typeof root.SpeechSynthesisUtterance !== "function") {
        throw new Error("SPEECH_SYNTHESIS_UNAVAILABLE");
      }
      root.speechSynthesis.cancel();
      var utterance = new root.SpeechSynthesisUtterance(cleanText);
      utterance.lang = LANG;
      utterance.onstart = function () { status("Leitura em voz alta."); };
      utterance.onend = function () { activeUtterance = null; status("Leitura concluída."); };
      utterance.onerror = function () { activeUtterance = null; status("Leitura interrompida pelo navegador."); };
      activeUtterance = utterance;
      root.speechSynthesis.speak(utterance);
      return true;
    }

    function stopSpeech() {
      if (!root.speechSynthesis || typeof root.speechSynthesis.cancel !== "function") return false;
      root.speechSynthesis.cancel();
      activeUtterance = null;
      status("Leitura parada.");
      return true;
    }

    function stopAll() {
      stopDictation();
      stopSpeech();
    }

    return Object.freeze({
      startDictation: startDictation,
      stopDictation: stopDictation,
      speak: speak,
      stopSpeech: stopSpeech,
      stopAll: stopAll
    });
  }

  root.AIBridgeVoice = Object.freeze({
    inspect: inspect,
    createController: createController
  });
})(typeof window !== "undefined" ? window : globalThis);
