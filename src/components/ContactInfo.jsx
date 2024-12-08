import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPhone, faEnvelope, faLocationDot } from '@fortawesome/free-solid-svg-icons';

export default function ContactInfo() {
  return (
    <div className="flex flex-wrap items-center gap-6 text-sm text-gray-300">
      <a 
        href="tel:0617959759" 
        className="flex items-center gap-2 hover:text-[#00f3ff] transition-colors"
        title="Appelez-nous"
      >
        <FontAwesomeIcon icon={faPhone} className="text-[#00f3ff]" />
        <span className="hidden md:inline">06 17 95 97 59</span>
      </a>
      <a 
        href="mailto:contact@reparateurpc.com" 
        className="flex items-center gap-2 hover:text-[#00f3ff] transition-colors"
        title="Envoyez-nous un email"
      >
        <FontAwesomeIcon icon={faEnvelope} className="text-[#00f3ff]" />
        <span className="hidden md:inline">contact@reparateurpc.com</span>
      </a>
      <div 
        className="hidden lg:flex items-center gap-2"
        title="Notre adresse"
      >
        <FontAwesomeIcon icon={faLocationDot} className="text-[#00f3ff]" />
        <span>6 impasse elisabeth vigée lebrun, Le Mans</span>
      </div>
    </div>
  );
}