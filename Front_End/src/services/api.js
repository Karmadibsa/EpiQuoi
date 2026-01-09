const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/chat';

export const sendMessage = async (text, history = []) => {
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: text,
                history: history
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return {
            text: data.response || "Réponse reçue du backend.",
            sender: 'bot'
        };
    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
};
