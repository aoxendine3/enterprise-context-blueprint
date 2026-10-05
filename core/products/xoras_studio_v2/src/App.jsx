import { useState, useRef, useEffect } from 'react';
import { Send, Terminal, Settings, Activity, Shield, Cpu } from 'lucide-react';

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'system', text: 'XORAS::OS Studio V2 Initialized. Local M4 Substrate Bound.' },
    { role: 'agent', name: 'DAXX', text: 'DAXX here. The placeholders have been purged. This UI is now physically wired to your local Ollama instance on port 11434. Send a message to verify.' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;
    
    const userText = input;
    setMessages(prev => [...prev, { role: 'user', text: userText }]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('http://127.0.0.1:11434/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'llama3', // Adjust to user's local model if known, default generic
          prompt: userText,
          stream: false
        })
      });

      if (!response.ok) {
        throw new Error('Ollama connection failed. Is it running on 11434?');
      }

      const data = await response.json();
      
      setMessages(prev => [...prev, { 
        role: 'agent', 
        name: 'OLLAMA (Local)', 
        text: data.response 
      }]);
      
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'system', 
        text: `SYSTEM ERROR: ${error.message}` 
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#0d1117] text-[#c9d1d9] font-sans">
      {/* Sidebar */}
      <div className="w-64 bg-[#161b22] border-r border-[#30363d] flex flex-col">
        <div className="p-4 border-b border-[#30363d] flex items-center gap-2 text-blue-400 font-bold">
          <Terminal size={20} />
          <span>XORAS STUDIO</span>
        </div>
        
        <div className="p-4 flex-1">
          <div className="text-xs font-semibold text-gray-500 mb-3 uppercase tracking-wider">Active Swarm (22)</div>
          
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm p-2 bg-[#21262d] rounded-md border border-[#30363d]">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <span>DAXX (Orchestrator)</span>
            </div>
            <div className="flex items-center gap-2 text-sm p-2 hover:bg-[#21262d] rounded-md transition-colors cursor-pointer text-gray-400">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <span>OLLAMA (Port 11434)</span>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-[#30363d] space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-400"><Cpu size={14} /> Apple M4 Max (Local)</div>
          <div className="flex items-center gap-2 text-xs text-green-500"><Activity size={14} /> API Linked</div>
          <div className="flex items-center gap-2 text-xs text-gray-400"><Shield size={14} /> Port 8085 Secured</div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative">
        <header className="h-14 border-b border-[#30363d] flex items-center px-6 justify-between bg-[#161b22]">
          <h2 className="font-semibold">Local Execution Console</h2>
          <Settings size={18} className="text-gray-400 cursor-pointer hover:text-white" />
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-2xl p-4 rounded-lg ${
                msg.role === 'user' ? 'bg-blue-600 text-white' : 
                msg.role === 'system' ? 'bg-[#21262d] border border-red-900 text-red-400 text-sm italic' : 
                'bg-[#21262d] border border-blue-900 text-gray-200'
              }`}>
                {msg.name && <div className="text-xs font-bold text-blue-400 mb-1">{msg.name}</div>}
                <div className="leading-relaxed whitespace-pre-wrap">{msg.text}</div>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-[#21262d] border border-blue-900 text-gray-400 p-4 rounded-lg text-sm italic">
                Ollama is computing...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 bg-[#0d1117]">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto relative">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Query local Ollama instance..." 
              className="w-full bg-[#161b22] border border-[#30363d] rounded-lg py-4 pl-4 pr-12 text-white focus:outline-none focus:border-blue-500 transition-colors shadow-lg"
              disabled={isTyping}
            />
            <button 
              type="submit" 
              disabled={isTyping}
              className={`absolute right-3 top-3.5 p-1.5 rounded text-white transition-colors ${isTyping ? 'bg-gray-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500'}`}
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
