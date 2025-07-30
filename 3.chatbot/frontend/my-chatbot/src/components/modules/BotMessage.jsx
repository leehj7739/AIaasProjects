import React from 'react';
import MessageBubble from './MessageBubble';

const BotMessage = ({ message }) => {
    return (
        <MessageBubble
            message={message}
            align="left"
            backgroundColor="bg-white"
            textColor="text-gray-800"
            avatarPosition="left"
        />
    );
};

export default BotMessage; 