const preferredVoices = {
    "en-US": "Google US English",
    "fr-FR": "Google français",
    "hi-IN": "Google हिन्दी",
    "es-ES": "Google español"
};

let voiceEnabled = true;
let availableVoices = [];

// Load voices
function loadVoices() {
    availableVoices = speechSynthesis.getVoices();
}
speechSynthesis.onvoiceschanged = loadVoices;
loadVoices();

// Toggle voice on/off
function toggleVoice() {
    voiceEnabled = !voiceEnabled;

    if (!voiceEnabled && speechSynthesis.speaking) {
        speechSynthesis.cancel();
    }

    document.getElementById("toggle-voice").innerText = voiceEnabled ? "🔊 Voice On" : "🔇 Voice Off";
}

// Handle enter key for chat input
document.getElementById("chat-input").addEventListener("keypress", function (event) {  //bind the event to the doc 
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});

// Send message to chatbot
function sendMessage() {
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    if (!message) return;

    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML += `<p><strong>You:</strong> ${message}</p>`;
    input.value = "";

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message })
    })
    .then(res => res.json())
    .then(data => {
        const reply = data.reply || data.error || "No response.";
        chatBox.innerHTML += `<p><strong>Bot:</strong> ${reply}</p>`;
        chatBox.scrollTop = chatBox.scrollHeight;

        // Stop previous speech
        speechSynthesis.cancel();

        if (voiceEnabled && 'speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(reply);
            const lang = detectLanguage(reply);
            utterance.lang = lang;

            const voice = getVoiceForLang(lang);
            if (voice) {
                utterance.voice = voice;
            }

            speechSynthesis.speak(utterance);
        }
    })
    .catch(err => {
        chatBox.innerHTML += `<p style="color:red;"><strong>Error:</strong> ${err.message}</p>`;
    });
}

// Match preferred voice per language
function getVoiceForLang(langCode) {
    const preferredName = preferredVoices[langCode];
    if (preferredName) {
        const voiceByName = availableVoices.find(v => v.name === preferredName);
        if (voiceByName) return voiceByName;
    }

    return availableVoices.find(voice => voice.lang === langCode) ||
           availableVoices.find(voice => voice.lang.startsWith(langCode.split('-')[0])) ||
           null;
}

// Detect language of chatbot reply
function detectLanguage(text) {
    if (/[\u0900-\u097F]/.test(text)) return 'hi-IN'; // Hindi
    if (/[áéíóúñü¿¡]/i.test(text)) return 'es-ES';    // Spanish
    if (/[àâçéèêëîïôûùüÿœæ]/i.test(text)) return 'fr-FR'; // French
    return 'en-US'; // Default English
}
