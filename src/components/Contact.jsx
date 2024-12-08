import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPhone, faEnvelope, faClock } from '@fortawesome/free-solid-svg-icons';

export default function Contact() {
  return (
    <section className="py-16 gradient-bg" id="contact">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 bg-clip-text text-transparent bg-gradient-to-r from-primary-light to-primary">
          Contactez-nous
        </h2>
        <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-8">
          <div className="p-6 rounded-lg card-gradient accent-border">
            <h3 className="text-2xl font-semibold mb-6">Informations de contact</h3>
            <div className="space-y-4">
              <p className="flex items-center gap-3">
                <FontAwesomeIcon icon={faPhone} className="text-primary-light" />
                <a href="tel:0617959759" className="hover:text-primary-light transition-colors">
                  06 17 95 97 59
                </a>
              </p>
              <p className="flex items-center gap-3">
                <FontAwesomeIcon icon={faEnvelope} className="text-primary-light" />
                <a href="mailto:contact@reparateurpc.com" className="hover:text-primary-light transition-colors">
                  contact@reparateurpc.com
                </a>
              </p>
              <p className="flex items-center gap-3">
                <FontAwesomeIcon icon={faClock} className="text-primary-light" />
                Lundi - Samedi: 9h - 19h
              </p>
            </div>
          </div>
          <div className="p-6 rounded-lg card-gradient accent-border">
            <h3 className="text-2xl font-semibold mb-6">Zone d'intervention</h3>
            <p className="mb-4 text-gray-300">
              Nous intervenons sur Le Mans et ses environs pour tous vos besoins en dépannage informatique.
            </p>
            <p className="mb-4 text-gray-300">
              Service à domicile ou assistance à distance selon vos préférences.
            </p>
            <p className="text-gray-300">
              Adresse:<br />
              6 impasse elisabeth vigée lebrun<br />
              Le Mans
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}