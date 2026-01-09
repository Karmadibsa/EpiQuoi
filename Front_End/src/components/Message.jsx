import React from 'react';
import { motion } from 'framer-motion';

const Message = ({ message }) => {
    const isUser = message.sender === 'user';
    // Use custom name if User, else EPIQUOI
    const senderName = isUser ? (message.userName || 'USER_') : 'EPIQUOI_';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} group`}
        >
            <div className={`max-w-[90%] md:max-w-[70%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>

                {/* Sender Label */}
                <span className={`font-heading text-sm mb-1 uppercase tracking-wider ${isUser ? 'text-epitech-blue' : 'text-epitech-pink'}`}>
                    {senderName}
                </span>

                {/* Bubble */}
                <div className={`
             relative px-6 py-4 text-base md:text-lg leading-relaxed font-body shadow-sm
             ${isUser
                        ? 'bg-epitech-blue text-white border-l-4 border-epitech-green'
                        : message.isError
                            ? 'bg-red-50 text-red-800 border-l-4 border-red-500'
                            : 'bg-white text-slate-800 border-l-4 border-epitech-pink'
                    }
        `}>
                    {/* Decorative Corner */}
                    <div className={`absolute top-0 w-2 h-2 ${isUser ? 'right-0 bg-white/20' : 'left-0 bg-black/5'} `}></div>

                    {/* Render with basic Markdown support (bold) */}
                    <div dangerouslySetInnerHTML={{ __html: message.text.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                </div>
            </div>

        </motion.div>
    );
};

export default Message;
