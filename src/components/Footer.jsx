import React from 'react';
import ContactInfo from './ContactInfo';

export default function Footer() {
  return (
    <footer className="bg-bg-card py-8">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <ContactInfo />
          <p className="text-sm text-gray-400">
            © 2023 Dépannage Informatique Le Mans. Tous droits réservés.
          </p>
        </div>
      </div>
    </footer>
  );
}