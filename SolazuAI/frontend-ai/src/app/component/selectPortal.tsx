import React from 'react';
import CreatableSelect from 'react-select/creatable';
import './selectPortal.css';
import { IoIosSearch } from "react-icons/io";

interface Option {
  value: string;
  label: string;
}

interface CustomSelectProps {
  options: string[];
  kind: string;
  onSelect: (selected: string) => void;
}

const CustomSelect: React.FC<CustomSelectProps> = ({ options, kind, onSelect }) => {
  // Convert strings to Option objects
  const selectOptions: Option[] = options.map(option => ({ value: option, label: option }));

  const handleChange = (selectedOption: any, actionMeta: any) => {
    console.log('Selected Option:', selectedOption);
    console.log('Action Meta:', actionMeta);

    // Check if selectedOption is null
    if (!selectedOption) {
      console.warn('No option selected or created');
      return;
    }

    // Check if the new option was created
    if (actionMeta.action === 'create-option') {
      console.log('New project added:', selectedOption.value);
      // You can implement functionality to handle the new project here
    }
    onSelect(selectedOption.value);
    console.log('Selected value:', selectedOption.value);
  };

  const isValidNewOption = (inputValue: string) => {
    // Ensure that a new option can be created only if it doesn't already exist
    return !!inputValue && !selectOptions.some(option => option.label === inputValue);
  };

  const customPlaceholder = () => {
    switch (kind) {
      case 'project':
        return 'Select project';
      case 'epic':
        return 'Select epic';
      case 'ticket':
        return 'Select ticket/doc';
      default:
        return 'Select option';
    }
  };

  return (
    <div className='selectOption'>
      <CreatableSelect
        options={selectOptions}
        onChange={handleChange}
        placeholder={customPlaceholder()}
        classNamePrefix="select"
        isClearable
        formatCreateLabel={(inputValue) => `Create "${inputValue}"`}
        isValidNewOption={isValidNewOption} // Validate the new option creation
      />
      <IoIosSearch className='text-black' />
    </div>
  );
};

export default CustomSelect;
