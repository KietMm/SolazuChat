import React from 'react';
import Select from 'react-select';
import './select.css';
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
  const selectOptions: Option[] = options.map(option => ({ value: option, label: option }));

  const handleChange = (selectedOption: any) => {
    onSelect(selectedOption.value);
    console.log('Selected value:', selectedOption.value);
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
      <Select
      options={selectOptions}
      onChange={handleChange}
      placeholder={customPlaceholder()}
      classNamePrefix="select"
      ></Select>
      <IoIosSearch className='text-black' />
    </div>
  );
};

export default CustomSelect;
