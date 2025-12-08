import { useState, useRef, useEffect } from 'react';
import { chatApi } from '../services/api';
import type { ChatMessage, ChatStreamEvent } from '../types';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [thinkingText, setThinkingText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setThinkingText('');

    // Create a placeholder for the assistant's response
    const assistantMessageId = generateId();
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };
    setMessages(prev => [...prev, assistantMessage]);

    try {
      let fullContent = '';
      
      for await (const event of chatApi.streamMessage(input.trim(), messages)) {
        switch (event.type) {
          case 'thinking':
            setThinkingText(event.content || '');
            break;
          case 'token':
            fullContent += event.content || '';
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMessageId
                  ? { ...m, content: fullContent }
                  : m
              )
            );
            break;
          case 'complete':
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMessageId
                  ? { ...m, content: event.content || fullContent, isStreaming: false, intent: event.intent }
                  : m
              )
            );
            break;
          case 'error':
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMessageId
                  ? { ...m, content: `Error: ${event.content}`, isStreaming: false }
                  : m
              )
            );
            break;
        }
      }
    } catch (error) {
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantMessageId
            ? { ...m, content: `Sorry, an error occurred: ${error}`, isStreaming: false }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      setThinkingText('');
    }
  };

  return (
    <div className="h-screen flex flex-col bg-cream-50">
      {/* Header */}
      <header className="bg-white border-b border-cream-300 px-6 py-4">
        <h1 className="text-2xl font-display font-bold text-sage-800">Chat with KitchenSage</h1>
        <p className="text-sage-600 text-sm mt-1">
          Ask me anything about recipes, meal planning, or cooking tips!
        </p>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-sage-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-sage-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h2 className="text-xl font-display font-bold text-sage-800 mb-2">
              Welcome to KitchenSage!
            </h2>
            <p className="text-sage-600 max-w-md mx-auto">
              I'm your AI cooking assistant. Try asking me things like:
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {[
                "Find me a quick chicken dinner",
                "Plan my meals for the week",
                "What can I make with eggs?",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="px-4 py-2 bg-sage-100 hover:bg-sage-200 text-sage-700 rounded-full text-sm transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-sage-600 text-white rounded-br-md'
                  : 'bg-white text-sage-800 border border-cream-200 rounded-bl-md shadow-sm'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
              {message.isStreaming && (
                <span className="inline-block w-2 h-4 bg-sage-400 animate-pulse ml-1"></span>
              )}
            </div>
          </div>
        ))}

        {isLoading && thinkingText && (
          <div className="flex items-center gap-2 text-sage-500 animate-pulse-soft">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-sm italic">{thinkingText}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 bg-white border-t border-cream-200">
        <div className="flex gap-3 max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me about recipes, meal planning, or cooking..."
            className="flex-1 px-4 py-3 bg-cream-50 border border-cream-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-transparent text-sage-800 placeholder-sage-400"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-6 py-3 bg-sage-600 hover:bg-sage-700 disabled:bg-sage-300 text-white rounded-xl font-medium transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            Send
          </button>
        </div>
      </form>
    </div>
  );
}

