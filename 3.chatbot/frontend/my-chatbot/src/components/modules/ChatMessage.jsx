import React from 'react';
import UserMessage from './UserMessage';
import BotMessage from './BotMessage';

const ChatMessage = ({ message }) => {
  const isUser = message.from === 'user';

  return isUser ? (
    <UserMessage message={message} />
  ) : (
    <BotMessage message={message} />
  );
};

export default ChatMessage;