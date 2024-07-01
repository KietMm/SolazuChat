import React, { useState, useEffect, useRef } from 'react';
import { FaArrowCircleUp } from 'react-icons/fa';

interface InputAreaProps {
    onSendMessage: (userMessage: string) => void;
}

const InputArea: React.FC<InputAreaProps> = ({ onSendMessage }) => {
    const [userInput, setUserInput] = useState<string>("");
    const [sendMessageFlag, setSendMessageFlag] = useState<boolean>(false);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (sendMessageFlag && userInput.trim()) {
            onSendMessage(userInput);
            setUserInput('');
            if (inputRef.current) {
                inputRef.current.style.height = '40px'; // Reset to default height
            }
            setSendMessageFlag(false);  // Reset the flag after sending
        }
    }, [sendMessageFlag, userInput, onSendMessage]);

    const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
        const textarea = event.target;
        setUserInput(textarea.value);
        textarea.style.height = 'auto';
        textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    };

    const sendMessage = () => {
        setSendMessageFlag(true);  // Set the flag to trigger the useEffect
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();  
            event.stopPropagation();  // Prevent the default behavior
            sendMessage();
        }
    };

    return (
        <div className='inputArea'>
            <textarea
                ref={inputRef}
                className='input'
                placeholder="Type your message..."
                value={userInput}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                style={{ overflowY: 'auto', resize: 'none', maxHeight: '200px' }}
            />
            <button onClick={sendMessage}>
                <FaArrowCircleUp />
            </button>
        </div>
    );
};

export default InputArea;
