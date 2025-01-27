import React, { useState, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Send } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => Promise<void>;
}

const ChatInterface = ({ messages, onSendMessage }: ChatInterfaceProps) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current;
      scrollContainer.scrollTop = scrollContainer.scrollHeight;
    }
  }, [messages]);

  // Initial focus and click handler setup
  useEffect(() => {
    const focusInput = () => {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    };

    // Focus input on mount
    focusInput();

    // Add click event listener to container
    const container = containerRef.current;
    if (container) {
      container.addEventListener('click', focusInput);
    }

    // Cleanup
    return () => {
      if (container) {
        container.removeEventListener('click', focusInput);
      }
    };
  }, []); // Empty dependency array since we only want this on mount

  // Keep focus on input when messages or loading state changes
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [messages, isLoading]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    setIsLoading(true);
    setInputMessage('');

    try {
      await onSendMessage(inputMessage);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div ref={containerRef} className="flex h-[calc(100vh-16rem)] flex-col">
      <div className="relative mb-4 flex-1 rounded-lg border border-gray-200 bg-gray-50/50 shadow-sm">
        <div
          ref={scrollAreaRef}
          className="absolute inset-0 overflow-y-auto rounded-lg px-4 py-4 [scrollbar-color:rgb(209_213_219)_transparent] [scrollbar-width:thin] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 hover:[&::-webkit-scrollbar-thumb]:bg-gray-400 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:w-2"
        >
          <div className="space-y-4">
            {messages.length === 0 && (
              <div className="flex h-full items-center justify-center text-gray-500">
                <p>No messages yet. Start a conversation!</p>
              </div>
            )}
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[70%] rounded-lg px-4 py-2 shadow-sm ${
                    message.sender === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-white text-gray-900'
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words">
                    {message.content}
                  </p>
                  <p
                    className={`mt-1 text-xs ${
                      message.sender === 'user'
                        ? 'text-blue-100'
                        : 'text-gray-500'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[70%] rounded-lg bg-white px-4 py-2 shadow-sm">
                  <div className="flex space-x-2">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-blue-400"></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-blue-400 delay-100"></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-blue-400 delay-200"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="flex gap-2"
      >
        <Input
          ref={inputRef}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Type your message..."
          className="flex-1"
          disabled={isLoading}
        />
        <Button type="submit" disabled={isLoading || !inputMessage.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
};

export { ChatInterface };
