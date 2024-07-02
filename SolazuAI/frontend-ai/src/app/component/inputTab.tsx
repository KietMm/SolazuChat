import React, { useState, useEffect } from 'react';
import './inputTab.css';

interface LinkInputProps {
  links: string[];
  onAddLink: () => void;
  onLinkChange: (index: number, value: string) => void;
}

const LinkInput: React.FC<LinkInputProps> = ({ links, onAddLink, onLinkChange }) => {
  useEffect(() => {
    if (links.length === 0) {
      onAddLink();
    }
  }, [links, onAddLink]);

  return (
    <div className="links-container">
      {links.map((link, index) => (
        <input
          key={index}
          type="text"
          value={link}
          onChange={(e) => onLinkChange(index, e.target.value)}
          className="link-input"
          placeholder="Paste link here"
        />
      ))}
      {links.length < 10 && (
        <button onClick={onAddLink} className="add-link-button">+</button>
      )}
    </div>
  );
};

interface TabsProps {
  links: { [key: string]: string[] };
  onLinkChange: (tab: string, index: number, value: string) => void;
  onAddLink: (tab: string) => void;
}

const Tabs: React.FC<TabsProps> = ({ links, onLinkChange, onAddLink }) => {
  const [activeTab, setActiveTab] = useState<string>('jira');

  const handleTabClick = (tab: string) => {
    setActiveTab(tab);
  };

  return (
    <div className="tabs-container">
      <div className="tabs-header">
        {['jira', 'confluence', 'docs', 'github'].map((tab) => (
          <button
            key={tab}
            className={`tab-button ${activeTab === tab ? 'active' : ''}`}
            onClick={() => handleTabClick(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>
      <div className="tabs-content">
        <LinkInput
          links={links[activeTab]}
          onAddLink={() => onAddLink(activeTab)}
          onLinkChange={(index, value) => onLinkChange(activeTab, index, value)}
        />
      </div>
    </div>
  );
};

export default Tabs;
