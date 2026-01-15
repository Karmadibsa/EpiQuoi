import React from 'react';
import { ArrowRight, RotateCcw } from 'lucide-react';
import Message from './Message';
import { useChat } from '../hooks/useChat';

const WidgetChat = () => {
    const {
        messages,
        input,
        setInput,
        isLoading,
        step,
        handleSend,
        scrollRef,
        setMessages
    } = useChat();

    const Suggestion = ({ label, query }) => (
        <button
            onClick={() => handleSend(query)}
            className="group flex items-center justify-between border border-slate-200 px-3 py-2 bg-white hover:border-epitech-blue hover:shadow-md transition-all duration-200 w-full rounded-md"
        >
            <span className="font-body text-xs text-left font-medium text-slate-700 group-hover:text-epitech-blue">{label}</span>
            <div className="w-1.5 h-1.5 rounded-full bg-slate-200 group-hover:bg-epitech-blue transition-colors"></div>
        </button>
    );

    return (
        <div className="flex flex-col h-full bg-slate-50 font-sans">
            {/* Widget Header */}
            <div className="flex-none flex items-center justify-between p-4 z-20 border-b border-slate-100 bg-white/80 backdrop-blur-sm sticky top-0">
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <div className="w-2.5 h-2.5 rounded-full bg-epitech-green animate-pulse absolute -right-0.5 -top-0.5"></div>
                        <img src="/logo-noir.png" alt="Epitech" className="h-5 w-auto" />
                    </div>
                    <span className="font-heading text-xs font-bold tracking-widest text-slate-700">EPIQUOI_ASSISTANT</span>
                </div>
                <button
                    onClick={() => setMessages([])}
                    title="Effacer la conversation"
                    className="p-1 text-slate-400 hover:text-epitech-blue hover:bg-slate-50 rounded-full transition-all"
                >
                    <RotateCcw size={12} />
                </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 z-10 scroll-smooth custom-scrollbar">
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center animate-fade-in px-2">
                        <div className="mb-6 text-center">
                            <h1 className="font-heading text-3xl text-epitech-blue mb-2">Hello_</h1>
                            <p className="text-xs text-slate-500 max-w-[180px] leading-relaxed">
                                Je suis l'assistant virtuel d'Epitech. Comment puis-je vous aider ?
                            </p>
                        </div>

                        <div className="w-full space-y-2">
                            <Suggestion label="Méthodologie Epitech ?" query="C'est quoi la méthodologie Epitech ?" />
                            <Suggestion label="Spécialisations" query="Quelles sont les spécialisations ?" />
                            <Suggestion label="Trouver mon campus" query="Où sont les campus Epitech ?" />
                        </div>
                    </div>
                ) : (
                    <div className="space-y-6 pb-2">
                        {messages.map(msg => <Message key={msg.id} message={msg} isWidget={true} />)}
                        {isLoading && (
                            <div className="flex justify-start w-full animate-pulse pl-2">
                                <span className="text-xs font-mono text-slate-400">Thinking...</span>
                            </div>
                        )}
                        <div ref={scrollRef} />
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="flex-none p-3 bg-white border-t border-slate-100">
                <form onSubmit={handleSend} className="relative flex items-center gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={step === 'error_zip' ? "Code postal..." : "Votre question..."}
                        className="flex-1 bg-slate-50 text-xs p-2.5 rounded-lg border border-transparent focus:border-epitech-blue/30 focus:bg-white outline-none transition-all placeholder:text-slate-400"
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="p-2.5 bg-epitech-blue text-white rounded-lg hover:bg-epitech-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <ArrowRight size={16} />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default WidgetChat;
