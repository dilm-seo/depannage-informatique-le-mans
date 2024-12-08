import React, { useState, useEffect } from 'react';
import { Link } from 'react-scroll';
import ContactInfo from './ContactInfo';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faLaptopMedical } from '@fortawesome/free-solid-svg-icons';

export default function Header() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 0);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className={`fixed w-full top-0 z-50 transition-all duration-300 ${
      isScrolled ? 'py-2 bg-black/90 backdrop-blur-sm' : 'py-4 bg-transparent'
    }`}>
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-bold neon-text flex items-center gap-2">
            <FontAwesomeIcon icon={faLaptopMedical} className="text-[#00f3ff]" />
            <span className="hidden sm:inline">Dépannage Informatique Le Mans</span>
            <span className="sm:hidden">Dépannage PC</span>
          </h1>
          <ContactInfo />
        </div>
      </div>
    </header>
  );
}