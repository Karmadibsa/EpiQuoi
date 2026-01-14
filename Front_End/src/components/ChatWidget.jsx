import React, { useState } from 'react';
import { MessageSquare, X } from 'lucide-react';
import WidgetChat from './WidgetChat';

const ChatWidget = () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end pointer-events-none">
            {/* Chat Window Container - Enable pointer events only when open */}
            <div
                className={`
                    pointer-events-auto
                    mb-4 bg-white rounded-2xl shadow-2xl overflow-hidden border border-slate-200
                    transition-all duration-300 origin-bottom-right ease-out
                    ${isOpen ? 'w-[90vw] md:w-[380px] h-[80vh] md:h-[550px] opacity-100 scale-100 translate-y-0' : 'w-[20px] h-[20px] opacity-0 scale-50 translate-y-10 pointer-events-none'}
                `}
            >
                <div className={`h-full w-full`}>
                    <WidgetChat />
                </div>
            </div>

            {/* Toggle Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`
                    pointer-events-auto
                    group flex items-center justify-center w-14 h-14 md:w-16 md:h-16 rounded-full shadow-lg 
                    transition-all duration-300 hover:scale-105 active:scale-95 z-50
                    ${isOpen ? 'bg-slate-900 rotate-90' : 'bg-epitech-blue hover:shadow-epitech-blue/50'}
                `}
            >
                {isOpen ? (
                    <X className="text-white" size={28} />
                ) : (
                    <MessageSquare className="text-white" size={28} />
                )}


            </button>
        </div>
    );
};

export default ChatWidget;
