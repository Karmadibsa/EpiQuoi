import { useState, useRef, useEffect } from 'react';
import { sendMessage } from '../services/api';
import { CAMPUSES } from '../services/constants';

export const useChat = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [step, setStep] = useState('chat'); // chat, error_zip
    const [loadingStatus, setLoadingStatus] = useState(null);

    const scrollRef = useRef(null);

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isLoading, step]);

    const handleSend = async (textOverride) => {
        const textToSend = typeof textOverride === 'string' ? textOverride : input;
        if (!textToSend.trim() || isLoading) return;

        if (typeof textOverride !== 'string' && textOverride?.preventDefault) {
            textOverride.preventDefault();
        }

        // Step: Zip Code Entry (Fallback Mode)
        if (step === 'error_zip') {
            const userMsg = { id: Date.now(), text: textToSend, sender: 'user' };
            setMessages(prev => [...prev, userMsg]);
            setInput('');
            setIsLoading(true);

            // Mock Campus Lookup
            setTimeout(() => {
                const found = CAMPUSES.find(c => textToSend.startsWith(c.zip.slice(0, 2)));
                let responseText = "";
                if (found) {
                    responseText = `Le campus **Epitech ${found.name}** semble être le plus proche (${found.zip}). \n\n Vous pouvez les contacter directement pour plus d'informations sur le programme.`;
                } else {
                    responseText = "Je n'ai pas trouvé de correspondance exacte, mais Epitech est présent dans toute la France. Je vous invite à consulter la carte sur le site officiel.";
                }

                setMessages(prev => [...prev, { id: Date.now() + 1, text: responseText, sender: 'bot' }]);
                setStep('chat');
                setIsLoading(false);
            }, 800);
            return;
        }

        // Normal Chat Flow
        const userMsg = { id: Date.now(), text: textToSend, sender: 'user' };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);
        setLoadingStatus('Réflexion');

        try {
            const response = await sendMessage(textToSend, messages, (evt) => {
                if (evt?.label) setLoadingStatus(evt.label);
            });
            const botMessage = { ...response, id: Date.now() + 1 };
            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                text: "⚠️ **Connexion au Cerveau Impossible** \n\n Je n'arrive pas à joindre le serveur. \n\n Pour vous aider, je peux chercher votre campus Epitech le plus proche. \n\n **Quel est votre Code Postal ?**",
                sender: 'bot',
                isError: true
            }]);
            setStep('error_zip');
        } finally {
            setIsLoading(false);
            setLoadingStatus(null);
        }
    };

    return {
        messages,
        input,
        setInput,
        isLoading,
        loadingStatus,
        step,
        handleSend,
        scrollRef,
        setMessages // Exported just in case needed for reset
    };
};
