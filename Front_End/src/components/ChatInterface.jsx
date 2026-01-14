import React from 'react';
import { ArrowRight, RotateCcw } from 'lucide-react';
import Message from './Message';
import { DotGrid } from './DotGrid';
import { useChat } from '../hooks/useChat';

const ChatInterface = () => {
    const {
        messages,
        input,
        setInput,
        isLoading,
        step,
        handleSend,
        scrollRef
    } = useChat();

    const Suggestion = ({ label, query }) => (
        <button
            onClick={() => handleSend(query)}
            className="group flex flex-col items-start border-2 border-slate-200/60 p-4 hover:border-epitech-blue hover:bg-white/80 backdrop-blur-sm transition-all duration-300 w-full md:w-auto md:min-w-[200px]"
        >
            <span className="font-heading text-lg uppercase text-slate-400 group-hover:text-epitech-blue mb-2 transition-colors">QUESTION_</span>
            <span className="font-body text-sm text-left font-medium text-slate-800">{label}</span>
            <div className="w-4 h-1 bg-epitech-green mt-4 opacity-0 group-hover:opacity-100 transition-opacity"></div>
        </button>
    );

    return (
        <DotGrid className="flex flex-col h-full bg-slate-50">
            {/* Header */}
            <div className="flex-none flex items-center justify-between p-6 md:px-12 md:py-8 z-20">
                <div className="flex items-center gap-4">
                    <img src="/logo-noir.png" alt="Epitech Logo" className="h-8 md:h-10 w-auto" />
                </div>

                <button
                    onClick={() => window.location.reload()}
                    className="group flex items-center gap-2 px-4 py-2 border border-slate-200 rounded-none hover:bg-epitech-blue hover:text-white transition-all duration-300 bg-white/50 backdrop-blur"
                >
                    <RotateCcw size={16} className="group-hover:-rotate-180 transition-transform duration-500" />
                    <span className="font-heading uppercase text-sm tracking-wider">RESET_</span>
                </button>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 overflow-y-auto px-4 md:px-12 z-10 scroll-smooth">
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center pb-20 animate-fade-in">
                        <h1 className="font-heading text-[10vw] md:text-[8rem] text-epitech-blue leading-tight select-none opacity-10 md:opacity-100 mb-8 drop-shadow-sm">
                            EPIQUOI<span className="text-epitech-pink">_</span>
                        </h1>

                        <div className="max-w-2xl px-4 mb-16">
                            <p className="font-body text-lg md:text-xl text-slate-600 font-light">
                                &lt; Posez vos questions sur la <span className="text-epitech-blue font-bold">Pédagogie</span>,
                                les <span className="text-epitech-blue font-bold">Spécialisations</span> ou trouvez votre <span className="text-epitech-blue font-bold">Campus</span>. /&gt;
                            </p>
                        </div>

                        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-6 px-4">
                            <Suggestion label="C'est quoi la méthodologie Epitech ?" query="C'est quoi la méthodologie Epitech ?" />
                            <Suggestion label="Quelles sont les spécialisations ?" query="Quelles sont les spécialisations ?" />
                            <Suggestion label="Trouver son campus le plus proche" query="Où sont les campus Epitech ?" />
                        </div>
                    </div>
                ) : (
                    <div className="w-full max-w-4xl mx-auto space-y-8 pb-4">
                        {messages.map(msg => <Message key={msg.id} message={msg} />)}
                        {isLoading && (
                            <div className="flex justify-start w-full animate-pulse">
                                <div className="font-heading text-2xl text-slate-300 uppercase tracking-widest flex items-center gap-2">
                                    {(() => {
                                        const lastMsg = messages[messages.length - 1];
                                        const text = lastMsg ? lastMsg.text.toLowerCase() : "";
                                        const isScraping = text.includes("news") || text.includes("actu") || text.includes("nouveauté");
                                        return isScraping ? "SEARCHING_WEB" : "TYPING";
                                    })()}
                                    <span className="text-epitech-green animate-bounce">_</span>
                                </div>
                            </div>
                        )}
                        <div ref={scrollRef} />
                    </div>
                )}
            </div>

            {/* Input UI */}
            <div className="flex-none p-4 md:p-8 z-20 bg-gradient-to-t from-slate-50 via-slate-50 to-transparent pt-12">
                <div className="max-w-4xl mx-auto w-full">
                    <form onSubmit={handleSend} className="relative group w-full">
                        <div className="absolute inset-0 bg-white transform skew-x-[-1deg] shadow-lg border border-slate-100 transition-all group-hover:shadow-xl rounded-sm"></div>
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={step === 'error_zip' ? "Entrez votre code postal (ex: 94270)..." : "Posez votre question..."}
                            className="relative bg-transparent w-full p-4 md:p-6 text-lg font-body outline-none placeholder:text-slate-400 text-slate-900 border-none"
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isLoading}
                            className="absolute right-4 top-1/2 -translate-y-1/2 p-3 bg-epitech-blue text-white hover:bg-epitech-dark disabled:opacity-0 transition-all duration-300"
                        >
                            <ArrowRight size={24} />
                        </button>
                    </form>
                    <div className="flex flex-col items-center mt-4 gap-1 opacity-60">
                        <p className="font-body text-[10px] text-slate-500 italic">
                            &lt; Une question sur le programme ? Le chat est réinitialisé à chaque actualisation pour garantir la confidentialité de vos échanges. /&gt;
                        </p>
                    </div>
                </div>
            </div>
        </DotGrid>
    );
};

export default ChatInterface;
