import React from 'react';
import MessageBubble from './MessageBubble';

const UserMessage = ({ message }) => {
    return (
        <MessageBubble
            message={message}
            align="right"
            backgroundColor="bg-blue-400"
            textColor="text-white"
            avatarPosition="right"
        />
    );
};

export default UserMessage; 