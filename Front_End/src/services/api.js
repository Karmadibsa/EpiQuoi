const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/chat';
const STREAM_URL = (import.meta.env.VITE_API_URL_STREAM || 'http://localhost:8000/chat/stream');

export const sendMessage = async (text, history = [], onProgress) => {
    try {
        // If a progress callback is provided, use SSE streaming endpoint
        if (typeof onProgress === 'function') {
            const response = await fetch(STREAM_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, history }),
            });
            if (!response.ok || !response.body) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                // Split SSE events by blank line
                const parts = buffer.split('\n\n');
                buffer = parts.pop() || '';

                for (const evt of parts) {
                    const lines = evt.split('\n');
                    const dataLine = lines.find(l => l.startsWith('data: '));
                    if (!dataLine) continue;
                    const jsonStr = dataLine.replace('data: ', '');
                    const payload = JSON.parse(jsonStr);

                    if (payload.type === 'progress') {
                        onProgress(payload);
                    } else if (payload.type === 'final') {
                        return {
                            text: payload.response || "Réponse reçue du backend.",
                            sender: 'bot'
                        };
                    } else if (payload.type === 'error') {
                        throw new Error(payload.message || 'Stream error');
                    }
                }
            }

            throw new Error('Stream ended without final response');
        }

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
